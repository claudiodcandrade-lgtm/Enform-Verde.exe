"""Validate presence of crop-specific model contracts, without pretending to execute solvers."""
import unittest
from crop_specific_model_registry import MODEL_REGISTRY,CURRENT_CALIBRATED_PANEL,model_contract

class TestCropSpecificRegistry(unittest.TestCase):
    def test_nine_crop_model_contracts(self):
        expected={"Soja","Milho","Sorgo","Feijão","Arroz","Cana-de-açúcar","Algodão","Café","Citros"}
        self.assertEqual(set(MODEL_REGISTRY),expected)
        for crop in expected:
            r=model_contract(crop)
            self.assertEqual(r["status"],"research_backed_not_integrated")
            self.assertTrue(r["recommended_model"] and r["source"].startswith("https://"))
            self.assertGreaterEqual(len(r["phenological_stages"]),3)
            self.assertGreaterEqual(len(r["sar_features"]),2)
            self.assertIn("não integrado",r["warning"])
    def test_only_historical_pam_panel_models_are_installed(self):
        self.assertEqual(CURRENT_CALIBRATED_PANEL,{"Soja","Milho"})
        self.assertTrue(model_contract("Soja")["existing_panel_available"])
        self.assertFalse(model_contract("Citros")["existing_panel_available"])
        self.assertEqual(model_contract("Outras")["status"],"N/D")

if __name__=="__main__":
    unittest.main()
