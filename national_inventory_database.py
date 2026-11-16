"""National catalog and conservative selection of Brazilian forest inventories.

The SQLite database distinguishes portal leads, published aggregates, open
plot data, and files actually present locally. A source is never eligible for
pixel pairing or model fitting merely because its catalog record exists.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
import time
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORTAL_REGISTRY = DATA / "national_inventory_portals_v1.csv"
DEFAULT_DB = DATA / "national_forest_inventory_catalog_v1.sqlite"
SFB_CKAN = "https://dados.florestal.gov.br/api/3/action"
SFB_SEARCH_TERMS = (
    '"Inventário Florestal Nacional"', "IFN", "DAP 10 por UF",
    "unidades amostrais IFN", "biomassa carbono IFN", "necromassa IFN",
    "regeneração IFN", "serapilheira IFN",
)

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS portals (
 source_id TEXT PRIMARY KEY, institution TEXT NOT NULL, unit_scope TEXT NOT NULL,
 portal_url TEXT NOT NULL, api_url TEXT, method TEXT, source_type TEXT,
 access_status TEXT, inventory_role TEXT, notes TEXT,
 last_checked_utc TEXT, last_check_status TEXT, last_check_message TEXT
);
CREATE TABLE IF NOT EXISTS inventory_records (
 record_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES portals(source_id),
 title TEXT NOT NULL, record_type TEXT NOT NULL, data_level TEXT,
 biome TEXT, uf TEXT, microregion TEXT, physiognomy TEXT,
 longitude REAL, latitude REAL, period_start TEXT, period_end TEXT,
 plot_count INTEGER, tree_record_count INTEGER, open_data INTEGER NOT NULL DEFAULT 0,
 georeferenced INTEGER NOT NULL DEFAULT 0, variables_json TEXT,
 license TEXT, dataset_url TEXT, local_path TEXT, harvest_status TEXT NOT NULL,
 evidence_status TEXT NOT NULL, model_eligible INTEGER NOT NULL DEFAULT 0,
 source_priority INTEGER, uncertainty_note TEXT, metadata_json TEXT,
 structural_metrics_json TEXT, updated_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inventory_compatibility
 ON inventory_records(biome,physiognomy,microregion,open_data,model_eligible);
CREATE INDEX IF NOT EXISTS idx_inventory_source ON inventory_records(source_id);
CREATE INDEX IF NOT EXISTS idx_inventory_filter
 ON inventory_records(biome,physiognomy,record_type,source_priority);
CREATE INDEX IF NOT EXISTS idx_inventory_access
 ON inventory_records(source_id,data_level,model_eligible,open_data,georeferenced);
CREATE INDEX IF NOT EXISTS idx_inventory_region
 ON inventory_records(uf,microregion,biome);
CREATE TABLE IF NOT EXISTS catalog_meta (
 key TEXT PRIMARY KEY, value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS harvest_runs (
 run_id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL,
 started_utc TEXT NOT NULL, finished_utc TEXT, status TEXT NOT NULL,
 discovered_count INTEGER NOT NULL DEFAULT 0, downloaded_count INTEGER NOT NULL DEFAULT 0,
 error TEXT, manifest_path TEXT
);
"""


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _norm(value):
    text=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(c for c in text if c.isalnum() and not unicodedata.combining(c))


def _read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))


def _conn(path=DEFAULT_DB):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(p)
    conn.row_factory=sqlite3.Row
    conn.executescript(SCHEMA)
    columns={r[1] for r in conn.execute("PRAGMA table_info(inventory_records)")}
    if "structural_metrics_json" not in columns:
        conn.execute("ALTER TABLE inventory_records ADD COLUMN structural_metrics_json TEXT")
    return conn


def _portal_map(conn):
    return {r["source_id"]:dict(r) for r in conn.execute("SELECT * FROM portals")}


_SEED_FILES=(PORTAL_REGISTRY, DATA/"structural_inventory_sources_v1.csv",
    DATA/"structural_aggregate_evidence_v1.csv",DATA/"national_inventory_datasets_v1.csv",
    DATA/"national_inventory_source_metrics_v1.json",DATA/"tapajos_ornl1552_structure_v1.csv",
    DATA/"microdados_inventarios_harmonizados_v1.csv",
    DATA/"ifn_fesv_mato_grosso_agb_candidates_v1.csv",DATA/"ifn_necromass_biome_uf_v1.csv")

def _seed_fingerprint():
    digest=hashlib.sha256()
    for file in _SEED_FILES:
        digest.update(file.name.encode()); digest.update(b"\0")
        if file.exists():
            digest.update(file.read_bytes())
        else:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def _catalog_revision(conn):
    row=conn.execute("SELECT value FROM catalog_meta WHERE key='seed_fingerprint'").fetchone()
    return row[0] if row else "unversioned"


