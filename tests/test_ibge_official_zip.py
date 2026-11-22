"""Synthetic transport/cache regressions, not IBGE spatial validation."""
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import requests
from tools.ibge_official_zip import download_ibge_zip


def zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr("vege_area.shp", b"x" * (1024 * 1024 + 1))
    return buf.getvalue()


class Response:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def raise_for_status(self):
        return None
    def iter_content(self, size):
        yield self.data


class IBGEZipCacheTests(unittest.TestCase):
    def test_verified_cache_skips_network(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            data = zip_bytes()
            (p / "vege.zip").write_bytes(data)
            (p / "vege.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n")
            with patch("tools.ibge_official_zip.requests.get", side_effect=AssertionError("network")):
                self.assertEqual(download_ibge_zip("https://geoftp.ibge.gov.br/vege.zip", p, "vege", "test"), p / "vege.zip")

    def test_corrupted_cache_forces_verified_redownload(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            data = zip_bytes()
            (p / "vege.zip").write_bytes(data)
            (p / "vege.sha256").write_text("0" * 64)
            with patch("tools.ibge_official_zip.requests.get", return_value=Response(data)) as get:
                download_ibge_zip("https://geoftp.ibge.gov.br/vege.zip", p, "vege", "test")
                self.assertEqual(get.call_count, 1)
                self.assertEqual((p / "vege.sha256").read_text().strip(), hashlib.sha256(data).hexdigest())

    def test_timeout_retries_and_cleans_partial(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            data = zip_bytes()
            with patch("tools.ibge_official_zip.requests.get", side_effect=[requests.exceptions.Timeout("temporary"), Response(data)]) as get:
                result = download_ibge_zip("https://geoftp.ibge.gov.br/vege.zip", p, "vege", "test", pause=lambda _: None)
                self.assertEqual(get.call_count, 2)
                self.assertTrue(result.is_file())
                self.assertFalse((p / "vege.part").exists())

    def test_html_response_fails_closed_and_is_not_cached(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            with patch("tools.ibge_official_zip.requests.get", return_value=Response(b"<html>" + b"x" * 1200000)):
                with self.assertRaisesRegex(ValueError, "valid ZIP"):
                    download_ibge_zip("https://geoftp.ibge.gov.br/vege.zip", p, "vege", "test", pause=lambda _: None)
                self.assertFalse((p / "vege.zip").exists())
                self.assertFalse((p / "vege.part").exists())


if __name__ == "__main__":
    unittest.main()
