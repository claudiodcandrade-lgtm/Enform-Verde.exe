import unittest

from carbon_dashboard_table import COMPARTMENTS, carbon_dashboard_rows


class CarbonDashboardTableTests(unittest.TestCase):
    def test_keeps_stock_and_uncertainty_by_pool_without_zero_imputation(self):
        native = {
            "native_area_ha": 10.0,
            "strata": [{"area_ha": 10.0, "components": [
                {"parametro": "Biomassa aérea", "tc": 20.0, "total_tc": 200.0,
                 "area_ha": 10.0, "quantified_area_ha": 10.0,
                 "range_tc_ha": [18.0, 22.0]},
            ]}],
        }
        rows = {row["compartment"]: row for row in carbon_dashboard_rows(native)}
        self.assertEqual(rows["Biomassa aérea"]["tc_ha"], 20.0)
        self.assertEqual(rows["Biomassa aérea"]["stock_tc"], 200.0)
        self.assertEqual(rows["Biomassa aérea"]["uncertainty_tc_ha"], 2.0)
        self.assertEqual(rows["Biomassa aérea"]["uncertainty_percent"],10.0)
        self.assertEqual(rows["Biomassa subterrânea"]["stock_tc"], None)
        self.assertIn("N/D", rows["Biomassa subterrânea"]["status"])
        self.assertEqual(tuple(rows), COMPARTMENTS)

    def test_combines_biomass_uncertainty_conservatively_with_rho_one(self):
        native = {
            "native_area_ha": 20.0,
            "strata": [{"area_ha": 10.0, "components": [
                {"parametro": "Biomassa aérea", "tc": 10.0, "total_tc": 100.0,
                 "area_ha": 10.0, "quantified_area_ha": 10.0,
                 "range_tc_ha": [8.0, 12.0]},
            ]}, {"area_ha": 10.0, "components": [
                {"parametro": "Biomassa aérea", "tc": 12.0, "total_tc": 120.0,
                 "area_ha": 10.0, "quantified_area_ha": 10.0,
                 "range_tc_ha": [10.0, 14.0]},
            ]}],
        }
        row = carbon_dashboard_rows(native)[0]
        self.assertEqual(row["stock_tc"], 220.0)
        self.assertEqual(row["area_ha"], 20.0)
        self.assertEqual(row["uncertainty_tc_ha"], 2.0)
        self.assertIn("ρ=1", row["uncertainty_kind"])

    def test_soil_spatial_sd_is_pooled_as_descriptive_only(self):
        native={"native_area_ha":20,"strata":[
            {"area_ha":10,"components":[{"parametro":"Solo 0–100 cm","tc":80,"total_tc":800,
              "area_ha":10,"quantified_area_ha":10,"spatial_sd_tc_ha":5}]},
            {"area_ha":10,"components":[{"parametro":"Solo 0–100 cm","tc":100,"total_tc":1000,
              "area_ha":10,"quantified_area_ha":10,"spatial_sd_tc_ha":5}]}]}
        row=carbon_dashboard_rows(native)[-1]
        self.assertAlmostEqual(row["uncertainty_tc_ha"],(125.0)**0.5)
        self.assertAlmostEqual(row["uncertainty_percent"],100*(125.0**0.5)/90)
        self.assertIn("NÃO é erro de predição",row["uncertainty_kind"])

    def test_partial_root_sensitivity_is_exposed_separately(self):
        native={"native_area_ha":10,"strata":[{"area_ha":10,"components":[
            {"parametro":"Biomassa subterrânea","tc":10,"total_tc":100,"area_ha":10,
             "quantified_area_ha":10,"sensitivity_tc_ha":5,"sensitivity_kind":"parâmetro alométrico"}]}]}
        row=carbon_dashboard_rows(native)[1]
        self.assertIsNone(row["uncertainty_tc_ha"])
        self.assertEqual(row["sensitivity_tc_ha"],5)
        self.assertEqual(row["sensitivity_percent"],50.0)


if __name__ == "__main__":
    unittest.main()
