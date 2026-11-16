#!/usr/bin/env python3
"""Build an indexed, provenance-preserving SQLite store for official inventory sources.

IFN DAP10 workbooks are primary measurement records. SINAFLOR POA rows are
sanitized operational/species-volume aggregates and are intentionally kept in
a distinct table and evidence class.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_IFN = DATA / "external_raw" / "ifn_dap10_set2025"
IFN_MANIFEST = DATA / "ifn_dap10_set2025_harvest_manifest.json"
DB_PATH = DATA / "national_inventory_microdata_v1.sqlite"
SINAFLOR_URL = (
    "https://stibamadadosabertosprd.blob.core.windows.net/"
    "dados-abertos/dados/SINAFLOR/poa/OutrosBiomas/poaOutrosBiomas.csv"
)
SINAFLOR_DATASET = "https://dadosabertos.ibama.gov.br/dataset/sinaflor-poa-outros-biomas"

IFN_FIELDS = {
    "Lotes": "lot_code", "UA": "ua_id", "bioma": "biome", "uf": "uf",
    "mun": "municipality", "lon_pc": "ua_center_lon", "lat_pc": "ua_center_lat",
    "Subunidade": "subunit", "Subparcela": "subplot", "Data": "measurement_date",
    "Sem_arvores_na_UA": "ua_no_trees", "Narv": "tree_number",
    "Nfuste": "stem_number", "Codigo_medicao": "measurement_code",
    "Especie_campo": "field_species", "Codigo_Coleta": "collection_code",
    "Nivel": "taxonomic_identification_level", "DAP": "dbh_cm", "DB1": "dbh_axis1_cm",
    "DB2": "dbh_axis2_cm", "SA": "sociological_position", "QF": "stem_quality",
    "PS": "stem_position", "AFF": "tree_form_code", "HT": "total_height_m",
    "HF": "commercial_height_m", "PL": "liana_code", "HM": "merchantable_height_m",
    "HAB": "habitat_code", "Obs": "field_observation", "Tocos": "stump_code",
    "MB": "dead_or_broken_code", "DAP_GRUPO": "dbh_threshold_group",
    "verbatimIdentification": "verbatim_identification", "id_FFB": "id_ffb",
    "id_POWO": "id_powo", "family": "family", "genus": "genus",
    "specificEpithet": "specific_epithet", "infraspecificEpithet": "infraspecific_epithet",
    "scientificName": "scientific_name", "taxonRank": "taxon_rank",
    "venacularName": "vernacular_name", "Codigo_coleta": "collection_id",
}
NUMERIC = {
    "ua_center_lon", "ua_center_lat", "tree_number", "stem_number", "dbh_cm",
    "dbh_axis1_cm", "dbh_axis2_cm", "total_height_m", "commercial_height_m",
    "merchantable_height_m", "id_ffb", "id_powo",
}
SINAFLOR_FIELDS = [
    "NRO_REGISTRO", "DATA_DE_EMISSAO", "NRO_AUTORIZACAO", "NRO_AUTORIZACAO_ORIGINAL",
    "NRO_AUTORIZACAO_PMFS_VINCULADO", "DATA_DE_VALIDADE", "UF", "MUNICIPIO",
    "LATITUDE_EMPREENDIMENTO", "LONGITUDE_EMPREENDIMENTO", "ATIVIDADE",
    "TIPO_DE_EMPREENDIMENTO", "COMPETENCIA_AVALIACAO", "ORGAO_AMBIENTAL_RESP_ANALISE",
    "AREA_MANEJO_FLORESTAL", "NRO_UPA", "AREA_UPA", "LATITUDE_UPA", "LONGITUDE_UPA",
    "METODO_INVENTARIO", "PRODUTO", "NOME_CIENTIFICO", "NOME_POPULAR", "VOLUME",
    "EQUACAO_VOLUME", "SITUACAO", "DATA_DA_SITUACAO", "ULTIMO_TRAMITE",
    "DATA_DO_TRAMITE", "ULTIMA_ATUALIZACAO_RELATORIO",
]
PII_COLUMNS = {
    "NOME_DETENTOR", "CPF_CNPJ_DETENTOR", "IMOVEL_RURAL_VINCULADO",
    "NRO_CAR_IMOVEL_RURAL", "NOME_EMPREENDIMENTO_VINC", "NOME_DO_RT", "NRO_ART",
    "NATUREZA_JURIDICA",
}


def _num(value):
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            number = float(text)
        except ValueError:
            return None
    return number if math.isfinite(number) else None


def _hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _date_iso(value):
    if value is None:
        return None
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def _schema(conn):
    conn.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    CREATE TABLE IF NOT EXISTS source_dataset(
      dataset_id TEXT PRIMARY KEY, institution TEXT NOT NULL, title TEXT NOT NULL,
      source_url TEXT NOT NULL, retrieved_at_utc TEXT NOT NULL, release_label TEXT,
      license TEXT, record_grain TEXT NOT NULL, row_count INTEGER NOT NULL,
      unit_count INTEGER, distinct_authorization_count INTEGER,
      source_sha256 TEXT, interpretation TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ifn_dap10_observation(
      source_row_id TEXT PRIMARY KEY, source_file TEXT NOT NULL, source_sha256 TEXT NOT NULL,
      source_row_number INTEGER NOT NULL, lot_code TEXT, ua_id TEXT, biome TEXT, uf TEXT,
      municipality TEXT, ua_center_lon REAL, ua_center_lat REAL, subunit INTEGER,
      subplot INTEGER, measurement_date TEXT, ua_no_trees TEXT, tree_number INTEGER,
      stem_number INTEGER, measurement_code TEXT, field_species TEXT, collection_code TEXT,
      taxonomic_identification_level TEXT, dbh_cm REAL, dbh_axis1_cm REAL, dbh_axis2_cm REAL,
      sociological_position TEXT, stem_quality TEXT, stem_position TEXT, tree_form_code TEXT,
      total_height_m REAL, commercial_height_m REAL, liana_code TEXT,
      merchantable_height_m REAL, habitat_code TEXT, field_observation TEXT,
      stump_code TEXT, dead_or_broken_code TEXT, dbh_threshold_group TEXT,
      verbatim_identification TEXT, id_ffb INTEGER, id_powo INTEGER, family TEXT, genus TEXT,
      specific_epithet TEXT, infraspecific_epithet TEXT, scientific_name TEXT, taxon_rank TEXT,
      vernacular_name TEXT, collection_id TEXT
    );
    CREATE TABLE IF NOT EXISTS ifn_sampling_unit_summary(
      ua_id TEXT NOT NULL, uf TEXT NOT NULL, lot_code TEXT, biome TEXT, municipality TEXT,
      ua_center_lon REAL, ua_center_lat REAL, first_measurement_date TEXT, last_measurement_date TEXT,
      observation_count INTEGER NOT NULL, distinct_subunit_subplot_count INTEGER NOT NULL,
      distinct_taxon_count INTEGER, mean_dbh_cm REAL, mean_total_height_m REAL,
      summed_sample_basal_area_m2 REAL,
      PRIMARY KEY(ua_id,uf)
    );
    CREATE TABLE IF NOT EXISTS sinaflor_poa_aggregate(
      source_row_id TEXT PRIMARY KEY, register_id TEXT, issuance_date TEXT, authorization_id TEXT,
      original_authorization_id TEXT, linked_pmfs_authorization_id TEXT, validity_date TEXT,
      uf TEXT, municipality TEXT, enterprise_latitude REAL, enterprise_longitude REAL,
      activity TEXT, enterprise_type TEXT, evaluation_competence TEXT, analysis_agency TEXT,
      management_area_ha REAL, upa_id TEXT, upa_area_ha REAL, upa_latitude REAL, upa_longitude REAL,
      inventory_method TEXT, product TEXT, scientific_name TEXT, popular_name TEXT, volume_value REAL,
      volume_equation TEXT, situation TEXT, situation_date TEXT, latest_proceeding TEXT,
      proceeding_date TEXT, report_updated_at TEXT,
      evidence_class TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ief_mg_published_equation(
      source_id TEXT PRIMARY KEY, institution TEXT NOT NULL, biome TEXT, physiognomy TEXT,
      region_code TEXT, equation_type TEXT, model TEXT, equation TEXT, dbh_unit TEXT,
      height_unit TEXT, output_unit TEXT, r2_adjusted_percent REAL, syx_output_unit REAL,
      syx_percent REAL, mean_error_output_unit REAL, source_chapter_pages TEXT,
      region_definition TEXT, citation TEXT, official_index_url TEXT, downloaded_chapter_url TEXT,
      license_status TEXT, use_limit TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_ifn_uf_biome ON ifn_dap10_observation(uf,biome);
    CREATE INDEX IF NOT EXISTS idx_ifn_ua ON ifn_dap10_observation(ua_id,subunit,subplot);
    CREATE INDEX IF NOT EXISTS idx_ifn_location ON ifn_dap10_observation(ua_center_lat,ua_center_lon);
    CREATE INDEX IF NOT EXISTS idx_ifn_species ON ifn_dap10_observation(scientific_name);
    CREATE INDEX IF NOT EXISTS idx_sinaflor_location ON sinaflor_poa_aggregate(uf,municipality,upa_latitude,upa_longitude);
    CREATE INDEX IF NOT EXISTS idx_sinaflor_status ON sinaflor_poa_aggregate(situation);
    CREATE INDEX IF NOT EXISTS idx_sinaflor_auth ON sinaflor_poa_aggregate(authorization_id,upa_id,scientific_name);
    """)


