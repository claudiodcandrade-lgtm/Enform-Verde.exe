"""End-to-end handoff contract: worker queue -> core result -> app dashboards."""
import json
import queue
import threading
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

from desktop_app import App, native_carbon_analysis, _sar_dashboard_payload, _verified_sar_height_details
from analysis_pipeline_contract import geometry_hash


class TextBuffer:
    def __init__(self):
        self.value = ""


class CoreToDashboardHandoffTests(unittest.TestCase):
    def test_queued_core_results_reach_both_panels_and_audit(self):
        aoi = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100)], crs="EPSG:6933")
        with tempfile.TemporaryDirectory() as tmp:
            vector = Path(tmp) / "land.geojson"
            vector.write_text("{}", encoding="utf-8")
            sar_result = {
                "status": "ERRO_TECNICO_LEITURA_SAR",
                "reason": "INPE_E_MPC_INDISPONIVEIS_NO_FIXTURE",
                "latest_acquisition_utc": "2026-11-12T10:30:00Z",
                "analysis_run_id": "RUN-HANDOFF-1",
                "aoi_hash_sha256": geometry_hash(aoi),
            }
            land = {
                "status": sar_result["status"],
                "reason": sar_result["reason"],
                "priority": "Sentinel-1 recente; fontes públicas",
                "method": "SAR VV/VH; classes atuais N/D quando pixels indisponíveis",
                "classes": [],
                "vector_path": str(vector),
                "area_uncertainty": "N/D",
                "warnings": ["Fixture controlado de falha de leitura SAR"],
                "recent_sar_cover": sar_result,
                "sar_classifier_lemplus": {"status": "N/D", "reason": sar_result["reason"]},
                "validation": None,
                "analysis_run_id": "RUN-HANDOFF-1",
                "aoi_hash_sha256": geometry_hash(aoi),
            }
            native = {
                "area_aoi_ha": 1.0,
                "native_area_ha": 1.0,
                "unknown_cover_area_ha": 1.0,
                "excluded_other_uses_ha": 0.0,
                "unmapped_aoi_area_ha": 0.0,
                "cover_completeness": "NOT_VERIFIED",
                "method": "Carbono nativo estratificado; fixture de integração",
                "known_total_tc": 12.5,
                "complete": False,
                "uncertainty_note": "Incerteza do total não quantificada.",
                "components": [{
                    "parametro": "Biomassa aérea",
                    "tc_on_all_native_area": 12.5,
                    "quantified_area_ha": 1.0,
                    "missing_native_area_ha": 0.0,
                    "known_total_tc": 12.5,
                }],
                "strata": [],
                "analysis_run_id": "RUN-HANDOFF-1",
                "aoi_hash_sha256": geometry_hash(aoi),
            }
            pedology = {"status": "N/D", "reason": "fixture"}
            fertility = {"status": "N/D", "reason": "fixture"}
            payload = {
                "sar": sar_result,
                "soil": {},
                "land_use": land,
                "native_carbon": native,
                "pedology": pedology,
                "fertility": fertility,
                "aoi_hash": geometry_hash(aoi),
                "analysis_run_id": "RUN-HANDOFF-1",
            }

            carbon_widget, crop_widget, crop_audit_widget = TextBuffer(), TextBuffer(), TextBuffer()
            scheduled = []
            app = SimpleNamespace(
                _analysis_queue=queue.Queue(), _analysis_generation=7, _analysis_running=True,
                pipeline_btn=SimpleNamespace(state=lambda *_: None),
                global_execute_btn=SimpleNamespace(state=lambda *_: None),
                status=SimpleNamespace(set=lambda value: None),
                after=lambda delay, callback: scheduled.append(callback),
            )
            app._analysis_queue.put((7, "ok", payload))
            App._poll_analysis(app)
            self.assertEqual(len(scheduled), 1, "poll deve encaminhar a carga à execução principal")
            app.project = {"version": "test"}
            app.gdf = aoi
            app.car = SimpleNamespace(get=lambda: "")
            app.ccir = SimpleNamespace(get=lambda: "")
            app.active_source = None
            app.active_input_id = None
            app.biome = SimpleNamespace(get=lambda: "Amazônia")
            app.ibge_physiognomy_gdf = None
            app.ibge_class_field = "legenda_1"
            app.land_use_config = None
            app.sar_paths = []
            app.inventory_evidence_data = None
            app.inventory_evidence_manifest = None
            app.biodiversity_inventory_records = None
            app.update_idletasks = lambda: None
            app.res = carbon_widget
            app.crop_res = crop_widget
            app.crop_audit = crop_audit_widget
            app.tabs = [None, None, None, "carbon"]
            app.nb = SimpleNamespace(select=lambda *_: None)
            app._set = lambda widget, value: setattr(widget, "value", value)
            app._weather_query_generation = 0
            app.after = lambda *_: None
            app._execute_main = lambda **kwargs: App._execute_main(app, **kwargs)
            app._present_native_carbon = lambda *args, **kwargs: App._present_native_carbon(app, *args, **kwargs)
            app._present_cultivated_monitoring = lambda land_result: App._present_cultivated_monitoring(app, land_result)

            # Execute the same callback the Tk event loop schedules. The two
            # presenters remain real: this test checks their rendered widgets.
            with patch("analysis_pipeline_contract.validate_result_for_publication"):
                scheduled.pop()()

            self.assertIn("12,50 tC", carbon_widget.value)
            self.assertIn("ERRO_TECNICO_LEITURA_SAR", carbon_widget.value)
            self.assertIn("ERRO_TECNICO_LEITURA_SAR", crop_widget.value)
            self.assertIn("INPE_E_MPC_INDISPONIVEIS_NO_FIXTURE", crop_audit_widget.value)
            self.assertEqual(app.project["pipeline_audit"]["overall_status"], "PARCIAL_COM_ERRO_TECNICO")
            self.assertEqual(app.project["pipeline_audit"]["stages"]["land_use"]["status"], "ERRO_TECNICO")
            self.assertEqual(app.project["native_carbon"]["known_total_tc"], 12.5)
            self.assertEqual(app.project["sar_result"], sar_result,
                             "SAR pré-computado não pode ser descartado antes do dashboard")
            audit_path = Path(tmp) / "carbono_formacoes_nativas.json"
            self.assertEqual(json.loads(audit_path.read_text(encoding="utf-8"))["known_total_tc"], 12.5)

            # Repeat the queue-to-dashboard handoff for successfully read
            # recent pixels whose semantics remain experimental. This proves
            # that scene/date/provider data reach both dashboards without
            # promoting candidate hectares to validated crop area.
            acquisition = "2026-11-12T10:30:00Z"
            land.update({
                "status": "SAR_REAL_EXPERIMENTAL_CANDIDATES",
                "reason": None,
                "classes": [{
                    "class_name": "Área cultivada — candidato SAR experimental; cultura N/D",
                    "source": "SAR_EXPERIMENTAL_MODELO",
                    "taxonomy": "Candidato VV/VH; sem validação semântica",
                    "area_ha": 0.42,
                    "area_pct": 42.0,
                    "native_status": False,
                }],
                "recent_sar_cover": {
                    "status": "SAR_REAL_EXPERIMENTAL_CANDIDATES",
                    "scene_count": 1,
                    "latest_acquisition_utc": acquisition,
                    "areas_ha": {"cultivated_candidate": 0.42},
                    "provider_processing_diagnostics": [{
                        "provider": "INPE RTC",
                        "candidate_scene_count": 1,
                        "selected_scene_count": 1,
                        "vv_vh_valid_pixels": 256,
                    }],
                },
            })
            native["strata"] = [{
                "class_name": "Floresta de fixture",
                "area_ha": 1.0,
                "area_pct": 100.0,
                "source": "Fixture de integração",
                "physiognomy": "Floresta de fixture",
                "physiognomy_resolution": "fixture controlado",
                "sar_details": {"height_mean_m": 31.0,"height_sd_m": 4.2,
                    "height_n_valid_pixels": 8,"height_metric":"H100",
                    "height_error_kind":"spatial standard deviation",
                    "height_route_status":"ALTURA_SAR_PROCESSADA",
                    "product":"FP_FH__L2A","sensor":"ESA BIOMASS","band":"P",
                    "source":"ESA BIOMASS FH",
                    "height_pixel_distribution":{"status":"SAR_PIXELS_HISTOGRAMMED",
                        "bins":[{"label":"25–30 m","pixel_count":3},{"label":"30–35 m","pixel_count":5}]},
                    "stats": [{
                    "scene": "S1_INPE_FIXTURE_001",
                    "path": "S1_INPE_FIXTURE_001_VV_VH.tif",
                    "acquisition_utc": acquisition,
                    "provider": "INPE RTC",
                    "pixel_state": "PROCESSADO",
                    "n": 256,
                }]},
                "components": [{
                    "parametro": "Biomassa aérea",
                    "tc": 12.5,
                    "area_ha": 1.0,
                    "area_basis_ha": 1.0,
                    "origem": "SAR_EXPERIMENTAL_MODELO",
                    "fonte": "Modelo de fixture",
                    "metodo": "Equação experimental de fixture",
                    "include_in_total": True,
                    "total_tc": 12.5,
                    "quantified_area_ha": 1.0,
                }],
            }]
            native["analysis_run_id"] = "RUN-HANDOFF-1"
            native["aoi_hash_sha256"] = geometry_hash(aoi)
            land["analysis_run_id"] = "RUN-HANDOFF-1"
            land["aoi_hash_sha256"] = geometry_hash(aoi)
            payload["sar"] = _sar_dashboard_payload(native,land)
            carbon_widget.value = crop_widget.value = crop_audit_widget.value = ""
            app.project = {"version": "test"}
            app._analysis_generation = 8
            app._analysis_running = True
            app._analysis_queue.put((8, "ok", payload))
            scheduled.clear()
            app.after = lambda delay, callback: scheduled.append(callback)
            App._poll_analysis(app)
            with patch("analysis_pipeline_contract.validate_result_for_publication"):
                scheduled.pop()()
            self.assertIn("S1_INPE_FIXTURE_001", carbon_widget.value)
            self.assertIn("12/11/2026", carbon_widget.value)
            self.assertIn(acquisition, crop_widget.value)
            self.assertIn("INPE RTC", crop_audit_widget.value)
            self.assertIn('"vv_vh_valid_pixels": 256', crop_audit_widget.value)
            self.assertIn("PREVISÃO EXPERIMENTAL PARA AFERIÇÃO EM CAMPO", carbon_widget.value)
            self.assertIn("Biomassa aérea", carbon_widget.value)
            self.assertIn("hash de rastreio:", carbon_widget.value)
            self.assertIn("previsões e observações permanecem separadas", carbon_widget.value)
            self.assertIn("candidato SAR experimental", crop_widget.value)
            self.assertIn("cultura N/D", crop_widget.value)
            self.assertEqual(app.project["sar_result"]["height_products"][0]["height_mean_m"],31.0)
            self.assertEqual(app.project["sar_result"]["height_products"][0]["height_n_valid_pixels"],8)
            self.assertIn('"height_mean_m": 31.0',carbon_widget.value)
            self.assertIn("ALTURA DE DOSSEL SAR",carbon_widget.value)
            carbon_audit=json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(carbon_audit["strata"][0]["sar_details"]["height_n_valid_pixels"],8)
            sar_audit=json.loads((Path(tmp)/"proveniencia_sar_painel.json").read_text(encoding="utf-8"))
            self.assertEqual(sar_audit["analysis_run_id"],"RUN-HANDOFF-1")
            self.assertEqual(sar_audit["aoi_hash_sha256"],geometry_hash(aoi))
            self.assertEqual(sar_audit["sar_dashboard_payload"]["height_products"][0]["height_mean_m"],31.0)


    def test_local_sar_runs_in_worker_and_reaches_both_core_stages(self):
        aoi = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100)], crs="EPSG:6933")
        sar_paths = ["local-sentinel1-vv.tif", "local-sentinel1-vh.tif"]
        land = {"status": "SAR_REAL", "vector_path": "land.geojson",
                "classes": [], "recent_sar_cover": {"pixel_state": "PROCESSADO"}}
        native = {"area_aoi_ha": 1.0, "strata": [], "components": [],
                  "known_total_tc": None, "status": "N/D"}
        app = SimpleNamespace(
            _analysis_running=False, _ibge_pending=False, gdf=aoi,
            car=SimpleNamespace(get=lambda: ""), ccir=SimpleNamespace(get=lambda: ""),
            active_source=None, active_input_id=None, sar_paths=sar_paths,
            land_use_config=None, inventory_evidence_data=None,
            inventory_evidence_manifest=None, biodiversity_inventory_records=None,
            ibge_physiognomy_gdf=None, ibge_class_field="legenda_1",
            biome=SimpleNamespace(get=lambda: "Amazônia"),
            phys=SimpleNamespace(get=lambda: "Floresta teste"),
            esa_token=SimpleNamespace(get=lambda: ""), edl_token=SimpleNamespace(get=lambda: ""),
            edl_user=SimpleNamespace(get=lambda: ""), edl_password=SimpleNamespace(get=lambda: ""),
            cdse_token=SimpleNamespace(get=lambda: ""),
            cdse_client_id=SimpleNamespace(get=lambda: ""),
            cdse_client_secret=SimpleNamespace(get=lambda: ""),
            _analysis_generation=0, _analysis_queue=queue.Queue(),
            pipeline_btn=SimpleNamespace(state=lambda *_: None),
            global_execute_btn=SimpleNamespace(state=lambda *_: None),
            status=SimpleNamespace(set=lambda *_: None), after=lambda *_: None,
            _poll_analysis=lambda: None,
            _execute_main=lambda *_args, **_kwargs: self.fail("local SAR must not run on Tk thread"),
        )
        worker_threads = []
        real_thread = threading.Thread
        class InlineThread:
            def __init__(self, target, **_kwargs):
                self._background = real_thread(target=target, **_kwargs) if _kwargs.get("name") == "EnformSoilStages" else None
                self.target = target
                worker_threads.append(self)
            def start(self):
                if self._background is not None:
                    self._background.start()
                else:
                    self.target()
            def join(self):
                if self._background is not None:
                    self._background.join()

        import sys
        import types
        pedology_module = types.ModuleType("soil_pedology_embrapa")
        pedology_module.analyze_embrapa_pedology = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("fixture soil failure"))
        fertility_module = types.ModuleType("soil_fertility_zonal")
        fertility_module.analyze_fertility = lambda *_args, **_kwargs: {"status": "OK"}
        with patch("desktop_app.threading.Thread", InlineThread), \
             patch("desktop_app.load_ibge_land_use_reference", return_value=(None, "legenda_1")), \
             patch("desktop_app.run_land_use", return_value=land) as land_use, \
             patch("desktop_app.native_carbon_analysis", side_effect=RuntimeError("fixture carbon failure")) as carbon, \
             patch.dict(sys.modules, {"soil_pedology_embrapa": pedology_module,
                                      "soil_fertility_zonal": fertility_module}), \
             patch("desktop_app._write_analysis_stage_checkpoint", return_value="checkpoint-test") as checkpoint:
            App.execute(app)
        self.assertEqual(len(worker_threads), 2)
        land_use.assert_called_once()
        self.assertEqual(land_use.call_args.kwargs["sar_paths"], sar_paths)
        carbon.assert_called_once()
        self.assertEqual(carbon.call_args.kwargs["sar_paths"], sar_paths)
        run_id, kind, payload = app._analysis_queue.get_nowait()
        self.assertEqual((run_id, kind), (1, "ok"))
        self.assertEqual(payload["land_use"]["status"], land["status"])
        self.assertEqual(payload["sar"]["status"], "SAR_PROCESSADO")
        self.assertEqual(payload["native_carbon"]["status"], "ERRO_TECNICO_CARBONO")
        self.assertEqual(payload["pedology"]["status"], "ERRO_TECNICO_SOLO")
        self.assertTrue(payload["stage_errors"])
        self.assertEqual(payload["checkpoint_path"], "checkpoint-test")
        self.assertIn("worker_wall_seconds", payload["performance"])
        self.assertIn("soil_pipeline_wall_seconds", payload["performance"])
        self.assertIn("pedology_seconds", payload["performance"])
        self.assertIn("fertility_seconds", payload["performance"])
        self.assertEqual(payload["land_use"]["analysis_run_id"], payload["analysis_run_id"])
        checkpoint.assert_called_once()

    def test_conditional_inventory_reuses_existing_sar_without_second_pipeline(self):
        aoi = gpd.GeoDataFrame(geometry=[box(-55.0, -4.0, -54.99, -3.99)], crs="EPSG:4326")
        sar_result = {
            "status": "SAR_NAO_PROCESSADO",
            "reason": "ausência de cenas confirmada após esgotar as rotas",
            "audit": {
                "sar_sources_exhausted": True,
                "sar_pixel_processing_status": "NENHUM_PIXEL_SAR_UTILIZAVEL_APOS_ROTAS_CONFIGURADAS",
                "scene_absence_certificate": {
                    "eligible": True, "status": "SAR_AUSENCIA_CENAS_CONFIRMADA"},
            },
            "inventory_fallback_gate": {
                "eligible": True, "status": "SAR_AUSENCIA_CENAS_CONFIRMADA"},
        }
        land = {
            "vector_path": "land.geojson",
            "validation": {},
            "potential_physiognomy_intersections": [
                {"name": "Floresta teste A", "area_ha": 1.0},
                {"name": "Floresta teste B", "area_ha": 2.0},
            ],
        }
        native = {"known_total_tc": None, "area_aoi_ha": 3.0,
                  "strata": [{"area_ha": 1.0, "sar_details": sar_result}], "components": []}
        with patch("geopandas.read_file", return_value=aoi), \
             patch("desktop_app.summarize_native_carbon", return_value=native), \
             patch("sar_pipeline.biomass_l2b_search", return_value=([], {"queries": [], "errors": []})), \
             patch("desktop_app.automatic_pipeline") as pipeline, \
             patch("ifn_carbon_fallback.estimate_inventory_carbon_scenario",
                   return_value={"status": "CENARIO_CONDICIONAL_INVENTARIO_SEM_AGB_ALTURA_SAR"}) as scenario:
            result = native_carbon_analysis(aoi, land, "Amazônia")
        self.assertEqual(pipeline.call_count, 0)
        self.assertEqual(scenario.call_count, 2)
        self.assertTrue(all(call.kwargs["sar_result"] == sar_result for call in scenario.call_args_list))
        self.assertTrue(all("conditional_only" not in call.kwargs for call in scenario.call_args_list))
        self.assertEqual(len(result["conditional_inventory_scenarios"]), 2)


    def test_semantic_sar_masks_and_aoi_identity_reach_dashboard_payload(self):
        land = {
            "status": "SAR_MODELO_EXPERIMENTAL",
            "current_sar_crop_identification": "CLASSIFICACAO_SAR_EXPERIMENTAL_SEM_VALIDACAO_LOCAL",
            "analysis_run_id": "RUN-SINOP-01",
            "aoi_hash_sha256": "a" * 64,
            "validation": {
                "model_id": "ENFORM_SAR_BRASIL_RF_V2",
                "model_sha256": "b" * 64,
                "observed_season": "2025/2026",
                "local_validation_status": "NAO_REALIZADA",
                "validation_scope": "EXTRAPOLACAO_NACIONAL_EXPERIMENTAL",
            },
            "classes": [
                {"class_name": "Formação florestal", "area_ha": 3.2, "area_pct": 32.0,
                 "source": "SAR_EXPERIMENTAL_MODELO", "taxonomy": "RF 2025/2026",
                 "native_status": True, "land_use_group": "Vegetação nativa"},
                {"class_name": "Lavoura de soja", "area_ha": 2.1, "area_pct": 21.0,
                 "source": "SAR_EXPERIMENTAL_MODELO", "taxonomy": "RF 2025/2026",
                 "native_status": False, "land_use_group": "Uso agropecuário/cultivado"},
            ],
        }
        payload = _sar_dashboard_payload({"strata": []}, land)
        semantic = payload["semantic_land_use"]
        self.assertEqual(payload["analysis_run_id"], "RUN-SINOP-01")
        self.assertEqual(payload["aoi_hash_sha256"], "a" * 64)
        self.assertEqual(semantic["status"], "CLASSIFICACAO_SAR_EXPERIMENTAL_SEM_VALIDACAO_LOCAL")
        self.assertEqual(semantic["model_id"], "ENFORM_SAR_BRASIL_RF_V2")
        self.assertEqual(semantic["observed_season"], "2025/2026")
        self.assertEqual(semantic["class_count"], 2)
        self.assertAlmostEqual(semantic["area_ha"], 5.3)
        self.assertEqual(semantic["classes"][1]["class_name"], "Lavoura de soja")

    def test_none_height_pixel_count_does_not_break_dashboard_handoff(self):
        payload = _sar_dashboard_payload({"strata": [{
            "class_name": "Floresta Ombrófila Densa",
            "sar_details": {"height_n_valid_pixels": None,
                            "height_mean_m": None,
                            "agb_mg_ha": None,
                            "stats": []},
        }]}, {})
        self.assertEqual(payload["status"], "SAR_N/D")
        self.assertEqual(payload["strata"][0]["height_n_valid_pixels"], None)
        self.assertEqual(payload["height_products"], [])

    def test_cci_agb_provenance_does_not_replace_fh_height_provenance(self):
        native={"strata":[{"class_name":"Formação florestal","physiognomy":"Floresta",
            "sar_details":{"data_origin":"SAR_DERIVED_CCI",
                "product":"ESA CCI Biomass AGB","source":"ESA CCI AGB v7",
                "paths":["cci_agb.tif","cci_sd.tif"],"agb_mg_ha":180.0,
                "height_mean_m":24.5,"height_n_valid_pixels":120,
                "height_metric":None,"height_route_status":"ALTURA_SAR_PROCESSADA",
                "sar_height":{"height_mean_m":24.5,"height_sd_m":3.0,
                    "height_n_valid_pixels":120,"height_metric":"ESA BIOMASS upper forest canopy height H100",
                    "height_error_kind":"spatial standard deviation",
                    "height_route_status":"ALTURA_SAR_PROCESSADA","product":"FP_FH__L2A",
                    "sensor":"ESA BIOMASS","band":"P","source":"ESA BIOMASS FH",
                    "paths":["fh_height.tiff"],"height_pixel_distribution":{"status":"SAR_PIXELS_HISTOGRAMMED"}}}}]}
        payload=_sar_dashboard_payload(native,{})
        height=payload["height_products"][0]
        self.assertEqual(height["product"],"FP_FH__L2A")
        self.assertEqual(height["source"],"ESA BIOMASS FH")
        self.assertEqual(height["paths"],["fh_height.tiff"])
        self.assertEqual(height["agb_product"],"ESA CCI Biomass AGB")
        self.assertEqual(height["agb_source"],"ESA CCI AGB v7")
        self.assertEqual(_verified_sar_height_details(native["strata"][0]["sar_details"])["source"],"ESA BIOMASS FH")

    def test_cci_payload_without_nested_height_does_not_invent_height_product(self):
        payload=_sar_dashboard_payload({"strata":[{"class_name":"Floresta","sar_details":{
            "data_origin":"SAR_DERIVED_CCI","product":"ESA CCI Biomass AGB",
            "source":"ESA CCI AGB v7","height_mean_m":24.5,
            "height_n_valid_pixels":120,"height_metric":None}}]}, {})
        self.assertEqual(payload["height_products"],[])
        self.assertEqual(_verified_sar_height_details({"product":"ESA CCI Biomass AGB",
            "height_mean_m":24.5,"height_n_valid_pixels":120}),{})


if __name__ == "__main__":
    unittest.main()
