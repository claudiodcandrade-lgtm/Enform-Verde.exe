"""Regression tests for the two independent executive analyses.

Run: python -m unittest discover -s tests -p 'test_dual_dashboard.py'
"""
import unittest
from dual_executive_dashboard import render_dual_dashboard, render_cultivated_dashboard

class DashboardTests(unittest.TestCase):
    def test_separate_views_and_native_carbon(self):
        html = render_dual_dashboard(
            native_carbon={"native_area_ha": 10, "partial_total_tc": 100,
                           "compartments": [{"name": "AGB", "tc_ha": 10,
                                             "uncertainty_tc_ha": 2,
                                             "uncertainty_kind": "SD do produto"}]},
            cultivated={"fields": [{"crop": "soja", "area_ha": 3, "yield_t_ha": 4,
                                     "yield_uncertainty_t_ha": 0.5}]})
        self.assertIn('id="carbon"', html)
        self.assertIn('id="cultivos"', html)
        self.assertIn("366,67 tCO₂e", html)
        self.assertIn("±2,00 tC/ha", html)
        self.assertIn("12,00 t", html)
        self.assertIn("±0,50 t/ha", html)
        self.assertIn("1,50 t", html)
        self.assertIn("PARCIAL", html)

    def test_uncertainty_absence_visible(self):
        html = render_dual_dashboard(
            native_carbon={"native_area_ha": 2, "partial_total_tc": 5,
                           "compartments": [{"name": "Solo", "tc_ha": 2.5}]},
            cultivated={"fields": [{"crop": "arroz", "area_ha": 1}]})
        self.assertIn("Incerteza do total: NÃO QUANTIFICADA", html)
        self.assertIn("Não quantificada", html)
        self.assertIn("Não disponível", html)

    def test_escape_untrusted_labels(self):
        html = render_cultivated_dashboard({"fields": [
            {"crop": "<script>alert(1)</script>", "area_ha": 1}]})
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_negative_area_rejected(self):
        with self.assertRaises(ValueError):
            render_cultivated_dashboard({"fields": [{"area_ha": -1}]})

    def test_negative_uncertainty_rejected(self):
        with self.assertRaises(ValueError):
            render_cultivated_dashboard({"fields": [{"area_ha": 1, "yield_uncertainty_t_ha": -1}]})

if __name__ == "__main__":
    unittest.main()
