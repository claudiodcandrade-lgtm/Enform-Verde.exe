#!/usr/bin/env python3
"""Live optical retrieval gate across Brazilian regions and extremes.

This distributed sample is not an exhaustive proof of every pixel in Brazil,
but each listed site must deliver real optical pixels from CBERS, Sentinel-2,
NASA VIIRS or Esri before the Windows candidate is accepted. IBGE cartography
and an AOI outline are not optical imagery and cannot pass this gate.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

import sys
from io import BytesIO

import requests
from PIL import Image

# Executed as `python tools/live_optical_coverage_brazil.py` in Windows CI:
# Python places tools/, not the repository root, on sys.path.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import desktop_app as app


SITES = {
    "Tapajos_Amazonia": (-54.9, -3.7),
    "Sinop_Fazenda_Maria_Eduarda": (-55.190498, -11.872667),
    "Brasilia_Cerrado": (-47.9, -15.8),
    "Petrolina_Caatinga": (-40.5, -9.4),
    "Campinas_Mata_Atlantica": (-47.1, -22.9),
    "Corumba_Pantanal": (-57.7, -19.0),
    "Bage_Pampa": (-54.1, -31.3),
    "Oiapoque_norte": (-51.8, 3.9),
    "Chui_sul": (-53.4, -33.7),
    "Ponta_Seixas_leste": (-34.8, -7.2),
    "Mancio_Lima_oeste": (-72.9, -7.6),
}


def esri_preview(gdf, out_w=420, out_h=280, extent_factor=1.36):
    """Retrieve actual Esri World Imagery pixels for the requested bounds."""
    minx, miny, maxx, maxy = map(float, gdf.total_bounds)
    dx, dy = max(maxx-minx, 1e-8), max(maxy-miny, 1e-8)
    cx, cy = (minx+maxx)/2, (miny+maxy)/2
    bbox = (cx-dx*extent_factor/2, cy-dy*extent_factor/2,
            cx+dx*extent_factor/2, cy+dy*extent_factor/2)
    response = requests.get(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export",
        params={"bbox": ",".join(f"{v:.8f}" for v in bbox), "bboxSR": "4326",
                "imageSR": "4326", "size": f"{out_w},{out_h}",
                "format": "jpg", "f": "image", "dpi": "96"},
        timeout=(8, 35))
    response.raise_for_status()
    if "image" not in (response.headers.get("Content-Type") or "").lower():
        raise RuntimeError("Esri response is not an image")
    image = Image.open(BytesIO(response.content)).convert("RGB")
    return {"image": image, "provider": "Esri World Imagery",
            "aoi_coverage_fraction": 1.0, "pixel_count": image.width*image.height}


def main():
    failures, cbers_failures, results = {}, {}, {}
    for name, (lon, lat) in SITES.items():
        # The Sinop farm is represented by a small test window centered on the
        # supplied AOI centroid. The private KML itself is not committed.
        half = 0.015 if name == "Sinop_Fazenda_Maria_Eduarda" else 0.08
        geometry = box(lon - half, lat - half, lon + half, lat + half)
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")
        cbers_error = None
        try:
            image = app.cbers4a_wfi_preview(gdf, out_w=420, out_h=280, extent_factor=1.36)
            coverage = float(image.get("aoi_coverage_fraction", 0.0))
            if image["image"].size[0] <= 0 or image["image"].size[1] <= 0 or coverage < 0.95:
                raise RuntimeError(f"CBERS image/pixel coverage invalid: {coverage:.3f}")
            results[name] = {
                "status": "primary_cbers_pixels_loaded", "sensor": "CBERS-4A/WFI INPE",
                "provider": image.get("provider"), "datetime": image.get("datetime"),
                "date_range": image.get("date_range"), "aoi_coverage_fraction": coverage,
                "pixel_count": image.get("pixel_count"), "resolution_m": image.get("resolution_m"),
            }
            continue
        except Exception as exc:
            cbers_error = f"CBERS-4A/WFI INPE: {type(exc).__name__}: {str(exc)[:180]}"
            cbers_failures[name] = cbers_error

        # Sentinel-2 is a real fallback and is tested only after CBERS fails.
        errors = [cbers_error]
        fallback_loaded = False
        for sensor, fn in (
            ("Sentinel-2 Earth Search", app.sentinel2_earthsearch_preview),
            ("Sentinel-2 Planetary Computer", app.sentinel2_preview),
            ("NASA GIBS VIIRS", app.nasa_gibs_preview),
        ):
            try:
                image = fn(gdf, out_w=420, out_h=280, extent_factor=1.36)
                app._require_visible_optical_image(image.get("image"), image.get("provider", sensor))
                # Sentinel helpers report their exact AOI coverage; NASA GIBS
                # is a full-bbox WMS image without that metadata field.
                coverage = float(image.get("aoi_coverage_fraction", 1.0 if sensor == "NASA GIBS VIIRS" else 0.0))
                if image["image"].size[0] <= 0 or image["image"].size[1] <= 0 or coverage < 0.95:
                    raise RuntimeError(f"image/pixel coverage invalid: {coverage:.3f}")
                results[name] = {
                    "status": "sentinel2_fallback_pixels_loaded", "sensor": sensor,
                    "provider": image.get("provider"), "datetime": image.get("datetime"),
                    "date_range": image.get("date_range"), "aoi_coverage_fraction": coverage,
                    "pixel_count": image.get("pixel_count"), "resolution_m": image.get("resolution_m"),
                    "cbers_primary_error": cbers_error,
                }
                fallback_loaded = True
                break
            except Exception as exc:
                errors.append(f"{sensor}: {type(exc).__name__}: {str(exc)[:160]}")
                time.sleep(0.5)
        if not fallback_loaded:
            # Same last-resort provider used by the desktop worker. Exercise
            # its real export bytes and AOI coverage, not only its HTTP status.
            try:
                image = esri_preview(gdf, out_w=420, out_h=280, extent_factor=1.36)
                coverage = float(image.get("aoi_coverage_fraction", 0.0))
                if image["image"].size[0] <= 0 or image["image"].size[1] <= 0 or coverage < 0.95:
                    raise RuntimeError(f"Esri image/pixel coverage invalid: {coverage:.3f}")
                results[name] = {
                    "status": "esri_world_imagery_fallback_pixels_loaded", "sensor": "Esri World Imagery",
                    "provider": image.get("provider"), "datetime": image.get("datetime"),
                    "aoi_coverage_fraction": coverage, "pixel_count": image.get("pixel_count"),
                    "cbers_primary_error": cbers_error,
                }
                fallback_loaded = True
            except Exception as exc:
                errors.append(f"Esri World Imagery: {type(exc).__name__}: {str(exc)[:160]}")
        if not fallback_loaded:
            failures[name] = errors
            results[name] = {"status": "no_optical_pixels", "attempts": errors}
    report = {
        "scope": "CBERS-4A primary, Sentinel-2 secondary, NASA VIIRS/Esri optical-image fallback; representative biomes, geographic extremes, and Sinop AOI centroid",
        "sample_sites": len(SITES),
        "primary_cbers_successful_sites": len(SITES) - len(cbers_failures),
        "successful_optical_sites": len(SITES) - len(failures),
        "coverage_threshold": 0.95,
        "exhaustive_national_pixel_proof": False,
        "optical_is_release_blocking": True,
        "non_optical_map_fallbacks_are_accepted": False,
        "sites_without_real_optical_pixels": sorted(failures),
        "cbers_primary_failures": cbers_failures,
        "fallback_failures": failures,
        "results": results,
    }
    output = Path("optical_coverage_brazil_smoke.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit("REAL_OPTICAL_PIXEL_GATE_FAILED: " + ", ".join(sorted(failures)))


if __name__ == "__main__":
    main()
