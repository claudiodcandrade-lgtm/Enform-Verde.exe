import unittest
from unittest.mock import patch

import sar_pipeline as sar


class BiomassAnalysisRouteCacheTests(unittest.TestCase):
    def test_height_model_is_primary_when_supported_and_downloads_are_shared(self):
        items = [
            {"id": "fh-1", "_product_type": "FP_FH__L2B", "_stage": "OPERATIONAL"},
            {"id": "agb-1", "_product_type": "FP_AGB_L2B", "_stage": "OPERATIONAL"},
        ]
        model = {
            "status": "SAR_PROCESSADO",
            "agb_mg_ha": 341.5,
            "uncertainty_mg_ha": 26.65,
            "uncertainty_kind": "RMSE leave-spatial-block-out; erro FH não incluído",
            "data_origin": "SAR_P_HEIGHT_X_INVENTORY_STRUCTURE",
            "source": "ESA BIOMASS H100 × inventário local",
            "height_mean_m": 31.2,
            "height_sd_m": 2.0,
        }
        direct_agb = {"status": "SAR_PROCESSADO", "agb_mg_ha": 390.0,
            "uncertainty_mg_ha": 55.0, "stats": [], "n_valid_pixels": 20}
        route_cache = {}
        with patch.object(sar, "national_predictive_route_matrix", return_value={}), \
             patch.object(sar, "download_maap_height", return_value={
                 "available": True, "paths": ["fh_height.tif"]}) as height_download, \
             patch.object(sar, "_zonal", return_value={
                 "mean": 31.2, "sd": 2.0, "n": 10, "min": 26.0, "max": 35.0}), \
             patch.object(sar, "tapajos_h100_structure_agb", return_value=model), \
             patch.object(sar, "download_maap_agb", return_value={
                 "available": True, "paths": ["agb.tif"]}) as agb_download, \
             patch.object(sar, "process_real_sar", return_value=direct_agb):
            first = sar.automatic_pipeline(object(), "Amazônia", "Floresta", cache="/tmp/cache-test",
                biomass_catalog_items=items, pipeline_route_cache=route_cache)
            second = sar.automatic_pipeline(object(), "Amazônia", "Floresta", cache="/tmp/cache-test",
                biomass_catalog_items=items, pipeline_route_cache=route_cache)

        self.assertEqual(first["data_origin"], "SAR_P_HEIGHT_X_INVENTORY_STRUCTURE")
        self.assertEqual(first["agb_mg_ha"], 341.5)
        self.assertEqual(first["official_agb_product_comparison"]["agb_mg_ha"], 390.0)
        self.assertIn("H100 SAR", first["agb_selection_reason"])
        self.assertEqual(second["data_origin"], "SAR_P_HEIGHT_X_INVENTORY_STRUCTURE")
        height_download.assert_called_once()
        agb_download.assert_called_once()
        self.assertEqual(second["audit"]["biomass_height"]["analysis_download_cache"], "HIT")
        self.assertEqual(second["audit"]["biomass_l2b"]["download"]["analysis_download_cache"], "HIT")


if __name__ == "__main__":
    unittest.main()
