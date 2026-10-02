import unittest
import sys
import types
import numpy as np
import pandas as pd
try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:
    gpd=box=None

# Requests is only used by live network routes, which these deterministic
# evaluator tests deliberately do not call.
try:
    import requests  # noqa: F401
except ImportError:
    sys.modules["requests"] = types.ModuleType("requests")
import sar_pipeline as sar


class CatalogModelExecutionTests(unittest.TestCase):
    def test_narvaes_published_equation_uses_exact_feature_contract(self):
        x={"sigma0_HH_db":-15,"Pv_db":0.2,"alpha_S2_deg":20,
           "Phi_S2_deg":-30,"Phi_S3_deg":45,"tau_m_deg":12}
        out=sar.execute_registered_model("NARVAES_2023_CENTRAL_AMAZON",x)
        expected=-1221.37-70.31*(-15)+1064.65*0.2+6.28*20-2.42*(-30)+3.44*45+6.05*12
        self.assertGreater(expected,0)
        self.assertAlmostEqual(out["agb_mg_ha"],expected,places=8)
        with self.assertRaisesRegex(ValueError,"Preditores obrigatórios ausentes"):
            sar.execute_registered_model("NARVAES_2023_CENTRAL_AMAZON",{"sigma0_HH_db":-10})

    def test_reference_recalibration_requires_real_spatial_pair_contract(self):
        rng=np.random.default_rng(7); n=40
        X=rng.normal(size=(n,6)); names=sar.MODEL_REGISTRY[[m["id"] for m in sar.MODEL_REGISTRY].index("NARVAES_2023_CENTRAL_AMAZON")]["predictors"]
        beta=np.array([1.1,-0.4,0.8,0.5,-0.3,0.2]); y=120+X@beta
        groups=np.repeat([f"site{i}" for i in range(5)],8)
        frame=pd.DataFrame(X,columns=names)
        fitted=sar.fit_catalog_reference("NARVAES_2023_CENTRAL_AMAZON",frame,y,groups,
            target_features=dict(zip(names,X[0])))
        self.assertFalse(fitted["reference_equation_used"])
        self.assertEqual(fitted["metrics"]["independent_groups"],5)
        self.assertIn("RMSE_Mg_ha",fitted["metrics"])
        with self.assertRaisesRegex(ValueError,"exige 5 grupos espaciais"):
            sar.fit_catalog_reference("NARVAES_2023_CENTRAL_AMAZON",frame,y,np.repeat(["a","b","c","d"],10))

    def test_missing_coefficient_reference_cannot_be_run_as_published_model(self):
        with self.assertRaisesRegex(ValueError,"não executável"):
            sar.execute_registered_model("CAATINGA_S1_JESUS_2023",{"VH":0.2})

    @unittest.skipUnless(gpd and box,"geospatial dependencies are installed in the Windows workflow")
    def test_regional_model_selection_requires_aoi_inside_declared_domain(self):
        model=next(m for m in sar.MODEL_REGISTRY if m["id"]=="NARVAES_2023_CENTRAL_AMAZON")
        features={p:1.0 for p in model["predictors"]}
        phys="floresta tropical com estágios primário, exploração seletiva e sucessão"
        self.assertIsNone(sar.select_executable_model("Amazônia",phys,features))
        local=gpd.GeoDataFrame(geometry=[box(-54.96,-3.07,-54.94,-3.06)],crs="EPSG:4326")
        distant=gpd.GeoDataFrame(geometry=[box(-47,-10,-46.9,-9.9)],crs="EPSG:4326")
        self.assertEqual(sar.select_executable_model("Amazônia",phys,features,aoi=local)["id"],model["id"])
        self.assertIsNone(sar.select_executable_model("Amazônia",phys,features,aoi=distant))


if __name__ == "__main__":
    unittest.main()
