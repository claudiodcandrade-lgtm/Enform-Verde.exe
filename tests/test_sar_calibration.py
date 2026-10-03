import unittest
import numpy as np
import pandas as pd
from sar_calibration import calibrate_height_structure_agb

class SarCalibrationTests(unittest.TestCase):
    def test_inventory_only_data_is_refused(self):
        with self.assertRaisesRegex(ValueError,"colunas ausentes"):
            calibrate_height_structure_agb(pd.DataFrame({"dbh_cm":[10]}))

    def test_insufficient_independent_sites_are_refused(self):
        d=pd.DataFrame({"agb_ref_mg_ha":np.arange(1,31),"site_id":["only"]*30,
            "basal_area_m2_ha":[10]*30,"mean_dbh_cm":[20]*30,"stems_ha":[500]*30,"height_sar_m":[8]*30})
        with self.assertRaisesRegex(ValueError,"5 sítios independentes"):
            calibrate_height_structure_agb(d)

    def test_spatial_cv_comparison_is_never_marked_deployable(self):
        rng=np.random.default_rng(42); n=50
        ba=rng.uniform(5,30,n); dbh=rng.uniform(8,35,n); stems=rng.uniform(200,1800,n); h=rng.uniform(3,25,n)
        agb=np.exp(0.35*np.log(ba)+0.25*np.log(h)+rng.normal(0,.08,n))*2
        d=pd.DataFrame({"agb_ref_mg_ha":agb,"site_id":np.repeat([f"site_{i}" for i in range(5)],10),
            "basal_area_m2_ha":ba,"mean_dbh_cm":dbh,"stems_ha":stems,"height_sar_m":h,
            "agb_label_provenance":"allometry: illustrative fixture"})
        out=calibrate_height_structure_agb(d)
        self.assertEqual(out["status"],"EXPLORATORY_SPATIAL_CV_ONLY")
        self.assertFalse(out["deployable"])
        self.assertEqual(out["n_pairs"],50)
        self.assertEqual(out["independent_sites"],5)
        self.assertIn("estrutura_mais_altura_SAR",out["comparison"])

if __name__=="__main__": unittest.main()
