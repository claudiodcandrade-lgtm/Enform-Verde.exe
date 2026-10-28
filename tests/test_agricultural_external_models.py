import unittest
from agricultural_external_models import (
    CANDIDATES, SUPPORTED_CROPS, SOURCE_TYPES,
    candidates_for_crop, assess_external_model_transfer,
)

class InternationalModelReferenceTests(unittest.TestCase):
    def test_all_international_methods_have_traceable_sources(self):
        ids = [m["id"] for m in CANDIDATES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(m["kind"]=="doctoral_thesis" for m in CANDIDATES))
        self.assertTrue(any(m["kind"]=="masters_dissertation" for m in CANDIDATES))
        for m in CANDIDATES:
            self.assertIn(m["kind"], SOURCE_TYPES)
            self.assertTrue(m["institution"])
            self.assertTrue(m["url"].startswith("https://"))
            self.assertTrue(m["sensors"])
            self.assertTrue(set(m["crops"]) & set(SUPPORTED_CROPS))
    def test_international_methods_dont_claim_validated_brazil_deployment(self):
        for crop in SUPPORTED_CROPS:
            refs = candidates_for_crop(crop)
            self.assertTrue(refs)
            for source in refs:
                result = assess_external_model_transfer(
                    candidate_id=source["id"],crop=crop,sensors=source["sensors"],
                    evidence={})
                self.assertFalse(result["eligible"])
                self.assertEqual(result["operational_label"],"áreas cultivadas")
    def test_specific_crop_references_are_research_not_deployed_weights(self):
        for crop in ("sorgo","feijão","citros"):
            sources=[m for m in CANDIDATES if crop in m["crops"]]
            self.assertTrue(sources)
            self.assertTrue(all(not m["weights_reusable"] for m in sources))
        sorghum=[m for m in CANDIDATES if "sorgo" in m["crops"]]
        self.assertTrue(all("unverified" in ",".join(m["sensors"]) for m in sorghum))
        for crop in ("sorgo","feijão","citros"):
            self.assertFalse(any(
                assess_external_model_transfer(candidate_id=m["id"],crop=crop,
                    sensors=m["sensors"],evidence={})["eligible"]
                for m in CANDIDATES if crop in m["crops"]))
    def test_reject_sensors_absent(self):
        result=assess_external_model_transfer(candidate_id="IRRI_RIICE_2014",
            crop="arroz",sensors=("Sentinel-2",),evidence={})
        self.assertFalse(result["eligible"])
        self.assertIn("required source sensor modalities are unavailable",result["errors"])
    def test_even_complete_self_reported_evidence_is_only_preflight(self):
        # No local classifier was executed. Even plausible signed-looking
        # metadata must NOT be interpreted as a validated SAR crop map.
        evidence={
            "artifact_sha256":"a"*64,
            "model_version":"v1",
            "predictor_manifest":"S1_VH_timeseries",
            "training_institution":"IRRI",
            "target_physiognomy":"tropical lowland rice",
            "target_season":"2026",
            "independent_brazil_test":True,
            "temporal_holdout":True,
            "spatial_holdout":True,
            "precision_wilson_lower95":0.95,
            "class_precision":0.97,
            "n_independent":100
        }
        result=assess_external_model_transfer(candidate_id="NATURE_RICE_S1_2019",
            crop="arroz",sensors=("Sentinel-1",),evidence=evidence)
        self.assertTrue(result["preflight_passed"])
        self.assertFalse(result["eligible"])
        self.assertEqual(result["operational_label"],"áreas cultivadas")
        self.assertTrue(any("preflight only" in item for item in result["errors"]))

    def test_foreign_source_not_banned_by_nationality(self):
        reference=next(m for m in CANDIDATES if m["id"]=="IRRI_RIICE_2014")
        self.assertEqual(reference["origin"],"international")
        self.assertIn("arroz",reference["crops"])
        # Candidate is accepted for screening, not pixel labeling.
        self.assertFalse(assess_external_model_transfer(candidate_id=reference["id"],
            crop="arroz",sensors=reference["sensors"],evidence={})["eligible"])

if __name__=="__main__":
    unittest.main()
