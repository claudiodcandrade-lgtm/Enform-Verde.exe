"""Consolidated identifiers (8 listed crops), automatic vigor guards and the
monitoring add-on. Fakes only for network parts; PAM data are the real file."""
import unittest
from datetime import date

import geopandas as gpd
from shapely.geometry import Point, box

import crop_identifier_consolidated as cic
from crop_monitoring_forecast import crops_in_land_result, monitoring_forecast
from crop_vigor_auto import automatic_vigor

LISTED = {"Soja", "Milho", "Sorgo", "Café", "Cana-de-açúcar", "Arroz", "Feijão", "Citros"}


class ConsolidatedIdentifierTests(unittest.TestCase):
    def test_all_listed_crops_have_a_route_and_stated_uncertainty(self):
        rows = {r["crop"]: r for r in cic.consolidated_table()}
        self.assertEqual(set(rows), LISTED)
        for r in rows.values():
            self.assertEqual(r["tier"], 1)                      # Brazilian sources first
            self.assertTrue(r["uncertainty"])
            self.assertFalse(r["sar_model_installed"])
        for c in ("Milho", "Sorgo", "Feijão"):
            self.assertFalse(rows[c]["label_allowed"])          # never named without a separating source
        for c in ("Soja", "Café", "Citros", "Arroz", "Cana-de-açúcar"):
            self.assertTrue(rows[c]["label_allowed"])

    def test_pam_attribution_is_probability_not_identification(self):
        att = cic.attribute_unseparated("51006", 100.0)       # Alto Teles Pires
        self.assertEqual(att["status"], "atribuicao_probabilistica")
        self.assertAlmostEqual(sum(att["probabilities"].values()), 1.0, places=6)
        self.assertEqual(att["most_likely"], "Milho")
        self.assertIn("Não identifica", att["note"])


class MonitoringTests(unittest.TestCase):
    land = {"classes": [
        {"class_name": "Lavoura de Soja", "source": "MAPBIOMAS", "area_ha": 120.0},
        {"class_name": "Outras Lavouras Temporárias", "source": "MAPBIOMAS", "area_ha": 30.0},
        {"class_name": "Lavoura de Café", "source": "MAPBIOMAS", "area_ha": 5.0},
        {"class_name": "Formação Florestal", "source": "MAPBIOMAS", "area_ha": 50.0}]}

    def test_land_result_parsing(self):
        self.assertEqual(crops_in_land_result(self.land), {"Soja": 120.0, "__temporarias__": 30.0, "Café": 5.0})

    def test_monitoring_lines_use_vigor_and_forecast_and_attribution(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        vig = lambda gdf, as_of, code: {"status": "experimental", "class": "alto vigor", "acquisition_utc": "2026-10-31T09:16:48Z",
                                         "probabilities": {"baixo vigor": .0, "vigor adequado": .2, "alto vigor": .8}}
        seen = {}
        def fake_forecast(fields, as_of):
            seen["vigor"] = fields[0]["vigor"]; seen["area"] = fields[0]["area_ha"]
            return {"status": "ok", "model": "panel", "model_label": "TESTE", "fields": {}}
        lines, audit = monitoring_forecast(g, self.land, as_of=date(2026, 10, 31), vigor_fn=vig, forecast_fn=fake_forecast)
        txt = "\n".join(lines)
        self.assertIn("Vigor automático (Sentinel-1 2026-10-31): alto vigor", txt)
        self.assertIn("cultura NÃO identificada", txt)
        self.assertIn("sem modelo calibrado", txt)                 # café has no calibrated model
        self.assertEqual(seen["area"], 120.0); self.assertEqual(seen["vigor"]["class"], "alto vigor")

    def test_vigor_failure_does_not_stop_forecast(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        def bad(*a): raise RuntimeError("offline")
        called = {}
        def fake_forecast(fields, as_of):
            called["v"] = fields[0]["vigor"]; return {"status": "N/D", "fields": {}}
        lines, _ = monitoring_forecast(g, {"classes": [self.land["classes"][0]]}, as_of=date(2026, 10, 31),
                                       vigor_fn=bad, forecast_fn=fake_forecast)
        self.assertIn("Vigor automático: N/D", "\n".join(lines)); self.assertEqual(called["v"]["status"], "N/D")


class AutomaticVigorGuardTests(unittest.TestCase):
    def test_no_scene_is_nd(self):
        g = gpd.GeoDataFrame(geometry=[box(-55.72, -12.52, -55.70, -12.50)], crs=4326)
        r = automatic_vigor(g, date(2026, 10, 31), 39, search=lambda *a, **k: {"scenes": []}, token_fn=lambda: "x")
        self.assertEqual(r["status"], "N/D"); self.assertIn("sem cena Sentinel-1", r["reason"])


if __name__ == "__main__":
    unittest.main()
