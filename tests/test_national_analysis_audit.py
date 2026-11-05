"""Geographic national controls: synthetic coverage metadata is NOT SAR evidence."""
import unittest
from datetime import datetime,timezone
import geopandas as gpd
from shapely.geometry import box
from national_analysis_audit import audit_national_coverage,BIOMES

class NationalCoverageAuditTests(unittest.TestCase):
    positions={"Amazônia":(-60.0,-3.0),"Cerrado":(-47.5,-15.8),
               "Caatinga":(-41.8,-9.0),"Mata Atlântica":(-44.0,-22.0),
               "Pantanal":(-57.0,-17.5),"Pampa":(-54.0,-31.5)}
    def test_nationwide_biomes_area_and_na_are_audited(self):
        self.assertEqual(set(self.positions),set(BIOMES))
        for biome,(lon,lat) in self.positions.items():
            with self.subTest(biome=biome):
                aoi=gpd.GeoDataFrame(geometry=[box(lon,lat,lon+.02,lat+.02)],crs=4326)
                total=float(aoi.to_crs(6933).geometry.union_all().area)/10000
                land={"classes":[{"class_name":"Vegetação nativa cartográfica",
                   "area_ha":total*.3,"native_status":True,"source":"IBGE+MAPBIOMAS"},
                  {"class_name":"Cultivos cartográficos","area_ha":total*.7,
                   "native_status":False,"source":"MAPBIOMAS"}],
                   "recent_sar_cover":{"status":"N/D","reason":"sem pixels acessíveis"}}
                a=audit_national_coverage(aoi,land,biome=biome,
                       at_utc=datetime(2026,11,4,tzinfo=timezone.utc))
                self.assertEqual(a["biome_label"],biome)
                self.assertEqual(a["current_sar_observation"],"N/D")
                self.assertEqual(a["current_sar_classification"],"N/D — SEM_CLASSIFICADOR_ATUAL_VALIDADO")
                self.assertIsNone(a["cartographic_classification_uncertainty_ha"])
                self.assertAlmostEqual(a["coverage_groups_pct"]["nativa_mapeada_ha"],30,places=3)
                self.assertTrue(a["brazil_bbox_plausible"])
                self.assertEqual(len(a["aoi_sha256_wgs84"]),64)
    def test_invalid_crs_and_bad_closure_fail_closed(self):
        frame=gpd.GeoDataFrame(geometry=[box(-60,-3,-59.99,-2.99)],crs=4326)
        with self.assertRaises(ValueError):
            audit_national_coverage(frame,{"classes":[{"area_ha":1,"native_status":True}]})
        with self.assertRaises(ValueError):
            audit_national_coverage(frame.set_crs(None,allow_override=True),{"classes":[]})
    def test_sar_candidates_are_not_verified_crop_or_forest(self):
        frame=gpd.GeoDataFrame(geometry=[box(-47,-16,-46.99,-15.99)],crs=4326)
        total=float(frame.to_crs(6933).geometry.union_all().area)/10000
        land={"classes":[{"class_name":"Soja (mapa 2025)","area_ha":total,
              "native_status":False,"source":"MAPBIOMAS"}],
              "recent_sar_cover":{"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES",
              "scene_ids":["S1A-1"],"areas_ha":{"candidato":total},
              "latest_acquisition_utc":"2026-10-30T12:00:00Z"}}
        result=audit_national_coverage(frame,land)
        self.assertEqual(result["current_sar_observation"],"PIXELS_REAIS")
        self.assertIn("SEM_CLASSIFICADOR",result["current_sar_classification"])
        self.assertIsNone(result["sar_candidate_uncertainty_ha"])
if __name__=="__main__":unittest.main()
