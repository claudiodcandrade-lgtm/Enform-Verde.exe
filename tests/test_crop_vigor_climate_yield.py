"""Crop identifier priority, vigor, climate favourability and yield scenarios.

Synthetic SAR/weather fixtures and the versioned IBGE PAM/microregion files.
These are numerical/contract regressions, NOT field validation.
"""
import math
import unittest
from datetime import date, timedelta

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

import crop_climate_favorability as ccf
import crop_vigor as cv
import crop_yield_scenario as cys
from crop_forecast_pipeline import forecast_fields, forecast_lines
from crop_model_priority import select_identifier, tier_of, wilson_interval

SHA = "a" * 64
OK = lambda acc, n, scope="published_original_domain": {
    "artifact_sha256": SHA, "artifact_verified": True, "predictor_manifest": ["VH", "VV"],
    "method_documented": True, "accuracy": acc, "n_independent": n, "validation_scope": scope}
CANDS = [
    {"id": "GLOBAL", "institution": "Some University, Germany", "origin": "international", "crops": ("soja",)},
    {"id": "ICRISAT", "institution": "ICRISAT", "origin": "african_savanna", "crops": ("soja",)},
    {"id": "CIRAD", "institution": "CIRAD UMR TETIS", "origin": "african_savanna", "crops": ("soja",)},
    {"id": "EMBRAPA", "institution": "Embrapa Territorial", "origin": "brazil", "crops": ("soja",)},
]


