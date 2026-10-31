"""Regression tests: carbon summary must not equate missing land-cover evidence with absence of native cover."""
import unittest
from executive_carbon_report import executive_carbon_lines, uncertainty_for_pool


def pt(value):
    return f"{float(value):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


class CarbonPresentationRegression(unittest.TestCase):
    def test_zero_spatial_sd_does_not_imply_zero_prediction_error(self):
        result=uncertainty_for_pool({"tc":84.4,"spatial_sd_tc_ha":0.0})
        self.assertEqual(result["absolute_tc_ha"],0.0)
        self.assertIn("NÃO significa incerteza de predição zero",result["kind"])

    def test_unknown_cover_never_claims_zero_natural_cover(self):
        report={"area_aoi_ha":1290.69, "native_area_ha":0, "unknown_cover_area_ha":1290.69,
                "strata":[], "known_total_tc":None}
        result="\n".join(executive_carbon_lines(report,pt))
        self.assertIn("Cobertura não confirmada: 1.290,69 ha", result)
        self.assertIn("N/D — cobertura não integralmente verificada", result)
        self.assertIn("não equivale a zero de vegetação nativa", result)

    def test_three_units_and_provenance_of_uncertainty_kind(self):
        report={"area_aoi_ha":1, "native_area_ha":1, "unknown_cover_area_ha":0,
                "known_total_tc":20, "complete":False,
                "strata":[{"class_name":"Floresta Ombrófila Densa","area_ha":1,
                  "components":[{"parametro":"Biomassa aérea","tc":20,"range_tc_ha":[18,22]},
                                {"parametro":"Solo 0–30 cm","tc":15}]}]}
        result="\n".join(executive_carbon_lines(report,pt))
        self.assertIn("±", "±")
        self.assertIn("2,00 tC/ha | 7,33 tCO₂e/ha | 10,00%",result)
        self.assertIn("N/D tC/ha | N/D tCO₂e/ha | N/D %",result)
        self.assertIn("Natureza:",result)


if __name__ == "__main__":
    unittest.main()
