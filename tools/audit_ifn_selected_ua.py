#!/usr/bin/env python3
"""Audit IFN unit-level estimates without pseudoreplicating allometric equations.

A descriptive stratified summary of selected-UA measurements is NOT an AOI
confidence interval, SAR validation or independent spatial transfer validation.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

REQUIRED = ("bioma", "uf", "ua", "fitofisionomia_ibge", "equacao_selecionada",
            "agb_mg_ha", "equation_choice_audited")

def summarize(path, expected_sha256):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest.lower() != expected_sha256.lower():
        raise ValueError("source SHA256 mismatch")
    strata = defaultdict(list)
    seen = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in REQUIRED):
            raise ValueError("missing obligatory selected-UA fields")
        for line, row in enumerate(reader, 2):
            bioma, uf, ua, fito, eq = (str(row[k]).strip() for k in REQUIRED[:5])
            if not all((bioma, uf, ua, fito, eq)):
                raise ValueError(f"row {line}: missing sampling domain")
            if str(row["equation_choice_audited"]).strip().lower() != "true":
                raise ValueError(f"row {line}: equation selection not audited")
            key = (bioma, uf, ua)
            if key in seen:
                raise ValueError(f"row {line}: repeated sampling UA; equations are not independent units")
            seen.add(key)
            try:
                value = float(row["agb_mg_ha"])
            except ValueError as exc:
                raise ValueError(f"row {line}: invalid AGB") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"row {line}: AGB must be finite and nonnegative")
            strata[(bioma, uf, fito)].append(value)
    if not strata:
        raise ValueError("no units")
    results = []
    for (bioma, uf, fito), values in sorted(strata.items()):
        n = len(values)
        avg = statistics.mean(values)
        sample_sd = statistics.stdev(values) if n > 1 else None
        results.append({"biome": bioma, "state": uf, "fitofisionomia_ibge": fito,
                        "independent_ua_count": n, "mean_agb_mg_ha": avg,
                        "sample_sd_agb_mg_ha": sample_sd,
                        "descriptive_se_mg_ha": sample_sd / math.sqrt(n) if n > 1 else None,
                        "aoi_ci95_validated": False,
                        "scientifically_validated": False})
    return {"source_sha256": digest, "sampling_unit": "IFN UA", "strata": results,
            "warning": "Unweighted descriptive UA summary only. Not an AOI estimate or validated CI95; "
                       "requires sampling-design weights, spatial crosswalk and independent transfer validation."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    result = summarize(args.csv, args.sha256)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"strata": len(result["strata"]), "aoi_ci95_validated": False}))

if __name__ == "__main__":
    main()
