#!/usr/bin/env python3
"""Materialize a source-SHA-bound scientific evidence manifest at CI runtime.

A committed JSON file cannot contain the SHA of its own commit without a
self-reference paradox. Commit only the evidence TEMPLATE (actual provenance,
dataset hashes, validation reports, source data). The CI creates a transient
manifest with the exact checked-out source SHA, then independently runs the
fail-closed scientific release gate. This tool never creates evidence, sets
'passed', changes statistics, or accepts an incomplete evidence template.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.scientific_release_gate import SECTIONS

PLACEHOLDER = "__RUNTIME_SOURCE_SHA__"


def materialize(template, source_sha):
    if not isinstance(template, dict):
        raise ValueError("evidence template must be a JSON object")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", source_sha):
        raise ValueError("tested source SHA must be 40 hexadecimal characters")
    claimed = template.get("source_sha")
    if claimed not in (None, PLACEHOLDER):
        raise ValueError("template must not pin a stale or self-referential source SHA")
    missing = SECTIONS - set(template)
    if missing:
        raise ValueError("evidence template lacks required sections: " + ", ".join(sorted(missing)))
    # Deep copy through JSON: prevents mutation of input and forbids opaque
    # Python objects that would not serialize to a portable evidence manifest.
    payload = json.loads(json.dumps(template, allow_nan=False))
    payload["source_sha"] = source_sha
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--template", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    template = Path(args.template).resolve()
    output = Path(args.output).resolve()
    if template == output:
        raise SystemExit("evidence template cannot be overwritten by runtime manifest")
    if not template.is_file():
        raise SystemExit("independent evidence template unavailable; no manifest materialized")
    payload = json.loads(template.read_text(encoding="utf-8"))
    result = materialize(payload, args.source_sha)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps({"source_sha": args.source_sha,
                      "template_sections": sorted(SECTIONS),
                      "status": "materialized_not_scientifically_approved"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
