import unittest
import geopandas as gpd
from shapely.geometry import Point
from national_fallback import national_agb_fallback

class PantanalFallbackTests(unittest.TestCase):
    def _aoi(self, lon, lat):
        return gpd.GeoDataFrame({"geometry":[Point(lon,lat)]}, crs="EPSG:4326")

    def test_riparian_forest_uses_published_southeast_pantanal_stock(self):
        r=national_agb_fallback("Pantanal","Floresta Ripária",
            self._aoi(-56.2289,-19.5531))
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["agb_mg_ha"],184.1/0.47)
        self.assertEqual(r["data_origin"],"MODELAGEM_LITERATURA_HIERARQUICA")
        self.assertIn("tipo não informado",r["uncertainty_kind"])

    def test_grassy_woody_savanna_is_supported_with_explicit_uncertainty(self):
        r=national_agb_fallback("Pantanal","Savana Gramíneo-Lenhosa",
            self._aoi(-56.3711,-19.9208))
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["agb_mg_ha"],26.6/0.47)
        self.assertGreater(r["uncertainty_mg_ha"],0)

    def test_does_not_transfer_pantanal_fallback_outside_evidence_domain(self):
        r=national_agb_fallback("Pantanal","Floresta Ripária",
            self._aoi(-57.0,-16.0))
        self.assertIsNone(r)

    def test_unreported_physiognomy_is_not_assigned_a_fake_value(self):
        r=national_agb_fallback("Pantanal","Savana Arborizada",None)
        self.assertIsNone(r)

if __name__=="__main__":
    unittest.main()
