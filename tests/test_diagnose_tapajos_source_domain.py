"""Contract tests: no Brazilian inference from an Africa-only SAR archive."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch

import numpy as np

from tools import diagnose_tapajos_2010_height as diagnostic


class TapajosSourceDomainTests(unittest.TestCase):
    def test_brazil_is_outside_deafrica_distribution(self):
        self.assertTrue(diagnostic.outside_deafrica_envelope(
            [{"lon": "-54.95", "lat": "-3.03"}]))
        self.assertFalse(diagnostic.outside_deafrica_envelope(
            [{"lon": "11.5", "lat": "-1.0"}]))
        self.assertFalse(diagnostic.outside_deafrica_envelope([]))

    def test_tapajos_diagnostic_never_queries_african_s3(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "diagnostic.json"
            with patch.object(diagnostic, "OUT", report), patch.object(
                    diagnostic, "list_objects", side_effect=AssertionError("African archive queried")):
                self.assertEqual(diagnostic.main(), 0)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "BLOCKED_SOURCE_GEOGRAPHY")
            self.assertFalse(result["deployable"])
            self.assertFalse(result["height_product_available"])
            self.assertIsNone(result["height_sar_m"])
            self.assertEqual(urlsplit(result["global_alternative"]).hostname, "www.eorc.jaxa.jp")
            self.assertEqual(urlsplit(result["global_alternative"]).scheme, "https")
            self.assertIn("JAXA", result["global_access"])
            self.assertFalse(result["scientific_validation"])

    def test_diagnostic_uses_jaxa_ensemble_power(self):
        dn = np.array([100, 100, 300], dtype=np.uint16)
        expected = 10 * math.log10((100 ** 2 + 100 ** 2 + 300 ** 2) / 3) - 83
        self.assertAlmostEqual(diagnostic.gamma0_db_from_dn(dn), expected)
        self.assertNotAlmostEqual(diagnostic.gamma0_db_from_dn(dn), -43.0, places=3)

    def test_pixel_centers_outside_plot_are_not_training_pairs(self):
        lon, lat = -54.95, -3.03
        # ~30 m offsets; should not be used as 50x50 m field plot pixels.
        dlon = 30.0 / (111320.0 * np.cos(np.deg2rad(lat)))
        dlat = 30.0 / 111320.0
        lons = np.array([[lon, lon + dlon], [lon, lon]])
        lats = np.array([[lat, lat], [lat + dlat, lat]])
        mask = diagnostic.plot_footprint_mask(lons, lats, lon, lat)
        np.testing.assert_array_equal(mask, np.array([[True, False], [False, True]]))


if __name__ == "__main__":
    unittest.main()
