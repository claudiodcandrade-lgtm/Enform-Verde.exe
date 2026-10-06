import unittest

import numpy as np

from mapbiomas_zonal import LEGEND, summarize_class_grid


class MapBiomasZonalTests(unittest.TestCase):
    def test_area_weighting_and_percentages_are_correct(self):
        values = np.array([[3, 3, 6], [4, 6, 6]])
        inside = np.ones_like(values, dtype=bool)
        result = summarize_class_grid(values, inside, [100.0, 200.0])
        by_code = {row["class_code"]: row for row in result["classes"]}
        # 3: 2*100 m²; 6: 1*100 + 2*200; 4: 1*200.
        self.assertAlmostEqual(by_code[3]["area_ha"], 0.02)
        self.assertAlmostEqual(by_code[6]["area_ha"], 0.05)
        self.assertAlmostEqual(by_code[4]["area_ha"], 0.02)
        self.assertAlmostEqual(sum(x["area_pct"] for x in result["classes"]), 100.0)
        self.assertEqual(by_code[6]["class_name"], "Floresta Alagável")

    def test_mask_and_nodata_do_not_enter_denominator(self):
        values = np.array([[3, 0], [6, 4]])
        inside = np.array([[True, True], [False, True]])
        result = summarize_class_grid(values, inside, [100.0, 100.0], nodata=0)
        self.assertEqual([x["class_code"] for x in result["classes"]], [3, 4])
        self.assertAlmostEqual(sum(x["area_pct"] for x in result["classes"]), 100.0)
        self.assertAlmostEqual(result["mapped_area_ha"], 0.02)

    def test_known_collection_11_natural_classes_have_landcover_crosswalk(self):
        for code in (3, 4, 5, 6, 7, 11, 12, 49, 50):
            self.assertIn(code, LEGEND)
            self.assertTrue(LEGEND[code][0])
            self.assertTrue(LEGEND[code][1])


if __name__ == "__main__":
    unittest.main()
