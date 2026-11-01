"""Fail-closed joins of independent SFB IFN observations, not SAR validation."""
import hashlib
import unittest
import json
import tempfile
from pathlib import Path

from tools.prepare_ifn_necromass_candidates import prepare, sources_from_download_audit

NECRO_HEADER = "bioma;uf;ua;n_transectos;cod_classe_uso_da_terra;necromassa_t_por_ha\n"
BIO_HEADER = "bioma;uf;ua;sanidade;classe_uso_da_terra;tipologia_da_vegetacao;equacoes;lon_pc;lat_pc\n"


def necro(biome="Cerrado", uf="Goiás", ua="GO_001", value="15,5", transects="2", code="14"):
    return ";".join((biome, uf, ua, transects, code, value)) + "\n"


def bio(biome="Cerrado", uf="GO", ua="GO_001", typology="Savana", land="Savana", eq="AGB_Chave", lon="-48,4"):
    return ";".join((biome, uf, ua, "Vivas", land, typology, eq, lon, "-15,8")) + "\n"


def run(necros, bios):
    n = (NECRO_HEADER + "".join(necros)).encode("utf-8")
    b = (BIO_HEADER + "".join(bios)).encode("utf-8")
    return prepare(n, b, hashlib.sha256(n).hexdigest(), hashlib.sha256(b).hexdigest())


class IFNNecromassCandidateTests(unittest.TestCase):
    def test_ua_join_does_not_mislabel_biomass_as_carbon_or_sar(self):
        candidates, report = run([necro()], [bio(), bio(eq="Eq.183")])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["uf"], "GO")
        self.assertEqual(candidates[0]["necromass_biomass_t_ha"], 15.5)
        self.assertEqual(candidates[0]["necromass_carbon_tC_ha"], None)
        self.assertFalse(candidates[0]["deadwood_transect_land_crosswalk_verified"])
        self.assertFalse(candidates[0]["sar_pair_eligible"])
        self.assertEqual(candidates[0]["source_n_transectos_uninterpreted"], "2")
        self.assertNotIn("transects_reported", candidates[0])
        self.assertFalse(report["land_code_dictionary_version_compatibility_verified"])
        self.assertFalse(report["scientific_validation"])
        self.assertIsNone(report["uncertainty_tC_ha"])

    def test_two_typologies_in_one_physical_ua_quarantined(self):
        candidates, report = run([necro()], [bio(), bio(typology="Floresta Ombrófila Densa", eq="Eq.183")])
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["ambiguous_biomass_ua_metadata"], 1)

    def test_unicode_alias_and_duplicate_necromass_not_independent(self):
        candidates, report = run([necro(), necro(uf="GO", ua="ＧＯ_００１")], [bio()])
        self.assertEqual(candidates, [])
        self.assertEqual(report["necromass_unique_physical_ua"], 1)
        self.assertEqual(report["exclusions"]["duplicate_necromass_physical_ua"], 1)

    def test_invalid_numeric_and_non_native_rejected(self):
        candidates, report = run([necro(value="nan"), necro(ua="GO_002")],
                                 [bio(), bio(ua="GO_002", land="Pastagem")])
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["invalid_necromass_measurement_or_transects"], 1)
        self.assertEqual(report["exclusions"]["not_unambiguously_native_living_tree_metadata"], 1)

    def test_biome_mismatch_and_outside_five_biomes(self):
        candidates, report = run([necro(), necro(biome="Pampa", uf="RS", ua="RS_01")],
                                 [bio(biome="Amazônia"), bio(biome="Pampa", uf="RS", ua="RS_01")])
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["biome_mismatch"], 1)
        self.assertEqual(report["exclusions"]["outside_five_target_biomes"], 1)

    def test_checksum_and_duplicate_headers_fail_closed(self):
        n = (NECRO_HEADER + necro()).encode()
        b = (BIO_HEADER + bio()).encode()
        with self.assertRaisesRegex(ValueError, "SHA256"):
            prepare(n, b, "0" * 64, hashlib.sha256(b).hexdigest())
        duplicated = (BIO_HEADER.replace("bioma;uf;", "bioma;uf;uf;") + bio()).encode()
        with self.assertRaisesRegex(ValueError, "duplicate or blank headers"):
            prepare(n, duplicated, hashlib.sha256(n).hexdigest(), hashlib.sha256(duplicated).hexdigest())

    def test_field_code_prevents_planted_forest_and_pasture_promotion(self):
        candidates, report = run([necro(code="19"), necro(ua="GO_002", code="45"),
                                  necro(ua="GO_003", code="")],
                                 [bio(), bio(ua="GO_002"), bio(ua="GO_003")])
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["planted_or_agricultural_necromass_land_code"], 2)
        self.assertEqual(report["exclusions"]["missing_necromass_land_code"], 1)

    def test_forest_code_requires_compatible_tree_land_class(self):
        candidates, report = run([necro(code="111"), necro(ua="GO_002", code="111")],
                                 [bio(), bio(ua="GO_002", land="Floresta Natural")])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["exclusions"]["tree_land_class_incompatible_with_necromass_code"], 1)
        self.assertEqual(candidates[0]["source_necromass_land_code"], "111")

    def test_natural_nonforest_code_is_not_promoted_as_forest(self):
        candidates, report = run([necro(code="31")], [bio()])
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["natural_nonforest_code_needs_separate_domain"], 1)

    def test_download_audit_source_filenames_and_hashes_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.json"
            audit = {"resources": [
                {"id": source_id, "status": "downloaded_unvalidated",
                 "local_file": source_id + ".csv", "sha256": "a" * 64}
                for source_id in ("ifn_painel_necromassa_t_ha_2026", "ifn_painel_biomassa_2026")
            ]}
            audit_path.write_text(json.dumps(audit), encoding="utf-8")
            resolved = sources_from_download_audit(audit_path, directory)
            self.assertEqual(len(resolved), 2)
            self.assertEqual(resolved[0][0].name, "ifn_painel_necromassa_t_ha_2026.csv")
            audit["resources"][0]["local_file"] = "../outside.csv"
            audit_path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete or unsafe"):
                sources_from_download_audit(audit_path, directory)

    def test_same_ua_different_states_remains_distinct(self):
        candidates, report = run([necro(ua="UA_1"), necro(uf="Mato Grosso", ua="UA_1")],
                                 [bio(ua="UA_1"), bio(uf="MT", ua="UA_1")])
        self.assertEqual(len(candidates), 2)
        self.assertEqual(report["candidate_ua"], 2)


if __name__ == "__main__":
    unittest.main()
