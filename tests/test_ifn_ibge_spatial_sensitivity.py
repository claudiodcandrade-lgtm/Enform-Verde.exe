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
