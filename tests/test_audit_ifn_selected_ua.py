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

    def test_state_alias_and_case_variant_ua_cannot_pseudoreplicate(self):
        conflict = ROWS + "Cerrado,Pará,ua1,Savana,eq3,300,true\\n"
        with self.assertRaisesRegex(ValueError, "repeated sampling UA"):
            self.check(conflict)

    def test_state_alias_normalized_in_stratum(self):
        alias = ROWS.replace(",PA,UA2,", ",Pará,UA2,")
        result = self.check(alias)
        self.assertEqual(len(result["strata"]), 1)
        self.assertEqual(result["strata"][0]["state"], "PA")
        self.assertEqual(result["strata"][0]["independent_ua_count"], 2)

    def test_invalid_state_is_not_an_independent_sampling_domain(self):
        with self.assertRaisesRegex(ValueError, "invalid UF identity"):
            self.check(ROWS.replace(",PA,UA2,", ",ZZ,UA2,"))

    def test_unknown_biome_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrecognized IFN biome"):
            self.check(ROWS.replace("Amazônia,PA,UA2", "BiomaInventado,PA,UA2"))

    def test_duplicate_csv_header_rejected(self):
        duplicated = ROWS.replace("bioma,uf,ua,", "bioma,uf,uf,ua,")
        with self.assertRaisesRegex(ValueError, "duplicate CSV header"):
            self.check(duplicated)

    def test_missing_uf_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing sampling domain"):
            self.check(ROWS.replace(",PA,UA2,", ",,UA2,"))

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
