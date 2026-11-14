"""End-to-end handoff contract: worker queue -> core result -> app dashboards."""
import json
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

from desktop_app import App, native_carbon_analysis
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
                "sar_details": {"stats": [{
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
        class InlineThread:
            def __init__(self, target, **_kwargs):
                self.target = target
                worker_threads.append(self)
            def start(self):
                self.target()

        import sys
        import types
        pedology_module = types.ModuleType("soil_pedology_embrapa")
        pedology_module.analyze_embrapa_pedology = lambda *_args, **_kwargs: ({"status": "OK"}, [])
        fertility_module = types.ModuleType("soil_fertility_zonal")
        fertility_module.analyze_fertility = lambda *_args, **_kwargs: {"status": "OK"}
        with patch("desktop_app.threading.Thread", InlineThread), \
             patch("desktop_app.load_ibge_land_use_reference", return_value=(None, "legenda_1")), \
             patch("desktop_app.run_land_use", return_value=land) as land_use, \
             patch("desktop_app.native_carbon_analysis", return_value=native) as carbon, \
             patch.dict(sys.modules, {"soil_pedology_embrapa": pedology_module,
                                      "soil_fertility_zonal": fertility_module}):
            App.execute(app)
        self.assertEqual(len(worker_threads), 1)
        land_use.assert_called_once()
        self.assertEqual(land_use.call_args.kwargs["sar_paths"], sar_paths)
        carbon.assert_called_once()
        self.assertEqual(carbon.call_args.kwargs["sar_paths"], sar_paths)
        run_id, kind, payload = app._analysis_queue.get_nowait()
        self.assertEqual((run_id, kind), (1, "ok"))
        self.assertEqual(payload["land_use"], land)

    def test_inventory_fallback_reuses_one_aoi_wide_sar_result(self):
        aoi = gpd.GeoDataFrame(geometry=[box(-55.0, -4.0, -54.99, -3.99)], crs="EPSG:4326")
        land = {
            "vector_path": "land.geojson",
            "validation": {},
            "potential_physiognomy_intersections": [
                {"name": "Floresta teste A", "area_ha": 1.0},
                {"name": "Floresta teste B", "area_ha": 2.0},
            ],
        }
        native = {"known_total_tc": None, "area_aoi_ha": 3.0, "strata": [], "components": []}
        sar_result = {"status": "SAR_NAO_PROCESSADO", "reason": "fixture"}
        with patch("geopandas.read_file", return_value=aoi), \
             patch("desktop_app.summarize_native_carbon", return_value=native), \
             patch("sar_pipeline.biomass_l2b_search", return_value=([], {"queries": [], "errors": []})), \
             patch("desktop_app.automatic_pipeline", return_value=sar_result) as pipeline, \
             patch("ifn_carbon_fallback.estimate_inventory_carbon_scenario",
                   return_value={"status": "CENARIO_CONDICIONAL_INVENTARIO_SEM_AGB_ALTURA_SAR"}) as scenario:
            result = native_carbon_analysis(aoi, land, "Amazônia")
        self.assertEqual(pipeline.call_count, 1)
        self.assertEqual(scenario.call_count, 2)
        self.assertTrue(all(call.kwargs["sar_result"] is sar_result for call in scenario.call_args_list))
        self.assertEqual(len(result["conditional_inventory_scenarios"]), 2)


if __name__ == "__main__":
    unittest.main()
