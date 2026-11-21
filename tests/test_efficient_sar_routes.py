"""Analysis-scoped route cache and lossless provider audit regression."""
import unittest
from unittest.mock import patch

from sar_pipeline import (
    _cci_history_for_analysis,
    _record_sentinel1_public_route,
)


class EfficientSarRouteTests(unittest.TestCase):
    def test_cci_catalog_download_search_is_shared_by_strata_in_same_tiles(self):
        route_cache = {}
        first = {"available": True, "paths": ["tile-1.tif"], "year": 2024}
        with patch("sar_pipeline._cci_v7_tile_ids",
                   side_effect=[["N00W060"], ["N00W060"], ["N00W050"]]), \
             patch("sar_pipeline.cci_history", return_value=first) as search:
            a = _cci_history_for_analysis(object(), "/tmp/cci", None, route_cache)
            b = _cci_history_for_analysis(object(), "/tmp/cci", None, route_cache)
            c = _cci_history_for_analysis(object(), "/tmp/cci", None, route_cache)
        self.assertEqual(search.call_count, 2)
        self.assertEqual(a, first)
        self.assertEqual(b, first)
        self.assertEqual(c, first)
        self.assertIsNot(a, b, "callers receive independent result dictionaries")

    def test_sentinel1_primary_success_is_not_overwritten_by_cdse(self):
        audit = {"sentinel1_public": None}
        mpc = {"route": "MPC", "pixel_state": "PROCESSADO", "stats": [{"n": 12}]}
        cdse = {"route": "CDSE", "pixel_state": "PROCESSADO", "stats": [{"n": 9}]}
        _record_sentinel1_public_route(audit, "MPC", mpc)
        _record_sentinel1_public_route(audit, "CDSE", cdse)
        self.assertEqual(audit["sentinel1_public"], mpc)
        self.assertEqual(audit["sentinel1_provider_routes"], {"MPC": mpc, "CDSE": cdse})

    def test_cdse_success_is_summary_when_mpc_has_no_pixels(self):
        audit = {"sentinel1_public": None}
        _record_sentinel1_public_route(
            audit, "MPC", {"route": "MPC", "pixel_state": "SEM_PIXELS_COMPATIVEIS"})
        cdse = {"route": "CDSE", "pixel_state": "PROCESSADO", "stats": [{"n": 9}]}
        _record_sentinel1_public_route(audit, "CDSE", cdse)
        self.assertEqual(audit["sentinel1_public"], cdse)


if __name__ == "__main__":
    unittest.main()
