"""Tests for modular evidence registry. Registry validity is not scientific approval."""
import hashlib
import json
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
        self.assertFalse(result["scientifically_homologated"])

    def test_claimed_validation_without_real_data_fails(self):
        row = dict(BASE, status="validated", evidence_type="literature_mean")
        result = assess({"source_sha": SHA, "capabilities": [row]}, SHA, ".")
        self.assertFalse(result["passed"])
        self.assertEqual(result["validated_count"], 0)

    def test_validated_report_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = b"independent plot observations for test fixture only"
            (root / "plots.csv").write_bytes(raw)
            raw_sha = hashlib.sha256(raw).hexdigest()
            report = {"dataset_sha256": raw_sha, "independent_sample_count": 3,
                      "rmse": 5.2, "mae": 4.1, "bias": -0.4, "interval_coverage": 0.9,
                      "train_partition": "geographic_tile_A", "test_partition": "geographic_tile_B",
                      "validation_design": "spatial holdout", "unit": "Mg/ha",
                      "train_spatial_units": 4, "test_spatial_units": 3}
            report_bytes = json.dumps(report).encode("utf-8")
            (root / "report.json").write_bytes(report_bytes)
            row = dict(BASE, status="validated", evidence_type="independent_real_data",
                       source_url="https://example.org/data", dataset_sha256=raw_sha,
                       dataset_file="plots.csv",
                       validation_report="report.json",
                       validation_report_sha256=hashlib.sha256(report_bytes).hexdigest(),
                       uncertainty_kind="predictive_interval", domain="microrregional FOD",
                       transfer_error_method="independent spatial holdout")
            validated = assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)
            self.assertTrue(validated["passed"])
            self.assertTrue(validated["scientifically_homologated"])
            # Inflating n from plot rows (12) while only 3 spatial units are
            # held out must never be accepted as independent validation.
            inflated = dict(report, independent_sample_count=12)
            inflated_bytes = json.dumps(inflated).encode("utf-8")
            (root / "report.json").write_bytes(inflated_bytes)
            inflated_row = dict(row, validation_report_sha256=hashlib.sha256(inflated_bytes).hexdigest())
            rejected = assess({"source_sha": SHA, "capabilities": [inflated_row]}, SHA, root)
            self.assertFalse(rejected["passed"])
            self.assertTrue(any("must equal distinct test spatial units" in e for e in rejected["errors"]))
            (root / "report.json").write_bytes(report_bytes)
            (root / "plots.csv").write_bytes(b"tampered observations")
            self.assertFalse(assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)["passed"])
            (root / "plots.csv").write_bytes(raw)
            no_raw_pointer = dict(row)
            no_raw_pointer.pop("dataset_file")
            self.assertFalse(assess({"source_sha": SHA, "capabilities": [no_raw_pointer]}, SHA, root)["passed"])
            report["test_spatial_units"] = 1
            wrong_units = json.dumps(report).encode("utf-8")
            (root / "report.json").write_bytes(wrong_units)
            row["validation_report_sha256"] = hashlib.sha256(wrong_units).hexdigest()
            self.assertFalse(assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)["passed"])
            report["test_spatial_units"] = 3
            report["dataset_sha256"] = "e" * 64
            mismatched_bytes = json.dumps(report).encode("utf-8")
            (root / "report.json").write_bytes(mismatched_bytes)
            row["validation_report_sha256"] = hashlib.sha256(mismatched_bytes).hexdigest()
            self.assertFalse(assess({"source_sha": SHA, "capabilities": [row]}, SHA, root)["passed"])
            row["validation_report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
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