def ingest_ifn(conn, manifest):
    workbook_meta = {x["filename"]: x for x in manifest["state_workbooks"]}
    insert_cols = [
        "source_row_id", "source_file", "source_sha256", "source_row_number", *IFN_FIELDS.values()
    ]
    query = f"INSERT OR REPLACE INTO ifn_dap10_observation ({','.join(insert_cols)}) VALUES ({','.join('?' for _ in insert_cols)})"
    n = 0
    summaries = defaultdict(lambda: {
        "obs": 0, "subplots": set(), "taxa": set(), "dbh_sum": 0.0, "dbh_n": 0,
        "height_sum": 0.0, "height_n": 0, "ba": 0.0, "date_min": None,
        "date_max": None, "static": None,
    })
    for filename, meta in sorted(workbook_meta.items()):
        path = RAW_IFN / filename
        if not path.is_file() or _hash(path) != meta["sha256"]:
            raise RuntimeError(f"IFN_SOURCE_HASH_MISMATCH:{filename}")
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = [str(x).strip() if x is not None else "" for x in next(rows)]
        if set(IFN_FIELDS) - set(header):
            raise RuntimeError(f"IFN_WORKBOOK_SCHEMA_MISMATCH:{filename}")
        indexes = {field: header.index(field) for field in IFN_FIELDS}
        batch = []
        for row_no, row in enumerate(rows, start=2):
            if not row or all(x is None for x in row):
                continue
            values = {}
            for official, canonical in IFN_FIELDS.items():
                value = row[indexes[official]]
                if canonical in NUMERIC:
                    value = _num(value)
                    if value is not None and canonical in {"tree_number", "stem_number", "id_ffb", "id_powo"}:
                        value = int(value)
                elif value is not None:
                    value = str(value).strip()
                values[canonical] = value
            uf = values["uf"] or Path(filename).stem.split("_")[2]
            ua = values["ua_id"] or ""
            source_id = f"IFN_DAP10_SET2025:{uf}:{row_no}"
            batch.append((source_id, filename, meta["sha256"], row_no,
                          *[values[k] for k in IFN_FIELDS.values()]))
            key = (ua, uf)
            s = summaries[key]
            s["obs"] += 1
            if values["subunit"] is not None or values["subplot"] is not None:
                s["subplots"].add((values["subunit"], values["subplot"]))
            if values["scientific_name"]:
                s["taxa"].add(values["scientific_name"])
            if values["dbh_cm"] and values["dbh_cm"] > 0:
                s["dbh_sum"] += values["dbh_cm"]
                s["dbh_n"] += 1
                s["ba"] += math.pi * (values["dbh_cm"] / 200.0) ** 2
            if values["total_height_m"] and values["total_height_m"] > 0:
                s["height_sum"] += values["total_height_m"]
                s["height_n"] += 1
            if values["measurement_date"]:
                date_value = _date_iso(values["measurement_date"])
                s["date_min"] = min(s["date_min"], date_value) if s["date_min"] else date_value
                s["date_max"] = max(s["date_max"], date_value) if s["date_max"] else date_value
            if s["static"] is None:
                s["static"] = {k: values[k] for k in (
                    "lot_code", "biome", "municipality", "ua_center_lon", "ua_center_lat")}
            if len(batch) >= 5000:
                conn.executemany(query, batch)
                batch.clear()
        if batch:
            conn.executemany(query, batch)
        wb.close()
        if ws.max_row - 1 != meta["row_count"]:
            raise RuntimeError(f"IFN_ROW_COUNT_MISMATCH:{filename}")
        conn.commit()
        print(f"ingested {filename}", flush=True)
    conn.execute("DELETE FROM ifn_sampling_unit_summary")
    summary_rows = []
    for (ua, uf), s in summaries.items():
        st = s["static"] or {}
        summary_rows.append((
            ua, uf, st.get("lot_code"), st.get("biome"), st.get("municipality"),
            st.get("ua_center_lon"), st.get("ua_center_lat"),
            s["date_min"], s["date_max"],
            s["obs"], len(s["subplots"]), len(s["taxa"]),
            s["dbh_sum"]/s["dbh_n"] if s["dbh_n"] else None,
            s["height_sum"]/s["height_n"] if s["height_n"] else None,
            s["ba"],
        ))
    conn.executemany("INSERT OR REPLACE INTO ifn_sampling_unit_summary VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",summary_rows)
    conn.commit()
    return {"observation_rows": sum(x["row_count"] for x in manifest["state_workbooks"]),
            "sampling_units": len(summaries), "units_summary_rows": len(summary_rows)}


