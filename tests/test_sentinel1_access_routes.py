import unittest
from unittest.mock import patch

import sentinel1_mpc


class Sentinel1AccessRouteTests(unittest.TestCase):
    def test_documented_collection_token_route_is_primary(self):
        with patch.object(sentinel1_mpc, "_https_json", return_value={"token": "?sig=abc"}) as get:
            token = sentinel1_mpc.get_runtime_sas_token()
        self.assertEqual(token, "sig=abc")
        self.assertEqual(get.call_args.args[0], sentinel1_mpc.SAS_TOKEN_URLS[0])
        self.assertIn("/token/sentinel-1-rtc", get.call_args.args[0])

    def test_legacy_storage_route_is_used_when_collection_route_fails(self):
        with patch.object(sentinel1_mpc, "_https_json",
                          side_effect=[RuntimeError("denied"), {"token": "sig=abc"}]) as get:
            token = sentinel1_mpc.get_runtime_sas_token()
        self.assertEqual(token, "sig=abc")
        self.assertEqual([c.args[0] for c in get.call_args_list], list(sentinel1_mpc.SAS_TOKEN_URLS))

    def test_failure_reports_all_attempted_routes_without_secrets(self):
        with patch.object(sentinel1_mpc, "_https_json", side_effect=RuntimeError("denied")):
            with self.assertRaisesRegex(RuntimeError, "collection and storage routes"):
                sentinel1_mpc.get_runtime_sas_token()

    def test_grd_uses_its_own_documented_collection_token_routes(self):
        with patch.object(sentinel1_mpc, "_https_json", return_value={"token": "?sig=grd"}) as get:
            token = sentinel1_mpc.get_runtime_sas_token("sentinel-1-grd")
        self.assertEqual(token, "sig=grd")
        self.assertIn("/token/sentinel-1-grd", get.call_args.args[0])
        self.assertNotEqual(sentinel1_mpc.SAS_TOKEN_ROUTES["sentinel-1-grd"],
                            sentinel1_mpc.SAS_TOKEN_ROUTES["sentinel-1-rtc"])

    def test_signed_asset_merges_sas_query(self):
        result = sentinel1_mpc._signed_href(
            "https://sentinel1euwestrtc.blob.core.windows.net/sentinel1-grd-rtc/item/vv.tif",
            "sv=1&sig=abc%3D")
        self.assertIn("sv=1", result)
        self.assertIn("sig=abc%3D", result)

    def test_grd_blob_host_is_accepted_for_collection_sas(self):
        result = sentinel1_mpc._signed_href(
            "https://sentinel1euwest.blob.core.windows.net/s1-grd/item/vv.tiff",
            "sv=1&sig=abc%3D")
        self.assertIn("sig=abc%3D", result)


if __name__ == "__main__":
    unittest.main()
