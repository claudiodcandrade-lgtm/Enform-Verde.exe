#!/usr/bin/env python3
"""Validate prompt and Word specification synchronization.

Binary Word updates are generated from a reviewed docs/spec_updates checkpoint
in a separate bot commit. Requiring the binary in the ORIGINAL code commit
rejects valid updates and obscures the separate build/source SHA.
"""
import subprocess
import sys
from pathlib import Path

SPEC = "docs/ESPECIFICACAO_TECNICA_COMPLETA.docx"
PROMPT = "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md"
SYNC = ".github/workflows/sync-full-spec-word.yml"

def effective(path):
    if path in (SPEC,PROMPT) or path.startswith("docs/"):
        return False
    return path.endswith((".py",".yml",".yaml",".csv",".gz",".json",".txt")) or path.startswith(".github/")

def check(changed, *, workflow_text=None, word_exists=None):
    eff=sorted(p for p in changed if effective(p))
    if not eff:return eff,[]
    missing=[]
    if PROMPT not in changed:missing.append(PROMPT)
    if SPEC not in changed:
        if workflow_text is None:
            workflow_text=Path(SYNC).read_text(encoding="utf-8") if Path(SYNC).exists() else ""
        if word_exists is None:
            word_exists=Path(SPEC).is_file()
        checkpoints=[p for p in changed if p.startswith("docs/spec_updates/") and p.endswith(".md")]
        active=bool(word_exists and checkpoints and any(
            ("- "+p) in workflow_text and ("--entry "+p) in workflow_text
            for p in checkpoints))
        if not active:
            missing.append(SPEC+" or reviewed checkpoint with active Word sync")
    return eff,missing

def main(base,head):
    out=subprocess.run(["git","diff","--name-only",f"{base}..{head}"],
                       capture_output=True,text=True,check=True)
    changed=set(filter(None,out.stdout.splitlines()))
    effective_files,missing=check(changed)
    print(f"effective changes: {len(effective_files)}; docs missing: {missing or 'none'}")
    for item in missing:print(f"::error::{item}")
    return 1 if missing else 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
