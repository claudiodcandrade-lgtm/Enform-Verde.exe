import unittest

from ifn_carbon_fallback import estimate_fesv_state_scenario, no_valid_sar_pixels


class IfnCarbonFallbackTests(unittest.TestCase):
    def setUp(self):
        self.no_pixels = {
            "status": "SAR_NAO_PROCESSADO",
            "audit": {"warnings": []},
            "inventory_fallback_gate": {"eligible": True},
        }

    def test_state_inventory_returns_conditional_estimate_and_descriptive_uncertainty(self):
        result = estimate_fesv_state_scenario(
            biome="Amazônia", physiognomy="Floresta Estacional Sempre-Verde Submontana",
            area_ha=1459.91, sar_result=self.no_pixels,
            centroid_lon=-55.190498, centroid_lat=-11.872667)
        self.assertEqual(result["status"], "CENARIO_CONDICIONAL_INVENTARIO_SEM_PIXELS_SAR")
        self.assertFalse(result["current_native_cover_confirmed"])
        self.assertGreaterEqual(result["inventory_n_unique_sampling_units"], 5)
        self.assertIsNotNone(result["carbon_total_tc_scenario"])
        self.assertIn("não IC95%", result["uncertainty"])
        self.assertEqual(result["estimate_label"], "estimativa com incerteza não mensurada")
        self.assertEqual(result["calculation_trace"]["selected_ua_count"],
                         result["inventory_n_unique_sampling_units"])
        self.assertAlmostEqual(result["calculation_trace"]["stock_tc_scenario"],
                               result["carbon_total_tc_scenario"])

    def test_technical_errors_and_processed_pixels_block_fallback(self):
        technical = {**self.no_pixels,
                     "audit": {"warnings": ["SELECTED_SCENES_PIXEL_READ_FAILED"]}}
        self.assertFalse(no_valid_sar_pixels(technical))
        processed = {**self.no_pixels, "audit": {"warnings": [],
                                                  "processed_without_agb": [{"source": "S1"}]}}
        self.assertFalse(no_valid_sar_pixels(processed))
        self.assertEqual(estimate_fesv_state_scenario(
            biome="Amazônia", physiognomy="Floresta Estacional Sempre-Verde",
            area_ha=10, sar_result=technical,
            centroid_lon=-55.19, centroid_lat=-11.87)["status"], "BLOQUEADO")

    def test_no_generalization_to_other_physiognomies(self):
        result = estimate_fesv_state_scenario(
            biome="Amazônia", physiognomy="Floresta Ombrófila Densa",
            area_ha=10, sar_result=self.no_pixels,
            centroid_lon=-55.19, centroid_lat=-11.87)
        self.assertEqual(result["status"], "N/D")


if __name__ == "__main__":
    unittest.main()
