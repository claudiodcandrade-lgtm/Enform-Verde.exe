"""Explicit local JSON manifest for experimental inventory evidence.

This loader does not verify field data, licenses or transfer metrics. Validation
is performed downstream, and scientific release requires independent auditing.
Never fetch arbitrary URLs or execute code embedded in a manifest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_native_inventory_manifest(path, *, max_bytes=5_000_000):
    source=Path(path)
    size=source.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ValueError("inventory JSON is empty or exceeds the 5 MB limit")
    payload=source.read_bytes()
    try:
        data=json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid UTF-8 JSON inventory manifest") from exc
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError('manifest must contain a "records" array')
    records=data["records"]
    if not records or len(records)>5000 or not all(isinstance(x,dict) for x in records):
        raise ValueError("records must contain 1 to 5000 inventory objects")
    for i,row in enumerate(records):
        # These are mandatory audit controls. The selector performs additional
        # biologic/measurement and uncertainty compatibility checks.
        if not all(isinstance(row.get(k),str) and row[k].strip() for k in
                   ("biome","physiognomy","pool","source","source_url","institution")):
            raise ValueError(f"record {i} lacks source or biome/fitofisionomia provenance")
        if row.get("licensed_for_use") is not True:
            raise ValueError(f"record {i} must declare a verifiable reuse license")
    return {
        "records": records,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "filename": source.name,
        "evidence_status": "EXTERNAL_UNVERIFIED_NOT_HOMOLOGATED",
        "source_file_path": str(source.resolve()),
    }
