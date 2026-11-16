import unittest
import importlib.util
from types import SimpleNamespace
from unittest.mock import patch

import sar_landcover_lemplus as sar


class _Geometry:
    def __init__(self, minx, miny, maxx, maxy):
        self.bounds = (minx, miny, maxx, maxy)

    def union_all(self):
        return self


class _Frame:
    def __init__(self, minx, miny, maxx, maxy):
        self.geometry = _Geometry(minx, miny, maxx, maxy)

    def to_crs(self, _crs):
        return self


class SarCropDomainPolicyTests(unittest.TestCase):
    def test_tapajos_outside_domain_keeps_agriculture_but_suppresses_crop_names(self):
        # Approximate Tapajos km 83 location, north of the model's training envelope.
        aoi = _Frame(-55.2, -3.2, -55.1, -3.1)
        self.assertFalse(sar._aoi_in_training_envelope(aoi))
        self.assertEqual(
            list(sar._crop_labels_with_domain_guard(["Soja", "Café"], False)),
            [sar.UNIDENTIFIED_CROP, sar.UNIDENTIFIED_CROP],
        )

    def test_sinop_inside_domain_retains_experimental_crop_predictions(self):
        aoi = _Frame(-55.21, -11.89, -55.17, -11.855)
        self.assertTrue(sar._aoi_in_training_envelope(aoi))
        self.assertEqual(
            list(sar._crop_labels_with_domain_guard(["Soja", "Café"], True)),
            ["Soja", "Café"],
        )

    def test_entire_aoi_must_fit_envelope_not_only_its_center(self):
        # Center is in the envelope, but part of this AOI extends north of it.
        aoi = _Frame(-55.2, -8.0, -55.0, -7.0)
        self.assertFalse(sar._aoi_in_training_envelope(aoi))

    def test_generic_experimental_crop_does_not_enter_crop_specific_forecast(self):
        from crop_monitoring_forecast import experimental_crops_in_land_result
        land={"classes":[{"class_name":sar.UNIDENTIFIED_CROP,"area_ha":1.92,
                           "source":"SAR_EXPERIMENTAL_MODELO"}]}
        self.assertEqual(experimental_crops_in_land_result(land),{})

    def test_80m_pixel_area_explains_064_ha_label_granularity(self):
        self.assertEqual(sar.PIXEL_M * sar.PIXEL_M / 10_000, 0.64)

    @unittest.skipUnless(importlib.util.find_spec("geopandas") and
                         importlib.util.find_spec("rasterio"),
                         "geospatial dependencies are installed in the Windows CI")
    def test_classifier_applies_crop_name_guard_to_classes_and_polygons(self):
        import numpy as np
        import geopandas as gpd
        from rasterio.transform import from_bounds
        from shapely.geometry import box

        class _Classifier:
            def __init__(self, classes, probabilities):
                self.classes_ = np.asarray(classes)
                self.probabilities = np.asarray(probabilities, dtype=float)

            def predict_proba(self, features):
                return np.tile(self.probabilities, (len(features), 1))

        aoi = gpd.GeoDataFrame(
            {"id": [1]}, geometry=[box(-55.20, -3.20, -55.10, -3.10)], crs="EPSG:4326")
        projected = aoi.to_crs(6933).total_bounds
        h = w = 4
        features = np.ones((h, w, 2), dtype=float)
        data = (features, from_bounds(*projected, width=w, height=h), (h, w))
        models = {
            "landcover": _Classifier(["Cultivo agrícola"], [1.0]),
            "crop": _Classifier(["Soja", "Café"], [0.7, 0.3]),
        }
        manifest = {"model_id": "fixture", "sha256": "fixture",
                    "validation": {"landcover": {"per_class": {}}, "crop": {"per_class": {}}},
                    "training_labels": [], "domain": {"transfer_note": "outside-domain test"}}
        with patch.object(sar, "load", return_value=(models, manifest)), \
                patch.object(sar, "_monthly_features", return_value=(data, {"scenes_used": 12})):
            result = sar.classify_aoi(aoi, as_of=__import__("datetime").date(2026, 11, 16))

        self.assertEqual(result["crop_label_policy"], "SPECIFIC_CROP_SUPPRESSED_OUTSIDE_TRAINING_ENVELOPE")
        self.assertTrue(result["classes"])
        self.assertEqual({row["class_name"] for row in result["classes"]}, {sar.UNIDENTIFIED_CROP})
        self.assertIsNotNone(result["polygons_6933"])
        self.assertEqual(set(result["polygons_6933"]["class_name"]), {sar.UNIDENTIFIED_CROP})


if __name__ == "__main__":
    unittest.main()
