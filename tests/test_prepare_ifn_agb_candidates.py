"""No invented SAR calibration from licensed but coarsely geolocated SFB panel."""
import hashlib
import unittest

from tools.prepare_ifn_agb_candidates import prepare

HEADER = ("bioma;uf;ua;lon_pc;lat_pc;sanidade;classe_uso_da_terra;"
          "tipologia_da_vegetacao;equacoes;area_ha;agb_media_kg_por_ha;"
          "agb_variancia_por_ua\n")


def record(biome="Cerrado", uf="Goiás", ua="GO_001", eq="AGB_Chave",
           land="Savana", lon="-48,42", lat="-15,84", agb="25950,56",
           area="0,1", variance="0", typology="Savana"):
    return ";".join((biome, uf, ua, lon, lat, "Vivas", land, typology,
                     eq, area, agb, variance)) + "\n"


def run(*rows):
    raw = (HEADER + "".join(rows)).encode("utf-8")
    return prepare(raw, hashlib.sha256(raw).hexdigest())


class IFNAGBCandidateTests(unittest.TestCase):
    def test_alternative_equations_do_not_pseudoreplicate_ua(self):
        candidates, report = run(record(), record(eq="Eq.183", agb="30000"))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["agb_chave_rows"], 1)
        self.assertEqual(report["candidate_ua"], 1)
        self.assertAlmostEqual(candidates[0]["agb_mg_ha"], 25.95056)
        self.assertEqual(candidates[0]["source_equation"], "AGB_Chave")
        self.assertEqual(candidates[0]["source_agb_variancia_por_ua_uninterpreted"], 0)
        self.assertNotIn("source_variance_kg2_per_ha2", candidates[0])
        self.assertEqual(candidates[0]["sar_pair_eligible"], "false")
        self.assertEqual(candidates[0]["equation_choice_audited"], "false")
        self.assertIsNone(report["coordinate_accuracy_m"])
        self.assertFalse(report["scientific_validation"])

    def test_multiple_agb_chave_classes_exclude_whole_ua(self):
        candidates, report = run(record(), record(land="Floresta Natural"))
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["excluded_multiple_agb_chave_rows_per_ua"], 1)

    def test_unclassified_and_outside_target_biome_excluded(self):
        candidates, report = run(record(ua="GO_002", land="Não classificado"),
                                 record(biome="Pampa", uf="RS", ua="RS_001", land="Estepe"),
                                 record(ua="GO_003", land="Savana"))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["exclusions"]["excluded_unclassified_or_non_native"], 1)
        self.assertEqual(report["exclusions"]["excluded_outside_five_biomes"], 1)

    def test_invalid_geography_and_negative_biomass_excluded(self):
        candidates, report = run(record(ua="GO_001", lat="0", lon="0"),
                                 record(ua="GO_002", lat="nan"),
                                 record(ua="GO_003", agb="-1"),
                                 record(ua="GO_004"))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["exclusions"]["excluded_invalid_coordinates"], 1)
        self.assertEqual(report["exclusions"]["excluded_invalid_numeric_fields"], 1)
        self.assertEqual(report["exclusions"]["excluded_invalid_biomass_or_area"], 1)

    def test_cross_biome_conflict_does_not_pseudoreplicate_same_state_ua(self):
        candidates, report = run(
            record(biome="Cerrado", uf="GO", ua="UA_100"),
            record(biome="Mata Atlântica", uf="GO", ua="UA_100",
                   land="Floresta Natural", typology="Floresta Ombrófila Densa"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(report["unique_ua_with_agb_chave"], 1)
        self.assertEqual(report["agb_chave_biome_ua_groups"], 2)
        self.assertEqual(
            report["exclusions"]["excluded_cross_biome_ua_identity_conflict"], 2
        )
        self.assertEqual(report["candidate_ua"], 0)

    def test_nonkey_equation_biome_conflict_excludes_key_candidate(self):
        # A conflicting biome on an alternative equation is still evidence
        # of an ambiguous physical UA; counting only AGB_Chave misses it.
        candidates, report = run(
            record(biome="Cerrado", uf="GO", ua="UA_101"),
            record(biome="Mata Atlântica", uf="GO", ua="UA_101",
                   eq="Eq.183", land="Floresta Natural"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(report["agb_chave_rows"], 1)
        self.assertEqual(report["biome_identity_crosscheck_scope"],
                         "all_source_equation_rows_with_valid_UF_and_casefolded_UA")
        self.assertEqual(
            report["exclusions"]["excluded_cross_biome_ua_identity_conflict"], 1
        )

    def test_nonkey_equation_conflicting_valid_centroid_excludes_candidate(self):
        # A unique AGB_Chave is not a trustworthy physical location if another
        # equation row for the same state/UA reports a different centroid.
        candidates, report = run(
            record(uf="GO", ua="UA_201", lat="-15,84", lon="-48,42"),
            record(uf="GO", ua="UA_201", eq="Eq.183",
                   lat="-15,86", lon="-48,42"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(
            report["exclusions"]["excluded_cross_equation_coordinate_conflict"], 1
        )
        self.assertIn("no independent positional accuracy inferred",
                      report["coordinate_crosscheck_scope"])

    def test_nonkey_equation_same_centroid_does_not_exclude_candidate(self):
        candidates, report = run(
            record(uf="GO", ua="UA_202", lat="-15,84", lon="-48,42"),
            record(uf="GO", ua="UA_202", eq="Eq.183",
                   lat="-15,84", lon="-48,42"),
        )
        self.assertEqual(len(candidates), 1)
        self.assertNotIn("excluded_cross_equation_coordinate_conflict",
                         report["exclusions"])
        self.assertEqual(candidates[0]["sar_pair_eligible"], "false")

    def test_nonkey_same_biome_and_reused_ua_different_uf_remain_valid(self):
        candidates, report = run(
            record(biome="Cerrado", uf="GO", ua="UA_101"),
            record(biome="Cerrado", uf="GO", ua="UA_101", eq="Eq.183"),
            record(biome="Pantanal", uf="MS", ua="UA_101"),
            record(biome="Pantanal", uf="MS", ua="UA_101", eq="Eq.184"),
        )
        self.assertEqual(len(candidates), 2)
        self.assertEqual(report["candidate_ua"], 2)
        self.assertNotIn("excluded_cross_biome_ua_identity_conflict",
                         report["exclusions"])

    def test_invalid_uf_on_nonkey_does_not_invent_crosscheck(self):
        candidates, report = run(
            record(uf="GO", ua="UA_102"),
            record(uf="ZZ", ua="UA_102", eq="Eq.183"),
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["exclusions"]["nonkey_rows_with_invalid_uf_not_crosschecked"], 1)
        self.assertEqual(candidates[0]["scientifically_validated"], "false")

    def test_reused_ua_across_distinct_states_remains_two_units(self):
        candidates, report = run(
            record(biome="Cerrado", uf="GO", ua="UA_100"),
            record(biome="Pantanal", uf="MS", ua="UA_100",
                   land="Savana", typology="Savana"),
        )
        self.assertEqual(report["candidate_ua"], 2)
        self.assertEqual(len(candidates), 2)
        self.assertNotIn("excluded_cross_biome_ua_identity_conflict",
                         report["exclusions"])

    def test_case_aliases_on_agb_chave_are_one_physical_ua(self):
        candidates, report = run(
            record(uf="GO", ua="UA_300"),
            record(uf="Goiás", ua="ua_300"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(report["unique_ua_with_agb_chave"], 1)
        self.assertEqual(report["agb_chave_biome_ua_groups"], 1)
        self.assertEqual(report["exclusions"]["excluded_multiple_agb_chave_rows_per_ua"], 1)

    def test_nonkey_case_alias_coordinate_conflict_excludes_ua(self):
        candidates, report = run(
            record(uf="GO", ua="UA_301", lat="-15,84"),
            record(uf="Goiás", ua="ua_301", eq="Eq.183", lat="-15,86"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(report["exclusions"]["excluded_cross_equation_coordinate_conflict"], 1)

    def test_case_alias_cross_biome_conflict_excludes_physical_ua(self):
        candidates, report = run(
            record(biome="Cerrado", uf="GO", ua="UA_302"),
            record(biome="Mata Atlântica", uf="Goiás", ua="ua_302",
                   land="Floresta Natural"),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(report["unique_ua_with_agb_chave"], 1)
        self.assertEqual(report["agb_chave_biome_ua_groups"], 2)
        self.assertEqual(report["exclusions"]["excluded_cross_biome_ua_identity_conflict"], 2)

    def test_duplicate_panel_header_is_rejected(self):
        raw = (HEADER.replace("bioma;uf;ua;", "bioma;uf;uf;ua;") + record()).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate or blank CSV headers"):
            prepare(raw, hashlib.sha256(raw).hexdigest())

    def test_hash_and_schema_fail_closed(self):
        raw = (HEADER + record()).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            prepare(raw, "0" * 64)
        with self.assertRaisesRegex(ValueError, "required observational columns"):
            prepare(b"bioma;uf;ua\nCerrado;GO;GO_1\n",
                    hashlib.sha256(b"bioma;uf;ua\nCerrado;GO;GO_1\n").hexdigest())

    def test_quantization_is_diagnostic_not_positional_accuracy(self):
        candidates, report = run(record())
        self.assertEqual(report["candidate_coords_both_on_0_02_degree_grid"], 1)
        self.assertEqual(report["candidate_coords_grid_fraction"], 1)
        self.assertEqual(candidates[0]["ibge_fitophysiognomy_verified"], "false")
        self.assertFalse(report["sar_pair_eligible"])


if __name__ == "__main__":
    unittest.main()
