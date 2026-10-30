#!/usr/bin/env python3
"""Recompute independent spatial-holdout error metrics from observed-vs-predicted CSV.

This is NOT a model and cannot create scientific observations. Input must contain
real measured plot values and genuinely independently predicted held-out plots.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

REQUIRED = ("observed", "predicted", "lower", "upper", "partition", "spatial_unit")

def validate_csv(path, dataset_sha256, unit):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest.lower() != dataset_sha256.lower():
        raise ValueError("source dataset sha256 mismatch")
    if not unit or not isinstance(unit, str):
        raise ValueError("measurement unit required")
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        if not rows.fieldnames or any(field not in rows.fieldnames for field in REQUIRED):
            raise ValueError("missing mandatory measured/predicted/interval/partition columns")
        records = list(rows)
    if not records:
        raise ValueError("no observations")
    partitions = {"train": set(), "test": set()}
    test = []
    for number, row in enumerate(records, 2):
        p = str(row["partition"]).strip().lower()
        if p not in partitions:
            raise ValueError(f"row {number}: partition must be train or test")
        group = str(row["spatial_unit"]).strip()
        if not group:
            raise ValueError(f"row {number}: spatial_unit missing")
        partitions[p].add(group)
        try:
            values = tuple(float(row[name]) for name in ("observed", "predicted", "lower", "upper"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"row {number}: values not numeric") from exc
        if not all(math.isfinite(x) for x in values):
            raise ValueError(f"row {number}: nonfinite measurement")
        observed, predicted, lower, upper = values
        if lower > upper:
            raise ValueError(f"row {number}: invalid prediction interval")
        if p == "test":
            test.append(values)
    if not partitions["train"] or not partitions["test"] or partitions["train"] & partitions["test"]:
        raise ValueError("training and test spatial units must be nonempty and disjoint")
    if len(test) < 2:
        raise ValueError("at least two independent test observations required")
    n = len(test)
    errors = [predicted - observed for observed, predicted, _, _ in test]
    rmse = math.sqrt(sum(error * error for error in errors) / n)
    mae = sum(abs(error) for error in errors) / n
    bias = sum(errors) / n
    coverage = sum(lower <= observed <= upper for observed, _, lower, upper in test) / n
    measured = [row[0] for row in test]
    mean = sum(measured) / n
    total = sum((x - mean) ** 2 for x in measured)
    r2 = None if total == 0 else 1 - sum(e * e for e in errors) / total
    return {
        "dataset_sha256": digest,
        "independent_sample_count": n,
        "rmse": rmse, "mae": mae, "bias": bias, "r2": r2,
        "interval_coverage": coverage, "interval_n_nominal": n,
        "train_partition": "train (independent spatial units)",
        "test_partition": "test (independent spatial units)",
        "validation_design": "externally supplied independent spatial holdout; spatial-unit disjointness checked",
        "train_spatial_units": len(partitions["train"]),
        "test_spatial_units": len(partitions["test"]),
        "unit": unit,
        "method_limitations": (
            "CSV values and independence are supplied by the producer; this program "
            "verifies partition disjointness but not whether predictions were fitted "
            "without access to held-out measurements or whether field data are real."
        ),
        "interval_kind": "empirical coverage of supplied per-observation intervals; not AOI IC95%"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    result = validate_csv(args.csv, args.dataset_sha256, args.unit)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"independent_sample_count": result["independent_sample_count"],
                      "rmse": result["rmse"], "interval_coverage": result["interval_coverage"],
                      "report": args.report}, ensure_ascii=False))

if __name__ == "__main__":
    main()
