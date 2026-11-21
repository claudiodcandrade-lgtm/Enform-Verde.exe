"""A technical failure in priority FH must not suppress independent CCI attempt."""
import unittest
from unittest.mock import patch

import sar_pipeline as sp


class AutomaticPipelineCciPriorityTests(unittest.TestCase):
    def test_cci_second_route_is_attempted_but_fh_error_stays_visible(self):
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
             patch.object(sp,"_cci_history_for_analysis",return_value=no_scene) as cci_search, \
             patch.object(sp,"process_real_sar",side_effect=AssertionError(
                 "CCI cannot be promoted while the priority FH route is unresolved")):
            result=sp.automatic_pipeline(object(),"Amazônia","Floresta Ombrófila Densa",
                cache="/tmp/enform-cci-priority-test",biomass_catalog_items=[],
                biomass_search_audit=height_audit)
        cci=result["audit"]["cci"]
        self.assertEqual(cci["selection_status"],"CONSULTA_CONCLUIDA_SEM_PRODUTO_COMPATIVEL")
        self.assertFalse(cci["download_skipped"])
        cci_search.assert_called_once()
        self.assertTrue(cci["priority_selection_gate"]["eligible"])
        self.assertGreater(cci["priority_selection_gate"]["fh_technical_errors_preserved"],0)
        self.assertFalse(cci["inventory_use_contract"]["inventory_calibration_applied"])
        self.assertTrue(cci["inventory_use_contract"]["ifn_microdata_consulted"])
        self.assertIn("pares AGB parcela–pixel",cci["inventory_use_contract"]["reason"])
        self.assertEqual(result["status"],"ERRO_TECNICO_ROTA_PRIORITARIA")
        self.assertIn("Corrigir a rota técnica",result["message"])
        self.assertIsNone(result["agb_mg_ha"])
        fh_route=next(row for row in result["audit"]["height_absence_certificate"]["routes"]
                      if row["route"]=="ESA_BIOMASS_FH")
        self.assertGreater(fh_route["technical_error_count"],0)


if __name__=="__main__":
    unittest.main()
