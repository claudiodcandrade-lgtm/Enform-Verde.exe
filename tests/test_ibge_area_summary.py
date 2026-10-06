import unittest
from desktop_app import ibge_area_summary_lines

class IbgeAreaSummaryTest(unittest.TestCase):
    def test_reports_physiognomy_name_and_extent_in_hectares(self):
        diagnosis = {
            "vegetacao": [
                {"campo": "legenda_1", "classes": [
                    ("Floresta Ombrófila Densa", 8705.0, 23.47),
                    ("Formação Savânica", 1200.0, 3.23),
                ]},
                {"campo": "legenda_2", "classes": [
                    ("Floresta", 8705.0, 23.47),
                    ("Savana", 1200.0, 3.23),
                ]},
            ]
        }
        text = "\n".join(ibge_area_summary_lines(diagnosis))
        self.assertIn("Fitofisionomia/região fitoecológica IBGE (legenda_1):", text)
        self.assertIn("Floresta Ombrófila Densa — 8.705,00 ha (23,47% da AOI)", text)
        self.assertIn("Tipo de cobertura vegetal IBGE (legenda_2):", text)
        self.assertIn("Floresta — 8.705,00 ha", text)
        self.assertIn("Formação Savânica — 1.200,00 ha", text)

    def test_shows_explicit_unavailable_state(self):
        lines = ibge_area_summary_lines({"vegetacao_error": "sem interseção"})
        self.assertTrue(any("não disponível — sem interseção" in line for line in lines))

if __name__ == "__main__":
    unittest.main()
