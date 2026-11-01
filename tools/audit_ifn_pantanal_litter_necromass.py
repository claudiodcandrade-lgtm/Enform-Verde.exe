#!/usr/bin/env python3
"""Fail-closed audit of licensed IFN Pantanal litter depth versus necromass UAs.

Neither depth nor a shared physical UA establishes a litter carbon stock,
IBGE fitophysiognomy, independent variance, or a SAR plot-pixel pair.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tools.ifn_state_identity import canonical_state, canonical_ua

LITTER_IDS = {
    "ifn_serapilheira_mato_grosso_retificada_2025": "MT",
    "ifn_serapilheira_mato_grosso_do_sul_retificada_2025": "MS",
}
NECRO_ID = "ifn_painel_necromassa_t_ha_2026"
LITTER_FIELDS = {"bioma", "uf", "ua", "mun", "lon_pc", "lat_pc", "data", "Uso_terra_PC", "Ponto", "Profundidade"}
NECRO_FIELDS = {"bioma", "uf", "ua", "necromassa_t_por_ha"}


def rows(raw, required):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
    headers = reader.fieldnames or []
    if not required.issubset(headers) or len(headers) != len(set(headers)) or any(not x for x in headers):
        raise ValueError("missing, blank or duplicate CSV headers")
    for index, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"ragged CSV row {index}")
        if any(value.strip() for value in row.values()):
            yield row


def number(value, low, high):
    try:
        parsed = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("invalid numeric measurement") from exc
    if not parsed.is_finite() or not low <= parsed <= high:
        raise ValueError("numeric measurement outside physical domain")
    return parsed


def audit(litter_by_id, necro_raw, expected_sha256):
    raw_sources = {**litter_by_id, NECRO_ID: necro_raw}
    if set(litter_by_id) != set(LITTER_IDS) or set(expected_sha256) != set(raw_sources):
        raise ValueError("incomplete IFN source manifest")
    source_sha = {}
    for source_id, raw in raw_sources.items():
        digest = hashlib.sha256(raw).hexdigest()
        if digest != str(expected_sha256[source_id]).lower():
            raise ValueError(f"IFN SHA256 mismatch: {source_id}")
        source_sha[source_id] = digest

    litter = defaultdict(dict)
    for source_id, uf_expected in LITTER_IDS.items():
        for row in rows(litter_by_id[source_id], LITTER_FIELDS):
            if canonical_state(row["uf"]) != uf_expected:
                raise ValueError("litter state inconsistent with licensed source")
            if row["bioma"].strip() != "Pantanal":
                continue
            key = (uf_expected, canonical_ua(row["ua"]))
            if not key[1]:
                raise ValueError("missing Pantanal physical UA")
            point = number(row["Ponto"], Decimal(1), Decimal(5))
            if point != point.to_integral_value():
                raise ValueError("non-integer litter point")
            point = int(point)
            depth = number(row["Profundidade"], Decimal(0), Decimal("100000"))
            lon = number(row["lon_pc"], Decimal(-180), Decimal(180))
            lat = number(row["lat_pc"], Decimal(-90), Decimal(90))
            identity = (row["mun"].strip(), lon, lat, row["data"].strip(), row["Uso_terra_PC"].strip())
            if not identity[0] or not identity[3] or not identity[4]:
                raise ValueError("missing Pantanal UA metadata")
            if key in litter and litter[key]["identity"] != identity:
                raise ValueError("conflicting metadata within physical UA")
            entry = litter.setdefault(key, {"identity": identity, "points": {}})
            if point in entry["points"]:
                raise ValueError("duplicate point in physical UA")
            entry["points"][point] = depth
    for entry in litter.values():
        if set(entry["points"]) != {1, 2, 3, 4, 5}:
            raise ValueError("incomplete five-point litter UA")

    necro_keys = set()
    necro_pantanal = set()
    necro_biomes = Counter()
    for row in rows(necro_raw, NECRO_FIELDS):
        biome = row["bioma"].strip()
        necro_biomes[biome or "N/D"] += 1
        uf, ua = canonical_state(row["uf"]), canonical_ua(row["ua"])
        if not uf or not ua:
            continue
        key = (uf, ua)
        necro_keys.add(key)
        if biome == "Pantanal":
            necro_pantanal.add(key)

    land_codes = Counter(entry["identity"][4] for entry in litter.values())
    points = [v for entry in litter.values() for v in entry["points"].values()]
    return {
        "report_type": "licensed_observational_cross_source_screening_only",
        "source_sha256": source_sha,
        "pantanal_litter_unique_physical_ua": len(litter),
        "pantanal_litter_depth_measurements": len(points),
        "pantanal_litter_zero_depth_measurements": sum(v == 0 for v in points),
        "pantanal_litter_land_codes_provisional": dict(sorted(land_codes.items())),
        "necromass_source_rows_by_biome": dict(sorted(necro_biomes.items())),
        "pantanal_necromass_source_rows": necro_biomes.get("Pantanal", 0),
        "litter_necromass_same_physical_ua_any_biome": len(set(litter) & necro_keys),
        "litter_necromass_same_physical_ua_both_pantanal": len(set(litter) & necro_pantanal),
        "ifn_land_code_dictionary_version_verified": False,
        "ibge_fitophysiognomy_verified": False,
        "carbon_stock_tC_ha": None,
        "confidence_interval_95": None,
        "spatial_sar_pair_verified": False,
        "scientific_validation": False,
        "warning": "Depth is not dry litter mass; physical UAs are not independent SAR pairs. No Pantanal stock, transfer error or IC95 may be inferred.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--download-audit", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    registry = json.loads(Path(args.download_audit).read_text(encoding="utf-8"))
    resources = {r["id"]: r for r in registry["resources"]}
    ids = set(LITTER_IDS) | {NECRO_ID}
    if not ids.issubset(resources):
        raise ValueError("missing official source in download audit")
    raw, sha = {}, {}
    for source_id in ids:
        entry = resources[source_id]
        if entry["status"] != "downloaded_unvalidated" or entry.get("local_file") != source_id + ".csv":
            raise ValueError("source is not a validated CSV acquisition")
        raw[source_id] = (Path(args.raw_dir) / entry["local_file"]).read_bytes()
        sha[source_id] = entry["sha256"]
    report = audit({k: raw[k] for k in LITTER_IDS}, raw[NECRO_ID], sha)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"litter_ua": report["pantanal_litter_unique_physical_ua"],
                      "necro_pantanal_rows": report["pantanal_necromass_source_rows"],
                      "cross_source_overlap": report["litter_necromass_same_physical_ua_any_biome"],
                      "scientific_validation": False}))


if __name__ == "__main__":
    main()
