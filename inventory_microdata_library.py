"""Validated summaries of tree-level inventory data bundled with Enform Verde.

Summaries preserve whether observations are georeferenced and whether plot
area is known. They never manufacture coordinates, area-normalized metrics,
SAR pairs, or fitophysiognomy assignments.
"""
from __future__ import annotations

import csv
import hashlib
from functools import lru_cache
import math
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "microdados_inventarios_harmonizados_v1.csv"
OFFICIAL_DB = Path(__file__).resolve().parent / "data" / "national_inventory_microdata_v1.sqlite"
REQUIRED = {
    "inventory_id", "plot_id", "tree_id", "dbh_cm", "height_m", "species",
    "status", "inventory_mass_kg_tree", "plot_georeferenced",
    "sar_pair_available", "data_source",
}

# Mexiana plot area is documented in the project history (25 x 10 m). Jalapão
# plot area is not present in the source evidence and is intentionally unset.
INVENTORY_CONTEXT = {
    "MX_SANTO_AMBROSIO_2025": {
        "site": "Fazenda Santo Ambrósio, Ilha Mexiana, Pará",
        "biome": "Amazônia",
        "physiognomy_scope": "Floresta Ombrófila Densa Aluvial e de Terras Baixas, agregado; sem classe atribuída por parcela",
        "plot_area_m2": 250.0,
        "plot_area_evidence": "Histórico do projeto: parcelas de 25 x 10 m",
        "regional_reference_scope": "Várzea estuarina da foz do Amazonas; referência estrutural regional indicada pelo proprietário",
        "limitation": "Parcelas sem coordenadas; AGB alométrica; sem pares parcela-pixel SAR; excluir savanas e campos; não separar FOD aluvial de terras baixas por parcela.",
    },
    "CE_JALAPAO_FOREST_2026": {
        "site": "Jalapão, Tocantins",
        "biome": "Cerrado",
        "physiognomy_scope": "Floresta, subtipo IBGE não resolvido",
        "plot_area_m2": None,
        "plot_area_evidence": None,
        "regional_reference_scope": "Referência de campo local; sem transferência automática para uma classe IBGE específica",
        "limitation": "Área das parcelas não confirmada; não calcular por hectare; sem coordenadas nem pares SAR; manter identificadores de parcela e árvores como observações de campo.",
    },
}


def load_inventory_tree_records(path: str | Path = DATA) -> tuple[list[dict], str]:
    """Load source rows, rejecting duplicate trees and malformed measurements."""
    source = Path(path)
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or ())
        if not REQUIRED.issubset(columns):
            raise ValueError("microbase lacks required provenance/measurement columns")
        rows = list(reader)
    if not rows:
        raise ValueError("microbase is empty")
    seen = set()
    for i, row in enumerate(rows, start=2):
        key = (row["inventory_id"], row["tree_id"])
        if not key[0]:
            raise ValueError(f"missing inventory identity at row {i}")
        if key[1]:
            if key in seen:
                raise ValueError(f"duplicate inventory/tree identity at row {i}")
            seen.add(key)
        for field in ("dbh_cm",):
            try:
                value = float(row[field])
            except (TypeError, ValueError):
                raise ValueError(f"invalid {field} at row {i}") from None
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"nonpositive or nonfinite {field} at row {i}")
        mass=row.get("inventory_mass_kg_tree","").strip()
        if mass:
            try:value=float(mass)
            except (TypeError,ValueError):raise ValueError(f"invalid inventory_mass_kg_tree at row {i}") from None
            if not math.isfinite(value) or value<0:
                raise ValueError(f"negative or nonfinite inventory_mass_kg_tree at row {i}")
        elif row["inventory_id"]=="MX_SANTO_AMBROSIO_2025":
            raise ValueError(f"missing allometric biomass value at row {i}")
        if row["inventory_id"] not in INVENTORY_CONTEXT:
            raise ValueError("unregistered inventory_id in bundled microbase")
    return rows, digest


