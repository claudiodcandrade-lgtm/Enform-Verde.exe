"""Synthetic regression fixtures: NOT orbital or accuracy validation."""
import unittest
import numpy as np
from recent_sar_landcover import classify_temporal,run_recent_sar_screen,candidate_class_name
class CurrentRadarScreenTests(unittest.TestCase):
    def test_class_two_is_a_cultivated_candidate_not_a_named_crop(self):
        label=candidate_class_name(2)
        self.assertEqual(label,"Área cultivada — candidato SAR experimental; cultura N/D")
        self.assertNotIn("soja",label.casefold())
        self.assertNotIn("vegetação nativa",label.casefold())

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
        self.assertEqual(r["status"],"N/D_DADOS")
        self.assertFalse(r["native_confirmed"]);self.assertFalse(r["crop_confirmed"])
    def test_missing_observations_are_not_valid_land_cover(self):
        a=np.ones((1,12,12))
        with self.assertRaises(ValueError):classify_temporal(a,a,np.ones((12,12),bool))

    def test_ineligible_candidates_are_not_reported_as_pixel_read_failure(self):
        import geopandas as gpd
        from shapely.geometry import box
        from datetime import datetime,timezone,timedelta
        ref=datetime(2026,11,9,tzinfo=timezone.utc)
        scenes=[]
        for i,days_ago in enumerate((2,12,22)):
            scenes.append({"id":f"candidate-{i}","provider":"MPC",
                "acquisition_utc":(ref-timedelta(days=days_ago)).isoformat(),
                "orbit_state":"ascending","relative_orbit":42,
                "assets":{"vv":{"href":"https://invalid/vv.tif"},
                          "vh":{"href":"https://invalid/vh.tif"}}})
        a=gpd.GeoDataFrame(geometry=[box(-55.8,-12.6,-55.7,-12.5)],crs=4326)
        r=run_recent_sar_screen(a,"unused",now=ref,
            search=lambda *a,**k:{"scenes":scenes,"scene_count":len(scenes),
                                  "pagination_complete":True,"providers":[]})
        self.assertEqual(r["status"],"N/D_DADOS")
        self.assertEqual(r["reason"],"NO_ELIGIBLE_TEMPORAL_SERIES")
        self.assertEqual(r["selected_scene_count"],0)
        self.assertEqual(r["pixel_read_attempt_count"],0)
        diag=r["provider_processing_diagnostics"][0]
        self.assertEqual(diag["candidate_scene_count"],3)
        self.assertFalse(diag["eligible_series_found"])
        self.assertEqual(diag["readable_scene_count"],0)
if __name__=="__main__":unittest.main()
