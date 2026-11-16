"""Validated summaries of tree-level inventory data bundled with Enform Verde.

Summaries preserve whether observations are georeferenced and whether plot
area is known. They never manufacture coordinates, area-normalized metrics,
SAR pairs, or fitophysiognomy assignments.
"""
from __future__ import annotations

import csv
import hashlib
import math
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
    import sqlite3
    path = Path(db_path).resolve()
    if not path.is_file():
        return []
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

