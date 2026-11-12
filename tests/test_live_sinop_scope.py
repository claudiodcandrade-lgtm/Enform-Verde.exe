"""The Sinop live SAR diagnostic must not report its sample box as farm AOI."""
import unittest

from tools.live_sinop_semantic_sar import build_report_header


class SinopLiveScopeTests(unittest.TestCase):
    def test_report_labels_test_box_and_unprocessed_farm_reference(self):
        report = build_report_header(1084.73, started_at="fixture")
        self.assertEqual(report["sample_box_area_ha"], 1084.73)
        self.assertEqual(report["reference_farm_area_ha_not_processed"], 1459.91)
        self.assertIn("NOT original KML", report["scope"])
        self.assertNotIn("aoi_area_ha", report)
        self.assertNotIn("original_farm_area_ha", report)


if __name__ == "__main__":
    unittest.main()
