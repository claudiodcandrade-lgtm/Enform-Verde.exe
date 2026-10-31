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
