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


class Sentinel1LiveAccessTests(unittest.TestCase):
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
        for scene in scenes[:5]:
            token = get_runtime_sas_token()
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
