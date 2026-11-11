import unittest

from sentinel1_mpc import asset_href_for_read_attempt


class Sentinel1MpcRetryTests(unittest.TestCase):
    def test_retry_rotates_signer_and_refreshes_collection_sas(self):
        calls=[]
        def sign(href):
            calls.append("sign")
            return "signed-by-asset-endpoint"
        def refresh():
            calls.append("refresh")
            return "sig=fresh"
        href="https://sentinel1euwestrtc.blob.core.windows.net/a.tif"
        first=asset_href_for_read_attempt(href,attempt=0,token="sig=old",
                                          token_fn=refresh,signer=sign)
        second=asset_href_for_read_attempt(href,attempt=1,token="sig=old",
                                           token_fn=refresh,signer=sign)
        third=asset_href_for_read_attempt(href,attempt=2,token="sig=old",
                                          token_fn=refresh,signer=sign)
        self.assertIn("sig=old",first)
        self.assertEqual(second,"signed-by-asset-endpoint")
        self.assertIn("sig=fresh",third)
        self.assertEqual(calls,["sign","refresh"])

    def test_failed_token_refresh_falls_back_to_original_collection_sas(self):
        href="https://sentinel1euwestrtc.blob.core.windows.net/a.tif"
        def fail():
            raise RuntimeError("temporary token endpoint failure")
        signed=asset_href_for_read_attempt(href,attempt=2,token="sig=still-valid",
                                           token_fn=fail,signer=lambda _:"unused")
        self.assertIn("sig=still-valid",signed)


if __name__ == "__main__":
    unittest.main()
