import tempfile
import unittest
from pathlib import Path

import numpy as np

from terraclass_sar_experiment import terraclass_category, train_spatial_map_agreement


class TerraClassCategoryTests(unittest.TestCase):
    def test_normalizes_supported_official_legend_names(self):
        self.assertEqual(terraclass_category("Vegetação Natural Primária"), "Vegetação nativa")
        self.assertEqual(terraclass_category("Cultura Agrícola Temporária de Mais de 1 Ciclo"), "Agricultura")
        self.assertIsNone(terraclass_category("Não Observado"))
        self.assertIsNone(terraclass_category("any arbitrary label"))

    def test_requires_exact_supported_domain_and_matched_year(self):
        with self.assertRaisesRegex(ValueError, "domínio"):
            train_spatial_map_agreement("x.tif", "x.gpkg", "x.joblib", "x.json",
                label_field="classe", domain="pantanal", reference_year=2024,
                feature_year=2024)
        with self.assertRaisesRegex(ValueError, "Ano"):
            train_spatial_map_agreement("x.tif", "x.gpkg", "x.joblib", "x.json",
                label_field="classe", domain="amazonia", reference_year=2024,
                feature_year=2025)

    def test_reports_only_spatial_map_agreement_for_synthetic_fixture(self):
        try:
            import geopandas as gpd
            import rasterio
            from rasterio.transform import from_origin
            from shapely.geometry import box
            import sklearn  # noqa: F401
        except ImportError:
            self.skipTest("geospatial/ML dependencies not installed")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raster_path = root / "features.tif"
            reference_path = root / "labels.gpkg"
            rng = np.random.default_rng(4)
            features = rng.normal(0, 0.1, size=(2, 20, 20)).astype("float32")
            features[0, :, 10:] += 2.0
            features[1, :, 10:] += 1.0
            with rasterio.open(raster_path, "w", driver="GTiff", height=20, width=20,
                               count=2, dtype="float32", crs="EPSG:6933",
                               transform=from_origin(0, 10000, 500, 500)) as dst:
                dst.write(features)
            gpd.GeoDataFrame(
                {"classe": ["Vegetação Natural Primária", "Cultura Agrícola Temporária"]},
                geometry=[box(0, 0, 5000, 10000), box(5000, 0, 10000, 10000)],
                crs="EPSG:6933").to_file(reference_path, driver="GPKG")
            report = train_spatial_map_agreement(
                raster_path, reference_path, root / "exp.joblib", root / "report.json",
                label_field="classe", domain="amazonia", reference_year=2024,
                feature_year=2024, block_size_m=1000)
            self.assertEqual(report["status"], "EXPERIMENTAL_MAP_AGREEMENT_ONLY")
            self.assertFalse(report["field_validation"])
            self.assertFalse(report["release_eligible"])
            self.assertEqual(report["n_spatial_blocks"], 100)
            self.assertEqual(set(report["class_names"]), {"Vegetação nativa", "Agricultura"})
            self.assertEqual(report["reference"]["prodes_used_as_label"], False)
            for metrics in report["per_class_map_agreement"].values():
                self.assertEqual(len(metrics["precision_ci95_block_bootstrap"]), 2)
                self.assertEqual(len(metrics["recall_ci95_block_bootstrap"]), 2)
                self.assertEqual(metrics["bootstrap_blocks"], 100)
            self.assertTrue((root / "exp.joblib").is_file())
            self.assertTrue((root / "report.json").is_file())


if __name__ == "__main__":
    unittest.main()
