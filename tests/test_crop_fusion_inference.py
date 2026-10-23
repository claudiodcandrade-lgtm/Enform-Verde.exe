import unittest
from crop_fusion_inference import decide_crop_with_phenology

class CropFusionTests(unittest.TestCase):
    def fixture(self):
        obs={"height_m":1.4,"height_uncertainty_m":0.2,"observation_date":"2026-02-15",
             "phenological_stage":"vegetative","municipality_code":"5103403","state":"MT","season":"2025/2026"}
        height={"height_source":"SAR_height_product","retrieval_model":"synthetic",
                "validation_reference":"synthetic","sensor":"test","processing":"test",
                "date":"2026-02-15","uncertainty_method":"prediction_interval_half_width",
                "rmse_m":0.4,"domain":"synthetic","independent_validation":True}
        record={"crop":"Soja","source_url":"https://example.invalid/zarc","source_institution":"MAPA",
                "state":"MT","municipality_code":"5103403","season":"2025/2026",
                "valid_year":2026,"planting_windows":[{"start":"2025-11-01","end":"2025-12-15"}],
                "stage_intervals_days":{"vegetative":[30,115]},
                "stage_reference_url":"https://example.invalid/fenologia"}
        gate={"Soja":{"eligible":True,"n_independent":100,"precision_wilson95_lower":.96}}
        return obs,height,record,gate
    def call(self,p=None):
        o,h,r,g=self.fixture()
        return decide_crop_with_phenology(p or {"Soja":.95,"Milho":.05},o,h,{"Soja":r},g,model_source="fixture")
    def test_accepted_only_as_supported_inference(self):
        r=self.call()
        self.assertEqual(r["crop"],"Soja")
        self.assertEqual(r["status"],"ACEITO_COM_EVIDENCIA_REGIONAL")
    def test_weak_score_rejected(self):
        self.assertIsNone(self.call({"Soja":.6,"Milho":.4})["crop"])
    def test_independent_validation_is_required(self):
        o,h,r,g=self.fixture();g["Soja"]["eligible"]=False
        self.assertIsNone(decide_crop_with_phenology({"Soja":1},o,h,{"Soja":r},g,model_source="fixture")["crop"])
    def test_regional_mismatch_abstains(self):
        o,h,r,g=self.fixture();o["state"]="PA"
        self.assertIsNone(decide_crop_with_phenology({"Soja":1},o,h,{"Soja":r},g,model_source="fixture")["crop"])
    def test_height_not_optional(self):
        o,h,r,g=self.fixture();h["independent_validation"]=False
        self.assertIsNone(decide_crop_with_phenology({"Soja":1},o,h,{"Soja":r},g,model_source="fixture")["crop"])
    def test_invalid_probabilities_rejected(self):
        self.assertIsNone(self.call({"Soja":1.2,"Milho":-.2})["crop"])

if __name__=="__main__":
    unittest.main()
