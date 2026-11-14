"""Pre-field crop SAR contract: experimental annual masks are usable for
conditional scenarios, but never misrepresented as current verified fields.
"""
import tempfile
from pathlib import Path
import unittest
import geopandas as gpd
from shapely.geometry import box
from crop_monitoring_forecast import (crops_in_land_result,experimental_crops_in_land_result,
                                     canonical_crop,_append_candidate_vigor_lines)
from crop_spatial_monitoring import crop_geometry,current_sar_cultivated_candidate_geometry


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
            self.assertFalse(crops_in_land_result(land))
            crops=experimental_crops_in_land_result(land)
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

    def test_current_vigor_mask_uses_only_recent_sar_cultivated_candidates(self):
        frame=gpd.GeoDataFrame({
            "class_code":[1,2,3,2],
            "source":["SAR_CURRENT_EXPERIMENTAL"]*3+["SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(0,0,.01,.01),box(1,1,1.02,1.02),box(2,2,2.01,2.01),
                      box(3,3,3.02,3.02)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"recent.geojson"
            frame.to_file(path,driver="GeoJSON")
            land={"recent_sar_cover":{"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES",
                                       "vector_path":str(path)}}
            result=current_sar_cultivated_candidate_geometry(land)
            self.assertIsNotNone(result)
            self.assertEqual(len(result),1)
            self.assertAlmostEqual(result.geometry.iloc[0].area,frame.geometry.iloc[1].area)
            self.assertIsNone(current_sar_cultivated_candidate_geometry(
                {"recent_sar_cover":{"status":"N/D","vector_path":str(path)}}))

    def test_candidate_vigor_panel_is_always_explicitly_conditional(self):
        lines=[]
        _append_candidate_vigor_lines(lines,{"status":"experimental","class":"vigor adequado",
            "probabilities":{"baixo vigor":.2,"vigor adequado":.6,"alto vigor":.2},
            "acquisition_period_utc":["2026-11-01T00:00:00Z","2026-11-12T00:00:00Z"]})
        rendered="\n".join(lines)
        self.assertIn("CONDICIONAL/EXPERIMENTAL",rendered)
        self.assertIn("cultura não identificada",rendered)
        self.assertIn("não confirma cultivo atual",rendered)
        self.assertIn("janela máxima 30 dias",rendered)


if __name__=="__main__":
    unittest.main()
