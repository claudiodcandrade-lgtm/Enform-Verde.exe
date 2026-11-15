"""Owner decision 4 = B: experimental radar height from a published model, error propagated."""
import unittest

from crop_height_features import check_crop_height_observation

C = {"validation_tier": "experimental_published", "height_source": "SAR_height_product",
     "retrieval_model": "regressão publicada VH/VV", "height_source_url": "https://doi.org/x",
     "sensor": "Sentinel-1", "date": "2026-10-31", "rmse_m": 0.10, "n_independent": 40,
     "crop": "Soja", "phase": "V6-R2"}
O = {"height_m": 0.55, "height_uncertainty_m": 0.10, "observation_date": "2026-10-31",
     "phenological_stage": "V8"}


class ExperimentalPublishedHeight(unittest.TestCase):
    def test_published_model_with_propagated_rmse_is_experimental_eligible(self):
        r = check_crop_height_observation(O, C)
        self.assertTrue(r["eligible"], r["reasons"]); self.assertTrue(r["experimental"])
        self.assertFalse(r["transfer_error_quantified"])

    def test_error_must_be_propagated(self):
        r = check_crop_height_observation(dict(O, height_uncertainty_m=0.02), C)
        self.assertFalse(r["eligible"])

    def test_missing_published_error_is_rejected(self):
        c = dict(C); c.pop("rmse_m")
        self.assertFalse(check_crop_height_observation(O, c)["eligible"])

    def test_validated_tier_keeps_strict_contract(self):
        c = dict(C); c.pop("validation_tier")
        self.assertFalse(check_crop_height_observation(O, c)["eligible"])


if __name__ == "__main__":
    unittest.main()
