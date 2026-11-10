"""Synthetic routing regression: FH L2A pixels must reach the automatic pipeline.

The mocked FH raster values are test fixtures, not measured field data.
Live MAAP FH evidence remains a separate GitHub Actions job.
"""
import unittest
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

import sar_pipeline as sp


class AutomaticFHL2ATests(unittest.TestCase):
    def test_real_fh_l2a_route_preserves_product_and_zonal_height(self):
        aoi=gpd.GeoDataFrame(
            geometry=[box(-55.21,-11.89,-55.17,-11.85)],crs="EPSG:4326")
        item={"id":"BIOMASS_FP_FH__L2A_SYNTHETIC",
              "_product_type":"FP_FH__L2A",
              "_collection":"BiomassLevel2a",
              "_stage":"OPERATIONAL_L2A",
              "assets":{}}
        predicted={"status":"SAR_MODELED_EXPERIMENTAL",
                   "agb_mg_ha":120.0,
                   "uncertainty_mg_ha":None,
                   "data_origin":"SYNTHETIC_TEST_ONLY"}
        with patch.object(sp,"national_predictive_route_matrix",return_value={}), \\
             patch.object(sp,"biomass_l2b_search",return_value=[item]), \\
             patch.object(sp,"download_maap_height",
                          return_value={"available":True,"paths":["/test/FP_FH__L2A_height.tif"],
                                        "fh_items":1}) as downloader, \\
             patch.object(sp,"role",return_value="HEIGHT"), \\
             patch.object(sp,"_zonal",return_value={"mean":21.5,"sd":4.3,
                                                     "n":1200,"min":4.0,"max":36.0}), \\
             patch.object(sp,"tapajos_h100_structure_agb",return_value=predicted):
            result=sp.automatic_pipeline(
                aoi,"Amazônia","Floresta Estacional Sempre-Verde",cache="/tmp/enform-fh-test")
        self.assertTrue(downloader.called)
        self.assertEqual(result["sar_height"]["product"],"FP_FH__L2A")
        self.assertEqual(result["height_mean_m"],21.5)
        self.assertEqual(result["height_n_valid_pixels"],1200)
        self.assertEqual(result["height_route_status"],"ALTURA_SAR_PROCESSADA")
        self.assertFalse(result["sar_height"]["height_interpretation"]
                         ["agb_inference_permitted"])
        self.assertEqual(result["audit"]["biomass_height_catalog"]["fh_count"],1)
        self.assertIn("FP_FH__L2A",result["audit"]["biomass_l2b"]
                      ["products_discovered"])
        self.assertEqual(result["data_origin"],"SYNTHETIC_TEST_ONLY")


if __name__=="__main__":
    unittest.main()
