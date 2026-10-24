import unittest
from crop_health_yield_quality import evaluate_yield_forecast

class YieldUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(
            predicted_t_ha=5.0, model_id="model-1", crop="soja",
            region="PR", season="2025/26",
            weather_provenance={"sources":[{"name":"NASA POWER","role":"historical"}],
                                "variables":["precipitation","temperature"],"period":"2025/26"},
            imagery_provenance={
                "crop_identification":{"modality":"SAR","sensor":"Sentinel-1","model_id":"crop-rf","crop":"soja","validation":{"independent_test":True,"in_domain":True}},
                "phenology_vigor":{"modality":"SAR","sensor":"Sentinel-1","model_id":"vigor-model","validation":{"independent_test":True,"in_domain":True}},
                "phytosanitary_signal":{"modality":"SAR","sensor":"Sentinel-1","model_id":"stress-model","diagnosis":"não determinado","validation":{"independent_test":True,"in_domain":True}}
            }, validation={
                "independent_test": True, "in_domain": True, "rmse_t_ha": 0.5,
                "mae_t_ha": 0.4, "bias_t_ha": 0.0, "sample_count": 100,
                "prediction_interval_validation": {
                    "independent_test": True, "spatial_temporal_holdout": True,
                    "method": "out-of-fold coverage", "nominal_coverage": 0.90,
                    "n_independent": 100, "n_covered": 92
                }
            },
            prediction_interval_t_ha={"lower":4.0,"upper":6.0,
                                      "nominal_coverage":0.90,"method":"conformal"},
            freshness_provenance={"status":"cenas_recentes_identificadas",
                "latest_acquisition_utc":"2026-10-23T08:44:48+00:00", "age_days":1,
                "scenes_in_series_window":3, "crop":"soja", "region":"PR",
                "phenological_phase":"florescimento",
                "freshness_criteria":{"defined":True,"max_age_days":5,
                    "minimum_scenes":3,"series_window_days":20,"source":"validated local protocol"}}
        )

    def test_calibrated_interval_is_reported(self):
        result = evaluate_yield_forecast(**self.base)
        self.assertEqual(result.status,"previsao_validada")
        self.assertEqual(result.provenance["prediction_interval"]["lower_t_ha"],4.0)
        self.assertGreater(result.uncertainty,0)

    def test_point_forecast_without_interval_is_blocked(self):
        args=dict(self.base);args.pop("prediction_interval_t_ha")
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")
        self.assertIsNone(result.value)
        self.assertTrue(any("Intervalo preditivo calibrado" in x for x in result.limitations))

    def test_poor_empirical_coverage_is_blocked(self):
        args=dict(self.base)
        args["validation"]=dict(self.base["validation"])
        args["validation"]["prediction_interval_validation"]=dict(self.base["validation"]["prediction_interval_validation"],n_covered=55)
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")
        self.assertTrue(any("Cobertura empírica" in x for x in result.limitations))

    def test_non_sar_crop_evidence_is_blocked(self):
        args=dict(self.base)
        args["imagery_provenance"]=dict(self.base["imagery_provenance"])
        args["imagery_provenance"]["crop_identification"]=dict(args["imagery_provenance"]["crop_identification"],modality="optical")
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")
        self.assertTrue(any("SAR declarado: crop_identification" in x for x in result.limitations))

    def test_missing_stress_indicator_is_blocked(self):
        args=dict(self.base)
        args["imagery_provenance"]=dict(self.base["imagery_provenance"])
        args["imagery_provenance"].pop("phytosanitary_signal")
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")
        self.assertTrue(any("phytosanitary_signal" in x for x in result.limitations))

    def test_small_validation_sample_is_blocked(self):
        args=dict(self.base)
        args["validation"]=dict(self.base["validation"])
        args["validation"]["prediction_interval_validation"]=dict(self.base["validation"]["prediction_interval_validation"],n_independent=20,n_covered=19)
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")

    def test_missing_sar_freshness_is_blocked(self):
        args=dict(self.base); args.pop("freshness_provenance")
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")
        self.assertTrue(any("Atualidade SAR" in x for x in result.limitations))

    def test_stale_sar_is_blocked(self):
        args=dict(self.base)
        args["freshness_provenance"]=dict(self.base["freshness_provenance"],age_days=12)
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")

    def test_wrong_region_sar_freshness_is_blocked(self):
        args=dict(self.base)
        args["freshness_provenance"]=dict(self.base["freshness_provenance"],region="SC")
        result=evaluate_yield_forecast(**args)
        self.assertEqual(result.status,"previsao_nao_habilitada")

if __name__=="__main__":
    unittest.main()
