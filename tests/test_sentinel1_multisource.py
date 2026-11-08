import io
import json
import unittest
from datetime import datetime, timezone
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
    def test_provider_error_does_not_erase_inpe_scenes(self):
        scene={"id":"INPE1","provider":"INPE","acquisition_utc":"2026-10-20T10:00:00+00:00",
               "assets":{"vv":{"href":"https://data.inpe.br/vv.tif"},
                         "vh":{"href":"https://data.inpe.br/vh.tif"}}}
        with patch.object(sentinel1_sources,"search_sentinel1_rtc",side_effect=RuntimeError("MPC down")), \
             patch.object(sentinel1_sources,"search_sentinel1_inpe_rtc",
                          return_value={"pagination_complete":True,"scenes":[scene]}):
            result=sentinel1_sources.search_sentinel1_sources(
                {"type":"Polygon","coordinates":[[[-56,-12],[-55,-12],[-55,-11],[-56,-11],[-56,-12]]]},
                start_utc=datetime(2026,10,1,tzinfo=timezone.utc),
                end_utc=datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(result["scene_count"],1)
        self.assertEqual(result["scenes"][0]["provider"],"INPE")
        self.assertFalse(result["pagination_complete"])
        self.assertNotIn("assets",result["providers"][1])


if __name__=="__main__":
    unittest.main()