def _source_for_inventory(source_id, institution, url, source_ids):
    """Map a bibliography row to its actual repository/journal, not a default."""
    sid=_norm(source_id); inst=_norm(institution); link=_norm(url)
    if "ifn" in sid or "sfb" in inst:return "SFB_IFN"
    # _norm removes punctuation, including underscores and hyphens, so both
    # SEMA_MT identifiers and SEMA-MT institution names normalize to "semamt".
    if "semamt" in sid or "semamt" in inst:return "SEMA_MT_GESTAO_FLORESTAL"
    if "ornl" in sid or "daacornl" in link:return "ORNL_DAAC"
    if "icmbio" in sid or "icmbio" in inst or "govbr/icmbio" in link:
        return "ICMBIO_PLANOS_UC"
    if "dryad" in sid or "dryad" in link:return "DRYAD"
    if "embrapa" in sid:
        if "pantanal" in sid:return "EMBRAPA_PANTANAL"
        if "cerrados" in sid:return "EMBRAPA_CERRADOS"
        if "semiarido" in sid:return "EMBRAPA_SEMIARIDO"
        if "florestas" in sid:return "EMBRAPA_FLORESTAS"
        if "amazonia oriental" in sid or "aomft" in sid:return "EMBRAPA_AMAZONIA_ORIENTAL"
    if "embrapa" in inst or "cnptiaembrapa" in link:return "EMBRAPA_REDAPE"
    if "sif" in sid or "sociedade de investigacoes florestais" in inst:return "SIF_UFV"
    if "jbrj" in sid or "jardim botanico do rio de janeiro" in inst:return "JBRJ_RESEARCH"
    if "vale" in sid or "vale" in inst:return "VALE_RESERVA_NATURAL"
    if "ief" in sid or "ief" in inst:return "IEF_MG_INVENTARIO"
    if "esalq" in sid or "esalq" in inst or "tese.usp.br" in link:return "USP_ESALQ"
    if "unesp" in sid or "unesp" in inst or "unesp.br" in link:return "UNESP_REPOSITORY"
    if "inpa" in inst or "inpa" in link:return "INPA_REPOSITORY"
    if "ufv" in inst or "locusufv" in link:return "UFV_LOCUS"
    if "ufra" in inst or "ufra" in link:return "UFRA_RIUFRA"
    if "ufpr" in inst or "ufpr" in link:return "UFPR_ACERVO"
    if "ufms" in inst or "ufms" in link:return "UFMS_REPOSITORY"
    if "ufla" in inst or "ufla" in link:return "UFLA_RIUFLA"
    if "unb" in inst or "unb" in link:return "UNB_REPOSITORY"
    if "museugoeldi" in inst or "museugoeldi" in link:return "MUSEU_GOELDI"
    if "ufsm" in inst or "ufsm" in link:return "UFSM_CIENCIA_FLORESTAL"
    if "ufrrj" in inst or "ufrrj" in link:return "UFRRJ_REPOSITORY"
    if "scielo" in link:return "SCIELO"
    if "ipef" in link:return "IPEF_SCIENTIA_FORESTALIS"
    if "furb" in inst or "iff.sc.gov.br" in link:return "IFFSC_FURB"
    if "ibama.gov.br" in link:return "IBAMA_SINAFLOR"
    if "bdtd" in link or "capes" in link:return "IBICT_BDTD"
    if "sinaflor" in sid:return "IBAMA_SINAFLOR"
    return "IBICT_BDTD" if "IBICT_BDTD" in source_ids else next(iter(source_ids))


