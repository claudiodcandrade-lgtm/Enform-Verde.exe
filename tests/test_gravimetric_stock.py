import unittest
from gravimetric_stock import litter_stock_from_quadrats, litter_depth_mass_calibration, necromass_line_intersect_stock, carbon_stock_from_mass

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

    def test_carbon_stock_uses_measured_carbon_fraction(self):
        r=carbon_stock_from_mass([10,20,30],[0.45,0.50,0.55])
        self.assertAlmostEqual(r["mean"],31.0/3.0)
        self.assertEqual(r["plot_carbon_stocks_tc_ha"],[4.5,10.0,16.5])
        self.assertGreater(r["margin_error"],0)

    def test_necromass_sums_pieces_by_transect_before_error(self):
        r=necromass_line_intersect_stock([10,20,10],[600,300,600],[10,10,10],
            transect_ids=["T1","T1","T2"],cluster_ids=["UA1","UA1","UA2"])
        self.assertEqual(r["n_independent_units"],2)
        self.assertEqual(len(r["transect_contributions_mg_ha"]),2)
        self.assertGreater(r["mean"],0)
        self.assertIn("decomposição",r["density_requirement"])

if __name__=="__main__":
    unittest.main()
