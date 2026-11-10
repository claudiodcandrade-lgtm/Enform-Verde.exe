"""Executed, spatially held-out training contracts for experimental SAR algorithms."""
import tempfile
import unittest
import numpy as np
from sar_algorithm_portfolio import (FEATURE_SCHEMA, ALGORITHMS,
    train_spatial_sar_portfolio, predict_experimental_sar_portfolio)

class PortfolioTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(173)
        n=120
        groups=np.repeat(np.arange(12),10)
        labels=np.tile(np.array(["Floresta","Lavoura"]),60)
        X=rng.normal(0,0.1,(n,len(FEATURE_SCHEMA)))
        X[labels=="Floresta",:3]+=1
        self.data=(X,labels,groups)
        self.prov={"reference_dataset":"actual independently collected field sample contract",
                   "observation_period":"2024-2025","reference_origin":"FIELD_INVENTORY"}
    def test_three_algorithms_run_on_identical_grouped_folds(self):
        X,y,g=self.data
        with tempfile.TemporaryDirectory() as d:
            r=train_spatial_sar_portfolio(X,y,g,provenance=self.prov,output_dir=d)
            self.assertEqual(set(r["evaluation"]),set(ALGORITHMS))
            self.assertIn(r["selected_algorithm"],ALGORITHMS)
            self.assertFalse(r["deployment_eligible"])
            self.assertEqual(r["independent_validation"],"NOT_PROVIDED")
            self.assertTrue(all(v["eligible"] for v in r["evaluation"].values()))
            import pathlib
            self.assertTrue((pathlib.Path(d)/"sar_algorithm_comparison.json").is_file())
            pred=predict_experimental_sar_portfolio(
                pathlib.Path(d)/"sar_portfolio_experimental.joblib",X[:4])
            self.assertEqual(len(pred["labels"]),4)
            self.assertFalse(pred["calibrated_probability"])
    def test_reject_historical_pseudolabels(self):
        X,y,g=self.data
        for origin in ("IBGE","MAPBIOMAS","SAR_MODEL_PREDICTIONS"):
            with self.assertRaisesRegex(ValueError,"HISTORICAL_OR_SELF_LABELS"):
                train_spatial_sar_portfolio(
                    X,y,g,provenance={**self.prov,"reference_origin":origin})
    def test_reject_insufficient_groups_and_nonfinite(self):
        X,y,g=self.data
        with self.assertRaisesRegex(ValueError,"SPATIALLY_DISTINCT"):
            train_spatial_sar_portfolio(X,y,np.zeros(len(y)),provenance=self.prov)
        X[0,0]=np.nan
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            train_spatial_sar_portfolio(X,y,g,provenance=self.prov)

if __name__=="__main__":
    unittest.main()
