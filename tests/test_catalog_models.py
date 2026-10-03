import unittest
from unittest.mock import patch
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
    def test_biomass_catalog_discovers_agb_and_height_without_conflating_them(self):
        agb={"id":"tile_FP_AGB_L2B","properties":{"datetime":"2026-08-01"},
             "assets":{"product":{"href":"https://example.test/agb.zip","type":"application/zip","title":"AGB product"}}}
        fh={"id":"tile_FP_FH__L2B","properties":{"datetime":"2026-08-02"},
            "assets":{"product":{"href":"https://example.test/fh.zip","type":"application/zip","title":"Forest height product"}}}
        calls=[]
        def fake_search(_gdf,collection,limit=100,product_type=None):
            calls.append((collection,product_type))
            rows={"FP_AGB_L2B":[agb],"FP_FH__L2B":[fh]}
            return rows.get(product_type,[])
        with patch.object(sar,"maap_search",side_effect=fake_search):
            items=sar.biomass_l2b_search(object())
        self.assertEqual(set(calls),{
            ("BiomassLevel2b","FP_AGB_L2B"),("BiomassLevel2b","FP_FH__L2B"),
            ("BiomassLevel2bIOC","FP_AGB_L2B"),("BiomassLevel2bIOC","FP_FH__L2B")})
        self.assertEqual({x["_product_type"] for x in items},{"FP_AGB_L2B","FP_FH__L2B"})
        self.assertEqual(sar._biomass_product_assets(fh,"FP_AGB_L2B"),[])
        self.assertEqual(sar._biomass_product_assets(agb,"FP_AGB_L2B"),[("product","https://example.test/agb.zip")])
        generic_agb={"id":"tile_FP_AGB_L2B","assets":{"data":{"href":"https://example.test/tile.tif","roles":["data"],"type":"image/tiff"}}}
        self.assertEqual(sar._biomass_product_assets(generic_agb,"FP_AGB_L2B"),[("data","https://example.test/tile.tif")])

    def test_biomass_catalog_audit_preserves_product_and_asset_metadata(self):
        item={"id":"tile_FP_FH__L2B","bbox":[-55,-4,-54,-3],
              "properties":{"datetime":"2026-08-02"},
              "assets":{"height":{"href":"https://example.test/fh.tif","type":"image/tiff","roles":["data"]}},
              "_collection":"BiomassLevel2b","_stage":"OPERATIONAL"}
        summary=sar._biomass_catalog_summary(item)
        self.assertEqual(summary["product_types"],["FP_FH__L2B"])
        self.assertEqual(summary["assets"][0]["key"],"height")
        self.assertEqual(summary["bbox"],item["bbox"])

    def test_height_only_biomass_catalog_does_not_attempt_agb_download(self):
        fh={"id":"tile_FP_FH__L2B","properties":{"datetime":"2026-08-02"},
            "assets":{"product":{"href":"https://example.test/fh.zip","type":"application/zip","title":"Forest height product"}},
            "_collection":"BiomassLevel2b","_stage":"OPERATIONAL","_product_type":"FP_FH__L2B"}
        with patch.object(sar,"biomass_l2b_search",return_value=[fh]), \
             patch.object(sar,"_download") as download, \
             patch.object(sar,"maap_access_token") as token:
            out=sar.download_maap_agb(object(),"dummy-token","/tmp/enform-test-cache")
        self.assertFalse(out["available"])
        self.assertEqual(out["fh_items"],1)
        self.assertIn("não substitui AGB",out["reason"])
        download.assert_not_called()
        token.assert_not_called()

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

    def test_agb_product_without_uncertainty_does_not_claim_statistical_error(self):
        zonal={
            "agb.tif":{"mean":300.0,"sd":42.0,"n":16,"min":250.0,"max":370.0},
            "canopy_height.tif":{"mean":24.0,"sd":5.0,"n":16,"min":14.0,"max":32.0},
        }
        with patch.object(sar,"_zonal",side_effect=lambda _gdf,path:zonal[str(path)]):
            out=sar.process_real_sar(object(),["agb.tif","canopy_height.tif"],"Amazônia","Floresta")
        self.assertEqual(out["agb_mg_ha"],300.0)
        self.assertIsNone(out["uncertainty_mg_ha"])
        self.assertEqual(out["spatial_sd_mg_ha"],42.0)
        self.assertEqual(out["n_valid_pixels"],16)
        self.assertEqual(out["height_mean_m"],24.0)

    def test_high_biomass_p_band_product_retains_agb_uncertainty_and_spatial_spread_separately(self):
        zonal={"FP_AGB_L2B_AGB.tif":{"mean":412.0,"sd":68.0,"n":25,"min":270.0,"max":590.0},
               "FP_AGB_L2B_AGB_Std_Dev.tif":{"mean":73.0,"sd":12.0,"n":25,"min":49.0,"max":105.0}}
        with patch.object(sar,"_zonal",side_effect=lambda _gdf,path:zonal[str(path)]):
            out=sar.process_real_sar(object(),list(zonal),"Amazônia","Floresta Ombrófila Densa")
        self.assertEqual(out["agb_mg_ha"],412.0)
        self.assertEqual(out["uncertainty_mg_ha"],73.0)
        self.assertIn("não é erro de validação local",out["uncertainty_kind"])
        self.assertEqual(out["spatial_sd_mg_ha"],68.0)
        self.assertEqual(out["n_valid_pixels"],25)

    def test_automatic_pipeline_labels_official_high_biomass_product_as_p_band(self):
        tile={"id":"tile_FP_AGB_L2B","properties":{"datetime":"2026-08-01"},
              "_product_type":"FP_AGB_L2B","_stage":"OPERATIONAL","_collection":"BiomassLevel2b"}
        product={"status":"SAR_PROCESSADO","agb_mg_ha":412.0,"uncertainty_mg_ha":73.0,
                 "uncertainty_kind":"média zonal de AGB_Std_Dev do produto ESA; incerteza do produto, não erro local de validação",
                 "stats":[],"spatial_sd_mg_ha":68.0,"n_valid_pixels":25}
        with patch.object(sar,"biomass_l2b_search",return_value=[tile]), \\
             patch.object(sar,"download_maap_agb",return_value={"paths":["FP_AGB_L2B_AGB.tif"],"available":True}), \\
             patch.object(sar,"process_real_sar",return_value=product):
            out=sar.automatic_pipeline(object(),"Amazônia","Floresta Ombrófila Densa",cache="/tmp/enform-high-agb-test")
        self.assertEqual(out["agb_mg_ha"],412.0)
        self.assertEqual(out["data_origin"],"SAR_P_BIOMASS_FP_AGB_L2B")
        self.assertEqual(out["sensor"],"ESA BIOMASS")
        self.assertEqual(out["band"],"P")
        self.assertEqual(out["product"],"FP_AGB_L2B")
        self.assertEqual(out["model_id"],"ESA_BIOMASS_FP_AGB_L2B")
        self.assertIn("não erro local",out["uncertainty_kind"])

    def test_sar_height_remains_available_when_no_agb_model_matches(self):
        zonal={"canopy_height.tif":{"mean":18.0,"sd":4.0,"n":9,"min":11.0,"max":25.0}}
        with patch.object(sar,"_zonal",side_effect=lambda _gdf,path:zonal[str(path)]):
            out=sar.process_real_sar(object(),["canopy_height.tif"],"Amazônia","Floresta")
        self.assertIsNone(out["agb_mg_ha"])
        self.assertEqual(out["height_mean_m"],18.0)
        self.assertEqual(out["height_n_valid_pixels"],9)


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

    def test_african_savanna_models_are_benchmarks_not_transferable_cerrado_equations(self):
        ids={"AFRICA_MITCHARD_2009_SAVANNA_L","AFRICA_BOUVET_2018_SAVANNA_PALSAR",
             "AFRICA_MERMOZ_2014_CAMEROON_PALSAR","AFRICA_GREATER_KRUGER_2018_PALSAR2"}
        entries={m["id"]:m for m in sar.MODEL_REGISTRY if m["id"] in ids}
        self.assertEqual(set(entries),ids)
        for model in entries.values():
            self.assertFalse(model["executable"])
            self.assertIsNone(model.get("coefficients"))
            self.assertTrue(model.get("doi"))
        self.assertIn("85 Mg/ha",entries["AFRICA_BOUVET_2018_SAVANNA_PALSAR"]["domain"])
        self.assertIn("253 parcelas",entries["AFRICA_MITCHARD_2009_SAVANNA_L"]["domain"])

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
