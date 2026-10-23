import csv, tempfile, unittest
from pathlib import Path
from independent_sar_validation import validate_independent_predictions

class IndependentSarValidationTests(unittest.TestCase):
    def make_csv(self,d,rows):
        p=Path(d)/"heldout.csv"
        names=("unit_id","truth","prediction","calibrated_probability","reference_source",
               "reference_date","observation_date","independent_field_reference",
               "source_record_id","biome","state")
        with p.open("w",newline="",encoding="utf8") as f:
            w=csv.DictWriter(f,fieldnames=names);w.writeheader();w.writerows(rows)
        return p
    def row(self,uid,truth="Eucalipto",pred="Eucalipto",independent="true"):
        return dict(unit_id=str(uid),truth=truth,prediction=pred,calibrated_probability=".98",
          reference_source="field_fixture",reference_date="2026-01-01",
          observation_date="2026-01-01",independent_field_reference=independent,
          source_record_id=str(uid),biome="Mata Atlântica",state="MG")
    def test_50_perfect_still_fails_conservative_wilson_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make_csv(d,[self.row(i) for i in range(50)])
            r=validate_independent_predictions(p,model_sha256="synthetic",reference_url="https://example.org")
            self.assertFalse(r["gates"]["Eucalipto"]["eligible"])
            self.assertFalse(r["all_targets_validated"])
    def test_100_independent_perfect_can_pass_single_class_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make_csv(d,[self.row(i) for i in range(100)])
            r=validate_independent_predictions(p,model_sha256="synthetic",reference_url="https://example.org")
            self.assertTrue(r["gates"]["Eucalipto"]["eligible"])
            self.assertFalse(r["gates"]["Pinus"]["eligible"])
    def test_training_overlap_and_non_field_reference_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make_csv(d,[self.row("a"),self.row("b",independent="false")])
            r=validate_independent_predictions(p,model_sha256="synthetic",reference_url="https://example.org",training_unit_ids=["a"])
            self.assertEqual(r["status"],"REPROVADO_AUDITORIA")
            self.assertEqual(len(r["audit_errors"]),2)

if __name__=="__main__": unittest.main()
