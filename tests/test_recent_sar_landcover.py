"""Synthetic regression fixtures: NOT orbital or accuracy validation."""
import unittest
import numpy as np
from recent_sar_landcover import classify_temporal,run_recent_sar_screen
class CurrentRadarScreenTests(unittest.TestCase):
    def test_candidates_and_uncertainty(self):
        r=np.random.default_rng(2026)
        vv=np.clip(r.normal(.13,.02,(4,12,12)),.0001,None)
        vh=np.clip(r.normal(.04,.014,(4,12,12)),.0001,None)
        classes,qa=classify_temporal(vv,vh,np.ones((12,12),bool))
        self.assertIn(1,classes);self.assertIn(2,classes)
        self.assertEqual(qa["valid_pixels"],144)
        self.assertIn("no IC95%",qa["uncertainty"])
    def test_no_scenes_no_classification(self):
        import geopandas as gpd
        from shapely.geometry import box
        a=gpd.GeoDataFrame(geometry=[box(-55.8,-12.6,-55.7,-12.5)],crs=4326)
        r=run_recent_sar_screen(a,"unused",search=lambda *a,**k:{"scenes":[]})
        self.assertEqual(r["status"],"N/D")
        self.assertFalse(r["native_confirmed"]);self.assertFalse(r["crop_confirmed"])
    def test_missing_observations_are_not_valid_land_cover(self):
        a=np.ones((1,12,12))
        with self.assertRaises(ValueError):classify_temporal(a,a,np.ones((12,12),bool))
if __name__=="__main__":unittest.main()
