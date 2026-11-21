#!/usr/bin/env python3
"""Attach IFN sampling-unit centers to the official IBGE legenda_1 layer.

This is a potential-phytoregion lookup at the IFN unit-center scale. It does
not assign a vegetation class to each tree or prove current native cover.
Boundary/multiple/no-match points remain ineligible for exact-physiognomy
selection rather than being guessed into a class.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "national_inventory_microdata_v1.sqlite"
ZIP = DATA / "external_raw" / "ibge_vegetation_2026" / "vege_area.zip"
URL = "https://geoftp.ibge.gov.br/informacoes_ambientais/vegetacao/vetores/escala_250_mil/versao_2026/vege_area.zip"


def build_crosswalk(db_path: Path = DB, vegetation_zip: Path = ZIP) -> dict:
    if not db_path.is_file():
        raise FileNotFoundError("IFN_MICRODATA_DB_NOT_FOUND")
    if not vegetation_zip.is_file():
        raise FileNotFoundError("IBGE_VEGETATION_2026_LAYER_NOT_FOUND")
    with sqlite3.connect(db_path) as source_conn:
        units = pd.read_sql_query(
            "SELECT ua_id, uf, biome, municipality, ua_center_lon, ua_center_lat "
            "FROM ifn_sampling_unit_summary ORDER BY uf, ua_id", source_conn)
    units["ua_center_lon"] = pd.to_numeric(units.ua_center_lon, errors="coerce")
    units["ua_center_lat"] = pd.to_numeric(units.ua_center_lat, errors="coerce")
    valid = units.dropna(subset=["ua_center_lon", "ua_center_lat"]).copy()
    points = gpd.GeoDataFrame(valid, geometry=gpd.points_from_xy(
        valid.ua_center_lon, valid.ua_center_lat), crs="EPSG:4674")
    polygons = gpd.read_file(f"zip://{vegetation_zip.resolve().as_posix()}",
        columns=["cd_fito", "legenda_1"], engine="pyogrio")
    if polygons.crs is None:
        raise RuntimeError("IBGE_VEGETATION_LAYER_MISSING_CRS")
    if not {"cd_fito", "legenda_1"}.issubset(polygons.columns):
        raise RuntimeError("IBGE_VEGETATION_LAYER_MISSING_LEGENDA_1")
    points = points.to_crs(polygons.crs)
    joined = gpd.sjoin(points, polygons[["cd_fito", "legenda_1", "geometry"]],
                       how="left", predicate="within")
    joined_by_unit={key:frame for key,frame in joined.groupby(["uf","ua_id"],dropna=False)}
    rows = []
    for _, unit in units.iterrows():
        key = (unit.uf, unit.ua_id)
        subset = joined_by_unit.get(key,joined.iloc[0:0]) if pd.notna(unit.ua_center_lon) and pd.notna(unit.ua_center_lat) else joined.iloc[0:0]
        matches = subset[subset.legenda_1.notna()]
        unique = matches[["cd_fito", "legenda_1"]].drop_duplicates()
        if len(unique) == 1:
            code, label = unique.iloc[0][["cd_fito", "legenda_1"]]
            status = "MATCH_UNICO_PONTO_INTERIOR"
        elif len(unique) > 1:
            code, label, status = None, None, "AMBIGUO_MULTIPLAS_LEGENDAS_1"
        elif pd.isna(unit.ua_center_lon) or pd.isna(unit.ua_center_lat):
            code, label, status = None, None, "SEM_COORDENADA_UA"
        else:
            code, label, status = None, None, "SEM_POLIGONO_INTERSECTADO"
        rows.append((unit.ua_id, unit.uf, unit.biome, unit.municipality,
                     float(unit.ua_center_lon) if pd.notna(unit.ua_center_lon) else None,
                     float(unit.ua_center_lat) if pd.notna(unit.ua_center_lat) else None,
                     str(code) if code is not None else None,
                     str(label).strip() if label is not None else None,
                     status, URL, "Vegetação IBGE 2026 1:250.000; legenda_1; associação pelo centro da UA IFN"))
    source_digest=hashlib.sha256()
    with vegetation_zip.open("rb") as source_stream:
        for chunk in iter(lambda:source_stream.read(1024*1024),b""):
            source_digest.update(chunk)
    source_hash = source_digest.hexdigest()
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS ifn_sampling_unit_ibge_crosswalk (
            ua_id TEXT NOT NULL, uf TEXT NOT NULL, source_biome TEXT, municipality TEXT,
            ua_center_lon REAL, ua_center_lat REAL, ibge_cd_fito TEXT, ibge_legenda_1 TEXT,
            match_status TEXT NOT NULL, source_url TEXT NOT NULL, method TEXT NOT NULL,
            source_sha256 TEXT NOT NULL, PRIMARY KEY(ua_id,uf))""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ifn_ibge_selection ON ifn_sampling_unit_ibge_crosswalk(source_biome,ibge_legenda_1,uf)")
        conn.execute("DELETE FROM ifn_sampling_unit_ibge_crosswalk")
        conn.executemany("INSERT INTO ifn_sampling_unit_ibge_crosswalk VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         [row + (source_hash,) for row in rows])
        conn.commit()
        counts = dict(conn.execute("SELECT match_status,COUNT(*) FROM ifn_sampling_unit_ibge_crosswalk GROUP BY match_status"))
    return {"sampling_units": len(rows), "vegetation_sha256": source_hash,
            "status_counts": counts,
            "eligible_unique_matches": counts.get("MATCH_UNICO_PONTO_INTERIOR", 0),
            "interpretation": "IBGE potential phytoregion assigned at IFN sampling-unit center; not per-tree location or current cover."}


if __name__ == "__main__":
    import json, requests
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    if not ZIP.is_file():
        with requests.get(URL, stream=True, timeout=(20, 180)) as response:
            response.raise_for_status()
            with ZIP.open("wb") as out:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        out.write(chunk)
    report=build_crosswalk()
    db_hash=hashlib.sha256()
    with DB.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            db_hash.update(chunk)
    report["database_sha256"]=db_hash.hexdigest()
    report["database_size_bytes"]=DB.stat().st_size
    ingestion=DATA/"official_inventory_microdata_ingestion_v1.json"
    if ingestion.is_file():
        metadata=json.loads(ingestion.read_text(encoding="utf-8"))
        metadata["database_sha256"]=report["database_sha256"]
        metadata["database_size_bytes"]=report["database_size_bytes"]
        metadata.setdefault("ifn",{})["ibge_spatial_crosswalk"]={
            "sampling_units":report["sampling_units"],
            "unique_matches":report["eligible_unique_matches"],
            "status_counts":report["status_counts"],
            "ibge_vegetation_source_sha256":report["vegetation_sha256"],
            "method":"IFN sampling-unit center within exactly one IBGE Vegetação 2026 polygon; legenda_1; no per-tree coordinates inferred"}
        ingestion.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    (DATA/"ifn_ibge_crosswalk_audit_v1.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
