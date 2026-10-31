"""Regression checks: a green build must not auto-homologate scientific outputs."""
import unittest
import tempfile
import hashlib
import json
from pathlib import Path
from tools.scientific_release_gate import assess

SHA = "a" * 40

class ScientificReleaseGateTests(unittest.TestCase):
    def test_no_real_evidence_fails_closed(self):
        errors = assess({"source_sha": SHA}, SHA)
        self.assertTrue(any("Missing scientific evidence" in e for e in errors))
        self.assertTrue(any("biomes" in e for e in errors))

    def test_wrong_commit_is_a_blocker(self):
        errors = assess({"source_sha": "b" * 40}, SHA)
        self.assertTrue(any("source_sha" in e for e in errors))

    def test_catalog_only_not_independent_validation(self):
        sample = {"source_sha": SHA, "sar": {
            "status": "passed", "evidence_type": "catalog_discovery",
            "source_url": "https://example.org/catalog", "dataset_sha256": "f"*64,
            "observed_at": "2026-10-28", "aoi_id": "Tapajos",
            "validation_report": "log.json", "scene_id": "sample",
            "acquisition_utc": "2026-10-28T12:00Z", "band": "P",
            "method": "unverified", "calibration_split": "A", "test_split": "A",
            "data_access": "catalog_only"}}
        errors = assess(sample, SHA)
        self.assertTrue(any("independent real data required" in e for e in errors))
        self.assertTrue(any("spatially independent" in e for e in errors))
        self.assertTrue(any("catalog discovery alone" in e for e in errors))

    def test_zero_transfer_uncertainty_cannot_pass(self):
        row = {"status": "passed", "evidence_type": "independent_real_data",
               "source_url": "https://example.org/study", "dataset_sha256": "f"*64,
               "observed_at": "2026-10-28", "aoi_id": "aoi",
               "validation_report": "test.json", "biome": "Pantanal",
               "pool": "soil_0_100", "depth_cm": [0, 30],
               "stock_tc_ha": 25, "ci95_lower_tc_ha": 24,
               "ci95_upper_tc_ha": 26,
               "uncertainty_includes_transfer_error": False}
        errors = assess({"source_sha": SHA, "carbon": [row]}, SHA)
        self.assertTrue(any("0-100 cm" in e for e in errors))
        self.assertTrue(any("transfer error" in e for e in errors))

    def test_report_integrity_rejects_missing_and_tampered_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = json.dumps({"dataset_sha256": "a" * 64}).encode("utf-8")
            row = {"status": "passed", "dataset_sha256": "a" * 64,
                   "validation_report": "report.json",
                   "validation_report_sha256": hashlib.sha256(valid).hexdigest()}
            from tools.scientific_release_gate import _verify_local_report
            errors = []
            _verify_local_report(row, "test", errors, root)
            self.assertTrue(any("absent" in e for e in errors))
            (root / "report.json").write_bytes(b"tampered")
            errors = []
            _verify_local_report(row, "test", errors, root)
            self.assertTrue(any("hash mismatch" in e for e in errors))
            (root / "report.json").write_bytes(valid)
            errors = []
            _verify_local_report(row, "test", errors, root)
            self.assertEqual(errors, [])

    def test_release_requires_actual_raw_observations_and_matching_digest(self):
        from tools.scientific_release_gate import _verify_local_dataset
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = b"test-only independent observations"
            digest = hashlib.sha256(raw).hexdigest()
            row = {"status": "passed", "dataset_file": "plots.csv",
                   "dataset_sha256": digest}
            errors = []
            _verify_local_dataset(row, "agb", errors, root)
            self.assertTrue(any("absent" in e for e in errors))
            (root / "plots.csv").write_bytes(b"tampered")
            errors = []
            _verify_local_dataset(row, "agb", errors, root)
            self.assertTrue(any("hash mismatch" in e for e in errors))
            (root / "plots.csv").write_bytes(raw)
            errors = []
            _verify_local_dataset(row, "agb", errors, root)
            self.assertEqual(errors, [])
            errors = []
            _verify_local_dataset(dict(row, dataset_file="../outside.csv"),
                                  "agb", errors, root)
            self.assertTrue(any("escapes" in e for e in errors))

    def test_report_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            from tools.scientific_release_gate import _verify_local_report
            errors = []
            _verify_local_report({"status": "passed", "validation_report": "../outside.json",
                                  "validation_report_sha256": "a" * 64},
                                 "test", errors, Path(tmp))
            self.assertTrue(any("escapes" in e for e in errors))

    def test_accuracy_has_no_arbitrary_minimum_but_must_be_valid(self):
        from tools.scientific_release_gate import assess
        base = {"status": "passed", "evidence_type": "independent_real_data",
                "source_url": "https://example.org", "dataset_sha256": "f" * 64,
                "observed_at": "2026-10-30", "aoi_id": "test",
                "validation_report": "report.json"}
        low = assess({"source_sha": SHA, "agriculture": dict(base, independent_accuracy=0.35)}, SHA)
        self.assertFalse(any("agriculture: independent_accuracy" in e for e in low))
        invalid = assess({"source_sha": SHA, "agriculture": dict(base, independent_accuracy=1.2)}, SHA)
        self.assertTrue(any("independent_accuracy must be a fraction" in e for e in invalid))


    def test_hashed_but_opaque_report_cannot_pass(self):
        from tools.scientific_release_gate import _verify_local_report
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = b"not JSON"
            (root / "report.json").write_bytes(data)
            row = {"status": "passed", "dataset_sha256": "a" * 64,
                   "validation_report": "report.json",
                   "validation_report_sha256": hashlib.sha256(data).hexdigest()}
            errors = []
            _verify_local_report(row, "carbon[0]", errors, root)
            self.assertTrue(any("valid JSON" in e for e in errors))

    def test_report_must_bind_to_dataset_and_independent_spatial_split(self):
        from tools.scientific_release_gate import _verify_local_report
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = {"dataset_sha256": "b" * 64, "independent_sample_count": 12,
                      "train_spatial_units": 4, "test_spatial_units": 3,
                      "train_partition": "A", "test_partition": "B",
                      "validation_design": "blocked holdout",
                      "rmse": 4.2, "mae": 3.0, "bias": -0.1,
                      "interval_coverage": 0.93}
            def audit(payload):
                data = json.dumps(payload).encode("utf-8")
                (root / "report.json").write_bytes(data)
                row = {"status": "passed", "dataset_sha256": "b" * 64,
                       "validation_report": "report.json",
                       "validation_report_sha256": hashlib.sha256(data).hexdigest()}
                errors = []
                _verify_local_report(row, "carbon[0]", errors, root)
                return errors
            self.assertEqual(audit(report), [])
            self.assertTrue(any("dataset hash mismatch" in e
                                for e in audit(dict(report, dataset_sha256="c" * 64))))
            self.assertTrue(any("partitions" in e
                                for e in audit(dict(report, test_partition="A"))))
            self.assertTrue(any("measured interval coverage" in e
                                for e in audit({k: v for k, v in report.items()
                                               if k != "interval_coverage"})))
            self.assertTrue(any("synthetic/catalog" in e
                                for e in audit(dict(report, evidence_type="synthetic"))))
            self.assertTrue(any("independent test spatial units" in e
                                for e in audit(dict(report, test_spatial_units=1))))

if __name__ == "__main__":
    unittest.main()
