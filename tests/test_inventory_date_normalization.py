import unittest
from datetime import date, datetime

from tools.inventory_date_utils import normalize_inventory_date
from tools.ingest_official_inventory_microdata import _update_date_bounds


class InventoryDateNormalizationTests(unittest.TestCase):
    def test_excel_serial_is_parsed_chronologically(self):
        self.assertEqual(normalize_inventory_date(45541), "2024-09-06")
        self.assertEqual(normalize_inventory_date("45541"), "2024-09-06")

    def test_text_dates_and_python_date_types_normalize(self):
        expected = "2024-09-06"
        self.assertEqual(normalize_inventory_date("06/09/2024"), expected)
        self.assertEqual(normalize_inventory_date("2024-09-06"), expected)
        self.assertEqual(normalize_inventory_date(date(2024, 9, 6)), expected)
        self.assertEqual(normalize_inventory_date(datetime(2024, 9, 6, 12)), expected)

    def test_date_bounds_ignore_missing_and_sort_iso_dates(self):
        bounds = {"date_min": None, "date_max": None}
        _update_date_bounds(bounds, None)
        _update_date_bounds(bounds, "2024-09-06")
        _update_date_bounds(bounds, "2023-01-01")
        _update_date_bounds(bounds, "2024-12-31")
        self.assertEqual(bounds, {"date_min": "2023-01-01", "date_max": "2024-12-31"})

    def test_blank_zero_and_invalid_dates_are_not_retained_as_dates(self):
        for value in (None, "", 0, "0", "not a date"):
            with self.subTest(value=value):
                self.assertIsNone(normalize_inventory_date(value))


if __name__ == "__main__":
    unittest.main()
