import unittest

from root_allometry_uncertainty import cairns_root_prediction

class RootUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.calibration={
            "source":"Independent root plots (synthetic test fixture)",
            "applicable_physiognomy":"Floresta Ombrófila Densa",
            "agb_sd_mg_ha":10.0,
            "agb_uncertainty_kind":"AOI_mean_standard_error",
            "coefficient_covariance":[[0.01,0.0],[0.0,0.001]],
            "residual_sd_log":0.15,
            "independent_validation":True,
        }

    def test_point_estimate_never_fakes_interval(self):
        r=cairns_root_prediction(100)
        self.assertGreater(r["mean_model_tc_ha"],0)
        self.assertIsNone(r["conditional_prediction_interval_tc_ha"])
        self.assertFalse(r["coverage_validated"])

    def test_conditional_interval_is_nonnegative_and_reproducible(self):
        first=cairns_root_prediction(100,calibration=self.calibration,draws=1200)
        second=cairns_root_prediction(100,calibration=self.calibration,draws=1200)
        self.assertEqual(first,second)
        lo,hi=first["conditional_prediction_interval_tc_ha"]
        self.assertLess(lo,first["mean_model_tc_ha"])
        self.assertGreater(hi,first["mean_model_tc_ha"])
        self.assertFalse(first["coverage_validated"])
        self.assertIn("not_validated",first["uncertainty_status"])

    def test_reject_negative_or_nonfinite_aboveground_biomass(self):
        for value in (-1,0,float("nan"),float("inf"),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                cairns_root_prediction(value)

    def test_reject_missing_and_unvalidated_calibration(self):
        for field in ("source","agb_sd_mg_ha","residual_sd_log","coefficient_covariance"):
            c=dict(self.calibration);c.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):
                cairns_root_prediction(100,calibration=c,draws=1000)
        c=dict(self.calibration);c["independent_validation"]=False
        with self.assertRaises(ValueError):
            cairns_root_prediction(100,calibration=c,draws=1000)

    def test_reject_invalid_covariance(self):
        c=dict(self.calibration)
        c["coefficient_covariance"]=[[1,2],[2,1]]
        with self.assertRaises(ValueError):
            cairns_root_prediction(100,calibration=c,draws=1000)

    def test_no_spurious_precision_when_only_zero_variances_known(self):
        c=dict(self.calibration)
        c["agb_sd_mg_ha"]=0
        c["residual_sd_log"]=0
        c["coefficient_covariance"]=[[0,0],[0,0]]
        r=cairns_root_prediction(100,calibration=c,draws=1000)
        self.assertAlmostEqual(r["conditional_prediction_interval_tc_ha"][0],
                               r["conditional_prediction_interval_tc_ha"][1],places=8)

if __name__=="__main__":
    unittest.main()
