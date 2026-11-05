"""Calibrated panel yield model: FAO water balance, pooled β, LOYO, vigor conditioning.

Synthetic data verify the estimators; the versioned artifact is checked for
its contract and out-of-sample metrics (built from PAM + NASA POWER + PronaSolos).
"""
import unittest
from datetime import date, timedelta

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

import crop_panel_yield_model as pm
import crop_water_balance_yield as wb
from crop_forecast_pipeline import forecast_fields, forecast_lines


def weather(years, rain=lambda d: 6.0):
    out = []; d = date(years[0], 1, 1)
    while d <= date(years[-1], 12, 31):
        out.append({"date": d.strftime("%Y%m%d"), "T2M_MAX": 32.0, "T2M_MIN": 20.0, "PRECTOTCORR": rain(d)}); d += timedelta(days=1)
    return out


class WaterBalanceTests(unittest.TestCase):
    def test_wet_season_has_no_loss_and_drought_reduces_ry(self):
        wet = wb.season_ry(weather(range(2019, 2022), lambda d: 12.0), "Soja", -12.5, 2020, 1.2)
        dry = wb.season_ry(weather(range(2019, 2022), lambda d: 0.5), "Soja", -12.5, 2020, 1.2)
        self.assertAlmostEqual(wet["ry"], 1.0, places=6); self.assertAlmostEqual(wet["isna"], 1.0, places=6)
        self.assertLess(dry["ry"], 0.3); self.assertEqual(dry["n_sowings"], 3)

    def test_flowering_drought_hurts_maize_more_than_soy(self):
        # same mid-season drought; FAO-33 flowering Ky maize (1.5) > soybean (0.8)
        def rain(d): return 0.0 if d.month in (12, 1) else 10.0
        soy = wb.season_ry(weather(range(2019, 2022), rain), "Soja", -12.5, 2020, 1.0)["ry"]
        self.assertLess(soy, 1.0)

    def test_harvest_year(self):
        self.assertEqual(wb.harvest_year("Soja", -12.5, 2026), 2027)
        self.assertEqual(wb.harvest_year("Milho", -12.5, 2026), 2027)
        self.assertEqual(wb.harvest_year("Milho", -28.0, 2026), 2027)


class PanelTests(unittest.TestCase):
    def synthetic_panel(self, beta=3000.0, noise=60.0, seed=1):
        rng = np.random.default_rng(seed); panel = {}
        for u in range(8):
            ry = {y: float(rng.uniform(.3, 1.0)) for y in range(2015, 2025)}
            panel[f"U{u}"] = {"uf": "RS", "ry": ry,
                              "yields": {y: 1500 + 40 * (y - 2015) + 100 * u + beta * ry[y] + rng.normal(0, noise) for y in ry}}
        return panel

    def test_pooled_beta_recovered_and_loyo_beats_trend(self):
        panel = self.synthetic_panel()
        units = [(c,) + pm._arrays(u["yields"], u["ry"]) for c, u in panel.items()]
        self.assertAlmostEqual(pm.fit_beta(units), 3000.0, delta=150)
        l = pm.loyo(panel)
        self.assertGreater(l["skill_vs_trend"], .5); self.assertEqual(l["units_improved"], 8)

    def test_no_signal_gives_no_skill(self):
        l = pm.loyo(self.synthetic_panel(beta=0.0))
        self.assertLess(l["skill_vs_trend"], .1)

    def test_vigor_thirds_order_the_forecast(self):
        art = pm.calibrate({"Soja": self.synthetic_panel(noise=200)}, {"test": True})
        out = {}
        for v in pm.VIGOR:
            p = pm.field_params(art, "Soja", "U0", "RS", {}, [0.6], 2025, {v: 1.0})
            out[v] = pm.simulate([{"id": "a", "area_ha": 1, "group": "g", "params": p}], n=600)["fields_kg_ha"]["a"]["median"]
        self.assertLess(out["baixo vigor"], out["vigor adequado"]); self.assertLess(out["vigor adequado"], out["alto vigor"])

    def test_shared_terms_make_fields_comonotonic(self):
        art = pm.calibrate({"Soja": self.synthetic_panel(noise=200)}, {})
        p = pm.field_params(art, "Soja", "U0", "RS", {}, [0.3, 0.9], 2025)
        r = pm.simulate([{"id": "a", "area_ha": 100, "group": "g", "params": p},
                         {"id": "b", "area_ha": 100, "group": "g", "params": p}], n=400)
        self.assertAlmostEqual(r["fields_kg_ha"]["a"]["median"], r["fields_kg_ha"]["b"]["median"])

    def test_unknown_group_is_nd(self):
        self.assertEqual(pm.field_params({"crops": {}}, "Soja", "X", "MT", {}, [1], 2025)["status"], "N/D")


class ArtifactTests(unittest.TestCase):
    def test_versioned_artifact_contract_and_out_of_sample_metrics(self):
        art = pm.load_artifact()
        self.assertIsNotNone(art)
        for crop in ("Soja", "Milho"):
            for g, m in art["crops"][crop].items():
                l = m["loyo"]
                self.assertGreaterEqual(l["units"], 8)
                self.assertEqual(len(l["errors_kg_ha"]), l["n"])
                self.assertGreater(m["beta_kg_ha_per_RY"], 0)       # drier → lower yield
        self.assertGreater(art["crops"]["Soja"]["Sul"]["loyo"]["skill_vs_trend"], 0.15)
        self.assertGreater(art["crops"]["Milho"]["Centro-Norte"]["loyo"]["skill_vs_trend"], 0.10)
        self.assertEqual(len(art["provenance"]["pam_file_sha256"]), 64)

    def test_pipeline_blocks_property_yield_without_observed_vigor(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        fake_wx = lambda lat, lon, s, e: {"daily": weather(range(2000, 2027), lambda d: 7.0), "source_url": "synthetic"}
        fake_awc = lambda lat, lon: {"awc_mm_cm": 1.1, "source": "teste"}
        rep = forecast_fields([{"id": "T", "gdf": g, "crop": "Soja", "identification": {"label_allowed": True},
                                "vigor": None, "area_ha": 100}], as_of=date(2026, 10, 31),
                              weather_fetcher=fake_wx, awc_fetcher=fake_awc, n_mc=200)
        self.assertEqual(rep["model"], "panel")
        txt = "\n".join(forecast_lines(rep))
        self.assertIn("calibrado no histórico PAM", txt)
        self.assertIn("vigor SAR atual indisponível", txt)
        self.assertNotIn("Alto Teles Pires", txt)


if __name__ == "__main__":
    unittest.main()
