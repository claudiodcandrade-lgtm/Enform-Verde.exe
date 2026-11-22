"""Synthetic geometry regressions: NOT independent IFN/IBGE validation."""
import unittest
from shapely.geometry import box
from tools.ifn_ibge_spatial_sensitivity import IbgeSensitivity


class IFNIBGESensitivityTests(unittest.TestCase):
    def test_interior_scenarios_do_not_validate_field_position(self):
        engine = IbgeSensitivity([box(-50, -16, -48, -14)], ["Savana"])
        row = engine.evaluate(-49, -15)
        self.assertEqual(row["legenda_1_no_centroide_publicado"], "Savana")
        self.assertEqual(row["estabilidade_geometrica_cenarios_m"],
                         {"0": True, "250": True, "1000": True})
        self.assertFalse(row["tipologia_campo_ibge_validada"])
        self.assertFalse(row["par_sar_validado"])
        self.assertEqual(row["erro_posicional_m"], "N/D")

    def test_near_boundary_fails_250_and_1000_m(self):
        engine = IbgeSensitivity([box(-50, -16, -49, -14),
                                  box(-49, -16, -48, -14)], ["Savana", "Floresta"])
        row = engine.evaluate(-49.001, -15)
        self.assertEqual(row["legenda_1_no_centroide_publicado"], "Savana")
        self.assertFalse(row["estabilidade_geometrica_cenarios_m"]["250"])
        self.assertFalse(row["estabilidade_geometrica_cenarios_m"]["1000"])

    def test_gap_fails_even_when_both_sides_same_class(self):
        engine = IbgeSensitivity([box(-50, -16, -49.0005, -14),
                                  box(-49, -16, -48, -14)], ["Savana", "Savana"])
        self.assertFalse(engine.evaluate(-49.001, -15)["estabilidade_geometrica_cenarios_m"]["250"])

    def test_overlap_of_different_legends_fails_closed(self):
        engine = IbgeSensitivity([box(-50, -16, -48, -14),
                                  box(-49.5, -16, -48, -14)], ["Savana", "Floresta"])
        row = engine.evaluate(-49, -15)
        self.assertEqual(row["legenda_1_no_centroide_publicado"], "N/D")
        self.assertFalse(row["estabilidade_geometrica_cenarios_m"]["0"])

    def test_transfer_and_sar_always_unvalidated(self):
        row = IbgeSensitivity([box(-50, -16, -48, -14)], ["Savana"]).evaluate(-49, -15)
        self.assertFalse(row["posicao_campo_verificada"])
        self.assertFalse(row["homologado"])
        self.assertEqual(row["erro_transferencia"], "N/D")

    def test_invalid_polygon_and_placeholder_centroid_rejected(self):
        with self.assertRaises(ValueError):
            IbgeSensitivity([box(-50, -16, -48, -14)], [""])
        with self.assertRaises(ValueError):
            IbgeSensitivity([box(-50, -16, -48, -14)], ["Savana"]).evaluate(0, 0)


if __name__ == "__main__":
    unittest.main()


class IBGEQuarantineTests(unittest.TestCase):
    def test_missing_legend_blocks_instead_of_fabricating_class(self):
        from tools.ifn_ibge_spatial_sensitivity import sanitize_official_ibge
        geometries, names, qc = sanitize_official_ibge([box(-50, -16, -48, -14)], [None])
        self.assertEqual(names, ["N/D"])
        self.assertEqual(qc["missing_legenda_1_quarantined"], 1)
        row = IbgeSensitivity(geometries, names).evaluate(-49, -15)
        self.assertEqual(row["legenda_1_no_centroide_publicado"], "N/D")
        self.assertFalse(row["estabilidade_geometrica_cenarios_m"]["250"])

    def test_invalid_polygon_quarantined_after_geometric_repair(self):
        from shapely.geometry import Polygon
        from tools.ifn_ibge_spatial_sensitivity import sanitize_official_ibge
        bowtie = Polygon([(-50, -16), (-48, -14), (-50, -14), (-48, -16)])
        self.assertFalse(bowtie.is_valid)
        geoms, names, qc = sanitize_official_ibge([bowtie], ["Savana"])
        self.assertEqual(names, ["N/D"])
        self.assertEqual(qc["invalid_geometry_quarantined"], 1)
        self.assertTrue(geoms[0].is_valid)

    def test_missing_geometry_explicitly_counted(self):
        from tools.ifn_ibge_spatial_sensitivity import sanitize_official_ibge
        geoms, names, qc = sanitize_official_ibge(
            [None, box(-50, -16, -48, -14)], ["Savana", "Floresta"])
        self.assertEqual(len(geoms), 1)
        self.assertEqual(names, ["Floresta"])
        self.assertEqual(qc["missing_or_empty_geometry"], 1)


