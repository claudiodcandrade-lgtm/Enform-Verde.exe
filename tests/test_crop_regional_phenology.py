"""Synthetic regional crop calendar checks: not agronomic validation."""
import unittest
from crop_regional_phenology import regional_stage_evidence

class RegionalPhenologyTests(unittest.TestCase):
    def fixture(self):
        obs={"height_m":1.4,"height_uncertainty_m":0.2,"observation_date":"2026-02-15",
             "phenological_stage":"vegetative","municipality_code":"5103403","state":"MT","season":"2025/2026"}
        contract={"height_source":"SAR_height_product","retrieval_model":"synthetic",
                  "height_source_url":"https://example.invalid/height","model_sha256":"a"*64,
                  "validation_reference":"synthetic","sensor":"Sentinel-1 test","processing":"test",
                  "date":"2026-02-15","uncertainty_method":"prediction_interval_half_width",
                  "rmse_m":0.4,"bias_m":0.0,"domain":"synthetic","crop":"Soja",
                  "region":"MT","phase":"vegetative","n_independent":80,
                  "n_spatial_blocks":5,"coverage_95":0.95,
                  "independent_validation":True,"in_domain_validation":True}
        record={"crop":"Soja","source_url":"https://example.invalid/zarc","source_institution":"MAPA",
                "state":"MT","municipality_code":"5103403","season":"2025/2026",
                "valid_year":2026,"planting_windows":[{"start":"2025-11-01","end":"2025-12-15"}],
                "stage_intervals_days":{"vegetative":[30,115],"harvest":[120,180]},
                "stage_reference_url":"https://example.invalid/fenologia"}
        return obs,contract,record

    def test_plausible_regional_stage(self):
        o,c,r=self.fixture()
        ans=regional_stage_evidence("Soja",o,c,r)
        self.assertTrue(ans["eligible_as_supporting_feature"])
        self.assertIn("vegetative",ans["possible_stages"])
    def test_geographic_mismatch(self):
        o,c,r=self.fixture();o["state"]="PA"
        self.assertFalse(regional_stage_evidence("Soja",o,c,r)["eligible_as_supporting_feature"])
    def test_out_of_season(self):
        o,c,r=self.fixture();r["planting_windows"]=[{"start":"2026-02-14","end":"2026-02-15"}]
        self.assertFalse(regional_stage_evidence("Soja",o,c,r)["eligible_as_supporting_feature"])
    def test_no_height_validation(self):
        o,c,r=self.fixture();c["independent_validation"]=False
        self.assertFalse(regional_stage_evidence("Soja",o,c,r)["eligible_as_supporting_feature"])
    def test_no_pretend_crop_inference(self):
        o,c,r=self.fixture()
        result=regional_stage_evidence("Soja",o,c,r)
        self.assertNotIn("classification",result)
        self.assertNotIn("probability",result)

if __name__=="__main__":
    unittest.main()
