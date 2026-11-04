"""AOI × IBGE phytophysiognomy intersections.

Converted from bare pytest functions to unittest.TestCase: the CI runs
``python -m unittest discover``, which silently collected ZERO tests from the
previous module, hiding two real failures (area shares not adding to 100 % and
the missing ``raster_total`` field). Fixtures are synthetic geometry, never
observations.
"""
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from fitofisionomia_intersections import (ibge_class_intersections,
                                          resolve_physiognomy_class,
                                          zonal_raster_by_ibge_class)


def _layers():
    aoi = gpd.GeoDataFrame({"id": [1]}, geometry=[box(0, 0, 2, 1)], crs="EPSG:4326")
    ibge = gpd.GeoDataFrame({"legenda": ["Floresta", "Savana"]},
                            geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)], crs="EPSG:4326")
    return aoi, ibge


class IbgeIntersectionTests(unittest.TestCase):
    def test_intersection_separates_ibge_classes_and_audits_area(self):
        aoi, ibge = _layers()
        result = ibge_class_intersections(aoi, ibge, "legenda")
        self.assertEqual({x["physiognomy"] for x in result["classes"]}, {"Floresta", "Savana"})
        self.assertLess(abs(sum(x["area_share_pct"] for x in result["classes"]) - 100.0), 1e-5)
        self.assertLess(result["area_unclassified_pct"], 1e-5)

    def test_long_geographic_edges_do_not_create_unclassified_sliver(self):
        # Regression: without densification a 2°×1° AOI reported 0.0052 %
        # "unclassified" although the IBGE layer covers it entirely.
        aoi = gpd.GeoDataFrame(geometry=[box(-55, -5, -50, -2)], crs="EPSG:4326")
        ibge = gpd.GeoDataFrame({"legenda": ["A", "B", "C"]},
                                geometry=[box(-55, -5, -53, -2), box(-53, -5, -51.5, -2),
                                          box(-51.5, -5, -50, -2)], crs="EPSG:4326")
        result = ibge_class_intersections(aoi, ibge, "legenda")
        total = sum(x["area_ha"] for x in result["classes"])
        self.assertLess(abs(total - result["area_aoi_ha"]) / result["area_aoi_ha"], 1e-7)

    def test_layer_far_from_aoi_is_rejected_not_reported_as_zero(self):
        aoi, _ = _layers()
        far = gpd.GeoDataFrame({"legenda": ["X"]}, geometry=[box(10, 10, 11, 11)], crs="EPSG:4326")
        with self.assertRaisesRegex(ValueError, "não intersecta"):
            ibge_class_intersections(aoi, far, "legenda")

    def test_zonal_stats_are_computed_inside_each_ibge_intersection(self):
        aoi, ibge = _layers()
        with tempfile.TemporaryDirectory() as tmp:
            raster = Path(tmp) / "agb.tif"
            with rasterio.open(raster, "w", driver="GTiff", height=1, width=2, count=1,
                               dtype="float32", crs="EPSG:4326",
                               transform=from_origin(0, 1, 1, 1), nodata=-9999) as dst:
                dst.write(np.array([[10, 20]], dtype="float32"), 1)
            result = zonal_raster_by_ibge_class(aoi, ibge, "legenda", raster)
        got = {x["physiognomy"]: x for x in result["classes"]}
        self.assertEqual(got["Floresta"]["mean"], 10.0)
        self.assertEqual(got["Savana"]["mean"], 20.0)
        self.assertAlmostEqual(got["Floresta"]["raster_total"],
                               10.0 * got["Floresta"]["area_ha"], places=6)
        self.assertGreater(got["Floresta"]["raster_total"], 0)
        self.assertEqual(got["Savana"]["n"], 1)
        self.assertIn("por hectare", got["Savana"]["raster_total_definition"])


class PhysiognomyResolutionTests(unittest.TestCase):
    def test_low_confidence_uses_ibge_reference_instead_of_indeterminate(self):
        result = resolve_physiognomy_class("Floresta ombrófila", 0.61, "Floresta ombrófila densa", 0.80)
        self.assertEqual(result["physiognomy"], "Floresta ombrófila densa")
        self.assertEqual(result["method"], "IBGE")
        self.assertIs(result["ibge_fallback"], True)

    def test_high_confidence_keeps_algorithm_class(self):
        result = resolve_physiognomy_class("Savana", 0.91, "Floresta", 0.80)
        self.assertEqual(result["physiognomy"], "Savana")
        self.assertEqual(result["method"], "algorithm")
        self.assertIs(result["ibge_fallback"], False)

    def test_low_confidence_without_ibge_reference_raises_coverage_error(self):
        with self.assertRaisesRegex(ValueError, "sem classe IBGE"):
            resolve_physiognomy_class("Savana", 0.4, None, 0.8)


if __name__ == "__main__":
    unittest.main()
