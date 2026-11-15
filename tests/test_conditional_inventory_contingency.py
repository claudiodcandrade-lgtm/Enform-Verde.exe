"""Conditional inventory scenarios remain available after SAR technical outcomes."""
import unittest
from ifn_carbon_fallback import estimate_inventory_carbon_scenario


class ConditionalInventoryTests(unittest.TestCase):
    def test_conditional_scenario_does_not_claim_sar_absence(self):
        result = estimate_inventory_carbon_scenario(
            biome="Cerrado", physiognomy="Formação Savânica",
            area_ha=10.0,
            sar_result={"status": "ERRO_TECNICO_LEITURA_SAR"},
            conditional_only=True)
        self.assertNotEqual(result.get("status"), "BLOQUEADO")
        self.assertIn(result.get("status"), ("N/D", "CENARIO_CONDICIONAL_INVENTARIO_SEM_AGB_ALTURA_SAR"))

    def test_default_gate_still_blocks_unresolved_sar(self):
        result = estimate_inventory_carbon_scenario(
            biome="Cerrado", physiognomy="Formação Savânica",
            area_ha=10.0,
            sar_result={"status": "ERRO_TECNICO_LEITURA_SAR"})
        self.assertEqual(result.get("status"), "BLOQUEADO")


if __name__ == "__main__":
    unittest.main()
