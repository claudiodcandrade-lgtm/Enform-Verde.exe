"""Serapilheira regional hierarchy (V87.40): enters the total with quantified transfer error."""
import math
import unittest

import geopandas as gpd
from shapely.geometry import box

import regional_litter_hierarchy as rl

SINOP = gpd.GeoDataFrame(geometry=[box(-55.21, -11.89, -55.17, -11.855)], crs=4326)
FESV = "Floresta Estacional Sempre-Verde Submontana"


class RegionalLitterTests(unittest.TestCase):
    def test_silva_2009_mean_is_the_annual_mean_of_monthly_stocks(self):
        self.assertAlmostEqual(rl.FESV_SITES[0]["mg_ha"], 5.1211, places=3)

    def test_tau_is_between_site_log_sd_of_independent_forest_sites(self):
        tau, k = rl.pooled_forest_tau()
        self.assertEqual(k, 10)
        self.assertAlmostEqual(tau, 0.396, places=3)

    def test_sinop_fesv_enters_total_with_predictive_interval(self):
        c = rl.fesv_northern_mt_litter_component("Amazônia", FESV, SINOP)
        self.assertTrue(c["include_in_total"])
        self.assertEqual(c["origin"], "INVENTARIO_REGIONAL_HIERARQUICO")
        lo, hi = c["range_tc_ha"]
        self.assertLess(lo, c["mean_tc_ha"]); self.assertLess(c["mean_tc_ha"], hi)
        g = math.sqrt(rl.FESV_SITES[0]["mg_ha"] * rl.FESV_SITES[1]["mg_ha"])
        self.assertAlmostEqual(c["mean_dry_mg_ha"], g, places=6)
        self.assertTrue(0.42 * g * 0.9 < c["mean_tc_ha"] < 0.50 * g * 1.1)
        self.assertIn("PREDITIVO 90%", c["uncertainty_kind"])

    def test_other_physiognomy_or_region_is_not_transferred(self):
        self.assertIsNone(rl.fesv_northern_mt_litter_component("Amazônia", "Floresta Ombrófila Densa", SINOP))
        far = gpd.GeoDataFrame(geometry=[box(-47.9, -15.9, -47.8, -15.8)], crs=4326)
        self.assertIsNone(rl.fesv_northern_mt_litter_component("Amazônia", FESV, far))
        self.assertIsNone(rl.fesv_northern_mt_litter_component("Cerrado", FESV, SINOP))

    def test_more_local_sites_narrow_the_prediction(self):
        one = rl.hierarchical_litter_estimate([6.0])
        three = rl.hierarchical_litter_estimate([6.0, 6.0, 6.0])
        self.assertLess(three["predictive_sd_ln"], one["predictive_sd_ln"])

    def test_native_carbon_uses_it_for_fesv(self):
        from native_carbon import estimate_native_components
        res = estimate_native_components(SINOP, FESV, "Amazônia", lambda *a, **k: {}, lambda a: {})
        rows = res["components"] if isinstance(res, dict) else res
        litter = [r for r in rows if r.get("parametro") == "Serapilheira"]
        self.assertEqual(len(litter), 1)
        self.assertTrue(litter[0]["include_in_total"])
        self.assertEqual(litter[0]["origem"], "INVENTARIO_REGIONAL_HIERARQUICO")


if __name__ == "__main__":
    unittest.main()
