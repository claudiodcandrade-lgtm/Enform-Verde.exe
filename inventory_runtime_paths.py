"""Paths for the external inventory database shipped beside the desktop app."""
from __future__ import annotations

import os
import sys
from pathlib import Path


DATABASE_NAME = "national_inventory_microdata_v1.sqlite"
MANIFEST_NAME = "national_inventory_microdata_v1.manifest.json"


def runtime_data_dir() -> Path:
    """Return the adjacent data folder, never PyInstaller's internal bundle."""
    override = os.environ.get("ENFORM_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parent / "data"


def inventory_database_path() -> Path:
    return runtime_data_dir() / DATABASE_NAME


def inventory_manifest_path(db_path: str | Path | None = None) -> Path:
    database = Path(db_path) if db_path is not None else inventory_database_path()
    return database.with_name(MANIFEST_NAME)
