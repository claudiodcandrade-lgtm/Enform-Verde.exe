#!/usr/bin/env python3
"""Spatially blocked diagnostic: 2010 ALOS PALSAR HH/HV vs ORNL Tapajos H100.

This is a research diagnostic, not a deployable canopy-height model. It uses
one field observation per 50x50 m plot and compares SAR+stand-class with a
stand-class-only baseline under spatial holdouts. No pixel is treated as an
independent plot and no operational height/AGB raster is emitted.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "tapajos_ornl1552_structure_v1.csv"
OUT = ROOT / "tapajos_2010_h100_diagnostic.json"
BUCKET = "https://deafrica-input-datasets.s3.af-south-1.amazonaws.com"
PREFIX = "alos_palsar_mosaic/2010/S05W055/"


def list_objects(prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix}
        if token:
            params["continuation-token"] = token
        url = BUCKET + "/?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Enform-Verde-height-diagnostic/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()
        root = ET.fromstring(body)
        keys.extend((node.text or "") for node in root.findall(".//{*}Contents/{*}Key"))
        truncated = root.findtext(".//{*}IsTruncated", "false").lower() == "true"
        token = root.findtext(".//{*}NextContinuationToken")
        if not truncated or not token:
            break
    return keys


def pick_rasters(keys: list[str]) -> list[str]:
    return [k for k in keys if k.lower().endswith((".tif", ".tiff"))]


def local_block(lon: float, lat: float, step_deg: float = 0.04) -> str:
    return f"{math.floor(lon / step_deg)}:{math.floor(lat / step_deg)}"


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    e = p - y
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(len(y)),
        "rmse_m": float(np.sqrt(np.mean(e ** 2))),
        "mae_m": float(np.mean(np.abs(e))),
        "bias_m": float(np.mean(e)),
        "r2": float(1.0 - np.sum(e ** 2) / ss_tot) if ss_tot > 0 else None,
        "residual_95_interval_m": [float(v) for v in np.quantile(e, [0.025, 0.975])],
    }


def design(classes: list[str], hh: np.ndarray, hv: np.ndarray) -> np.ndarray:
    # Stand type is an inventory stratum covariate, not a SAR observation.
    names = ["PF", "SLF", "SF"]
    cls = np.column_stack([[1.0 if x == n else 0.0 for x in classes] for n in names])
    return np.column_stack([hh, hv, hv - hh, cls])


def spatial_cv(y: np.ndarray, x: np.ndarray, groups: np.ndarray, alpha: float = 1.0) -> tuple[np.ndarray, int]:
    pred = np.full(len(y), np.nan)
    folds = 0
    for group in np.unique(groups):
        test = groups == group
        train = ~test
        if train.sum() < 5 or test.sum() == 0:
            continue
        folds += 1
        mu = x[train].mean(axis=0)
        sd = x[train].std(axis=0)
        sd[sd < 1e-9] = 1.0
        xt = (x[train] - mu) / sd
        xv = (x[test] - mu) / sd
        # Ridge with unpenalized intercept; fixed small alpha avoids unstable
        # many-coefficient fits on this 30-plot exploratory sample.
        xc = np.column_stack([np.ones(len(xt)), xt])
        vc = np.column_stack([np.ones(len(xv)), xv])
        penalty = np.eye(xc.shape[1]) * alpha
        penalty[0, 0] = 0.0
        beta = np.linalg.solve(xc.T @ xc + penalty, xc.T @ y[train])
        pred[test] = vc @ beta
    return pred, folds


def main() -> int:
    if not CSV.exists():
        raise FileNotFoundError(CSV)
    import csv
    rows = list(csv.DictReader(CSV.open(encoding="utf-8", newline="")))
    if len(rows) != 30:
        raise ValueError(f"Expected 30 ORNL plots; found {len(rows)}")

    keys = list_objects(PREFIX)
    raster_keys = pick_rasters(keys)
    print(f"PUBLIC_S3_PREFIX={PREFIX}")
    print(f"OBJECTS={len(keys)} GEOTIFFS={len(raster_keys)}")
    for key in raster_keys:
        print("RASTER_KEY=" + key)
    if not raster_keys:
        raise RuntimeError("No GeoTIFFs listed under the official 2010 L-band tile prefix.")

    # Remote COG reads use HTTP range requests. Disable GDAL directory scans so
    # opening one tile does not enumerate sibling files.
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.tiff,.ovr,.xml")
    os.environ.setdefault("GDAL_HTTP_VERSION", "2")
    import rasterio
    from rasterio.windows import Window

    hh_values, hv_values, h100, classes, groups = [], [], [], [], []
    sample_log = []
    errors = []
    for key in raster_keys:
        url = BUCKET + "/" + urllib.parse.quote(key, safe="/")
        try:
            with rasterio.open(url) as ds:
                descriptions = [str(x or "").strip().lower() for x in ds.descriptions]
                if all(x in descriptions for x in ("hh", "hv")):
                    hh_band = descriptions.index("hh") + 1
                    hv_band = descriptions.index("hv") + 1
                elif ds.count >= 5:
                    # Digital Earth Africa product spec order: HH, HV, date,
                    # local incidence angle, processing mask.
                    hh_band, hv_band = 1, 2
                elif ds.count >= 2:
                    hh_band, hv_band = 1, 2
                else:
                    errors.append({"key": key, "error": f"Expected HH/HV bands, got {ds.count}"})
                    continue
                mask_band = descriptions.index("mask") + 1 if "mask" in descriptions else (5 if ds.count >= 5 else None)
                print(f"OPENED={key} CRS={ds.crs} SIZE={ds.width}x{ds.height} BANDS={ds.count} DESC={descriptions}")
                for row in rows:
                    lon, lat = float(row["lon"]), float(row["lat"])
                    r, c = ds.index(lon, lat)
                    r0, c0 = max(0, r - 2), max(0, c - 2)
                    r1, c1 = min(ds.height, r + 3), min(ds.width, c + 3)
                    if r1 <= r0 or c1 <= c0:
                        continue
                    win = Window(c0, r0, c1 - c0, r1 - r0)
                    hh = ds.read(hh_band, window=win).astype(float)
                    hv = ds.read(hv_band, window=win).astype(float)
                    if ds.transform:
                        rr, cc = np.mgrid[r0:r1, c0:c1]
                        xs, ys = rasterio.transform.xy(ds.transform, rr, cc, offset="center")
                        xs, ys = np.asarray(xs), np.asarray(ys)
                        # 50x50m square plot footprint centered on surveyed plot.
                        dx = (xs - lon) * 111320.0 * math.cos(math.radians(lat))
                        dy = (ys - lat) * 111320.0
                        inside = (np.abs(dx) <= 25.0) & (np.abs(dy) <= 25.0)
                    else:
                        inside = np.ones(hh.shape, dtype=bool)
                    valid = inside & np.isfinite(hh) & np.isfinite(hv) & (hh > 0) & (hv > 0)
                    if mask_band:
                        m = ds.read(mask_band, window=win)
                        valid &= (m == 255)
                    if not valid.any():
                        # Keep closest valid sample only if the plot box misses
                        # pixel centers due to raster grid/centroid rounding.
                        valid = np.isfinite(hh) & np.isfinite(hv) & (hh > 0) & (hv > 0)
                        if mask_band:
                            valid &= ds.read(mask_band, window=win) == 255
                    if not valid.any():
                        sample_log.append({"plot": int(float(row["plot"])), "status": "no_valid_land_pixel"})
                        continue
                    hh_dn = float(np.median(hh[valid]))
                    hv_dn = float(np.median(hv[valid]))
                    hh_db = 10.0 * math.log10(hh_dn * hh_dn) - 83.0
                    hv_db = 10.0 * math.log10(hv_dn * hv_dn) - 83.0
                    hh_values.append(hh_db)
                    hv_values.append(hv_db)
                    h100.append(float(row["h100_field_m"]))
                    classes.append(row["type"])
                    groups.append(local_block(lon, lat))
                    sample_log.append({"plot": int(float(row["plot"])), "pixels_used": int(valid.sum()),
                                       "hh_db": hh_db, "hv_db": hv_db, "status": "sampled"})
                break
        except Exception as exc:
            errors.append({"key": key, "error": str(exc)[:800]})
            print(f"OPEN_ERROR={key}: {exc}")
    if not h100:
        result = {
            "status": "BLOCKED_DATA_READ", "deployable": False,
            "reason": "Could not read public 2010 HH/HV pixels for the plot centroids.",
            "prefix": PREFIX, "raster_keys": raster_keys, "errors": errors,
            "sampled_plots": sample_log,
        }
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 2

    y = np.asarray(h100, dtype=float)
    classes_a = list(classes)
    hh, hv = np.asarray(hh_values), np.asarray(hv_values)
    grp = np.asarray(groups)
    # SAR+class model is assessed against a class-only baseline in identical
    # spatial holdouts. Field H100 is never substituted into output pixels.
    sar_x = design(classes_a, hh, hv)
    base_x = design(classes_a, np.zeros(len(y)), np.zeros(len(y)))[:, 3:]
    pred_sar, folds = spatial_cv(y, sar_x, grp)
    pred_base, folds_base = spatial_cv(y, base_x, grp)
    keep = np.isfinite(pred_sar) & np.isfinite(pred_base)
    if keep.sum() < 10 or folds < 3:
        status = "INSUFFICIENT_SPATIAL_HOLDS"
    else:
        sar_m = metrics(y[keep], pred_sar[keep])
        base_m = metrics(y[keep], pred_base[keep])
        improves = sar_m["rmse_m"] < base_m["rmse_m"]
        status = "SAR_SIGNAL_BEATS_CLASS_BASELINE_EXPLORATORY" if improves else "NO_DEFENSIBLE_SAR_HEIGHT_SIGNAL"
    pf = np.asarray([c == "PF" for c in classes_a], dtype=bool)
    pf_correlations = None
    if int(pf.sum()) >= 3:
        pf_correlations = {
            "n_pf": int(pf.sum()),
            "h100_range_m": [float(y[pf].min()), float(y[pf].max())],
            "hh_h100_pearson_r": float(np.corrcoef(hh[pf], y[pf])[0, 1]),
            "hv_h100_pearson_r": float(np.corrcoef(hv[pf], y[pf])[0, 1]),
            "warning": "descriptive only; PF subset has few spatial blocks and is not independent validation",
        }
    result = {
        "status": status,
        "high_biomass_PF_descriptive": pf_correlations,
        "deployable": False,
        "product": "Digital Earth Africa/JAXA 2010 annual ALOS PALSAR HH/HV mosaic",
        "product_kind": "L-band dual-polarization gamma0 backscatter; not a direct height product",
        "public_prefix": PREFIX,
        "n_field_plots": 30,
        "n_sar_plot_pairs": int(len(y)),
        "n_spatial_blocks": int(len(np.unique(grp))),
        "n_spatial_holdouts": int(folds),
        "field_target": "ORNL 1552 H100 (field H100, September 2010); used only as calibration/validation label",
        "sampling": "median valid HH/HV over pixel centers inside 50x50m plot footprint; one response per plot",
        "sar_plus_class_oof": metrics(y[keep], pred_sar[keep]) if keep.sum() else None,
        "class_only_oof": metrics(y[keep], pred_base[keep]) if keep.sum() else None,
        "plot_samples": sample_log,
        "errors": errors,
        "decision": "Exploratory local evidence only. Do not create an H_SAR raster or AGB from this diagnostic. Deployment still requires independent sites and domain validation.",
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
