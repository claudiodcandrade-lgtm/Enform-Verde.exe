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
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

from tools.ifn_state_identity import canonical_state, canonical_ua
from tools.prepare_ifn_agb_candidates import NATIVE_CLASSES

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
# Source land-use labels are only a preliminary screen, never a verified
# contemporary-cover map or an IBGE fitophysiognomy crosswalk.
NATIVE_SOURCE_LAND_CLASSES = frozenset(
    unicodedata.normalize("NFKC", label).strip().casefold() for label in NATIVE_CLASSES
)
REQUIRED = {"bioma", "uf", "lon_pc", "lat_pc", "ua", "n_subunidades", "sanidade",
            "classe_uso_da_terra", "tipologia_da_vegetacao", "equacoes", "area_ha",
            "agb_media_kg_por_ha", "agb_variancia_por_ua", "valor_r"}
LICENSE_URL = "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono"
# Intentionally generous bounding box: plausibility screen only, NOT IBGE
# state/biome overlay, geolocation accuracy, or a verified source CRS.
BRAZIL_SCREEN_ENVELOPE = (Decimal("-75"), Decimal("-32"), Decimal("-35"), Decimal("7"))


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
    # Header aliases (case, NFKC, whitespace) and invisible controls must not
    # create ambiguous observation fields or conceal an alternative UF/UA.
    normalized = [unicodedata.normalize("NFKC", name).strip().casefold()
                  for name in fields]
    if (len(fields) != len(set(normalized))
            or any(not name or any(unicodedata.category(ch) in {"Cc", "Cf"}
                                   for ch in name) for name in normalized)):
        raise ValueError("duplicate or blank IFN panel CSV headers")
    if not REQUIRED.issubset(fields):
        raise ValueError("missing IFN panel columns")
    counts = Counter()
    units = defaultdict(set)
    typology_units = defaultdict(set)
    equations_by_ua = defaultdict(set)
    typologies_by_ua = defaultdict(set)
    source_typologies_by_ua = defaultdict(set)
    biomes_by_ua = defaultdict(set)
    land_classes_by_ua = defaultdict(set)
    centroids_by_ua = defaultdict(set)
    zero_zero_centroid_ua = set()
    outside_brazil_envelope_ua = set()
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
        # (0, 0) is outside Brazil and is a common missing-location sentinel.
        # Retain the observation for coverage counts, but never treat this
        # placeholder as a matching physical centroid across source panels.
        if lon is not None and lat is not None and lon == 0 and lat == 0:
            zero_zero_centroid_ua.add(key)
            lon = lat = None
        elif lon is not None and lat is not None:
            west, east, south, north = BRAZIL_SCREEN_ENVELOPE
            if not (west <= lon <= east and south <= lat <= north):
                # A globally valid longitude/latitude is not necessarily a
                # plausible Brazilian plot. Keep UA counts, but do not certify
                # centroid concordance for locations outside this broad screen.
                outside_brazil_envelope_ua.add(key)
                lon = lat = None
        centroids_by_ua[key].add((lon, lat) if lon is not None and lat is not None else None)
        counts[biome] += 1
        units[biome].add(key)
        typology_units[(biome, typology)].add(key)
        equations_by_ua[key].add(equation)
        typologies_by_ua[key].add(typology)
        # Source terminology is only a preliminary label, not IBGE legenda_1.
        source_typologies_by_ua[key].add(unicodedata.normalize(
            "NFKC", typology).strip().casefold())
        biomes_by_ua[key].add(biome)
        # Multiple source equations/subunits may carry different land-use
        # classes for one physical UA. A mixed or missing class cannot be
        # represented as an independently confirmed native sampling unit.
        land_class = unicodedata.normalize(
            'NFKC', row['classe_uso_da_terra'].strip()).casefold()
        land_classes_by_ua[key].add(land_class or None)
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
        "ua_with_missing_or_conflicting_source_land_class": sum(
            len(v) != 1 or None in v for v in land_classes_by_ua.values()),
        "ua_with_missing_or_conflicting_centroid": sum(
            len(v) != 1 or None in v for v in centroids_by_ua.values()),
        "ua_with_zero_zero_centroid_placeholder": len(zero_zero_centroid_ua),
        "ua_with_centroid_outside_brazil_screen_envelope": len(outside_brazil_envelope_ua),
        "typology_ua_counts_provisional_not_ibge_verified": {
            b: {t: len(v) for (bb, t), v in sorted(typology_units.items()) if bb == b}
            for b in sorted(ALLOWED_BIOMES) if counts[b]
        },
        "_units_by_biome": units,
        "_centroids_by_ua": centroids_by_ua,
        "_biomes_by_ua": biomes_by_ua,
        "_land_classes_by_ua": land_classes_by_ua,
        "_source_typologies_by_ua": source_typologies_by_ua,
    }