def initialize_database(path=DEFAULT_DB, *, seed=True):
    """Create/update catalog tables and seed known portals plus repository data."""
    conn=_conn(path)
    portals=_read_csv(PORTAL_REGISTRY)
    conn.executemany("""INSERT INTO portals
      (source_id,institution,unit_scope,portal_url,api_url,method,source_type,
       access_status,inventory_role,notes)
      VALUES (:source_id,:institution,:unit_scope,:portal_url,:api_url,:method,
       :source_type,:access_status,:inventory_role,:notes)
      ON CONFLICT(source_id) DO UPDATE SET institution=excluded.institution,
       unit_scope=excluded.unit_scope,portal_url=excluded.portal_url,
       api_url=excluded.api_url,method=excluded.method,source_type=excluded.source_type,
       access_status=excluded.access_status,inventory_role=excluded.inventory_role,
       notes=excluded.notes""",portals)
    seed_fingerprint=_seed_fingerprint() if seed else None
    saved_fingerprint=conn.execute("SELECT value FROM catalog_meta WHERE key='seed_fingerprint'").fetchone()
    needs_seed=bool(seed and (not saved_fingerprint or saved_fingerprint[0]!=seed_fingerprint))
    if needs_seed:
        source_ids={r[0] for r in conn.execute("SELECT source_id FROM portals")}
        now=_now()
        def insert(row):
            conn.execute("""INSERT INTO inventory_records
              (record_id,source_id,title,record_type,data_level,biome,uf,microregion,
               physiognomy,longitude,latitude,period_start,period_end,plot_count,
               tree_record_count,open_data,georeferenced,variables_json,license,
               dataset_url,local_path,harvest_status,evidence_status,model_eligible,
               source_priority,uncertainty_note,metadata_json,structural_metrics_json,updated_utc)
              VALUES (:record_id,:source_id,:title,:record_type,:data_level,:biome,:uf,
               :microregion,:physiognomy,:longitude,:latitude,:period_start,:period_end,
               :plot_count,:tree_record_count,:open_data,:georeferenced,:variables_json,
               :license,:dataset_url,:local_path,:harvest_status,:evidence_status,
               :model_eligible,:source_priority,:uncertainty_note,:metadata_json,:structural_metrics_json,:updated_utc)
              ON CONFLICT(record_id) DO UPDATE SET
               source_id=excluded.source_id,title=excluded.title,record_type=excluded.record_type,
               data_level=excluded.data_level,biome=excluded.biome,uf=excluded.uf,
               microregion=excluded.microregion,physiognomy=excluded.physiognomy,
               longitude=excluded.longitude,latitude=excluded.latitude,period_start=excluded.period_start,
               period_end=excluded.period_end,plot_count=excluded.plot_count,
               tree_record_count=excluded.tree_record_count,open_data=excluded.open_data,
               georeferenced=excluded.georeferenced,variables_json=excluded.variables_json,
               license=excluded.license,dataset_url=excluded.dataset_url,local_path=excluded.local_path,
               harvest_status=excluded.harvest_status,evidence_status=excluded.evidence_status,
               model_eligible=excluded.model_eligible,source_priority=excluded.source_priority,
               uncertainty_note=excluded.uncertainty_note,metadata_json=excluded.metadata_json,
               structural_metrics_json=excluded.structural_metrics_json,updated_utc=excluded.updated_utc""",row)
        official_ifn_stats={}
        official_ifn_db=DATA/"national_inventory_microdata_v1.sqlite"
        if official_ifn_db.is_file():
            try:
                with sqlite3.connect(f"file:{official_ifn_db.resolve()}?mode=ro",uri=True) as ifn_conn:
                    official_ifn_stats={"tree_record_count":ifn_conn.execute(
                        "SELECT count(*) FROM ifn_dap10_observation").fetchone()[0],
                        "plot_count":ifn_conn.execute(
                        "SELECT count(*) FROM ifn_sampling_unit_summary").fetchone()[0]}
            except sqlite3.Error:
                official_ifn_stats={}
        for r in _read_csv(DATA/"structural_inventory_sources_v1.csv"):
            if r["source_id"] in {"MX_SANTO_AMBROSIO_PROJECT_167","CE_JALAPAO_PROJECT_10"}:
                # These are separately registered owner-provided local records,
                # not public repository candidates or institutional datasets.
                continue
            # The IFN DAP10 dataset is represented once below by its harvested
            # dataset record, avoiding a duplicate candidate in on-demand queries.
            if r["source_id"]=="SFB_IFN_DAP10_SET2025" and official_ifn_stats:
                continue
            src=_source_for_inventory(r["source_id"],r["institution"],r.get("url"),source_ids)
            if src not in source_ids:src="EMBRAPA_REDAPE"
            level=r.get("data_level") or "candidate"
            opened=str(r.get("plot_data_open","")).upper()=="TRUE"
            primary=level in {"primary_tree","primary_plot","primary_or_supplementary"}
            insert(dict(record_id="source:"+r["source_id"],source_id=src,
                title=r["source_id"]+" — "+r.get("institution",""),record_type="source_candidate",
                data_level=level,biome=r.get("biome"),uf=None,microregion=r.get("region"),
                physiognomy=r.get("physiognomy"),longitude=None,latitude=None,
                period_start=None,period_end=None,plot_count=None,tree_record_count=None,
                open_data=int(opened),georeferenced=0,variables_json=json.dumps(
                    [x.strip() for x in r.get("structural_fields","").split(";") if x.strip()],ensure_ascii=False),
                license=None,dataset_url=r.get("url"),local_path=None,
                harvest_status="CATALOGADO_NAO_BAIXADO",
                evidence_status="FONTE_CANDIDATA_REQUER_AUDITORIA",
                model_eligible=0,source_priority=(1 if opened and primary else 3),
                uncertainty_note="Referência não implica dados locais prontos nem elegibilidade de modelo.",
                metadata_json=json.dumps(r,ensure_ascii=False),
                structural_metrics_json=json.dumps({"listed_fields":r.get("structural_fields"),
                    "statistical_use":r.get("statistical_use")},ensure_ascii=False),updated_utc=now))
        for r in _read_csv(DATA/"structural_aggregate_evidence_v1.csv"):
            src=_source_for_inventory(r.get("source_id"),r.get("citation"),r.get("url"),source_ids)
            metrics={"metric":r.get("metric"),"unit":r.get("unit"),
                "center_type":r.get("center_type"),"center":r.get("center"),
                "sd":r.get("sd"),"se":r.get("se"),"ci95_low":r.get("ci95_low"),
                "ci95_high":r.get("ci95_high"),"iqr_low":r.get("iqr_low"),
                "iqr_high":r.get("iqr_high"),"range_low":r.get("range_low"),
                "range_high":r.get("range_high"),"n_plots":r.get("n_plots"),
                "n_sites":r.get("n_sites"),"statistical_use":r.get("statistical_use")}
            insert(dict(record_id="aggregate:"+r["source_id"],source_id=src,
                title=r.get("citation") or r["source_id"],record_type="published_aggregate",
                data_level=r.get("data_level") or "published_aggregate",biome=r.get("biome"),
                uf=None,microregion=r.get("region"),physiognomy=r.get("physiognomy"),
                longitude=None,latitude=None,period_start=None,period_end=None,
                plot_count=int(r["n_plots"]) if str(r.get("n_plots","")).isdigit() else None,
                tree_record_count=None,open_data=0,georeferenced=0,
                variables_json=json.dumps([r.get("metric"),r.get("unit")],ensure_ascii=False),
                license=None,dataset_url=r.get("url"),local_path=None,
                harvest_status="REFERENCIA_PUBLICADA_NAO_HARMONIZADA",
                evidence_status="AGREGADO_PUBLICADO_REQUER_AUDITORIA",
                model_eligible=0,source_priority=2,
                uncertainty_note="Não usar como parcela nem para calibrar SAR sem erro, desenho e domínio compatíveis.",
                metadata_json=json.dumps(r,ensure_ascii=False),
                structural_metrics_json=json.dumps(metrics,ensure_ascii=False),updated_utc=now))
        # Curated government/institutional datasets are first-class catalogue
        # records. Listed/open does not mean downloaded or scientifically used.
        repository_ids={
            "DRYAD_UFRA_EMBRAPA_INPE":"DRYAD",
            "NASA_ORNL_DAAC":"ORNL_DAAC",
        }
        for r in _read_csv(DATA/"national_inventory_datasets_v1.csv"):
            observed_status=r.get("current_harvest_status") or "listed_not_downloaded"
            is_loaded_ifn=(r["dataset_id"]=="SFB_IFN_DAP10_SET2025" and bool(official_ifn_stats))
            if is_loaded_ifn:
                observed_status="BAIXADO_HARMONIZADO_LOCAL"
            repository_source=repository_ids.get(r["source_id"],r["source_id"])
            if repository_source not in source_ids:
                # Keep the original source label in metadata, but satisfy the
                # catalog FK with the canonical repository registered above.
                repository_source=_source_for_inventory(
                    r["source_id"],r.get("title"),r.get("dataset_url"),source_ids)
            evidence=("DADOS_AGREGADOS_DE_FONTE_OFICIAL_COM_HASH; NAO_SAO_PARCELAS_INDEPENDENTES"
                      if observed_status=="downloaded_sanitized_summary" else
                      "MICRODADOS_PRIMARIOS_IFN; 27 ARQUIVOS UF DE UM PROGRAMA; UAS NAO SAO POSICOES DE ARVORES"
                      if is_loaded_ifn else
                      "METADADO_DE_BASE; REQUER_DOWNLOAD_DOCUMENTO_E_AUDITORIA")
            insert(dict(record_id="dataset:"+r["dataset_id"],source_id=repository_source,
                title=r["title"],record_type="public_dataset_catalog",data_level=r.get("data_grain"),
                biome=None,uf=None,microregion=None,physiognomy=None,longitude=None,latitude=None,
                period_start=None,period_end=None,plot_count=official_ifn_stats.get("plot_count") if is_loaded_ifn else None,
                tree_record_count=official_ifn_stats.get("tree_record_count") if is_loaded_ifn else None,
                open_data=int(r.get("access_type") in {"open_dataset","open_or_terms","public_reports"}),
                georeferenced=0,variables_json="[]",license=r.get("license_note"),
                dataset_url=r.get("dataset_url"),local_path=("data/national_inventory_microdata_v1.sqlite"
                    if is_loaded_ifn else "data/national_inventory_source_metrics_v1.json"
                    if observed_status=="downloaded_sanitized_summary" else None),
                harvest_status=observed_status,evidence_status=evidence,model_eligible=0,
                source_priority=1 if r.get("access_type")=="open_dataset" else 3,
                uncertainty_note=r.get("inventory_semantics"),
                metadata_json=json.dumps(r,ensure_ascii=False),
                structural_metrics_json=None,updated_utc=now))
        metrics_path=DATA/"national_inventory_source_metrics_v1.json"
        if metrics_path.exists():
            snapshot=json.loads(metrics_path.read_text(encoding="utf-8"))
            for source_id,details in snapshot.get("sources",{}).items():
                rec_id="source_metrics:"+source_id
                metrics_source=("IBAMA_LICENCIAMENTO" if source_id=="IBAMA_LICENSES_FEDERAL" else "IBAMA_SINAFLOR")
                if metrics_source not in source_ids:continue
                insert(dict(record_id=rec_id,source_id=("IBAMA_LICENCIAMENTO" if source_id=="IBAMA_LICENSES_FEDERAL" else "IBAMA_SINAFLOR"),
                    title="Contagem agregada de registros — "+source_id,
                    record_type="source_inventory_count_snapshot",data_level="aggregate_catalog_count",
                    biome=None,uf=None,microregion=None,physiognomy=None,longitude=None,latitude=None,
                    period_start=None,period_end=None,plot_count=None,tree_record_count=None,
                    open_data=1,georeferenced=0,variables_json="[]",license="Estatística agregada; fonte oficial e SHA-256 no JSON",
                    dataset_url=details.get("dataset_url"),local_path="data/national_inventory_source_metrics_v1.json",
                    harvest_status="CONTAGEM_AGREGADA_LIVE_COM_HASH",evidence_status="CONTAGEM_DE_REGISTROS_NAO_CONTAGEM_DE_INVENTARIOS_INDEPENDENTES",
                    model_eligible=0,source_priority=2,
                    uncertainty_note=(details.get("summary") or {}).get("inventory_count_interpretation"),
                    metadata_json=json.dumps(details,ensure_ascii=False),structural_metrics_json=None,updated_utc=now))
        # Files actually bundled in the application. Counts refer to table
        # rows/unique plots, not to independent regional inventory campaigns.
        tap_rows=_read_csv(DATA/"tapajos_ornl1552_structure_v1.csv")
        tap_plots={r.get("plot") for r in tap_rows if r.get("plot")}
        insert(dict(record_id="local:ORNL_1552_TAPAJOS",source_id="ORNL_DAAC",
            title="ORNL DAAC 1552 — resumos estruturais por parcela, FLONA Tapajós",
            record_type="harmonized_plot_level_dataset",data_level="primary_plot",
            biome="Amazônia",uf="PA",microregion="FLONA Tapajós",physiognomy="Floresta Ombrófila Densa",
            longitude=None,latitude=None,period_start=None,period_end=None,plot_count=len(tap_plots),
            tree_record_count=None,open_data=1,georeferenced=1,
            variables_json=json.dumps(["plot","n_trees","stems_ha","basal_area_m2_ha","h100_field_m","wood_density_ba_g_cm3","agb_chave2014_mg_ha"],ensure_ascii=False),
            license="ORNL DAAC terms; cite dataset DOI 10.3334/ORNLDAAC/1552",dataset_url="https://doi.org/10.3334/ORNLDAAC/1552",
            local_path="data/tapajos_ornl1552_structure_v1.csv",harvest_status="BAIXADO_HARMONIZADO_LOCAL",
            evidence_status="RESUMO_DE_30_PARCELAS_PRIMARIAS; tabela árvore-a-árvore não está embutida; não há pares SAR parcela-pixel nacionais",
            model_eligible=1,source_priority=1,uncertainty_note="Calibração H100×G restrita aos suportes cadastrados em Tapajós.",
            metadata_json=json.dumps({"csv_rows":len(tap_rows),"unique_plots":len(tap_plots),"record_grain":"uma linha por parcela"},ensure_ascii=False),
            structural_metrics_json=json.dumps({"fields_in_file":["n_trees","stems_ha","basal_area_m2_ha","h100_field_m","agb_chave2014_mg_ha"],"diameter_distribution":"not_present"},ensure_ascii=False),updated_utc=now))
        # Project-history microdata are included as local structural evidence,
        # with geolocation and sampling-area limits preserved in the catalog.
        from inventory_microdata_library import summarize_inventory_microdata
        microbase=summarize_inventory_microdata(DATA/"microdados_inventarios_harmonizados_v1.csv")
        for inventory_id,details in microbase["inventories"].items():
            mexiana=inventory_id=="MX_SANTO_AMBROSIO_2025"
            insert(dict(record_id="local:"+inventory_id,source_id="PROJECT_INVENTORY_LIBRARY",
                title=("Inventário florestal — Ilha Mexiana / Fazenda Santo Ambrósio" if mexiana
                       else "Inventário florestal — Jalapão"),
                record_type="harmonized_plot_level_dataset" if mexiana else "harmonized_tree_level_dataset_unscaled",
                data_level="primary_plot" if mexiana else "primary_tree",
                biome=details["biome"],uf=("PA" if mexiana else "TO"),
                microregion=("Ilha Mexiana / foz do Amazonas" if mexiana else None),
                physiognomy=details["physiognomy_scope"],longitude=None,latitude=None,
                period_start=None,period_end=None,plot_count=details["plot_count"],
                tree_record_count=details["tree_record_count"],open_data=0,georeferenced=0,
                variables_json=json.dumps(["DAP_cm","height_m","species","plot_id","status","allometric_biomass"],ensure_ascii=False),
                license="Dados de inventário fornecidos no histórico do projeto; licença de redistribuição não declarada.",
                dataset_url=None,local_path="data/microdados_inventarios_harmonizados_v1.csv",
                harvest_status="MICRODADOS_HARMONIZADOS_LOCAL_SEM_GEOREFERENCIA" if mexiana else "MICRODADOS_HARMONIZADOS_LOCAL_SEM_AREA_DE_PARCELA",
                evidence_status="INVENTARIO_PRIMARIO_AGREGADO_REGIONAL_SEM_PAREAMENTO_SAR" if mexiana else "INVENTARIO_PRIMARIO_SEM_AREA_PARCELA_E_SEM_CLASSE_IBGE_CONFIRMADA",
                model_eligible=0,source_priority=1 if mexiana else 2,
                uncertainty_note=details["limitation"],
                metadata_json=json.dumps({"inventory_id":inventory_id,"site":details["site"],
                    "distinct_plots":details["plot_count"],"tree_record_count":details["tree_record_count"],
                    "source_dataset_sha256":microbase["source_dataset_sha256"],
                    "area_normalized_metrics_available":details["area_normalized_metrics_available"],
                    "regional_reference_scope":details["regional_reference_scope"],
                    "plot_area_evidence":details["plot_area_evidence"]},ensure_ascii=False),
                structural_metrics_json=json.dumps({"tree_sample_mean_dbh_cm":details["diameter_sample_mean_cm"],
                    "tree_sample_mean_height_m":details["height_sample_mean_m"],
                    "mean_plot_stems_ha":details["mean_plot_stems_ha"],
                    "mean_plot_basal_area_m2_ha":details["mean_plot_basal_area_m2_ha"],
                    "mean_plot_agb_allometric_mg_ha":details["mean_plot_agb_allometric_mg_ha"],
                    "agb_kind":details["agb_kind"],"top10_species_by_stem_count":details["top10_species_by_stem_count"],
                    "source_dataset_sha256":microbase["source_dataset_sha256"]},ensure_ascii=False),updated_utc=now))
        for filename,title,kind,rows_count,note in (
            ("ifn_fesv_mato_grosso_agb_candidates_v1.csv","IFN MT — candidatos AGB FESV","ifn_candidate",37,"Equação Chave e transferência não validadas; cenário condicional restrito."),
            ("ifn_necromass_biome_uf_v1.csv","IFN — resumos de necromassa por bioma/UF","thematic_aggregate",43,"Agregados por UF/bioma; não são parcelas primárias harmonizadas.")):
            count=len(_read_csv(DATA/filename))
            insert(dict(record_id="local:"+filename,source_id="SFB_IFN",title=title,
                record_type=kind,data_level=kind,biome=None,uf=None,microregion=None,physiognomy=None,
                longitude=None,latitude=None,period_start=None,period_end=None,plot_count=None,
                tree_record_count=None,open_data=1,georeferenced=0,variables_json="[]",license="SFB/IFN; conservar citação",
                dataset_url="https://dados.florestal.gov.br/pt_BR/dataset/",local_path="data/"+filename,
                harvest_status="RESUMO_TABULAR_LOCAL_NAO_DADOS_DE_ARVORE_POR_PARCELA",
                evidence_status="AGREGADO_OU_CANDIDATO_NAO_HARMONIZADO",model_eligible=0,
                source_priority=2,uncertainty_note=note,metadata_json=json.dumps({"row_count":count},ensure_ascii=False),
                structural_metrics_json=json.dumps({"row_count":count},ensure_ascii=False),updated_utc=now))
        conn.execute("INSERT INTO catalog_meta(key,value) VALUES('seed_fingerprint',?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value",(seed_fingerprint,))
    conn.commit()
    result=database_summary(conn)
    conn.close()
    return result


