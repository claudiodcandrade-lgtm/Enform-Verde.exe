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
        self.assertEqual(rows["Biomassa subterrânea"]["stock_tc"], None)
        self.assertIn("N/D", rows["Biomassa subterrânea"]["status"])
        self.assertEqual(tuple(rows), COMPARTMENTS)

    def test_does_not_combine_strata_without_declared_covariance(self):
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
        self.assertIsNone(row["uncertainty_tc_ha"])
        self.assertIn("covariância", row["uncertainty_kind"])


if __name__ == "__main__":
    unittest.main()
