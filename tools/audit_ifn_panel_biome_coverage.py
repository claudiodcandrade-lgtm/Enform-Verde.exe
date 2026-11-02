#!/usr/bin/env python3
"""Audit real IFN 2026 biomass-panel coverage without promoting modeled rows.

Each row may be a subunit/equation estimate, not an independent plot. Distinct
physical UAs are counted by UF+UA, never by equation, typology or subunit.
No panel estimate is promoted to SAR validation, AOI carbon or an IC95.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

from tools.ifn_state_identity import canonical_state, canonical_ua

# Panel repeats UF and physical UA for many equations/subunits. Cache strict
# canonicalization, preserving rejection of malformed source identities.
canonical_state = lru_cache(maxsize=256)(canonical_state)
canonical_ua = lru_cache(maxsize=65536)(canonical_ua)

SOURCES = {
    "ifn_painel_biomassa_2026": "living_tree_agb_model_outputs",
    "ifn_painel_arvores_mortas_2026": "standing_dead_tree_model_outputs",
}
TARGET_BIOMES = ("Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal")
ALLOWED_BIOMES = set(TARGET_BIOMES) | {"Pampa"}
REQUIRED = {"bioma", "uf", "lon_pc", "lat_pc", "ua", "n_subunidades", "sanidade",
            "classe_uso_da_terra", "tipologia_da_vegetacao", "equacoes", "area_ha",
            "agb_media_kg_por_ha", "agb_variancia_por_ua", "valor_r"}
LICENSE_URL = "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono"


def _finite_nonnegative(value, field, line):
    try:
        number = float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {line}: invalid {field}") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"row {line}: invalid {field}")
    return number


def _coordinate(value, field, line):
    """Parse reported centroid coordinates; blank remains unresolved, not zero."""
    raw = str(value).strip()
    if not raw:
        return None
    try:
        coordinate = Decimal(raw.replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"row {line}: invalid {field}") from exc
    limit = Decimal(180 if field == "lon_pc" else 90)
    if not coordinate.is_finite() or not -limit <= coordinate <= limit:
        raise ValueError(f"row {line}: invalid {field}")
    return coordinate


def _screen(raw):
    stream = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig", newline="")
    reader = csv.DictReader(stream, delimiter=";", strict=True)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or any(not name or not name.strip() for name in fields):
        raise ValueError("duplicate or blank IFN panel CSV headers")
    if not REQUIRED.issubset(fields):
        raise ValueError("missing IFN panel columns")
    counts = Counter()
    units = defaultdict(set)
    typology_units = defaultdict(set)
    equations_by_ua = defaultdict(set)
    typologies_by_ua = defaultdict(set)
    biomes_by_ua = defaultdict(set)
    centroids_by_ua = defaultdict(set)
    for line, row in enumerate(reader, 2):
        if None in row or any(row.get(name) is None for name in REQUIRED):
            raise ValueError(f"row {line}: malformed IFN panel CSV record")
        biome = row["bioma"].strip()
        if biome not in ALLOWED_BIOMES:
            raise ValueError(f"row {line}: invalid or missing IFN panel biome")
        uf = canonical_state(row["uf"])
        ua = canonical_ua(row["ua"])
        typology = row["tipologia_da_vegetacao"].strip()
        equation = row["equacoes"].strip()
        if not uf or not ua or not typology or not equation:
            raise ValueError(f"row {line}: missing physical UA, typology or equation")
        _finite_nonnegative(row["agb_media_kg_por_ha"], "AGB", line)
        _finite_nonnegative(row["agb_variancia_por_ua"], "UA variance", line)
        _finite_nonnegative(row["area_ha"], "area", line)
        key = (uf, ua)
        lon = _coordinate(row["lon_pc"], "lon_pc", line)
        lat = _coordinate(row["lat_pc"], "lat_pc", line)
        centroids_by_ua[key].add((lon, lat) if lon is not None and lat is not None else None)
        counts[biome] += 1
        units[biome].add(key)
        typology_units[(biome, typology)].add(key)
        equations_by_ua[key].add(equation)
        typologies_by_ua[key].add(typology)
        biomes_by_ua[key].add(biome)
    if not counts:
        raise ValueError("empty IFN panel")
    return {
        "row_count": sum(counts.values()),
        "unique_physical_ua_count": len(biomes_by_ua),
        "rows_beyond_unique_physical_ua_count": sum(counts.values()) - len(biomes_by_ua),
        "rows_by_biome": dict(sorted(counts.items())),
        "unique_physical_ua_by_biome": {b: len(units[b]) for b in sorted(ALLOWED_BIOMES)},
        "ua_with_multiple_equation_labels": sum(len(v) > 1 for v in equations_by_ua.values()),
        "ua_with_multiple_typology_labels": sum(len(v) > 1 for v in typologies_by_ua.values()),
        "ua_with_conflicting_biome_labels": sum(len(v) > 1 for v in biomes_by_ua.values()),
        "ua_with_missing_or_conflicting_centroid": sum(
            len(v) != 1 or None in v for v in centroids_by_ua.values()),
        "typology_ua_counts_provisional_not_ibge_verified": {
            b: {t: len(v) for (bb, t), v in sorted(typology_units.items()) if bb == b}
            for b in sorted(ALLOWED_BIOMES) if counts[b]
        },
        "_units_by_biome": units,
        "_centroids_by_ua": centroids_by_ua,
        "_biomes_by_ua": biomes_by_ua,
    }


def audit(raw_by_id, expected_sha256):
    if set(raw_by_id) != set(SOURCES) or set(expected_sha256) != set(SOURCES):
        raise ValueError("incomplete IFN panel source set")
    reports, digests = {}, {}
    for sid in SOURCES:
        digest = hashlib.sha256(raw_by_id[sid]).hexdigest()
        if digest != str(expected_sha256[sid]).lower():
            raise ValueError("IFN panel source SHA256 mismatch: " + sid)
        digests[sid] = digest
        reports[sid] = _screen(raw_by_id[sid])
    # A physical UA with inconsistent biome labels cannot support any biome,
    # even when both panels report the same centroid for that UA.
    biome_labels_by_ua = defaultdict(set)
    for report in reports.values():
        for ua, labels in report["_biomes_by_ua"].items():
            biome_labels_by_ua[ua].update(labels)
    ambiguous_ua = {ua for ua, labels in biome_labels_by_ua.items() if len(labels) > 1}
    raw_overlap = {
        biome: reports["ifn_painel_biomassa_2026"]["_units_by_biome"][biome]
               & reports["ifn_painel_arvores_mortas_2026"]["_units_by_biome"][biome]
        for biome in TARGET_BIOMES
    }
    valid_overlap = {biome: raw_overlap[biome] - ambiguous_ua for biome in TARGET_BIOMES}
    overlap = {biome: len(valid_overlap[biome]) for biome in TARGET_BIOMES}
    quarantined_overlap = {biome: len(raw_overlap[biome] & ambiguous_ua)
                           for biome in TARGET_BIOMES}
    concordant = {}
    for biome in TARGET_BIOMES:
        left = reports["ifn_painel_biomassa_2026"]["_centroids_by_ua"]
        right = reports["ifn_painel_arvores_mortas_2026"]["_centroids_by_ua"]
        common = valid_overlap[biome]
        concordant[biome] = sum(
            len(left[ua]) == len(right[ua]) == 1
            and None not in left[ua] and left[ua] == right[ua]
            for ua in common)
    for report in reports.values():
        del report["_units_by_biome"]
        del report["_centroids_by_ua"]
        del report["_biomes_by_ua"]
    return {
        "report_type": "licensed_IFN_panel_2026_biome_UA_coverage_screening_only",
        "source_sha256": digests,
        "source_license": "Creative Commons Attribution (official SFB portal)",
        "source_license_url": LICENSE_URL,
        "panel_data": reports,
        "physical_ua_quarantined_for_conflicting_biome_labels": len(ambiguous_ua),
        "target_biome_coverage": {
            biome: {
                "living_tree_panel_present": bool(reports["ifn_painel_biomassa_2026"]["rows_by_biome"].get(biome)),
                "standing_dead_panel_present": bool(reports["ifn_painel_arvores_mortas_2026"]["rows_by_biome"].get(biome)),
                "physical_ua_overlap_between_panels": overlap[biome],
                "overlap_ua_quarantined_for_conflicting_biome_labels": quarantined_overlap[biome],
                "overlap_ua_with_identical_reported_centroid": concordant[biome],
                "overlap_ua_centroid_missing_or_discordant": overlap[biome] - concordant[biome],
                "independent_validation": False,
            } for biome in TARGET_BIOMES
        },
        "ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified": False,
        "ifn_panel_equation_independence_verified": False,
        "field_acquisition_date_per_record_verified": False,
        "sar_plot_pixel_validation": False,
        "sampling_design_variance_and_transfer_error_validated": False,
        "carbon_stock_tC_ha": None,
        "confidence_interval_95": None,
        "scientific_validation": False,
        "warning": "IFN panel AGB rows are repeated subunit/allometric-equation outputs, not independent field plots or independent SAR pairs. Physical UAs with conflicting biome labels are quarantined across panels. Unique physical UAs and identical reported centroids are descriptive joins only, not positional accuracy or independent spatial validation; panel typology is not a verified spatial IBGE crosswalk. Missing Pantanal panel rows are N/D, not zero. No AOI carbon, root/wood stock, design-based IC95, SAR error or transfer uncertainty can be inferred."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--download-audit", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    registry = json.loads(Path(args.download_audit).read_text(encoding="utf-8"))
    resources = {r["id"]: r for r in registry["resources"]}
    if not set(SOURCES).issubset(resources):
        raise ValueError("missing IFN panel acquisition records")
    raw, digests = {}, {}
    for sid in SOURCES:
        row = resources[sid]
        if row.get("status") != "downloaded_unvalidated" or row.get("local_file") != sid + ".csv":
            raise ValueError("IFN panel raw source not acquired")
        raw[sid] = (Path(args.raw_dir) / (sid + ".csv")).read_bytes()
        digests[sid] = row["sha256"]
    result = audit(raw, digests)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"panel_coverage": result["target_biome_coverage"],
                      "scientific_validation": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
