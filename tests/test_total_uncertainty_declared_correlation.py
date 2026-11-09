"""Owner decision 7 = B: total uncertainty with declared correlation, never a simple sum."""
import math
import unittest

from executive_carbon_report import executive_carbon_lines


def comp(p, t, lo, hi):
    return {"parametro": p, "tc": t, "total_tc": t * 100, "quantified_area_ha": 100.0, "range_tc_ha": [lo, hi]}


def native(components, complete=True):
    known = sum(c["total_tc"] for c in components)
    return {"area_aoi_ha": 100.0, "native_area_ha": 100.0, "excluded_other_uses_ha": 0.0,
            "unknown_cover_area_ha": 0.0, "cover_completeness": "COMPLETE", "complete": complete,
            "known_total_tc": known, "strata": [{"class_name": "F", "area_ha": 100.0, "components": components}]}


class DeclaredCorrelationTotal(unittest.TestCase):
    def test_biomass_pools_correlated_litter_and_soil_independent(self):
        rows = [comp("Biomassa aérea", 60, 50, 70), comp("Biomassa subterrânea", 15, 12, 18),
                comp("Necromassa aérea", 5, 4, 6), comp("Necromassa subterrânea", 1, .8, 1.2),
                comp("Serapilheira", 3, 1, 5), comp("Solo 0–100 cm", 80, 70, 90)]
        text = "\n".join(executive_carbon_lines(native(rows), lambda x, nd=2: f"{x:.2f}"))
        k = 44 / 12
        bio = (10 + 3 + 1 + .2) * k
        expected = math.sqrt(bio ** 2 + (2 * k) ** 2 + (10 * k) ** 2)
        simple_sum = (10 + 3 + 1 + .2 + 2 + 10) * k
        total_line = next(l for l in text.splitlines() if l.startswith("| TOTAL"))
        self.assertIn(f"{expected:.2f}", total_line)
        self.assertNotIn(f"{simple_sum:.2f}", total_line)
        self.assertIn("correlação declarada", text)

    def test_missing_pool_uncertainty_keeps_total_nd(self):
        rows = [comp("Biomassa aérea", 60, 50, 70), {"parametro": "Solo 0–100 cm", "tc": 80, "total_tc": 8000,
                                                      "quantified_area_ha": 100.0}]
        text = "\n".join(executive_carbon_lines(native(rows), lambda x, nd=2: f"{x:.2f}"))
        total_line = next(l for l in text.splitlines() if l.startswith("| TOTAL"))
        self.assertIn("| N/D | N/D |", total_line)


if __name__ == "__main__":
    unittest.main()