def audit(raw_by_id, expected_sha256, include_candidate_rows=False):
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
    # Source classes are NOT IBGE-verified or proof of current native cover.
    # Even as a provisional screen, require a single identical native label
    # across ALL rows/equations in both panels for each physical UA.
    left_classes = reports["ifn_painel_biomassa_2026"]["_land_classes_by_ua"]
    right_classes = reports["ifn_painel_arvores_mortas_2026"]["_land_classes_by_ua"]
    provisional_native_overlap = {
        biome: sum(
            len(left_classes[ua]) == len(right_classes[ua]) == 1
            and left_classes[ua] == right_classes[ua]
            and next(iter(left_classes[ua])) in NATIVE_SOURCE_LAND_CLASSES
            for ua in valid_overlap[biome]
        ) for biome in TARGET_BIOMES
    }
    # A provisional native land-use label does not imply a unique source
    # vegetation typology. Require a single matching typology in ALL equation
    # rows of BOTH panels before identifying a geolocatable IBGE crosswalk
    # candidate. This is still not an IBGE polygon intersection or validation.
    left_typologies = reports["ifn_painel_biomassa_2026"]["_source_typologies_by_ua"]
    right_typologies = reports["ifn_painel_arvores_mortas_2026"]["_source_typologies_by_ua"]
    left_centroids = reports["ifn_painel_biomassa_2026"]["_centroids_by_ua"]
    right_centroids = reports["ifn_painel_arvores_mortas_2026"]["_centroids_by_ua"]
    matching_source_typology = {
        biome: sum(
            len(left_typologies[ua]) == len(right_typologies[ua]) == 1
            and left_typologies[ua] == right_typologies[ua]
            for ua in valid_overlap[biome]
        ) for biome in TARGET_BIOMES
    }
    provisional_geolocated_native_typology = {
        biome: sum(
            len(left_classes[ua]) == len(right_classes[ua]) == 1
            and left_classes[ua] == right_classes[ua]
            and next(iter(left_classes[ua])) in NATIVE_SOURCE_LAND_CLASSES
            and len(left_typologies[ua]) == len(right_typologies[ua]) == 1
            and left_typologies[ua] == right_typologies[ua]
            and len(left_centroids[ua]) == len(right_centroids[ua]) == 1
            and None not in left_centroids[ua]
            and left_centroids[ua] == right_centroids[ua]
            for ua in valid_overlap[biome]
        ) for biome in TARGET_BIOMES
    }
    # Export only source-consistent physical UAs for a future IBGE overlay.
    # This does not establish the source CRS, positional accuracy, IBGE class,
    # independent SAR pairs or scientifically defensible carbon estimates.
    candidate_rows = []
    if include_candidate_rows:
        for biome in TARGET_BIOMES:
            for ua in sorted(valid_overlap[biome]):
                if not (
                    len(left_classes[ua]) == len(right_classes[ua]) == 1
                    and left_classes[ua] == right_classes[ua]
                    and next(iter(left_classes[ua])) in NATIVE_SOURCE_LAND_CLASSES
                    and len(left_typologies[ua]) == len(right_typologies[ua]) == 1
                    and left_typologies[ua] == right_typologies[ua]
                    and len(left_centroids[ua]) == len(right_centroids[ua]) == 1
                    and None not in left_centroids[ua]
                    and left_centroids[ua] == right_centroids[ua]
                ):
                    continue
                lon, lat = next(iter(left_centroids[ua]))
                candidate_rows.append({
                    "bioma_declarado": biome, "uf": ua[0], "ua": ua[1],
                    "lon_pc_publicado": str(lon), "lat_pc_publicado": str(lat),
                    "classe_nativa_declarada": next(iter(left_classes[ua])),
                    "tipologia_origem_declarada": next(iter(left_typologies[ua])),
                    "crs_fonte_verificado": "false",
                    "legenda_1_ibge_verificada": "false",
                    "par_sar_validado": "false",
                    "estoque_carbono_validado": "false",
                })
        if len(candidate_rows) != sum(provisional_geolocated_native_typology.values()):
            raise AssertionError("candidate rows do not reconcile with screened physical UAs")
    for report in reports.values():
        del report["_units_by_biome"]
        del report["_centroids_by_ua"]
        del report["_biomes_by_ua"]
        del report["_land_classes_by_ua"]
        del report["_source_typologies_by_ua"]
    result = {
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
                "overlap_ua_with_single_matching_source_native_land_class_provisional": provisional_native_overlap[biome],
                "overlap_ua_without_single_matching_source_native_land_class": overlap[biome] - provisional_native_overlap[biome],
                "overlap_ua_with_single_matching_source_typology_provisional": matching_source_typology[biome],
                "overlap_ua_without_single_matching_source_typology": overlap[biome] - matching_source_typology[biome],
                "overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional": provisional_geolocated_native_typology[biome],
                "independent_validation": False,
            } for biome in TARGET_BIOMES
        },
        "source_native_land_class_screening_only_not_current_cover": True,
        "ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified": False,
        "ifn_panel_equation_independence_verified": False,
        "field_acquisition_date_per_record_verified": False,
        "sar_plot_pixel_validation": False,
        "sampling_design_variance_and_transfer_error_validated": False,
        "carbon_stock_tC_ha": None,
        "confidence_interval_95": None,
        "scientific_validation": False,
        "warning": "IFN panel AGB rows are repeated subunit/allometric-equation outputs, not independent field plots or independent SAR pairs. Physical UAs with conflicting biome labels are quarantined across panels. Unique physical UAs and identical reported centroids are descriptive joins only, not positional accuracy or independent spatial validation; zero-zero placeholders and locations outside a generous Brazil bounding envelope are unresolved, never concordant; this envelope is only a plausibility screen, not a verified IBGE overlay or source CRS; panel typology and source land-use labels are not a verified spatial IBGE crosswalk or current-cover confirmation; provisional native overlaps require identical single native source class in both panels and exclude mixed, missing or anthropized classes; the stricter geolocatable candidate subset additionally requires a single matching source vegetation typology and a resolved identical centroid in both panels, but still requires an actual IBGE legenda_1 overlay and independent verification. Missing Pantanal panel rows are N/D, not zero. No AOI carbon, root/wood stock, design-based IC95, SAR error or transfer uncertainty can be inferred."
    }
    return (result, candidate_rows) if include_candidate_rows else result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--download-audit", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--candidate-csv", default=None,
                        help="Optional unvalidated physical-UA source table for future IBGE overlay")
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
    if args.candidate_csv:
        result, candidates = audit(raw, digests, include_candidate_rows=True)
        csv_path = Path(args.candidate_csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        columns = ("bioma_declarado", "uf", "ua", "lon_pc_publicado",
                   "lat_pc_publicado", "classe_nativa_declarada",
                   "tipologia_origem_declarada", "crs_fonte_verificado",
                   "legenda_1_ibge_verificada", "par_sar_validado",
                   "estoque_carbono_validado")
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(candidates)
        result["candidate_csv_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        result["candidate_csv_physical_ua_count"] = len(candidates)
        result["candidate_csv_scientifically_validated"] = False
        result["candidate_csv_warning"] = (
            "Source-reported IFN coordinates and labels only; source CRS, "
            "positional accuracy, IBGE legenda_1, SAR and carbon NOT verified."
        )
    else:
        result = audit(raw, digests)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"panel_coverage": result["target_biome_coverage"],
                      "scientific_validation": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
