"""Real-data-independent regressions for IFN Pantanal litter/necromass joins."""
import hashlib
import unittest
from tools.audit_ifn_pantanal_litter_necromass import LITTER_IDS, NECRO_ID, audit

LITTER_HEADER = "bioma;uf;ua;mun;lon_pc;lat_pc;data;Uso_terra_PC;Ponto;Profundidade\n"
NECRO_HEADER = "bioma;uf;ua;necromassa_t_por_ha\n"


def fixture(duplicate=False, land="14", other_biome="Cerrado", mismatch=False):
    litter = {}
    for sid, uf in LITTER_IDS.items():
        state = "Mato Grosso" if uf == "MT" else "Mato Grosso do Sul"
        lines = []
        for point in (1, 2, 3, 4, 5):
            lines.append(f"Pantanal;{state};{uf}_01;Mun;-57,5;-17,4;2018/01/01;{land};{point};{point - 1}\n")
        if duplicate and uf == "MT":
            lines.append(lines[-1])
        litter[sid] = (LITTER_HEADER + "".join(lines)).encode()
    necro = (NECRO_HEADER + f"{other_biome};MT;MT_01;3,5\n").encode()
    hashes = {**{k: hashlib.sha256(v).hexdigest() for k, v in litter.items()},
              NECRO_ID: hashlib.sha256(necro).hexdigest()}
    if mismatch:
        hashes[NECRO_ID] = "0" * 64
    return litter, necro, hashes


class IFNPantanalCrossSourceTests(unittest.TestCase):
    def test_no_carbon_promotion_and_cross_biome_match_not_valid(self):
        report = audit(*fixture())
        self.assertEqual(report["pantanal_litter_unique_physical_ua"], 2)
        self.assertEqual(report["pantanal_litter_depth_measurements"], 10)
        self.assertEqual(report["litter_necromass_same_physical_ua_any_biome"], 1)
        self.assertEqual(report["litter_necromass_same_physical_ua_both_pantanal"], 0)
        self.assertIsNone(report["carbon_stock_tC_ha"])
        self.assertFalse(report["scientific_validation"])

    def test_pantanal_overlap_is_only_identity_not_stock(self):
        report = audit(*fixture(other_biome="Pantanal"))
        self.assertEqual(report["litter_necromass_same_physical_ua_both_pantanal"], 1)
        self.assertIsNone(report["confidence_interval_95"])
        self.assertFalse(report["spatial_sar_pair_verified"])

    def test_duplicate_points_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate point"):
            audit(*fixture(duplicate=True))

    def test_source_checksum_required(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit(*fixture(mismatch=True))

    def test_missing_depth_and_invalid_numbers_rejected(self):
        litter, necro, hashes = fixture()
        sid = next(iter(LITTER_IDS))
        litter[sid] = litter[sid].replace(b";1;0\n", b";1;NaN\n")
        hashes[sid] = hashlib.sha256(litter[sid]).hexdigest()
        with self.assertRaisesRegex(ValueError, "numeric measurement"):
            audit(litter, necro, hashes)

    def test_ambiguous_land_code_within_ua_rejected(self):
        litter, necro, hashes = fixture()
        sid = next(iter(LITTER_IDS))
        litter[sid] = litter[sid].replace(b";14;5;4\n", b";45;5;4\n")
        hashes[sid] = hashlib.sha256(litter[sid]).hexdigest()
        with self.assertRaisesRegex(ValueError, "conflicting metadata"):
            audit(litter, necro, hashes)


    def test_necromass_invalid_biomass_cannot_create_identity_match(self):
        for invalid in ("", "-1", "NaN", "Infinity", "not_a_number"):
            with self.subTest(invalid=invalid):
                litter, necro, hashes = fixture(other_biome="Pantanal")
                necro = (NECRO_HEADER + f"Pantanal;MT;MT_01;{invalid}\n").encode()
                hashes[NECRO_ID] = hashlib.sha256(necro).hexdigest()
                report = audit(litter, necro, hashes)
                self.assertEqual(report["litter_necromass_same_physical_ua_both_pantanal"], 0)
                self.assertEqual(report["necromass_valid_rows_with_identity"], 0)
                self.assertEqual(report["necromass_quarantined_rows_by_reason"]["invalid_or_missing_biomass"], 1)
                self.assertIsNone(report["carbon_stock_tC_ha"])

    def test_missing_necromass_biome_is_quarantined(self):
        litter, necro, hashes = fixture()
        necro = (NECRO_HEADER + " ;MT;MT_01;3,5\n").encode()
        hashes[NECRO_ID] = hashlib.sha256(necro).hexdigest()
        report = audit(litter, necro, hashes)
        self.assertEqual(report["litter_necromass_same_physical_ua_any_biome"], 0)
        self.assertEqual(report["necromass_quarantined_rows_by_reason"]["missing_biome"], 1)

    def test_zero_necromass_is_valid_identity_only_not_stock(self):
        litter, necro, hashes = fixture(other_biome="Pantanal")
        necro = (NECRO_HEADER + "Pantanal;MT;MT_01;0\n").encode()
        hashes[NECRO_ID] = hashlib.sha256(necro).hexdigest()
        report = audit(litter, necro, hashes)
        self.assertEqual(report["litter_necromass_same_physical_ua_both_pantanal"], 1)
        self.assertEqual(report["necromass_valid_rows_with_identity"], 1)
        self.assertEqual(report["necromass_quarantined_rows_by_reason"], {})
        self.assertIsNone(report["carbon_stock_tC_ha"])


if __name__ == "__main__":
    unittest.main()
