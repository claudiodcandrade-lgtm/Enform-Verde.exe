"""Integration regression for five-biome IBGE AOI intersection and area reporting.

These tests use synthetic geometry to validate area accounting, not biological
classification nor independent real data validation.
"""
import unittest

import geopandas as gpd
from shapely.geometry import box
from desktop_app import _shares, _shares_with_code

class IbgeEqualAreaTests(unittest.TestCase):
    def setUp(self):
        self.aoi = gpd.GeoDataFrame(
            geometry=[box(-50, -4, -48, -2)], crs="EPSG:4326")
        self.half = gpd.GeoDataFrame(
            {"legenda_1": ["Floresta Ombrófila Densa"], "cd_fito": ["FOD"]},
            geometry=[box(-50, -4, -49, -2)], crs="EPSG:4326")

    def test_unmapped_area_is_not_silently_included(self):
        groups = _shares(self.aoi, self.half, ["legenda_1"])
        self.assertEqual(len(groups), 1)
        rows = {name: (area, pct) for name, area, pct in groups[0][1]}
        self.assertIn("Floresta Ombrófila Densa", rows)
        self.assertIn("Sem cobertura IBGE", rows)
        self.assertAlmostEqual(sum(v[1] for v in rows.values()), 100., places=4)
        self.assertAlmostEqual(rows["Floresta Ombrófila Densa"][1], 50., places=4)

    def test_fito_code_percent_denominator_is_whole_aoi(self):
        rows = _shares_with_code(self.aoi, self.half, "legenda_1", "cd_fito")
        self.assertAlmostEqual(sum(r["percent"] for r in rows), 100., places=4)
        forest = next(r for r in rows if r["code"] == "FOD")
        missing = next(r for r in rows if r["name"] == "Sem cobertura IBGE")
        self.assertAlmostEqual(forest["percent"], 50., places=4)
        self.assertAlmostEqual(missing["percent"], 50., places=4)

    def test_overlapping_classes_fail_closed(self):
        overlapping = gpd.GeoDataFrame(
            {"legenda_1": ["Floresta Ombrófila Densa", "Savana"], "cd_fito": ["FOD", "SAV"]},
            geometry=[box(-50, -4, -49, -2), box(-49.5, -4, -48.5, -2)],
            crs="EPSG:4326")
        with self.assertRaisesRegex(ValueError, "Sobreposição"):
            _shares(self.aoi, overlapping, ["legenda_1"])
        with self.assertRaisesRegex(ValueError, "Sobreposição"):
            _shares_with_code(self.aoi, overlapping, "legenda_1", "cd_fito")

if __name__ == "__main__":
    unittest.main()
