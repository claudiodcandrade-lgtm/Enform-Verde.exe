"""Always-available SAR classifier (owner decision 8A) trained on LEM+ field labels."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

import sar_landcover_lemplus as sl
from land_use_sar import report_lines, run_land_use

AOI = gpd.GeoDataFrame(geometry=[box(-45.90, -12.30, -45.86, -12.26)], crs=4326)


def fake_result():
    eq = AOI.to_crs(6933).geometry.iloc[0]
    minx, miny, maxx, maxy = eq.bounds
    midx = (minx + maxx) / 2
    polys = gpd.GeoDataFrame({"class_name": ["Vegetação nativa (assinatura SAR)", "Lavoura de Soja"]},
                             geometry=[box(minx, miny, midx, maxy), box(midx, miny, maxx, maxy)], crs=6933)
    return {"status": "SAR_CLASSIFICADOR_EXPERIMENTAL", "model_id": "ENFORM_SAR_LEMPLUS_RF_V1", "season": "2025/2026",
            "classes": [], "polygons_6933": polys}


class LemplusModelTests(unittest.TestCase):
    def test_primary_classifier_has_binary_mpc_aoi_cog_fallback(self):
        source=Path(sl.__file__).read_text(encoding="utf-8")
        body=source[source.index("def _monthly_features"):source.index("def _safe_error_detail")]
        self.assertIn('for attempt in ((0,4) if provider=="MPC" else (0,1))',body)
        self.assertNotIn('"GDAL_HTTP_TIMEOUT":"45"',body)
        self.assertIn("_open_signed_cog_via_https(",body)
        self.assertIn('"HTTPS_BINARY_AOI_CROP"',body)
        self.assertIn("max_bytes=128*1024*1024",body)
        self.assertIn("max_crop_bytes=128*1024*1024",body)

    def test_contingency_runs_when_recent_s1_pixels_exist_but_semantic_model_fails(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        recent={"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES","scene_count":12,
                "readable_scene_count":12,"vector_path":None,"raster_path":None,
                "provider_processing_diagnostics":[{"provider":"MPC","readable_scene_count":12}],
                "failed_scene_reads":[]}
        alternative={"status":"ALTERNATIVE_RADAR_PIXELS_PROCESSED",
                     "classification_status":"N/D_VALIDACAO"}
        ib=AOI.copy();ib["legenda_1"]="Floresta Ombrófila Densa"
        with tempfile.TemporaryDirectory() as d, \
             patch("sar_model_discovery.discover_installed_sar_configs",return_value=([],[])), \
             patch("sar_landcover_lemplus.classify_aoi",return_value={
                 "status":"ERRO_TECNICO_LEITURA_SAR","reason":"UnicodeDecodeError"}), \
             patch("recent_sar_landcover.run_recent_sar_screen",return_value=recent), \
             patch("radar_contingency.run_alternative_radar_screen",return_value=alternative) as contingency, \
             patch("native_sar_experimental.run_sentinel1_native_screen",return_value={"status":"N/D"}), \
             patch("crop_mapbiomas_pam_fallback.build_mapbiomas_pam_contingency",return_value={"status":"N/D"}):
            result=run_land_use(AOI,d,ibge=ib)
        contingency.assert_called_once()
        self.assertEqual(result["alternative_radar_screen"]["status"],"ALTERNATIVE_RADAR_PIXELS_PROCESSED")
        self.assertEqual(result["alternative_radar_screen"]["trigger_reason"],
                         "PRIMARY_SEMANTIC_CLASSIFICATION_UNAVAILABLE")
        report="\n".join(report_lines(result))
        self.assertIn("Gatilho: PRIMARY_SEMANTIC_CLASSIFICATION_UNAVAILABLE",report)

    def test_applied_lemplus_result_does_not_report_no_sar_classifier(self):
        import tempfile
        from unittest.mock import patch
        ib=AOI.copy();ib["legenda_1"]="Floresta Estacional Sempre-Verde"
        recent={"status":"N/D_SEM_PIXELS_SAR","scene_count":0,"vector_path":None,
                "raster_path":None,"provider_processing_diagnostics":[],"failed_scene_reads":[]}
        with tempfile.TemporaryDirectory() as d, \
             patch("sar_model_discovery.discover_installed_sar_configs",return_value=([],[
                 "Identificadores SAR não instalados no diretório /tmp/modelos_sar.",
                 "Nenhum identificador SAR executável compatível instalado; usar mapa de cobertura atual."])), \
             patch("sar_landcover_lemplus.classify_aoi",return_value=fake_result()), \
             patch("recent_sar_landcover.run_recent_sar_screen",return_value=recent), \
             patch("radar_contingency.run_alternative_radar_screen",return_value={"status":"NOT_NEEDED"}), \
             patch("native_sar_experimental.run_sentinel1_native_screen",return_value={"status":"N/D"}), \
             patch("crop_mapbiomas_pam_fallback.build_mapbiomas_pam_contingency",return_value={"status":"N/D"}):
            result=run_land_use(AOI,d,ibge=ib)
        self.assertFalse(result["sar_classifier_lemplus"]["result_applied_to_current_aoi"])
        self.assertTrue(result["sar_classifier_lemplus"]["result_applied_to_annual_map"])
        self.assertEqual(result["sar_classifier_lemplus"]["current_semantic_classification"],False)
        self.assertEqual(result["alternative_radar_screen"]["trigger_reason"],
                         "PRIMARY_SEMANTIC_CLASSIFICATION_UNAVAILABLE")
        self.assertIn("último ano agrícola completo", "\n".join(report_lines(result)))
        warnings="\n".join(result.get("warnings",[]))
        self.assertNotIn("Nenhum identificador SAR semântico operacional foi aplicado",warnings)
        self.assertNotIn("Nenhum identificador SAR executável compatível instalado",warnings)
        self.assertNotIn("Identificadores SAR não instalados no diretório",warnings)
        self.assertIn("SAR EXPERIMENTAL",warnings)

    def test_manifest_hash_metrics_and_labels(self):
        man = json.loads(sl.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(sl.MODEL.read_bytes()).hexdigest(), man["sha256"])
        self.assertFalse(man["mapbiomas_used"])
        self.assertIn("LEM+", man["training_labels"][0]["dataset"])
        self.assertTrue(any("Rondonia" in t["dataset"] for t in man["training_labels"]))
        lc = man["validation"]["landcover"]
        self.assertGreater(lc["overall_accuracy"], 0.9)
        self.assertIn("blocos espaciais", lc["validation"])
        self.assertGreaterEqual(lc["n_spatial_blocks"], 50)
        for cls in ("Vegetação nativa (Cerrado)", "Floresta nativa"):
            lo, hi = lc["per_class"][cls]["precision_wilson95"]
            self.assertTrue(0 < lo < hi <= 1)
        self.assertIn("Amazônia-RO (2022)", lc["by_region"])
        models, _ = sl.load()
        self.assertEqual(models["landcover"].n_features_in_, 36)

    def test_crop_identity_is_suppressed_outside_training_envelope(self):
        tapajos = gpd.GeoDataFrame(geometry=[box(-55.2,-3.2,-55.1,-3.1)],crs=4326)
        sinop = gpd.GeoDataFrame(geometry=[box(-55.21,-11.89,-55.17,-11.855)],crs=4326)
        self.assertFalse(sl._aoi_in_training_envelope(tapajos))
        self.assertTrue(sl._aoi_in_training_envelope(sinop))
        labels=sl._crop_labels_with_domain_guard(["Soja","Café"],False)
        self.assertEqual(list(labels),[sl.UNIDENTIFIED_CROP,sl.UNIDENTIFIED_CROP])
        self.assertEqual(list(sl._crop_labels_with_domain_guard(["Soja"],True)),["Soja"])

    def test_model_loader_blocks_incompatible_sklearn_runtime(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            manifest = Path(d) / "model.json"
            manifest.write_text(json.dumps({
                "sha256": hashlib.sha256(sl.MODEL.read_bytes()).hexdigest(),
                "runtime_dependencies": {"scikit-learn": "0.0-test-mismatch"},
            }), encoding="utf-8")
            with patch.object(sl, "_resource", side_effect=[manifest, sl.MODEL]):
                with self.assertRaisesRegex(RuntimeError, "VERSAO_SKLEARN_INCOMPATIVEL"):
                    sl.load()

    def test_agricultural_year_is_last_complete_oct_sep(self):
        months, season = sl.agricultural_year(date(2026, 11, 8))
        self.assertEqual(season, "2025/2026"); self.assertEqual(months[0], (2025, 10)); self.assertEqual(months[-1], (2026, 9))
        self.assertEqual(sl.agricultural_year(date(2026, 3, 1))[1], "2024/2025")

    def test_domain_gate(self):
        ib = AOI.copy(); ib["legenda_1"] = "Savana Arborizada"
        self.assertTrue(sl.in_validated_domain(ib)[0])
        ib["legenda_1"] = "Floresta Estacional Sempre-Verde"
        self.assertTrue(sl.in_validated_domain(ib)[0])                     # Amazon forest inside MT/RO envelope
        far = gpd.GeoDataFrame({"legenda_1": ["Floresta Ombrófila Densa"]}, geometry=[box(-43.3, -22.9, -43.2, -22.8)], crs=4326)
        outside_ok, outside_msg = sl.in_validated_domain(far)
        self.assertTrue(outside_ok)  # national pilot executes, but extrapolation is explicitly unvalidated
        self.assertIn("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL", outside_msg)
        ib["legenda_1"] = "Estepe"
        extrap_ok, extrap_msg = sl.in_validated_domain(ib)
        self.assertTrue(extrap_ok)
        self.assertIn("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL", extrap_msg)
        self.assertFalse(sl.in_validated_domain(None)[0])


class UnidentifiedCropTests(unittest.TestCase):
    def test_unidentified_crop_is_labelled_cultivated_area_and_not_native(self):
        from native_carbon import native_class
        self.assertEqual(sl.CROP_NAMES[sl.UNIDENTIFIED_CROP], "Área cultivada — cultura não identificada")
        self.assertFalse(native_class(sl.UNIDENTIFIED_CROP, "SAR_VALIDADO", {}))
        self.assertEqual(sl.CROP_MAJORITY, 0.5)


class LandUseIntegrationTests(unittest.TestCase):
    def _run(self, legend):
        ib = AOI.copy(); ib["legenda_1"] = legend
        with tempfile.TemporaryDirectory() as d, \
             patch("sar_landcover_lemplus.classify_aoi", return_value=fake_result()), \
             patch("recent_sar_landcover.run_recent_sar_screen", return_value={"status": "N/D_DADOS", "reason": "offline"}), \
             patch("radar_contingency.run_alternative_radar_screen", return_value={"status":"N/D_DADOS","reason":"offline","classification_status":"N/D_VALIDACAO"}), \
             patch("crop_mapbiomas_pam_fallback.build_mapbiomas_pam_contingency", return_value={"status":"N/D","reason":"fixture offline"}), \
             patch("sar_model_discovery.discover_installed_sar_configs", return_value=([], [])):
            return run_land_use(AOI, d, ibge=ib)

    def test_in_domain_classes_preserve_experimental_sar_identity(self):
        r = self._run("Savana Arborizada")
        names = {c["class_name"]: c for c in r["classes"]}
        self.assertIn("Lavoura de Soja", names)
        self.assertIs(names["Lavoura de Soja"]["native_status"], False)
        # SAR establishes the native polygon; the EXACT IBGE intersection
        # supplies a botanical name, never a new vegetation mask.
        self.assertIn("Savana Arborizada", names)
        self.assertIs(names["Savana Arborizada"]["native_status"], True)
        self.assertEqual(names["Savana Arborizada"]["source"],
                         "SAR_EXPERIMENTAL_MODELO+IBGE")
        self.assertNotIn("Formação savânica", names)
        self.assertAlmostEqual(sum(c["area_ha"] for c in r["classes"]),
                               r["area_aoi_ha"], places=4)
        self.assertFalse(any(str(c["source"]).startswith("MAPBIOMAS") for c in r["classes"]))
        audit=r["sar_classifier_lemplus"]
        self.assertTrue(audit["model_call_attempted"])
        self.assertFalse(audit["result_applied_to_current_aoi"])
        self.assertTrue(audit["result_applied_to_annual_map"])
        self.assertFalse(audit["current_semantic_classification"])
        self.assertEqual(audit["temporal_scope"],
                         "ULTIMO_ANO_AGRICOLA_COMPLETO; NÃO REPRESENTA COBERTURA ATUAL")
        self.assertEqual(audit["execution_scope"],"AOI_INTEGRAL_ULTIMO_ANO_AGRICOLA_COMPLETO")
        self.assertAlmostEqual(audit["aoi_area_ha"],r["area_aoi_ha"],places=5)
        self.assertTrue(audit["aoi_sha256_wgs84"])
        self.assertIn("mapa anual aplicado=True","\n".join(report_lines(r)))
        self.assertEqual(r["alternative_radar_screen"]["trigger_reason"],
                         "PRIMARY_SEMANTIC_CLASSIFICATION_UNAVAILABLE")

    def test_existing_sar_classifier_records_lemplus_as_not_executed(self):
        predicted = gpd.GeoDataFrame(
            {"class_name": ["Soja"], "source": ["SAR_VALIDADO_TESTE"],
             "taxonomy": ["teste"]}, geometry=AOI.geometry, crs=AOI.crs)
        validation = {"class_metadata": {"Soja": {"parent": "uso agrícola"}}}
        ib = AOI.copy(); ib["legenda_1"] = "Savana Arborizada"
        with tempfile.TemporaryDirectory() as d, \
             patch("sar_model_discovery.discover_installed_sar_configs", return_value=(["modelo.json"], [])), \
             patch("land_use_sar.classify_config", return_value=(predicted, validation)), \
             patch("sar_landcover_lemplus.classify_aoi") as classify_lemplus, \
             patch("recent_sar_landcover.run_recent_sar_screen", return_value={"status": "N/D_DADOS", "reason": "offline"}), \
             patch("radar_contingency.run_alternative_radar_screen", return_value={"status":"N/D_DADOS","reason":"offline","classification_status":"N/D_VALIDACAO"}), \
             patch("crop_mapbiomas_pam_fallback.build_mapbiomas_pam_contingency", return_value={"status":"N/D","reason":"fixture offline"}):
            r = run_land_use(AOI, d, ibge=ib)
        classify_lemplus.assert_not_called()
        audit = r["sar_classifier_lemplus"]
        self.assertEqual(audit["status"], "NOT_EXECUTED")
        self.assertEqual(audit["execution_scope"], "NOT_EXECUTED")
        self.assertFalse(audit["model_call_attempted"])
        self.assertFalse(audit["result_applied_to_current_aoi"])

    def test_out_of_domain_output_is_not_used(self):
        r = self._run("Estepe Arborizada")
        self.assertFalse(any(str(c["source"]).startswith("SAR_VALIDADO") for c in r["classes"]))
        self.assertTrue(any(str(c["source"]).startswith("SAR_EXPERIMENTAL_MODELO") for c in r["classes"]))
        self.assertIn("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL", r["sar_classifier_lemplus"]["domain"])


if __name__ == "__main__":
    unittest.main()
