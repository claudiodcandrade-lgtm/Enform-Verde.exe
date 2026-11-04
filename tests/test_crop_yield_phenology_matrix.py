"""Matrix tests use synthetic fixtures, not observed productivity or SAR validation."""
import unittest
from crop_yield_phenology_matrix import design_features,integrate_yield_matrix,validate_field_observation
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
