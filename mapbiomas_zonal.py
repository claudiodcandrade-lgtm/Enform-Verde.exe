"""Area shares by MapBiomas Brazil annual land-cover class.

Reads only the pixels intersecting an AOI from the official public GeoTIFF via
GDAL's HTTP range support. Area is calculated geodesically by raster row; class
shares are normalized to the valid mapped area. These are cover/use classes,
not a replacement for detailed IBGE phytophysiognomic legend codes.
"""
from __future__ import annotations

from collections import defaultdict

COLLECTION = 11
YEAR = 2025
RESOLUTION_M = 30
RASTER_URL = (
    "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/"
    "collection11/lulc/coverage/brazil_coverage/"
    "brazil_coverage-col11_{year}.tif"
)
SOURCE_URL = "https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/"

# MapBiomas Brazil Collection 11, level 2 classes. IDs follow its published legend.
LEGEND = {
    3: ("Formação Florestal", "formação florestal"),
    4: ("Formação Savânica", "formação savânica"),
    5: ("Mangue", "mangue"),
    6: ("Floresta Alagável", "floresta alagável"),
    7: ("Savana Alagada (beta)", "savana alagada"),
    9: ("Silvicultura", "silvicultura"),
    11: ("Campo Alagado e Área Pantanosa", "área úmida/campo alagado"),
    12: ("Formação Campestre", "formação campestre"),
    15: ("Pastagem", "pastagem"),
    18: ("Agricultura", "agricultura"),
    19: ("Lavoura Temporária", "lavoura temporária"),
    20: ("Cana", "cana"),
    21: ("Mosaico de Usos", "mosaico de usos"),
    24: ("Infraestrutura Urbana", "área urbana/infraestrutura"),
    25: ("Outra Área não Vegetada", "área não vegetada"),
    29: ("Afloramento Rochoso", "afloramento rochoso"),
    30: ("Mineração", "mineração"),
    33: ("Rio, Lago e Oceano", "água"),
    39: ("Soja", "lavoura temporária"),
    40: ("Arroz", "lavoura temporária"),
    41: ("Outras Lavouras Temporárias", "lavoura temporária"),
    46: ("Café", "lavoura perene"),
    47: ("Citrus", "lavoura perene"),
    48: ("Outras Lavouras Perenes", "lavoura perene"),
    49: ("Restinga Arbórea", "restinga arbórea"),
    50: ("Restinga Herbácea", "restinga herbácea"),
    62: ("Algodão", "lavoura temporária"),
}


def summarize_class_grid(values, inside, row_pixel_areas_m2, nodata=None):
    """Summarize a 2D class array and matching AOI mask using row pixel areas."""
    import numpy as np

    arr = np.asarray(values)
    mask = np.asarray(inside, dtype=bool)
    if arr.ndim != 2 or arr.shape != mask.shape or len(row_pixel_areas_m2) != arr.shape[0]:
        raise ValueError("grade, máscara e áreas por linha incompatíveis")
    areas = defaultdict(float)
    valid_area = 0.0
    # Aggregate bounded row blocks with NumPy instead of calling unique once
    # per raster row. The block size caps temporary memory for large AOIs.
    block_rows = 64
    row_areas = np.asarray(row_pixel_areas_m2, dtype=float)
    for start in range(0, arr.shape[0], block_rows):
        stop = min(start + block_rows, arr.shape[0])
        block = arr[start:stop]
        selected = mask[start:stop].copy()
        if nodata is not None:
            selected &= block != nodata
        selected &= block > 0
        if not selected.any():
            continue
        codes, inverse = np.unique(block[selected], return_inverse=True)
        pixel_areas = np.broadcast_to(
            row_areas[start:stop, None], block.shape
        )[selected]
        summed_areas = np.bincount(inverse, weights=pixel_areas, minlength=len(codes))
        for code, area in zip(codes, summed_areas):
            area = float(area)
            areas[int(code)] += area
            valid_area += area
    rows = []
    for code in sorted(areas):
        name, crosswalk = LEGEND.get(code, (f"Classe MapBiomas {code}", "classe sem correspondência cadastrada"))
        area_ha = areas[code] / 10000.0
        rows.append({
            "class_code": code, "class_name": name, "crosswalk_group": crosswalk,
            "area_ha": area_ha,
            "area_pct": (100.0 * areas[code] / valid_area) if valid_area else None,
        })
    return {"classes": rows, "mapped_area_ha": valid_area / 10000.0}


