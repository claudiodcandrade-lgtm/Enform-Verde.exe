import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import sentinel1_inpe
import sentinel1_sources


class _Response:
    def __init__(self, value):
        self.buffer=io.BytesIO(json.dumps(value).encode())
    def __enter__(self): return self
    def __exit__(self,*args): self.buffer.close()
    def read(self,*args): return self.buffer.read(*args)


class InpeRtcTests(unittest.TestCase):
    def test_catalog_retries_transient_transport_failure(self):
        from urllib.error import URLError
        item={"type":"Feature","id":"S1_RETRY",
              "properties":{"datetime":"2026-10-20T10:00:00Z"},
              "assets":{"vv":{"href":"https://data.inpe.br/vv.tif","title":"VV"},
                        "vh":{"href":"https://data.inpe.br/vh.tif","title":"VH"}},
              "links":[]}
        def opener(req,timeout=45):
            if opener.calls==0:
                opener.calls+=1
                raise URLError("temporary connection reset")
            opener.calls+=1
            return _Response({"features":[item],"links":[]})
        opener.calls=0
        with patch("sentinel1_inpe.time.sleep") as delay:
            result=sentinel1_inpe.search_sentinel1_inpe_rtc(
                {"type":"Polygon","coordinates":[[[-56,-12],[-55,-12],[-55,-11],[-56,-11],[-56,-12]]]},
                start_utc=datetime(2026,10,1,tzinfo=timezone.utc),
                end_utc=datetime(2026,11,1,tzinfo=timezone.utc),opener=opener)
        self.assertEqual(opener.calls,2)
        delay.assert_called_once_with(1)
        self.assertEqual(result["scene_count"],1)

    def test_normalizes_gamma0_vv_vh_and_requires_complete_polarization(self):
        item={
            "type":"Feature","id":"S1_TEST",
            "properties":{"datetime":"2026-10-20T10:00:00Z","sat:orbit_state":"ascending","sat:relative_orbit":42},
            "assets":{
                "gamma0_vv":{"href":"https://data.inpe.br/eodata/vv.tif","title":"Gamma0 VV"},
                "gamma0_vh":{"href":"https://data.inpe.br/eodata/vh.tif","title":"Gamma0 VH"},
                "layover_shadow_mask":{"href":"https://data.inpe.br/eodata/mask.tif","title":"Layover and Shadow Mask"}},
            "links":[]}
        def opener(req,timeout=45):
            return _Response({"features":[item],"links":[]})
        result=sentinel1_inpe.search_sentinel1_inpe_rtc(
            {"type":"Polygon","coordinates":[[[-56,-12],[-55,-12],[-55,-11],[-56,-11],[-56,-12]]]},
            start_utc=datetime(2026,10,1,tzinfo=timezone.utc),
            end_utc=datetime(2026,11,1,tzinfo=timezone.utc),opener=opener)
        self.assertEqual(result["scene_count"],1)
        scene=result["scenes"][0]
        self.assertEqual(scene["provider"],"INPE")
        self.assertEqual(set(scene["assets"]),{"vv","vh"})
        self.assertEqual(scene["radiometry"],"gamma0_power")

    def test_rejects_untrusted_asset_hosts(self):
        self.assertIsNone(sentinel1_inpe._asset_for(
            {"vv":{"href":"http://example.invalid/vv.tif","title":"VV"}}, "vv"))


