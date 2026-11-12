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


def mapbiomas_class_percentages(aoi, year=YEAR, raster_url=None):
    """Return MapBiomas class area and percent for an AOI from public C11 GeoTIFF."""
    import rasterio
    import geopandas as gpd
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds, transform as window_transform
    from pyproj import Geod
    from shapely.geometry import mapping
    from carbon_compartments import aoi_to_wgs84

    url = raster_url or RASTER_URL.format(year=int(year))
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
                with rasterio.open("/vsicurl/" + url) as src:
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
                        "source_url": url, "legend_url": SOURCE_URL,
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
    raise RuntimeError(f"MAPBIOMAS_{stage}_{kind}: {detail}") from None
