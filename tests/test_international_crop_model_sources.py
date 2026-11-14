"""Ground rules for global sources and current-SAR vs historical-map precedence."""
import unittest
from international_crop_model_sources import (
    PROVIDERS, international_crop_sources, installation_diagnostic)


class InternationalSourcesTests(unittest.TestCase):
    def test_references_are_auditable_with_modalities_and_licenses(self):
        rows=international_crop_sources()
        self.assertEqual(len({p["id"] for p in rows}),len(rows))
        self.assertGreaterEqual(len(rows),5)
        self.assertEqual(rows[0]["id"],"esa_worldcereal")
        for item in rows:
            self.assertTrue(item["code_url"].startswith("https://"))
            self.assertTrue(item["training_url"].startswith("https://"))
            self.assertTrue(item["modalities"])
            self.assertTrue(item["license"])
            self.assertIs(item["crop_vocabulary_guarantee"],False)
            self.assertTrue(item["requires_independent_brazil_validation"])

    def test_european_s2_not_falsely_marked_sar_only(self):
        euro=next(item for item in PROVIDERS if item["id"]=="eurocropsml")
        self.assertEqual(euro["modalities"],("Sentinel-2",))
        self.assertEqual(euro["type"],"labelled_training_reference_only")

    def test_no_false_installed_worldcereal_or_classification(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            info=installation_diagnostic(
                environ={"ENFORM_WORLDCEREAL_CROPTYPE_HEAD":
                         str(Path(tmp)/"nonexistent.zip")}, model_dir=tmp)
            self.assertFalse(info["installed_sar_candidate_manifest"])
            self.assertFalse(info["worldcereal_custom_head_file_present"])
            self.assertFalse(info["worldcereal_ready_for_automatic_brazil_inference"])
            self.assertIn("SAR",info["priority"])
            self.assertIn("historical MapBiomas",info["priority"])

    def test_local_head_is_not_sufficient_for_operational_model(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            head=Path(tmp)/"trained_head.zip"
            head.write_bytes(b"placeholder is not a deployable model")
            info=installation_diagnostic(
                environ={"ENFORM_WORLDCEREAL_CROPTYPE_HEAD":str(head)},
                model_dir=tmp)
            self.assertTrue(info["worldcereal_custom_head_file_present"])
            self.assertFalse(info["worldcereal_ready_for_automatic_brazil_inference"])


if __name__=="__main__":
    unittest.main()
