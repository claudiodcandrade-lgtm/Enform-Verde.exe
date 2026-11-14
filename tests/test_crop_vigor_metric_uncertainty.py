"""SAR vigor test arrays are synthetic, and are never real orbit acquisitions."""
import unittest
import numpy as np
from crop_vigor import classify_vigor, field_metrics

class TestVigorUncertainty(unittest.TestCase):
    def test_indicators_and_block_bootstrap(self):
        rng=np.random.default_rng(12)
        shape=(24,24)
        refs=[field_metrics(rng.normal(-17+k*.5,2,shape),
                            rng.normal(-10-k*.2,1.5,shape),height_m=np.full(shape,.5+.05*k)) for k in range(8)]
        r=classify_vigor(rng.normal(-17,2,shape),rng.normal(-10,1.5,shape),refs,n_boot=80,seed=12,
                         height_m=np.full(shape,.7))
        self.assertEqual(r["status"],"experimental")
        metrics={"size","uniformity","texture_homogeneity"}
        self.assertTrue(metrics.issubset(r["metrics"]))
        self.assertEqual(set(r["metric_boot_p05_p95"]),metrics)
        for lo,hi in r["metric_boot_p05_p95"].values():
            self.assertTrue(np.isfinite([lo,hi]).all())
            self.assertLessEqual(lo,hi)
        self.assertGreater(r["n_bootstrap"],0)
        self.assertAlmostEqual(sum(r["probabilities"].values()),1)
        self.assertIn("NÃO acurácia",r["uncertainty_scope"])
    def test_no_comparison_fields(self):
        r=classify_vigor(np.full((25,25),-16.),np.full((25,25),-10.),[],n_boot=20)
        self.assertEqual(r["status"],"N/D")

if __name__=="__main__":
    unittest.main()