def database_summary(conn_or_path=DEFAULT_DB):
    own=not isinstance(conn_or_path,sqlite3.Connection)
    conn=_conn(conn_or_path) if own else conn_or_path
    summary={"portal_count":conn.execute("SELECT count(*) FROM portals").fetchone()[0],
        "catalog_record_count":conn.execute("SELECT count(*) FROM inventory_records").fetchone()[0],
        "open_plot_candidates":conn.execute("SELECT count(*) FROM inventory_records WHERE open_data=1 AND data_level LIKE 'primary_%'").fetchone()[0],
        "locally_harmonized_plot_level_datasets":conn.execute("SELECT count(*) FROM inventory_records WHERE harvest_status='BAIXADO_HARMONIZADO_LOCAL'").fetchone()[0],
        "locally_harmonized_project_inventory_datasets":conn.execute("SELECT count(*) FROM inventory_records WHERE harvest_status LIKE 'MICRODADOS_HARMONIZADOS_LOCAL_%'").fetchone()[0],
        "locally_usable_primary_inventory_datasets":conn.execute("SELECT count(*) FROM inventory_records WHERE harvest_status='BAIXADO_HARMONIZADO_LOCAL' OR harvest_status LIKE 'MICRODADOS_HARMONIZADOS_LOCAL_%'").fetchone()[0],
        "locally_usable_research_or_official_primary_datasets":conn.execute("SELECT count(*) FROM inventory_records WHERE harvest_status='BAIXADO_HARMONIZADO_LOCAL' AND source_id IN ('ORNL_DAAC','SFB_IFN','EMBRAPA_REDAPE')").fetchone()[0],
        "published_aggregate_records":conn.execute("SELECT count(*) FROM inventory_records WHERE record_type='published_aggregate'").fetchone()[0],
        "curated_public_dataset_records":conn.execute("SELECT count(*) FROM inventory_records WHERE record_type='public_dataset_catalog'").fetchone()[0],
        "source_count_snapshots":conn.execute("SELECT count(*) FROM inventory_records WHERE record_type='source_inventory_count_snapshot'").fetchone()[0],
        "records_by_status":{r[0]:r[1] for r in conn.execute("SELECT harvest_status,count(*) FROM inventory_records GROUP BY harvest_status")}}
    observed={}
    for row in conn.execute("SELECT record_id,metadata_json FROM inventory_records WHERE record_type='source_inventory_count_snapshot'"):
        detail=json.loads(row["metadata_json"] or "{}")
        observed[row["record_id"].removeprefix("source_metrics:")]=(detail.get("summary") or {})
    summary["observed_official_counts"]=observed
    snapshot_path=DATA/"national_inventory_source_metrics_v1.json"
    if snapshot_path.exists():
        full_snapshot=json.loads(snapshot_path.read_text(encoding="utf-8"))
        summary["cross_source_deduplication"]=full_snapshot.get("cross_source_deduplication",{})
    if own:conn.close()
    return summary


