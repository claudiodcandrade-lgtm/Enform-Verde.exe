"""Executive report regression: regional forecast supersedes only blocked placeholders."""
import unittest
from crop_report_consistency import remove_superseded_yield_placeholders


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


if __name__ == "__main__":
    unittest.main()