def summarize_inventory_microdata(path: str | Path = DATA) -> dict:
    """Return source-level and plot-level summaries without spatial inference."""
    rows, digest = load_inventory_tree_records(path)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["inventory_id"]].append(row)
    outputs = {}
    for inventory_id, trees in sorted(grouped.items()):
        context = dict(INVENTORY_CONTEXT[inventory_id])
        by_plot: dict[str, list[dict]] = defaultdict(list)
        diameters = []
        heights = []
        species = Counter()
        living = []
        for row in trees:
            if row["plot_id"].strip():
                by_plot[row["plot_id"]].append(row)
            dbh = float(row["dbh_cm"])
            diameters.append(dbh)
            if row["height_m"].strip():
                height = float(row["height_m"])
                if math.isfinite(height) and height > 0:
                    heights.append(height)
            if row["species"].strip() and row["status"].casefold() == "alive":
                species[row["species"].strip()] += 1
            if row["status"].casefold() == "alive":
                living.append(row)
        plot_summaries = []
        plot_area_ha = (context["plot_area_m2"] / 10_000
                        if context["plot_area_m2"] else None)
        for plot_id, stems in sorted(by_plot.items(), key=lambda item: float(item[0])):
            ba_m2 = sum(math.pi * (float(stem["dbh_cm"]) / 200) ** 2 for stem in stems)
            mass_kg = sum(float(stem["inventory_mass_kg_tree"] or 0) for stem in stems)
            plot = {
                "plot_id": plot_id,
                "tree_count": len(stems),
                "mean_dbh_cm": sum(float(stem["dbh_cm"]) for stem in stems) / len(stems),
                "mean_height_m": (sum(float(stem["height_m"]) for stem in stems if stem["height_m"].strip())
                                  / sum(bool(stem["height_m"].strip()) for stem in stems)
                                  if any(stem["height_m"].strip() for stem in stems) else None),
                "plot_georeferenced": False,
                "sar_pair_available": False,
            }
            if plot_area_ha:
                plot.update({
                    "stems_ha": len(stems) / plot_area_ha,
                    "basal_area_m2_ha": ba_m2 / plot_area_ha,
                    "agb_allometric_mg_ha": mass_kg / 1000 / plot_area_ha,
                })
            else:
                plot.update({"stems_ha": None, "basal_area_m2_ha": None,
                             "agb_allometric_mg_ha": None})
            plot_summaries.append(plot)
        outputs[inventory_id] = {
            **context,
            "inventory_id": inventory_id,
            "tree_record_count": len(trees),
            "living_tree_count": len(living),
            "plot_count": len(by_plot),
            "tree_rows_without_plot_id": sum(not row["plot_id"].strip() for row in trees),
            "height_measurement_count": len(heights),
            "plot_georeferenced": False,
            "sar_pair_available": False,
            "source_dataset_sha256": digest,
            "diameter_sample_mean_cm": sum(diameters) / len(diameters),
            "height_sample_mean_m": sum(heights) / len(heights) if heights else None,
            "top10_species_by_stem_count": species.most_common(10),
            "plot_summaries": plot_summaries,
            "area_normalized_metrics_available": bool(plot_area_ha),
            "limitation": context["limitation"],
        }
        if plot_area_ha and plot_summaries:
            outputs[inventory_id]["mean_plot_stems_ha"] = sum(p["stems_ha"] for p in plot_summaries) / len(plot_summaries)
            outputs[inventory_id]["mean_plot_basal_area_m2_ha"] = sum(p["basal_area_m2_ha"] for p in plot_summaries) / len(plot_summaries)
            outputs[inventory_id]["mean_plot_agb_allometric_mg_ha"] = sum(p["agb_allometric_mg_ha"] for p in plot_summaries) / len(plot_summaries)
            outputs[inventory_id]["agb_kind"] = "AGB allométrica fornecida na planilha; não medida destrutiva"
        else:
            outputs[inventory_id]["mean_plot_stems_ha"] = None
            outputs[inventory_id]["mean_plot_basal_area_m2_ha"] = None
            outputs[inventory_id]["mean_plot_agb_allometric_mg_ha"] = None
            outputs[inventory_id]["agb_kind"] = "N/D — área amostral não confirmada"
    return {
        "source_dataset_sha256": digest,
        "tree_record_count": len(rows),
        "distinct_inventory_count": len(outputs),
        "inventories": outputs,
    }


