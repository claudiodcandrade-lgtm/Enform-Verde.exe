import csv
import math
import tempfile
import unittest
from pathlib import Path
from inventory_structure import summarize_inventory_csv
from sar_pipeline import _height_interpretation


class InventoryStructureTests(unittest.TestCase):
    def test_basal_area_is_live_tree_section_area_over_plot_area(self):
        rows=[
            {"inventory_id":"MX_SANTO_AMBROSIO_2025","dbh_cm":"20","height_m":"10","plot_id":"1","status":"alive"},
            {"inventory_id":"MX_SANTO_AMBROSIO_2025","dbh_cm":"20","height_m":"12","plot_id":"1","status":"alive"},
            {"inventory_id":"MX_SANTO_AMBROSIO_2025","dbh_cm":"100","height_m":"8","plot_id":"1","status":"dead"},
        ]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"trees.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            out=summarize_inventory_csv(p)
        plot=out["plot_summary"][0]
        self.assertEqual(plot["n_live_stems"],2)
        self.assertAlmostEqual(plot["mean_dbh_cm"],20)
        self.assertAlmostEqual(plot["basal_area_m2_ha"],math.pi*0.2**2/4*2/0.025)
        self.assertFalse(plot["sar_pair_available"])
        self.assertFalse(plot["agb_sar_calibration_eligible"])

    def test_height_products_are_not_claimed_as_agb(self):
        for path,band in (("ESA_FP_FH__L2B_height.tif","P"),("TanDEM-X_InSAR_height.tif","X")):
            result=_height_interpretation(path)
            self.assertEqual(result["band"],band)
            self.assertFalse(result["agb_inference_permitted"])


if __name__=="__main__":
    unittest.main()
