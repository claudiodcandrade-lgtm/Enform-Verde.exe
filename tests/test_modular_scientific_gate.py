"""Tests for modular evidence registry. Registry validity is not scientific approval."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.modular_scientific_gate import assess

SHA = "a" * 40
BASE = {"biome": "Amazônia", "pool": "agb", "fitofisionomia": "Floresta Ombrófila Densa"}

class ModularGateTests(unittest.TestCase):
    def test_empty_registry_fails(self):
        self.assertFalse(assess({"source_sha": SHA, "capabilities": []}, SHA, ".")["passed"])

    def test_nd_is_explicit_not_validated(self):
        row = dict(BASE, status="not_available", reason="SAR raster unavailable")
        result = assess({"source_sha": SHA, "capabilities": [row]}, SHA, ".")
        self.assertTrue(result["passed"])
        self.assertEqual(result["validated_count"], 0)
        self.assertEqual(result["not_available_count"], 1)

    def test_claimed_validation_without_real_data_fails(self):
        row = dict(BASE, status="validated", evidence_type="literature_mean")
        result = assess({"source_sha": SHA, "capabilities": [row]}, SHA, ".")
        self.assertFalse(result["passed"])
        self.assertEqual(result["validated_count"], 0)

    def test_validated_report_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "report.json").write_bytes(b"real-validation-report")
            row = dict(BASE, status="validated", evidence_type="independent_real_data",
                       source_url="https://example.org/data", dataset_sha256="f" * 64,
                       validation_report="report.json",
                       validation_report_sha256=hashlib.sha256(b"real-validation-report").hexdigest(),
                       uncertainty_kind="predictive_interval", domain="microrregional FOD",
                       transfer_error_method="independent spatial holdout")
            self.assertTrue(assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)["passed"])
            (root / "report.json").write_bytes(b"tampered")
            self.assertFalse(assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)["passed"])

    def test_malformed_types_do_not_crash(self):
        row = dict(BASE, biome=["Amazônia"], status="validated")
        result = assess({"source_sha": SHA, "capabilities": [row]}, SHA, ".")
        self.assertFalse(result["passed"])
        self.assertEqual(result["validated_count"], 0)

    def test_soil_depth_must_be_complete(self):
        row = dict(BASE, pool="soil_0_100", status="experimental", reason="transferred model",
                   source_url="https://example.org", dataset_sha256="f" * 64,
                   validation_report="missing.json", validation_report_sha256="f" * 64,
                   uncertainty_kind="prediction_interval", domain="test",
                   transfer_error_method="spatial validation", depth_cm=[0, 30])
        result = assess({"source_sha": SHA, "capabilities": [row]}, SHA, ".")
        self.assertTrue(any("0-100" in e for e in result["errors"]))

if __name__ == "__main__":
    unittest.main()
