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
            raw = b"synthetic promotion fixture, not independent field observations"
            (root / "plot.csv").write_bytes(raw)
            report = {"dataset_sha256": hashlib.sha256(raw).hexdigest(),
                      "independent_sample_count": 4, "rmse": 2.0, "mae": 1.5,
                      "bias": 0.3, "interval_coverage": 0.9,
                      "train_partition": "A", "test_partition": "B",
                      "validation_design": "spatial holdout", "unit": "Mg/ha",
                      "train_spatial_units": 3, "test_spatial_units": 4,
                      "train_spatial_unit_ids": ["A1", "A2", "A3"],
                      "test_spatial_unit_ids": ["B1", "B2", "B3", "B4"]}
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
            self.assertEqual(manifest["capabilities"][0]["dataset_file"], "plot.csv")
            # One malformed or unlicensed candidate cannot suppress a separate
            # verified biome/pool, nor may it be silently promoted.
            (candidates / "unverified.json").write_text(json.dumps({
                "biome": "Cerrado", "pool": "agb", "status": "validated",
                "dataset_file": "missing.csv", "dataset_sha256": "0" * 64,
            }))
            audit, manifest = promote(SHA, root, candidates)
            self.assertTrue(audit["promoted"])
            self.assertTrue(audit["partial"])
            self.assertEqual(audit["accepted_count"], 1)
            self.assertGreater(audit["rejected_count"], 0)
            self.assertTrue(any("unverified.json" in e for e in audit["errors"]))
            self.assertEqual(len(manifest["capabilities"]), 1)
            self.assertEqual(manifest["capabilities"][0]["biome"], "Amazônia")
            (candidates / "unverified.json").unlink()
            # Promotion must reject a hashed report inflating n from 4
            # independent spatial units to 12 repeated observations.
            inflated = dict(report, independent_sample_count=12)
            inflated_bytes = json.dumps(inflated).encode()
            (root / "report.json").write_bytes(inflated_bytes)
            inflated_candidate = dict(candidate, validation_report_sha256=hashlib.sha256(inflated_bytes).hexdigest())
            (candidates / "candidate.json").write_text(json.dumps(inflated_candidate))
            audit, manifest = promote(SHA, root, candidates)
            self.assertFalse(audit["promoted"])
            self.assertIsNone(manifest)
            (root / "report.json").write_bytes(data)
            (candidates / "candidate.json").write_text(json.dumps(candidate))
            (root / "plot.csv").write_bytes(b"corrupted")
            audit, manifest = promote(SHA, root, candidates)
            self.assertFalse(audit["promoted"])
            self.assertIsNone(manifest)

class ManifestLifecycleTests(unittest.TestCase):
    def test_failed_promotion_deletes_stale_manifest_from_previous_run(self):
        from unittest.mock import patch
        from tools.promote_independent_evidence import main
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "modular_capabilities.json"
            audit = root / "audit.json"
            candidates = root / "candidates"
            candidates.mkdir()
            # Deliberately stale: a prior workflow result is not evidence for
            # the current source SHA or candidate directory.
            manifest.write_text(json.dumps({
                "source_sha": SHA, "capabilities": [{"status": "validated"}]
            }), encoding="utf-8")
            args = ["promote_independent_evidence.py", "--source-sha", SHA,
                    "--root", str(root), "--candidates", str(candidates),
                    "--manifest", str(manifest), "--audit", str(audit)]
            with patch("sys.argv", args):
                self.assertEqual(main(), 1)
            self.assertFalse(manifest.exists())
            result = json.loads(audit.read_text(encoding="utf-8"))
            self.assertFalse(result["promoted"])
            self.assertEqual(result["accepted_count"], 0)

    def test_repeated_failure_is_idempotent(self):
        from unittest.mock import patch
        from tools.promote_independent_evidence import main
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = ["promote_independent_evidence.py", "--source-sha", SHA,
                    "--root", str(root), "--candidates", str(root / "missing"),
                    "--manifest", str(root / "missing_manifest.json"),
                    "--audit", str(root / "audit.json")]
            with patch("sys.argv", args):
                self.assertEqual(main(), 1)
                self.assertEqual(main(), 1)
            self.assertFalse((root / "missing_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
