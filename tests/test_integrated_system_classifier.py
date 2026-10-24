import unittest
from integrated_system_classifier import identify_integrated_system, validated_precision_interval, model_route_status

def item(component, unit="T1", period="2026", confidence=0.98):
    return {"present":True,"validated":True,"confidence":confidence,
            "unit_id":unit,"period":period,"source":"referencia_"+component}

class IntegratedSystemTests(unittest.TestCase):
    def test_precision_interval_is_not_area_interval(self):
        interval=validated_precision_interval(95,100)
        self.assertLess(interval["ci95"][0],0.95)
        self.assertGreater(interval["ci95"][1],0.95)
        self.assertIsNone(validated_precision_interval(101,100))
    def test_unverified_published_model_is_not_operational(self):
        self.assertFalse(model_route_status("ilpf_spatial_unet")["operational"])
    def test_ilpf(self):
        evidence={c:item(c) for c in ("lavoura","pecuaria","floresta")}
        self.assertEqual(identify_integrated_system(evidence)["class_name"],"ILPF")
    def test_ilf(self):
        self.assertEqual(identify_integrated_system(
            {c:item(c) for c in ("lavoura","floresta")})["class_name"],"ILF")
    def test_ipf(self):
        self.assertEqual(identify_integrated_system(
            {c:item(c) for c in ("pecuaria","floresta")})["class_name"],"IPF")
    def test_spatial_mismatch_abstains(self):
        evidence={"lavoura":item("lavoura"),"floresta":item("floresta",unit="T2")}
        self.assertIsNone(identify_integrated_system(evidence)["class_name"])
    def test_missing_validation_abstains(self):
        evidence={"lavoura":item("lavoura"),"floresta":item("floresta")}
        evidence["floresta"]["validated"]=False
        self.assertIsNone(identify_integrated_system(evidence)["class_name"])
    def test_low_confidence_abstains(self):
        evidence={"pecuaria":item("pecuaria"),"floresta":item("floresta",confidence=0.8)}
        self.assertIsNone(identify_integrated_system(evidence)["class_name"])

if __name__=="__main__":
    unittest.main()
