"""Synthetic integrity tests; map pseudo-labels cannot validate crop identification."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from crop_map_training import extract_pseudolabel_training_samples


class CropMapTrainingTests(unittest.TestCase):
    def fixture(self, base):
        transform = from_origin(500000, 9000000, 10, 10)
        features = Path(base) / "sar.tif"
        labels = Path(base) / "agriculture.tif"
        with rasterio.open(features, "w", driver="GTiff", height=20, width=20,
                           count=2, dtype="float32", crs="EPSG:32722",
                           transform=transform) as dst:
            dst.write(np.ones((2, 20, 20), dtype="float32"))
        with rasterio.open(labels, "w", driver="GTiff", height=20, width=20,
                           count=1, dtype="uint8", crs="EPSG:32722",
                           transform=transform) as dst:
            a = np.zeros((20, 20), dtype="uint8")
            a[2:10, 2:10] = 39
            a[11:19, 11:19] = 46
            dst.write(a, 1)
        return features, labels

    def test_extract_is_training_only_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = self.fixture(d)
            result = extract_pseudolabel_training_samples(
                a, b, Path(d)/"pseudo.geojson",year=2025,feature_year=2025,
                reference_url="https://brasil.mapbiomas.org/",max_per_class=5)
            self.assertEqual(result["counts"]["Soja"],5)
            self.assertEqual(result["counts"]["Café"],5)
            self.assertFalse(result["validation_eligible"])
            import json
            data = json.loads(Path(result["path"]).read_text())
            self.assertTrue(all(f["properties"]["training_only"] for f in data["features"]))
            self.assertTrue(all(f["properties"]["split"]=="train" for f in data["features"]))

    def test_mismatched_year_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=self.fixture(d)
            with self.assertRaisesRegex(ValueError,"Safra"):
                extract_pseudolabel_training_samples(a,b,Path(d)/"p.geojson",
                    year=2025,feature_year=2024,reference_url="https://brasil.mapbiomas.org/")

    def test_unsupported_second_season_must_not_use_first_season_legend(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=self.fixture(d)
            with self.assertRaisesRegex(ValueError,"Produto/legenda"):
                extract_pseudolabel_training_samples(a,b,Path(d)/"p.geojson",
                    reference_kind="mapbiomas_c11_second_season",
                    year=2025,feature_year=2025,reference_url="https://brasil.mapbiomas.org/")


if __name__=="__main__":
    unittest.main()
