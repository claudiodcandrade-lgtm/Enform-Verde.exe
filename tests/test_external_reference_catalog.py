import unittest
from external_reference_catalog import select_validation_source, REFERENCE_SOURCES
class ExternalReferencesTests(unittest.TestCase):
 def test_no_source_is_auto_validated(self):
  for key in REFERENCE_SOURCES:
   self.assertFalse(select_validation_source(key)["eligible_for_independent_test"])
 def test_map_sources_never_field_validation(self):
  for key in ("mapbiomas_validation","conab_maps","trazo_fields"):
   self.assertFalse(select_validation_source(key,records_available=True,independently_audited=True)["eligible_for_independent_test"])
 def test_audited_field_source_can_be_eligible_for_test_not_validated(self):
  x=select_validation_source("goiatuba_2025_field",records_available=True,independently_audited=True)
  self.assertTrue(x["eligible_for_independent_test"])
  self.assertEqual(x["status"],"READY_FOR_PAIRED_SAR_TEST")
 def test_overlap_blocks(self):
  self.assertFalse(select_validation_source("sc_rice",records_available=True,independently_audited=True,model_training_overlap=True)["eligible_for_independent_test"])
if __name__=="__main__": unittest.main()
