"""Always-available SAR classifier (owner decision 8A) trained on LEM+ field labels."""
import hashlib
import json
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import box

import sar_landcover_lemplus as sl
from land_use_sar import run_land_use

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
             patch("sar_model_discovery.discover_installed_sar_configs", return_value=([], [])):
            return run_land_use(AOI, d, ibge=ib)

    def test_in_domain_classes_are_sar_and_native_named_by_ibge(self):
        r = self._run("Savana Arborizada")
        names = {c["class_name"]: c for c in r["classes"]}
        self.assertIn("Lavoura de Soja", names); self.assertIs(names["Lavoura de Soja"]["native_status"], False)
        self.assertIn("Savana Arborizada", names); self.assertIs(names["Savana Arborizada"]["native_status"], True)
        self.assertFalse(any(str(c["source"]).startswith("MAPBIOMAS") for c in r["classes"]))

    def test_out_of_domain_output_is_not_used(self):
        r = self._run("Estepe Arborizada")
        self.assertFalse(any(str(c["source"]).startswith("SAR_VALIDADO") for c in r["classes"]))
        self.assertTrue(any(str(c["source"]).startswith("SAR_EXPERIMENTAL_MODELO") for c in r["classes"]))
        self.assertIn("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL", r["sar_classifier_lemplus"]["domain"])


if __name__ == "__main__":
    unittest.main()
