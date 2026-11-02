"""Synthetic regressions for IFN panel coverage screening (never homologation)."""
import hashlib
import unittest
from tools.audit_ifn_panel_biome_coverage import SOURCES, audit

HEADER = "bioma;uf;lon_pc;lat_pc;ua;n_subunidades;sanidade;classe_uso_da_terra;tipologia_da_vegetacao;equacoes;area_ha;agb_media_kg_por_ha;agb_variancia_por_ua;valor_r\n"

def line(biome="Cerrado", uf="GO", ua="GO_1", typology="Savana", equation="Eq.1", agb="150,5", lon="-48,0", lat="-15,0"):
    return ";".join((biome, uf, lon, lat, ua, "1", "Vivas", "Savana", typology,
                     equation, "0,4", agb, "0", "0,56")) + "\n"

def fixture(living=None, dead=None):
    living = HEADER + (living if living is not None else line() + line(equation="Eq.2"))
    dead = HEADER + (dead if dead is not None else line(equation="Eq.dead"))
    raw = dict(zip(SOURCES, (living.encode(), dead.encode())))
    return raw, {key: hashlib.sha256(value).hexdigest() for key, value in raw.items()}

class PanelCoverageTests(unittest.TestCase):
    def test_equation_rows_not_counted_as_independent_ua(self):
        report = audit(*fixture())
        living = report["panel_data"]["ifn_painel_biomassa_2026"]
        self.assertEqual(living["row_count"], 2)
        self.assertEqual(living["unique_physical_ua_count"], 1)
        self.assertEqual(living["ua_with_multiple_equation_labels"], 1)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["physical_ua_overlap_between_panels"], 1)
        self.assertIsNone(report["carbon_stock_tC_ha"])
        self.assertFalse(report["scientific_validation"])

    def test_missing_pantanal_is_not_zero_biomass(self):
        report = audit(*fixture())
        self.assertFalse(report["target_biome_coverage"]["Pantanal"]["living_tree_panel_present"])
        self.assertFalse(report["target_biome_coverage"]["Pantanal"]["standing_dead_panel_present"])
        self.assertIsNone(report["confidence_interval_95"])

    def test_pantanal_rows_still_not_validation(self):
        report = audit(*fixture(living=line(biome="Pantanal", uf="MT", ua="MT_99"),
                                dead=line(biome="Pantanal", uf="MT", ua="MT_99")))
        self.assertTrue(report["target_biome_coverage"]["Pantanal"]["living_tree_panel_present"])
        self.assertFalse(report["target_biome_coverage"]["Pantanal"]["independent_validation"])
        self.assertFalse(report["sar_plot_pixel_validation"])

    def test_repeated_ua_across_biomes_not_two_independent_units(self):
        report = audit(*fixture(living=line() + line(biome="Caatinga")))
        living = report["panel_data"]["ifn_painel_biomassa_2026"]
        self.assertEqual(living["unique_physical_ua_count"], 1)
        self.assertEqual(living["ua_with_conflicting_biome_labels"], 1)

    def test_centroid_concordance_does_not_claim_sar_validation(self):
        report = audit(*fixture())
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(result["overlap_ua_with_identical_reported_centroid"], 1)
        self.assertEqual(result["overlap_ua_centroid_missing_or_discordant"], 0)
        self.assertFalse(result["independent_validation"])

    def test_cross_panel_centroid_mismatch_is_explicit(self):
        report = audit(*fixture(dead=line(equation="Eq.dead", lon="-49,0")))
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(result["overlap_ua_with_identical_reported_centroid"], 0)
        self.assertEqual(result["overlap_ua_centroid_missing_or_discordant"], 1)

    def test_repeated_ua_conflicting_centroid_quarantined(self):
        report = audit(*fixture(living=line() + line(equation="Eq.2", lat="-16,0")))
        living = report["panel_data"]["ifn_painel_biomassa_2026"]
        self.assertEqual(living["ua_with_missing_or_conflicting_centroid"], 1)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["overlap_ua_with_identical_reported_centroid"], 0)

    def test_blank_centroid_not_interpreted_as_zero(self):
        report = audit(*fixture(living=line(lon="")))
        self.assertEqual(report["panel_data"]["ifn_painel_biomassa_2026"]["ua_with_missing_or_conflicting_centroid"], 1)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["overlap_ua_centroid_missing_or_discordant"], 1)

    def test_invalid_coordinate_rejected(self):
        for lon in ("181", "NaN", "not_a_number"):
            with self.subTest(lon=lon), self.assertRaisesRegex(ValueError, "invalid lon_pc"):
                audit(*fixture(living=line(lon=lon)))

    def test_malformed_or_duplicate_header_rejected(self):
        raw, sha = fixture()
        raw["ifn_painel_biomassa_2026"] = raw["ifn_painel_biomassa_2026"].replace(b"bioma;uf;", b"bioma;uf;uf;")
        sha["ifn_painel_biomassa_2026"] = hashlib.sha256(raw["ifn_painel_biomassa_2026"]).hexdigest()
        with self.assertRaisesRegex(ValueError, "duplicate or blank"):
            audit(raw, sha)

    def test_source_sha_mismatch_rejected(self):
        raw, sha = fixture()
        sha["ifn_painel_biomassa_2026"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            audit(raw, sha)

    def test_invalid_negative_biomass_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid AGB"):
            audit(*fixture(living=line(agb="-1")))

    def test_invisible_ua_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "control/format"):
            audit(*fixture(living=line(ua="GO_1\u200b")))

if __name__ == "__main__":
    unittest.main()
