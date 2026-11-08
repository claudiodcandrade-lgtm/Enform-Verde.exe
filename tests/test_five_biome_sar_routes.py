"""Regression: five native biomes must be eligible for SAR routing diagnostics.

This is a structural coverage check, not a proof of AOI-specific AGB or SAR
measurement. A successful result must not be labelled scientific validation.
"""
import unittest

from sar_pipeline import (
    SUPPORTED_NATIONAL_BIOMES,
    _canonical_biome_name,
    national_predictive_route_matrix,
)

class FiveBiomeSarRouteTests(unittest.TestCase):
    def test_all_five_biomes_supported(self):
        names = ("Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal")
        self.assertEqual(set(SUPPORTED_NATIONAL_BIOMES), set(names))
        for name in names:
            with self.subTest(biome=name):
                route = national_predictive_route_matrix(name, "formação nativa", aoi=None)
                self.assertTrue(route["supported_biome"])
                self.assertEqual(route["biome"], name)
                self.assertEqual(set(route["supported_scope"]), set(names))
                self.assertFalse(route["biome_mean_permitted"])
                self.assertTrue(any(x["route"] == "ESA_BIOMASS_FP_AGB_L2B"
                                    for x in route["direct_product_routes"]))
                # No actual scene processed, so routing MUST NOT claim validity.
                self.assertEqual(route["direct_product_routes"][0]["eligible"], "runtime_check")

    def test_lowercase_pantanal_alias(self):
        self.assertEqual(_canonical_biome_name("pantanal"), "Pantanal")
        self.assertTrue(national_predictive_route_matrix("pantanal",
                        "Formação Campestre")["supported_biome"])

if __name__ == "__main__":
    unittest.main()
