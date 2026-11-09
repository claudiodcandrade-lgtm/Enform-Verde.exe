"""Live regression guard for current VV/VH COG reads over the Sinop AOI.

This deliberately exercises public catalogue discovery, the documented SAS route,
GDAL/rasterio decoding and actual pixel extraction. It is not a synthetic contract.
"""
import unittest
from datetime import datetime, timedelta, timezone

from sentinel1_mpc import (
    extract_cog_point,
    get_runtime_sas_token,
    search_sentinel1_rtc,
)


def require_live_mpc_token():
    """Skip only when the public signing service is unavailable externally.

    Release acceptance still has a separate required live-pixel gate, so this
    keeps the general regression suite honest without turning an outage into a
    false pass for the Windows artifact.
    """
    try:
        return get_runtime_sas_token()
    except RuntimeError as exc:
        if "SAS token unavailable via collection and storage routes" in str(exc):
            raise unittest.SkipTest("Microsoft Planetary Computer SAS signing service unavailable; required release live-pixel gate remains blocking") from exc
        raise


class Sentinel1LiveAccessTests(unittest.TestCase):
    def test_signing_service_outage_is_explicit_skip(self):
        from unittest.mock import patch
        with patch(__name__ + ".get_runtime_sas_token",
                   side_effect=RuntimeError("MPC Sentinel-1 SAS token unavailable via collection and storage routes (RuntimeError,RuntimeError)")):
            with self.assertRaises(unittest.SkipTest):
                require_live_mpc_token()

    def test_current_mpc_scene_decodes_real_vv_and_vh_pixels(self):
        # Center of the user's attached Sinop AOI (FAZENDA MARIA EDUARDA).
        lon, lat = -55.1887, -11.8717
        ring = [[-55.215, -11.892], [-55.162, -11.892],
                [-55.162, -11.851], [-55.215, -11.851],
                [-55.215, -11.892]]
        aoi = {"type": "Polygon", "coordinates": [ring]}
        now = datetime.now(timezone.utc)
        found = search_sentinel1_rtc(aoi, start_utc=now-timedelta(days=45), end_utc=now,
                                     page_limit=30, max_pages=5)
        scenes = [s for s in found["scenes"] if {"vv", "vh"} <= set(s.get("assets") or {})]
        self.assertTrue(scenes, "MPC found no recent VV/VH Sentinel-1 scenes over the AOI")

        failures = []
        token = require_live_mpc_token()
        for scene in scenes[:5]:
            try:
                vv = extract_cog_point(scene["assets"]["vv"]["href"], lon=lon, lat=lat,
                                       polarization="vv", token=token, window_size=3)
                vh = extract_cog_point(scene["assets"]["vh"]["href"], lon=lon, lat=lat,
                                       polarization="vh", token=token, window_size=3)
                self.assertGreater(vv["valid_pixels"], 0)
                self.assertGreater(vh["valid_pixels"], 0)
                self.assertTrue(vv["median_native"] > 0)
                self.assertTrue(vh["median_native"] > 0)
                self.assertEqual(vv["status"], "pixels_read")
                self.assertEqual(vh["status"], "pixels_read")
                return
            except Exception as exc:
                failures.append((scene.get("id"), type(exc).__name__))
        self.fail("Catalog scenes existed but no VV/VH pair decoded after retries: "+repr(failures))


if __name__ == "__main__":
    unittest.main()
