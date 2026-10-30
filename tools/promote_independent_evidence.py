#!/usr/bin/env python3
"""Promote independently verified raw data + model reports into modular manifest.

Never synthesize observations or metrics. A candidate only becomes a capability
when its raw dataset and report SHA256 hashes verify AND modular checks pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
from tools.modular_scientific_gate import assess

def promote(source_sha, root, candidates):
    root = Path(root).resolve()
    errors, accepted = [], []
    for candidate_path in sorted(Path(candidates).glob("*.json")):
        try:
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{candidate_path.name}: invalid JSON ({type(exc).__name__})")
            continue
        if not isinstance(candidate, dict) or candidate.get("status") != "validated":
            errors.append(f"{candidate_path.name}: only independently validated candidates may be promoted")
            continue
        relative = candidate.get("dataset_file")
        if not isinstance(relative, str) or not relative.strip():
            errors.append(f"{candidate_path.name}: missing raw dataset_file")
            continue
        dataset = (root / relative).resolve()
        if not dataset.is_relative_to(root) or not dataset.is_file():
            errors.append(f"{candidate_path.name}: raw dataset absent/outside evidence root")
            continue
        try:
            observed = hashlib.sha256(dataset.read_bytes()).hexdigest()
        except OSError:
            errors.append(f"{candidate_path.name}: raw dataset unreadable")
            continue
        if observed.lower() != str(candidate.get("dataset_sha256", "")).lower():
            errors.append(f"{candidate_path.name}: raw dataset SHA256 mismatch")
            continue
        record = dict(candidate)
        record.pop("dataset_file", None)
        audit = assess({"source_sha": source_sha, "capabilities": [record]}, source_sha, root)
        if not audit["passed"] or audit["validated_count"] != 1:
            errors.extend(f"{candidate_path.name}: {msg}" for msg in audit["errors"])
            continue
        accepted.append(record)
    if not accepted:
        errors.append("No independently validated candidate with verified source bytes and report")
    if errors:
        return {"promoted": False, "errors": errors, "accepted_count": len(accepted)}, None
    result = {"source_sha": source_sha, "capabilities": accepted}
    final_audit = assess(result, source_sha, root)
    if not final_audit["passed"]:
        return {"promoted": False, "errors": final_audit["errors"], "accepted_count": 0}, None
    return {"promoted": True, "errors": [], "accepted_count": len(accepted)}, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--root", default="validation")
    parser.add_argument("--candidates", default="validation/evidence_candidates")
    parser.add_argument("--manifest", default="validation/modular_capabilities.json")
    parser.add_argument("--audit", default="modular_promotion_audit.json")
    args = parser.parse_args()
    audit, manifest = promote(args.source_sha, args.root, args.candidates)
    Path(args.audit).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if manifest is not None:
        Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["promoted"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