def query_official_inventory_measurements(*, uf: str | None = None,
        biome: str | None = None, municipality: str | None = None,
        species: str | None = None, dbh_min_cm: float | None = None,
        dbh_max_cm: float | None = None, bbox: tuple[float, float, float, float] | None = None,
        limit: int = 200, db_path: str | Path = OFFICIAL_DB) -> list[dict]:
    """Query harvested official tree observations on demand, read-only and bounded.

    bbox is west,south,east,north and filters IFN sampling-unit centers, not
    individual tree positions. Results are source measurements, not expanded
    per-hectare estimates; the IFN design and expansion weights must be applied
    separately before population inference.
    """
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("IFN_MICRODATA_DB_NOT_AVAILABLE")
    safe_limit = max(1, min(int(limit), 200))
    clauses, params = [], []
    for field, value in (("uf", uf), ("biome", biome), ("municipality", municipality)):
        if value:
            clauses.append(f"{field} = ?")
            params.append(str(value).strip())
    if species:
        clauses.append("scientific_name LIKE ?")
        params.append(f"%{str(species).strip()}%")
    if dbh_min_cm is not None:
        clauses.append("dbh_cm >= ?")
        params.append(float(dbh_min_cm))
    if dbh_max_cm is not None:
        clauses.append("dbh_cm <= ?")
        params.append(float(dbh_max_cm))
    if bbox is not None:
        west, south, east, north = map(float, bbox)
        if west > east or south > north:
            raise ValueError("invalid bbox order")
        clauses.extend(("ua_center_lon BETWEEN ? AND ?", "ua_center_lat BETWEEN ? AND ?"))
        params.extend((west, east, south, north))
    sql = "SELECT * FROM ifn_dap10_observation"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY uf, ua_id, subunit, subplot, source_row_number LIMIT ?"
    params.append(safe_limit)
    uri = path.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=3) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return [dict(row) for row in conn.execute(sql, params)]


def _norm_label(value: str | None) -> str:
    text=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(c for c in text if c.isalnum() and not unicodedata.combining(c))


@lru_cache(maxsize=8)
def _official_inventory_database_status_cached(path_text: str, size_bytes: int, mtime_ns: int) -> dict:
    """Report whether tree data and verified IBGE unit crosswalk are present."""
    path=Path(path_text)
    if not path.is_file():
        return {"status":"N/D","available":False,
                "reason":"IFN_MICRODATA_DB_NOT_AVAILABLE","operational_for_tree_selection":False}
    try:
        with sqlite3.connect(f"file:{path}?mode=ro",uri=True,timeout=5) as conn:
            observations=conn.execute("SELECT COUNT(*) FROM ifn_dap10_observation").fetchone()[0]
            units=conn.execute("SELECT COUNT(*) FROM ifn_sampling_unit_summary").fetchone()[0]
            tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "ifn_sampling_unit_ibge_crosswalk" not in tables:
                return {"status":"INCOMPLETO","available":True,"observation_rows":observations,
                        "sampling_units":units,"reason":"IFN_IBGE_PHYSIOGNOMY_CROSSWALK_NOT_AVAILABLE",
                        "operational_for_tree_selection":False}
            crosswalk=conn.execute("SELECT COUNT(*) FROM ifn_sampling_unit_ibge_crosswalk WHERE match_status='MATCH_UNICO_PONTO_INTERIOR'").fetchone()[0]
            source_files=conn.execute("SELECT COUNT(DISTINCT source_file) FROM ifn_dap10_observation").fetchone()[0]
            source_hashes=conn.execute("SELECT COUNT(DISTINCT source_sha256) FROM ifn_dap10_observation").fetchone()[0]
        expected_rows,expected_units,expected_files=841387,8951,27
        ready=(observations==expected_rows and units==expected_units and
               crosswalk==expected_units and source_files==expected_files and source_hashes==expected_files)
        return {"status":"PRONTO_PARA_SELECAO_DE_REFERENCIAS" if ready else "INCOMPLETO_OU_DIVERGENTE","available":True,
                "observation_rows":observations,"sampling_units":units,
                "source_workbooks":source_files,"source_workbook_hashes":source_hashes,
                "ibge_unique_unit_matches":crosswalk,"expected_observation_rows":expected_rows,
                "expected_sampling_units":expected_units,
                "operational_for_tree_selection":ready,
                "agb_or_canopy_height_estimator_available":False,
                "reason":None if ready else "IFN_COUNTS_SOURCE_HASHES_OR_IBGE_CROSSWALK_DID_NOT_MEET_EXPECTED_CONTRACT"}
    except sqlite3.Error as exc:
        return {"status":"ERRO_LEITURA","available":True,
                "reason":"IFN_DB_SCHEMA_OR_READ_ERROR:"+type(exc).__name__,
                "operational_for_tree_selection":False}


