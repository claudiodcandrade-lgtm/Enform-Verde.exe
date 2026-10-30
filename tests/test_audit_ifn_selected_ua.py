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
