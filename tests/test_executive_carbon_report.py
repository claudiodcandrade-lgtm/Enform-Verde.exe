import unittest
from executive_carbon_report import (executive_carbon_lines, uncertainty_for_pool,
                                     litter_dashboard_summaries)

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
    def test_litter_dry_mass_without_documented_carbon_fraction(self):
        u=uncertainty_for_pool({"tc":2.33,"range_dry_mg_ha":[3.08,6.81]})
        self.assertIsNone(u["absolute_tc_ha"])
        self.assertIn("não documentada",u["kind"])
    def test_litter_dry_mass_with_documented_fraction(self):
        u=uncertainty_for_pool({"tc":2.33,"range_dry_mg_ha":[3.08,6.81],"carbon_fraction":0.47})
        self.assertAlmostEqual(u["absolute_tc_ha"],(6.81-3.08)*0.47/2)

    def test_soil_spatial_variability_not_prediction_error(self):
        u=uncertainty_for_pool({"tc":46.06,"spatial_sd_tc_ha":2.0747289})
        self.assertIn("NÃO é erro",u["kind"])
    def test_unknown_error_is_not_zero(self):
        u=uncertainty_for_pool({"tc":22.42})
        self.assertIsNone(u["absolute_tc_ha"])

    def test_root_input_sensitivity_is_visible_but_not_promoted_to_full_uncertainty(self):
        u=uncertainty_for_pool({"tc":22.48,"sensitivity_tc_ha":9.5,
            "sensitivity_kind":"sensibilidade parcial à AGB"})
        self.assertEqual(u["scope"],"sensitivity")
        native={"area_aoi_ha":10,"native_area_ha":10,"known_total_tc":224.8,"complete":False,
            "strata":[{"class_name":"Formação florestal","area_ha":10,"components":[
                {"parametro":"Biomassa subterrânea","tc":22.48,"total_tc":224.8,
                 "quantified_area_ha":10,"sensitivity_tc_ha":9.5,
                 "sensitivity_kind":"sensibilidade parcial à AGB; erro alométrico e transferência N/D"}]}]}
        lines="\n".join(executive_carbon_lines(native,lambda x:f"{x:.2f}" if x is not None else "N/D"))
        self.assertIn("sensibilidade parcial da entrada",lines)
        self.assertIn("incerteza total não mensurável",lines)
        self.assertIn("incerteza não mensurável",lines)
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

    def test_measurable_uncertainty_reports_all_three_units(self):
        native={"area_aoi_ha":10,"native_area_ha":10,"known_total_tc":1000,"complete":False,
            "strata":[{"class_name":"FOD","physiognomy":"FOD","area_ha":10,"components":[
                {"parametro":"Biomassa aérea","tc":100,"total_tc":1000,
                 "area_ha":10,"quantified_area_ha":10,"agb_uncertainty_mg_ha":10}]}]}
        lines=executive_carbon_lines(native,lambda x:f"{x:.2f}" if x is not None else "N/D")
        text="\n".join(lines)
        self.assertIn("incerteza mensurável: ±4.70 tC/ha | ±17.23 tCO₂e/ha | 4.70%",text)
        self.assertIn("NÃO é IC95%",text)

    def test_combined_total_uncertainty_also_uses_three_units(self):
        native={"area_aoi_ha":10,"native_area_ha":10,"known_total_tc":1000,"complete":True,
                "total_uncertainty":{"se_tC":10},"strata":[]}
        lines=executive_carbon_lines(native,lambda x:f"{x:.2f}" if x is not None else "N/D")
        self.assertTrue(any("incerteza combinada: ±1.00 tC/ha | ±3.67 tCO₂e/ha | 1.00%" in line
                            for line in lines))

    def test_experimental_litter_is_reported_separately_from_known_pool_total(self):
        native={"components":[{"parametro":"Serapilheira","known_total_tc":None}],
            "strata":[{"class_name":"FESV","physiognomy":"FESV","area_ha":100,
                "components":[{"parametro":"Serapilheira","tc":3.075,
                    "area_ha":100,"total_tc":None,"experimental_total_tc":307.5,
                    "origem":"EXPERIMENTAL_FISICO","fonte":"inventários FESV",
                    "metodo":"hierarquia regional","uncertainty_kind":"preditivo 90%",
                    "source_url":"https://example.org/data"}]}]}
        rows=litter_dashboard_summaries(native)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["status"],"CENÁRIO EXPERIMENTAL — FORA DO TOTAL CONHECIDO")
        self.assertAlmostEqual(rows[0]["tc_ha"],3.075)
        self.assertAlmostEqual(rows[0]["stock_tc"],307.5)
        self.assertIn("preditivo 90%",rows[0]["note"])
        self.assertIn("https://example.org/data",rows[0]["note"])

    def test_supported_carbon_value_keeps_value_when_uncertainty_is_not_measurable(self):
        native={"area_aoi_ha":10,"native_area_ha":10,"known_total_tc":50,"complete":False,
                "strata":[{"class_name":"FESV","area_ha":10,"components":[
                    {"parametro":"Biomassa aérea","tc":5,"total_tc":50,"quantified_area_ha":10}]}]}
        lines=executive_carbon_lines(native,lambda x:f"{x:.2f}" if x is not None else "N/D")
        joined="\\n".join(lines)
        self.assertIn("5.00 tC/ha",joined)
        self.assertIn("incerteza não mensurável",joined)
        self.assertNotIn("N/D tC/ha | N/D tCO₂e/ha | N/D % — incerteza",joined)

if __name__=="__main__":
    unittest.main()
