"""Sinop-scale crop mask regression. Synthetic polygons only; no remote claim."""
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import geopandas as gpd
from shapely.geometry import box

from crop_monitoring_forecast import crops_in_land_result, monitoring_forecast
from crop_spatial_monitoring import (crop_geometry, sample_crop_patches,
                                     sampled_sentinel_vigor,
                                     current_candidate_vigor_blocks)


class MunicipalCropMaskTests(unittest.TestCase):
    def test_current_sar_candidate_pixels_are_dissolved_into_disjoint_reference_blocks(self):
        from shapely.geometry import box
        mask=gpd.GeoDataFrame(geometry=[box(0,0,4000,4000)],crs=6933)
        design=current_candidate_vigor_blocks(mask)
        self.assertEqual(design["status"],"ok")
        self.assertEqual(len(design["target_blocks"]),6)
        self.assertGreaterEqual(len(design["reference_gdf"]),6)
        for target in design["target_blocks"]:
            for reference in design["reference_gdf"].geometry:
                self.assertFalse(target.geometry.iloc[0].intersects(reference))

    def test_fragmented_crop_mask_retries_smaller_blocks_without_relaxing_purity(self):
        # Eight separated 9-ha fields: a 16-ha window dilutes each field below
        # the 90% purity gate, while an 8-ha interior window is usable.
        from shapely.geometry import box
        cells=[box(i*500,j*500,i*500+300,j*500+300)
               for i in range(4) for j in range(2)]
        mask=gpd.GeoDataFrame(geometry=cells,crs=6933)
        design=current_candidate_vigor_blocks(mask)
        self.assertEqual(design["status"],"ok")
        self.assertEqual(design["block_area_ha"],8.0)
        self.assertGreaterEqual(design["reference_block_count"],6)
        for target in design["target_blocks"]:
            self.assertGreaterEqual(target.to_crs(6933).geometry.area.iloc[0]/10000,2.0)
            self.assertLessEqual(target.to_crs(6933).geometry.area.iloc[0]/10000,8.01)

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
        self.assertIsNone(c, "MapBiomas annual class cannot establish a current field mask")

    def test_sample_based_vigor_with_audit(self):
        # Synthetic SAR_VALIDADO polygon tests the sampler itself; it does not
        # promote the MapBiomas annual mask used by the production fixture.
        sar=self.full.copy()
        sar["class_name"]="Lavoura de soja";sar["source"]="SAR_VALIDADO"
        sar_path=str(Path(self.tmp.name)/"sar.geojson")
        sar.to_file(sar_path,driver="GeoJSON")
        c=crop_geometry({"vector_path":sar_path},"Soja",canonical_fn=lambda x: {"soja":"Soja"}.get(x.casefold(),x))
        self.assertIsNotNone(c)
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
        self.assertEqual(crops_in_land_result(self.land),{})


if __name__=="__main__":
    unittest.main()
