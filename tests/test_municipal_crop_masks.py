"""Sinop-scale crop mask regression. Synthetic polygons only; no remote claim."""
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import geopandas as gpd
from shapely.geometry import box

from crop_monitoring_forecast import crops_in_land_result, monitoring_forecast
from crop_spatial_monitoring import crop_geometry, sample_crop_patches, sampled_sentinel_vigor


class MunicipalCropMaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=str(Path(self.tmp.name)/"uso_solo_intersecao.geojson")
        # 4x4 km mapped soy, separate native woodland and other use.
        g=gpd.GeoDataFrame({
            "class_name":["Lavoura de soja","Formação Florestal","Infraestrutura Urbana"],
            "source":["MAPBIOMAS","MAPBIOMAS","MAPBIOMAS"],
            "geometry":[box(500000, 1000000, 504000, 1004000),
                        box(504000, 1000000, 508000, 1004000),
                        box(500000, 1004000, 508000, 1005000)]},crs=6933)
        g.to_crs(4326).to_file(self.path,driver="GeoJSON")
        self.full=gpd.GeoDataFrame(geometry=[box(500000,1000000,508000,1005000)],crs=6933).to_crs(4326)
        self.land={"vector_path":self.path,"classes":[
            {"class_name":"Lavoura de soja","source":"MAPBIOMAS","area_ha":1600},
            {"class_name":"Formação Florestal","source":"MAPBIOMAS","area_ha":1600}]}

    def test_crop_geometry_contains_no_native_polygon(self):
        c=crop_geometry(self.land,"Soja",canonical_fn=lambda x: {"soja":"Soja"}.get(x.casefold(),x))
        self.assertIsNotNone(c)
        self.assertAlmostEqual(c.to_crs(6933).geometry.area.sum()/10000,1600,places=2)
        patches=sample_crop_patches(c)
        self.assertGreater(len(patches),0)
        native=box(504000,1000000,508000,1004000)
        for p in patches:
            self.assertLess(p.to_crs(6933).geometry.iloc[0].intersection(native).area,1.)

    def test_sample_based_vigor_with_audit(self):
        c=crop_geometry(self.land,"Soja",canonical_fn=lambda x: {"soja":"Soja"}.get(x.casefold(),x))
        seen=[]
        def fake(patch,day,code):
            seen.append((patch.to_crs(6933).geometry.area.sum()/10000,code))
            return {"status":"experimental","class":"vigor adequado",
                    "probabilities":{"baixo vigor":.1,"vigor adequado":.8,"alto vigor":.1}}
        v=sampled_sentinel_vigor(c,date(2026,11,4),39,fake)
        self.assertEqual(v["status"],"experimental")
        self.assertTrue(seen)
        self.assertTrue(all(ha < 100 for ha,_ in seen))
        self.assertEqual(v["patches_valid"],len(seen))
        self.assertIn("NÃO calibradas",v["uncertainty_warning"])

    def test_missing_crop_vector_does_not_treat_municipality_as_field(self):
        self.assertIsNone(crop_geometry({"vector_path":"missing.geojson"},"Soja",
                                       canonical_fn=lambda x:x))
        self.assertEqual(crops_in_land_result(self.land),{"Soja":1600.0})


if __name__=="__main__":
    unittest.main()
