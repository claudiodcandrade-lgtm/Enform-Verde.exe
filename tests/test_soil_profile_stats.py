import unittest
from soil_profile_stats import summarize_paired_soil_profiles as summarize

class PairedSoilProfileRegression(unittest.TestCase):
    def test_zero_to_100_requires_all_five_layers_at_same_location(self):
        observations = [
            {2:10,3:20,4:30,5:40,6:50},
            {2:20,3:30,4:40},  # deep layers unavailable at this point
        ]
        out = summarize(observations)
        self.assertAlmostEqual(out["0–30 cm"]["tc_ha"], 75)
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"], 150)
        self.assertEqual(out["0–30 cm"]["n_samples"], 2)
        self.assertEqual(out["0–100 cm"]["n_samples"], 1)
        self.assertIsNone(out["0–100 cm"]["spatial_sd_tc_ha"])
        self.assertFalse(out["0–100 cm"]["predictive_uncertainty_quantified"])
        self.assertNotIn("0–200 cm", out)

    def test_disjoint_horizons_never_create_artificial_profile(self):
        out = summarize([{2: 10,3:20}, {4:30,5:40,6:50}])
        self.assertEqual(out, {})

    def test_pairwise_total_sd_captures_negative_covariance(self):
        out = summarize([{2:10,3:20,4:30}, {2:20,3:10,4:30}])
        self.assertEqual(out["0–30 cm"]["tc_ha"], 60)
        self.assertEqual(out["0–30 cm"]["spatial_sd_tc_ha"], 0)

    def test_paired_layer_means_share_same_sample_cohort(self):
        out = summarize([{2:10,3:20,4:30,5:40,6:50},
                         {2:200,3:300,4:400}])
        self.assertEqual(out["0–100 cm"]["layer_means_tc_ha"]["0–5"], 10)
        self.assertEqual(out["0–30 cm"]["layer_means_tc_ha"]["0–5"], 105)

    def test_missing_not_zero(self):
        out = summarize([{2:0,3:0,4:0}, {2:50,3:20}])
        self.assertEqual(out["0–30 cm"]["n_samples"], 1)
        self.assertEqual(out["0–30 cm"]["tc_ha"],0)

    def test_bad_inputs_fail_closed(self):
        for bad in ([{2:-1}], [{2:float("nan")}], [{2:float("inf")}], [{2:None}], [{2:True}], "not a sequence", [None]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    summarize(bad)

if __name__ == "__main__":
    unittest.main()
