"""Synthetic regression for Sentinel-1 grid rollback after a failed VV/VH scene.

This test verifies software behavior; it is not ground truth or SAR accuracy.
"""
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from recent_sar_landcover import run_recent_sar_screen


class Sentinel1GridRecoveryTests(unittest.TestCase):
    def test_failed_scene_does_not_poison_output_grid(self):
        ref = datetime(2026, 11, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            aoi = gpd.GeoDataFrame(geometry=[
                box(-55.20, -11.88, -55.19, -11.87)], crs="EPSG:4326")

            def write(name, resolution, values):
                n = int(round(0.015 / resolution))
                file = root / name
                with rasterio.open(file, "w", driver="GTiff", height=n, width=n,
                                    count=1, dtype="float32", crs="EPSG:4326",
                                    transform=from_origin(-55.202, -11.867, resolution, resolution),
                                    nodata=-9999) as target:
                    target.write(values(n).astype("float32"), 1)
                return str(file)

            # This first high-resolution VV asset can initialize a 100+ pixel
            # grid before its paired VH asset fails. It must be discarded.
            failed_vv = write("failed_vv.tif", 0.0001,
                              lambda n: np.full((n, n), .12))
            yy, xx = np.mgrid[0:60, 0:60]
            scenes = []
            for i, ago in enumerate((2, 13, 43, 74)):
                if i == 0:
                    assets = {"vv": {"href": failed_vv},
                              "vh": {"href": str(root / "missing_vh.tif")}}
                else:
                    vv = write(f"valid_{i}_vv.tif", 0.00025,
                               lambda n, i=i: .07 + .004*i +
                               .04*np.indices((n, n))[1]/n)
                    vh = write(f"valid_{i}_vh.tif", 0.00025,
                               lambda n, i=i: .018 + .005*i +
                               .015*np.indices((n, n))[0]/n)
                    assets = {"vv": {"href": vv}, "vh": {"href": vh}}
                scenes.append({
                    "id": f"scene-{i}", "provider": "MPC",
                    "acquisition_utc": (ref - timedelta(days=ago)).isoformat(),
                    "orbit_state": "ascending", "relative_orbit": 50,
                    "assets": assets
                })
            search = lambda *args, **kwargs: {
                "scenes": scenes, "pagination_complete": True,
                "providers": [], "scene_count": len(scenes)}
            with patch("sentinel1_mpc._signed_href", side_effect=lambda href, token: href):
                response = run_recent_sar_screen(
                    aoi, str(root / "out"), now=ref, search=search,
                    token_fn=lambda: "dummy-test-token")
            # Two independent contracts: reader successfully recovered the 3
            # subsequent scenes, and the scientific classifier may abstain when
            # these synthetic inputs do not separate candidate signatures.
            self.assertEqual(response["readable_scene_count"], 3, str(response))
            self.assertGreaterEqual(response["provider_processing_diagnostics"][0]
                                    ["failed_scene_count"], 1)
            self.assertEqual(response["source_scene_count"], 3)
            height, width = response["committed_grid_shape"]
            self.assertLess(width, 65)
            self.assertLess(height, 65)
            self.assertGreater(width, 20)
            self.assertGreater(height, 20)
            self.assertEqual(response["committed_grid_crs"], "EPSG:4326")
            if response["status"] == "ERRO_TECNICO":
                self.assertIn("does not spatially/temporally separate", response["reason"])
                self.assertFalse(response["native_confirmed"])
                self.assertFalse(response["crop_confirmed"])
            else:
                self.assertEqual(response["status"], "SAR_REAL_EXPERIMENTAL_CANDIDATES",
                                 str(response))
                with rasterio.open(response["raster_path"]) as src:
                    self.assertEqual((src.height, src.width), (height, width))


if __name__ == "__main__":
    unittest.main()