class IFNIBGESourceTypologyCrossTabTests(unittest.TestCase):
    """Synthetic physical-UA counts; no observational validation claim."""

    def test_physical_ua_cross_tab_and_nd_are_descriptive(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_crosswalk
        rows = [
            {"uf": "GO", "ua": str(i), "bioma_declarado": "Cerrado",
             "tipologia_origem_declarada": "Savana",
             "ibge_legenda_1_centroide_publicado_nao_validado": legend}
            for i, legend in enumerate(("Savana", "Floresta", "N/D"), 1)
        ]
        result = summarize_source_typology_ibge_crosswalk(rows)
        self.assertEqual(sum(x["ua_fisicas"] for x in
            result["source_typology_ibge_cross_tab_published_centroid_UNVALIDATED"]), 3)
        summary = result["source_typology_ibge_by_biome_UNVALIDATED"]["Cerrado"]
        self.assertEqual(summary["published_centroid_ibge_label_present"], 2)
        self.assertEqual(summary["published_centroid_ibge_label_ND"], 1)
        self.assertEqual(summary["source_typologies_with_multiple_published_ibge_legends"], 1)
        self.assertFalse(result["source_typology_ibge_independently_validated"])
        self.assertIsNone(result["source_typology_ibge_transfer_error"])

    def test_duplicate_physical_ua_rejected(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_crosswalk
        row = {"uf": "GO", "ua": "1", "bioma_declarado": "Cerrado",
               "tipologia_origem_declarada": "Savana",
               "ibge_legenda_1_centroide_publicado_nao_validado": "Savana"}
        with self.assertRaisesRegex(ValueError, "duplicate IFN physical"):
            summarize_source_typology_ibge_crosswalk([row, dict(row)])

    def test_missing_source_typology_fails_closed(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_crosswalk
        row = {"uf": "GO", "ua": "1", "bioma_declarado": "Cerrado",
               "tipologia_origem_declarada": "",
               "ibge_legenda_1_centroide_publicado_nao_validado": "Savana"}
        with self.assertRaisesRegex(ValueError, "missing IFN"):
            summarize_source_typology_ibge_crosswalk([row])



class IFNIBGEStableScenarioCrossTabTests(unittest.TestCase):
    """Only descriptive scenario robustness; never a measured error or CI."""

    def make_row(self, ua, legend="Savana", flags=("true", "true", "false")):
        return {"uf": "GO", "ua": str(ua), "bioma_declarado": "Cerrado",
                "tipologia_origem_declarada": "Savana",
                "ibge_legenda_1_centroide_publicado_nao_validado": legend,
                **{f"estavel_cenario_{r}_m_nao_erro": v
                   for r, v in zip((0, 250, 1000), flags)}}

    def test_scenario_counts_deduplicated_and_not_validation(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_stability
        rows = [self.make_row(1, flags=("true", "true", "true")),
                self.make_row(2),
                self.make_row(3, legend="N/D", flags=("false", "false", "false"))]
        result = summarize_source_typology_ibge_stability(rows)
        summary = result["source_typology_ibge_stability_by_biome_UNVALIDATED"]["Cerrado"]
        self.assertEqual([summary[f"ua_fisicas_estaveis_cenario_{r}_m_nao_erro"]
                          for r in (0, 250, 1000)], [2, 2, 1])
        self.assertFalse(result["source_typology_ibge_scenario_stability_is_positional_accuracy"])
        self.assertFalse(result["source_typology_ibge_scenario_stability_is_field_validation"])

    def test_zero_stable_biome_retained(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_stability
        result = summarize_source_typology_ibge_stability([
            self.make_row(1, legend="N/D", flags=("false", "false", "false"))])
        self.assertEqual(result["source_typology_ibge_stability_by_biome_UNVALIDATED"]
                         ["Cerrado"]["ua_fisicas_estaveis_cenario_250_m_nao_erro"], 0)

    def test_bad_or_non_nested_flags_fail_closed(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_stability
        for flags in (("true", "false", "true"),
                      ("false", "true", "true"),
                      ("true", "missing", "false")):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                summarize_source_typology_ibge_stability([self.make_row(1, flags=flags)])
        with self.assertRaisesRegex(ValueError, "N/D IBGE"):
            summarize_source_typology_ibge_stability([
                self.make_row(1, legend="N/D", flags=("true", "true", "true"))])

    def test_duplicate_ua_rejected(self):
        from tools.ifn_ibge_spatial_sensitivity import summarize_source_typology_ibge_stability
        row = self.make_row(1)
        with self.assertRaisesRegex(ValueError, "duplicate IFN physical"):
            summarize_source_typology_ibge_stability([row, dict(row)])

    def test_same_class_overlapping_polygons_never_stable(self):
        engine = IbgeSensitivity([box(-50, -16, -48, -14),
                                  box(-49.5, -16, -48, -14)], ["Savana", "Savana"])
        result = engine.evaluate(-49, -15)
        self.assertEqual(result["legenda_1_no_centroide_publicado"], "Savana")
        self.assertEqual(result["estabilidade_geometrica_cenarios_m"],
                         {"0": False, "250": False, "1000": False})
