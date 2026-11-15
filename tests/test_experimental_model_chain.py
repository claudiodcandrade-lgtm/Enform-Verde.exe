"""Owner policy 09/11/2026: defensible experimental models run now; field accuracy later."""
import unittest
from datetime import date, timedelta

import numpy as np

import crop_vigor as cv


def _field(rng, mu, spread, n=40):
    vh = mu + rng.gamma(4, spread / 4, (n, n)) - spread
    return vh, vh + 6 + rng.normal(0, .5, (n, n))


class ExperimentalRviVigorTests(unittest.TestCase):
    def test_vigor_without_height_runs_as_experimental_rvi_proxy(self):
        rng = np.random.default_rng(5)
        refs = [cv.field_metrics(*_field(rng, -16 + rng.normal(0, .6), 2.0)) for _ in range(10)]
        r = cv.classify_vigor(*_field(rng, -13.5, 1.2), refs, n_boot=60)
        self.assertEqual(r["status"], "experimental")
        self.assertEqual(r["size_basis"], "EXPERIMENTAL_PROXY_VV+VH")
        self.assertIn("Nasirzadehdizaji", r["size_proxy_evidence"]); self.assertIn("0,82", r["size_proxy_evidence"])
        self.assertIn(r["class"], cv.CLASSES)
        self.assertAlmostEqual(sum(r["probabilities"].values()), 1.0)

    def test_height_and_rvi_are_never_mixed(self):
        rng = np.random.default_rng(6)
        refs = [cv.field_metrics(*_field(rng, -16, 2.0), height_m=np.full((40, 40), .8)) for _ in range(8)]
        r = cv.classify_vigor(*_field(rng, -16, 2.0), refs, n_boot=20)
        self.assertEqual(r["status"], "N/D")


class WeatherLatencyTests(unittest.TestCase):
    def test_power_latency_does_not_null_the_season(self):
        from crop_panel_yield_model import season_ry_ensemble
        days = []; d = date(2000, 1, 1)
        last_obs = date(2026, 11, 3)                     # POWER latency: data end before as_of
        while d <= last_obs:
            days.append({"date": d.strftime("%Y%m%d"), "T2M_MAX": 32.0, "T2M_MIN": 21.0, "PRECTOTCORR": 6.0}); d += timedelta(days=1)
        ens = season_ry_ensemble(days, "Soja", -12.0, 2026, 1.0, date(2026, 11, 9), range(2000, 2026))
        self.assertGreater(len(ens), 20)


class VigorSearchGeometryTests(unittest.TestCase):
    def test_scene_search_uses_field_bbox(self):
        src = open("crop_vigor_auto.py", encoding="utf-8").read()
        self.assertIn("_scene(_box(*g.bounds)", src)


if __name__ == "__main__":
    unittest.main()
