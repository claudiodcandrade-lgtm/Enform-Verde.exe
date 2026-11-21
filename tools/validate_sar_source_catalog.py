#!/usr/bin/env python3
"""Validate the packaged national SAR/reference source registry."""
import csv
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "data" / "sar_data_sources_brazil_v1.csv"
REQUIRED = {
    "ORNL_GTDX_AMAZON_25M", "JAXA_ALOS_PALSAR_GLOBAL_MOSAIC",
    "ESA_BIOMASS_L1C_P", "ESA_BIOMASS_L2B_P", "ESA_CCI_BIOMASS_V7",
    "NASA_NISAR_GCOV_L", "NASA_GEDI_L2A_L2B", "SFB_IFN_PRIMARY_TREES",
}
FIELDS = {
    "source_id", "mission_band", "data_type", "access_state_2026_10_04",
    "download_or_catalog_url", "height_role", "agb_role", "uncertainty_and_limitations",
}

def main():
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise SystemExit(f"Missing catalog columns: {FIELDS - set(reader.fieldnames or [])}")
        rows = list(reader)
        for line_number, row in enumerate(rows, start=2):
            if None in row or any(value is None for value in row.values()):
                raise SystemExit(f"Malformed CSV column count at line {line_number}")
    ids = [row.get("source_id", "").strip() for row in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate source_id in SAR registry")
    missing = REQUIRED - set(ids)
    if missing:
        raise SystemExit(f"Missing priority source records: {sorted(missing)}")
    for row in rows:
        if not all(row.get(k, "").strip() for k in FIELDS):
            raise SystemExit(f"Incomplete source metadata: {row.get('source_id')}")
    print(f"SAR_SOURCE_CATALOG_OK rows={len(rows)} missions= X/L/P + lidar/inventory")
if __name__ == "__main__":
    main()
