"""Anonymous Microsoft Planetary Computer Sentinel-1 RTC acquisition route.

Catalog discovery, temporary SAS signing and COG pixel reads are separate
states. Never persist/log SAS tokens. Pixel samples are not crop labels.
"""
from __future__ import annotations

import json
import os
import ssl
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

STAC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS_TOKEN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel1euwestrtc/sentinel1-grd-rtc"
ALLOWED_HOSTS = {"planetarycomputer.microsoft.com", "sentinel1euwestrtc.blob.core.windows.net"}


def _https_json(url, payload=None, *, opener=urlopen, timeout=45):
    if urlsplit(url).scheme != "https" or urlsplit(url).hostname not in ALLOWED_HOSTS:
        raise ValueError("Refusing untrusted MPC endpoint")
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=data, headers={"Accept": "application/geo+json, application/json",
                  **({"Content-Type": "application/json"} if data is not None else {})},
                  method="POST" if data is not None else "GET")
    try:
        with opener(req, timeout=timeout) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        # Do not surface query strings: signed assets may contain SAS secrets.
        raise RuntimeError(f"MPC HTTPS request failed ({type(exc).__name__})") from None


def search_sentinel1_rtc(aoi_geojson, *, start_utc, end_utc,
                         opener=urlopen, page_limit=50, max_pages=20):
    """Search the public S1 RTC STAC collection and follow pagination links."""
    if not isinstance(aoi_geojson, dict) or aoi_geojson.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("AOI must be a GeoJSON Polygon or MultiPolygon in EPSG:4326")
    start, end = _aware(start_utc), _aware(end_utc)
    if start >= end or end > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise ValueError("Invalid or future acquisition interval")
    if not 1 <= page_limit <= 100 or not 1 <= max_pages <= 100:
        raise ValueError("Pagination limit outside safe bounds")
    body = {"collections": ["sentinel-1-rtc"], "intersects": aoi_geojson,
            "datetime": start.isoformat().replace("+00:00", "Z") + "/" + end.isoformat().replace("+00:00", "Z"),
            "limit": page_limit}
    url, method, next_body = STAC_SEARCH, "POST", body
    scenes, seen = [], set()
    pages = 0
    while url and pages < max_pages:
        if urlsplit(url).scheme != "https" or urlsplit(url).hostname not in ALLOWED_HOSTS:
            raise ValueError("Untrusted pagination URL")
        payload = next_body if method == "POST" else None
        page = _https_json(url, payload, opener=opener)
        pages += 1
        for item in page.get("features", []):
            props = item.get("properties") or {}
            ident = item.get("id")
            acquired = props.get("datetime") or props.get("start_datetime")
            if not ident or ident in seen or not acquired:
                continue
            seen.add(ident)
            scenes.append({"id": ident, "acquisition_utc": acquired,
                "published_utc": props.get("published") or props.get("created"),
                "platform": props.get("platform"), "orbit_state": props.get("sat:orbit_state"),
                "relative_orbit": props.get("sat:relative_orbit"),
                "polarizations": props.get("sar:polarizations"),
                "incidence_angle": props.get("view:incidence_angle"),
                "collection": item.get("collection", "sentinel-1-rtc"),
                "assets": item.get("assets", {}), "source": STAC_SEARCH})
        link = next((link for link in page.get("links", []) if link.get("rel") == "next"), None)
        if not link:
            url = None
        else:
            url = link.get("href")
            method = str(link.get("method", "GET")).upper()
            next_body = link.get("body")
            if method not in {"GET", "POST"}:
                raise ValueError("Unsupported STAC pagination method")
    scenes.sort(key=lambda row: row["acquisition_utc"], reverse=True)
    return {"status": "discovery_only", "queried_at_utc": datetime.now(timezone.utc).isoformat(),
            "scene_count": len(scenes), "pages_read": pages,
            "pagination_complete": not bool(url), "scenes": scenes,
            "warning": "Catalog availability is not proof of pixel coverage, crop identity, or validated phenology."}


