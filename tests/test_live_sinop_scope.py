"""The Sinop live SAR diagnostic must not report its sample box as farm AOI."""
import unittest

from tools.live_sinop_semantic_sar import (build_report_header, summarize_sample_box,
                                           summarize_crop_forecast,
                                           summarize_height_inventory_route)


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

    def test_live_carbon_audit_separates_fh_height_from_cci_agb(self):
        row=summarize_height_inventory_route({"class_name":"Floresta","sar_details":{
            "product":"ESA CCI Biomass AGB","source":"ESA CCI AGB v7",
            "data_origin":"SAR_DERIVED_CCI","paths":["cci_agb.tif"],
            "audit":{"biomass_height":{"available":True,"pixel_read_complete":True,
                "valid_pixel_count":120,"technical_error_count":0}},
            "sar_height":{"product":"FP_FH__L2A","source":"ESA BIOMASS FH",
                "height_mean_m":24.5,"height_n_valid_pixels":120,"height_metric":"H100",
                "height_route_status":"ALTURA_SAR_PROCESSADA","paths":["fh_height.tiff"]},
            "inventory_agb_comparison":{"inventory_sources_searched":["IFN","ALL_PUBLISHED"],
                "registered_published_inventory_sources":["EMBRAPA","UFV"],
                "matched_published_inventory_sources":[]}}})
        self.assertEqual(row["height_product"],"FP_FH__L2A")
        self.assertEqual(row["height_source"],"ESA BIOMASS FH")
        self.assertEqual(row["height_paths"],["fh_height.tiff"])
        self.assertEqual(row["agb_product"],"ESA CCI Biomass AGB")
        self.assertEqual(row["agb_source"],"ESA CCI AGB v7")
        self.assertEqual(row["registered_published_inventory_sources"],["EMBRAPA","UFV"])
        self.assertEqual(row["matched_published_inventory_sources"],[])


if __name__ == "__main__":
    unittest.main()