@lru_cache(maxsize=128)
def _cached_inventory_query(db_path, db_mtime_ns, db_size, biome, physiognomy,
                            uf, microregion, limit):
    """Bounded read-only SQL lookup; cache key tracks every catalog write."""
    path=Path(db_path).resolve()
    uri=path.as_uri()+"?mode=ro"
    conn=sqlite3.connect(uri,uri=True,timeout=2.0)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    where=[]; params=[]
    for column,value in (("biome",biome),("physiognomy",physiognomy),
                         ("uf",uf),("microregion",microregion)):
        if value:
            where.append(f"({column} IS NULL OR {column}=?)"); params.append(value)
    sql="SELECT * FROM inventory_records"
    if where: sql+=" WHERE "+" AND ".join(where)
    sql+=" ORDER BY source_priority IS NULL,source_priority,record_id LIMIT ?"
    params.append(limit)
    rows=[dict(row) for row in conn.execute(sql,params)]
    conn.close()
    return tuple(rows)


def query_inventory_candidates(path=DEFAULT_DB, *, biome=None, physiognomy=None,
                               uf=None, microregion=None, limit=50):
    """Fetch a small, relevant catalog slice on demand (never a carbon estimate).

    This API is intentionally read-only. It returns source records for review;
    numeric use still requires the evidence and eligibility checks above.
    """
    db=Path(path).resolve()
    if not db.is_file(): return []
    limit=max(1,min(int(limit),200))
    values=tuple(str(v).strip() if v else None for v in
                 (biome,physiognomy,uf,microregion))
    stat=db.stat()
    rows=_cached_inventory_query(str(db),stat.st_mtime_ns,stat.st_size,*values,limit)
    return [dict(row) for row in rows]


