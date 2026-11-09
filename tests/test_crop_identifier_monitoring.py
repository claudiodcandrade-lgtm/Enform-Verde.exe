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
        # V87.36/V87.37: no thematic map names a current crop; every crop needs
        # an independently validated SAR classifier (none installed → no label).
        rows = {r["crop"]: r for r in cic.consolidated_table()}
        self.assertEqual(set(rows), LISTED)
        for r in rows.values():
            self.assertFalse(r["label_allowed"])
            self.assertNotIn("MAPBIOMAS", repr(r).upper())

    def test_pam_attribution_is_probability_not_identification(self):
        att = cic.attribute_unseparated("51006", 100.0)       # Alto Teles Pires
        self.assertEqual(att["status"], "PAM_PRIOR_ONLY")
        self.assertAlmostEqual(sum(att["probabilities"].values()), 1.0, places=6)
        self.assertEqual(att["most_likely"], "Milho")
        self.assertIn("não identifica cultura", att["note"])


class MonitoringTests(unittest.TestCase):
    land = {"classes": [
        {"class_name": "Lavoura de Soja", "source": "MAPBIOMAS", "area_ha": 120.0},
        {"class_name": "Outras Lavouras Temporárias", "source": "MAPBIOMAS", "area_ha": 30.0},
        {"class_name": "Lavoura de Café", "source": "MAPBIOMAS", "area_ha": 5.0},
        {"class_name": "Formação Florestal", "source": "MAPBIOMAS", "area_ha": 50.0}]}

    def test_mapbiomas_is_historical_not_current_crop_identification(self):
        self.assertEqual(crops_in_land_result(self.land), {})
        sar = {"classes": [
            {"class_name": "Lavoura de Soja", "source": "SAR_VALIDADO", "area_ha": 12.0},
            {"class_name": "Lavoura de Café", "source": "MAPBIOMAS", "area_ha": 5.0}]}
        self.assertEqual(crops_in_land_result(sar), {"Soja": 12.0})

    def test_mapbiomas_reference_cannot_trigger_vigor_or_yield(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        called = {}
        def fake_forecast(fields, as_of):
            called["forecast"] = True
            return {"status": "ok", "model": "panel", "production": {}}
        lines, audit = monitoring_forecast(
            g, self.land, as_of=date(2026, 10, 31), forecast_fn=fake_forecast)
        txt = "\n".join(lines)
        self.assertIn("Cultura atual: N/D", txt)
        # V87.38: MapBiomas is not even shown in the current-crop section.
        self.assertNotIn("MapBiomas", txt)
        self.assertIn("Vigor: N/D", txt)
        self.assertIn("Produtividade e produção da propriedade: N/D", txt)
        self.assertNotIn("Produtividade provável:", txt)
        self.assertNotIn("Soja (120", txt)
        self.assertNotIn("forecast", called)
        self.assertEqual(audit["current_crop_identification"], "N/D")
    def test_vigor_failure_blocks_forecast_even_with_mapbiomas_area(self):
        g = gpd.GeoDataFrame(geometry=[Point(-55.7, -12.5).buffer(.01)], crs=4326)
        called = {}
        def bad(*a): raise RuntimeError("offline")
        def fake_forecast(fields, as_of):
            called["forecast"] = True
            return {"status": "ok"}
        lines, audit = monitoring_forecast(
            g, {"classes": [self.land["classes"][0]]},
            as_of=date(2026, 10, 31), vigor_fn=bad, forecast_fn=fake_forecast)
        text = "\n".join(lines)
        self.assertIn("Cultura atual: N/D", text)
        self.assertNotIn("forecast", called)
        self.assertEqual(audit["current_crop_identification"], "N/D")

class AutomaticVigorGuardTests(unittest.TestCase):
    def test_no_scene_is_nd(self):
        g = gpd.GeoDataFrame(geometry=[box(-55.72, -12.52, -55.70, -12.50)], crs=4326)
        r = automatic_vigor(g, date(2026, 10, 31), 39, search=lambda *a, **k: {"scenes": []}, token_fn=lambda: "x")
        self.assertEqual(r["status"], "N/D"); self.assertIn("sem cena Sentinel-1", r["reason"])


if __name__ == "__main__":
    unittest.main()
