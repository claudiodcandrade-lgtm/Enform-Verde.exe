"""Pre-field crop SAR contract: experimental annual masks are usable for
conditional scenarios, but never misrepresented as current verified fields.
"""
import tempfile
from pathlib import Path
import unittest
import geopandas as gpd
from shapely.geometry import box
from crop_monitoring_forecast import crops_in_land_result,canonical_crop
from crop_spatial_monitoring import crop_geometry


class ExperimentalCropForecastContracts(unittest.TestCase):
    def test_experimental_sar_soy_polygon_can_be_used_conditionally(self):
        frame=gpd.GeoDataFrame({
            "class_name":["Lavoura de Soja","Formação florestal"],
            "source":["SAR_EXPERIMENTAL_MODELO","SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(-55.2,-11.89,-55.19,-11.88),
                      box(-55.19,-11.89,-55.18,-11.88)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"classes.geojson"
            frame.to_file(path,driver="GeoJSON")
            land={"vector_path":str(path),"classes":[
                {"class_name":"Lavoura de Soja","source":"SAR_EXPERIMENTAL_MODELO",
                 "area_ha":float(frame.iloc[[0]].to_crs(6933).geometry.area.sum()/10000)},
                {"class_name":"Formação florestal","source":"SAR_EXPERIMENTAL_MODELO",
                 "area_ha":float(frame.iloc[[1]].to_crs(6933).geometry.area.sum()/10000)}],
                "validation":{"observed_season":"2025/2026"}}
            crops=crops_in_land_result(land)
            self.assertIn("Soja",crops)
            self.assertNotIn("Formação florestal",crops)
            geoms=crop_geometry(land,"Soja",canonical_fn=canonical_crop)
            self.assertIsNotNone(geoms)
            self.assertEqual(len(geoms),1)
            self.assertGreater(float(geoms.to_crs(6933).geometry.area.sum()),0)

    def test_unverified_cartographic_classes_never_enable_forecast(self):
        land={"classes":[
            {"class_name":"Lavoura de Soja","source":"IBGE_POTENCIAL","area_ha":900},
            {"class_name":"Lavoura de Milho","source":"FALLBACK_CARTOGRAFICO","area_ha":800}]}
        self.assertFalse(crops_in_land_result(land))


if __name__=="__main__":
    unittest.main()
