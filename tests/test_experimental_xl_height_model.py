"""Synthetic contract tests only; they do not establish scientific accuracy."""
import unittest
import numpy as np
import pandas as pd
from native_biomass_sentinel1_height import (
    fit_experimental_xl_height_model, predict_experimental_xl_height,
)


class ExperimentalXLHeightTests(unittest.TestCase):
    def setUp(self):
        rows=[]
        rng=np.random.default_rng(10)
        for site in range(6):
            for plot in range(8):
                x=float(site*8+plot)/20
                rows.append({"site_id":f"S{site}","plot_id":f"S{site}P{plot}",
                    "texture":x,"backscatter":x*2+0.1,
                    "field_height_m":5+12*x+float(rng.normal(0,0.1)),
                    "sar_product_id":"S1-X-test-v1",
                    "field_height_definition":"H100",\n                    "biome":"Amazônia","physiognomy":"Floresta Ombrófila Densa","region":"Tapajós",
                    "spatial_match_error_m":5.0,"pixel_size_m":20.0,
                    "date_field":"2025-06-01T00:00:00Z",
                    "date_sar":"2025-08-01T00:00:00Z"})
        self.frame=pd.DataFrame(rows)
        self.kw=dict(feature_columns=["texture","backscatter"],band="X",
            physiognomy="Floresta Ombrófila Densa",
            reference_url="https://example.org/field-data",
            reference_sha256="a"*64,
            reference_kind="independent_field_observations",
            primary_route_status="UNAVAILABLE")

    def test_spatial_x_fallback_fits_auditable_model_and_predicts_in_domain(self):
        model=fit_experimental_xl_height_model(self.frame,**self.kw)
        self.assertEqual(model["status"],"MODELO_XL_EXPERIMENTAL_COM_VALIDACAO_ESPACIAL")
        self.assertEqual(model["band"],"X")
        self.assertEqual(model["metrics"]["n_spatial_sites"],6)
        result=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},model,band="X",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE")
        self.assertEqual(result["status"],"ALTURA_XL_EXPERIMENTAL")
        self.assertLess(result["height_interval_oof_m"][0],result["height_mean_m"])
        self.assertGreater(result["height_interval_oof_m"][1],result["height_mean_m"])
        self.assertEqual(result["reference_sha256"],"a"*64)

    def test_p_route_blocks_x_and_x_route_blocks_l(self):
        model=fit_experimental_xl_height_model(self.frame,**self.kw)
        out=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},model,band="X",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="AVAILABLE")
        self.assertEqual(out["status"],"N/D")
        lmodel=dict(model,band="L")
        out=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},lmodel,band="L",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE",x_route_status="AVAILABLE")
        self.assertEqual(out["status"],"N/D")

    def test_out_of_domain_predictors_and_missing_uncertainty_return_nd(self):
        model=fit_experimental_xl_height_model(self.frame,**self.kw)
        out=predict_experimental_xl_height(
            {"texture":1e6,"backscatter":1.1},model,band="X",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE")
        self.assertEqual(out["status"],"N/D")
        model["metrics"].pop("RMSE_m")
        out=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},model,band="X",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE")
        self.assertEqual(out["status"],"N/D")

    def test_pseudolabels_and_unverifiable_provenance_are_rejected(self):
        kwargs=dict(self.kw,reference_kind="MapBiomas")
        with self.assertRaisesRegex(ValueError,"observações de campo independentes"):
            fit_experimental_xl_height_model(self.frame,**kwargs)
        kwargs=dict(self.kw,reference_sha256="")
        with self.assertRaisesRegex(ValueError,"Fonte, SHA-256"):
            fit_experimental_xl_height_model(self.frame,**kwargs)


    def test_spatial_temporal_and_product_matching_qc_is_mandatory(self):
        bad=self.frame.copy()
        bad.loc[:,"spatial_match_error_m"]=11.0
        with self.assertRaisesRegex(ValueError,"Nenhum par passou a QA"):
            fit_experimental_xl_height_model(bad,**self.kw)
        bad=self.frame.copy()
        bad.loc[:,"date_sar"]="2020-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"Nenhum par passou a QA"):
            fit_experimental_xl_height_model(bad,**self.kw)
        bad=self.frame.copy()
        bad.loc[0,"sar_product_id"]="different-product"
        with self.assertRaisesRegex(ValueError,"Separe produtos SAR"):
            fit_experimental_xl_height_model(bad,**self.kw)

    def test_l_band_only_accepts_fallback_after_x_is_unavailable(self):
        model=fit_experimental_xl_height_model(
            self.frame,**dict(self.kw,band="L"))
        allowed=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},model,band="L",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE",x_route_status="UNAVAILABLE")
        blocked=predict_experimental_xl_height(
            {"texture":0.5,"backscatter":1.1},model,band="L",
            physiognomy="Floresta Ombrófila Densa",
            primary_route_status="UNAVAILABLE",x_route_status="AVAILABLE")
        self.assertEqual(allowed["status"],"ALTURA_XL_EXPERIMENTAL")
        self.assertEqual(blocked["status"],"N/D")


if __name__=="__main__":
    unittest.main()
