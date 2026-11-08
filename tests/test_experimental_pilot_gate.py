import copy
import json
import unittest
from pathlib import Path

from tools.experimental_pilot_gate import assess


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class ExperimentalPilotGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "validation/experimental_models.json").read_text(encoding="utf-8"))

    def test_pre_field_model_set_is_ready_without_claiming_homologation(self):
        result = assess(self.manifest, SHA, ROOT)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["model_count"], 14)
        self.assertEqual(result["field_validation"], "pending")
        self.assertFalse(result["scientifically_homologated"])
        self.assertEqual({m["field_validation_status"] for m in result["models"]}, {"pending"})
        self.assertTrue(all(len(m["module_sha256"]) == 64 for m in result["models"]))

    def test_field_validation_cannot_be_marked_complete_by_pre_field_manifest(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["models"][0]["field_validation_status"] = "passed"
        result = assess(manifest, SHA, ROOT)
        self.assertFalse(result["passed"])
        self.assertTrue(any("field validation must be explicitly pending" in e for e in result["errors"]))

    def test_pre_field_profile_rejects_empirical_accuracy_claims(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["models"][0]["rmse"] = 0.2
        result = assess(manifest, SHA, ROOT)
        self.assertFalse(result["passed"])
        self.assertTrue(any("cannot claim empirical validation metrics" in e for e in result["errors"]))

    def test_bad_entrypoint_fails_closed(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["models"][0]["entrypoint"] = "fabricated_estimator"
        result = assess(manifest, SHA, ROOT)
        self.assertFalse(result["passed"])
        self.assertTrue(any("declared entrypoint not found" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
