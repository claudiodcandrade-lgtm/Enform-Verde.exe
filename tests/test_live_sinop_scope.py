"""The Sinop live SAR diagnostic must not report its sample box as farm AOI."""
import unittest

from tools.live_sinop_semantic_sar import build_report_header, summarize_sample_box


class SinopLiveScopeTests(unittest.TestCase):
    def test_report_labels_test_box_and_unprocessed_farm_reference(self):
        report = build_report_header(1084.73, started_at="fixture")
        self.assertEqual(report["sample_box_area_ha"], 1084.73)
        self.assertEqual(report["reference_farm_area_ha_not_processed"], 1459.91)
        self.assertIn("NOT original KML", report["scope"])
        self.assertNotIn("aoi_area_ha", report)
        self.assertNotIn("original_farm_area_ha", report)

    def test_sample_box_summary_computes_total_and_unclassified_without_old_keys(self):
        result = summarize_sample_box(10.0, {"forest": 4.0, "crop": 2.5})
        self.assertEqual(result["sample_box_polygon_area_ha"], 6.5)
        self.assertEqual(result["sample_box_unclassified_area_ha"], 3.5)
        self.assertEqual(result["sample_box_polygon_area_by_class_ha"],
                         {"forest": 4.0, "crop": 2.5})
        self.assertNotIn("polygon_area_ha", result)


if __name__ == "__main__":
    unittest.main()
