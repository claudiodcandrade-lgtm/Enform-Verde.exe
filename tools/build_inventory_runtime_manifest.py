#!/usr/bin/env python3
"""Create the immutable runtime manifest after the IFN SQLite is materialized."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(db_path: Path, harvest_path: Path, output_path: Path) -> dict:
    db_path=db_path.resolve()
    harvest=json.loads(harvest_path.read_text(encoding="utf-8"))
    workbooks=harvest.get("state_workbooks") or []
    hashes={str(row.get("sha256") or "").lower() for row in workbooks}
    hashes.discard("")
    if not db_path.is_file() or not workbooks or len(hashes)!=len(workbooks):
        raise ValueError("IFN_DATABASE_OR_HARVEST_PROVENANCE_INCOMPLETE")

    with sqlite3.connect(db_path.as_uri()+"?mode=ro",uri=True,timeout=10) as conn:
        conn.execute("PRAGMA query_only=ON")
        tables={row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        required={"ifn_dap10_observation","ifn_sampling_unit_summary",
                  "ifn_sampling_unit_ibge_crosswalk","source_dataset"}
        if not required.issubset(tables):
            raise ValueError("IFN_REQUIRED_TABLES_MISSING")
        source=conn.execute("SELECT row_count,unit_count FROM source_dataset "
            "WHERE dataset_id='IFN_DAP10_SET2025'").fetchone()
        summary_units=int(conn.execute(
            "SELECT COUNT(*) FROM ifn_sampling_unit_summary").fetchone()[0])
        matched_units=int(conn.execute("SELECT COUNT(*) "
            "FROM ifn_sampling_unit_ibge_crosswalk "
            "WHERE match_status='MATCH_UNICO_PONTO_INTERIOR'").fetchone()[0])

    if not source:
        raise ValueError("IFN_SOURCE_DATASET_METADATA_MISSING")
    observations=int(source[0]); units=int(source[1] or 0)
    harvested=int(harvest.get("total_valid_dap_records") or harvest.get("total_rows") or 0)
    if (observations!=harvested or units!=summary_units or matched_units!=units
            or len(workbooks)!=27 or observations!=841387 or units!=8951):
        raise ValueError("IFN_MATERIALIZED_DATABASE_DOES_NOT_MATCH_HARVEST_CONTRACT")

    database_sha256=sha256_file(db_path)
    manifest={
        "manifest_version":1,
        "database_file":db_path.name,
        "database_size_bytes":db_path.stat().st_size,
        "database_sha256":database_sha256,
        "expected_database_sha256":database_sha256,
        "observation_rows":observations,
        "sampling_units":units,
        "ibge_unique_unit_matches":matched_units,
        "source_workbooks":len(workbooks),
        "source_workbook_hashes":len(hashes),
        "verification":"generated after IFN harvest/ingest/crosswalk; full database SHA-256 checked at build; runtime validates size, schema and source metadata without scanning tree records"
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--database",default="data/national_inventory_microdata_v1.sqlite")
    parser.add_argument("--harvest",default="data/ifn_dap10_set2025_harvest_manifest.json")
    parser.add_argument("--output",default="data/national_inventory_microdata_v1.manifest.json")
    args=parser.parse_args()
    print(json.dumps(build_manifest(Path(args.database),Path(args.harvest),Path(args.output)),ensure_ascii=False))


if __name__=="__main__":
    main()
