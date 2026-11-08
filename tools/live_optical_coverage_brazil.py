#!/usr/bin/env python3
"""Live optical-background smoke checks across Brazilian regions/extremes.

This is a distributed sample, not a proof for every pixel. It verifies that
the app resolves real imagery pixels with >=95% AOI coverage at each site.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

import sys

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
        ):
            try:
                image = fn(gdf, out_w=420, out_h=280, extent_factor=1.36) if sensor != "Sentinel-2 Planetary Computer" else fn(gdf, out_h=280, extent_factor=1.36)
                coverage = float(image.get("aoi_coverage_fraction", 0.0))
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
            failures[name] = errors
            results[name] = {"status": "no_optical_pixels", "attempts": errors}
    report = {
        "scope": "CBERS-4A primary, Sentinel-2 fallback; representative biomes, geographic extremes, and Sinop AOI centroid",
        "sample_sites": len(SITES),
        "primary_cbers_successful_sites": len(SITES) - len(cbers_failures),
        "successful_optical_sites": len(SITES) - len(failures),
        "coverage_threshold": 0.95,
        "exhaustive_national_pixel_proof": False,
        "cbers_primary_failures": cbers_failures,
        "fallback_failures": failures,
        "results": results,
    }
    output = Path("optical_coverage_brazil_smoke.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(f"Neither CBERS-4A nor Sentinel-2 resolved optical imagery for {len(failures)} of {len(SITES)} sample AOIs")
    if cbers_failures:
        raise SystemExit(f"CBERS-4A primary imagery did not meet coverage at {len(cbers_failures)} of {len(SITES)} sample AOIs; Sentinel-2 successes are fallback only")


if __name__ == "__main__":
    main()