def rank_inventory_candidates(candidates:Iterable[dict], *, biome:str, physiognomy:str,
                              longitude:float|None=None, latitude:float|None=None,
                              microregion:str|None=None, region:str|None=None):
    """Rank exact-physiognomy sources by evidence quality and proximity.

    Open institutionally recognized plots lead, followed by recognized published
    aggregates. An agency inventory is a last resort when the attachment,
    source hash, method/units, and acceptance evidence are verified. By owner
    decision, an approved SINAFLOR PMFS establishes acceptance of its
    underlying inventory; the exact source document and approval reference
    must still be retrievable. Administrative summaries are never plot data.
    Agency records are never promoted to SAR calibration.
    """
    b,p=_norm(biome),_norm(physiognomy)
    eligible=[]
    for row in candidates:
        if _norm(row.get("biome")) not in (b,"*") or _norm(row.get("physiognomy"))!=p:
            continue
        x,y=row.get("longitude"),row.get("latitude")
        distance=None
        try:
            if longitude is not None and latitude is not None and x is not None and y is not None:
                phi1,phi2=math.radians(float(latitude)),math.radians(float(y))
                dphi=phi2-phi1; dlambda=math.radians(float(x)-float(longitude))
                a=math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                distance=6371.0088*2*math.asin(min(1,math.sqrt(a)))
        except (TypeError,ValueError,OverflowError):
            distance=None
        level=str(row.get("data_level") or "")
        open_plot=bool(row.get("open_data")) and level in {
            "primary_tree","primary_plot","primary_or_supplementary"} and bool(row.get("georeferenced"))
        metric=row.get("structural_metrics") or {}
        center=metric.get("center",row.get("published_mean")) if isinstance(metric,dict) else row.get("published_mean")
        try:center_ok=center is not None and math.isfinite(float(center))
        except (TypeError,ValueError,OverflowError):center_ok=False
        evidence=str(row.get("record_type") or row.get("data_level") or "")
        aggregate=(evidence=="published_aggregate" or level=="published_aggregate")
        trusted_aggregate=aggregate and bool(row.get("institution_recognized")) and center_ok
        checks=row.get("checks") if isinstance(row.get("checks"),dict) else {}
        method_verified=bool(row.get("method_and_units_verified") or checks.get("metodo_e_unidades_verificados"))
        sinaflor_pmfs_accepted=(
            str(row.get("source_id") or "")=="IBAMA_SINAFLOR"
            and bool(row.get("pmfs_approval_verified"))
            and bool(row.get("plan_approval_evidence_url"))
        )
        explicit_attachment_acceptance=bool(row.get("agency_inventory_acceptance_verified"))
        approved_license_inventory=(
            bool(row.get("environmental_approval_verified"))
            and bool(row.get("approval_evidence_url"))
            and bool(row.get("approval_source_official_verified"))
        )
        approved_process_acceptance=sinaflor_pmfs_accepted or approved_license_inventory
        acceptance_evidence=(bool(row.get("acceptance_evidence_url"))
            or approved_process_acceptance)
        document_hash=str(row.get("inventory_document_sha256") or "").strip().lower()
        document_hash_ok=(len(document_hash)==64 and all(c in "0123456789abcdef" for c in document_hash))
        official_inventory_repository=bool(row.get("inventory_document_official_repository_verified"))
        accepted_agency=((explicit_attachment_acceptance or approved_process_acceptance) and center_ok
            and bool(row.get("inventory_document_url")) and document_hash_ok and official_inventory_repository
            and acceptance_evidence and method_verified
            and (approved_process_acceptance or bool(checks.get("aceite_expresso_do_inventario_anexo", True))))
        use=("PARCELA_ABERTA_PARA_ESTRUTURA" if open_plot else
             "MEDIA_PUBLICADA_TOTALIZADA_REFERENCIA_REGIONAL" if trusted_aggregate else
             "INVENTARIO_ANEXO_ACEITO_REFERENCIA_DE_ULTIMO_NIVEL" if accepted_agency else
             "TRIAGEM_SEM_USO_QUANTITATIVO")
        eligible.append({**row,"distance_km":distance,"open_georeferenced_plot_data":open_plot,
                         "published_totalized_reference":trusted_aggregate,
                         "verified_accepted_agency_inventory":accepted_agency,
                         "selection_use":use,
                         "selection_priority":1 if open_plot else 2 if trusted_aggregate else 3 if accepted_agency else 4})
    # Locality is resolved before source type: first use the same
    # microrregion/physiognomy; only if no such record exists widen to the
    # same physiognomy in the named region/biome. This prevents a nearby
    # incompatible formation from outranking a valid regional reference.
    if microregion:
        local=[r for r in eligible if _norm(r.get("microregion"))==_norm(microregion)]
        if local:
            eligible=local
            for row in eligible: row["geographic_scope"]="MICRORREGIAO"
        else:
            if region:
                regional=[r for r in eligible if _norm(r.get("region"))==_norm(region)
                          or _norm(r.get("macroregion"))==_norm(region)]
                if regional: eligible=regional
            for row in eligible: row["geographic_scope"]="REGIONAL_FALLBACK"
    else:
        for row in eligible: row["geographic_scope"]="REGIONAL_COMPATIBLE"
    eligible.sort(key=lambda r:(r["selection_priority"],
        r["distance_km"] if r["distance_km"] is not None else float("inf"),
        0 if r.get("model_eligible") else 1,str(r.get("record_id") or "")))
    return eligible


