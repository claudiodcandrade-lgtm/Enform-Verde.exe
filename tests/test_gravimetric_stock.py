import unittest
from gravimetric_stock import litter_stock_from_quadrats, litter_depth_mass_calibration, necromass_line_intersect_stock

class GravimetricStockTests(unittest.TestCase):
    def test_litter_stock_unit_conversion_and_margin(self):
        r=litter_stock_from_quadrats([250,500,750],[0.25,0.25,0.25])
        self.assertEqual(r["plot_stocks_mg_ha"],[10.0,20.0,30.0])
        self.assertEqual(r["n_independent_units"],3)
        self.assertGreater(r["margin_error"],0)
        self.assertEqual(r["unit"],"Mg matéria seca/ha")

    def test_cluster_subsamples_are_not_pseudoreplicated(self):
        r=litter_stock_from_quadrats([250,500,1000,1250],[0.25]*4,cluster_ids=["UA1","UA1","UA2","UA2"])
        self.assertEqual(r["n_independent_units"],2)
        self.assertTrue(r["subsamples_collapsed"])

    def test_depth_conversion_requires_paired_gravimetry(self):
        r=litter_depth_mass_calibration([1,2,3,4],[100,200,300,400],[0.25]*4,2.5)
        self.assertAlmostEqual(r["predicted_mean_mg_ha"],10.0)
        self.assertEqual(r["n_pairs"],4)
        with self.assertRaises(ValueError):
            litter_depth_mass_calibration([1,2],[100,200],[0.25,0.25],1.5)

    def test_necromass_line_intersect_requires_decay_density(self):
        r=necromass_line_intersect_stock([10,20],[600,300],[10,10],cluster_ids=["UA1","UA2"])
        self.assertEqual(r["n_independent_units"],2)
        self.assertGreater(r["mean"],0)
        self.assertIn("decomposição",r["density_requirement"])

if __name__=="__main__":
    unittest.main()
