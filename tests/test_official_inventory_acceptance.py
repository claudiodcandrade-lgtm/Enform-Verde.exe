import unittest

from official_inventory_harvest import evaluate_agency_accepted_inventory_document


class AgencyInventoryAcceptanceTests(unittest.TestCase):
    def _base(self):
        return dict(
            authorized_access=True,
            process_id="PROC-123",
            inventory_document_url="https://example.test/inventory.pdf",
            inventory_document_sha256="a" * 64,
            inventory_attachment_confirmed=True,
            acceptance_evidence_url="https://example.test/decision.pdf",
            acceptance_explicitly_covers_inventory=True,
            physiognomy_match=True,
            spatial_match=True,
            extracted_numeric_metric=True,
            method_and_units_verified=True,
            sample_size=12,
            sampling_error_published=True,
        )

    def test_explicit_acceptance_of_hashed_inventory_attachment_is_last_resort(self):
        result = evaluate_agency_accepted_inventory_document(**self._base())
        self.assertTrue(result["agency_inventory_acceptance_verified"])
        self.assertTrue(result["may_support_regional_reference"])
        self.assertFalse(result["include_in_sar_calibration"])
        self.assertEqual(result["source_hierarchy_rank"], 4)
        self.assertEqual(result["uncertainty_status"], "MENSURADA")

    def test_license_or_plan_approval_without_acceptance_of_attachment_is_rejected(self):
        args = self._base()
        args["acceptance_explicitly_covers_inventory"] = False
        result = evaluate_agency_accepted_inventory_document(**args)
        self.assertFalse(result["agency_inventory_acceptance_verified"])
        self.assertFalse(result["may_support_regional_reference"])
        self.assertFalse(result["checks"]["aceite_expresso_do_inventario_anexo"])

    def test_missing_sampling_error_reports_literal_uncertainty_status(self):
        args = self._base()
        args["sampling_error_published"] = False
        result = evaluate_agency_accepted_inventory_document(**args)
        self.assertEqual(result["uncertainty_status"], "incerteza não mensurável")


if __name__ == "__main__":
    unittest.main()
