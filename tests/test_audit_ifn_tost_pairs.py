import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.audit_ifn_tost_pairs import audit, pair_decision

HEADER = "bioma,tipologia,equacao_1,equacao_2,reject_intercept,reject_slope,equivalente\n"
ROWS = (HEADER + "Amazônia,FOD,A,B,True,True,Equivalente\n"
        + "Amazônia,FOD,B,C,True,True,Equivalente\n"
        + "Amazônia,FOD,A,C,False,True,Não Equivalente\n")

class IFNTOSTAuditTests(unittest.TestCase):
    def _run(self, data, sha=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tost.csv"
            contents = data.encode()
            path.write_bytes(contents)
            return audit(path, sha or hashlib.sha256(contents).hexdigest())

    def test_equivalence_not_transitive(self):
        result = self._run(ROWS)
        self.assertEqual(result["comparisons"], 3)
        self.assertEqual(pair_decision(result, "Amazônia", "FOD", "A", "B"), "equivalent_pairwise")
        self.assertEqual(pair_decision(result, "Amazônia", "FOD", "B", "C"), "equivalent_pairwise")
        self.assertEqual(pair_decision(result, "Amazônia", "FOD", "A", "C"), "not_equivalent_pairwise")
        self.assertEqual(pair_decision(result, "Cerrado", "FOD", "A", "B"), "not_assessed")

    def test_unknown_pair_is_not_equivalent(self):
        result = self._run(HEADER + "Amazônia,FOD,A,B,True,True,Equivalente\n")
        self.assertEqual(pair_decision(result, "Amazônia", "FOD", "A", "C"), "not_assessed")

    def test_mislabeled_comparison_fails(self):
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self._run(HEADER + "Amazônia,FOD,A,B,False,True,Equivalente\n")

    def test_source_digest_must_match(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            self._run(ROWS, sha="0" * 64)

    def test_conflicting_duplicate_fails(self):
        with self.assertRaisesRegex(ValueError, "contradictory"):
            self._run(ROWS + "Amazônia,FOD,B,A,False,True,Não Equivalente\n")

if __name__ == "__main__":
    unittest.main()
