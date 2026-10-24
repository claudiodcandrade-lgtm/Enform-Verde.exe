import unittest
from agricultural_yield_units import probable_productivity, probable_production


class CropYieldUnitTests(unittest.TestCase):
    def test_grain_productivity_converts_to_documented_60kg_sacks(self):
        result=probable_productivity(4.0,"soja_grao")
        self.assertEqual(result["unit"],"sacas/ha")
        self.assertAlmostEqual(result["value"],4000/60)
        self.assertEqual(result["conversion"]["kg_per_sack"],60)

    def test_production_covers_crop_area_inside_the_aoi(self):
        result=probable_production(4.0,3.0,"milho_grao")
        self.assertEqual(result["value_t"],12.0)
        self.assertEqual(result["sacks"],200.0)

    def test_cane_and_citrus_remain_in_tonnes_per_hectare(self):
        for crop in ("cana_de_acucar","laranja"):
            result=probable_productivity(80.0,crop)
            self.assertEqual(result["unit"],"t/ha")
            self.assertIsNone(result["conversion"])

    def test_negative_values_are_rejected(self):
        with self.assertRaises(ValueError): probable_productivity(-1,"soja")
        with self.assertRaises(ValueError): probable_production(1,-1,"soja")


if __name__=="__main__":
    unittest.main()
