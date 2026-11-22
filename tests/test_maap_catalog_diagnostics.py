"""ESA MAAP live probe: no hidden catalog errors or false AOI coverage."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tools.verify_esa_maap_live import catalog_diagnostics


class FakeResponse:
    def __init__(self, status=200, features=None):
        self.status_code = status
        self.features = features if features is not None else []
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad catalog response")
    def json(self):
        return {"features": self.features, "links": []}


class CatalogDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.aoi = SimpleNamespace(total_bounds=(-55.21, -11.89, -55.17, -11.85))

    def test_errors_are_not_reported_as_empty_coverage(self):
        with patch("requests.get", return_value=FakeResponse(503)):
            rows = catalog_diagnostics(self.aoi)
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["status"] == "ERROR" for row in rows))
        self.assertTrue(all(row["http_status"] == 503 for row in rows))

    def test_all_collections_and_regional_context_are_checked(self):
        with patch("requests.get", return_value=FakeResponse()):
            rows = catalog_diagnostics(self.aoi)
        self.assertEqual(len(rows), 8)
        self.assertEqual(len([row for row in rows if row["scope"] == "AOI"]), 4)
        self.assertEqual(len([row for row in rows if row["scope"] == "REGIONAL_CONTEXT"]), 4)
        self.assertTrue(all(row["status"] == "OK" for row in rows))
        self.assertTrue(all(row["returned_items"] == 0 for row in rows))


if __name__ == "__main__":
    unittest.main()
