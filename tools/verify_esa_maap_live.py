#!/usr/bin/env python3
"""ESA MAAP real-data integration probe. Credential only from environment.

Run: ESA_MAAP_OFFLINE_TOKEN=<secret> python tools/verify_esa_maap_live.py
       --bbox WEST SOUTH EAST NORTH [--download]

No token, authorization header, private AOI geometry or signed asset URL is logged.
Without --download: authenticates, discovers FH scenes, verifies HTTP range access.
With --download: attempts to download an FH raster and read valid AOI pixels.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import requests
    import geopandas as gpd
    from shapely.geometry import box
    import sar_pipeline as sp

    parser = argparse.ArgumentParser()
    parser.add_argument("--bbox", required=True, type=float, nargs=4,
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--cache", default="maap_probe_cache")
    args = parser.parse_args()

    token = os.environ.get("ESA_MAAP_OFFLINE_TOKEN", "").strip()
    if not token:
        print(json.dumps({"status": "N/D", "stage": "authentication",
                          "reason": "ESA_MAAP_OFFLINE_TOKEN environment secret absent"}))
        return 2

    w, s, e, n = args.bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        print(json.dumps({"status": "ERROR", "stage": "AOI", "reason": "invalid bbox"}))
        return 2
    aoi = gpd.GeoDataFrame(geometry=[box(w, s, e, n)], crs="EPSG:4326")

    # Exchange the offline token without writing it to any file or log.
    try:
        bearer = sp.maap_access_token(token)
    except Exception as ex:
        print(json.dumps({"status": "ERROR", "stage": "authentication",
                          "error_type": type(ex).__name__}))
        return 3
    print(json.dumps({"stage": "authentication", "status": "ACCESS_TOKEN_ISSUED"}))

    try:
        items = sp.biomass_l2b_search(aoi, limit=30)
        fh = [x for x in items if x.get("_product_type") in
              ("FP_FH__L2A", "FP_FH__L2B")]
    except Exception as ex:
        print(json.dumps({"status": "ERROR", "stage": "discovery",
                          "error_type": type(ex).__name__}))
        return 4
    print(json.dumps({"stage": "discovery", "status": "OK" if fh else "NO_FH_PRODUCTS",
                      "fh_count": len(fh),
                      "product_types": sorted({x.get("_product_type") for x in fh})}))
    if not fh:
        return 5

    asset = next(((x, key, url) for x in fh for key, url in
                  sp._biomass_product_assets(x, x["_product_type"])), None)
    if asset is None:
        print(json.dumps({"stage": "assets", "status": "NO_DOWNLOADABLE_FH_ASSET"}))
        return 6
    _, key, url = asset

    # Real authenticated byte-range request, without exposing the URL.
    try:
        with requests.get(url, headers={"Authorization": "Bearer " + bearer,
                                       "Range": "bytes=0-1023"},
                          timeout=(15, 60), stream=True, allow_redirects=True) as response:
            status_code = response.status_code
            response.raise_for_status()
            fragment = next(response.iter_content(chunk_size=1024), b"")
        print(json.dumps({"stage": "asset_http", "status": "READABLE",
                          "http_status": status_code, "bytes_read": len(fragment),
                          "asset_key": key}))
    except Exception as ex:
        print(json.dumps({"stage": "asset_http", "status": "ERROR",
                          "error_type": type(ex).__name__}))
        return 7

    if not args.download:
        print(json.dumps({"stage": "pixels", "status": "NOT_TESTED",
                          "reason": "rerun with --download to process actual FH pixels"}))
        return 0

    # The production download adapter is exercised in the full test.
    # This can transfer large official products; user opts in explicitly.
    try:
        result = sp.download_maap_height(aoi, token, args.cache, items=fh)
        import rasterio
        from rasterio.mask import mask
        from rasterio.warp import transform_geom
        import numpy as np
        for path in result.get("paths") or []:
            with rasterio.open(path) as src:
                geom = transform_geom("EPSG:4326", src.crs,
                                      aoi.geometry.iloc[0].__geo_interface__)
                try:
                    pixels, _ = mask(src, [geom], crop=True, filled=False)
                except ValueError:
                    continue
                values = np.ma.asarray(pixels[0], dtype=float).compressed()
                valid = values[np.isfinite(values) & (values > 0)]
                if valid.size:
                    print(json.dumps({"stage": "pixels", "status": "FH_PIXELS_READ",
                                      "valid_pixels": int(valid.size),
                                      "mean_height_m": float(valid.mean()),
                                      "product_type": "FH"}))
                    return 0
        print(json.dumps({"stage": "pixels", "status": "NO_VALID_FH_PIXELS",
                          "downloaded_raster_count": len(result.get("paths") or []),
                          "errors_count": len(result.get("errors") or [])}))
        return 8
    except Exception as ex:
        print(json.dumps({"stage": "pixels", "status": "ERROR",
                          "error_type": type(ex).__name__}))
        return 9


if __name__ == "__main__":
    raise SystemExit(main())
