import unittest
from executive_carbon_report import executive_carbon_lines, uncertainty_for_pool

class ExecutiveCarbonReportTests(unittest.TestCase):
    def test_tapajos_agb_sd_is_not_confidence_interval(self):
        row={"tc":123.64,"agb_uncertainty_mg_ha":126.7558823529}
        u=uncertainty_for_pool(row)
        self.assertAlmostEqual(u["absolute_tc_ha"],59.5752647,places=4)
        self.assertIn("NÃO é IC95%",u["kind"])
    def test_necromass_published_interval(self):
        u=uncertainty_for_pool({"tc":8.7,"range_tc_ha":[7.4,10]})
        self.assertAlmostEqual(u["absolute_tc_ha"],1.3)
        self.assertAlmostEqual(u["percent"],14.9425287356)
    def test_soil_spatial_variability_not_prediction_error(self):
        u=uncertainty_for_pool({"tc":46.06,"spatial_sd_tc_ha":2.0747289})
        self.assertIn("NÃO é erro",u["kind"])
    def test_unknown_error_is_not_zero(self):
        u=uncertainty_for_pool({"tc":22.42})
        self.assertIsNone(u["absolute_tc_ha"])
    def test_executive_panel_precedes_details(self):
        native={"area_aoi_ha":1290.69,"native_area_ha":1290.69,
                "known_total_tc":262202,"complete":False,
                "strata":[{"class_name":"Floresta Ombrófila Densa","area_ha":1290.69,
                           "components":[{"parametro":"Necromassa aérea","tc":8.7,
                                          "range_tc_ha":[7.4,10]}]}]}
        lines=executive_carbon_lines(native,lambda x:f"{x:.2f}" if x is not None else "N/D")
        self.assertIn("PAINEL EXECUTIVO",lines[0])
        self.assertTrue(any("1.30 tC/ha" in x for x in lines))
        self.assertTrue(any("IC95%" in x for x in lines))

if __name__=="__main__":
    unittest.main()
