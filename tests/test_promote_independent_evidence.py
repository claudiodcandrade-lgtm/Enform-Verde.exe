"""Only raw, independently evidenced data may be promoted into a modular manifest."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.promote_independent_evidence import promote

SHA = "a" * 40

class EvidencePromotionTests(unittest.TestCase):
    def test_missing_candidates_do_not_generate_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            audit, manifest = promote(SHA, temp, Path(temp) / "absent")
            self.assertFalse(audit["promoted"])
            self.assertIsNone(manifest)

    def test_verified_candidate_promotes_and_corrupted_data_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = b"genuine independent observations from named inventory"
            (root / "plot.csv").write_bytes(raw)
            report = {"dataset_sha256": hashlib.sha256(raw).hexdigest(),
                      "independent_sample_count": 12, "rmse": 2.0, "mae": 1.5,
                      "bias": 0.3, "interval_coverage": 0.9,
                      "train_partition": "A", "test_partition": "B",
                      "validation_design": "spatial holdout", "unit": "Mg/ha"}
            data = json.dumps(report).encode()
            (root / "report.json").write_bytes(data)
            candidate = {
                "biome": "Amazônia", "pool": "agb",
                "fitofisionomia": "Floresta Ombrófila Densa", "status": "validated",
                "evidence_type": "independent_real_data",
                "dataset_file": "plot.csv",
                "dataset_sha256": report["dataset_sha256"],
                "validation_report": "report.json",
                "validation_report_sha256": hashlib.sha256(data).hexdigest(),
                "source_url": "https://dados.florestal.gov.br/dataset/example",
                "uncertainty_kind": "independently measured prediction interval",
                "domain": "test-only", "transfer_error_method": "spatial holdout"
            }
            candidates = root / "candidates"
            candidates.mkdir()
            (candidates / "candidate.json").write_text(json.dumps(candidate))
            audit, manifest = promote(SHA, root, candidates)
            self.assertTrue(audit["promoted"])
            self.assertEqual(len(manifest["capabilities"]), 1)
            (root / "plot.csv").write_bytes(b"corrupted")
            audit, manifest = promote(SHA, root, candidates)
            self.assertFalse(audit["promoted"])
            self.assertIsNone(manifest)

if __name__ == "__main__":
    unittest.main()
