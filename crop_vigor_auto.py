"""Automatic three-class vigor for a field from the latest Sentinel-1 RTC scene.

1. Latest Sentinel-1 RTC (Microsoft Planetary Computer, anonymous SAS) within
   ``window_days`` that covers the field; VV/VH γ⁰ read only in a window of
   field + ``ring_km`` (COG range reads), converted to dB.
2. Reference fields: square blocks (≈ field area) in the ring whose pixels are
   ≥ 80 % of the SAME MapBiomas C11 class as the field (e.g. 39 soja), read
   from the official public GeoTIFF and resampled (nearest) to the S1 grid.
   Same scene, same date, same region → comparable phenology.
3. crop_vigor.classify_vigor (robust z, terciles, spatial bootstrap).
Status remains experimental (no field truth of vigor).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

MIN_REFERENCE_BLOCKS = 6


def _local_mapbiomas():
    """Same local sources accepted by land_use_sar (env var, ~/.enform_verde caches)."""
    import os
    from pathlib import Path
    from mapbiomas_zonal import YEAR
    env = os.environ.get("ENFORM_MAPBIOMAS_LOCAL_TIF", "").strip()
    if env and Path(env).is_file():
        return env
    root = Path.home() / ".enform_verde"
    for d in (root / "mapbiomas", root / "cache" / "mapbiomas", root / "uso_solo", root / "dados" / "mapbiomas"):
        for name in (f"brazil_coverage-col11_{YEAR}.tif", f"mapbiomas_brazil_collection11_coverage_{YEAR}.tif"):
            if (d / name).is_file():
                return str(d / name)
    return None


def _scene(field_4326, as_of, window_days, search):
    from shapely.geometry import mapping
    end = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=timezone.utc)
    end = min(end, datetime.now(timezone.utc))
    found = search(mapping(field_4326), start_utc=end - timedelta(days=window_days), end_utc=end)
    for s in found["scenes"]:
        if {"vv", "vh"} <= set(s["assets"]) and "VH" in (s.get("polarizations") or ["VH"]):
            return s
    return None


def automatic_vigor(field_gdf, as_of, mapbiomas_class, *, ring_km=8.0, window_days=24,
                    search=None, token_fn=None, mapbiomas_url=None, max_px=2500):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import geometry_mask
    from rasterio.warp import reproject, transform_geom
    from rasterio.windows import from_bounds
    from shapely.geometry import box, mapping, shape

    from crop_vigor import classify_vigor, field_metrics
    from mapbiomas_zonal import RASTER_URL, YEAR
    from sentinel1_mpc import _signed_href, get_runtime_sas_token, search_sentinel1_rtc

    search = search or search_sentinel1_rtc
    token_fn = token_fn or get_runtime_sas_token
    g = field_gdf.to_crs(4326).geometry.union_all()
    scene = _scene(g, as_of, window_days, search)
    if scene is None:
        return {"status": "N/D", "reason": f"sem cena Sentinel-1 RTC VV/VH nos últimos {window_days} dias",
                "search_window_days": window_days, "as_of": as_of.isoformat()}
    # Catalog entries alone are not evidence of current, acquired SAR pixels.
    # Reject stale/future scene dates even if a custom STAC backend returns them.
    acquired = datetime.fromisoformat(str(scene.get("acquisition_utc", "")).replace("Z", "+00:00"))
    reference = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=timezone.utc)
    if acquired.tzinfo is None:
        return {"status": "N/D", "reason": "cena sem timezone de aquisição", "scene_id": scene["id"]}
    age_days = (reference - acquired.astimezone(timezone.utc)).total_seconds() / 86400.0
    if age_days < 0 or age_days > window_days:
        return {"status": "N/D", "reason": f"cena fora da janela de atualidade de {window_days} dias",
                "scene_id": scene["id"], "acquisition_utc": scene["acquisition_utc"],
                "scene_age_days": age_days}
    token = token_fn()
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"):
        with rasterio.open(_signed_href(scene["assets"]["vh"]["href"], token)) as vh_src, \
             rasterio.open(_signed_href(scene["assets"]["vv"]["href"], token)) as vv_src:
            crs = vh_src.crs
            gf = shape(transform_geom("EPSG:4326", crs, mapping(g)))
            ring = gf.buffer(ring_km * 1000.0)
            win = from_bounds(*ring.bounds, transform=vh_src.transform).round_offsets().round_lengths()
            win = win.intersection(rasterio.windows.Window(0, 0, vh_src.width, vh_src.height))
            if win.width > max_px or win.height > max_px:
                return {"status": "N/D", "reason": "janela SAR excede o limite; reduzir ring_km"}
            vh = vh_src.read(1, window=win).astype(float); vv = vv_src.read(1, window=win).astype(float)
            tr = vh_src.window_transform(win)
    for a in (vh, vv):
        a[(a <= 0) | ~np.isfinite(a)] = np.nan
    vh_db, vv_db = 10 * np.log10(vh), 10 * np.log10(vv)
    shp = vh.shape
    field_mask = geometry_mask([mapping(gf)], out_shape=shp, transform=tr, invert=True)
    # MapBiomas class on the S1 grid
    url = mapbiomas_url or _local_mapbiomas() or RASTER_URL.format(year=YEAR)
    mb = np.zeros(shp, dtype="uint8")
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(url if url.startswith(("/", "file:")) or __import__("pathlib").Path(url).is_file() else "/vsicurl/" + url) as src:
                rb = rasterio.warp.transform_bounds(crs, src.crs, *ring.bounds)
                w = from_bounds(*rb, transform=src.transform).round_offsets().round_lengths()
                arr = src.read(1, window=w, boundless=True, fill_value=0)
                reproject(arr, mb, src_transform=src.window_transform(w), src_crs=src.crs,
                          dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
    except Exception as exc:
        # 03/11/2026: the official MapBiomas C11 GeoTIFF link returned HTTP 403
        # (anonymous access denied). Without a same-class reference map the
        # relative vigor is undefined → N/D, never a guessed reference.
        return {"status": "N/D", "scene_id": scene["id"],
                "reason": "mapa de referência MapBiomas indisponível (" + type(exc).__name__ + ": "
                          + str(exc)[:120] + "); vigor relativo não definível"}
    in_field = field_mask & np.isfinite(vh_db) & np.isfinite(vv_db)
    if in_field.sum() < 30:
        return {"status": "N/D", "reason": "talhão com menos de 30 pixels SAR válidos"}
    fvh = np.where(field_mask, vh_db, np.nan); fvv = np.where(field_mask, vv_db, np.nan)
    side = max(5, int(round(math.sqrt(in_field.sum()))))
    refs, used = [], 0
    for r in range(0, shp[0] - side + 1, side):
        for c in range(0, shp[1] - side + 1, side):
            sl = (slice(r, r + side), slice(c, c + side))
            if field_mask[sl].any():
                continue
            same = (mb[sl] == mapbiomas_class) & np.isfinite(vh_db[sl])
            if same.mean() < 0.8:
                continue
            try:
                refs.append(field_metrics(np.where(same, vh_db[sl], np.nan), np.where(same, vv_db[sl], np.nan)))
                used += 1
            except ValueError:
                continue
    if used < MIN_REFERENCE_BLOCKS:
        return {"status": "N/D", "reason": f"só {used} talhões de referência da mesma classe MapBiomas no raio de {ring_km} km"}
    out = classify_vigor(fvh, fvv, refs, n_boot=200)
    out.update({"scene_id": scene["id"], "acquisition_utc": scene["acquisition_utc"],
                "scene_age_days": round(age_days, 2), "search_window_days": window_days,
                "reference_blocks": used, "reference_definition":
                f"blocos de {side}×{side} px com ≥80% classe MapBiomas {mapbiomas_class} ({YEAR}) num raio de {ring_km} km, mesma cena",
                "source": "Sentinel-1 RTC (Microsoft Planetary Computer) + MapBiomas C11"})
    return out
