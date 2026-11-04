#!/usr/bin/env python3
"""User rule (2026-11-03): every effective step updates BOTH the full technical
specification (docs/ESPECIFICACAO_TECNICA_COMPLETA.docx) and the continuity
prompt (docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md).

Usage in CI:  python tools/check_docs_updated.py <base_sha> <head_sha>
Fails when any code/data/workflow file changed in base..head but either
document did not change in the same range.
"""
import subprocess
import sys

SPEC = "docs/ESPECIFICACAO_TECNICA_COMPLETA.docx"
PROMPT = "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md"


def effective(path):
    if path in (SPEC, PROMPT) or path.startswith("docs/"):
        return False
    return path.endswith((".py", ".yml", ".yaml", ".csv", ".gz", ".json", ".txt")) or path.startswith(".github/")


def check(changed):
    eff = sorted(p for p in changed if effective(p))
    missing = [d for d in (SPEC, PROMPT) if d not in changed] if eff else []
    return eff, missing


def main(base, head):
    out = subprocess.run(["git", "diff", "--name-only", f"{base}..{head}"], capture_output=True, text=True, check=True)
    changed = set(filter(None, out.stdout.splitlines()))
    eff, missing = check(changed)
    print(f"effective changes: {len(eff)}; documents missing: {missing or 'none'}")
    for m in missing:
        print(f"::error::{m} must be updated in the same change set as code/data/workflows")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
