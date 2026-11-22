import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from crop_monitoring_forecast import _cached_recent_vigor_search


class LocalVigorSceneCacheTests(unittest.TestCase):
    def test_reuses_newest_existing_vv_vh_scene_within_thirty_days(self):
        with tempfile.TemporaryDirectory() as td:
            vv=Path(td)/"vv.tif"; vh=Path(td)/"vh.tif"
            vv.write_bytes(b"vv"); vh.write_bytes(b"vh")
            now=datetime.now(timezone.utc)
            scene={"id":"S1_LOCAL","acquisition_utc":(now-timedelta(days=2)).isoformat(),
                "assets":{"vv":{"href":str(vv)},"vh":{"href":str(vh)}}}
            land={"recent_sar_cover":{"vigor_scene_assets":[scene]}}
            result=_cached_recent_vigor_search(land,date.today())
        self.assertTrue(result["reused_from_recent_sar_screen"])
        self.assertEqual(result["scenes"][0]["provider"],"LOCAL_CACHE")
        self.assertEqual(result["scenes"][0]["id"],"S1_LOCAL")

    def test_rejects_stale_or_missing_local_assets(self):
        with tempfile.TemporaryDirectory() as td:
            vv=Path(td)/"vv.tif"; vv.write_bytes(b"vv")
            stale={"id":"STALE","acquisition_utc":
                (datetime.now(timezone.utc)-timedelta(days=31)).isoformat(),
                "assets":{"vv":{"href":str(vv)},"vh":{"href":str(vv)}}}
            missing={"id":"MISSING","acquisition_utc":datetime.now(timezone.utc).isoformat(),
                "assets":{"vv":{"href":str(vv)},"vh":{"href":str(Path(td)/"missing.tif")}}}
            result=_cached_recent_vigor_search(
                {"recent_sar_cover":{"vigor_scene_assets":[stale,missing]}},date.today())
        self.assertIsNone(result)


if __name__=="__main__":
    unittest.main()
