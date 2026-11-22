"""Inventory contingency requires affirmative, complete scene-absence evidence."""
import unittest
from ifn_carbon_fallback import estimate_inventory_carbon_scenario


class ConditionalInventoryTests(unittest.TestCase):
    def test_technical_failure_cannot_unlock_inventory_contingency(self):
        result = estimate_inventory_carbon_scenario(
            biome="Cerrado", physiognomy="Formação Savânica",
            area_ha=10.0,
            sar_result={"status": "ERRO_TECNICO_LEITURA_SAR"},
            conditional_only=True)
        self.assertEqual(result.get("status"), "BLOQUEADO")

    def test_legacy_conditional_flag_cannot_bypass_absence_certificate(self):
        result = estimate_inventory_carbon_scenario(
            biome="Cerrado", physiognomy="Formação Savânica",
            area_ha=10.0,
            sar_result={"status": "ERRO_TECNICO_LEITURA_SAR"},
            conditional_only=True)
        self.assertEqual(result.get("status"), "BLOQUEADO")

    def test_default_gate_still_blocks_unresolved_sar(self):
        result = estimate_inventory_carbon_scenario(
            biome="Cerrado", physiognomy="Formação Savânica",
            area_ha=10.0,
            sar_result={"status": "ERRO_TECNICO_LEITURA_SAR"})
        self.assertEqual(result.get("status"), "BLOQUEADO")


if __name__ == "__main__":
    unittest.main()