class IdentifierPriorityTests(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(tier_of(CANDS[3]), (1, 0))
        self.assertEqual(tier_of(CANDS[2]), (2, 0))
        self.assertEqual(tier_of(CANDS[1]), (2, 1))
        self.assertEqual(tier_of(CANDS[0]), (3, 0))
        self.assertEqual(tier_of({"institution": "ESALQ/USP", "origin": "?"})[0], 1)

    def test_brazil_first_even_with_lower_accuracy(self):
        r = select_identifier("soja", CANDS, {"EMBRAPA": OK(.70, 200, "brazil_independent"),
                                             "CIRAD": OK(.95, 500), "GLOBAL": OK(.99, 900)})
        self.assertEqual(r["selected"], "EMBRAPA"); self.assertEqual(r["status"], "validated_brazil")

    def test_cirad_before_other_african_and_global(self):
        r = select_identifier("soja", CANDS, {"ICRISAT": OK(.95, 500), "CIRAD": OK(.80, 300),
                                             "GLOBAL": OK(.99, 900)})
        self.assertEqual(r["selected"], "CIRAD"); self.assertEqual(r["tier"], 2)
        self.assertEqual(r["status"], "experimental_transfer")
        self.assertEqual(r["rejected_higher_priority"][0]["id"], "EMBRAPA")
        self.assertFalse(r["transfer_error_quantified"])

    def test_unquantifiable_uncertainty_is_not_usable_and_falls_through(self):
        st = OK(.9, 100); st.pop("n_independent")
        r = select_identifier("soja", CANDS, {"EMBRAPA": st, "GLOBAL": OK(.85, 120)})
        self.assertEqual(r["selected"], "GLOBAL"); self.assertEqual(r["tier"], 3)
        self.assertIn("incerteza não quantificável", " ".join(r["rejected_higher_priority"][0]["reasons"]))

    def test_none_usable_gives_cultivated_area_not_a_crop(self):
        r = select_identifier("soja", CANDS, {})
        self.assertFalse(r["label_allowed"]); self.assertIn("cultura não identificada", r["output_label"])

    def test_wilson(self):
        lo, hi = wilson_interval(45, 50)
        self.assertLess(lo, .9); self.assertGreater(hi, .9)


def _field(rng, mu, spread, n=40):
    vh = mu + rng.gamma(4, spread / 4, (n, n)) - spread
    return vh, vh + 6 + rng.normal(0, .5, (n, n))


def _h(mu, n=40):
    """Synthetic plant height (m): V87.36 composite vigor requires height."""
    return np.full((n, n), mu)


class VigorTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(3)
        self.ref = []
        for _ in range(12):
            d = self.rng.normal(0, .6)
            self.ref.append(cv.field_metrics(*_field(self.rng, -16 + d, 2.0), height_m=_h(0.8 + 0.1 * d)))

    def test_glcm_symmetric_counts(self):
        c = cv._glcm_counts(np.array([[0, 1], [1, 0]]))
        self.assertEqual((c[0, 0], c[0, 1], c[1, 0], c[1, 1]), (2, 4, 4, 2))
        self.assertTrue(np.allclose(c, c.T))

    def test_strong_and_weak_fields(self):
        hi = cv.classify_vigor(*_field(self.rng, -13.5, 1.2), self.ref, n_boot=80, height_m=_h(1.2))
        lo = cv.classify_vigor(*_field(self.rng, -19.0, 4.0), self.ref, n_boot=80, height_m=_h(0.4))
        self.assertEqual(hi["class"], "alto vigor"); self.assertGreater(hi["probabilities"]["alto vigor"], .9)
        self.assertEqual(lo["class"], "baixo vigor"); self.assertGreater(lo["probabilities"]["baixo vigor"], .9)
        self.assertAlmostEqual(sum(hi["probabilities"].values()), 1.0)
        self.assertEqual(hi["status"], "experimental")

    def test_insufficient_reference_or_pixels_is_nd(self):
        self.assertEqual(cv.classify_vigor(*_field(self.rng, -16, 2), self.ref[:3])["status"], "N/D")
        vh, vv = _field(self.rng, -16, 2, n=4)
        self.assertEqual(cv.classify_vigor(vh, vv, self.ref)["status"], "N/D")

    def test_height_and_rvi_size_are_not_mixed(self):
        vh, vv = _field(self.rng, -16, 2)
        rvi_refs = [cv.field_metrics(*_field(self.rng, -16, 2.0)) for _ in range(8)]   # RVI-size refs
        r = cv.classify_vigor(vh, vv, rvi_refs, height_m=np.full(vh.shape, 0.8))
        self.assertEqual(r["status"], "N/D")
        r = cv.classify_vigor(vh, vv, self.ref)          # field without height, refs with height
        self.assertEqual(r["status"], "N/D")             # never mix height and RVI-proxy sizes


def _synthetic_weather(lat, years, dry_year=None, hot_year=None):
    out = []
    d = date(years[0], 1, 1)
    while d <= date(years[-1] + 1, 12, 31):
        sy = d.year if d.month >= 10 else d.year - 1
        rain = 6.0 + 2.0 * math.sin(d.toordinal())
        tmax = 31.0 + 1.5 * math.cos(d.toordinal() / 3)
        if sy == dry_year: rain *= .2
        if sy == hot_year: tmax += 6
        out.append({"date": d.strftime("%Y%m%d"), "T2M_MAX": tmax, "T2M_MIN": tmax - 10, "PRECTOTCORR": rain})
        d += timedelta(days=1)
    return out


class ClimateTests(unittest.TestCase):
    def test_fao56_radiation_example(self):
        self.assertAlmostEqual(ccf.extraterrestrial_radiation(-20, 246), 32.2, places=1)
        self.assertTrue(2 < ccf.et0_hargreaves(32, 20, -12, 300) < 8)

    def test_dry_hot_season_is_unfavourable(self):
        yrs = list(range(2005, 2026))
        wx = _synthetic_weather(-12.5, yrs, dry_year=2025, hot_year=2025)
        r = ccf.favourability(wx, "Soja", -12.5, 2025, yrs[:-1])
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["class"], "desfavorável"); self.assertAlmostEqual(r["probabilities"]["desfavorável"], 1.0)

    def test_partial_season_uses_analog_years(self):
        yrs = list(range(2005, 2026))
        wx = _synthetic_weather(-12.5, yrs)
        r = ccf.favourability(wx, "Soja", -12.5, 2025, yrs[:-1], as_of=date(2025, 10, 20))
        self.assertLess(r["observed_fraction_of_season"], .2)
        self.assertEqual(len(r["analog_F"]), len(r["reference_years"]))

    def test_short_record_is_nd(self):
        wx = _synthetic_weather(-12.5, [2020, 2021, 2022])
        self.assertEqual(ccf.favourability(wx, "Soja", -12.5, 2022, [2020, 2021])["status"], "N/D")


