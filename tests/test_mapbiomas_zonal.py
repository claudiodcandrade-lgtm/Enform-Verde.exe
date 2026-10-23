import unittest

import numpy as np

from mapbiomas_zonal import LEGEND, summarize_class_grid


class MapBiomasZonalTests(unittest.TestCase):
    def test_area_weighting_and_percentages_are_correct(self):
        values = np.array([[3, 3, 6], [4, 6, 6]])
        inside = np.ones_like(values, dtype=bool)
        result = summarize_class_grid(values, inside, [100.0, 200.0])
        by_code = {row["class_code"]: row for row in result["classes"]}
        # 3: 2*100 m²; 6: 1*100 + 2*200; 4: 1*200.
        self.assertAlmostEqual(by_code[3]["area_ha"], 0.02)
        self.assertAlmostEqual(by_code[6]["area_ha"], 0.05)
        self.assertAlmostEqual(by_code[4]["area_ha"], 0.02)
        self.assertAlmostEqual(sum(x["area_pct"] for x in result["classes"]), 100.0)
        self.assertEqual(by_code[6]["class_name"], "Floresta Alagável")

    def test_mask_and_nodata_do_not_enter_denominator(self):
        values = np.array([[3, 0], [6, 4]])
        inside = np.array([[True, True], [False, True]])
        result = summarize_class_grid(values, inside, [100.0, 100.0], nodata=0)
        self.assertEqual([x["class_code"] for x in result["classes"]], [3, 4])
        self.assertAlmostEqual(sum(x["area_pct"] for x in result["classes"]), 100.0)
        self.assertAlmostEqual(result["mapped_area_ha"], 0.02)

    def test_raster_row_area_is_divided_by_pixel_count(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import rasterio
        import geopandas as gpd
        from rasterio.transform import from_origin
        from shapely.geometry import box
        from pyproj import Geod
        from mapbiomas_zonal import mapbiomas_class_percentages
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"classes.tif"
            with rasterio.open(path,"w",driver="GTiff",height=1,width=2,count=1,dtype="uint8",crs=4326,transform=from_origin(-50,-10,.001,.001),nodata=0) as dst:
                dst.write(np.array([[3,3]],dtype="uint8"),1)
            original=rasterio.open
            def local_open(value,*args,**kwargs):
                return original(str(value).removeprefix("/vsicurl/"),*args,**kwargs)
            aoi=gpd.GeoDataFrame(geometry=[box(-50,-10.001,-49.998,-10)],crs=4326)
            with patch("rasterio.open",side_effect=local_open):
                result=mapbiomas_class_percentages(aoi,raster_url=str(path))
            expected=abs(Geod(ellps="WGS84").geometry_area_perimeter(aoi.geometry.iloc[0])[0])/10000
            self.assertAlmostEqual(result["mapped_area_ha"],expected,places=5)

    def test_known_collection_11_natural_classes_have_landcover_crosswalk(self):
        for code in (3, 4, 5, 6, 7, 11, 12, 49, 50):
            self.assertIn(code, LEGEND)
            self.assertTrue(LEGEND[code][0])
            self.assertTrue(LEGEND[code][1])


if __name__ == "__main__":
    unittest.main()
