"""Any measured published classification accuracy is reportable, not an exclusion."""
import unittest
from datetime import datetime, timezone
from agricultural_diagnostic_quality import assess_diagnostic

NOW = datetime(2026,10,28,tzinfo=timezone.utc)

def check(validation, *, label="cana-de-açúcar", probabilities=None):
    return assess_diagnostic(
        acquisition_utc="2026-10-27T00:00:00Z",
        processing_ok=True,
        source_verified=True,
        model_validation={label:validation},
        probabilities=probabilities or {label:.52,"outro":.48},
        native_mask_confirmed=False,
        now=NOW)

class PublishedMeasuredAccuracyTests(unittest.TestCase):
    def test_foreign_publication_with_6538_percent_is_reportable(self):
        result=check(dict(published_validation=True,institution="IPB University",
                          publication_url="https://journal.ipb.ac.id/jika/article/view/48719",
                          metric="mean overall accuracy",published_accuracy=.6538))
        self.assertEqual(result["status"],"classificação_provisória_com_acurácia_publicada")
        self.assertAlmostEqual(result["measured_accuracy"],.6538)
        self.assertEqual(result["validation_scope"],"published_original_domain_only")
        self.assertFalse(result["native_carbon_eligible"])
        self.assertIn("não é acurácia validada",result["uncertainty_note"])

    def test_any_local_accuracy_is_accepted_even_zero(self):
        result=check(dict(independent_test=True,in_domain=True,precision=0.0,
                          recall=0.0,n_independent=2,metric="class precision"),
                     probabilities={"cana-de-açúcar":.51,"outro":.49})
        self.assertEqual(result["status"],"classificação_com_evidências")
        self.assertEqual(result["measured_accuracy"],0)
        self.assertEqual(result["sample_count"],2)

    def test_no_accuracy_evidence_is_rejected(self):
        result=check(dict(published_validation=True,institution="IPB",
                          publication_url="https://journal.ipb.ac.id/jika/article/view/48719",
                          metric="overall accuracy"))
        self.assertEqual(result["status"],"não_classificado")
        self.assertIn("Desempenho quantitativo não informado",result["reasons"])

    def test_invalid_metric_does_not_unlock_class(self):
        for bad in (float("nan"),-1,1.1):
            result=check(dict(published_validation=True,institution="IPB",
                              publication_url="https://journal.ipb.ac.id/jika/article/view/48719",
                              metric="overall accuracy",published_accuracy=bad))
            self.assertEqual(result["status"],"não_classificado")
            self.assertIn("Acurácia publicada inválida",result["reasons"])

    def test_native_carbon_not_enabled_by_foreign_published_accuracy(self):
        r=assess_diagnostic(acquisition_utc="2026-10-27T00:00:00Z",processing_ok=True,
            source_verified=True,
            model_validation={"vegetação nativa":{
                "published_validation":True,"institution":"Example Institute",
                "publication_url":"https://example.edu/article","metric":"overall accuracy",
                "published_accuracy":.55}},
            probabilities={"vegetação nativa":.55,"outro":.45},
            native_mask_confirmed=True,now=NOW)
        self.assertFalse(r["native_carbon_eligible"])
        self.assertEqual(r["validation_scope"],"published_original_domain_only")

if __name__ == "__main__":
    unittest.main()
