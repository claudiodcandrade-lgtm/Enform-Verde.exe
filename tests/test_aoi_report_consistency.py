"""No-dependency regression tests for AOI SAR class and field reporting."""
import unittest

from tools.test_models_aoi import summarize_class_areas, crop_field_key


class AoiReportConsistencyTests(unittest.TestCase):
    def test_multiple_polygons_of_same_class_are_summed(self):
        rows = [("Lavoura de Soja", 100.21), ("Floresta nativa", 20.0),
                ("Lavoura de Soja", 39.94), ("Lavoura de Soja", 0.01)]
        self.assertEqual(summarize_class_areas(rows),
                         {"Lavoura de Soja": 140.2, "Floresta nativa": 20.0})

    def test_duplicate_crop_fields_keep_distinct_keys(self):
        fields = {}
        for i, hectares in enumerate((20, 40), 1):
            fields[crop_field_key("Soja", i)] = hectares
        self.assertEqual(len(fields), 2)
        self.assertEqual(sum(fields.values()), 60)

    def test_zero_or_tiny_slivers_are_excluded(self):
        self.assertEqual(summarize_class_areas([("Soja", 0.05), ("Milho", 0.0)]), {})


if __name__ == "__main__":
    unittest.main()
