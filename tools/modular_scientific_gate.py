#!/usr/bin/env python3
"""Modular scientific evidence assessment, separate from national release approval."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

BIOMES = {"Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal"}
POOLS = {"agb", "roots", "standing_deadwood", "downed_deadwood", "litter", "soil_0_100"}
STATUSES = {"validated", "experimental", "not_available"}

def _check_independent_report(payload, row, label, errors):
    """Confirm independent metrics exist; a digest by itself is not validation."""
    if not isinstance(payload, dict):
        errors.append(f"{label}: validation report must be a JSON object")
        return
    if payload.get("dataset_sha256") != row.get("dataset_sha256"):
        errors.append(f"{label}: report dataset hash does not match source")
    n = payload.get("independent_sample_count")
    if type(n) is not int or n <= 0:
        errors.append(f"{label}: independent sample count missing")
    for field in ("rmse", "mae", "bias", "interval_coverage"):
        value = payload.get(field)
        if type(value) not in (int, float) or not math.isfinite(value):
            errors.append(f"{label}: invalid independent {field}")
        elif field in ("rmse", "mae") and value < 0:
            errors.append(f"{label}: {field} cannot be negative")
        elif field == "interval_coverage" and not 0 <= value <= 1:
            errors.append(f"{label}: interval_coverage must lie in [0,1]")
    if payload.get("train_partition") == payload.get("test_partition") or not all(
            isinstance(payload.get(k), str) and payload[k].strip()
            for k in ("train_partition", "test_partition", "validation_design", "unit")):
        errors.append(f"{label}: independent validation split/design/unit absent")

def assess(manifest, source_sha, root):
    errors, rows_out, seen = [], [], set()
    if not isinstance(manifest, dict):
        return {"passed": False, "errors": ["Manifest must be an object"], "capabilities": []}
    if not re.fullmatch(r"[0-9a-fA-F]{40}", str(source_sha)) or manifest.get("source_sha") != source_sha:
        errors.append("source_sha must equal tested commit")
    rows = manifest.get("capabilities")
    if not isinstance(rows, list):
        return {"passed": False, "errors": errors + ["capabilities must be a list"], "capabilities": []}
    root = Path(root).resolve()
    if not rows:
        errors.append("No capabilities declared")
    for i, row in enumerate(rows):
        label = f"capabilities[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: expected object")
            continue
        biome, pool, physio = row.get("biome"), row.get("pool"), row.get("fitofisionomia")
        if not isinstance(biome, str) or not isinstance(pool, str) or not isinstance(physio, str) or not physio.strip():
            errors.append(f"{label}: invalid biome/pool/fitofisionomia types")
            continue
        key = (biome, pool, physio)
        if biome not in BIOMES or pool not in POOLS:
            errors.append(f"{label}: invalid biome/pool/fitofisionomia")
            continue
        if key in seen:
            errors.append(f"{label}: duplicate capability")
            continue
        seen.add(key)
        status = row.get("status")
        if status not in STATUSES:
            errors.append(f"{label}: invalid status")
            continue
        if status == "not_available":
            if not str(row.get("reason", "")).strip():
                errors.append(f"{label}: N/D requires reason")
        else:
            if status == "validated" and row.get("evidence_type") != "independent_real_data":
                errors.append(f"{label}: validation requires independent real data")
            if status == "experimental" and not str(row.get("reason", "")).strip():
                errors.append(f"{label}: experimental requires limitations")
            for field in ("source_url", "dataset_sha256", "validation_report",
                          "validation_report_sha256", "uncertainty_kind", "domain",
                          "transfer_error_method"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{label}: missing {field}")
            for field in ("dataset_sha256", "validation_report_sha256"):
                if not re.fullmatch(r"[0-9a-fA-F]{64}", str(row.get(field, ""))):
                    errors.append(f"{label}: invalid {field}")
            report = row.get("validation_report")
            if isinstance(report, str) and report.strip():
                target = (root / report).resolve()
                if not target.is_relative_to(root):
                    errors.append(f"{label}: report outside evidence root")
                elif not target.is_file():
                    errors.append(f"{label}: report absent")
                else:
                    try:
                        actual = hashlib.sha256(target.read_bytes()).hexdigest()
                    except OSError:
                        errors.append(f"{label}: report unreadable")
                    else:
                        if actual.lower() != str(row.get("validation_report_sha256", "")).lower():
                            errors.append(f"{label}: report hash mismatch")
                        elif status == "validated":
                            try:
                                payload = json.loads(target.read_text(encoding="utf-8"))
                            except (OSError, ValueError, UnicodeError):
                                errors.append(f"{label}: independent report must be valid JSON")
                            else:
                                _check_independent_report(payload, row, label, errors)
            if pool == "soil_0_100" and row.get("depth_cm") != [0, 100]:
                errors.append(f"{label}: soil requires 0-100 cm")
        rows_out.append({"biome": biome, "pool": pool, "fitofisionomia": physio, "status": status})
    # A failed registry must never advertise approved capability counts.
    passed = not errors
    return {"passed": passed, "errors": errors, "capabilities": rows_out,
            "validated_count": (sum(r["status"] == "validated" for r in rows_out) if passed else 0),
            "experimental_count": (sum(r["status"] == "experimental" for r in rows_out) if passed else 0),
            "not_available_count": (sum(r["status"] == "not_available" for r in rows_out) if passed else 0),
            "scientifically_homologated": passed and any(r["status"] == "validated" for r in rows_out)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="validation/modular_capabilities.json")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--report", default="modular_gate_report.json")
    args = parser.parse_args()
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        result = {"passed": False, "errors": [f"Manifest unavailable: {exc}"], "capabilities": []}
    else:
        result = assess(manifest, args.source_sha, path.parent)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Registry integrity alone (including N/D-only registry) never passes scientific CI.
    return 0 if result.get("scientifically_homologated") is True else 1

if __name__ == "__main__":
    raise SystemExit(main())
