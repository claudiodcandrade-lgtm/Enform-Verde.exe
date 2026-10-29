"""Offline contract checks for transient Microsoft Planetary Computer SAS signing failures.

No network required. These tests prove retry behavior, not real SAR availability.
"""
import unittest
from unittest.mock import patch

import requests
from sar_pipeline import _planetary_sign_asset


class _Reply:
    def __init__(self, url="https://assets.example.test/a.tif?sig=secret"):
        self.url = url

    def raise_for_status(self):
        return None

    def json(self):
        return {"href": self.url}


def _error(status, retry_after=None):
    response = requests.Response()
    response.status_code = status
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return requests.exceptions.HTTPError("mock service error", response=response)


class PlanetarySignRetryTests(unittest.TestCase):
    def test_429_retry_after_is_honored_and_recovers(self):
        failures = [_error(429, 3), _Reply()]
        waits = []
        with patch("sar_pipeline.requests.get", side_effect=failures) as get:
            signed = _planetary_sign_asset("https://assets.example.test/a.tif",
                                            sleep=waits.append)
        self.assertEqual(signed, "https://assets.example.test/a.tif?sig=secret")
        self.assertEqual(get.call_count, 2)
        self.assertGreaterEqual(waits[0], 3.0)
        self.assertLessEqual(waits[0], 15.25)

    def test_429_is_bounded_and_fails_closed(self):
        waits = []
        with patch("sar_pipeline.requests.get", side_effect=[_error(429, 60)] * 3) as get:
            with self.assertRaises(requests.exceptions.HTTPError):
                _planetary_sign_asset("https://assets.example.test/a.tif", sleep=waits.append)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(len(waits), 2)
        self.assertTrue(all(15 <= x <= 15.25 for x in waits))

    def test_403_is_not_retried(self):
        with patch("sar_pipeline.requests.get", side_effect=_error(403)) as get:
            with self.assertRaises(requests.exceptions.HTTPError):
                _planetary_sign_asset("https://assets.example.test/a.tif", sleep=lambda _: None)
        self.assertEqual(get.call_count, 1)

    def test_timeout_is_retried(self):
        with patch("sar_pipeline.requests.get",
                   side_effect=[requests.exceptions.Timeout("network"), _Reply()]) as get:
            result = _planetary_sign_asset("https://assets.example.test/a.tif",
                                            sleep=lambda _: None)
        self.assertIn("sig=secret", result)
        self.assertEqual(get.call_count, 2)

    def test_reject_non_https_and_invalid_signed_url(self):
        with self.assertRaises(ValueError):
            _planetary_sign_asset("http://assets.example.test/a.tif")
        with patch("sar_pipeline.requests.get",
                   return_value=_Reply("http://assets.example.test/a.tif")):
            with self.assertRaises(ValueError):
                _planetary_sign_asset("https://assets.example.test/a.tif", sleep=lambda _: None)


if __name__ == "__main__":
    unittest.main()
