#!/usr/bin/env python3
"""Prepare conservative, UNVALIDATED IFN/SFB plot-level AGB candidates.

The official panel repeats each sampling unit for many alternative equations.
Only its explicitly labelled AGB_Chave row is retained, and even that is NOT
an independently audited equation, a SAR calibration, or an AOI estimate.
Publicly rounded coordinates have unknown positional accuracy; they MUST NOT
be paired to SAR pixels without an independently verified location.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from tools.harvest_ifn_field_data import canonical_state

TARGET_BIOMES = frozenset(("Amazônia", "Caatinga", "Cerrado", "Mata Atlântica", "Pantanal"))
NATIVE_CLASSES = frozenset((
    "Floresta Natural", "Savana", "Savana-estépica", "Estepe",
    "Palmeiral", "Formação Pioneira", "Campinarana",
))
REQUIRED = frozenset((
    "bioma", "uf", "ua", "lon_pc", "lat_pc", "sanidade",
    "classe_uso_da_terra", "tipologia_da_vegetacao", "equacoes",
    "area_ha", "agb_media_kg_por_ha", "agb_variancia_por_ua",
))
COLUMNS = (
    "bioma", "uf", "ua", "classe_uso_da_terra", "tipologia_da_vegetacao",
    "lon_pc", "lat_pc", "area_ha", "agb_mg_ha",
    "source_variance_kg2_per_ha2", "source_equation",
    "equation_choice_audited", "ibge_fitophysiognomy_verified",
    "sar_pair_eligible", "scientifically_validated",
)
SOURCE_PAGE = "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono"


def _number(raw):
    value = float(str(raw).strip().replace(",", "."))
    if not math.isfinite(value):
        raise ValueError("non-finite numeric field")
    return value


def prepare(raw, expected_sha256):
    """Return one conservative candidate per distinct (biome, UF, UA).

    All non-AGB_Chave alternatives are deliberately ignored; duplicated
    AGB_Chave rows (often mixed vegetation/subunits) exclude the whole UA,
    rather than pretending subunits or equation rows are independent plots.
    """
    digest = hashlib.sha256(raw).hexdigest()
    if digest.lower() != str(expected_sha256).lower():
        raise ValueError("IFN panel source SHA256 mismatch")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=";")
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("IFN panel missing required observational columns")
    grouped = defaultdict(list)
    total_rows = 0
    chosen_rows = 0
    for row in reader:
        if not any(row.values()):
            continue
        total_rows += 1
        if str(row["equacoes"]).strip() != "AGB_Chave":
            continue
        chosen_rows += 1
        biome = str(row["bioma"]).strip()
        ua = str(row["ua"]).strip()
        uf = canonical_state(row["uf"])
        if not biome or not uf or not ua:
            raise ValueError("AGB_Chave row has incomplete sampling-unit identity")
        grouped[(biome, uf, ua)].append(row)

    counters = Counter()
    by_biome = Counter()
    candidates = []
    quantized = 0
    for (biome, uf, ua), rows in sorted(grouped.items()):
        if len(rows) != 1:
            counters["excluded_multiple_agb_chave_rows_per_ua"] += 1
            continue
        row = rows[0]
        if biome not in TARGET_BIOMES:
            counters["excluded_outside_five_biomes"] += 1
            continue
        if str(row["classe_uso_da_terra"]).strip() not in NATIVE_CLASSES:
            counters["excluded_unclassified_or_non_native"] += 1
            continue
        if str(row["sanidade"]).strip() != "Vivas":
            counters["excluded_nonliving_agb_record"] += 1
            continue
        if not str(row["tipologia_da_vegetacao"]).strip():
            counters["excluded_missing_source_typology"] += 1
            continue
        try:
            lat, lon = _number(row["lat_pc"]), _number(row["lon_pc"])
            area = _number(row["area_ha"])
            agb_kg = _number(row["agb_media_kg_por_ha"])
            variance = _number(row["agb_variancia_por_ua"])
        except (ValueError, TypeError):
            counters["excluded_invalid_numeric_fields"] += 1
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            counters["excluded_invalid_coordinates"] += 1
            continue
        if area <= 0 or agb_kg < 0 or variance < 0:
            counters["excluded_invalid_biomass_or_area"] += 1
            continue
        # Diagnostic ONLY: grid quantization is not positional accuracy.
        if abs(lat * 50 - round(lat * 50)) < 1e-7 and abs(lon * 50 - round(lon * 50)) < 1e-7:
            quantized += 1
        candidates.append({
            "bioma": biome, "uf": uf, "ua": ua,
            "classe_uso_da_terra": row["classe_uso_da_terra"].strip(),
            "tipologia_da_vegetacao": row["tipologia_da_vegetacao"].strip(),
            "lon_pc": lon, "lat_pc": lat, "area_ha": area,
            "agb_mg_ha": agb_kg / 1000.0,
            # Source variance is NOT an AOI error, a 95% interval or transfer error.
            "source_variance_kg2_per_ha2": variance,
            "source_equation": "AGB_Chave",
            "equation_choice_audited": "false",
            "ibge_fitophysiognomy_verified": "false",
            "sar_pair_eligible": "false",
            "scientifically_validated": "false",
        })
        by_biome[biome] += 1

    report = {
        "source_sha256": digest, "source_page": SOURCE_PAGE,
        "source_license": "CC BY per official IFN panel dataset; verify before redistribution",
        "source_observation_rows": total_rows,
        "agb_chave_rows": chosen_rows,
        "unique_ua_with_agb_chave": len(grouped),
        "candidate_ua": len(candidates),
        "candidate_ua_by_biome": dict(sorted(by_biome.items())),
        "exclusions": dict(sorted(counters.items())),
        "candidate_coords_both_on_0_02_degree_grid": quantized,
        "candidate_coords_grid_fraction": quantized / len(candidates) if candidates else None,
        "coordinate_accuracy_m": None,
        "sar_pair_eligible": False,
        "scientific_validation": False,
        "ibge_spatial_crosswalk": "not_performed",
        "warning": (
            "AGB_Chave is a published equation-selection label, NOT an independently "
            "validated choice. Source coordinates appear quantized and positional "
            "accuracy is unknown: do not pair to SAR pixels, infer plot-scale "
            "accuracy, calculate AOI IC95%, or transfer stocks across IBGE classes. "
            "One UA may contain multiple source land-cover classes; all repeated "
            "AGB_Chave UA records are excluded rather than pseudoreplicated."
        ),
    }
    return candidates, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Original licensed SFB panel biomass CSV")
    parser.add_argument("--sha256", required=True, help="Exact raw source digest from harvest manifest")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    candidates, report = prepare(Path(args.csv).read_bytes(), args.sha256)
    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(candidates)
    report["candidate_csv_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
