"""Model-only outputs are NOT independent validation or invented field data."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from modeled_field_validation import (build_pre_field_manifest,
                                      field_measurement_rows,
                                      write_pre_field_evidence)


def fixture():
    return {"known_total_tc":470, "complete":False,"native_area_ha":10,
        "strata":[{"physiognomy":"Floresta Ombrófila Densa",
                   "area_ha":10,"source":"SAR_VALIDADO+IBGE",
                   "components":[
                       {"parametro":"Biomassa aérea","tc":47,
                        "origem":"SAR_QUANTITATIVO","metodo":"AGB × 0.47",
                        "fonte":"Fonte com domínio explícito","range_tc_ha":[40,55],
                        "include_in_total":True},
                       {"parametro":"Solo 0–100 cm","tc":90,"area_basis_ha":4,
                        "metodo":"Soma de cinco horizontes no pixel",
                        "fonte":"Embrapa/PronaSolos","origem":"MAPEAMENTO",
                        "official_uncertainty":{"status":"ENVELOPE_MARGINAL_OFICIAL",
                          "sum_bounds_envelope_tc_ha":[80,110]},
                        "include_in_total":True},
                       {"parametro":"Necromassa aérea","tc":None,
                        "origem":"N/D","fonte":"Sem dado compatível","metodo":"N/D"}]}]}


class PreFieldTests(unittest.TestCase):
    def test_actual_estimates_are_predictions_not_observations(self):
        result=build_pre_field_manifest(fixture(),analysis_id="AOI-123")
        self.assertFalse(result["scientifically_homologated"])
        self.assertFalse(result["observed_validation_evidence"])
        self.assertEqual(result["predictions_with_numeric_model"],2)
        self.assertEqual(result["predictions_without_model"],1)
        agb, soil, dead=result["predictions"]
        self.assertEqual(agb["stock_predicted_tC"],470)
        self.assertEqual(agb["stock_range_tC"],[400,550])
        self.assertEqual(soil["stock_predicted_tC"],360)
        self.assertEqual(soil["stock_range_tC"],[320,440])
        self.assertIn("NAO_IC95_CONJUNTO",soil["uncertainty_kind"])
        self.assertFalse(soil["target_aoi_ci95_validated"])
        self.assertEqual(dead["status"],"N/D")
        self.assertIsNone(dead["density_predicted_tc_ha"])
        self.assertIsNone(dead["stock_predicted_tC"])
        self.assertEqual(result["existing_native_stock_tC"],470)
        self.assertFalse(result["existing_native_stock_is_complete"])

    def test_no_source_or_no_input_does_not_fabricate_estimate(self):
        a=fixture()
        a["strata"][0]["components"][0]["fonte"]="N/D"
        a["strata"][0]["components"][1]["tc"]=float("nan")
        result=build_pre_field_manifest(a,analysis_id="A")
        self.assertEqual(result["predictions_with_numeric_model"],0)
        self.assertEqual(result["predictions_without_model"],3)
        for p in result["predictions"]:
            self.assertIsNone(p["stock_predicted_tC"])
            self.assertNotEqual(p["status"],"PROJECAO_EXPERIMENTAL_PARA_VALIDACAO")

    def test_csv_field_values_are_always_blank(self):
        result=build_pre_field_manifest(fixture(),analysis_id="TEST")
        with tempfile.TemporaryDirectory() as folder:
            paths=write_pre_field_evidence(folder,result)
            raw=json.loads(Path(paths["predictions_json"]).read_text(encoding="utf-8"))
            self.assertEqual(len(raw["predictions"]),3)
            with Path(paths["field_template_csv"]).open(
                    encoding="utf-8-sig",newline="") as stream:
                rows=list(csv.DictReader(stream,delimiter=";"))
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[0]["valor_modelado"],"47.0")
            for row in rows:
                for col in ("valor_medido_campo","data_coleta_utc",
                            "parcela_talhao_id","grupo_espacial_independente",
                            "latitude","longitude"):
                    self.assertEqual(row[col],"")

    def test_unqualified_yield_is_nd_not_invented(self):
        native={"strata":[],"native_area_ha":0,"known_total_tc":None}
        result=build_pre_field_manifest(native,analysis_id="YLD",
            land={"yield_forecast":{"crop":"Soja","yield_t_ha":4,
                                    "status":"previsao_experimental"}})
        self.assertEqual(result["predictions_with_numeric_model"],0)
        self.assertEqual(result["predictions"][0]["status"],"N/D")
        self.assertIsNone(result["predictions"][0]["predicted_t_ha"])

    def test_invalid_analysis_id_rejected(self):
        with self.assertRaises(ValueError):
            build_pre_field_manifest(fixture(),analysis_id="")


if __name__=="__main__":
    unittest.main()
