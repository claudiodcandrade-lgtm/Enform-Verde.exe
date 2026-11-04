"""Regression gates for national standing-litter references; synthetic AOI only."""
import unittest
from shapely.geometry import box
from national_litter_inventory_registry import (
    REFERENCES, published_national_litter_component, ifn_litter_context)


class NationalLitterRegistryTests(unittest.TestCase):
    def test_every_reference_has_direct_mass_provenance_and_exact_physiognomy(self):
        assert len(REFERENCES) >= 7
        assert len({r["key"] for r in REFERENCES}) == len(REFERENCES)
        for r in REFERENCES:
            self.assertGreater(r["dry_mg_ha"],0)
            self.assertTrue(r["url"].startswith("https://"))
            self.assertTrue(r["terms"])
            self.assertEqual(len(r["bbox"]),4)

    def test_mata_galeria_does_not_match_cerrado_tipico(self):
        geom=box(-47.95,-15.98,-47.94,-15.97)
        a=published_national_litter_component("Cerrado","Mata de Galeria",geom)
        b=published_national_litter_component("Cerrado","Cerrado Típico",geom)
        self.assertEqual(a["source_record_id"],"MATA_GALERIA_DF")
        self.assertEqual(b["source_record_id"],"CERRADO_TIPICO_DF")
        self.assertAlmostEqual(a["mean_tc_ha"],9.36*.47,places=6)
        self.assertAlmostEqual(b["mean_tc_ha"],6.08*.47,places=6)
        self.assertFalse(a["include_in_total"])
        self.assertEqual(a["origin"],"EXPERIMENTAL_FISICO")

    def test_state_and_physiognomy_transfer_are_rejected(self):
        geom=box(-55.5,-11.9,-55.4,-11.8)
        self.assertIsNone(published_national_litter_component(
            "Amazônia", "Floresta Ombrófila Mista",geom))
        self.assertIsNone(published_national_litter_component(
            "Mata Atlântica", "Floresta Ombrófila Mista",geom))
        self.assertIsNone(published_national_litter_component(
            "Caatinga","Cerrado Típico",box(-47.95,-15.98,-47.94,-15.97)))

    def test_inventory_ifn_depth_not_carbon(self):
        context=ifn_litter_context()
        self.assertEqual(context["observed_variable"],"Profundidade (cm), five points/UA")
        self.assertFalse(context["usable_for_carbon"])
        self.assertIn("retificado",context["version"])
        self.assertIsNone(published_national_litter_component(
            "Caatinga","Savana Estépica Arborizada",box(-40,-9,-39.9,-8.9)))

    def test_published_dry_stock_not_deposition(self):
        result=published_national_litter_component(
            "Mata Atlântica","Floresta Ombrófila Mista",box(-50.3,-29.5,-50.2,-29.4))
        self.assertAlmostEqual(result["mean_dry_mg_ha"],14.296)
        self.assertIn("SEM",result["status"])
        self.assertFalse(result["include_in_total"])


if __name__=="__main__":
    unittest.main()
