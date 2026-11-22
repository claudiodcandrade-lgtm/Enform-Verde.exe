import unittest
from integrated_system_classifier import identify_integrated_system, validated_precision_interval, model_route_status, classify_integrated_batch
from crop_monitoring_forecast import _integrated_system_audit

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
    def test_batch_route_preserves_abstention(self):
        rows=[{"observation_id":"A","components":{c:item(c) for c in ("lavoura","floresta")}},
              {"observation_id":"B","components":{"lavoura":item("lavoura")}}]
        report=classify_integrated_batch(rows)
        self.assertEqual(report["accepted"],1)
        self.assertEqual(report["abstained"],1)
        self.assertEqual(report["results"][0]["class_name"],"ILF")
        self.assertIsNone(report["results"][1]["class_name"])
    def test_ilpf(self):
        evidence={c:item(c) for c in ("lavoura","pecuaria","floresta")}
        self.assertEqual(identify_integrated_system(evidence)["class_name"],"ILPF")
    def test_ilf(self):
        self.assertEqual(identify_integrated_system(
            {c:item(c) for c in ("lavoura","floresta")})["class_name"],"ILF")
    def test_ipf(self):
        self.assertEqual(identify_integrated_system(
            {c:item(c) for c in ("pecuaria","floresta")})["class_name"],"IPF")
    def test_ilp(self):
        self.assertEqual(identify_integrated_system(
            {c:item(c) for c in ("lavoura","pecuaria")})["class_name"],"ILP")
    def test_scientific_ilp_ilpf_routes_reach_report_audit(self):
        evidence={c:item(c) for c in ("lavoura","pecuaria")}
        result=_integrated_system_audit({"integrated_system_evidence":[
            {"observation_id":"talhao-1","components":evidence}]})
        self.assertEqual(result["records"][0]["decision"]["class_name"],"ILP")
        route=result["records"][0]["classifier_route"]
        self.assertFalse(route["operational"])
        self.assertIn("MOD13Q1",route["task"])
        self.assertEqual(route["reported_metrics"]["f1"],0.995)
        self.assertEqual(result["route_catalog"]["ILPF"]["reported_metrics"]["iou"],0.8815)
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
