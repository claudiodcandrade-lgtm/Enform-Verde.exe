"""Regression checks: a green build must not auto-homologate scientific outputs."""
import unittest
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

if __name__ == "__main__":
    unittest.main()
