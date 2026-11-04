import unittest
from experimental_audit import audit_carbon_component, audit_yield_forecast, eligible_experimental_yield

class TestExperimentalAudit(unittest.TestCase):
    def test_ton_c_and_carbondioxide(self):
        row={"tc":30,"range_tc_ha":[25,40],"fonte":"SFB/IFN","source_url":"https://dados.florestal.gov.br","source_sha256":"a"*64}
        a=audit_carbon_component(row,area_ha=100,formation="Cerrado")
        self.assertEqual(a["result"]["stock_tC"],3000)
        self.assertEqual(a["result"]["stock_tCO2e"],11000)
        self.assertEqual(a["scaled_source_range_tC"],[2500,4000])
        self.assertFalse(a["is_AOI_CI95"])
        self.assertEqual(a["trace_sha256"],audit_carbon_component(row,area_ha=100,formation="Cerrado")["trace_sha256"])

    def test_missing_and_invalid_are_nd(self):
        self.assertEqual(audit_carbon_component({"tc":None},area_ha=3,formation="X")["status"],"N/D")
        self.assertEqual(audit_carbon_component({"tc":float("nan")},area_ha=3,formation="X")["status"],"N/D")
        self.assertIsNone(audit_carbon_component({"tc":20,"range_tc_ha":[30,50]},area_ha=3,formation="X")["density_source_range_tC_ha"])

    def test_crop_yield_with_trace(self):
        f={"status":"previsao_experimental","yield_t_ha":3,"crop_area_ha":30,"crop":"soja",
           "prediction_interval_t_ha":{"lower":2,"upper":4},"model_id":"regional",
           "source_url":"https://sidra.ibge.gov.br","source_sha256":"a"*64,
           "training_source":"https://sidra.ibge.gov.br",
           "geographic_domain":"microrregiao","temporal_domain":"2015-2024",
           "uncertainty_kind":"explicit_uncalibrated_scenario_range",
           "interval_method":"intervalo de residuos historicos"}
        self.assertTrue(eligible_experimental_yield(f))
        t=audit_yield_forecast(f)
        self.assertEqual(t["result"]["production_t"],90)
        self.assertEqual(t["result"]["production_range_t"],[60,120])
        self.assertFalse(t["field_coverage_validated"])
        del f["source_sha256"]
        self.assertFalse(eligible_experimental_yield(f))

if __name__=="__main__":
    unittest.main()
