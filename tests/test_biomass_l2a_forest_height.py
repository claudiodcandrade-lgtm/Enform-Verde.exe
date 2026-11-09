"""ESA BIOMASS P-band Level-2A Forest Height (open since 30/06/2026) is a height source."""
import unittest
from unittest.mock import patch

import sar_pipeline as sp

BASE = "https://catalog.maap.eo.esa.int/data/biomass-pdgs-01/BiomassLevel2a/2026/10/10/BIO_FP_FH__L2A_X/"


def item(pid, ptype):
    return {"id": pid, "properties": {"datetime": "2026-10-10T09:37:46Z"}, "assets": {
        "enclosure_i_fh_tiff": {"href": BASE + "bio_fp_fh__l2a_i_fh.tiff", "type": "image/tiff"},
        "enclosure_i_quality_tiff": {"href": BASE + "bio_fp_fh__l2a_i_quality.tiff", "type": "image/tiff"},
        "enclosure_fh_ql_png": {"href": BASE + "bio_fp_fh__l2a_fh_ql.png", "type": "image/png"},
        "enclosure_fh_map_kml": {"href": BASE + "bio_fp_fh__l2a_fh_map.kml", "type": "application/vnd.google-earth.kml+xml"},
        "product": {"href": "https://catalog.maap.eo.esa.int/data/zipper/x/BIO", "type": "application/zip"}}}


class BiomassL2aTests(unittest.TestCase):
    def test_only_fh_geotiff_selected_for_l2a(self):
        keys = [k for k, _ in sp._biomass_product_assets(item("BIO_FP_FH__L2A_X", "FP_FH__L2A"), "FP_FH__L2A")]
        self.assertEqual(keys, ["enclosure_i_fh_tiff"])

    def test_l2b_ranked_before_l2a_and_l2a_included(self):
        def fake(gdf, collection, limit=50, product_type=None):
            if collection == "BiomassLevel2a" and product_type == "FP_FH__L2A":
                return [item("BIO_FP_FH__L2A_X", "FP_FH__L2A")]
            if collection == "BiomassLevel2b" and product_type == "FP_FH__L2B":
                return [item("BIO_FP_FH__L2B_Y", "FP_FH__L2B")]
            return []
        with patch.object(sp, "maap_search", side_effect=fake):
            out = sp.biomass_l2b_search(None)
        self.assertEqual([i["_product_type"] for i in out], ["FP_FH__L2B", "FP_FH__L2A"])

    def test_height_route_accepts_l2a_and_states_p_band(self):
        with patch.object(sp, "biomass_l2b_search", return_value=[]):
            r = sp.download_maap_height(None, None, "/tmp/x_cache")
        self.assertIn("banda P", r["reason"])


if __name__ == "__main__":
    unittest.main()
