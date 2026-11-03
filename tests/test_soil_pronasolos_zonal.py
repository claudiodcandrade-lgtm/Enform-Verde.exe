"""Synthetic rasters only. These are numerical regressions, NOT field validation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from soil_pronasolos_zonal import mapped_soil_0_100_on_polygon, verified_local_horizons


class SoilPolygonZonalTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root=Path(self.dir.name)
        self.paths={}
        for i in range(2,7):
            p=self.root/f"soil_{i}.tif"
            with rasterio.open(p,"w",driver="GTiff",height=2,width=2,
                               count=1,dtype="float32",crs="EPSG:6933",
                               transform=from_origin(0,20,10,10),nodata=-9999) as src:
                src.write(np.full((2,2),float(i),dtype="float32"),1)
            self.paths[i]=p

    def gdf(self,geom):
        return gpd.GeoDataFrame(geometry=[geom],crs="EPSG:6933")

    def test_full_polygon_uses_all_five_raw_horizons_and_weighted_intersections(self):
        out=mapped_soil_0_100_on_polygon(self.gdf(box(0,0,20,20)),self.paths)
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"],20)
        self.assertEqual(out["_diagnostic"]["valid_complete_pixels"],4)
        self.assertAlmostEqual(out["_diagnostic"]["coverage_fraction"],1)
        self.assertEqual(out["_diagnostic"]["target_status"],"COMPLETO_POR_INTERSECAO_RASTER")

    def test_partial_pixel_polygon_has_exact_area_weight(self):
        # Half of left-column pixels, all right-column pixels: precisely 300 m².
        geom=box(5,0,20,20)
        with rasterio.open(self.paths[6],"r+") as ds:
            ds.write(np.array([[20,50],[20,50]],dtype="float32"),1)
        out=mapped_soil_0_100_on_polygon(self.gdf(geom),self.paths)
        # Other four horizons total 2+3+4+5=14, last is 20 on left and 50 on right:
        # mean (100*34 + 200*64) / 300 = 54.
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"],54)
        self.assertAlmostEqual(out["_diagnostic"]["intersected_area_ha"],.03)

    def test_thin_polygon_across_pixel_boundary_keeps_both_cells(self):
        # A 2 m-wide strip straddles column boundary; both columns contribute.
        with rasterio.open(self.paths[6],"r+") as ds:
            ds.write(np.array([[20,50],[20,50]],dtype="float32"),1)
        out=mapped_soil_0_100_on_polygon(self.gdf(box(9,0,11,20)),self.paths)
        self.assertAlmostEqual(out["0–100 cm"]["tc_ha"],49)
        self.assertAlmostEqual(out["_diagnostic"]["coverage_fraction"],1)
        self.assertEqual(out["_diagnostic"]["valid_complete_pixels"],4)

    def test_missing_deep_horizon_is_nd_not_extrapolated(self):
        partial={i:p for i,p in self.paths.items() if i!=6}
        self.assertNotIn("0–100 cm",mapped_soil_0_100_on_polygon(self.gdf(box(0,0,20,20)),partial))

    def test_no_data_in_any_one_layer_does_not_fake_100cm(self):
        with rasterio.open(self.paths[6],"r+") as ds:
            ds.write(np.array([[-9999.,-9999.],[-9999.,-9999.]],dtype="float32"),1)
        out=mapped_soil_0_100_on_polygon(self.gdf(box(0,0,20,20)),self.paths)
        self.assertNotIn("0–100 cm",out)
        self.assertEqual(out["_diagnostic"]["target_status"],"INCOMPLETO_NAO_EXTRAPOLAR")

    def test_misaligned_layers_fail_closed(self):
        p=self.paths[6]
        with rasterio.open(p,"r+") as ds:
            ds.transform=from_origin(1,20,10,10)
        out=mapped_soil_0_100_on_polygon(self.gdf(box(0,0,20,20)),self.paths)
        self.assertNotIn("0–100 cm",out)

    def test_verified_local_manifest_accepts_only_all_five_hashed_raw_files(self):
        items={}
        for i,path in self.paths.items():
            items[str(i)]={"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        m={"publisher":"Embrapa Solos/PronaSolos","unit":"Mg C/ha",
           "raw_raster":True,"license_reviewed":True,
           "source_url":"https://example.org/synthetic-fixture",
           "layers":items}
        (self.root/"manifest.json").write_text(json.dumps(m),encoding="utf-8")
        self.assertEqual(set(verified_local_horizons(self.root)),set(self.paths))
        # SHA mismatch invalidates the entire five-layer source, not just one.
        m["layers"]["6"]["sha256"]="a"*64
        (self.root/"manifest.json").write_text(json.dumps(m),encoding="utf-8")
        self.assertIsNone(verified_local_horizons(self.root))


if __name__=="__main__":
    unittest.main()
