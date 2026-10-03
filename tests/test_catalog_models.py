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
    def test_raster_role_classifier_distinguishes_backscatter_height_and_uncertainty(self):
        cases={
            "sigma0_HH.tif":"HH",
            "sigma0_HV_db.tif":"HV",
            "AGB_Mg_ha.tif":"AGB",
            "AGB_Std_Dev.tif":"UNCERTAINTY",
            "canopy_height_m.tif":"HEIGHT",
            "height_uncertainty.tif":"UNCERTAINTY",
        }
        for name,expected in cases.items():
            with self.subTest(name=name):self.assertEqual(sar.role(name),expected)


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

    def test_national_route_matrix_covers_supported_biomes_without_generic_means(self):
        samples={
            "Amazônia":"Floresta Ombrófila Densa",
            "Cerrado":"Savana Arborizada",
            "Caatinga":"Savana Estépica",
            "Mata Atlântica":"Floresta Estacional Semidecidual",
        }
        for biome,phys in samples.items():
            m=sar.national_predictive_route_matrix(biome,phys)
            self.assertTrue(m["supported_biome"],biome)
            self.assertFalse(m["biome_mean_permitted"],biome)
            self.assertIn(m["local_numeric_state"],("hierarchical_model_fallback_available","local_numeric_reference_available"))
            self.assertIn("state-level",m["ifn_sfb_reference"]["scope"])
        self.assertFalse(sar.national_predictive_route_matrix("Pampa","Estepe")["supported_biome"])
        self.assertFalse(sar.national_predictive_route_matrix("Pantanal","Savana")["supported_biome"])

    def test_lband_dualpol_high_biomass_is_stratifier_not_agb_equation(self):
        stats=[
            {"polarization":"HH","mean_db":-7.039013463912296},
            {"polarization":"HV","mean_db":-11.637107111856047},
        ]
        d=sar.lband_dualpol_diagnostic(stats,"Amazônia","Floresta Ombrófila Densa",273.515)
        self.assertIsNotNone(d)
        self.assertEqual(d["role"],"SAR_ESTRATIFICADOR")
        self.assertEqual(d["saturation_risk"],"high")
        self.assertFalse(d["quantitative_agb_from_dualpol_permitted"])
        self.assertAlmostEqual(d["hh_minus_hv_db"],4.598093647943751,places=9)
        self.assertGreater(d["rfdi"],0)
        self.assertLess(d["rfdi"],1)

    @unittest.skipUnless(gpd and box,"geospatial dependencies are installed in the Windows workflow")
    def test_nonamazon_aoi_cannot_receive_tapajos_numeric_fallback(self):
        aoi=gpd.GeoDataFrame(geometry=[box(-46.75,-10.35,-46.70,-10.30)],crs="EPSG:4326")
        self.assertIsNone(sar.literature_fallback("Cerrado","Savana Arborizada",aoi=aoi))
        m=sar.national_predictive_route_matrix("Cerrado","Savana Arborizada",aoi=aoi)
        self.assertEqual(m["local_numeric_state"],"hierarchical_model_fallback_available")
        self.assertIsNotNone(m["regional_numeric_fallback"])
        self.assertGreater(m["regional_numeric_fallback"]["agb_mg_ha"],0)
        self.assertEqual(len(m["regional_numeric_fallback"]["agb_range_mg_ha"]),2)

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
