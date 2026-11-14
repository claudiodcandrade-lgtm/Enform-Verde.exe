import unittest

from agricultural_native_policy import has_cultivated_area


class CultivatedAreaDetectionTests(unittest.TestCase):
    def test_detects_generic_crop_class_and_named_crop(self):
        self.assertTrue(has_cultivated_area([{"class_name": "Áreas cultivadas", "area_ha": 1}]))
        self.assertTrue(has_cultivated_area([{"class_name": "Soja", "area_ha": 0.5}]))

    def test_pasture_alone_is_not_a_crop_area(self):
        self.assertFalse(has_cultivated_area([{"class_name": "Pastagem", "area_ha": 20}]))

    def test_ignores_zero_area_and_unclassified_cover(self):
        self.assertFalse(has_cultivated_area([
            {"class_name": "Milho", "area_ha": 0},
            {"class_name": "Não classificado", "area_ha": 5},
        ]))


if __name__ == "__main__":
    unittest.main()
