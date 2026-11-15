#!/usr/bin/env python3
"""Independent-source IFN Pantanal field-subplot x litter-depth identity audit.

Physical UF+UA matches and land-use codes are descriptive only. Litter depth
is NOT dry mass, carbon, current native cover, IBGE class, or SAR validation.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from tools.audit_ifn_field_land_use import SOURCES as FIELD_IDS, load_subplots, normalized
from tools.audit_ifn_pantanal_litter_necromass import LITTER_FIELDS, rows, number
from tools.ifn_state_identity import canonical_state, canonical_ua

LITTER_IDS = {
    "ifn_serapilheira_mato_grosso_retificada_2025": "MT",
    "ifn_serapilheira_mato_grosso_do_sul_retificada_2025": "MS",
}


def verified_paths(raw_dir, report, ids, suffix):
    resources = report.get("resources")
    if not isinstance(resources, list):
        raise ValueError("missing licensed acquisition resource list")
    if len({r.get("id") for r in resources}) != len(resources):
        raise ValueError("duplicate licensed acquisition resource id")
    entries = {r["id"]: r for r in resources}
    if not set(ids).issubset(entries):
        raise ValueError("missing required licensed source")
    result, digests = {}, {}
    for sid in ids:
        entry = entries[sid]
        if entry.get("status") != "downloaded_unvalidated" or entry.get("validated_file_extension") != suffix:
            raise ValueError("unverified licensed source format or status: " + sid)
        path = Path(raw_dir) / (sid + suffix)
        if entry.get("local_file") != path.name:
            raise ValueError("source filename mismatch: " + sid)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != entry.get("sha256"):
            raise ValueError("source SHA256 mismatch: " + sid)
        result[sid] = path
        digests[sid] = sha
    return result, digests



def read_field_reported_centroids(paths):
    """Read reported panel-style centroids, never independent GPS accuracy."""
    from openpyxl import load_workbook
    result = defaultdict(set)
    for sid, uf in FIELD_IDS.items():
        wb = load_workbook(paths[sid], read_only=True, data_only=False, keep_links=False)
        try:
            if len(wb.worksheets) != 1:
                raise ValueError("unexpected field workbook sheet count")
            iterator = wb.worksheets[0].iter_rows(values_only=True)
            header = next(iterator, None)
            labels = [normalized(v) for v in (header or ())]
            required = {"bioma", "uf", "ua", "lon_pc", "lat_pc"}
            if not required.issubset(labels) or len(set(labels)) != len(labels):
                raise ValueError("field reported coordinate headers missing or ambiguous")
            indices = {name: labels.index(name) for name in required}
            for values in iterator:
                if not values or normalized(values[indices["bioma"]]) != "pantanal":
                    continue
                if canonical_state(values[indices["uf"]]) != uf:
                    raise ValueError("field reported coordinate UF conflicts with source")
                ua = canonical_ua(values[indices["ua"]])
                if not ua:
                    raise ValueError("field Pantanal physical UA missing")
                key = (uf, ua)
                try:
                    lon = number(values[indices["lon_pc"]], Decimal(-180), Decimal(180))
                    lat = number(values[indices["lat_pc"]], Decimal(-90), Decimal(90))
                    coord = (lon, lat) if (lon, lat) != (0, 0) else None
                except ValueError:
                    coord = None
                result[key].add(coord)
        finally:
            wb.close()
    return result


def read_pantanal_litter(paths):
    litter = {}
    for sid, uf in LITTER_IDS.items():
        for row in rows(paths[sid].read_bytes(), LITTER_FIELDS):
            if canonical_state(row["uf"]) != uf:
                raise ValueError("litter UF inconsistent with source")
            if normalized(row["bioma"]) != "pantanal":
                continue
            ua = canonical_ua(row["ua"])
            if not ua:
                raise ValueError("litter Pantanal UA missing")
            key = (uf, ua)
            point = number(row["Ponto"], Decimal(1), Decimal(5))
            if point != point.to_integral_value():
                raise ValueError("noninteger litter point")
            point = int(point)
            number(row["Profundidade"], Decimal(0), Decimal("Infinity"))
            code = normalized(row["Uso_terra_PC"])
            if not code:
                raise ValueError("litter land code missing")
            lon = number(row["lon_pc"], Decimal(-180), Decimal(180))
            lat = number(row["lat_pc"], Decimal(-90), Decimal(90))
            entry = litter.setdefault(key, {"points": set(), "codes": set(), "centroids": set()})
            entry["centroids"].add((lon, lat))
            if point in entry["points"]:
                raise ValueError("duplicate litter point")
            entry["points"].add(point)
            entry["codes"].add(code)
    for entry in litter.values():
        if (entry["points"] != {1, 2, 3, 4, 5} or len(entry["codes"]) != 1
                or len(entry["centroids"]) != 1):
            raise ValueError("incomplete litter points or conflicting land codes")
    return litter


def audit(field_paths, litter_paths, field_report, litter_report):
    field_verified, field_hashes = verified_paths(
        {p.parent for p in field_paths.values()}.pop() if field_paths else ".",
        field_report, FIELD_IDS, ".xlsx")
    litter_verified, litter_hashes = verified_paths(
        {p.parent for p in litter_paths.values()}.pop() if litter_paths else ".",
        litter_report, LITTER_IDS, ".csv")
    # Do not accept caller-supplied unverified alternate paths.
    if field_paths != field_verified or litter_paths != litter_verified:
        raise ValueError("unverified observational source paths")
    field, source_rows = load_subplots(field_paths)
    field_centroids = read_field_reported_centroids(field_paths)
    litter = read_pantanal_litter(litter_paths)
    field_pantanal = {
        key: info for key, info in field.items()
        if info["biomes"] == {"pantanal"}
    }
    conflicting_field_biome = {
        key for key, info in field.items()
        if "pantanal" in info["biomes"] and info["biomes"] != {"pantanal"}
    }
    overlap = set(field_pantanal) & set(litter)
    by_uf = defaultdict(Counter)
    for key in field_pantanal:
        by_uf[key[0]]["field_pantanal_ua"] += 1
    for key in litter:
        by_uf[key[0]]["litter_pantanal_ua"] += 1
    for key in overlap:
        uf = key[0]
        c = by_uf[uf]
        c["same_physical_ua"] += 1
        reported = field_centroids.get(key, set())
        if len(reported) != 1 or None in reported:
            c["field_reported_centroid_missing_or_conflicting"] += 1
        elif next(iter(reported)) == next(iter(litter[key]["centroids"])):
            c["same_reported_centroid_not_independent_accuracy"] += 1
        else:
            c["reported_centroid_disagrees_between_sources"] += 1
        info = field_pantanal[key]
        if info["duplicate"] or info["unresolved"]:
            c["field_subplot_identity_unresolved"] += 1
            continue
        if info["flags"] == {"s"}:
            c["all_field_subplots_forest_S"] += 1
        elif info["flags"] == {"n"}:
            c["all_field_subplots_forest_N"] += 1
        elif "N/D" in info["flags"]:
            c["field_forest_flag_unresolved"] += 1
        else:
            c["mixed_field_forest_flags"] += 1
        if len(info["codes"]) != 1 or "N/D" in info["codes"]:
            c["field_land_code_mixed_or_missing"] += 1
        elif info["codes"] == litter[key]["codes"]:
            c["single_land_code_equal_across_sources"] += 1
        else:
            c["single_land_code_disagrees_across_sources"] += 1
    return {
        "report_type": "IFN_Pantanal_2025_field_subplots_x_litter_depth_identity_screening_NOT_homologation",
        "source_sha256": {**field_hashes, **litter_hashes},
        "field_rows_by_source": source_rows,
        "field_pantanal_physical_ua": len(field_pantanal),
        "litter_pantanal_physical_ua": len(litter),
        "same_physical_ua_field_and_litter": len(overlap),
        "field_only_pantanal_physical_ua": len(set(field_pantanal) - set(litter)),
        "litter_only_pantanal_physical_ua": len(set(litter) - set(field_pantanal)),
        "field_ua_with_conflicting_pantanal_biome_quarantined": len(conflicting_field_biome),
        "by_uf": {uf: dict(sorted(counts.items())) for uf, counts in sorted(by_uf.items())},
        "same_UA_not_independent_spatial_or_temporal_validation": True,
        "reported_centroid_equality_not_independent_position_accuracy": True,
        "land_code_dictionary_2025_equivalence_verified": False,
        "ibge_fitophysiognomy_verified": False,
        "sar_plot_pixel_pairs_verified": False,
        "carbon_stock_tC_ha": None,
        "transfer_error": None,
        "confidence_interval_95": None,
        "scientific_validation": False,
        "warning": "Physical UF+UA joins and raw code equality are descriptive. "
                   "Subplot forest S/N does not classify native cover. "
                   "Depth is not dry litter mass; per-row dates, independently "
                   "verified field coordinates, IBGE classes, SAR pairs and "
                   "sampling variance remain N/D. No carbon or IC95 inferred."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field-dir", required=True)
    p.add_argument("--litter-dir", required=True)
    p.add_argument("--field-audit", required=True)
    p.add_argument("--litter-audit", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    field_paths = {sid: Path(args.field_dir) / (sid + ".xlsx") for sid in FIELD_IDS}
    litter_paths = {sid: Path(args.litter_dir) / (sid + ".csv") for sid in LITTER_IDS}
    report = audit(field_paths, litter_paths,
                   json.loads(Path(args.field_audit).read_text(encoding="utf-8")),
                   json.loads(Path(args.litter_audit).read_text(encoding="utf-8")))
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"field_pantanal_ua": report["field_pantanal_physical_ua"],
                      "litter_pantanal_ua": report["litter_pantanal_physical_ua"],
                      "overlap": report["same_physical_ua_field_and_litter"],
                      "scientific_validation": False}))


if __name__ == "__main__":
    main()
