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

import desktop_app as app


SITES = {
    "Tapajos_Amazonia": (-54.9, -3.7),
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
    failures, results = {}, {}
    for name, (lon, lat) in SITES.items():
        geometry = box(lon - 0.08, lat - 0.08, lon + 0.08, lat + 0.08)
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")
        errors = []
        for sensor, fn in (
            ("Sentinel-2 Earth Search", app.sentinel2_earthsearch_preview),
            ("Sentinel-2 Planetary Computer", app.sentinel2_preview),
            ("CBERS-4A/WFI INPE", app.cbers4a_wfi_preview),
        ):
            try:
                image = fn(gdf, out_w=420, out_h=280, extent_factor=1.36) if sensor != "Sentinel-2 Planetary Computer" else fn(gdf, out_h=280, extent_factor=1.36)
                coverage = float(image.get("aoi_coverage_fraction", 0.0))
                if image["image"].size[0] <= 0 or image["image"].size[1] <= 0 or coverage < 0.95:
                    raise RuntimeError(f"image/pixel coverage invalid: {coverage:.3f}")
                results[name] = {
                    "status": "real_pixels_loaded", "sensor": sensor,
                    "provider": image.get("provider"), "datetime": image.get("datetime"),
                    "date_range": image.get("date_range"),
                    "aoi_coverage_fraction": coverage,
                    "pixel_count": image.get("pixel_count"),
                    "resolution_m": image.get("resolution_m"),
                }
                break
            except Exception as exc:
                errors.append(f"{sensor}: {type(exc).__name__}: {str(exc)[:160]}")
                time.sleep(0.5)
        else:
            failures[name] = errors
            results[name] = {"status": "no_optical_pixels", "attempts": errors}
    report = {"scope": "representative_biomes_and_geographic_extremes",
              "sample_sites": len(SITES), "successful_sites": sum(v["status"] == "real_pixels_loaded" for v in results.values()),
              "coverage_threshold": 0.95, "exhaustive_national_pixel_proof": False,
              "results": results, "failures": failures}
    output = Path("optical_coverage_brazil_smoke.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(f"Optical imagery was not resolved for {len(failures)} of {len(SITES)} Brazilian sample AOIs")


if __name__ == "__main__":
    main()
