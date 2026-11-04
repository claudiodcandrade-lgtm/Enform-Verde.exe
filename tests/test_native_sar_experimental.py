"""Contract tests for operational experimental Sentinel-1 candidate screening.
Synthetic rasters verify plumbing and bounds, not scientific accuracy.
"""
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from native_sar_experimental import native_structure_index, run_sentinel1_native_screen


class NativeSarExperimentalTests(unittest.TestCase):
    def test_index_is_bounded_and_marks_score_as_uncalibrated(self):
        rng=np.random.default_rng(20)
        vv=-8+rng.normal(0,0.5,(32,32))
        vh=-15+rng.normal(0,1.5,(32,32))
        out=native_structure_index(vv,vh)
        self.assertEqual(out["status"],"SAR_EXPERIMENTAL_INDEX")
        self.assertIsNone(out["probability"])
        self.assertIsNone(out["accuracy"])
        score=out["score"]
        self.assertTrue(np.nanmin(score)>=0)
        self.assertTrue(np.nanmax(score)<=1)
        self.assertIn("granulometria",out["feature_semantics"]["morphological_scale_response_db"])

    def test_missing_pixels_produce_nd(self):
        a=np.full((9,9),-10.0)
        out=native_structure_index(a,a,mask=np.zeros_like(a,dtype=bool))
        self.assertEqual(out["status"],"N/D")
        self.assertIsNone(out["score"])

    def test_actual_geotiff_pair_creates_auditable_screen_outputs(self):
        rng=np.random.default_rng(22)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            transform=from_origin(500000,7600240,10,10)
            profile=dict(driver="GTiff",height=24,width=24,count=1,dtype="float32",
                         crs="EPSG:32621",transform=transform,nodata=-9999)
            vv=root/"S1A_IW_GRDH_1SDV_VV.tif"
            vh=root/"S1A_IW_GRDH_1SDV_VH.tif"
            for path,array in ((vv,-8+rng.normal(0,0.7,(24,24))),
                               (vh,-15+rng.normal(0,1.2,(24,24)))):
                with rasterio.open(path,"w",**profile) as dst:
                    dst.write(array.astype("float32"),1)
                    dst.update_tags(SATELLITE="Sentinel-1")
            aoi=gpd.GeoDataFrame({"id":[1]},geometry=[box(500020,7600020,500220,7600220)],crs="EPSG:32621")
            out=run_sentinel1_native_screen(aoi,[str(vv),str(vh)],root/"out")
            self.assertEqual(out["status"],"SAR_EXPERIMENTAL_CANDIDATE_SCREEN")
            self.assertFalse(out["native_presence_confirmed"])
            self.assertIsNone(out["probability"])
            self.assertLessEqual(out["threshold_sensitivity_area_ha"]["0.85"]["area_ha"],
                                 out["threshold_sensitivity_area_ha"]["0.55"]["area_ha"])
            self.assertTrue(Path(out["score_raster_path"]).is_file())
            self.assertTrue(Path(out["candidate_vector_path"]).is_file())
            self.assertIn("not interval",out["sensitivity_is"])


if __name__=="__main__":
    unittest.main()
