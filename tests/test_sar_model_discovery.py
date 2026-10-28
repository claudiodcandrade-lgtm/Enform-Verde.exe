"""Tests for SAR-first discovery without inventing model weights or accuracy."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box, mapping
from sar_model_discovery import discover_installed_sar_configs
from land_use_sar import run_land_use, report_lines


def fixture(registry, *, name="ativo.json", domain=None):
    registry.mkdir(parents=True, exist_ok=True)
    (registry/"observations.geojson").write_text("synthetic-fixture-only",encoding="utf-8")
    (registry/"features.tif").write_bytes(b"synthetic-fixture-only")
    cfg={
        "institution":"SYNTHETIC TEST FIXTURE — NO REAL MODEL",
        "reference_kind":"independent_observations",
        "reference_url":"https://example.invalid/synthetic",
        "publication_url":"https://example.invalid/synthetic",
        "sensor":"Sentinel-1 SAR","processing":"RTC VV/VH","period":"2025",
        "features":[{"name":"VV","unit":"linear","source":"SAR"}],
        "classes":{"Soja":{"parent":"uso agropecuário"}},
        "domain":mapping(domain or box(-51,-12,-49,-8)),
        "samples":"observations.geojson","feature_raster":"features.tif"
    }
    path=registry/name
    path.write_text(json.dumps(cfg),encoding="utf-8")
    return path

class AutomaticIdentifierDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(-50.5,-10.5,-50.4,-10.4)],crs="EPSG:4326")

    def test_installed_model_discovered_without_manual_selection(self):
        with tempfile.TemporaryDirectory() as d:
            registry=Path(d)/"modelos_sar"
            active=fixture(registry)
            paths,notes=discover_installed_sar_configs(
                self.aoi,registry_dir=registry,environ={})
            self.assertEqual(paths,[str(active.resolve())])
            self.assertFalse(any("Nenhum identificador" in item for item in notes))

    def test_outside_training_domain_never_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            path=fixture(Path(d),domain=box(-48,-7,-47,-6))
            candidates,notes=discover_installed_sar_configs(
                self.aoi,registry_dir=Path(d),environ={})
            self.assertEqual(candidates,[])
            self.assertTrue(any("fora do domínio" in item for item in notes))

    def test_missing_predictors_and_sample_files_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=fixture(Path(d))
            (Path(d)/"features.tif").unlink()
            candidates,notes=discover_installed_sar_configs(
                self.aoi,registry_dir=Path(d),environ={})
            self.assertEqual(candidates,[])
            self.assertTrue(any("ausentes" in item for item in notes))

    def test_env_explicit_config_can_be_discovered_when_registry_absent(self):
        with tempfile.TemporaryDirectory() as d:
            config=fixture(Path(d)/"external")
            paths,notes=discover_installed_sar_configs(
                self.aoi,registry_dir=Path(d)/"not_installed",
                environ={"ENFORM_LAND_USE_SAR_CONFIG":str(config)})
            self.assertEqual(paths,[str(config.resolve())])

    def test_uninstalled_config_never_fakes_sar_status(self):
        with tempfile.TemporaryDirectory() as d:
            registry=Path(d)/"empty"
            with patch.dict(os.environ,{"ENFORM_SAR_MODELS_DIR":str(registry),
                                        "ENFORM_LAND_USE_SAR_CONFIG":""}):
                with patch("land_use_sar.raster_class_polygons",
                           side_effect=RuntimeError("test offline map")),patch("time.sleep"):
                    result=run_land_use(self.aoi,Path(d)/"out",mapbiomas_path="missing.tif")
            self.assertEqual(result["sar_selection"],"NO_EXECUTABLE_SAR_CLASSIFIER")
            self.assertIsNone(result["sar_model_config"])
            self.assertEqual(result["status"],"FALLBACK_CARTOGRAFICO")
            self.assertIsNone(result["validation"])
            self.assertTrue(any("Nenhum identificador SAR" in w for w in result["warnings"]))

    def test_installed_candidate_is_executed_before_map_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            registry=Path(d)/"modelos_sar"
            active=fixture(registry)
            sar=gpd.GeoDataFrame(
                [{"class_name":"Soja","source":"SAR_VALIDADO","taxonomy":"SAR institucional",
                  "geometry":self.aoi.geometry.iloc[0]}],crs="EPSG:4326")
            validation={"class_metadata":{"Soja":{"parent":"uso agropecuário"}},
                        "gates":{}}
            with patch.dict(os.environ,{"ENFORM_SAR_MODELS_DIR":str(registry),
                                        "ENFORM_LAND_USE_SAR_CONFIG":""}):
                with patch("land_use_sar.classify_config",return_value=(sar,validation)) as trained, \
                     patch("land_use_sar.raster_class_polygons",side_effect=RuntimeError("offline")), \
                     patch("time.sleep"):
                    result=run_land_use(self.aoi,Path(d)/"output",mapbiomas_path="missing.tif")
            trained.assert_called_once()
            self.assertEqual(Path(result["sar_model_config"]),active.resolve())
            self.assertEqual(result["sar_selection"],"INSTALLED_AUTO_DISCOVERED")
            self.assertEqual(result["status"],"SAR_ELEGIVEL")
            self.assertEqual(result["classes"][0]["source"],"SAR_VALIDADO")
            self.assertIn("Identificador SAR utilizado:", "\n".join(report_lines(result)))

    def test_invalid_trained_model_does_not_override_cartography(self):
        with tempfile.TemporaryDirectory() as d:
            registry=Path(d)/"modelos_sar";fixture(registry)
            reference=self.aoi.copy();reference["legenda_1"]="Floresta Ombrófila Densa"
            with patch.dict(os.environ,{"ENFORM_SAR_MODELS_DIR":str(registry),
                                        "ENFORM_LAND_USE_SAR_CONFIG":""}):
                with patch("land_use_sar.classify_config",side_effect=ValueError("synthetic failed validation")), \
                     patch("land_use_sar.raster_class_polygons",side_effect=RuntimeError("offline")), \
                     patch("time.sleep"):
                    result=run_land_use(self.aoi,Path(d)/"out",mapbiomas_path="missing.tif",ibge=reference)
            self.assertEqual(result["status"],"FALLBACK_CARTOGRAFICO")
            self.assertIsNone(result["validation"])
            self.assertTrue(any("synthetic failed validation" in w for w in result["warnings"]))
            self.assertTrue(all(c["source"]!="SAR_VALIDADO" for c in result["classes"]))

if __name__=="__main__":
    unittest.main()
