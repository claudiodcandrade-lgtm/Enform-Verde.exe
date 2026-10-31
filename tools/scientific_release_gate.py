#!/usr/bin/env python3
"""Fail-closed evidence gate for scientific release, separate from building Windows ZIP.

A successful CI build, mock, literature mean, discovery-only SAR scene or synthetic
validation can never be interpreted as independent scientific homologation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

BIOMES = {"Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal"}
POOLS = {"agb", "roots", "standing_deadwood", "downed_deadwood", "litter", "soil_0_100"}
SECTIONS = {"biomes", "sar", "carbon", "agriculture", "weather",
            "vigor", "yield", "executive_panel", "performance", "regression", "windows"}

def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def _provenance(row, label, errors):
    if not isinstance(row, dict):
        errors.append(f"{label}: expected evidence object")
        return False
    for field in ("source_url", "dataset_sha256", "observed_at", "aoi_id", "validation_report"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            errors.append(f"{label}: missing provenance {field}")
    digest = row.get("dataset_sha256", "")
    if not re.fullmatch("[0-9a-fA-F]{64}", str(digest)):
        errors.append(f"{label}: dataset_sha256 is not a SHA-256 digest")
    if row.get("evidence_type") != "independent_real_data":
        errors.append(f"{label}: independent real data required (not synthetic, bibliography or catalog)")
    if row.get("status") != "passed":
        errors.append(f"{label}: outcome is not passed")
    return True

def _verify_local_report(row, label, errors, root):
    """Check that cited validation results actually exist and are integrity-pinned."""
    if not isinstance(row, dict) or row.get("status") != "passed":
        return
    report = row.get("validation_report")
    digest = row.get("validation_report_sha256")
    if not isinstance(report, str) or not report.strip():
        errors.append(f"{label}: validation report path missing")
        return
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        errors.append(f"{label}: validation_report_sha256 required")
        return
    target = (root / report).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: validation report escapes evidence directory")
        return
    if not target.is_file():
        errors.append(f"{label}: validation report file absent")
        return
    try:
        actual = hashlib.sha256(target.read_bytes()).hexdigest().lower()
    except OSError as exc:
        errors.append(f"{label}: validation report unreadable ({type(exc).__name__})")
        return
    if actual != digest.lower():
        errors.append(f"{label}: validation report hash mismatch")
        return
    # A checksum pins bytes, not scientific content. Refuse opaque or
    # internally inconsistent reports even when their digest is correct.
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        errors.append(f"{label}: validation report must be valid JSON")
        return
    if not isinstance(payload, dict):
        errors.append(f"{label}: validation report must be a JSON object")
        return
    if payload.get("dataset_sha256") != row.get("dataset_sha256"):
        errors.append(f"{label}: validation report dataset hash mismatch")
    if payload.get("evidence_type") in ("synthetic", "fixture", "literature_mean", "catalog_discovery"):
        errors.append(f"{label}: synthetic/catalog report cannot validate real observations")
    # Spatially independent metrics are mandatory for scientific inference;
    # a successful executable smoke test is not a scientific validation.
    scientific = (label.startswith("biomes[") or label.startswith("carbon[")
                  or label in ("sar", "agriculture", "vigor", "yield"))
    if scientific:
        n = payload.get("independent_sample_count")
        train = payload.get("train_spatial_units")
        test = payload.get("test_spatial_units")
        if type(n) is not int or n <= 0:
            errors.append(f"{label}: independent sample count absent")
        if type(train) is not int or train < 1:
            errors.append(f"{label}: independent training spatial units absent")
        if type(test) is not int or test < 2 or (type(n) is int and n < test):
            errors.append(f"{label}: independent test spatial units invalid")
        p_train, p_test = payload.get("train_partition"), payload.get("test_partition")
        if not (isinstance(p_train, str) and p_train.strip()
                and isinstance(p_test, str) and p_test.strip()
                and p_train != p_test):
            errors.append(f"{label}: independent train/test partitions absent or identical")
        if not isinstance(payload.get("validation_design"), str) or not payload["validation_design"].strip():
            errors.append(f"{label}: independent validation design absent")
        for metric in ("rmse", "mae", "bias"):
            value = payload.get(metric)
            if not _is_number(value) or (metric != "bias" and value < 0):
                errors.append(f"{label}: invalid independent {metric}")
        if label.startswith("carbon[") or label == "yield":
            coverage = payload.get("interval_coverage")
            if not _is_number(coverage) or not 0 <= coverage <= 1:
                errors.append(f"{label}: measured interval coverage required; descriptive bounds are not validated IC95")


def _verify_local_dataset(row, label, errors, root):
    """Release requires the actual observation bytes, not a plausible digest."""
    if not isinstance(row, dict) or row.get("status") != "passed":
        return
    relative = row.get("dataset_file")
    if not isinstance(relative, str) or not relative.strip():
        errors.append(f"{label}: raw dataset_file required for independent evidence")
        return
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        errors.append(f"{label}: raw dataset escapes evidence directory")
        return
    if not target.is_file():
        errors.append(f"{label}: raw dataset file absent")
        return
    try:
        observed = hashlib.sha256(target.read_bytes()).hexdigest()
    except OSError:
        errors.append(f"{label}: raw dataset unreadable")
        return
    if observed.lower() != str(row.get("dataset_sha256", "")).lower():
        errors.append(f"{label}: raw dataset hash mismatch")


def assess(evidence, expected_sha, evidence_root=None):
    errors = []
    if not isinstance(evidence, dict):
        return ["Root must be an evidence object"]
    if evidence.get("source_sha") != expected_sha or not re.fullmatch("[0-9a-fA-F]{40}", expected_sha):
        errors.append("source_sha must equal the exact 40-character tested branch HEAD")
    missing = SECTIONS - set(evidence)
    if missing:
        errors.append("Missing scientific evidence sections: " + ", ".join(sorted(missing)))
    rows = evidence.get("biomes", [])
    if not isinstance(rows, list):
        rows = []
    names = set()
    for i, row in enumerate(rows):
        label = f"biomes[{i}]"
        if not _provenance(row, label, errors):
            continue
        name = row.get("biome")
        names.add(name)
        if name not in BIOMES:
            errors.append(f"{label}: unsupported biome {name!r}")
        for field in ("rmse_mg_ha", "bias_mg_ha", "mae_mg_ha", "r2", "independent_plot_count"):
            if not _is_number(row.get(field)):
                errors.append(f"{label}: missing independent validation metric {field}")
        if _is_number(row.get("r2")) and row["r2"] > 1:
            errors.append(f"{label}: r2 cannot exceed 1")
        for metric in ("rmse_mg_ha", "mae_mg_ha"):
            if _is_number(row.get(metric)) and row[metric] < 0:
                errors.append(f"{label}: {metric} must be nonnegative")
        if not isinstance(row.get("independent_plot_count"), int) or row.get("independent_plot_count", 0) <= 0:
            errors.append(f"{label}: independent sample count must be positive")
    if names != BIOMES:
        errors.append("Missing independently validated biomes: " + ", ".join(sorted(BIOMES - names)))
    sar = evidence.get("sar")
    if _provenance(sar, "sar", errors):
        for field in ("scene_id", "acquisition_utc", "band", "method", "calibration_split", "test_split"):
            if not isinstance(sar.get(field), str) or not sar[field].strip():
                errors.append(f"sar: missing {field}")
        if sar.get("calibration_split") == sar.get("test_split"):
            errors.append("sar: calibration/test splits must be spatially independent")
        if sar.get("data_access") != "downloaded_and_processed":
            errors.append("sar: catalog discovery alone is not processed satellite data")
    carbon = evidence.get("carbon", [])
    if not isinstance(carbon, list):
        carbon = []
    covered = set()
    for i, row in enumerate(carbon):
        label = f"carbon[{i}]"
        if not _provenance(row, label, errors):
            continue
        pair = (row.get("biome"), row.get("pool"))
        covered.add(pair)
        if pair[1] not in POOLS or pair[0] not in BIOMES:
            errors.append(f"{label}: invalid biome/pool")
        for field in ("stock_tc_ha", "ci95_lower_tc_ha", "ci95_upper_tc_ha"):
            if not _is_number(row.get(field)):
                errors.append(f"{label}: missing numeric uncertainty field {field}")
        if all(_is_number(row.get(f)) for f in ("stock_tc_ha", "ci95_lower_tc_ha", "ci95_upper_tc_ha")):
            if not row["ci95_lower_tc_ha"] <= row["stock_tc_ha"] <= row["ci95_upper_tc_ha"]:
                errors.append(f"{label}: invalid 95% uncertainty interval")
        if row.get("pool") == "soil_0_100" and row.get("depth_cm") != [0, 100]:
            errors.append(f"{label}: soil must explicitly cover 0-100 cm")
        if row.get("uncertainty_includes_transfer_error") is not True:
            errors.append(f"{label}: uncertainty must include spatial/model transfer error")
    for biome in BIOMES:
        for pool in POOLS:
            if (biome, pool) not in covered:
                errors.append(f"carbon: missing {pool} in {biome}")
    for section in ("agriculture", "weather", "vigor", "yield", "executive_panel", "performance", "regression", "windows"):
        row = evidence.get(section)
        if _provenance(row, section, errors):
            if section == "agriculture":
                acc = row.get("independent_accuracy")
                if not _is_number(acc):
                    errors.append("agriculture: actual independent classification accuracy missing")
                elif not 0 <= acc <= 1:
                    errors.append("agriculture: independent_accuracy must be a fraction between 0 and 1")
            if section == "yield" and row.get("mode") not in ("independently_validated_forecast", "forecast_blocked_without_valid_model"):
                errors.append("yield: forecast must be validated or visibly blocked")
            if section == "vigor" and row.get("mode") not in ("validated_classes", "vigor_blocked_without_valid_model"):
                errors.append("vigor: classes must be validated or visibly blocked")
            if section == "windows":
                if row.get("source_sha") != expected_sha:
                    errors.append("windows: tested EXE source SHA differs from release SHA")
                if not re.fullmatch("[0-9a-fA-F]{64}", str(row.get("exe_sha256", ""))):
                    errors.append("windows: EXE SHA-256 missing")
                if not re.fullmatch("[0-9a-fA-F]{64}", str(row.get("zip_sha256", ""))):
                    errors.append("windows: ZIP SHA-256 missing")
                if not str(row.get("artifact_url", "")).startswith("https://github.com/"):
                    errors.append("windows: real GitHub artifact URL missing")
                if row.get("clean_windows_smoke") is not True:
                    errors.append("windows: extracted EXE clean-machine smoke absent")
    if evidence_root is not None:
        root = Path(evidence_root)
        for section in SECTIONS:
            item = evidence.get(section)
            if isinstance(item, list):
                for i, row in enumerate(item):
                    _verify_local_dataset(row, f"{section}[{i}]", errors, root)
                    _verify_local_report(row, f"{section}[{i}]", errors, root)
            else:
                _verify_local_dataset(item, section, errors, root)
                _verify_local_report(item, section, errors, root)
    return errors

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="validation/release_evidence.json")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--report", default="release_gate_report.json")
    args = parser.parse_args(argv)
    path = Path(args.evidence)
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        evidence = {}
        reason = f"Evidence manifest unavailable or invalid: {type(exc).__name__}: {exc}"
    else:
        reason = ""
    errors = assess(evidence, args.source_sha, path.parent)
    if reason:
        errors.insert(0, reason)
    report = {"source_sha": args.source_sha, "homologated": not errors,
              "blockers": errors, "evidence_path": str(path)}
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