class MultiProviderTests(unittest.TestCase):
    def test_catalog_retries_transient_provider_before_marking_error(self):
        scene={"id":"MPC1","acquisition_utc":"2026-10-20T10:00:00+00:00",
               "assets":{"vv":{"href":"https://example.invalid/vv.tif"},
                         "vh":{"href":"https://example.invalid/vh.tif"}}}
        with patch.object(sentinel1_sources,"search_sentinel1_rtc",
                          side_effect=[RuntimeError("transient"),
                              {"pagination_complete":True,"scenes":[scene]}]) as mpc, \
             patch.object(sentinel1_sources,"search_sentinel1_inpe_rtc",
                          return_value={"pagination_complete":True,"scenes":[]}), \
             patch("sentinel1_sources.time.sleep") as delay:
            result=sentinel1_sources.search_sentinel1_sources(
                {"type":"Polygon","coordinates":[[[-56,-12],[-55,-12],[-55,-11],[-56,-11],[-56,-12]]]},
                start_utc=datetime(2026,10,1,tzinfo=timezone.utc),
                end_utc=datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(mpc.call_count,2)
        self.assertEqual(result["scene_count"],1)
        self.assertEqual(result["providers"][0]["attempts"],2)
        delay.assert_called_once_with(1)

    def test_provider_error_does_not_erase_inpe_scenes(self):
        scene={"id":"INPE1","provider":"INPE","acquisition_utc":"2026-10-20T10:00:00+00:00",
               "assets":{"vv":{"href":"https://data.inpe.br/vv.tif"},
                         "vh":{"href":"https://data.inpe.br/vh.tif"}}}
        with patch.object(sentinel1_sources,"search_sentinel1_rtc",side_effect=RuntimeError("MPC down")), \
             patch.object(sentinel1_sources,"search_sentinel1_inpe_rtc",
                          return_value={"pagination_complete":True,"scenes":[scene]}), \
             patch("sentinel1_sources.time.sleep"):
            result=sentinel1_sources.search_sentinel1_sources(
                {"type":"Polygon","coordinates":[[[-56,-12],[-55,-12],[-55,-11],[-56,-11],[-56,-12]]]},
                start_utc=datetime(2026,10,1,tzinfo=timezone.utc),
                end_utc=datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(result["scene_count"],1)
        self.assertEqual(result["scenes"][0]["provider"],"INPE")
        self.assertFalse(result["pagination_complete"])
        self.assertNotIn("assets",result["providers"][1])

    def test_inpe_rtc_route_requires_real_vv_vh_pixels(self):
        import numpy as np
        import geopandas as gpd
        import rasterio
        from rasterio.transform import from_origin
        from shapely.geometry import box
        from sar_pipeline import inpe_sentinel1_rtc
        with tempfile.TemporaryDirectory() as td:
            raster_path=Path(td)/"rtc.tif"
            with rasterio.open(raster_path,"w",driver="GTiff",width=20,height=20,count=1,
                               dtype="float32",crs="EPSG:4326",
                               transform=from_origin(-55.2,-11.8,0.001,0.001),nodata=-9999) as dst:
                dst.write(np.full((20,20),0.12,dtype="float32"),1)
            item={"id":"S1_INPE_TEST","acquisition_utc":"2026-10-20T10:00:00+00:00",
                  "assets":{"vv":{"href":"https://data.inpe.br/vv.tif"},
                            "vh":{"href":"https://data.inpe.br/vh.tif"}}}
            real_open=rasterio.open
            with patch("sentinel1_inpe.search_sentinel1_inpe_rtc",
                       return_value={"collection":"sentinel-1-rtc-1","scenes":[item],
                                     "pagination_complete":True}), \
                 patch("rasterio.open",side_effect=lambda path,*a,**kw:
                       real_open(raster_path,*a,**kw)):
                aoi=gpd.GeoDataFrame(geometry=[box(-55.195,-11.815,-55.185,-11.805)],crs="EPSG:4326")
                result=inpe_sentinel1_rtc(aoi)
            self.assertEqual(result["pixel_state"],"PROCESSADO")
            self.assertEqual({x["polarization"] for x in result["stats"]},{"VV","VH"})
            self.assertTrue(all(x["n"]>0 for x in result["stats"]))
            self.assertEqual(result["stats"][0]["scene"],"S1_INPE_TEST")
if __name__=="__main__":
    unittest.main()
