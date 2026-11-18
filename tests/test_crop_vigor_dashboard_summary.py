import unittest
from pathlib import Path

from crop_vigor_dashboard_summary import crop_vigor_dashboard_lines


def ptbr(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


class CropVigorDashboardSummaryTests(unittest.TestCase):
    def test_desktop_does_not_read_audit_line_list_as_a_dictionary(self):
        source = (Path(__file__).resolve().parents[1] / "desktop_app.py").read_text(encoding="utf-8")
        start = source.index("    def _present_cultivated_monitoring(self,land):")
        end = source.index("    def query_crop_weather(self):", start)
        report_builder = source[start:end]
        self.assertRegex(report_builder, r"\baudit\s*=\s*\[")
        self.assertNotRegex(report_builder, r"\baudit\.get\s*\(")
        self.assertIn("crop_vigor_dashboard_lines(fc_audit,format_ptbr)", source[end:])

    def test_live_model_audit_is_visible_in_executive_summary(self):
        audit = {
            "crops": {
                "Soja": {
                    "forecast_inputs": {
                        "crop_mask_season": "2025/2026",
                        "experimental_current_sar_vigor_conditioned_yield": True,
                        "vigor_model_audit": {
                            "used_in_yield_distribution": True,
                            "probabilities_used": {
                                "baixo vigor": .43,
                                "vigor adequado": .21,
                                "alto vigor": .36,
                            },
                        },
                    },
                    "crop_specific_vigor": {
                        "status": "experimental",
                        "class": "baixo vigor",
                        "sample_area_ha": 8.0,
                        "sar_sample_coverage_fraction": .02456,
                        "accepted_scenes": [{
                            "acquisition_utc": "2026-11-12T09:16:48Z",
                        }],
                    },
                },
            },
        }
        lines = crop_vigor_dashboard_lines(audit, ptbr)
        self.assertEqual(len(lines), 1)
        self.assertIn("Soja: vigor baixo vigor", lines[0])
        self.assertIn("participação na distribuição PAM×clima: SIM, condicional", lines[0])
        self.assertIn("baixo vigor: 43%", lines[0])
        self.assertIn("amostra: 8,00 ha (2,46% da máscara)", lines[0])
        self.assertIn("2026-11-12T09:16:48Z", lines[0])
        self.assertIn("máscara: 2025/2026", lines[0])

    def test_classification_alone_never_claims_model_use(self):
        audit = {
            "crops": {
                "Café": {
                    "forecast_inputs": {
                        "experimental_current_sar_vigor_conditioned_yield": True,
                    },
                    "crop_specific_vigor": {
                        "status": "experimental",
                        "class": "baixo vigor",
                        "reason": None,
                    },
                },
            },
        }
        self.assertIn(
            "participação na distribuição PAM×clima: NÃO confirmada",
            crop_vigor_dashboard_lines(audit, ptbr)[0],
        )

    def test_no_crop_audit_keeps_candidate_diagnostic_visible(self):
        lines = crop_vigor_dashboard_lines({
            "current_sar_candidate_vigor": {
                "status": "N/D",
                "reason": "sem pixels válidos",
            }
        }, ptbr)
        self.assertIn("sem pixels válidos", lines[0])
        self.assertIn("uso na previsão por cultura: não confirmado", lines[0])


if __name__ == "__main__":
    unittest.main()
