import unittest
from datetime import datetime, timezone

import geopandas as gpd
from shapely.geometry import box

from crop_vigor_auto import automatic_vigor


class CropVigorSearchDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.field = gpd.GeoDataFrame(geometry=[box(-55.2, -11.9, -55.19, -11.89)], crs=4326)
        self.as_of = datetime.now(timezone.utc).date()

    def test_completed_empty_catalogs_mean_true_scene_absence(self):
        def search(*_args, **_kwargs):
            return {
                "scenes": [], "scene_count": 0, "pagination_complete": True,
                "providers": [
                    {"provider": "MPC", "status": "OK", "pagination_complete": True},
                    {"provider": "INPE", "status": "OK", "pagination_complete": True},
                ],
                "queried_at_utc": "2026-11-17T00:00:00Z",
            }

        result = automatic_vigor(self.field, self.as_of, "Soja", search=search)
        self.assertEqual(result["status"], "N/D")
        self.assertIn("sem cena Sentinel-1 RTC", result["reason"])
        self.assertEqual(result["scene_search_audit"]["scene_count"], 0)

    def test_incomplete_catalog_is_technical_error_not_scene_absence(self):
        def search(*_args, **_kwargs):
            return {
                "scenes": [], "scene_count": 0, "pagination_complete": False,
                "providers": [
                    {"provider": "MPC", "status": "ERRO_TECNICO", "pagination_complete": False},
                    {"provider": "INPE", "status": "OK", "pagination_complete": True},
                ],
                "queried_at_utc": "2026-11-17T00:00:00Z",
            }

        result = automatic_vigor(self.field, self.as_of, "Soja", search=search)
        self.assertEqual(result["status"], "ERRO_TECNICO")
        self.assertIn("ausência não comprovada", result["reason"])
        self.assertEqual(result["scene_search_audit"]["providers"][0]["status"], "ERRO_TECNICO")


if __name__ == "__main__":
    unittest.main()
