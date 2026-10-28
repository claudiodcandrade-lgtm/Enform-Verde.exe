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
    def test_no_direct_sorghum_bean_citrus_model_is_invented(self):
        for crop in ("sorgo","feijão","citros"):
            self.assertFalse(any(crop in m["crops"] for m in CANDIDATES))
            self.assertTrue(candidates_for_crop(crop)) # generic cropland route only
    def test_reject_sensors_absent(self):
        result=assess_external_model_transfer(candidate_id="IRRI_RIICE_2014",
            crop="arroz",sensors=("Sentinel-2",),evidence={})
        self.assertFalse(result["eligible"])
        self.assertIn("required source sensor modalities are unavailable",result["errors"])
    def test_foreign_source_not_banned_by_nationality(self):
        reference=next(m for m in CANDIDATES if m["id"]=="IRRI_RIICE_2014")
        self.assertEqual(reference["origin"],"international")
        self.assertIn("arroz",reference["crops"])
        # Candidate is accepted for screening, not pixel labeling.
        self.assertFalse(assess_external_model_transfer(candidate_id=reference["id"],
            crop="arroz",sensors=reference["sensors"],evidence={})["eligible"])

if __name__=="__main__":
    unittest.main()
