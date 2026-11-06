"""On-demand raw Embrapa/PronaSolos 90 m SOC stock rasters via OGC WCS 2.0.1.

Why: the 0–100 cm soil stock must come from the EXACT intersection of the
analysed polygon with the official map, not from a handful of identify points.
Embrapa GeoInfo's GeoServer publishes the five raw stock horizons as WCS
coverages (float32, EPSG:4326, 0.000833…° ≈ 92 m, nodata −9999, Mg C/ha).
Only the polygon's window is downloaded, so no multi-GB national file is needed.

Verified 2026-11-03: values returned by GetCoverage at (−55.0, −3.0) are
7.7 / 14.6 / 20.7 / 18.9 / 17.0 Mg C/ha, identical to the SGB MapServer
``estoque_carbono_90m`` identify response at the same coordinate.

Fail-closed rules: every horizon must be HTTP 200 + a GeoTIFF that opens with
rasterio, one band, EPSG:4326, the published pixel size, all five on the same
grid. Anything else is reported as an acquisition failure, never as zero
carbon. Each file is cached with its SHA-256 and the request URL.

Licence: "Mapa de estoque de carbono orgânico do solo do Brasil (90 m - Versão
2021)", Embrapa Solos, CC BY-NC 3.0 BR. Commercial use requires Embrapa
authorisation; this module records the licence but does not grant it.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

WCS_ENDPOINT = "https://geoinfo.dados.embrapa.br/geoserver/ows"
COVERAGES = {  # MapServer/identify layer id -> WCS coverage id
    2: "geonode__br_90m_carbon_stock_0_5cm_v2",
    3: "geonode__br_90m_carbon_stock_5_15cm_v2",
    4: "geonode__br_90m_carbon_stock_15_30cm_v2",
    5: "geonode__br_90m_carbon_stock_30_60cm_v2",
    6: "geonode__br_90m_carbon_stock_60_100cm_v2",
}
PIXEL_DEG = 1.0 / 1200.0          # 0.000833… degree, published grid
NODATA = -9999.0
SOURCE = {
    "publisher": "Embrapa Solos/PronaSolos",
    "title": "Mapa de estoque de carbono orgânico do solo do Brasil (90 m - Versão 2021)",
    "citation": ("VASQUES, G. M.; DART, R. O.; BACA, J. F. M.; CEDDIA, M. B.; "
                 "MENDONÇA SANTOS, M. L. Embrapa Solos, 2021."),
    "metadata_url": "http://geoinfo.cnps.embrapa.br/maps/3175",
    "license": "CC BY-NC 3.0 BR (uso não comercial; uso comercial exige autorização da Embrapa)",
    "unit": "Mg C/ha",
    "known_limitations": ("O mapa contém erros e pixels sem valor; solos rasos, afloramentos, "
                          "dunas, áreas urbanas e corpos d'água não foram excluídos (nota Embrapa)."),
}
MAX_TILE_PX = 2048


class WcsAcquisitionError(RuntimeError):
    """Raised when the official raster window cannot be obtained/validated."""


def _default_cache():
    return Path.home() / ".enform_verde" / "pronasolos_wcs_cache"


def _window_bounds(geom_4326, margin_px=2):
    """Bounding box snapped OUTWARD to the published 1/1200° grid."""
    minx, miny, maxx, maxy = geom_4326.bounds
    m = margin_px * PIXEL_DEG
    snap_lo = lambda v: math.floor(v / PIXEL_DEG) * PIXEL_DEG
    snap_hi = lambda v: math.ceil(v / PIXEL_DEG) * PIXEL_DEG
    return (snap_lo(minx - m), snap_lo(miny - m), snap_hi(maxx + m), snap_hi(maxy + m))


def _tiles(bounds, max_px=MAX_TILE_PX):
    minx, miny, maxx, maxy = bounds
    span = max_px * PIXEL_DEG
    nx = max(1, math.ceil((maxx - minx) / span - 1e-9))
    ny = max(1, math.ceil((maxy - miny) / span - 1e-9))
    for j in range(ny):
        for i in range(nx):
            yield (minx + i * span, miny + j * span,
                   min(maxx, minx + (i + 1) * span), min(maxy, miny + (j + 1) * span))


def coverage_url(coverage_id, bounds):
    minx, miny, maxx, maxy = bounds
    query = [("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"),
             ("coverageId", coverage_id),
             ("subset", f"Lat({miny:.10f},{maxy:.10f})"),
             ("subset", f"Long({minx:.10f},{maxx:.10f})"),
             ("format", "image/tiff")]
    return WCS_ENDPOINT + "?" + urlencode(query)


def validate_tile(path):
    """Open a downloaded tile and enforce the published raster contract."""
    import rasterio
    try:
        with rasterio.open(path) as src:
            if src.count != 1:
                raise WcsAcquisitionError("cobertura WCS com número de bandas inesperado")
            if src.crs is None or src.crs.to_epsg() != 4326:
                raise WcsAcquisitionError(f"CRS inesperado: {src.crs}")
            a, e = src.transform.a, src.transform.e
            if (abs(a - PIXEL_DEG) > 1e-9 or abs(-e - PIXEL_DEG) > 1e-9
                    or abs(src.transform.b) > 1e-12 or abs(src.transform.d) > 1e-12):
                raise WcsAcquisitionError("grade de pixel diferente da publicada (1/1200°)")
            if src.dtypes[0] not in ("float32", "float64"):
                raise WcsAcquisitionError("tipo de dado não é ponto flutuante (possível imagem renderizada)")
            return {"width": src.width, "height": src.height,
                    "transform": tuple(src.transform)[:6], "nodata": src.nodata}
    except WcsAcquisitionError:
        raise
    except Exception as exc:  # not a GeoTIFF (HTML error page, XML exception...)
        raise WcsAcquisitionError("resposta não é GeoTIFF válido: " + type(exc).__name__) from exc


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _download(url, dest, session, timeout, attempts=3):
    last = None
    for k in range(attempts):
        try:
            r = session.get(url, timeout=timeout)
            ctype = r.headers.get("Content-Type", "")
            if r.status_code != 200:
                raise WcsAcquisitionError(f"HTTP {r.status_code}")
            if "tiff" not in ctype.lower():
                raise WcsAcquisitionError("Content-Type inesperado: " + ctype[:60]
                                          + " | " + r.text[:160].replace("\n", " "))
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(r.content)
            tmp.replace(dest)
            return
        except Exception as exc:
            last = exc
            if k + 1 < attempts:
                time.sleep(1.5 * (2 ** k))
    raise WcsAcquisitionError(f"falha ao obter cobertura WCS após {attempts} tentativas: "
                              f"{type(last).__name__}: {str(last)[:200]}")


def fetch_horizons(geom_4326, cache_dir=None, session=None, timeout=(10, 120)):
    """Download (or reuse verified cache of) the five horizons for a polygon window.

    Returns {"paths": {layer_id: Path}, "provenance": {...}}. Raises
    WcsAcquisitionError on any failure; the caller must report N/D, never 0.
    """
    import requests
    import rasterio
    from rasterio.merge import merge

    if geom_4326 is None or geom_4326.is_empty:
        raise WcsAcquisitionError("geometria vazia")
    bounds = _window_bounds(geom_4326)
    key = hashlib.sha256(json.dumps([round(v, 10) for v in bounds]).encode()).hexdigest()[:16]
    root = Path(cache_dir or _default_cache()) / key
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paths = {int(k): root / v["file"] for k, v in manifest["layers"].items()}
            if (set(paths) == set(COVERAGES)
                    and all(p.is_file() and _sha256(p) == manifest["layers"][str(k)]["sha256"]
                            for k, p in paths.items())):
                manifest["cache_reused"] = True
                return {"paths": paths, "provenance": manifest}
        except Exception:
            pass  # corrupt/stale cache: re-acquire below
    session = session or requests.Session()
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    layers, grids = {}, set()
    for lid, cov in COVERAGES.items():
        tile_paths, urls = [], []
        for t, tb in enumerate(_tiles(bounds)):
            url = coverage_url(cov, tb)
            tp = root / f"{cov}_t{t}.tif"
            _download(url, tp, session, timeout)
            validate_tile(tp)
            tile_paths.append(tp)
            urls.append(url)
        out = root / f"{cov}.tif"
        if len(tile_paths) == 1:
            tile_paths[0].replace(out)
        else:
            srcs = [rasterio.open(p) for p in tile_paths]
            try:
                arr, transform = merge(srcs, nodata=NODATA)
                profile = srcs[0].profile
            finally:
                for s in srcs:
                    s.close()
            profile.update(height=arr.shape[1], width=arr.shape[2], transform=transform,
                           nodata=NODATA, compress="deflate")
            with rasterio.open(out, "w", **profile) as dst:
                dst.write(arr)
            for p in tile_paths:
                p.unlink(missing_ok=True)
        grid = validate_tile(out)
        grids.add((grid["width"], grid["height"], tuple(round(v, 12) for v in grid["transform"])))
        layers[str(lid)] = {"coverage_id": cov, "file": out.name, "sha256": _sha256(out),
                            "bytes": out.stat().st_size, "request_urls": urls}
    if len(grids) != 1:
        raise WcsAcquisitionError("os cinco horizontes não vieram na mesma grade; perfil não pareável")
    manifest = dict(SOURCE, endpoint=WCS_ENDPOINT, protocol="OGC WCS 2.0.1 GetCoverage",
                    retrieved_at_utc=retrieved, window_bounds_epsg4326=list(bounds),
                    pixel_size_deg=PIXEL_DEG, nodata=NODATA, layers=layers, cache_reused=False)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"paths": {int(k): root / v["file"] for k, v in layers.items()}, "provenance": manifest}
