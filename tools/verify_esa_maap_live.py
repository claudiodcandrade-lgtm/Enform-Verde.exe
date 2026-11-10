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



def catalog_diagnostics(aoi, expand_degrees=0.5):
    """Diagnose STAC search without misreporting HTTP errors as no coverage.

    Read only public catalog metadata: no credential or private geometry in logs.
    Expanded search is diagnostic only and never constitutes AOI coverage.
    """
    import requests
    import sar_pipeline as sp
    w, s, e, n = map(float, aoi.total_bounds)
    scopes = [
        ("AOI", [w, s, e, n]),
        ("REGIONAL_CONTEXT", [max(-180, w-expand_degrees),
                              max(-90, s-expand_degrees),
                              min(180, e+expand_degrees),
                              min(90, n+expand_degrees)])
    ]
    out = []
    for label, bbox in scopes:
        for collection in ("BiomassLevel2a", "BiomassLevel2aIOC",
                           "BiomassLevel2b", "BiomassLevel2bIOC"):
            row = {"stage": "catalog_probe", "scope": label, "collection": collection}
            try:
                # Official MAAP STAC GET search accepts bbox CSV and collection id.
                response = requests.get(sp.MAAP_STAC + "search",
                    params={"collections": collection,
                            "bbox": ",".join(map(str, bbox)), "limit": 100},
                    timeout=(15, 75))
                row["http_status"] = response.status_code
                response.raise_for_status()
                payload = response.json()
                features = payload.get("features", [])
                types = set()
                for item in features:
                    types.update(sp._biomass_item_product_types(item))
                row["status"] = "OK"
                row["returned_items"] = len(features)
                row["fh_recognized"] = sum(
                    bool({"FP_FH__L2A", "FP_FH__L2B"} &
                         set(sp._biomass_item_product_types(item)))
                    for item in features)
                row["product_types_seen"] = sorted(types)
                row["next_page"] = bool(any(link.get("rel") == "next"
                    for link in payload.get("links", [])))
            except Exception as ex:
                row["status"] = "ERROR"
                row["error_type"] = type(ex).__name__
                # No exception messages: they can contain signed URLs or
                # internal request details.
            out.append(row)
    return out


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
        diagnostics = catalog_diagnostics(aoi)
        for item in diagnostics:
            print(json.dumps(item))
        success = [item for item in diagnostics
                   if item["scope"] == "AOI" and item["status"] == "OK"]
        fh_found = any(item.get("fh_recognized", 0) > 0 for item in success)
        print(json.dumps({"stage": "discovery_diagnosis",
                          "status": ("FILTER_OR_POST_SEARCH_MISMATCH" if fh_found
                                    else "AOI_CATALOG_ERROR" if len(success) < 4
                                    else "NO_FH_IN_FIRST_100_PER_COLLECTION"),
                          "successful_collections": len(success)}))
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
