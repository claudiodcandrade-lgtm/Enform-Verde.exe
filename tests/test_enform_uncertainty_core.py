import unittest
from enform_uncertainty_core import aggregate_stock, soil_horizon_stock_tc_ha

class UncertaintyCoreTests(unittest.TestCase):
    def test_soil_units(self):
        self.assertAlmostEqual(soil_horizon_stock_tc_ha(30,1.2,.02),72.)
        self.assertAlmostEqual(soil_horizon_stock_tc_ha(30,1.2,.02,.25),54.)
    def test_correlated_strata(self):
        r=aggregate_stock([1,1],[10,20],[[4,4],[4,4]])
        self.assertEqual(r["stock_tC"],30)
        self.assertAlmostEqual(r["se_tC"],4)
        self.assertAlmostEqual(r["stock_tCO2e"],110)
    def test_missing_covariance_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_stock([1,2],[10,20],[[1]])
    def test_negative_variance_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_stock([1],[10],[[-1]])
    def test_indefinite_matrix_rejected_even_with_positive_total_variance(self):
        with self.assertRaisesRegex(ValueError,"positive semidefinite"):
            aggregate_stock([1,1],[10,20],[[1,2],[2,1]])
    def test_zero_variance_cannot_have_nonzero_covariance(self):
        with self.assertRaisesRegex(ValueError,"zero-variance"):
            aggregate_stock([1,1],[10,20],[[0,1],[1,4]])
    def test_normal_interval_never_claims_calibration(self):
        r=aggregate_stock([1],[10],[[4]])
        self.assertIs(r["coverage_validated"],False)
        self.assertEqual(r["interval_method"],"normal_approximation_clipped_at_zero")
if __name__ == "__main__":
    unittest.main()