def discover_ckan_datasets(api_base:str, queries:Iterable[str], *, session=None,
                           rows:int=100, max_pages:int=30):
    """Paginated CKAN metadata discovery; no attachments downloaded here."""
    if session is None:
        try: import requests
        except ImportError as exc: raise RuntimeError("requests ausente para descoberta CKAN") from exc
        session=requests.Session()
    found={}
    for query in queries:
        for page in range(max_pages):
            start=page*rows
            response=session.get(api_base.rstrip("/")+"/package_search",
                params={"q":query,"rows":rows,"start":start},timeout=(10,60))
            response.raise_for_status(); body=response.json()
            result=body.get("result",{})
            if body.get("success") is False:raise RuntimeError("CKAN rejeitou busca: "+query)
            items=result.get("results") or []; total=int(result.get("count") or 0)
            for item in items:
                key=str(item.get("id") or item.get("name") or "")
                if key:found[key]=item
            if not items or (total and start+len(items)>=total) or len(items)<rows:break
        else:
            raise RuntimeError(f"Busca CKAN incompleta para {query!r}; paginação excedeu {max_pages} páginas")
    return sorted(found.values(),key=lambda r:str(r.get("title") or r.get("name") or "").casefold())


def discover_sfb_ifn(session=None):
    return discover_ckan_datasets(SFB_CKAN,SFB_SEARCH_TERMS,session=session)