def ingest_sinaflor(conn):
    import requests
    response = requests.get(SINAFLOR_URL, timeout=(10, 90))
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(text.splitlines(), delimiter=";")
    rows = list(reader)
    if not rows or len(rows[0]) < 10:
        reader = csv.DictReader(text.splitlines(), delimiter=",")
        rows = list(reader)
    if not rows or not set(SINAFLOR_FIELDS).issubset(set(rows[0])):
        raise RuntimeError("SINAFLOR_POA_SCHEMA_MISMATCH")
    if not PII_COLUMNS.isdisjoint(SINAFLOR_FIELDS):
        raise RuntimeError("PII_FIELD_PRESENT_IN_PUBLIC_SINAFLOR_WHITELIST")
    conn.execute("DELETE FROM sinaflor_poa_aggregate")
    cols = [
        "source_row_id", "register_id", "issuance_date", "authorization_id",
        "original_authorization_id", "linked_pmfs_authorization_id", "validity_date", "uf",
        "municipality", "enterprise_latitude", "enterprise_longitude", "activity",
        "enterprise_type", "evaluation_competence", "analysis_agency", "management_area_ha",
        "upa_id", "upa_area_ha", "upa_latitude", "upa_longitude", "inventory_method",
        "product", "scientific_name", "popular_name", "volume_value", "volume_equation",
        "situation", "situation_date", "latest_proceeding", "proceeding_date",
        "report_updated_at", "evidence_class",
    ]
    field_to_col = dict(zip(SINAFLOR_FIELDS, cols[1:-1]))
    insert = f"INSERT INTO sinaflor_poa_aggregate ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})"
    status = Counter()
    auths_by_status = defaultdict(set)
    unique_auth = set()
    for i, row in enumerate(rows, start=2):
        values = []
        for field, col in field_to_col.items():
            value = (row.get(field) or "").strip()
            if col in {"enterprise_latitude", "enterprise_longitude", "upa_latitude", "upa_longitude",
                       "management_area_ha", "upa_area_ha", "volume_value"}:
                value = _num(value)
            values.append(value if value != "" else None)
        status_value = (row.get("SITUACAO") or "").strip()
        auth = (row.get("NRO_AUTORIZACAO") or "").strip()
        status[status_value] += 1
        if auth:
            unique_auth.add(auth)
            auths_by_status[status_value].add(auth)
        record_id = f"SINAFLOR_POA_OUTROS_BIOMAS:{i}"
        conn.execute(insert, (record_id, *values,
            "species_volume_operation_aggregate; not tree/plot microdata; no approval inferred"))
    conn.commit()
    sanitized_path = DATA / "sinaflor_poa_outros_biomas_sanitized_v1.csv"
    with sanitized_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SINAFLOR_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in SINAFLOR_FIELDS})
    return {
        "rows": len(rows), "distinct_authorizations": len(unique_auth),
        "distinct_register_ids": len({(r.get("NRO_REGISTRO") or "").strip() for r in rows if r.get("NRO_REGISTRO")}),
        "distinct_linked_pmfs": len({(r.get("NRO_AUTORIZACAO_PMFS_VINCULADO") or "").strip() for r in rows if r.get("NRO_AUTORIZACAO_PMFS_VINCULADO")}),
        "rows_by_situation": dict(status),
        "distinct_authorizations_by_situation": {k: len(v) for k, v in auths_by_status.items()},
        "raw_source_sha256": digest, "sanitized_csv": str(sanitized_path.relative_to(ROOT)),
        "pii_columns_removed": sorted(PII_COLUMNS),
    }


