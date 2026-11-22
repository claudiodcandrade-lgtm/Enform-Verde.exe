"""MPC asset signing route — independent from collection-wide SAS."""
import io
import json
import unittest
from urllib.parse import urlsplit, parse_qs
from sentinel1_mpc import sign_asset_href

class _Response:
    def __init__(self, value):
        self.stream = io.BytesIO(json.dumps(value).encode("utf-8"))
    def __enter__(self):
        return self.stream
    def __exit__(self, *args):
        self.stream.close()

class TestMpcAssetSigning(unittest.TestCase):
    def test_per_asset_signing(self):
        unsigned = "https://sentinel1euwestrtc.blob.core.windows.net/sentinel1-grd-rtc/test.tif"
        def opener(req, timeout=45):
            url = req.full_url
            self.assertEqual(urlsplit(url).path, "/api/sas/v1/sign")
            self.assertEqual(parse_qs(urlsplit(url).query)["href"][0], unsigned)
            return _Response({"href": unsigned + "?sv=2026-11-10&sig=secret"})
        signed = sign_asset_href(unsigned, opener=opener)
        self.assertIn("sig=", signed)

    def test_refuses_untrusted_asset(self):
        with self.assertRaises(ValueError):
            sign_asset_href("https://untrusted.example/test.tif")

    def test_refuses_untrusted_signer_response(self):
        unsigned = "https://sentinel1euwestrtc.blob.core.windows.net/test.tif"
        def opener(req, timeout=45):
            return _Response({"href":"https://untrusted.example/fake.tif"})
        with self.assertRaises(ValueError):
            sign_asset_href(unsigned, opener=opener)

if __name__ == "__main__":
    unittest.main()