def register_discovered_records(path, source_id, records, *, source_url_key="url"):
    """Save discovered catalog records; all enter as unreviewed, non-model leads."""
    conn=_conn(path); now=_now(); added=0
    for item in records:
        rid=str(item.get("api_record_id") or item.get("id") or item.get("name") or item.get("persistent_id") or item.get("record_id") or "")
        if not rid:continue
        before=conn.total_changes
        conn.execute("""INSERT INTO inventory_records
          (record_id,source_id,title,record_type,data_level,open_data,georeferenced,
           dataset_url,harvest_status,evidence_status,model_eligible,source_priority,
           uncertainty_note,metadata_json,updated_utc)
          VALUES (?,?,?,?,?,0,0,?,'METADADO_DESCOBERTO_NAO_BAIXADO',
           'NAO_TRIADO_NAO_ELEGIVEL',0,4,?,?,?)
          ON CONFLICT(record_id) DO UPDATE SET title=excluded.title,
           dataset_url=excluded.dataset_url,metadata_json=excluded.metadata_json,
           updated_utc=excluded.updated_utc""",
          (f"{source_id}:{rid}",source_id,str(item.get("title") or item.get("name") or rid),
           "portal_lead","metadata",item.get(source_url_key) or item.get("url") or "",
           "Sem classificação científica; metadado de descoberta somente.",
           json.dumps(item,ensure_ascii=False),now))
        if conn.total_changes>before:added+=1
    conn.commit(); conn.close(); return added


def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser(description="Base nacional catalográfica de inventários florestais brasileiros")
    ap.add_argument("--db",default=str(DEFAULT_DB)); ap.add_argument("--discover-sfb",action="store_true")
    ap.add_argument("--discover-open-portals",action="store_true",
                    help="Busca metadados nas fontes hierarquizadas (IFN/SFB, IBAMA, Embrapa, repositórios acadêmicos e Zenodo) e grava um manifesto; não promove anexos")
    ap.add_argument("--output-library",default="Enform_Verde_Biblioteca_Inventarios",
                    help="Pasta de saída para manifesto, catálogo pesquisável e índice HTML de links")
    ap.add_argument("--summary",action="store_true")
    args=ap.parse_args(argv)
    summary=initialize_database(args.db,seed=True)
    if args.discover_open_portals:
        try:
            from inventory_source_access import collect_hierarchical_sources
            result=collect_hierarchical_sources(args.output_library)
            summary["hierarchical_source_discovery"]={
                "status":"OK","machine_discovered_count":result.get("machine_discovered_count"),
                "catalog_leads_registered":result.get("catalog_leads_registered"),
                "runs":result.get("runs"),"output":args.output_library}
        except Exception as exc:
            summary["hierarchical_source_discovery"]={"status":"ERROR",
                "error":type(exc).__name__+": "+str(exc)[:300]}
    elif args.discover_sfb:
        outcomes={}
        routes=[("SFB_IFN",discover_sfb_ifn)]
        for source_id,discover in routes:
            try:
                records=discover()
                added=register_discovered_records(args.db,source_id,records)
                outcomes[source_id]={"status":"OK","datasets_discovered":len(records),"catalog_records_inserted":added}
            except Exception as exc:
                outcomes[source_id]={"status":"ERROR","error":type(exc).__name__+": "+str(exc)[:300]}
        summary=initialize_database(args.db,seed=False)
        summary["discovery_runs"]=outcomes
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