class YieldScenarioTests(unittest.TestCase):
    Y = {2015 + i: 3000 + 30 * i + d for i, d in enumerate([0, -150, 120, 60, -40, 200, -90, 10, 150, -120])}

    def test_theil_sen_exact_line(self):
        b, a = cys.theil_sen([1, 2, 3, 4], [5, 7, 9, 11])
        self.assertAlmostEqual(b, 2); self.assertAlmostEqual(a, 3)

    def test_matrix_rule(self):
        t = cys.scenario_table(self.Y, 2027)
        tab = t["table_kg_ha"]
        self.assertAlmostEqual(tab["baixo vigor"]["desfavorável"], t["floor"])
        self.assertAlmostEqual(tab["alto vigor"]["favorável"], t["ceiling"])
        self.assertGreater(tab["vigor adequado"]["favorável"], t["mean"] - 1e-9)
        vals = [tab[v][c] for v in cys.VIGOR for c in cys.CLIMATE]
        for v in cys.VIGOR:
            row = [tab[v][c] for c in cys.CLIMATE]; self.assertEqual(row, sorted(row))
        self.assertEqual(len(vals), 9)

    def test_deterministic_inputs_reproduce_table_cell(self):
        f = {"id": "A", "crop": "Soja", "micro_code": "X", "area_ha": 100, "yields": self.Y,
             "vigor_probs": {"vigor adequado": 1}, "climate_probs": {"favorável": 1}}
        r = cys.forecast_production([f], 2027, n_mc=400)
        cell = cys.scenario_table(self.Y, 2027)["table_kg_ha"]["vigor adequado"]["favorável"]
        self.assertLess(abs(r["fields_kg_ha"]["A"]["median"] - cell), 120)   # only trend bootstrap left
        self.assertIn("model_error", r["uncertainty_sources_NOT_quantified"])
        self.assertIn("transfer", r["uncertainty_sources_NOT_quantified"])

    def test_shared_climate_makes_fields_dependent(self):
        mk = lambda i: {"id": i, "crop": "Soja", "micro_code": "X", "area_ha": 100, "area_sd_ha": 1,
                        "yields": self.Y, "vigor_probs": {"vigor adequado": 1},
                        "climate_probs": {"desfavorável": .5, "favorável": .5},
                        "hindcast": {"errors_kg_ha": [-100, 0, 100]}, "transfer_sd_kg_ha": 50}
        r = cys.forecast_production([mk("A"), mk("B")], 2027, n_mc=600)
        self.assertEqual(r["uncertainty_sources_NOT_quantified"], [])
        self.assertGreater(r["production_t"]["p95"] - r["production_t"]["p05"], 0)

    def test_real_pam_and_microregion_files(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        m = cys.microregion_of(g)["dominant"]
        self.assertEqual((m["code"], m["uf"]), ("51006", "MT"))
        y = cys.load_microregion_yields("Soja", "51006")
        self.assertEqual(sorted(y), list(range(2015, 2025)))
        self.assertTrue(all(2000 < v < 5000 for v in y.values()))

    def test_hindcast_reports_skill_against_trend_only(self):
        F = {y: (-1 if v < 3150 else 1) * 1.0 for y, v in self.Y.items()}
        h = cys.hindcast_errors(self.Y, F)
        self.assertEqual(h["n"], 10); self.assertIn("climate_skill_vs_trend", h)


class PipelineTests(unittest.TestCase):
    def test_unidentified_crop_is_nd_and_identified_field_is_forecast(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        fake = lambda lat, lon, s, e: {"daily": _synthetic_weather(lat, list(range(2000, 2026))), "source_url": "synthetic"}
        vig = {"status": "experimental", "class": "vigor adequado",
               "probabilities": {"baixo vigor": .1, "vigor adequado": .8, "alto vigor": .1}}
        fields = [{"id": "T1", "gdf": g, "crop": "Soja", "identification": {"label_allowed": True},
                   "vigor": vig, "area_ha": 200},
                  {"id": "T2", "gdf": g, "crop": "Soja", "identification": {"label_allowed": False},
                   "vigor": vig, "area_ha": 100}]
        rep = forecast_fields(fields, as_of=date(2026, 3, 1), weather_fetcher=fake, n_mc=300, model="scenario")
        self.assertEqual(rep["fields"]["T2"]["status"], "N/D")
        self.assertEqual(rep["fields"]["T1"]["harvest_year"], 2026)
        lines = "\n".join(forecast_lines(rep))
        self.assertIn("CENÁRIO NÃO CALIBRADO", lines); self.assertIn("Alto Teles Pires", lines); self.assertIn("T2: N/D", lines)


if __name__ == "__main__":
    unittest.main()
