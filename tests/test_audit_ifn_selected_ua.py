import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.audit_ifn_selected_ua import summarize

HEADER = "bioma,uf,ua,fitofisionomia_ibge,equacao_selecionada,agb_mg_ha,equation_choice_audited\n"
ROWS = HEADER + "Amazônia,PA,UA1,Floresta Ombrófila Densa,eq1,100,true\nAmazônia,PA,UA2,Floresta Ombrófila Densa,eq1,200,true\n"

class IFNSelectedUATests(unittest.TestCase):
    def check(self, csv, sha=None):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "selected.csv"
            data = csv.encode("utf-8")
            path.write_bytes(data)
            return summarize(path, sha or hashlib.sha256(data).hexdigest())

    def test_unique_ua_descriptive_only(self):
        result = self.check(ROWS)
        row = result["strata"][0]
        self.assertEqual(row["independent_ua_count"], 2)
        self.assertEqual(row["mean_agb_mg_ha"], 150)
        self.assertFalse(row["aoi_ci95_validated"])
        self.assertFalse(row["scientifically_validated"])

    def test_repeated_ua_rejected_even_if_equation_differs(self):
        repeated = ROWS + "Amazônia,PA,UA1,Floresta Ombrófila Densa,eq2,110,true\n"
        with self.assertRaisesRegex(ValueError, "repeated sampling UA"):
            self.check(repeated)

    def test_same_physical_ua_across_biomes_rejected(self):
        # Changing the biome does not create an independent sampling unit.
        conflict = ROWS + "Cerrado,PA,UA1,Savana,eq3,300,true\n"
        with self.assertRaisesRegex(ValueError, "conflicting biome"):
            self.check(conflict)

    def test_reused_ua_in_distinct_states_remains_distinct(self):
        other_state = ROWS + "Amazônia,AM,UA1,Floresta Ombrófila Densa,eq1,300,true\n"
        result = self.check(other_state)
        counts = sorted(row["independent_ua_count"] for row in result["strata"])
        self.assertEqual(counts, [1, 2])
        self.assertFalse(any(row["scientifically_validated"] for row in result["strata"]))

    def test_unaudited_choice_rejected(self):
        with self.assertRaisesRegex(ValueError, "selection not audited"):
            self.check(ROWS.replace(",true", ",false"))

    def test_source_integrity(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            self.check(ROWS, sha="0" * 64)

    def test_negative_agb_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            self.check(ROWS.replace(",100,true", ",-100,true"))

if __name__ == "__main__":
    unittest.main()
