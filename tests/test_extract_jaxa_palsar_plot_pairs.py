"""Regression tests for JAXA plot/pixel extraction; synthetic rasters test code only."""
import csv
from datetime import date
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from tools.extract_jaxa_palsar_plot_pairs import extract, sha256_file

HAVE_RASTERIO = importlib.util.find_spec("rasterio") is not None
HAVE_NUMPY = importlib.util.find_spec("numpy") is not None


@unittest.skipUnless(HAVE_RASTERIO and HAVE_NUMPY, "rasterio and numpy required")
class JAXAPlotPairTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = {}
        self.rasters = {}
        transform = from_origin(-55.00033, -2.99967, 0.00022, 0.00022)
        values = {"hh": (100, "uint16"), "hv": (50, "uint16"),
                  "mask": (255, "uint8"),
                  "date": ((date(2010, 9, 1) - date(2006, 1, 24)).days + 1, "uint16")}
        for name, (value, dtype) in values.items():
            path = self.root / (name + ".tif")
            with rasterio.open(path, "w", driver="GTiff", width=3, height=3, count=1,
                               dtype=dtype, crs="EPSG:4326", transform=transform) as ds:
                ds.write(np.full((3, 3), value, dtype=dtype), 1)
            self.rasters[name] = path
        self.plots = self.root / "plots.csv"
        self.plots.write_text("plot,lon,lat,h100_field_m\n1,-55.0,-3.0,28.0\n",
                              encoding="utf-8")

    def audit(self, year=2010, bad_sha=None):
        hashes = {k: sha256_file(v) for k, v in self.rasters.items()}
        if bad_sha:
            hashes[bad_sha] = "0" * 64
        return extract(self.rasters, hashes, self.plots, sha256_file(self.plots), year)

    def test_real_file_pairs_are_not_sar_height_or_scientific_validation(self):
        result = self.audit()
        self.assertEqual(result["n_pairs"], 1)
        row = result["pairs"][0]
        self.assertEqual(row["status"], "paired_unvalidated")
        self.assertEqual(row["pixels_inside_plot"], 9)
        self.assertAlmostEqual(row["hh_gamma0_db"], -43.0)
        self.assertAlmostEqual(row["hv_gamma0_db"], -49.020599913, places=5)
        self.assertEqual(row["observed_date_range"], ["2010-09-01", "2010-09-01"])
        self.assertIsNone(result["height_sar_m"])
        self.assertFalse(result["scientifically_validated"])
        self.assertFalse(result["source_identity_independently_verified"])
        self.assertFalse(result["aoi_ci95_validated"])

    def test_wrong_acquisition_year_is_not_pair(self):
        result = self.audit(year=2009)
        self.assertEqual(result["n_pairs"], 0)
        self.assertEqual(result["pairs"][0]["status"], "acquisition_year_mismatch")

    def test_sha_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.audit(bad_sha="hh")

    def test_non_land_mask_excluded(self):
        import numpy as np
        import rasterio
        with rasterio.open(self.rasters["mask"], "r+") as ds:
            ds.write(np.full((3, 3), 100, dtype="uint8"), 1)
        result = self.audit()
        self.assertEqual(result["n_pairs"], 0)
        self.assertEqual(result["pairs"][0]["status"], "no_valid_footprint_pixel")

    def test_grid_mismatch_rejected(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        with rasterio.open(self.rasters["hv"], "r+") as ds:
            ds.transform = from_origin(-55.001, -2.99967, 0.00022, 0.00022)
        with self.assertRaisesRegex(ValueError, "grid"):
            self.audit()

    def test_duplicate_plot_rejected(self):
        with self.plots.open("a", encoding="utf-8") as stream:
            stream.write("1,-55.0,-3.0,28.0\n")
        with self.assertRaisesRegex(ValueError, "unique"):
            self.audit()


if __name__ == "__main__":
    unittest.main()
