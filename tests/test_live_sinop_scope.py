"""The Sinop live SAR diagnostic must not report its sample box as farm AOI."""
import unittest

from tools.live_sinop_semantic_sar import (build_report_header, summarize_sample_box,
                                           summarize_crop_forecast)


class SinopLiveScopeTests(unittest.TestCase):
    def test_report_labels_test_box_and_unprocessed_farm_reference(self):
        report = build_report_header(1084.73, started_at="fixture")
        self.assertEqual(report["sample_box_area_ha"], 1084.73)
        self.assertEqual(report["reference_farm_area_ha_not_processed"], 1459.91)
        self.assertIn("NOT original KML", report["scope"])
        self.assertNotIn("aoi_area_ha", report)
        self.assertNotIn("original_farm_area_ha", report)

    def test_sample_box_summary_computes_total_and_unclassified_without_old_keys(self):
        result = summarize_sample_box(10.0, {"forest": 4.0, "crop": 2.5})
        self.assertEqual(result["sample_box_polygon_area_ha"], 6.5)
        self.assertEqual(result["sample_box_unclassified_area_ha"], 3.5)
        self.assertEqual(result["sample_box_polygon_area_by_class_ha"],
                         {"forest": 4.0, "crop": 2.5})
        self.assertNotIn("polygon_area_ha", result)

    def test_live_forecast_status_uses_model_audit_not_scene_presence(self):
        from datetime import date
        report = summarize_crop_forecast({"crops": {
            "Soja": {"forecast_status": "ok",
                     "crop_specific_vigor": {"status":"N/D","reason":"sem cena atual"},
                     "forecast_inputs": {"vigor_model_audit": {
                         "used_in_yield_distribution": False,
                         "reason": "sem cena contemporânea"}},
                     "forecast_render_status": "OK"},
            "Milho": {"forecast_status": "ok",
                      "forecast_inputs": {"vigor_model_audit": {
                          "used_in_yield_distribution": True}},
                      "forecast_render_status": "OK"}}},
            ["linha"], as_of=date(2026, 11, 18), current_mask=False)
        self.assertEqual(report["status"], "VIGOR_CONFIRMADO_NA_DISTRIBUICAO")
        self.assertFalse(report["mask_is_current_semantic_classification"])
        self.assertEqual(report["crops"]["Soja"]["vigor_model_audit"]["reason"],
                         "sem cena contemporânea")
        self.assertEqual(report["crops"]["Soja"]["crop_specific_vigor"]["reason"],
                         "sem cena atual")

    def test_live_forecast_never_claims_vigor_without_model_confirmation(self):
        from datetime import date
        report = summarize_crop_forecast({"crops": {
            "Soja": {"forecast_status": "ok", "forecast_render_status": "OK",
                     "vigor_model_audit": {"used_in_yield_distribution": False}}}},
            [], as_of=date(2026, 11, 18))
        self.assertEqual(report["status"], "PREVISAO_EXECUTADA_SEM_VIGOR_CONFIRMADO")


if __name__ == "__main__":
    unittest.main()
