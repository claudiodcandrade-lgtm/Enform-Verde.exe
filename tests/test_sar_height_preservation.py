"""Regression: IFN inventory stock estimates must never replace SAR canopy height.

All tests are synthetic unit contracts. They are not evidence of satellite
availability or independent scientific validation.
"""
import unittest

from sar_pipeline import _preserve_sar_canopy_height, height_scope_contract
from secondary_carbon_adapter import secondary_native_components
from native_carbon import estimate_native_components


class SARCanopyHeightPreservationTests(unittest.TestCase):
    def test_p_band_height_preserved_with_agb_and_provenance(self):
        observed = {
            "height_mean_m": 29.1,
            "height_sd_m": 4.3,
            "height_n_valid_pixels": 47,
            "height_metric": "H100",
            "height_error_kind": "product-standard-error",
            "height_standard_error_pixel_zonal_mean_m": 2.0,
            "product": "FP_FH__L2B",
            "sensor": "ESA BIOMASS",
            "band": "P",
            "paths": ["https://example.org/scene.tif"],
        }
        out = _preserve_sar_canopy_height(
            {"status": "SAR_PROCESSADO", "agb_mg_ha": 310.0,
             "source": "ESA BIOMASS FP_AGB_L2B"},
            observed, {"source": "catalog"})
        self.assertEqual(out["agb_mg_ha"], 310.0)
        self.assertEqual(out["height_mean_m"], 29.1)
        self.assertEqual(out["sar_height"]["product"], "FP_FH__L2B")
        self.assertEqual(out["height_standard_error_pixel_zonal_mean_m"], 2.0)
        self.assertEqual(out["height_n_valid_pixels"], 47)
        self.assertEqual(out["height_route_status"], "ALTURA_SAR_PROCESSADA")
        self.assertEqual(out["audit"]["source"], "catalog")
        self.assertEqual(observed["height_mean_m"], 29.1)

    def test_inventories_dont_become_or_replace_height(self):
        inventory = {"data_origin": "LITERATURA_MICRORREGIONAL",
                     "agb_mg_ha": 270.0, "field_tree_height_m": 38.0}
        absent = _preserve_sar_canopy_height(inventory, None)
        self.assertNotIn("height_mean_m", absent)
        self.assertNotIn("sar_height", absent)
        self.assertEqual(absent["field_tree_height_m"], 38.0)
        self.assertEqual(absent["height_route_status"], "SEM_PRODUTO_DE_ALTURA_SAR_VALIDO")
        height = {"height_mean_m": 26.5, "height_metric": "GEDI RH98",
                  "height_definition_compatible_with_H100": False,
                  "source": "ORNL DAAC GEDI–TanDEM-X",
                  "band": "X", "sensor": "TanDEM-X InSAR + GEDI"}
        out = _preserve_sar_canopy_height(inventory, height)
        self.assertEqual(out["height_mean_m"], 26.5)
        self.assertFalse(out["sar_height"]["height_definition_compatible_with_H100"])
        self.assertEqual(out["agb_mg_ha"], 270.0)

    def test_missing_invalid_and_zero_height_never_inferred(self):
        cases = (None, {}, {"height_mean_m": 0},
                 {"height_mean_m": -1}, {"height_mean_m": float("nan")},
                 {"height_mean_m": float("inf")},
                 {"height_mean_m": "invalid"})
        for bad in cases:
            with self.subTest(bad=bad):
                out = _preserve_sar_canopy_height(
                    {"agb_mg_ha": 250, "field_tree_height_m": 34}, bad)
                self.assertNotIn("sar_height", out)
                self.assertNotIn("height_mean_m", out)
                self.assertEqual(out["agb_mg_ha"], 250)
                self.assertIn(out["height_route_status"],
                              ("SEM_PRODUTO_DE_ALTURA_SAR_VALIDO",
                               "ALTURA_SAR_INVALIDA_OU_N_D"))

    def test_height_contract_keeps_independent_metric_and_uncertainty(self):
        scope = height_scope_contract("Amazônia", "Floresta Ombrófila Densa")
        self.assertIn("FP_FH__L2B", scope["priority"])
        self.assertIn("GTDX", scope["fallback"])
        self.assertIn("pixel SD", scope["error_policy"])
        self.assertEqual(scope["status"], "AOI_SPECIFIC_COVERAGE_AND_ERROR_REQUIRED")

    def test_inventory_fallback_changes_stock_not_sar_height(self):
        # The fallback is optional, and no SAR pixel is fabricated by inventory.
        # Fake locally-scoped evidence is used ONLY as a software contract fixture.
        source = [{
            "biome": "Amazônia",
            "physiognomy": "Floresta Ombrófila Densa",
            "pool": "litter", "unit": "tC/ha",
            "source": "test source", "source_url": "https://example.org/data",
            "institution": "fixture university", "licensed_for_use": True,
            "geographic_tier": "microrregional",
            "evidence_level": "primary_plots_open",
            "estimate": 3, "published_sd": 0.5,
        }]
        def sar_estimator(*_):
            return _preserve_sar_canopy_height(
                {"status": "SAR_PROCESSADO", "agb_mg_ha": 240,
                 "data_origin": "SAR_P_BIOMASS_FP_AGB_L2B",
                 "source": "P-band observation"},
                {"height_mean_m": 31, "height_n_valid_pixels": 8,
                 "band": "P", "sensor": "ESA BIOMASS",
                 "height_metric": "H100"})
        measured = estimate_native_components(
            None, "Floresta Ombrófila Densa", "Amazônia",
            sar_estimator, lambda _: {}, inventory_evidence=source)
        components = {x["parametro"]: x for x in measured["components"]}
        self.assertEqual(components["Serapilheira"]["tc"], 3)
        self.assertAlmostEqual(components["Biomassa aérea"]["tc"], 112.8)
        self.assertEqual(measured["sar_details"]["height_mean_m"], 31)


if __name__ == "__main__":
    unittest.main()
