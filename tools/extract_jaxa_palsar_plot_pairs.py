#!/usr/bin/env python3
"""Prepare *observed* JAXA PALSAR plot/pixel pairs; NEVER derive canopy height.

Requires locally obtained, integrity-pinned HH/HV/mask/date rasters (2007-2010
ALOS annual mosaic) and plot coordinates. Raw data are not distributed here.
No training, independent validation, SAR height, or AOI CI95 is inferred.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path

JAXA_SOURCE = "https://www.eorc.jaxa.jp/ALOS/en/dataset/fnf_e.htm"
JAXA_ACCESS = "https://www.eorc.jaxa.jp/ALOS/en/palsar_fnf/registration.htm"
ALOS_LAUNCH = date(2006, 1, 24)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _grid_signature(ds):
    return (ds.width, ds.height, str(ds.crs), tuple(ds.transform))


def extract(rasters, expected_sha256, plots, plots_sha256, year):
    """Return traceable, unvalidated backscatter/field pairs for real local files.

    The caller must independently verify that user-supplied files are genuine
    JAXA data and that the applicable license permits the intended use.
    """
    if type(year) is not int or year not in (2007, 2008, 2009, 2010):
        raise ValueError("Only ALOS PALSAR annual mosaics from 2007-2010 supported")
    if set(rasters) != {"hh", "hv", "mask", "date"} or set(expected_sha256) != set(rasters):
        raise ValueError("HH/HV/mask/date raster paths and checksums are mandatory")
    paths = {k: Path(v) for k, v in rasters.items()}
    paths["plots"] = Path(plots)
    hashes = {k: sha256_file(p) for k, p in paths.items()}
    expected = dict(expected_sha256, plots=plots_sha256)
    for k in paths:
        if not isinstance(expected[k], str) or hashes[k].lower() != expected[k].lower():
            raise ValueError(f"{k}: SHA256 mismatch; no unverified input may be sampled")

    import numpy as np
    import rasterio
    from rasterio.warp import transform as crs_transform
    from rasterio.windows import Window

    with Path(plots).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        mandatory = {"plot", "lon", "lat", "h100_field_m"}
        if not reader.fieldnames or not mandatory.issubset(reader.fieldnames):
            raise ValueError("plot CSV lacks ID, WGS84 coordinates or field H100")
        records = list(reader)
    if not records:
        raise ValueError("empty plot inventory")

    seen = set()
    results = []
    with ExitStack() as stack:
        datasets = {k: stack.enter_context(rasterio.open(path)) for k, path in rasters.items()}
        hh_ds = datasets["hh"]
        if hh_ds.crs is None or hh_ds.count != 1:
            raise ValueError("HH must have a CRS and exactly one band")
        grid = _grid_signature(hh_ds)
        for k, ds in datasets.items():
            if ds.crs is None or ds.count != 1 or _grid_signature(ds) != grid:
                raise ValueError(f"{k}: CRS, grid, or band count incompatible with HH")
        if not all(datasets[k].dtypes[0] in ("uint16", "int16") for k in ("hh", "hv")):
            raise ValueError("HH/HV must be original 16-bit DN, not pre-converted dB")
        for record in records:
            pid = str(record["plot"]).strip()
            if not pid or pid in seen:
                raise ValueError("plot IDs must be unique and nonempty")
            seen.add(pid)
            lon, lat, field_height = (float(record[k]) for k in ("lon", "lat", "h100_field_m"))
            if not all(map(math.isfinite, (lon, lat, field_height))) or not (
                    -180 <= lon <= 180 and -90 <= lat <= 90 and field_height > 0):
                raise ValueError(f"plot {pid}: invalid coordinates/field height")
            result = {"plot": pid, "lon": lon, "lat": lat,
                      "field_h100_m": field_height, "status": "no_valid_footprint_pixel"}
            x, y = crs_transform("EPSG:4326", hh_ds.crs, [lon], [lat])
            r, c = hh_ds.index(x[0], y[0])
            if not (0 <= r < hh_ds.height and 0 <= c < hh_ds.width):
                result["status"] = "outside_raster"
                results.append(result)
                continue
            r0, c0 = max(0, r - 3), max(0, c - 3)
            r1, c1 = min(hh_ds.height, r + 4), min(hh_ds.width, c + 4)
            window = Window(c0, r0, c1 - c0, r1 - r0)
            hh = datasets["hh"].read(1, window=window, masked=True)
            hv = datasets["hv"].read(1, window=window, masked=True)
            quality = datasets["mask"].read(1, window=window, masked=True)
            days = datasets["date"].read(1, window=window, masked=True)
            rr, cc = np.mgrid[r0:r1, c0:c1]
            xx, yy = rasterio.transform.xy(hh_ds.transform, rr.ravel(), cc.ravel(), offset="center")
            lons, lats = crs_transform(hh_ds.crs, "EPSG:4326", xx, yy)
            lons = np.asarray(lons).reshape(hh.shape)
            lats = np.asarray(lats).reshape(hh.shape)
            dx = (lons - lon) * 111320.0 * math.cos(math.radians(lat))
            dy = (lats - lat) * 111320.0
            inside = (np.abs(dx) <= 25) & (np.abs(dy) <= 25)
            valid = inside & ~np.ma.getmaskarray(hh) & ~np.ma.getmaskarray(hv)
            valid &= ~np.ma.getmaskarray(quality) & ~np.ma.getmaskarray(days)
            valid &= (quality.data == 255) & (hh.data > 0) & (hv.data > 0) & (days.data > 0)
            if not valid.any():
                results.append(result)
                continue
            obs_dates = [ALOS_LAUNCH + timedelta(days=int(n) - 1) for n in days.data[valid]]
            if any(d.year != year for d in obs_dates):
                result["status"] = "acquisition_year_mismatch"
                result["observed_date_range"] = [min(obs_dates).isoformat(), max(obs_dates).isoformat()]
                results.append(result)
                continue
            hh_dn = float(np.median(hh.data[valid]))
            hv_dn = float(np.median(hv.data[valid]))
            result.update(status="paired_unvalidated",
                          pixels_inside_plot=int(valid.sum()),
                          hh_gamma0_db=10.0 * math.log10(hh_dn ** 2) - 83.0,
                          hv_gamma0_db=10.0 * math.log10(hv_dn ** 2) - 83.0,
                          observed_date_range=[min(obs_dates).isoformat(), max(obs_dates).isoformat()],
                          spatial_block=f"{math.floor(lon / 0.04)}:{math.floor(lat / 0.04)}")
            results.append(result)

    return {
        "status": "OBSERVED_SAR_PLOT_PAIRS_UNVALIDATED",
        "source_declared": "JAXA global ALOS/PALSAR annual mosaic (user-supplied files)",
        "source_identity_independently_verified": False,
        "source_url": JAXA_SOURCE,
        "source_registration": JAXA_ACCESS,
        "declared_year": year,
        "input_sha256": hashes,
        "n_field_plots": len(records),
        "n_pairs": sum(row["status"] == "paired_unvalidated" for row in results),
        "pairs": results,
        "height_sar_m": None,
        "canopy_height_model_validated": False,
        "scientifically_validated": False,
        "aoi_ci95_validated": False,
        "acquisition_time_utc": None,
        "license_commercial_use_verified": False,
        "warning": "HH/HV are radar backscatter, NOT direct canopy height. Dates are mosaic day codes, not UTC timestamps. Independent spatial/temporal validation, provenance and licensing remain mandatory."
    }


def main():
    parser = argparse.ArgumentParser()
    for k in ("hh", "hv", "mask", "date"):
        parser.add_argument("--" + k, required=True)
        parser.add_argument("--" + k + "-sha256", required=True)
    parser.add_argument("--plots", required=True)
    parser.add_argument("--plots-sha256", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    result = extract({k: getattr(args, k) for k in ("hh", "hv", "mask", "date")},
                     {k: getattr(args, k + "_sha256") for k in ("hh", "hv", "mask", "date")},
                     args.plots, args.plots_sha256, args.year)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"n_pairs": result["n_pairs"], "scientifically_validated": False}))


if __name__ == "__main__":
    main()
