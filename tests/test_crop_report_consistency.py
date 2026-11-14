"""Executive report regression: regional forecast supersedes only blocked placeholders."""
import unittest
from crop_report_consistency import (remove_superseded_yield_placeholders, current_crop_area_by_semantic_sar,
                                    experimental_seasonal_sar_classes,
                                    executive_cover_distribution_lines)


class SinopExecutiveConsistencyTest(unittest.TestCase):
    def test_superseded_inside_multiline_chunk(self):
        base = ("PAINEL EXECUTIVO — PREVISÃO DE SAFRAS\n"
                "Idade provável da lavoura: INDISPONÍVEL — sem SAR validado\n"
                "Produtividade provável: BLOQUEADA — modelo insuficiente\n"
                "Produção provável: INDISPONÍVEL — sem área definida\n"
                "Carbono nativo: calculado separadamente\n")
        after = remove_superseded_yield_placeholders([base, "PAINEL EXECUTIVO — METEOROLOGIA"])
        joined = "\n".join(after)
        self.assertNotIn("Produtividade provável: BLOQUEADA", joined)
        self.assertNotIn("Produção provável: INDISPONÍVEL", joined)
        self.assertIn("Idade provável da lavoura: INDISPONÍVEL", joined)
        self.assertIn("Carbono nativo", joined)
        self.assertIn("METEOROLOGIA", joined)

    def test_preserves_valid_yield_results(self):
        text = "Produtividade provável: ESTIMATIVA EXPERIMENTAL 3,82 t/ha\n"
        self.assertEqual(remove_superseded_yield_placeholders([text]), [text])

    def test_removes_superseded_new_productivity_headline_too(self):
        text = "Produtividade estimada no momento dessa análise: BLOQUEADA — modelo insuficiente\n"
        self.assertEqual(remove_superseded_yield_placeholders([text]), [""])


class ExecutiveCoverDistributionTests(unittest.TestCase):
    def test_every_disjoint_cover_class_has_area_percent_and_reconciliation(self):
        land={"classes":[
            {"class_name":"Lavoura de Soja","area_ha":40,"area_pct":40,"source":"SAR_VALIDADO"},
            {"class_name":"Vegetação nativa","area_ha":50,"area_pct":50,"source":"SAR_VALIDADO"},
            {"class_name":"Não classificado","area_ha":10,"area_pct":10,"source":"SEM_COBERTURA"}]}
        lines=executive_cover_distribution_lines(land,100,lambda x,nd=2:f"{x:.{nd}f}")
        joined="\n".join(lines)
        for label in ("Lavoura de Soja","Vegetação nativa","Não classificado"):
            self.assertIn(label,joined)
        for value in ("40.00 ha (40.00% da AOI)","50.00 ha (50.00% da AOI)","10.00 ha (10.00% da AOI)"):
            self.assertIn(value,joined)
        self.assertIn("100.00 ha; AOI 100.00 ha; diferença 0.00 ha",joined)

    def test_no_classes_stays_nd_instead_of_zero(self):
        self.assertIn("N/D",executive_cover_distribution_lines({},100,lambda x,nd=2:f"{x:.{nd}f}")[0])


class CurrentCropAreaEvidenceTests(unittest.TestCase):
    def test_missing_sar_classifier_is_not_zero_crop_area(self):
        self.assertEqual(current_crop_area_by_semantic_sar(
            {"status":"N/D_SEM_COBERTURA_SAR","classes":[]}), (None,None))

    def test_eligible_empty_crop_mask_is_measured_zero(self):
        self.assertEqual(current_crop_area_by_semantic_sar(
            {"status":"SAR_ELEGIVEL","classes":[]}), (0.0,0.0))

    def test_experimental_real_pixel_classes_are_preserved_as_seasonal_not_current(self):
        land={"status":"N/D_SEM_COBERTURA_SAR",
              "sar_classifier_lemplus":{"status":"SAR_CLASSIFICADOR_EXPERIMENTAL",
                  "season":"2025/2026","model_id":"ENFORM_SAR_BRASIL_RF_V2",
                  "model_sha256":"abc","pixels":1692,"scenes_used":30,
                  "landcover_overall_accuracy":0.921,
                  "landcover_overall_accuracy_wilson95":[0.90,0.94]},
              "classes":[
                  {"class_name":"Lavoura de Soja","area_ha":325.73,"source":"SAR_EXPERIMENTAL_MODELO"},
                  {"class_name":"Floresta nativa","area_ha":279.72,"source":"SAR_EXPERIMENTAL_MODELO"},
                  {"class_name":"Agricultura histórica","area_ha":8,"source":"MAPBIOMAS"}]}
        result=experimental_seasonal_sar_classes(land)
        self.assertEqual(result["season"],"2025/2026")
        self.assertEqual(result["pixels"],1692)
        self.assertEqual(sum(x["area_ha"] for x in result["classes"]),605.45)
        self.assertEqual(result["area_uncertainty"],"Estimativa com incerteza não mensurada")
        self.assertEqual(current_crop_area_by_semantic_sar(land),(None,None))

    def test_experimental_seasonal_result_requires_classifier_audit_and_sar_source(self):
        self.assertIsNone(experimental_seasonal_sar_classes({
            "sar_classifier_lemplus":{"status":"ERRO_TECNICO"},
            "classes":[{"class_name":"Soja","area_ha":10,"source":"SAR_EXPERIMENTAL_MODELO"}]}))
        self.assertIsNone(experimental_seasonal_sar_classes({
            "sar_classifier_lemplus":{"status":"SAR_CLASSIFICADOR_EXPERIMENTAL"},
            "classes":[{"class_name":"Soja","area_ha":10,"source":"MAPBIOMAS"}]}))


if __name__ == "__main__":
    unittest.main()
