#!/usr/bin/env python3
"""Audit IFN/SFB pairwise allometric-equation equivalence without transitivity.

TOST equivalence only supports *pairwise comparison*. It never validates
SAR/AGB predictions, uncertainty for an AOI, or the accuracy of either equation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

FIELDS = ("bioma", "tipologia", "equacao_1", "equacao_2", "reject_intercept", "reject_slope", "equivalente")

def _bool(value):
    v = str(value).strip().casefold()
    if v in ("true", "verdadeiro", "1", "sim"):
        return True
    if v in ("false", "falso", "0", "não", "nao"):
        return False
    raise ValueError("TOST rejection flag is not boolean")

def _equivalence_label(value):
    v = str(value).strip().casefold()
    if v in ("equivalente", "true", "sim"):
        return True
    if v in ("não equivalente", "nao equivalente", "false", "não", "nao"):
        return False
    raise ValueError("TOST equivalence label is unknown")

def audit(path, expected_sha256):
    raw = Path(path).read_bytes()
    observed_digest = hashlib.sha256(raw).hexdigest()
    if observed_digest.lower() != str(expected_sha256).lower():
        raise ValueError("TOST dataset checksum mismatch")
    pairs = {}
    count = equivalent_count = 0
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(field not in reader.fieldnames for field in FIELDS):
            raise ValueError("TOST mandatory columns absent")
        for line_number, row in enumerate(reader, 2):
            biome, typology = str(row["bioma"]).strip(), str(row["tipologia"]).strip()
            eq1, eq2 = str(row["equacao_1"]).strip(), str(row["equacao_2"]).strip()
            if not all((biome, typology, eq1, eq2)) or eq1 == eq2:
                raise ValueError(f"row {line_number}: incomplete domain/equations or self-comparison")
            a = _bool(row["reject_intercept"])
            b = _bool(row["reject_slope"])
            verdict = _equivalence_label(row["equivalente"])
            if verdict != (a and b):
                raise ValueError(f"row {line_number}: TOST label conflicts with reject flags")
            key = (biome, typology, *sorted((eq1, eq2)))
            if key in pairs and pairs[key] != verdict:
                raise ValueError(f"row {line_number}: contradictory duplicate pair")
            pairs[key] = verdict
            count += 1
            equivalent_count += verdict
    if count == 0:
        raise ValueError("empty TOST dataset")
    return {"source_sha256": observed_digest, "comparisons": count,
            "distinct_pairs": len(pairs), "equivalent_rows": equivalent_count,
            "not_equivalent_rows": count - equivalent_count,
            "pair_verdicts": pairs}

def pair_decision(audited, biome, typology, equation_a, equation_b):
    if not all(isinstance(x, str) and x.strip() for x in
               (biome, typology, equation_a, equation_b)):
        return "not_assessed"
    if equation_a == equation_b:
        return "same_equation"
    key = (biome, typology, *sorted((equation_a, equation_b)))
    verdict = audited["pair_verdicts"].get(key)
    return "not_assessed" if verdict is None else ("equivalent_pairwise" if verdict else "not_equivalent_pairwise")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--biome", required=True)
    parser.add_argument("--typology", required=True)
    parser.add_argument("--equation-a", required=True)
    parser.add_argument("--equation-b", required=True)
    args = parser.parse_args()
    result = audit(args.csv, args.sha256)
    print(json.dumps({
        "source_sha256": result["source_sha256"],
        "comparisons": result["comparisons"],
        "distinct_pairs": result["distinct_pairs"],
        "pair_status": pair_decision(result, args.biome, args.typology,
                                     args.equation_a, args.equation_b),
        "scientific_validation": False,
        "warning": "Pairwise TOST is neither transitive nor SAR/AOI accuracy validation."
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
