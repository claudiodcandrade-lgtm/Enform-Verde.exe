import unittest

from carbon_compartments import tapajos_litter_stock_component

try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:
    gpd=box=None

class CarbonCompartmentTests(unittest.TestCase):
    @unittest.skipUnless(gpd and box, "geospatial dependencies required")
    def test_tapajos_standing_litter_stock_is_available_and_geofenced(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-54.984,-3.068,-54.982,-3.065)],crs="EPSG:4326")
        r=tapajos_litter_stock_component("Amazônia","Floresta Ombrófila Densa",aoi)
        self.assertIsNotNone(r)
        self.assertEqual(r["mean_dry_mg_ha"],6.0)
        self.assertEqual(r["range_dry_mg_ha"],[0.0,11.8])
        self.assertEqual(r["evidence_type"],"standing_litter_dry_mass")
        self.assertNotIn("queda anual",r["method"])

    @unittest.skipUnless(gpd and box, "geospatial dependencies required")
    def test_tapajos_litter_does_not_transfer_outside_study_class_or_biome(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-54.96,-3.31,-54.94,-3.29)],crs="EPSG:4326")
        self.assertIsNone(tapajos_litter_stock_component("Amazônia","Floresta Ombrófila Densa",aoi))
        local=gpd.GeoDataFrame(geometry=[box(-54.984,-3.068,-54.982,-3.065)],crs="EPSG:4326")
        self.assertIsNone(tapajos_litter_stock_component("Cerrado","Floresta Ombrófila Densa",local))
        self.assertIsNone(tapajos_litter_stock_component("Amazônia","Savana Arborizada",local))

if __name__=="__main__":
    unittest.main()
