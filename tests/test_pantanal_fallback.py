import unittest
from unittest.mock import patch
from national_fallback import national_agb_fallback

class PantanalFallbackTests(unittest.TestCase):
    def test_riparian_forest_uses_published_southeast_pantanal_stock(self):
        with patch("national_fallback._aoi_distance_km",return_value=0.0):
            r=national_agb_fallback("Pantanal","Floresta Ripária",object())
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["agb_mg_ha"],184.1/0.47)
        self.assertEqual(r["data_origin"],"MODELAGEM_LITERATURA_HIERARQUICA")
        self.assertIn("tipo não informado",r["uncertainty_kind"])

    def test_grassy_woody_savanna_is_supported_with_explicit_uncertainty(self):
        with patch("national_fallback._aoi_distance_km",return_value=0.0):
            r=national_agb_fallback("Pantanal","Savana Gramíneo-Lenhosa",object())
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["agb_mg_ha"],26.6/0.47)
        self.assertGreater(r["uncertainty_mg_ha"],0)

    def test_does_not_transfer_pantanal_fallback_outside_evidence_domain(self):
        with patch("national_fallback._aoi_distance_km",return_value=200.0):
            r=national_agb_fallback("Pantanal","Floresta Ripária",object())
        self.assertIsNone(r)

    def test_unreported_physiognomy_is_not_assigned_a_fake_value(self):
        r=national_agb_fallback("Pantanal","Savana Arborizada",None)
        self.assertIsNone(r)

if __name__=="__main__":
    unittest.main()