def _mapbiomas_cache_path(year):
    """Stable per-user cache for the HTTPS fallback when GDAL lacks /vsicurl/."""
    import os
    from pathlib import Path
    root = os.environ.get("LOCALAPPDATA")
    if root:
        base = Path(root) / "EnformVerde" / "cache" / "mapbiomas"
    else:
        base = Path.home() / ".cache" / "enform-verde" / "mapbiomas"
    return base / f"brazil_coverage-col11_{int(year)}.tif"


def _download_mapbiomas_geotiff(url, destination, *, max_bytes=5_000_000_000):
    """Download and validate the official COG if the bundled GDAL has no curl VFS.

    This is deliberately a last resort: the national GeoTIFF may be large.
    A partial/HTML response is never cached or treated as valid coverage.
    """
    import os
    import urllib.request
    import rasterio
    from pathlib import Path

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "EnformVerde/3.26 MapBiomas official GeoTIFF"}
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            reported = response.headers.get("Content-Length")
            if "text/html" in content_type or "application/json" in content_type:
                raise ValueError("Resposta MapBiomas não é GeoTIFF: " + content_type)
            if reported and int(reported) > max_bytes:
                raise ValueError("GeoTIFF MapBiomas excede limite de cache de 5 GB")
            copied = 0
            with temporary.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > max_bytes:
                        raise ValueError("Download MapBiomas excedeu limite de cache de 5 GB")
                    stream.write(chunk)
        if copied == 0 or (reported and copied != int(reported)):
            raise ValueError("Download MapBiomas vazio ou truncado")
        with rasterio.open(temporary) as check:
            if not check.crs or check.count < 1 or check.width < 1 or check.height < 1:
                raise ValueError("GeoTIFF MapBiomas sem metadados válidos")
        os.replace(temporary, destination)
        return destination
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def mapbiomas_class_percentages(aoi, year=YEAR, raster_url=None, _source_url=None):
    """Return MapBiomas class area and percent for an AOI from public C11 GeoTIFF."""
    import rasterio
    import geopandas as gpd
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds, transform as window_transform
    from pyproj import Geod
    from shapely.geometry import mapping
    from carbon_compartments import aoi_to_wgs84

    url = str(raster_url or RASTER_URL.format(year=int(year)))
    published_url = _source_url or url
    frame = aoi_to_wgs84(aoi)
    geom = frame.geometry.union_all()
    if geom.is_empty:
        raise ValueError("AOI vazia")
    # Different Windows TLS proxies and GDAL builds handle multipart Range,
    # HEAD, and HTTP/2 differently. Try independent transports against the
    # same public GeoTIFF; never turn a transport failure into an empty mask.
    strategies = [
        {"GDAL_HTTP_MULTIRANGE":"YES"},
        {"GDAL_HTTP_MULTIRANGE":"SERIAL", "CPL_VSIL_CURL_USE_HEAD":"NO",
         "GDAL_HTTP_VERSION":"1.1", "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES":"NO"},
        {"GDAL_HTTP_MULTIRANGE":"YES", "GDAL_HTTP_MULTIPLEX":"NO",
         "CPL_VSIL_CURL_USE_HEAD":"NO", "GDAL_HTTP_VERSION":"1.1"},
    ]
    last_error = None
    for strategy_index, strategy in enumerate(strategies, start=1):
        stage = "open_cog"
        try:
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                VSI_CACHE="TRUE", GDAL_HTTP_TIMEOUT="45",
                GDAL_HTTP_MAX_RETRY="2", **strategy,
            ):
                raster_path = ("/vsicurl/" + url) if url.startswith(("http://", "https://")) else url
                with rasterio.open(raster_path) as src:
                    if src.crs is None:
                        raise ValueError("GeoTIFF MapBiomas sem CRS")
                    geom_src = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(src.crs).iloc[0]
                    bounds = gpd.GeoSeries([geom_src], crs=src.crs).total_bounds
                    window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
                    window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                    stage = "read_pixel_window"
                    values = src.read(1, window=window, boundless=False)
                    transform = window_transform(window, src.transform)
                    mask = geometry_mask([mapping(geom_src)], out_shape=values.shape, transform=transform, invert=True, all_touched=False)
                    stage = "summarize_pixels"
                    geod = Geod(ellps="WGS84")
                    from pyproj import Transformer
                    to_wgs84 = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
                    areas = []
                    for row in range(values.shape[0]):
                        corners = [transform * (0, row), transform * (values.shape[1], row),
                                   transform * (values.shape[1], row + 1), transform * (0, row + 1)]
                        lons, lats = to_wgs84.transform([p[0] for p in corners], [p[1] for p in corners])
                        area, _ = geod.polygon_area_perimeter(lons, lats)
                        areas.append(abs(area) / values.shape[1])
                    result = summarize_class_grid(values, mask, areas, nodata=src.nodata)
                    result.update({
                        "collection": COLLECTION, "year": int(year), "resolution_m": RESOLUTION_M,
                        "source_url": published_url, "legend_url": SOURCE_URL,
                        "method": "contagem de pixels MapBiomas dentro da AOI; área geodésica por linha; percentual relativo aos pixels válidos; resolução nominal 30 m; máscara por centro do pixel",
                        "status": "MAPBIOMAS — COBERTURA E USO, NÃO SUBSTITUI LEGENDA DETALHADA IBGE",
                    })
                    result["read_strategy"] = ["MULTIRANGE_DEFAULT", "SERIAL_RANGE_NO_HEAD_HTTP11",
                                               "MULTIRANGE_NO_MULTIPLEX_HTTP11"][strategy_index-1]
                    result["transport_attempts"] = strategy_index
                    return result
        except Exception as exc:
            try: detail = str(exc)
            except Exception: detail = "mensagem não decodificável"
            import re
            detail = re.sub(r"https?://[^\s'\"]+", "[URL_REMOVIDA]", detail)
            last_error = (stage, type(exc).__name__, detail.encode("utf-8","replace").decode("utf-8")[:240])
    stage, kind, detail = last_error or ("open_cog", "RuntimeError", "falha sem diagnóstico")
    # A retry options matrix cannot fix a GDAL build compiled without curl VFS.
    # Fall back to an atomic HTTPS download only for that specific open failure,
    # then rerun the same exact AOI pixel calculation against the validated file.
    unsupported_vsi = ("does not exist in the file system" in detail.lower()
                       or "not recognized as a supported dataset name" in detail.lower()
                       or "not recognized as a supported file format" in detail.lower())
    if url.startswith(("http://", "https://")) and stage == "open_cog" and unsupported_vsi:
        local = _mapbiomas_cache_path(year)
        try:
            cache_valid = False
            if local.is_file() and local.stat().st_size > 0:
                try:
                    with rasterio.open(local) as check:
                        cache_valid = bool(check.crs and check.count >= 1 and check.width > 0 and check.height > 0)
                except Exception:
                    cache_valid = False
            if not cache_valid:
                local.unlink(missing_ok=True)
                _download_mapbiomas_geotiff(url, local)
            return mapbiomas_class_percentages(aoi, year=year, raster_url=str(local), _source_url=url)
        except Exception as exc:
            try: fallback_detail = str(exc)
            except Exception: fallback_detail = "mensagem não decodificável"
            import re
            fallback_detail = re.sub(r"https?://[^\s'\"]+", "[URL_REMOVIDA]", fallback_detail)
            detail = (detail + "; HTTPS_LOCAL_FALLBACK_"
                      + type(exc).__name__ + ": "
                      + fallback_detail.encode("utf-8", "replace").decode("utf-8")[:180])
    raise RuntimeError(f"MAPBIOMAS_{stage}_{kind}: {detail}") from None
