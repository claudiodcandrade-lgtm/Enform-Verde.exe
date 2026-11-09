"""Executive report regression: regional forecast supersedes only blocked placeholders."""
import unittest
from crop_report_consistency import (remove_superseded_yield_placeholders, current_crop_area_by_semantic_sar)


class SinopExecutiveConsistencyTest(unittest.TestCase):
    def test_superseded_inside_multiline_chunk(self):
        base = ("PAINEL EXECUTIVO — PREVISÃO DE SAFRAS\n"
                "Idade provável da lavoura: INDISPONÍVEL — sem SAR validado\n"
                "Produtividade provável: BLOQUEADA — modelo insuficiente\n"
                "Produção provável: INDISPONÍVEL — sem área definida\n"
                "Carbono nativo: calculado separadamente\n")
        after = remove_superseded_yield_placeholders([base, "PAINEL EXECUTIVO — METEOROLOGIA"])
        joined = "\n".join(after)
        self.assertNotIn("Produtividade provável: BLOQUEADA", joined)
        self.assertNotIn("Produção provável: INDISPONÍVEL", joined)
        self.assertIn("Idade provável da lavoura: INDISPONÍVEL", joined)
        self.assertIn("Carbono nativo", joined)
        self.assertIn("METEOROLOGIA", joined)

    def test_preserves_valid_yield_results(self):
        text = "Produtividade provável: ESTIMATIVA EXPERIMENTAL 3,82 t/ha\n"
        self.assertEqual(remove_superseded_yield_placeholders([text]), [text])


class CurrentCropAreaEvidenceTests(unittest.TestCase):
    def test_missing_sar_classifier_is_not_zero_crop_area(self):
        self.assertEqual(current_crop_area_by_semantic_sar(
            {"status":"N/D_SEM_COBERTURA_SAR","classes":[]}), (None,None))

    def test_eligible_empty_crop_mask_is_measured_zero(self):
        self.assertEqual(current_crop_area_by_semantic_sar(
            {"status":"SAR_ELEGIVEL","classes":[]}), (0.0,0.0))


if __name__ == "__main__":
    unittest.main()
