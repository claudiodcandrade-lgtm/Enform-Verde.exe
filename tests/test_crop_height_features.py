"""Tests for crop-height evidence guards; no classification accuracy claimed."""
import unittest
from crop_height_features import check_crop_height_observation, height_interval_features

class CropHeightTests(unittest.TestCase):
    def fixture(self):
        obs={"height_m":1.5,"height_uncertainty_m":0.3,"observation_date":"2025-05-15","phenological_stage":"vegetative"}
        contract={"height_source":"SAR_height_product","retrieval_model":"synthetic_test",
                  "height_source_url":"https://example.org/height","model_sha256":"a"*64,
                  "validation_reference":"synthetic_test","sensor":"test","processing":"test",
                  "date":"2025-05-15","uncertainty_method":"prediction_interval_half_width",
                  "rmse_m":0.4,"bias_m":0.0,"domain":"synthetic","crop":"milho",
                  "region":"test-region","phase":"vegetative","n_independent":80,
                  "n_spatial_blocks":5,"coverage_95":0.95,
                  "independent_validation":True,"in_domain_validation":True}
        return obs,contract
    def test_bounded_features(self):
        o,c=self.fixture()
        data,a=height_interval_features(o,c)
        self.assertTrue(a["eligible"])
        self.assertAlmostEqual(data["height_lower_m"],1.2)
        self.assertAlmostEqual(data["height_upper_m"],1.8)
    def test_missing_independent_validation(self):
        o,c=self.fixture();c["independent_validation"]=False
        self.assertFalse(check_crop_height_observation(o,c)["eligible"])
    def test_mismatched_date(self):
        o,c=self.fixture();o["observation_date"]="2025-05-16"
        self.assertFalse(check_crop_height_observation(o,c)["eligible"])
    def test_backscatter_cannot_be_height(self):
        o,c=self.fixture();c["height_source"]="Sentinel-1_VH"
        self.assertFalse(check_crop_height_observation(o,c)["eligible"])
    def test_uncertainty_required(self):
        o,c=self.fixture();o.pop("height_uncertainty_m")
        data,a=height_interval_features(o,c)
        self.assertIsNone(data)
        self.assertFalse(a["eligible"])
if __name__=="__main__":
    unittest.main()
