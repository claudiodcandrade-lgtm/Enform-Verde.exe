"""Synthetic regressions for IFN panel coverage screening (never homologation)."""
import hashlib
import unittest
from tools.audit_ifn_panel_biome_coverage import SOURCES, audit

HEADER = "bioma;uf;lon_pc;lat_pc;ua;n_subunidades;sanidade;classe_uso_da_terra;tipologia_da_vegetacao;equacoes;area_ha;agb_media_kg_por_ha;agb_variancia_por_ua;valor_r\n"

def line(biome="Cerrado", uf="GO", ua="GO_1", typology="Savana", equation="Eq.1", agb="150,5", lon="-48,0", lat="-15,0", land_class="Savana"):
    return ";".join((biome, uf, lon, lat, ua, "1", "Vivas", land_class, typology,
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

    def test_same_ua_conflicting_biomes_in_both_panels_not_double_counted(self):
        living = line() + line(biome="Caatinga", equation="Eq.2")
        dead = line(equation="Dead.1") + line(biome="Caatinga", equation="Dead.2")
        report = audit(*fixture(living=living, dead=dead))
        self.assertEqual(report["physical_ua_quarantined_for_conflicting_biome_labels"], 1)
        for biome in ("Cerrado", "Caatinga"):
            result = report["target_biome_coverage"][biome]
            self.assertEqual(result["physical_ua_overlap_between_panels"], 0)
            self.assertEqual(result["overlap_ua_quarantined_for_conflicting_biome_labels"], 1)
            self.assertEqual(result["overlap_ua_with_identical_reported_centroid"], 0)
        self.assertFalse(report["scientific_validation"])

    def test_biome_disagreement_across_panels_quarantined(self):
        report = audit(*fixture(living=line(), dead=line(biome="Caatinga")))
        self.assertEqual(report["physical_ua_quarantined_for_conflicting_biome_labels"], 1)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["physical_ua_overlap_between_panels"], 0)
        self.assertEqual(report["target_biome_coverage"]["Caatinga"]["physical_ua_overlap_between_panels"], 0)
        self.assertIsNone(report["carbon_stock_tC_ha"])

    def test_unambiguous_ua_still_counted_once(self):
        report = audit(*fixture())
        self.assertEqual(report["physical_ua_quarantined_for_conflicting_biome_labels"], 0)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(report["target_biome_coverage"]["Cerrado"]["overlap_ua_quarantined_for_conflicting_biome_labels"], 0)

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

    def test_normalized_or_invisible_header_alias_rejected(self):
        # A second UF column must not shadow the true identity field even if
        # its spelling differs by case, Unicode width or invisible formatting.
        for alias in (" UF ", "ｕｆ", "u\u200bf"):
            with self.subTest(alias=alias):
                raw, sha = fixture()
                sid = "ifn_painel_biomassa_2026"
                raw[sid] = raw[sid].replace(
                    b"bioma;uf;", ("bioma;uf;" + alias + ";").encode("utf-8"))
                sha[sid] = hashlib.sha256(raw[sid]).hexdigest()
                with self.assertRaisesRegex(ValueError, "duplicate or blank"):
                    audit(raw, sha)


    def test_zero_zero_centroid_is_missing_not_concordant(self):
        # The Gulf of Guinea (0, 0) is not a Brazilian IFN plot.
        report = audit(*fixture(living=line(lon="0", lat="-0,0"),
                                dead=line(lon="0,0", lat="0")))
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(result["overlap_ua_with_identical_reported_centroid"], 0)
        self.assertEqual(result["overlap_ua_centroid_missing_or_discordant"], 1)
        for panel in report["panel_data"].values():
            self.assertEqual(panel["ua_with_zero_zero_centroid_placeholder"], 1)
            self.assertEqual(panel["ua_with_missing_or_conflicting_centroid"], 1)
        self.assertFalse(report["scientific_validation"])

    def test_one_zero_zero_panel_cannot_match_a_real_centroid(self):
        report = audit(*fixture(living=line(lon="0", lat="0"),
                                dead=line(lon="-50", lat="-5")))
        self.assertEqual(report["target_biome_coverage"]["Cerrado"][
            "overlap_ua_with_identical_reported_centroid"], 0)
        self.assertEqual(report["panel_data"]["ifn_painel_biomassa_2026"][
            "ua_with_zero_zero_centroid_placeholder"], 1)
        self.assertEqual(report["panel_data"]["ifn_painel_arvores_mortas_2026"][
            "ua_with_zero_zero_centroid_placeholder"], 0)

    def test_equatorial_brazilian_latitude_zero_is_not_a_placeholder(self):
        report = audit(*fixture(living=line(lon="-50", lat="0"),
                                dead=line(lon="-50", lat="0")))
        self.assertEqual(report["target_biome_coverage"]["Cerrado"][
            "overlap_ua_with_identical_reported_centroid"], 1)
        for panel in report["panel_data"].values():
            self.assertEqual(panel["ua_with_zero_zero_centroid_placeholder"], 0)

    def test_globally_valid_but_non_brazilian_centroid_not_concordant(self):
        # Two panels repeating the same non-Brazilian coordinate must not
        # count as verified Brazilian centroid concordance.
        report = audit(*fixture(living=line(lon="-10", lat="-15"),
                                dead=line(lon="-10", lat="-15")))
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(result["overlap_ua_with_identical_reported_centroid"], 0)
        self.assertEqual(result["overlap_ua_centroid_missing_or_discordant"], 1)
        for panel in report["panel_data"].values():
            self.assertEqual(panel["ua_with_centroid_outside_brazil_screen_envelope"], 1)
            self.assertEqual(panel["ua_with_missing_or_conflicting_centroid"], 1)
        self.assertFalse(report["scientific_validation"])

    def test_equatorial_brazilian_centroid_stays_concordant(self):
        report = audit(*fixture(living=line(lon="-60", lat="0"),
                                dead=line(lon="-60", lat="0")))
        self.assertEqual(report["target_biome_coverage"]["Cerrado"][
            "overlap_ua_with_identical_reported_centroid"], 1)
        for panel in report["panel_data"].values():
            self.assertEqual(panel["ua_with_centroid_outside_brazil_screen_envelope"], 0)

    def test_one_non_brazilian_panel_centroid_does_not_match(self):
        report = audit(*fixture(living=line(lon="-10", lat="-15"),
                                dead=line(lon="-50", lat="-15")))
        self.assertEqual(report["target_biome_coverage"]["Cerrado"][
            "overlap_ua_with_identical_reported_centroid"], 0)
        self.assertEqual(report["panel_data"]["ifn_painel_biomassa_2026"][
            "ua_with_centroid_outside_brazil_screen_envelope"], 1)
        self.assertEqual(report["panel_data"]["ifn_painel_arvores_mortas_2026"][
            "ua_with_centroid_outside_brazil_screen_envelope"], 0)

    def test_source_native_land_class_screen_remains_unvalidated(self):
        report = audit(*fixture())
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["overlap_ua_with_single_matching_source_native_land_class_provisional"], 1)
        self.assertEqual(result["overlap_ua_without_single_matching_source_native_land_class"], 0)
        self.assertFalse(result["independent_validation"])
        self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])

    def test_agricultural_source_class_not_native_candidate(self):
        report = audit(*fixture(living=line(land_class="Pastagem"),
                                dead=line(land_class="Pastagem")))
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
        self.assertEqual(result["overlap_ua_with_single_matching_source_native_land_class_provisional"], 0)
        self.assertEqual(result["overlap_ua_without_single_matching_source_native_land_class"], 1)

    def test_mixed_source_land_class_in_one_ua_not_native_candidate(self):
        report = audit(*fixture(living=line() + line(equation="Eq.2", land_class="Pastagem")))
        result = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(report["panel_data"]["ifn_painel_biomassa_2026"][
            "ua_with_missing_or_conflicting_source_land_class"], 1)
        self.assertEqual(result["overlap_ua_with_single_matching_source_native_land_class_provisional"], 0)

    def test_cross_panel_or_missing_source_land_class_not_native_candidate(self):
        for dead_class in ("Floresta Natural", ""):
            with self.subTest(dead_class=dead_class):
                report = audit(*fixture(dead=line(land_class=dead_class)))
                result = report["target_biome_coverage"]["Cerrado"]
                self.assertEqual(result["physical_ua_overlap_between_panels"], 1)
                self.assertEqual(result["overlap_ua_with_single_matching_source_native_land_class_provisional"], 0)
                self.assertIsNone(report["carbon_stock_tC_ha"])

    def test_native_source_typology_and_centroid_subset_is_only_provisional(self):
        report = audit(*fixture())
        item = report["target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 1)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 1)
        self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])
        self.assertIsNone(report["confidence_interval_95"])

    def test_mixed_typology_across_equations_is_not_crosswalk_candidate(self):
        living = line() + line(equation="Eq.2", typology="Floresta Estacional")
        item = audit(*fixture(living=living))["target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_native_land_class_provisional"], 1)
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 0)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 0)

    def test_cross_panel_typology_disagreement_is_not_crosswalk_candidate(self):
        item = audit(*fixture(dead=line(typology="Floresta Estacional")))[
            "target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 0)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 0)

    def test_source_typology_unicode_case_normalization_preserves_matching(self):
        item = audit(*fixture(dead=line(typology="ＳＡＶＡＮＡ")))[
            "target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 1)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 1)

    def test_matching_typology_but_discordant_centroid_not_geolocatable(self):
        item = audit(*fixture(dead=line(lon="-49,0")))[
            "target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 1)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 0)

    def test_matching_typology_on_pasture_is_not_native_crosswalk_candidate(self):
        item = audit(*fixture(living=line(land_class="Pastagem"),
                              dead=line(land_class="Pastagem")))[
            "target_biome_coverage"]["Cerrado"]
        self.assertEqual(item["overlap_ua_with_single_matching_source_typology_provisional"], 1)
        self.assertEqual(item["overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 0)

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


    def test_candidate_export_deduplicates_equation_rows(self):
        report, candidates = audit(*fixture(), include_candidate_rows=True)
        self.assertEqual(len(candidates), 1)
        self.assertEqual((candidates[0]["uf"], candidates[0]["ua"]), ("GO", "go_1"))
        self.assertEqual(candidates[0]["lon_pc_publicado"], "-48.0")
        self.assertEqual(candidates[0]["lat_pc_publicado"], "-15.0")
        self.assertEqual(candidates[0]["legenda_1_ibge_verificada"], "false")
        self.assertEqual(candidates[0]["par_sar_validado"], "false")
        self.assertFalse(report["scientific_validation"])

    def test_export_grid_coincidence_is_not_positional_accuracy(self):
        report, candidates = audit(*fixture(), include_candidate_rows=True)
        self.assertEqual(candidates[0]["centroide_ambas_coordenadas_na_grade_0_02_grau"], "true")
        self.assertEqual(candidates[0]["precisao_posicional_m"], "N/D")
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid"], 1)
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid_fraction"], 1.0)
        self.assertFalse(report["centroid_grid_coincidence_is_positional_accuracy"])
        self.assertIsNone(report["source_centroid_accuracy_m"])
        self.assertFalse(report["sar_plot_pixel_validation"])

    def test_export_off_grid_point_is_not_discarded_or_claimed_accurate(self):
        report, candidates = audit(*fixture(living=line(lon="-48.01"),
                                            dead=line(lon="-48.01")),
                                   include_candidate_rows=True)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["centroide_ambas_coordenadas_na_grade_0_02_grau"], "false")
        self.assertEqual(candidates[0]["precisao_posicional_m"], "N/D")
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid"], 0)
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid_fraction"], 0.0)
        self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])

    def test_grid_count_excludes_non_native_and_handles_empty_subset(self):
        report, candidates = audit(*fixture(dead=line(land_class="Pastagem")),
                                   include_candidate_rows=True)
        self.assertEqual(candidates, [])
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid"], 0)
        self.assertIsNone(report["candidate_centroids_both_coordinates_on_0_02_degree_grid_fraction"])
        self.assertEqual(report["candidate_centroids_both_coordinates_on_0_02_degree_grid_by_biome"]["Pantanal"], 0)

    def test_candidate_export_quarantines_typology_and_centroid_conflicts(self):
        for dead in (line(typology="Floresta Estacional"), line(lon="-49")):
            with self.subTest(dead=dead):
                report, candidates = audit(*fixture(dead=dead), include_candidate_rows=True)
                self.assertEqual(candidates, [])
                self.assertEqual(report["target_biome_coverage"]["Cerrado"][
                    "overlap_ua_with_native_source_class_matching_typology_and_centroid_provisional"], 0)

    def test_candidate_export_quarantines_pasture_and_biome_conflicts(self):
        for raw, sha in (
            fixture(dead=line(land_class="Pastagem")),
            fixture(living=line() + line(biome="Caatinga")),
        ):
            report, candidates = audit(raw, sha, include_candidate_rows=True)
            self.assertEqual(candidates, [])
            self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])

    def test_official_2026_metadata_documents_wgs84_not_plot_accuracy(self):
        report, candidates = audit(*fixture(), include_candidate_rows=True)
        self.assertTrue(report["source_coordinate_crs_documentation_verified"])
        self.assertEqual(report["source_coordinate_crs_declared_by_official_metadata"], "EPSG:4326")
        self.assertIn("metadados_painelbiomassacarbono", report["source_coordinate_crs_metadata_url"])
        self.assertFalse(report["source_coordinate_positional_accuracy_verified"])
        self.assertEqual(candidates[0]["crs_fonte_verificado"], "true")
        self.assertEqual(candidates[0]["crs_fonte_documentado"], "EPSG:4326")
        self.assertEqual(candidates[0]["precisao_geografica_de_campo_verificada"], "false")
        self.assertEqual(candidates[0]["precisao_posicional_m"], "N/D")
        self.assertFalse(report["sar_plot_pixel_validation"])
        self.assertIn("WGS84", report["centroid_collision_warning"])
        self.assertIn("WGS84", report["warning"])

    def test_official_panel_typology_is_secondary_inference_not_field_truth(self):
        report = audit(*fixture())
        self.assertFalse(report["source_typology_direct_field_observation_verified"])
        self.assertTrue(report["source_typology_inferred_from_secondary_evidence"])
        self.assertEqual(report["source_panel_field_years_from_metadata"], "2011-2024")
        self.assertEqual(report["source_panel_tree_dap_min_cm"], 10)
        self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])

    def test_distinct_physical_ua_sharing_published_centroid_are_flagged(self):
        living = line(ua="GO_1") + line(ua="GO_2", equation="Eq.2")
        dead = line(ua="GO_1", equation="Dead.1") + line(ua="GO_2", equation="Dead.2")
        report, candidates = audit(*fixture(living=living, dead=dead),
                                   include_candidate_rows=True)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(report["candidate_distinct_published_centroids_shared_by_multiple_ua"], 1)
        self.assertEqual(report["candidate_physical_ua_at_shared_published_centroids"], 2)
        self.assertEqual(report["candidate_physical_ua_at_shared_published_centroids_by_biome"]["Cerrado"], 2)
        self.assertEqual(report["candidate_distinct_published_centroids_with_multiple_declared_biomes"], 0)
        for candidate in candidates:
            self.assertEqual(candidate["centroide_publicado_compartilhado_entre_ua"], "true")
            self.assertEqual(candidate["numero_ua_fisicas_no_mesmo_centroide_publicado"], 2)
            self.assertEqual(candidate["precisao_posicional_m"], "N/D")
            self.assertEqual(candidate["par_sar_validado"], "false")
        self.assertFalse(report["candidate_centroid_collision_is_independent_plot_geolocation"])
        self.assertFalse(report["scientific_validation"])

    def test_distinct_candidate_centroids_not_falsely_collided(self):
        living = line(ua="GO_1") + line(ua="GO_2", lon="-48.02")
        dead = line(ua="GO_1") + line(ua="GO_2", lon="-48.02")
        report, candidates = audit(*fixture(living=living, dead=dead),
                                   include_candidate_rows=True)
        self.assertEqual(report["candidate_distinct_published_centroids_shared_by_multiple_ua"], 0)
        self.assertEqual(report["candidate_physical_ua_at_shared_published_centroids"], 0)
        self.assertEqual({x["centroide_publicado_compartilhado_entre_ua"] for x in candidates}, {"false"})
        self.assertEqual({x["numero_ua_fisicas_no_mesmo_centroide_publicado"] for x in candidates}, {1})

    def test_published_centroid_shared_across_declared_biomes_is_not_verified(self):
        living = line(ua="GO_1") + line(biome="Caatinga", uf="BA", ua="BA_2")
        dead = line(ua="GO_1") + line(biome="Caatinga", uf="BA", ua="BA_2")
        report, candidates = audit(*fixture(living=living, dead=dead),
                                   include_candidate_rows=True)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(report["candidate_distinct_published_centroids_with_multiple_declared_biomes"], 1)
        self.assertEqual(report["candidate_physical_ua_at_shared_published_centroids"], 2)
        self.assertFalse(report["ifn_panel_fitophysiognomy_ibge_spatial_crosswalk_verified"])
        self.assertFalse(report["sar_plot_pixel_validation"])

    def test_repeated_equation_rows_do_not_create_spurious_centroid_collision(self):
        report, candidates = audit(*fixture(), include_candidate_rows=True)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["candidate_distinct_published_centroids_shared_by_multiple_ua"], 0)
        self.assertEqual(candidates[0]["centroide_publicado_compartilhado_entre_ua"], "false")

    def test_candidate_export_stable_across_equation_order(self):
        a = audit(*fixture(living=line() + line(equation="Eq.2")),
                  include_candidate_rows=True)[1]
        b = audit(*fixture(living=line(equation="Eq.2") + line()),
                  include_candidate_rows=True)[1]
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main()
