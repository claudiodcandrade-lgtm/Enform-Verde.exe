import unittest

from sar_height_absence import build_height_absence_certificate, regional_height_fallback_decision


def certificate():
    return {"status":"SAR_AUSENCIA_COBERTURA_CONFIRMADA",
        "global_search_complete":True,"pagination_complete":True,"pixel_read_complete":True,
        "routes":[{"configured":True,"coverage_absence_confirmed":True,
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


if __name__=="__main__":
    unittest.main()
