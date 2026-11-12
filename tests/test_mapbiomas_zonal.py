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

    def test_unsupported_vsi_downloads_validated_local_geotiff(self):
        """A Windows GDAL without /vsicurl must reach the same AOI pixel read."""
        import io
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import rasterio
        import geopandas as gpd
        from rasterio.errors import RasterioIOError
        from rasterio.transform import from_origin
        from shapely.geometry import box
        import mapbiomas_zonal as mz

        class Response(io.BytesIO):
            def __init__(self, payload):
                super().__init__(payload)
                self.headers = {"Content-Type":"image/tiff", "Content-Length":str(len(payload))}
            def __enter__(self): return self
            def __exit__(self, *args): self.close()

        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/"official.tif"
            cached=root/"cache"/"official.tif"
            with rasterio.open(source,"w",driver="GTiff",height=2,width=2,count=1,
                               dtype="uint8",crs=4326,transform=from_origin(-50,-10,.001,.001),nodata=0) as dst:
                dst.write(np.array([[3,4],[3,4]],dtype="uint8"),1)
            payload=source.read_bytes()
            original=rasterio.open
            def fail_remote(value,*args,**kwargs):
                if str(value).startswith("/vsicurl/"):
                    raise RasterioIOError("not recognized as a supported dataset name")
                return original(value,*args,**kwargs)
            aoi=gpd.GeoDataFrame(geometry=[box(-50,-10.002,-49.998,-10)],crs=4326)
            with patch.object(mz,"_mapbiomas_cache_path",return_value=cached), \
                 patch("rasterio.open",side_effect=fail_remote), \
                 patch("urllib.request.urlopen",return_value=Response(payload)):
                result=mz.mapbiomas_class_percentages(aoi,raster_url="https://example.test/official.tif")
            self.assertGreater(result["mapped_area_ha"],0)
            self.assertEqual(result["source_url"],"https://example.test/official.tif")
            self.assertTrue(cached.is_file())

    def test_known_collection_11_natural_classes_have_landcover_crosswalk(self):
        for code in (3, 4, 5, 6, 7, 11, 12, 49, 50):
            self.assertIn(code, LEGEND)
            self.assertTrue(LEGEND[code][0])
            self.assertTrue(LEGEND[code][1])


    def test_blocked_aggregation_matches_row_reference(self):
        # A deterministic raster wider and taller than one aggregation block
        # checks masks, NoData, per-row areas, and all observed class codes.
        rng = np.random.default_rng(20261105)
        values = rng.choice([0, 3, 4, 6, 11, 62], size=(193, 127)).astype(np.int16)
        inside = rng.random(values.shape) > 0.23
        row_areas = np.linspace(720.125, 910.875, values.shape[0])
        nodata = 0

        expected = {}
        valid_area = 0.0
        for row in range(values.shape[0]):
            selected = inside[row] & (values[row] != nodata) & (values[row] > 0)
            if not selected.any():
                continue
            codes, counts = np.unique(values[row][selected], return_counts=True)
            for code, count in zip(codes, counts):
                area = int(count) * float(row_areas[row])
                expected[int(code)] = expected.get(int(code), 0.0) + area
                valid_area += area

        actual = summarize_class_grid(values, inside, row_areas, nodata=nodata)
        actual_by_code = {row["class_code"]: row for row in actual["classes"]}
        self.assertEqual(set(actual_by_code), set(expected))
        self.assertAlmostEqual(actual["mapped_area_ha"], valid_area / 10000.0, places=11)
        for code, area_m2 in expected.items():
            self.assertAlmostEqual(actual_by_code[code]["area_ha"], area_m2 / 10000.0, places=11)
            self.assertAlmostEqual(
                actual_by_code[code]["area_pct"],
                100.0 * area_m2 / valid_area,
                places=11,
            )


if __name__ == "__main__":
    unittest.main()
