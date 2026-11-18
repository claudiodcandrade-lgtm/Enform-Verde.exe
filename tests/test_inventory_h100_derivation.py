import unittest
import pandas as pd
from height_calibration import derive_inventory_h100

class InventoryH100Tests(unittest.TestCase):
    def frame(self, heights, area=0.1):
        return pd.DataFrame({"plot_id":["P1"]*len(heights),"tree_number":[str(i) for i in range(len(heights))],
            "total_height_m":heights,"sample_area_ha":[area]*len(heights),
            "biome":["Amazonia"]*len(heights),"physiognomy":["Ombrofila Densa"]*len(heights),
            "microregion":["Tapajos"]*len(heights)})
    def test_h100_matches_top_100_trees_per_ha_for_standard_ifn_area(self):
        out=derive_inventory_h100(self.frame(list(range(1,11)),.1))
        self.assertAlmostEqual(out.iloc[0].field_height_m,5.5)
        self.assertEqual(out.iloc[0].h100_equivalent_tree_count,10)
    def test_fractional_equivalent_tree_count_is_weighted(self):
        out=derive_inventory_h100(self.frame(list(range(1,17)),.155))
        self.assertAlmostEqual(out.iloc[0].h100_equivalent_tree_count,15.5)
        self.assertAlmostEqual(out.iloc[0].field_height_m,(sum(range(2,17))+.5*1)/15.5)
    def test_insufficient_inventory_trees_do_not_fall_back_to_mean_tree_height(self):
        self.assertTrue(derive_inventory_h100(self.frame(list(range(1,9)),.1)).empty)
    def test_multistem_tree_is_counted_once(self):
        d=self.frame(list(range(1,11)),.1)
        d.loc[1,"tree_number"]="0"
        self.assertTrue(derive_inventory_h100(d).empty)
    def test_physiognomy_and_region_are_required(self):
        d=self.frame(list(range(1,11)),.1);d["microregion"]=""
        self.assertTrue(derive_inventory_h100(d).empty)

if __name__=="__main__":unittest.main()
