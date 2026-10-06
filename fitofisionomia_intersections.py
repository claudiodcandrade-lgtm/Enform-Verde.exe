"""IBGE phytophysiognomy intersections and class-wise raster summaries.

Geometry areas are measured in SIRGAS 2000 / Brazil Albers (EPSG:5880).
Raster statistics are calculated inside the AOI ∩ IBGE class geometry, never
from a whole-property zonal mask. The caller remains responsible for verifying
that the selected vector is the official IBGE vegetation layer/version.
"""
from __future__ import annotations

import math
from pathlib import Path

def _valid_geometry(geom):
    if geom is None or geom.is_empty:
        return None
    try:
        if not geom.is_valid:
            from shapely.validation import make_valid
            geom = make_valid(geom)
    except Exception:
        if not geom.is_valid:
            geom = geom.buffer(0)
    return None if geom.is_empty else geom

def ibge_class_intersections(aoi_gdf, ibge_gdf, class_field):
    """Intersect AOI with each mapped IBGE class; return class geometries and area audit."""
    import geopandas as gpd
    if aoi_gdf is None or ibge_gdf is None or len(aoi_gdf) == 0 or len(ibge_gdf) == 0:
        raise ValueError("AOI e camada IBGE precisam conter geometrias.")
    if not aoi_gdf.crs or not ibge_gdf.crs:
        raise ValueError("As duas camadas precisam declarar seu CRS.")
    if class_field not in ibge_gdf.columns:
        raise ValueError("Campo de classe IBGE inexistente: " + str(class_field))
    equal_area = "EPSG:5880"
    aoi = aoi_gdf.to_crs(equal_area)[["geometry"]].copy()
    aoi["geometry"] = aoi.geometry.map(_valid_geometry)
    aoi = aoi[aoi.geometry.notna() & ~aoi.geometry.is_empty]
    if aoi.empty:
        raise ValueError("AOI sem geometria válida após reprojeção.")
    aoi_geom = _valid_geometry(aoi.geometry.union_all())
    aoi_area = float(aoi_geom.area) / 10000.0
    mapped = ibge_gdf[[class_field, "geometry"]].copy()
    mapped = mapped.rename(columns={class_field: "physiognomy"})
    mapped["geometry"] = mapped.geometry.map(_valid_geometry)
    mapped = mapped[mapped.geometry.notna() & ~mapped.geometry.is_empty & mapped["physiognomy"].notna()]
    mapped = mapped.to_crs(equal_area)
    mapped = mapped[mapped.geometry.intersects(aoi_geom)]
    if mapped.empty:
        raise ValueError("A camada IBGE não intersecta a AOI.")
    clipped = gpd.overlay(gpd.GeoDataFrame(geometry=[aoi_geom], crs=equal_area),
                           mapped, how="intersection", keep_geom_type=False)
    clipped["geometry"] = clipped.geometry.map(_valid_geometry)
    clipped = clipped[clipped.geometry.notna() & ~clipped.geometry.is_empty]
    clipped["_area_ha"] = clipped.geometry.area / 10000.0
    classes = []
    for name, rows in clipped.groupby("physiognomy", dropna=True, sort=True):
        geom = _valid_geometry(rows.geometry.union_all())
        area = float(geom.area) / 10000.0
        if area <= 0:
            continue
        classes.append({"physiognomy": str(name), "area_ha": area,
                        "area_share_pct": 100.0 * area / aoi_area,
                        "geometry": geom})
    mapped_geom = _valid_geometry(clipped.geometry.union_all())
    covered = float(mapped_geom.area) / 10000.0 if mapped_geom is not None else 0.0
    return {"area_aoi_ha": aoi_area, "area_classified_ha": covered,
            "area_unclassified_ha": max(0.0, aoi_area-covered),
            "area_unclassified_pct": 100.0 * max(0.0,aoi_area-covered) / aoi_area if aoi_area else 0.0,
            "crs_area": equal_area, "classes": classes}

def zonal_raster_by_ibge_class(aoi_gdf, ibge_gdf, class_field, raster_path):
    """Return pixel statistics and area-weighted totals for each AOI×IBGE class."""
    import numpy as np
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    audit = ibge_class_intersections(aoi_gdf, ibge_gdf, class_field)
    out=[]
    with rasterio.open(raster_path) as src:
        for row in audit["classes"]:
            geom = transform_geom("EPSG:5880", src.crs, row["geometry"].__geo_interface__)
            try:
                arr, _ = mask(src, [geom], crop=True, filled=False)
                values=np.ma.array(arr[0]).compressed().astype(float)
                values=values[np.isfinite(values)]
                if src.nodata is not None:
                    values=values[values != src.nodata]
            except ValueError:
                values=np.array([],dtype=float)
            rec={k:v for k,v in row.items() if k!="geometry"}
            if not len(values):
                rec.update({"mean":None,"sd":None,"n":0,"min":None,"max":None})
            else:
                mean=float(values.mean())
                rec.update({"mean":mean,"sd":float(values.std(ddof=1)) if len(values)>1 else 0.0,
                            "n":int(len(values)),"min":float(values.min()),"max":float(values.max())})
            out.append(rec)
    return {"raster_path":str(Path(raster_path)),"class_field":class_field,
            "area_aoi_ha":audit["area_aoi_ha"],"area_classified_ha":audit["area_classified_ha"],
            "area_unclassified_ha":audit["area_unclassified_ha"],
            "area_unclassified_pct":audit["area_unclassified_pct"],
            "area_crs":audit["crs_area"],"classes":out}
