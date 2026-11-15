"""Deterministic contracts for alternative radar fallback; no live data claimed."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from radar_contingency import run_alternative_radar_screen

class AlternativeRadarTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 6, tzinfo=timezone.utc)
        self.aoi = object()

    def test_nisar_is_prioritized_and_pixels_never_become_s1_classes(self):
        groups = [
            {"dataset": "ALOS PALSAR", "items": [
                {"id": "alos-new", "download_url": "https://example.invalid/a.tif",
                 "properties": {"startTime": "2026-11-05T00:00:00Z"}}]},
            {"dataset": "NISAR L2 GCOV", "items": [
                {"id": "nisar", "download_url": "https://example.invalid/n.h5",
                 "properties": {"startTime": "2026-11-01T00:00:00Z"}}]},
        ]
        processed = []
        def download(_session, _url, target):
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_bytes(b"pixel fixture")
            return Path(target)
        def process(_aoi, item, local_path, workdir):
            processed.append(item["id"])
            return {"sensor": "NISAR", "band": "L", "features": {"L_HV_dB": -20},
                    "paths": [str(local_path)]}
        with tempfile.TemporaryDirectory() as output:
            r = run_alternative_radar_screen(
                self.aoi, output, now=self.now,
                discover=lambda _aoi: groups,
                session_factory=lambda: (object(), {"available": True, "reason": "test"}),
                downloader=download, pixel_processor=process)
            self.assertEqual(r["status"], "ALTERNATIVE_RADAR_PIXELS_PROCESSED")
            self.assertEqual(processed, ["nisar"])
            self.assertFalse(r["native_confirmed"])
            self.assertFalse(r["crop_confirmed"])
            self.assertEqual(r["classification_status"], "N/D_VALIDACAO")
            self.assertNotIn("vv", r.get("pixel_result", {}).get("features", {}))
            self.assertTrue(Path(r["manifest_path"]).is_file())

    def test_restricted_access_is_not_reported_as_missing_data(self):
        groups = [{"dataset": "NISAR L2 GCOV", "items": [
            {"id": "n", "download_url": "https://example.invalid/n.h5",
             "properties": {"startTime": "2026-11-01T00:00:00Z"}}]}]
        with tempfile.TemporaryDirectory() as output:
            r = run_alternative_radar_screen(
                self.aoi, output, now=self.now, discover=lambda _aoi: groups,
                session_factory=lambda: (None, {"available": False, "reason": "login required"}))
            self.assertEqual(r["status"], "ACESSO_RESTRITO")
            self.assertNotEqual(r["status"], "N/D_DADOS")

    def test_no_candidate_does_not_claim_national_absence(self):
        with tempfile.TemporaryDirectory() as output:
            r = run_alternative_radar_screen(
                self.aoi, output, now=self.now,
                discover=lambda _aoi: [
                    {"dataset": "NISAR L2 GCOV", "items": []},
                    {"dataset": "ALOS PALSAR", "items": []},
                ],
                session_factory=lambda: (None, {"available": False}))
            self.assertEqual(r["status"], "ERRO_TECNICO")
            self.assertFalse(r["global_search_complete"])
            self.assertIn("SAOCOM-1A/1B CONAE", r["routes_not_configured"])

    def test_stale_and_future_acquisitions_are_rejected(self):
        groups = [{"dataset": "NISAR L2 GCOV", "items": [
            {"id": "old", "download_url": "https://example.invalid/old.h5",
             "properties": {"startTime": "2026-09-01T00:00:00Z"}},
            {"id": "future", "download_url": "https://example.invalid/future.h5",
             "properties": {"startTime": "2026-11-07T00:00:00Z"}},
        ]}]
        with tempfile.TemporaryDirectory() as output:
            r = run_alternative_radar_screen(
                self.aoi, output, now=self.now, discover=lambda _aoi: groups,
                session_factory=lambda: (None, {"available": False}))
            self.assertEqual(r["catalog_candidates_recent"], 0)
            self.assertEqual(r["status"], "ERRO_TECNICO")

if __name__ == "__main__":
    unittest.main()
