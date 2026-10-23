"""Unit tests for optional crop model registry (synthetic metadata only)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from crop_model_registry import CROPS, audit_registry, evaluate_crop_model, model_accepts_scene


class CropRegistryTests(unittest.TestCase):
    def specimen(self, folder, crop="Soja"):
        p = Path(folder) / "weights.bin"
        p.write_bytes(b"synthetic-only-not-a-real-model")
        return {
            "crop": crop, "model_id": "fixture", "model_version": "1",
            "repository_url": "https://example.invalid/model",
            "license": "test-only", "sensor": "Sentinel-1",
            "processing": "RTC gamma0 linear", "period": "2025-crop-season",
            "domain": {"region": "synthetic"}, "feature_schema": ["VV", "VH"],
            "modality": "SAR-only", "sar_features": ["VV", "VH"],
            "weights": {"path": "weights.bin", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()},
            "validation": {"reference_url": "https://example.invalid/validation",
                           "reference_sha256": "synthetic", "split_protocol": "field-and-year-held-out",
                           "geographic_domain": "synthetic", "temporal_domain": "2025",
                           "confusion_matrix": [[100,0],[0,100]],
                           "calibration_method": "synthetic",
                           "independent": True, "representative": True,
                           "n_accepted": 100, "n_correct": 100,
                           "calibrated_probability_threshold": 0.90}}
    def test_eight_names(self):
        self.assertEqual(len(CROPS), 8)
    def test_no_weights_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            m = self.specimen(d)
            Path(d,"weights.bin").unlink()
            r=evaluate_crop_model(m,base_dir=d)
            self.assertFalse(r["eligible"])
            self.assertIn("arquivo de pesos indisponível",r["reasons"])
    def test_precision_and_samples(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.specimen(d)
            m["validation"]["n_accepted"]=49
            self.assertFalse(evaluate_crop_model(m,base_dir=d)["eligible"])
            m["validation"]["n_accepted"]=100
            m["validation"]["n_correct"]=90
            self.assertFalse(evaluate_crop_model(m,base_dir=d)["eligible"])
    def test_incompatible_scene(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.specimen(d)
            scene={k:m[k] for k in ("sensor","processing","period","modality","feature_schema","domain")}
            self.assertTrue(model_accepts_scene(m,scene))
            scene["processing"]="sigma0 dB"
            self.assertFalse(model_accepts_scene(m,scene))
    def test_missing_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.specimen(d)
            m["validation"]["independent"]=False
            self.assertFalse(evaluate_crop_model(m,base_dir=d)["eligible"])
    def test_manifest_is_audit_not_inference(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d,"registry.json")
            p.write_text(json.dumps({"models":[self.specimen(d)]}),encoding="utf-8")
            r=audit_registry(p)
            self.assertEqual(r["eligible_models"],1)
            self.assertIn("NÃO EXECUTADA",r["inference_status"])


if __name__ == "__main__":
    unittest.main()