def official_inventory_database_status(db_path: str | Path = OFFICIAL_DB) -> dict:
    """Check the large IFN database once per file version, then reuse its audit.

    The database is immutable during an analysis. Keying the cache by absolute
    path, size and nanosecond mtime invalidates it after a replacement/update,
    while avoiding repeated full-table COUNT scans in one desktop session.
    """
    path=Path(db_path).resolve()
    if not path.is_file():
        return {"status":"N/D","available":False,
                "reason":"IFN_MICRODATA_DB_NOT_AVAILABLE","operational_for_tree_selection":False}
    stat=path.stat()
    result=_official_inventory_database_status_cached(str(path),stat.st_size,stat.st_mtime_ns)
    return dict(result)


def select_official_inventory_units(*, biome: str, physiognomy: str,
        longitude: float, latitude: float, max_distance_km: float = 250.0,
        max_units: int = 5, include_trees: bool = True,
        db_path: str | Path = OFFICIAL_DB) -> dict:
    """Select nearest unique IFN sampling units by exact biome and IBGE legenda_1.

    Distance is from the IFN sampling-unit center. Tree records inherit that
    center only for candidate selection; they are never represented as
    individually georeferenced. Returned measurements are raw sampled trees,
    not per-hectare estimates and not an AGB estimate.
    """
    path=Path(db_path).resolve()
    if not path.is_file():
        return {"status":"N/D","reason":"IFN_MICRODATA_DB_NOT_AVAILABLE","units":[],"trees":[]}
    try:
        lon,lat,radius=float(longitude),float(latitude),float(max_distance_km)
        if not all(math.isfinite(v) for v in (lon,lat,radius)) or not -180<=lon<=180 or not -90<=lat<=90 or radius<=0:
            raise ValueError("invalid target coordinate or search radius")
    except (TypeError,ValueError,OverflowError) as exc:
        return {"status":"N/D","reason":"INVALID_SELECTION_LOCATION_OR_RADIUS","diagnostic":type(exc).__name__,"units":[],"trees":[]}
    with sqlite3.connect(f"file:{path}?mode=ro",uri=True,timeout=5) as conn:
        conn.row_factory=sqlite3.Row
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "ifn_sampling_unit_ibge_crosswalk" not in tables:
            return {"status":"N/D","reason":"IFN_IBGE_PHYSIOGNOMY_CROSSWALK_NOT_AVAILABLE","units":[],"trees":[]}
        # The composite crosswalk index starts with source_biome and legenda_1.
        # Use an exact indexed lookup for the common case so the 466 MiB tree
        # table is touched only for the selected units. If a caller supplies a
        # spelling/case variant, preserve the accent/case-insensitive matching
        # behavior through the narrower biome fallback and Python normalizer.
        records=conn.execute("""SELECT s.*, x.ibge_cd_fito, x.ibge_legenda_1, x.match_status,
                   x.source_url AS crosswalk_source, x.source_sha256 AS crosswalk_sha256
            FROM ifn_sampling_unit_summary s JOIN ifn_sampling_unit_ibge_crosswalk x
              ON x.ua_id=s.ua_id AND x.uf=s.uf
            WHERE x.source_biome=? AND x.ibge_legenda_1=?
              AND s.biome=? AND x.match_status='MATCH_UNICO_PONTO_INTERIOR'
              AND x.ibge_legenda_1 IS NOT NULL""",
            (str(biome).strip(),str(physiognomy).strip(),str(biome).strip())).fetchall()
        if not records:
            records=conn.execute("""SELECT s.*, x.ibge_cd_fito, x.ibge_legenda_1, x.match_status,
                       x.source_url AS crosswalk_source, x.source_sha256 AS crosswalk_sha256
                FROM ifn_sampling_unit_summary s JOIN ifn_sampling_unit_ibge_crosswalk x
                  ON x.ua_id=s.ua_id AND x.uf=s.uf
                WHERE s.biome=? AND x.match_status='MATCH_UNICO_PONTO_INTERIOR'
                  AND x.ibge_legenda_1 IS NOT NULL""",(str(biome).strip(),)).fetchall()
        target=_norm_label(physiognomy)
        candidates=[]
        for row in records:
            if _norm_label(row["ibge_legenda_1"])!=target:
                continue
            if row["ua_center_lon"] is None or row["ua_center_lat"] is None:
                continue
            p1,p2=math.radians(lat),math.radians(float(row["ua_center_lat"]))
            dp=p2-p1; dl=math.radians(float(row["ua_center_lon"])-lon)
            a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
            distance=6371.0088*2*math.asin(min(1.0,math.sqrt(a)))
            if distance<=radius:
                candidates.append((distance,dict(row)))
        candidates.sort(key=lambda item:(item[0],item[1]["uf"],item[1]["ua_id"]))
        candidates=candidates[:max(1,min(int(max_units),100))]
        if not candidates:
            return {"status":"N/D","reason":"NO_IFN_UNIT_MATCHES_LOCATION_BIOME_PHYSIOGNOMY_AND_RADIUS",
                    "units":[],"trees":[],"selection":{"biome":biome,"physiognomy":physiognomy,"radius_km":radius}}
        units=[]; trees=[]; dbh_values=[]; height_values=[]; sample_ba=0.0
        species_unit_counts=Counter(); species_tree_counts=Counter()
        bins={"10_20":0,"20_30":0,"30_40":0,"40_60":0,"60_plus":0}
        for distance,unit in candidates:
            unit["distance_km"]=distance
            units.append(unit)
            rows=conn.execute("""SELECT * FROM ifn_dap10_observation
                WHERE ua_id=? AND uf=? ORDER BY subunit,subplot,source_row_number""",
                (unit["ua_id"],unit["uf"])).fetchall()
            species_seen_in_unit=set()
            for row in rows:
                tree=dict(row)
                # Presence across independent UAs is the reported frequency;
                # stem counts are retained separately and never called frequency.
                taxon=(tree.get("scientific_name") or tree.get("verbatim_identification") or "").strip()
                taxon_key=_norm_label(taxon)
                if taxon_key and not any(x in taxon_key for x in ("indeterminad", "naoidentificad", "semidentificacao")):
                    species_seen_in_unit.add(taxon)
                    species_tree_counts[taxon]+=1
                dbh=tree.get("dbh_cm")
                if dbh is not None and float(dbh)>0:
                    d=float(dbh); dbh_values.append(d); sample_ba+=math.pi*(d/200.0)**2
                    bin_id="10_20" if d<20 else "20_30" if d<30 else "30_40" if d<40 else "40_60" if d<60 else "60_plus"
                    bins[bin_id]+=1
                height=tree.get("total_height_m")
                if height is not None and float(height)>0: height_values.append(float(height))
                if include_trees:
                    tree["sampling_unit_distance_km"]=distance
                    tree["tree_coordinate_interpretation"]="UA_CENTER_ONLY_NOT_INDIVIDUAL_TREE_COORDINATE"
                    trees.append(tree)
            for taxon in species_seen_in_unit:
                species_unit_counts[taxon]+=1
    db_status=official_inventory_database_status(path)
    selected_unit_count=max(1,len(units))
    top_species=sorted(species_unit_counts,
        key=lambda name:(-species_unit_counts[name],-species_tree_counts[name],name.casefold()))[:10]
    biodiversity={"status":"INDICADOR_FITOSSOCIOLOGICO_IFN" if top_species else "N/D",
        "definition":"frequência absoluta = UAs compatíveis com a espécie / UAs selecionadas × 100; n de indivíduos apresentado separadamente",
        "n_unique_sampling_units":len(units),"n_tree_records_with_taxon":sum(species_tree_counts.values()),
        "unique_taxa_observed":len(species_unit_counts),
        "top_10_species_by_sampling_unit_frequency":[{
            "rank":i+1,"species":name,"sampling_units_present":species_unit_counts[name],
            "frequency_pct":100.0*species_unit_counts[name]/selected_unit_count,
            "tree_records":species_tree_counts[name]}
            for i,name in enumerate(top_species)],
        "limitations":["IFN DAP10 selecionado por proximidade, bioma e legenda_1 IBGE; não é censo de toda a região",
            "frequência entre UAs não equivale a abundância relativa nem a índice completo de biodiversidade",
            "uma UA representa a unidade amostral; não atribuir coordenadas individuais às árvores"]}
    return {"status":"SELECAO_IFN_POR_LOCALIZACAO_BIOMA_FITOFISIONOMIA",
        "selection":{"biome":biome,"physiognomy":physiognomy,"target_longitude":lon,
            "target_latitude":lat,"radius_km":radius,"selected_unique_units":len(units),
            "source":"IFN/DAP10 + IBGE Vegetação 2026 legenda_1",
            "crosswalk_method":"ponto interior único do centro da unidade amostral"},
        "database_status":db_status,"units":units,"trees":trees,
        "biodiversity_reference":biodiversity,
        "raw_tree_sample_summary":{"tree_record_count":len(dbh_values),
            "mean_dbh_cm":sum(dbh_values)/len(dbh_values) if dbh_values else None,
            "mean_individual_tree_height_m":sum(height_values)/len(height_values) if height_values else None,
            "observed_sample_basal_area_m2":sample_ba,
            "dbh_class_tree_counts":bins,
            "warning":"amostra bruta das árvores selecionadas; não é densidade por hectare nem estimativa da AOI"},
        "interpretation":"DAP/HT são medições de árvore em unidades amostrais. Sem aplicar desenho amostral/expansão e equação compatível, não são métricas por hectare nem AGB da AOI; altura de árvore não substitui altura média do dossel SAR."}


def query_ief_mg_equations(*, physiognomy: str | None = None,
        region_code: str | None = None, limit: int = 50,
        db_path: str | Path = OFFICIAL_DB) -> list[dict]:
    """Return published IEF-MG dry-matter equations for review, never auto-apply.

    A returned equation is eligible only after matching the original
    physiognomy, regional basin, measured inputs, output component and
    retransformation treatment described in the source.
    """
    import sqlite3
    path = Path(db_path).resolve()
    if not path.is_file():
        return []
    safe_limit = max(1, min(int(limit), 200))
    clauses, params = [], []
    for field, value in (("physiognomy", physiognomy), ("region_code", region_code)):
        if value:
            clauses.append(f"{field} LIKE ?")
            params.append(f"%{str(value).strip()}%")
    sql = "SELECT * FROM ief_mg_published_equation"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY physiognomy, region_code, source_id LIMIT ?"
    params.append(safe_limit)
    uri = path.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=3) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return [dict(row) for row in conn.execute(sql, params)]