def _aware(value):
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("UTC timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def get_runtime_sas_token(*, opener=urlopen):
    """Request a fresh temporary SAS token; caller must keep it in memory only."""
    payload = _https_json(SAS_TOKEN_URL, opener=opener)
    token = payload.get("token") if isinstance(payload, dict) else None
    if not token:
        raise RuntimeError("MPC did not return a SAS token")
    return str(token).lstrip("?")


def _signed_href(href, token):
    parts = urlsplit(href)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise ValueError("Refusing asset outside the MPC Sentinel-1 RTC host")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in parse_qsl(token.lstrip("?"), keep_blank_values=True):
        query[key] = value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def extract_cog_point(asset_href, *, lon, lat, polarization, token=None, window_size=3,
                      ca_bundle=None):
    """Read a small georeferenced COG window and return raw native RTC values."""
    if polarization not in {"vv", "vh"} or not -180 <= float(lon) <= 180 or not -90 <= float(lat) <= 90:
        raise ValueError("Invalid point or polarization")
    if window_size < 1 or window_size > 101 or window_size % 2 != 1:
        raise ValueError("window_size must be an odd integer from 1 to 101")
    token = token if token is not None else get_runtime_sas_token()
    signed = _signed_href(asset_href, token)
    import numpy as np
    import rasterio
    from rasterio.windows import Window
    from rasterio.warp import transform
    if ca_bundle is None:
        ca_bundle = ssl.get_default_verify_paths().cafile
    if not ca_bundle:
        try:
            import certifi
            ca_bundle = certifi.where()
        except ImportError:
            ca_bundle = None
    # Keep TLS certificate checks on. Set GDAL's CA bundle only; never enable
    # GDAL_HTTP_UNSAFESSL or requests verify=False.
    env = {"GDAL_HTTP_UNSAFESSL": "NO"}
    if ca_bundle:
        env["GDAL_CURL_CA_BUNDLE"] = ca_bundle
        env["CURL_CA_BUNDLE"] = ca_bundle
    with rasterio.Env(**env):
        with rasterio.open(signed) as ds:
            x, y = transform("EPSG:4326", ds.crs, [float(lon)], [float(lat)])
            row, col = ds.index(x[0], y[0])
            half = window_size // 2
            win = Window(col-half, row-half, window_size, window_size)
            arr = ds.read(1, window=win, masked=True).astype("float64")
            valid = np.asarray(arr.compressed(), dtype="float64")
            valid = valid[np.isfinite(valid)]
            if not len(valid):
                raise ValueError("No valid RTC pixels at requested coordinate")
            return {"status": "pixels_read", "polarization": polarization.upper(),
                    "crs": ds.crs.to_string(), "raster_dtype": ds.dtypes[0],
                    "nodata": ds.nodata, "window_size": window_size,
                    "valid_pixels": int(len(valid)), "median_native": float(np.median(valid)),
                    "p25_native": float(np.quantile(valid, .25)),
                    "p75_native": float(np.quantile(valid, .75)),
                    "min_native": float(valid.min()), "max_native": float(valid.max()),
                    "unit": "RTC product native; confirm unit from collection documentation",
                    "acquisition_utc": None,
                    "warning": "Point window is not an agricultural field mask or crop-specific aggregate."}


def extract_cog_polygon(asset_href, *, polygon_geojson, polarization, token=None,
                        ca_bundle=None, max_pixels=5_000_000):
    """Extract native VV/VH zonal stats from a supplied verified field polygon.

    The polygon itself must come from a separately verified field reference.
    This routine measures SAR values only; it does not establish crop identity.
    """
    if polarization not in {"vv", "vh"}:
        raise ValueError("polarization must be vv or vh")
    if (not isinstance(polygon_geojson, dict) or
            polygon_geojson.get("type") not in {"Polygon", "MultiPolygon"}):
        raise ValueError("A verified Polygon or MultiPolygon GeoJSON is required")
    if not isinstance(max_pixels, int) or not 1 <= max_pixels <= 40_000_000:
        raise ValueError("max_pixels outside safe extraction limits")
    token = token if token is not None else get_runtime_sas_token()
    signed = _signed_href(asset_href, token)
    import numpy as np
    import rasterio
    from rasterio.features import bounds as geometry_bounds
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    if ca_bundle is None:
        ca_bundle = ssl.get_default_verify_paths().cafile
    if not ca_bundle:
        try:
            import certifi
            ca_bundle = certifi.where()
        except ImportError:
            ca_bundle = None
    env = {"GDAL_HTTP_UNSAFESSL": "NO"}
    if ca_bundle:
        env["GDAL_CURL_CA_BUNDLE"] = ca_bundle
        env["CURL_CA_BUNDLE"] = ca_bundle
    with rasterio.Env(**env):
        with rasterio.open(signed) as ds:
            if ds.crs is None:
                raise ValueError("COG is missing georeferenced CRS")
            geom = transform_geom("EPSG:4326", ds.crs, polygon_geojson)
            # Reject pathological AOIs before asking GDAL to read a huge COG window.
            bounds = geometry_bounds(geom)
            window = ds.window(*bounds).round_offsets().round_lengths()
            pixels = max(0, int(window.width)) * max(0, int(window.height))
            if pixels > max_pixels:
                raise ValueError("AOI COG window exceeds max_pixels; split into tiles first")
            data, out_transform = mask(ds, [geom], crop=True, filled=False, all_touched=False)
            band = data[0].astype("float64")
            valid = np.asarray(band.compressed(), dtype="float64")
            valid = valid[np.isfinite(valid)]
            inside = int(np.ma.count(band))
            if not len(valid):
                raise ValueError("No valid RTC pixels inside polygon")
            # Raster pixel area is reported in squared units of the projected CRS;
            # irregular/geographic CRS areas are intentionally not converted to ha.
            projected_area = (abs(float(out_transform.a * out_transform.e - out_transform.b * out_transform.d))
                              if ds.crs and ds.crs.is_projected else None)
            return {"status": "polygon_pixels_read", "polarization": polarization.upper(),
                    "crs": ds.crs.to_string(), "raster_dtype": ds.dtypes[0],
                    "nodata": ds.nodata, "valid_pixels": int(len(valid)),
                    "inside_pixels": inside, "valid_pixel_fraction": float(len(valid)/inside) if inside else None,
                    "pixel_area_crs_units_squared": projected_area,
                    "median_native": float(np.median(valid)),
                    "p25_native": float(np.quantile(valid, .25)),
                    "p75_native": float(np.quantile(valid, .75)),
                    "mean_native": float(np.mean(valid)), "std_native": float(np.std(valid)),
                    "min_native": float(valid.min()), "max_native": float(valid.max()),
                    "unit": "RTC product native; confirm unit from collection documentation",
                    "warning": "Crop identity and independent mask approval must be verified outside this extractor."}
