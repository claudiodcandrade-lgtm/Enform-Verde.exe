"""Regression contracts: live Sentinel-1 queries must be date-bounded."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
import numpy as np

import geopandas as gpd
from shapely.geometry import box


class _Response:
    def raise_for_status(self):
        return None
    def json(self):
        return {"features": []}


class _SceneResponse(_Response):
    def json(self):
        return {"features":[{"id":"scene-1","properties":{"datetime":"2026-11-12T10:00:00Z"},
            "assets":{"vv":{"href":"https://example.test/vv.tif"},
                      "vh":{"href":"https://example.test/vh.tif"}}}]}


class _Raster:
    crs="EPSG:4326"
    def __enter__(self): return self
    def __exit__(self,*args): return False


class Sentinel1FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(-55.21,-11.89,-55.17,-11.855)],crs="EPSG:4326")

    def _assert_last_30_days(self, body):
        start,end=body["datetime"].split("/")
        start_dt=datetime.fromisoformat(start.replace("Z","+00:00"))
        end_dt=datetime.fromisoformat(end.replace("Z","+00:00"))
        self.assertEqual(end_dt.tzinfo,timezone.utc)
        self.assertLessEqual((end_dt-start_dt).total_seconds(),30*86400+1)
        self.assertGreater((end_dt-start_dt).total_seconds(),29*86400)

    def test_mpc_carbon_route_searches_only_recent_acquisitions(self):
        from sar_pipeline import planetary_sentinel1_cog
        with patch("sar_pipeline.requests.post",return_value=_Response()) as post:
            result=planetary_sentinel1_cog(self.aoi,"unused-current-s1")
        self._assert_last_30_days(post.call_args.kwargs["json"])
        self.assertEqual(post.call_args.kwargs["timeout"],(15,45))
        self.assertFalse(result["stats"])

    def test_mpc_carbon_route_retries_transient_stac_timeout(self):
        import requests
        from sar_pipeline import planetary_sentinel1_cog
        with patch("sar_pipeline.requests.post",
                   side_effect=[requests.exceptions.ReadTimeout("transient"),_Response()]) as post, \
             patch("sar_pipeline.time.sleep"):
            result=planetary_sentinel1_cog(self.aoi,"unused-current-s1")
        self.assertEqual(post.call_count,2)
        self.assertFalse(result["stats"])

    def test_cdse_carbon_catalog_route_searches_only_recent_acquisitions(self):
        from sar_pipeline import public_sentinel1_cog
        with patch("sar_pipeline.requests.post",return_value=_Response()) as post:
            result=public_sentinel1_cog(self.aoi,"unused-current-s1-cdse")
        self._assert_last_30_days(post.call_args.kwargs["json"])
        self.assertEqual(result["items"],0)

    def test_mpc_single_polarization_is_partial_not_processed(self):
        from sar_pipeline import planetary_sentinel1_cog
        from rasterio.mask import mask

        def read_mask(src, geometries, **kwargs):
            if "vh" in current_asset[0]:
                raise TimeoutError("VH asset timed out")
            return np.ma.array([[[2.0,3.0],[4.0,5.0]]]), None

        current_asset=[""]
        def signed(href):
            current_asset[0]=href
            return href

        with patch("sar_pipeline.requests.post",return_value=_SceneResponse()), \
             patch("sar_pipeline._planetary_sign_asset",side_effect=signed), \
             patch("rasterio.open",return_value=_Raster()), \
             patch("rasterio.mask.mask",side_effect=read_mask):
            result=planetary_sentinel1_cog(self.aoi,"unused-current-s1")

        self.assertFalse(result["available"])
        self.assertEqual(result["stats"],[])
        self.assertEqual(result["pixel_state"],"VV_VH_PAIR_INCOMPLETE")
        self.assertEqual(len(result["partial_stats"]),1)
        self.assertIn("VH asset timed out", " ".join(result["errors"]))


if __name__=="__main__":
    unittest.main()
