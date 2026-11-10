"""Exact SAR native mask × IBGE phytoregion intersection; experimental provenance.

Synthetic geometries only. Does not prove real current land cover accuracy.
"""
import unittest
import geopandas as gpd
from shapely.geometry import box

from land_use_sar import name_native_from_ibge
from native_carbon import native_class


class SARIBGEIntersectionTests(unittest.TestCase):
    def test_intersection_only_names_sar_native_area(self):
        sar=gpd.GeoDataFrame(
            {"class_name":["Formação florestal","Lavoura de soja"],
             "source":["SAR_EXPERIMENTAL_MODELO","SAR_EXPERIMENTAL_MODELO"],
             "taxonomy":["SAR 2025/26 experimental"]*2},
            geometry=[box(0,0,1000,500),box(0,500,1000,1000)],crs="EPSG:6933")
        ibge=gpd.GeoDataFrame(
            {"class_name":["Floresta Estacional Sempre-Verde","Savana"]},
            geometry=[box(0,0,500,1000),box(500,0,1000,1000)],crs="EPSG:6933")
        out=name_native_from_ibge(sar,ibge,max_proximity_m=0)
        label=out[(out.class_name=="Floresta Estacional Sempre-Verde")]
        self.assertEqual(len(label),1)
        self.assertAlmostEqual(label.geometry.area.sum()/10000,25)
        self.assertEqual(label.source.iloc[0],"SAR_EXPERIMENTAL_MODELO+IBGE")
        self.assertTrue(native_class(label.class_name.iloc[0],label.source.iloc[0]))
        self.assertFalse(any("Savana"==x for x in out.class_name))
        self.assertAlmostEqual(out.geometry.area.sum()/10000,100)
        crops=out[out.class_name=="Lavoura de soja"]
        self.assertEqual(len(crops),1)
        self.assertFalse(native_class("Lavoura de soja",crops.source.iloc[0]))

    def test_ibge_cannot_create_native_without_sar_mask(self):
        sar=gpd.GeoDataFrame({"class_name":["Lavoura de soja"],
             "source":["SAR_EXPERIMENTAL_MODELO"],"taxonomy":["experimental"]},
             geometry=[box(0,0,1000,1000)],crs="EPSG:6933")
        ibge=gpd.GeoDataFrame({"class_name":["Floresta Estacional Sempre-Verde"]},
             geometry=[box(0,0,1000,1000)],crs="EPSG:6933")
        result=name_native_from_ibge(sar,ibge,max_proximity_m=0)
        self.assertEqual(result.class_name.iloc[0],"Lavoura de soja")
        self.assertIsNone(native_class("Floresta Estacional Sempre-Verde","IBGE"))

    def test_without_intersection_no_proximity_fabrication(self):
        sar=gpd.GeoDataFrame(
            {"class_name":["Formação florestal"],"source":["SAR_EXPERIMENTAL_MODELO"],
             "taxonomy":["experimental"]},geometry=[box(0,0,100,100)],
             crs="EPSG:6933")
        ibge=gpd.GeoDataFrame({"class_name":["Floresta Estacional Sempre-Verde"]},
             geometry=[box(200,0,300,100)],crs="EPSG:6933")
        out=name_native_from_ibge(sar,ibge,max_proximity_m=0)
        self.assertEqual(out.class_name.iloc[0],"Formação florestal")
        self.assertFalse("IBGE" in out.source.iloc[0])


if __name__=="__main__":
    unittest.main()
