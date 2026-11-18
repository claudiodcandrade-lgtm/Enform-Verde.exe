import unittest

from sar_height_absence import (build_height_absence_certificate,
    regional_height_fallback_decision,secondary_cci_agb_decision)


def certificate():
    return {"status":"SAR_AUSENCIA_COBERTURA_CONFIRMADA",
        "global_search_complete":True,"pagination_complete":True,"pixel_read_complete":True,
        "routes":[{"route":"ESA_BIOMASS_FH","configured":True,"coverage_absence_confirmed":True,
            "catalog_search_complete":True,"pagination_complete":True,
            "pixel_read_complete":True,"valid_pixel_count":0,"technical_error_count":0},
            {"route":"GTDX_GEDI_TANDEM_X","configured":True,"coverage_absence_confirmed":True,
            "catalog_search_complete":True,"pagination_complete":True,
            "pixel_read_complete":True,"valid_pixel_count":0,"technical_error_count":0}]}


class SarHeightAbsenceTests(unittest.TestCase):
    def test_live_route_audits_build_absence_certificate_only_when_complete(self):
        esa={"queries":[{"product_type":product,"catalog_search_complete":True,
            "pagination_complete":True,"matching_product_count":0,"technical_error_count":0}
            for product in ("FP_FH__L2A","FP_FH__L2B") for _ in range(2)]}
        gtdx={"catalog_search_complete":True,"pagination_complete":True,
            "pixel_read_complete":True,"valid_pixel_count":0,"technical_error_count":0}
        cert=build_height_absence_certificate(esa,{},gtdx)
        self.assertTrue(regional_height_fallback_decision(cert)[0])
        esa["queries"][0]["pagination_complete"]=False
        cert=build_height_absence_certificate(esa,{},gtdx)
        self.assertFalse(regional_height_fallback_decision(cert)[0])

    def test_found_biomass_product_or_gtdx_error_blocks_absence_certificate(self):
        esa={"queries":[{"product_type":product,"catalog_search_complete":True,
            "pagination_complete":True,"matching_product_count":1 if index==0 else 0,"technical_error_count":0}
            for index,product in enumerate(("FP_FH__L2A","FP_FH__L2B","FP_FH__L2A","FP_FH__L2B"))]}
        gtdx={"catalog_search_complete":False,"pagination_complete":False,
            "pixel_read_complete":False,"valid_pixel_count":None,"technical_error_count":1}
        cert=build_height_absence_certificate(esa,{"pixel_read_complete":False,"technical_error_count":1},gtdx)
        self.assertFalse(regional_height_fallback_decision(cert)[0])

    def test_all_routes_confirmed_absent_allows_regional_chart_reference(self):
        allowed,reason=regional_height_fallback_decision(certificate())
        self.assertTrue(allowed)
        self.assertIn("AUSENCIA_SAR_CONFIRMADA",reason)

    def test_technical_error_blocks_regional_height_substitution(self):
        c=certificate();c["routes"][0]["technical_error_count"]=1
        allowed,reason=regional_height_fallback_decision(c)
        self.assertFalse(allowed)
        self.assertEqual(reason,"ERRO_TECNICO_SAR_BLOQUEIA_FALLBACK")

    def test_pixels_or_incomplete_pagination_block_substitution(self):
        c=certificate();c["routes"][0]["valid_pixel_count"]=8
        self.assertFalse(regional_height_fallback_decision(c)[0])
        c=certificate();c["pagination_complete"]=False
        self.assertFalse(regional_height_fallback_decision(c)[0])

    def test_asset_http_error_is_counted_and_never_claimed_as_absence(self):
        esa={"queries":[{"product_type":product,"catalog_search_complete":True,
            "pagination_complete":True,"matching_product_count":1 if index==0 else 0,
            "technical_error_count":0}
            for index,product in enumerate(("FP_FH__L2A","FP_FH__L2B","FP_FH__L2A","FP_FH__L2B"))]}
        cert=build_height_absence_certificate(esa,
            {"available":False,"errors":["HTTP 401 Unauthorized"]},
            {"catalog_search_complete":True,"pagination_complete":True,
             "pixel_read_complete":True,"valid_pixel_count":0,"technical_error_count":0})
        esa_route=next(r for r in cert["routes"] if r["route"]=="ESA_BIOMASS_FH")
        self.assertEqual(esa_route["technical_error_count"],1)
        self.assertFalse(esa_route["coverage_absence_confirmed"])
        self.assertFalse(regional_height_fallback_decision(cert)[0])

    def test_successful_height_pixels_are_a_completed_read_not_absence(self):
        esa={"queries":[{"product_type":product,"catalog_search_complete":True,
            "pagination_complete":True,"matching_product_count":1 if index==0 else 0,
            "technical_error_count":0}
            for index,product in enumerate(("FP_FH__L2A","FP_FH__L2B","FP_FH__L2A","FP_FH__L2B"))]}
        cert=build_height_absence_certificate(esa,
            {"pixel_read_complete":True,"valid_pixel_count":12,"technical_error_count":0},
            {"catalog_search_complete":True,"pagination_complete":True,
             "pixel_read_complete":True,"valid_pixel_count":0,"technical_error_count":0})
        esa_route=next(r for r in cert["routes"] if r["route"]=="ESA_BIOMASS_FH")
        self.assertTrue(esa_route["pixel_read_complete"])
        self.assertFalse(esa_route["coverage_absence_confirmed"])

    def test_cci_is_blocked_when_priority_fh_route_has_a_technical_error(self):
        c=certificate()
        c["routes"][0]["technical_error_count"]=1
        decision=secondary_cci_agb_decision(c)
        self.assertFalse(decision["eligible"])
        self.assertEqual(decision["evidence"],"PRIORITY_ROUTE_TECHNICAL_ERROR")

    def test_cci_is_allowed_only_after_confirmed_absence_or_valid_fh_without_applicable_model(self):
        self.assertTrue(secondary_cci_agb_decision(certificate())["eligible"])
        c=certificate()
        c["status"]="AUSENCIA_SAR_NAO_COMPROVADA"
        c["routes"][0].update({"coverage_absence_confirmed":False,"valid_pixel_count":12})
        self.assertTrue(secondary_cci_agb_decision(c,valid_height_pixels=True)["eligible"])
        self.assertFalse(secondary_cci_agb_decision(c)["eligible"])


if __name__=="__main__":
    unittest.main()
