import unittest
from pathlib import Path
from carbon_compartments import ifn_necromass_component, tapajos_litter_stock_component

try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:
    gpd=box=None

DATA=Path(__file__).resolve().parents[1]/"data"/"ifn_necromass_biome_uf_v1.csv"

class CarbonCompartmentTests(unittest.TestCase):
    def test_direct_ifn_necromass_uses_biome_and_state_and_preserves_transfer_limit(self):
        r=ifn_necromass_component("Amazônia","Pará",DATA)
        self.assertIsNotNone(r)
        self.assertEqual(r["evidence_type"],"direct_ifn_aboveground_necromass")
        self.assertGreater(r["mean_dry_mg_ha"],0)
        self.assertGreater(r["n_independent_units"],1)
        self.assertFalse(r["include_in_total"])
        self.assertIn("não traz coordenadas nem classe IBGE",r["method"])
        self.assertIsNone(ifn_necromass_component("Pantanal","Mato Grosso do Sul",DATA))
        self.assertIsNone(ifn_necromass_component("Amazônia","São Paulo",DATA))

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
