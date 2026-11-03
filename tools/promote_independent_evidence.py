#!/usr/bin/env python3
"""Promote independently verified raw data + model reports into modular manifest.

Never synthesize observations or metrics. A candidate only becomes a capability
when its raw dataset and report SHA256 hashes verify AND modular checks pass.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
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
        # Retain the raw file pointer: downstream gate must independently
        # rehash the observations, not trust the promoter or a JSON digest.
        audit = assess({"source_sha": source_sha, "capabilities": [record]}, source_sha, root)
        if not audit["passed"] or audit["validated_count"] != 1:
            errors.extend(f"{candidate_path.name}: {msg}" for msg in audit["errors"])
            continue
        accepted.append(record)
    if not accepted:
        errors.append("No independently validated candidate with verified source bytes and report")
        return {"promoted": False, "errors": errors, "accepted_count": 0,
                "rejected_count": len(errors), "partial": False}, None
    # Modular homologation must not discard independently verified capabilities
    # merely because an unrelated candidate was rejected. Preserve every
    # rejection in the audit; never include a rejected row in the manifest.
    # This does NOT approve the whole scientific release.
    result = {"source_sha": source_sha, "capabilities": accepted}
    final_audit = assess(result, source_sha, root)
    if not final_audit["passed"]:
        return {"promoted": False, "errors": final_audit["errors"], "accepted_count": 0}, None
    return {"promoted": True, "errors": errors, "accepted_count": len(accepted),
            "rejected_count": len(errors), "partial": bool(errors)}, result

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
    manifest_path = Path(args.manifest)
    if manifest is not None:
        # Replace atomically: never expose a truncated manifest to the next gate.
        import os
        import tempfile
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            prefix=".modular_manifest_", suffix=".json", dir=manifest_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(manifest, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, manifest_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    else:
        # Fail closed: a previously promoted manifest on the same workspace
        # must never survive an unsuccessful current evidence acquisition.
        # Otherwise the next 'if: always()' modular gate could read stale data.
        manifest_path.unlink(missing_ok=True)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["promoted"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
