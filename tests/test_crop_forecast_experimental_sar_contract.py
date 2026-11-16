"""Pre-field crop SAR contract: experimental annual masks are usable for
conditional scenarios, but never misrepresented as current verified fields.
"""
import tempfile
from pathlib import Path
import unittest
from datetime import date
from unittest.mock import patch
import geopandas as gpd
from shapely.geometry import box
from crop_monitoring_forecast import (crops_in_land_result,experimental_crops_in_land_result,
                                     canonical_crop,_append_candidate_vigor_lines,monitoring_forecast)
from crop_spatial_monitoring import (crop_geometry,current_sar_cultivated_candidate_geometry,
                                    current_candidate_vigor_blocks)


class ExperimentalCropForecastContracts(unittest.TestCase):
    def test_proven_absence_contingency_estimate_is_exposed_in_dashboard_audit(self):
        frame=gpd.GeoDataFrame(geometry=[box(-55.20,-11.89,-55.19,-11.88)],crs=4326)
        contingency={"status":"FALLBACK_HISTORICO_MAPBIOMAS_PAM",
            "classes":[{"label":"Soja","area_ha":40.0,"pam_year_count":10,
                "conditional_reference_production_t":138.0,
                "conditional_reference_production_p05_p95_t":[120.0,156.0],
                "climate_adjusted_forecast":{"status":"experimental","harvest_year":2026,
                    "model":"PAM_CLIMATE_SCENARIO",
                    "production_t":{"median":132.0,"p05":101.0,"p95":164.0}}}]}
        land={"status":"N/D_SEM_COBERTURA_SAR","classes":[],
              "agriculture_historical_contingency":contingency}
        lines,audit=monitoring_forecast(frame,land,as_of=date(2026,11,16))
        rendered="\n".join(lines)
        self.assertIn("ESTIMATIVA CONTINGENCIAL PAM",rendered)
        self.assertIn("Reserva histórica: 138.00 t",rendered)
        self.assertIn("PREVISÃO EXPERIMENTAL PAM×CLIMA SEM VIGOR — 132.00 t",rendered)
        self.assertIn("não confirma cultura ou área atuais",rendered)
        self.assertEqual(audit["yield_contingency"]["status"],"ESTIMATIVA_HISTORICA_DISPONIVEL")
        self.assertFalse(audit["yield_contingency"]["current_crop_or_area_confirmed"])

    def test_experimental_sar_soy_polygon_can_be_used_conditionally(self):
        frame=gpd.GeoDataFrame({
            "class_name":["Lavoura de Soja","Formação florestal"],
            "source":["SAR_EXPERIMENTAL_MODELO","SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(-55.2,-11.89,-55.19,-11.88),
                      box(-55.19,-11.89,-55.18,-11.88)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"classes.geojson"
            frame.to_file(path,driver="GeoJSON")
            land={"vector_path":str(path),"classes":[
                {"class_name":"Lavoura de Soja","source":"SAR_EXPERIMENTAL_MODELO",
                 "area_ha":float(frame.iloc[[0]].to_crs(6933).geometry.area.sum()/10000)},
                {"class_name":"Formação florestal","source":"SAR_EXPERIMENTAL_MODELO",
                 "area_ha":float(frame.iloc[[1]].to_crs(6933).geometry.area.sum()/10000)}],
                "validation":{"observed_season":"2025/2026"}}
            self.assertFalse(crops_in_land_result(land))
            crops=experimental_crops_in_land_result(land)
            self.assertIn("Soja",crops)
            self.assertNotIn("Formação florestal",crops)
            geoms=crop_geometry(land,"Soja",canonical_fn=canonical_crop)
            self.assertIsNotNone(geoms)
            self.assertEqual(len(geoms),1)
            self.assertGreater(float(geoms.to_crs(6933).geometry.area.sum()),0)

    def test_annual_sar_mask_reaches_calibrated_model_as_conditional_scenario(self):
        frame=gpd.GeoDataFrame({"class_name":["Lavoura de Soja"],
            "source":["SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(-55.20,-11.89,-55.19,-11.88)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"annual.geojson";frame.to_file(path,driver="GeoJSON")
            land={"vector_path":str(path),"classes":[{"class_name":"Lavoura de Soja",
                "source":"SAR_EXPERIMENTAL_MODELO","area_ha":1.0}],
                "validation":{"observed_season":"2025/2026"}}
            called={}
            def forecast(fields,as_of):
                called["fields"]=fields
                return {"model":"panel","model_label":"painel teste","fields":{},
                    "production":{"fields_kg_ha":{},"production_t":{"median":0,"p05":0,"p95":0,
                    "interval_note":"fixture"}}}
            with patch("crop_panel_yield_model.load_artifact",return_value={"crops":{"Soja":{}}}):
                lines,audit=monitoring_forecast(
                    frame,land,as_of=date(2026,11,15),forecast_fn=forecast,
                    micro_fn=lambda _g:{"dominant":{"code":"51006","name":"Alto Teles Pires"}})
            self.assertIn("fields",called,"máscara SAR anual não pode ser bloqueada antes do modelo")
            self.assertEqual(called["fields"][0]["crop"],"Soja")
            self.assertEqual(called["fields"][0]["vigor"]["status"],"N/D")
            self.assertEqual(audit["crops"]["Soja"]["transfer_uncertainty"],"NAO_QUANTIFICADA")
            inputs=audit["crops"]["Soja"]["forecast_inputs"]
            self.assertEqual(inputs["crop_mask_source"],"SAR_EXPERIMENTAL_ANUAL")
            self.assertEqual(inputs["crop_mask_season"],"2025/2026")
            self.assertEqual(inputs["yield_history"],"IBGE PAM N9, escala microrregional")
            self.assertFalse(inputs["current_crop_specific_sar_vigor_used"])
            rendered="\n".join(lines)
            self.assertIn("previsão SEM VIGOR",rendered)
            self.assertIn("PREVISÃO CONDICIONAL",rendered)
            self.assertIn("NÃO quantificada",rendered)

    def test_current_sar_vigor_on_annual_mask_is_conditionally_fed_to_yield_model(self):
        frame=gpd.GeoDataFrame({"class_name":["Lavoura de Soja"],
            "source":["SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(-55.20,-11.89,-55.19,-11.88)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"annual.geojson";frame.to_file(path,driver="GeoJSON")
            land={"vector_path":str(path),"classes":[{"class_name":"Lavoura de Soja",
                "source":"SAR_EXPERIMENTAL_MODELO","area_ha":1.0}],
                "validation":{"observed_season":"2025/2026"}}
            vigor={"status":"experimental","class":"vigor adequado",
                "probabilities":{"baixo vigor":.2,"vigor adequado":.6,"alto vigor":.2},
                "accepted_scenes":[{"scene_id":"S1_TEST","acquisition_utc":"2026-11-12T10:00:00Z"}],
                "acquisition_period_utc":["2026-11-12T10:00:00Z","2026-11-12T10:00:00Z"],
                "patches_evaluated":6,"patches_valid":5,"sample_audit":[],
                "sar_sample_coverage_fraction":.8}
            called={}
            def forecast(fields,as_of):
                called["fields"]=fields
                return {"model":"panel","model_label":"painel teste","fields":{},
                    "production":{"fields_kg_ha":{},"production_t":{"median":0,"p05":0,"p95":0,
                    "interval_note":"fixture"}}}
            with patch("crop_panel_yield_model.load_artifact",return_value={"crops":{"Soja":{}}}), \
                 patch("crop_spatial_monitoring.sampled_sentinel_vigor",return_value=vigor), \
                 patch("crop_spatial_monitoring.current_candidate_vigor_blocks",return_value={
                     "status":"ok","target_blocks":[frame[["geometry"]]],
                     "reference_gdf":frame[["geometry"]],"target_block_count":1,
                     "reference_block_count":6,"blocks_available":7,"block_area_ha":16.0}):
                lines,audit=monitoring_forecast(
                    frame,land,as_of=date(2026,11,15),forecast_fn=forecast,
                    micro_fn=lambda _g:{"dominant":{"code":"51006","name":"Alto Teles Pires"}})
            inputs=audit["crops"]["Soja"]["forecast_inputs"]
            self.assertEqual(called["fields"][0]["vigor"]["probabilities"],vigor["probabilities"])
            self.assertFalse(inputs["current_crop_specific_sar_vigor_used"])
            self.assertTrue(inputs["experimental_current_sar_vigor_conditioned_yield"])
            self.assertIn("não confirmada",inputs["vigor_observation_scope"])
            self.assertEqual(inputs["crop_mask_season"],"2025/2026")
            self.assertEqual(audit["crops"]["Soja"]["forecast"]["input_provenance"],inputs)
            rendered="\n".join(lines)
            self.assertIn("vigor SAR datado incorporado ao modelo",rendered)
            self.assertIn("PREVISÃO CONDICIONAL",rendered)

    def test_unverified_cartographic_classes_never_enable_forecast(self):
        land={"classes":[
            {"class_name":"Lavoura de Soja","source":"IBGE_POTENCIAL","area_ha":900},
            {"class_name":"Lavoura de Milho","source":"FALLBACK_CARTOGRAFICO","area_ha":800}]}
        self.assertFalse(crops_in_land_result(land))

    def test_current_vigor_mask_uses_only_recent_sar_cultivated_candidates(self):
        frame=gpd.GeoDataFrame({
            "class_code":[1,2,3,2],
            "source":["SAR_CURRENT_EXPERIMENTAL"]*3+["SAR_EXPERIMENTAL_MODELO"]},
            geometry=[box(0,0,.01,.01),box(1,1,1.02,1.02),box(2,2,2.01,2.01),
                      box(3,3,3.02,3.02)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"recent.geojson"
            frame.to_file(path,driver="GeoJSON")
            land={"recent_sar_cover":{"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES",
                                       "vector_path":str(path)}}
            result=current_sar_cultivated_candidate_geometry(land)
            self.assertIsNotNone(result)
            self.assertEqual(len(result),1)
            self.assertAlmostEqual(result.geometry.iloc[0].area,frame.geometry.iloc[1].area)
            self.assertIsNone(current_sar_cultivated_candidate_geometry(
                {"recent_sar_cover":{"status":"N/D","vector_path":str(path)}}))

    def test_candidate_vigor_panel_is_always_explicitly_conditional(self):
        lines=[]
        _append_candidate_vigor_lines(lines,{"status":"experimental","class":"vigor adequado",
            "probabilities":{"baixo vigor":.2,"vigor adequado":.6,"alto vigor":.2},
            "acquisition_period_utc":["2026-11-01T00:00:00Z","2026-11-12T00:00:00Z"]})
        rendered="\n".join(lines)
        self.assertIn("CONDICIONAL/EXPERIMENTAL",rendered)
        self.assertIn("cultura não identificada",rendered)
        self.assertIn("não confirma cultivo atual",rendered)
        self.assertIn("janela máxima 30 dias",rendered)

    def test_annual_mask_vigor_uses_disjoint_spatial_reference_blocks(self):
        footprint=gpd.GeoDataFrame(geometry=[box(-55.20,-11.95,-55.15,-11.90)],crs=4326)
        design=current_candidate_vigor_blocks(
            footprint,footprint_label="máscara anual SAR experimental da cultura")
        self.assertEqual(design["status"],"ok")
        self.assertGreaterEqual(design["reference_block_count"],6)
        targets=[item.to_crs(6933).geometry.iloc[0] for item in design["target_blocks"]]
        references=[geom for geom in design["reference_gdf"].to_crs(6933).geometry]
        self.assertTrue(all(not target.intersects(ref) for target in targets for ref in references))
        small=gpd.GeoDataFrame(geometry=[box(-55.20,-11.89,-55.19,-11.88)],crs=4326)
        insufficient=current_candidate_vigor_blocks(
            small,footprint_label="máscara anual SAR experimental da cultura")
        self.assertEqual(insufficient["status"],"N/D")
        self.assertIn("máscara anual SAR experimental da cultura permite apenas",
                      insufficient["reason"])

    def test_non_panel_priority_crop_reaches_experimental_forecast_route(self):
        frame=gpd.GeoDataFrame({"class_name":["Lavoura de Sorgo"],
            "source":["SAR_VALIDADO"]},
            geometry=[box(-55.20,-11.89,-55.19,-11.88)],crs=4326)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"sorghum.geojson";frame.to_file(path,driver="GeoJSON")
            area=float(frame.to_crs(6933).geometry.area.sum()/10000)
            land={"vector_path":str(path),"classes":[{"class_name":"Lavoura de Sorgo",
                "source":"SAR_VALIDADO","area_ha":area}]}
            called={}
            def forecast(fields,as_of):
                called["fields"]=fields
                return {"status":"N/D","model":"PAM_CLIMATE_SCENARIO",
                        "fields":{}}
            with patch("crop_panel_yield_model.load_artifact",
                       return_value={"crops":{"Soja":{},"Milho":{}}}), \
                 patch("crop_forecast_pipeline.forecast_lines",return_value=[]), \
                 patch("sar_crop_live_probe.probe_recent_sar_crop_pixels",
                       return_value={"status":"N/D","reason":"fixture"}):
                lines,audit=monitoring_forecast(
                    frame,land,as_of=date(2026,11,16),vigor_fn=lambda *_a:{"status":"N/D","reason":"fixture"},
                    forecast_fn=forecast,
                    micro_fn=lambda _g:{"dominant":{"code":"51006","name":"Alto Teles Pires"}})
            self.assertEqual(called["fields"][0]["crop"],"Sorgo")
            self.assertIn("Sorgo",audit["crops"])
            self.assertEqual(audit["crops"]["Sorgo"]["forecast_inputs"]["priority_model_contract"]["status"],
                             "PAM_CLIMA_EXPERIMENTAL_SEM_PAINEL_PROPRIO")
            self.assertTrue(any("ROTA PRIORITÁRIA: cenário experimental PAM + clima" in line for line in lines), lines)


if __name__=="__main__":
    unittest.main()
