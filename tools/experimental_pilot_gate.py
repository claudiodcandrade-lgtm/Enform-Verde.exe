#!/usr/bin/env python3
"""Check pre-field model readiness without claiming empirical validation."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path


def _symbols(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return set()
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def assess(manifest: dict, source_sha: str, root: str | Path) -> dict:
    root = Path(root).resolve()
    errors, models, seen = [], [], set()
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        errors.append("source_sha must be a full commit SHA")
    if manifest.get("profile") != "pre_field_experimental":
        errors.append("profile must be pre_field_experimental")
    rows = manifest.get("models")
    if not isinstance(rows, list) or not rows:
        errors.append("models must be a non-empty list")
        rows = []
    protocol = manifest.get("field_validation_protocol")
    protocol_path = (root / protocol).resolve() if isinstance(protocol, str) else root / "__missing__"
    if not protocol_path.is_relative_to(root) or not protocol_path.is_file():
        errors.append("prospective field-validation protocol missing or outside repository")
    for i, row in enumerate(rows):
        label = f"models[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: expected object")
            continue
        model_id = row.get("model_id")
        if not isinstance(model_id, str) or not model_id.strip() or model_id in seen:
            errors.append(f"{label}: model_id missing or duplicated")
            continue
        seen.add(model_id)
        if row.get("status") != "pre_field_experimental":
            errors.append(f"{label}: status must remain pre_field_experimental")
        if row.get("field_validation_status") != "pending":
            errors.append(f"{label}: field validation must be explicitly pending")
        for key in ("purpose", "equation_or_method", "output_units", "uncertainty_semantics",
                    "domain_limits", "abstention_rule", "source_document"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(f"{label}: {key} required")
        source_doc = row.get("source_document")
        if isinstance(source_doc, str):
            source_path = (root / source_doc).resolve()
            if not source_path.is_relative_to(root) or not source_path.is_file():
                errors.append(f"{label}: source document missing or outside repository")
        if any(key in row for key in ("accuracy", "rmse", "mae", "bias", "validated")):
            errors.append(f"{label}: pre-field model cannot claim empirical validation metrics")
        module = row.get("module")
        entrypoint = row.get("entrypoint")
        if not isinstance(module, str) or not isinstance(entrypoint, str):
            errors.append(f"{label}: module and entrypoint required")
            continue
        target = (root / module).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(f"{label}: model module missing or outside repository")
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if entrypoint not in _symbols(target):
            errors.append(f"{label}: declared entrypoint not found in model module")
        models.append({"model_id": model_id, "module": module, "entrypoint": entrypoint,
                       "module_sha256": digest, "status": "pre_field_experimental",
                       "field_validation_status": "pending"})
    passed = not errors
    return {"passed": passed, "source_sha": source_sha, "profile": "pre_field_experimental",
            "models": models if passed else [], "model_count": len(models) if passed else 0,
            "field_validation": "pending", "scientifically_homologated": False,
            "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="validation/experimental_models.json")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--report", default="experimental_pilot_gate_report.json")
    args = parser.parse_args()
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        result = assess(manifest, args.source_sha, path.parent.parent)
        repo_root = path.parent.parent.resolve()
        if (repo_root / ".git").exists():
            actual_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root,
                                        check=True, capture_output=True, text=True).stdout.strip()
            if actual_sha != args.source_sha:
                result["passed"] = False
                result["errors"].append("source_sha does not match checked-out repository HEAD")
                result["models"] = []
                result["model_count"] = 0
            tracked_paths = [args.manifest] + [row.get("module", "") for row in manifest.get("models", [])
                                               if isinstance(row, dict)]
            diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *tracked_paths],
                                  cwd=repo_root, capture_output=True, text=True)
            if diff.returncode != 0:
                result["passed"] = False
                result["errors"].append("model modules or manifest differ from the checked-out source SHA")
                result["models"] = []
                result["model_count"] = 0
    except (OSError, ValueError, AttributeError) as exc:
        result = {"passed": False, "source_sha": args.source_sha,
                  "profile": "pre_field_experimental", "models": [], "model_count": 0,
                  "field_validation": "pending", "scientifically_homologated": False,
                  "errors": [f"manifest unavailable or invalid: {type(exc).__name__}: {exc}"]}
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
