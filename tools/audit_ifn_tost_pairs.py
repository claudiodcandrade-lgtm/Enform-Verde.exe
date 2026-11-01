#!/usr/bin/env python3
"""Audit IFN/SFB pairwise allometric-equation equivalence without transitivity.

TOST equivalence only supports *pairwise comparison*. It never validates
SAR/AGB predictions, uncertainty for an AOI, or the accuracy of either equation.
"""
import argparse
import csv
import hashlib
import io
import json
import unicodedata
from pathlib import Path
from openpyxl import load_workbook

FIELDS = ("bioma", "tipologia", "equacao_1", "equacao_2", "reject_intercept", "reject_slope", "equivalente")


def _identity(value):
    return unicodedata.normalize("NFKC", str(value or "").strip()).casefold()


def _records(raw):
    """Read the licensed SFB file by payload magic, not its misleading suffix."""
    if raw.startswith(b"PK\x03\x04"):
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        try:
            iterator = iter(workbook.active.iter_rows(values_only=True))
            headers = list(next(iterator, ()))
            rows = []
            for values in iterator:
                if not any(value not in (None, "") for value in values):
                    continue
                if len(values) > len(headers) and any(
                        value not in (None, "") for value in values[len(headers):]):
                    raise ValueError("TOST unexpected extra workbook columns")
                rows.append(dict(zip(headers, values)))
        finally:
            workbook.close()
    else:
        try:
            decoded = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = raw.decode("cp1252")
        reader = csv.DictReader(io.StringIO(decoded))
        headers = reader.fieldnames or []
        rows = list(reader)
    if not headers or any(not isinstance(h, str) or not h.strip() for h in headers):
        raise ValueError("TOST blank or missing headers")
    normalized_headers = [_identity(h) for h in headers]
    if len(normalized_headers) != len(set(normalized_headers)):
        raise ValueError("TOST duplicate headers")
    if any(field not in headers for field in FIELDS):
        raise ValueError("TOST mandatory columns absent")
    if any(None in row for row in rows):
        raise ValueError("TOST unexpected extra CSV columns")
    return rows

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
    for line_number, row in enumerate(_records(raw), 2):
        biome, typology = _identity(row["bioma"]), _identity(row["tipologia"])
        eq1, eq2 = _identity(row["equacao_1"]), _identity(row["equacao_2"])
        if not all((biome, typology, eq1, eq2)) or eq1 == eq2:
            raise ValueError(f"row {line_number}: incomplete domain/equations or self-comparison")
        a = _bool(row["reject_intercept"])
        b = _bool(row["reject_slope"])
        verdict = _equivalence_label(row["equivalente"])
        if verdict != (a and b):
            raise ValueError(f"row {line_number}: TOST label conflicts with reject flags")
        key = (biome, typology, *sorted((eq1, eq2)))
        if key in pairs:
            if pairs[key] != verdict:
                raise ValueError(f"row {line_number}: contradictory duplicate pair")
            raise ValueError(f"row {line_number}: duplicate pair (not independent evidence)")
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
    biome, typology, equation_a, equation_b = map(_identity, (biome, typology, equation_a, equation_b))
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
