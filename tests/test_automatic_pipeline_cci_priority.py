"""A technical failure in priority FH must not promote CCI to selected AGB."""
import unittest
from unittest.mock import patch

import sar_pipeline as sp


class AutomaticPipelineCciPriorityTests(unittest.TestCase):
    def test_cci_pixels_are_not_selected_when_biomass_fh_search_failed(self):
        queries=[{"product_type":product,"catalog_search_complete":True,
                  "pagination_complete":True,"matching_product_count":0,
                  "technical_error_count":0}
                 for product in ("FP_FH__L2A","FP_FH__L2B") for _ in range(2)]
        queries[0]["catalog_search_complete"]=False
        queries[0]["technical_error_count"]=1
        height_audit={"queries":queries,"errors":[],"height_queries_complete":False}
        no_scene={"items":0,"scene_ids":[],"pixel_state":"SEM_PIXELS_COMPATIVEIS",
                  "stats":[],"errors":[],"catalog_search_complete":True,
                  "pagination_complete":True,"technical_error_count":0}
        gtdx_empty={"available":False,"catalog_search_complete":True,
                    "pagination_complete":True,"pixel_read_complete":True,
                    "valid_pixel_count":0,"technical_error_count":0}
        with patch.object(sp,"national_predictive_route_matrix",return_value={}), \
             patch.object(sp,"download_gtdx_height",return_value=gtdx_empty), \
             patch.object(sp,"planetary_alos_palsar",return_value=no_scene), \
             patch.object(sp,"discover_asf",return_value=[]), \
             patch.object(sp,"_earthaccess_requests_session",return_value=(None,{"reason":"no credentials"})), \
             patch.object(sp,"planetary_sentinel1_cog",return_value=no_scene), \
             patch.object(sp,"inpe_sentinel1_rtc",return_value={**no_scene,"provider":"INPE"}), \
             patch.object(sp,"public_sentinel1_cog",return_value=no_scene), \
             patch.object(sp,"_cci_history_for_analysis",return_value={
                 "items":1,"paths":["cci_agb.tif"],"version":"7.0","year":2024,
                 "catalog_search_complete":True,"pagination_complete":True,
                 "technical_error_count":0}), \
             patch.object(sp,"process_real_sar",side_effect=AssertionError(
                 "CCI cannot be promoted while the priority FH route is unresolved")):
            result=sp.automatic_pipeline(object(),"Amazônia","Floresta Ombrófila Densa",
                cache="/tmp/enform-cci-priority-test",biomass_catalog_items=[],
                biomass_search_audit=height_audit)
        cci=result["audit"]["cci"]
        self.assertEqual(cci["selection_status"],
            "ADIADA_ERRO_OU_AUSENCIA_NAO_COMPROVADA_NA_ROTA_PRIORITARIA")
        self.assertFalse(cci["priority_selection_gate"]["eligible"])
        self.assertEqual(result["status"],"ERRO_TECNICO_ROTA_PRIORITARIA")
        self.assertIn("Corrigir a rota técnica",result["message"])
        self.assertIsNone(result["agb_mg_ha"])
        self.assertTrue(any("Corrigir/repetir a rota prioritária" in warning
                            for warning in result["audit"]["warnings"]))


if __name__=="__main__":
    unittest.main()
