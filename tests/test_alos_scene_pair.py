import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
import sar_pipeline

class _GDF:
    total_bounds=(-48,-16,-47.99,-15.99)
    def to_crs(self,*args):return self
    class _Geometry:
        def union_all(self):return SimpleNamespace(__geo_interface__={"type":"Polygon","coordinates":[[[-48,-16],[-47.99,-16],[-47.99,-15.99],[-48,-16]]]})
    geometry=_Geometry()

class _Resp:
    def __init__(self,body):self.body=body
    def raise_for_status(self):pass
    def json(self):return self.body

class _Dataset:
    crs="EPSG:4326"
    def __enter__(self):return self
    def __exit__(self,*args):pass

class _Env:
    def __enter__(self):return self
    def __exit__(self,*args):pass

class ALOSScenePairTests(unittest.TestCase):
    def test_same_scene_dual_pol_required(self):
        scenes=[{"id":"scene1","assets":{"HH":{"href":"https://example.test/HH1"}}},
                {"id":"scene2","assets":{"HV":{"href":"https://example.test/HV2"}}},
                {"id":"scene3","assets":{"hh":{"href":"https://example.test/HH3"},"hv":{"href":"https://example.test/HV3"}}}]
        def post(*args,**kwargs):return _Resp({"features":scenes})
        def get(*args,**kwargs):return _Resp({"href":kwargs["params"]["href"]})
        with patch.object(sar_pipeline.requests,"post",side_effect=post),patch.object(sar_pipeline.requests,"get",side_effect=get),patch("rasterio.Env",return_value=_Env()),patch("rasterio.open",return_value=_Dataset()),patch("rasterio.mask.mask",return_value=(np.ma.array([[[100.,120.]]]),None)),patch("rasterio.warp.transform_geom",return_value={"type":"Polygon","coordinates":[]}):
            result=sar_pipeline.planetary_alos_palsar(_GDF(),"unused")
        self.assertEqual({x["scene"] for x in result["stats"]},{"scene3"})
        self.assertEqual({x["polarization"] for x in result["stats"]},{"HH","HV"})
        self.assertEqual(result["missing_polarizations"],[])

    def test_gtdx_rh98_cannot_enter_h100_inventory_model(self):
        result=sar_pipeline.tapajos_h100_structure_agb(
            None,{"height_mean_m":25.0,"height_definition_compatible_with_H100":False,
                  "sensor":"TanDEM-X InSAR + GEDI"},"Amazônia","Floresta Ombrófila Densa")
        self.assertEqual(result["status"],"SAR_HEIGHT_STRUCTURE_BLOCKED")
        self.assertIsNone(result["agb_mg_ha"])

    def test_no_cross_scene_pair_when_only_single_polarizations_exist(self):
        scenes=[{"id":"scene1","assets":{"HH":{"href":"https://example.test/HH1"}}},
                {"id":"scene2","assets":{"HV":{"href":"https://example.test/HV2"}}}]
        def post(*args,**kwargs):return _Resp({"features":scenes})
        def get(*args,**kwargs):return _Resp({"href":kwargs["params"]["href"]})
        with patch.object(sar_pipeline.requests,"post",side_effect=post),patch.object(sar_pipeline.requests,"get",side_effect=get),patch("rasterio.Env",return_value=_Env()),patch("rasterio.open",return_value=_Dataset()),patch("rasterio.mask.mask",return_value=(np.ma.array([[[100.,120.]]]),None)),patch("rasterio.warp.transform_geom",return_value={"type":"Polygon","coordinates":[]}):
            result=sar_pipeline.planetary_alos_palsar(_GDF(),"unused")
        self.assertEqual(len(result["stats"]),1)
        self.assertEqual(len(result["missing_polarizations"]),1)
        self.assertEqual(len({x["scene"] for x in result["stats"]}),1)

if __name__=="__main__":unittest.main()