def ingest_ief_equations(conn):
    path = DATA / "ief_mg_2008_dry_matter_equations_v1.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"source_id", "equation", "physiognomy", "region_code", "use_limit"}
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("IEF_EQUATION_TABLE_SCHEMA_MISMATCH")
    cols = list(rows[0])
    conn.execute("DELETE FROM ief_mg_published_equation")
    query = f"INSERT INTO ief_mg_published_equation ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})"
    for row in rows:
        for key in ("r2_adjusted_percent", "syx_output_unit", "syx_percent", "mean_error_output_unit"):
            row[key] = _num(row.get(key))
        conn.execute(query, [row.get(key) for key in cols])
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ief_physiognomy_region ON ief_mg_published_equation(physiognomy,region_code)")
    conn.commit()
    return {"equation_count": len(rows), "source_pdf_sha256": _hash(DATA / "external_raw" / "ief_mg_2008" / "IEF_UFLA_2008_equacoes_peso_materia_seca_capitulo_III.pdf")}


def main():
    manifest = json.loads(IFN_MANIFEST.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    _schema(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM ifn_dap10_observation")
    conn.execute("DELETE FROM ifn_sampling_unit_summary")
    ifn_result = ingest_ifn(conn, manifest)
    ifn_result["biome_summary"] = [
        {"biome": row[0], "sampling_units": row[1], "observation_rows": row[2]}
        for row in conn.execute(
            "SELECT biome, COUNT(*), SUM(observation_count) "
            "FROM ifn_sampling_unit_summary GROUP BY biome ORDER BY biome")]
    sinaflor_result = ingest_sinaflor(conn)
    ief_result = ingest_ief_equations(conn)
    conn.execute("""INSERT OR REPLACE INTO source_dataset VALUES
      (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "IFN_DAP10_SET2025", "SFB/IFN", "Inventário Florestal Nacional — DAP ≥10 cm — 27 UFs",
        "https://dados.florestal.gov.br/dataset/ifn-dap-10-por-uf_disp-set2025", now,
        "recursos estaduais disponibilizados em setembro de 2025", manifest.get("license"),
        "tree/stem measurement records; sampled-unit coordinates", ifn_result["observation_rows"],
        ifn_result["sampling_units"], None, None,
        "One national IFN program; UF files are state partitions, not independent inventories. "
        "Coordinates identify sampling units, not tree positions. DAP and total height are field measurements; "
        "use the sampling design/expansion factors before population estimates."))
    conn.execute("""INSERT OR REPLACE INTO source_dataset VALUES
      (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "IBAMA_SINAFLOR_POA_OUTROS_BIOMAS", "IBAMA/SINAFLOR", "POA Outros Biomas — operação agregada",
        SINAFLOR_DATASET, now, "snapshot live conforme relatório público", "dados abertos IBAMA; verificar termos por recurso",
        "operation/species/product aggregate; not tree/plot measurements", sinaflor_result["rows"], None,
        sinaflor_result["distinct_authorizations"], sinaflor_result["raw_source_sha256"],
        "Sanitized public administrative records retain area, method, species/product, volume, location and status. "
        "Personal/property identifiers removed. No approval or inventory approval inferred from authorization status."))
    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    report = {
        "retrieved_at_utc": now, "database": str(DB_PATH.relative_to(ROOT)),
        "database_sha256": _hash(DB_PATH), "database_size_bytes": DB_PATH.stat().st_size,
        "ifn": {**ifn_result, "source_sha256_by_state": {
            x["filename"]: x["sha256"] for x in manifest["state_workbooks"]}},
        "sinaflor_poa": sinaflor_result,
        "ief_mg_2008_equations": ief_result,
        "interpretation": (
            "The IFN adds hundreds of thousands of primary DAP/height/species records in one nationally "
            "designed inventory program, not one separate inventory per UF. SINAFLOR adds process-linked "
            "species/volume aggregates and leads to underlying approved studies, not tree-level inventory data."
        ),
    }
    report_path = DATA / "official_inventory_microdata_ingestion_v1.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ifn": ifn_result, "sinaflor_poa": sinaflor_result, "ief_mg_2008_equations": ief_result,
                      "database_size_bytes": report["database_size_bytes"],
                      "database_sha256": report["database_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
