import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from fitofisionomia_intersections import ibge_class_intersections, zonal_raster_by_ibge_class

def _layers():
    aoi = gpd.GeoDataFrame({"id":[1]}, geometry=[box(0,0,2,1)], crs="EPSG:4326")
    ibge = gpd.GeoDataFrame({"legenda":["Floresta","Savana"]},
        geometry=[box(0,0,1,1),box(1,0,2,1)], crs="EPSG:4326")
    return aoi, ibge

def test_intersection_separates_ibge_classes_and_audits_area():
    aoi, ibge = _layers()
    result=ibge_class_intersections(aoi,ibge,"legenda")
    assert {x["physiognomy"] for x in result["classes"]} == {"Floresta","Savana"}
    assert abs(sum(x["area_share_pct"] for x in result["classes"])-100.0) < 1e-5
    assert result["area_unclassified_pct"] < 1e-5

def test_zonal_stats_are_computed_inside_each_ibge_intersection(tmp_path):
    aoi, ibge = _layers()
    raster=tmp_path/"agb.tif"
    with rasterio.open(raster,"w",driver="GTiff",height=1,width=2,count=1,
                       dtype="float32",crs="EPSG:4326",
                       transform=from_origin(0,1,1,1),nodata=-9999) as dst:
        dst.write(np.array([[10,20]],dtype="float32"),1)
    result=zonal_raster_by_ibge_class(aoi,ibge,"legenda",raster)
    got={x["physiognomy"]:x for x in result["classes"]}
    assert got["Floresta"]["mean"] == 10.0
    assert got["Savana"]["mean"] == 20.0
    assert got["Floresta"]["raster_total"] > 0
    assert got["Savana"]["n"] == 1
