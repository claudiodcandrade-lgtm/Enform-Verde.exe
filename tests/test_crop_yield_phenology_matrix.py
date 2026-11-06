"""Matrix tests use synthetic fixtures, not observed productivity or SAR validation."""
import unittest
from crop_yield_phenology_matrix import design_features,integrate_yield_matrix,validate_field_observation,experimental_prior_projection
from crop_specific_model_registry import MODEL_REGISTRY

def fixtures(crop):
    stages=MODEL_REGISTRY[crop]["critical_stages"]
    obs={s:{"eta_etc":.75,"heat_z":.3,"sar_vigor_z":-.25,
            "sar_scene_ids":["SCENE-UNIT-TEST"],"sar_acquisition_utc":"2026-11-01T10:00:00Z",
            "sar_pixels_read":True,"weather_source":"NASA POWER"} for s in stages}
    return obs,{s:.8 for s in stages}

class TestPhenologyMatrix(unittest.TestCase):
    def test_stage_features(self):
        for crop in MODEL_REGISTRY:
            obs,ky=fixtures(crop)
            names,x=design_features(crop,{"stages":obs},ky_by_stage=ky)
            self.assertEqual(len(x),4*len(obs))
            self.assertEqual(len(names),len(x))
            self.assertAlmostEqual(x[0],.2)
            self.assertAlmostEqual(x[3],-.05)
    def test_sar_conditional_fails_closed_without_real_fit(self):
        obs,ky=fixtures("Soja")
        r=integrate_yield_matrix("Soja",pam_baseline_kg_ha=3200.,stages=obs,ky_by_stage=ky)
        self.assertEqual(r["status"],"N/D")
        self.assertEqual(r["pam_baseline_kg_ha"],3200.)
    def test_published_prior_missing_is_nd(self):
        obs,ky=fixtures("Soja")
        r=experimental_prior_projection("Soja",pam_baseline_kg_ha=3200.,stages=obs,ky_by_stage=ky,published_prior=None)
        self.assertEqual(r["status"],"N/D")
    def test_scientific_prior_fixture_propagates_nonzero_uncertainty(self):
        obs,ky=fixtures("Soja")
        names,_=design_features("Soja",{"stages":obs},ky_by_stage=ky)
        # Synthetic PRIOR INPUT as UNIT TEST, never claim real calibrated paper.
        prior={"crop":"Soja","feature_names":names,
               "source_url":"https://example.org/unit-test-fixture",
               "coefficient_domain":"TEST DATA ONLY","reviewed_crop_stage_transfer":True,
               "coeff_mean":[0.]*len(names),"coeff_sd":[25.]*len(names),
               "historical_residuals_kg_ha":[-300.,-200.,-100.,0.,100.,200.,300.],
               "baseline_uncertainty_kg_ha":125.,"transfer_sd_kg_ha":150.}
        r=experimental_prior_projection("Soja",pam_baseline_kg_ha=3200.,
            stages=obs,ky_by_stage=ky,published_prior=prior,n_mc=500,seed=9)
        self.assertEqual(r["status"],"experimental_literature_prior_not_field_validated")
        self.assertLess(r["p05_kg_ha"],r["median_kg_ha"])
        self.assertLess(r["median_kg_ha"],r["p95_kg_ha"])
        self.assertAlmostEqual(r["median_sacks_60kg_ha"],r["median_kg_ha"]/60)
        self.assertEqual(r["interval_90_relative_percent"][0]<0,True)
        self.assertEqual(r["interval_90_relative_percent"][1]>0,True)
        self.assertEqual(r["seed"],9)
    def test_yield_observation_requires_evidence(self):
        obs,_=fixtures("Soja")
        o={"field_id":"TEST","harvest_year":2026,"observed_yield_source":"independent_field",
           "observed_yield_kg_ha":3200.,"stages":obs}
        validate_field_observation("Soja",o)
        o["observed_yield_source"]=""
        with self.assertRaises(ValueError):
            validate_field_observation("Soja",o)

if __name__=="__main__":
    unittest.main()
