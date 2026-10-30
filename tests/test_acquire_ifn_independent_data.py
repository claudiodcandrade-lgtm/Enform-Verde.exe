import io
import tempfile
import unittest
from pathlib import Path
from tools.acquire_ifn_independent_data import fetch_sources

URL = "https://dados.florestal.gov.br/dataset/ifn.csv"

class IFNAcquisitionTests(unittest.TestCase):
    def test_raw_download_has_hash_but_is_not_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            def fake_open(request, timeout):
                return io.BytesIO(b"parcela,serapilheira\n1,2.4\n")
            registry = {"sources": [{"id": "ifn_pa", "url": URL, "license": "CC BY", "role": "litter"}]}
            result = fetch_sources(registry, temp, opener=fake_open)
            item = result["resources"][0]
            self.assertEqual(item["status"], "downloaded_unvalidated")
            self.assertEqual(len(item["sha256"]), 64)
            self.assertEqual(item["csv_data_rows"], 1)
            self.assertEqual(item["csv_header"], ["parcela", "serapilheira"])
            self.assertFalse(result["scientific_validation"])
            self.assertTrue((Path(temp) / "ifn_pa.csv").exists())

    def test_realistic_cp1252_observations_preserve_biome_names(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "ifn_cp1252", "url": URL,
                       "license": "CC BY", "role": "litter",
                       "expected_columns": ["bioma", "uf", "ua", "Profundidade"]}]}
            data = 'bioma;uf;ua;Profundidade\\nAmazônia;Pará;PA_1;2,7\\n'.replace('\\n', '\n').encode("cp1252")
            result = fetch_sources(registry, temp, opener=lambda request, timeout: io.BytesIO(data))
            item = result["resources"][0]
            self.assertEqual(item["status"], "downloaded_unvalidated")
            self.assertEqual(item["csv_encoding"], "cp1252")
            self.assertEqual(item["biome_rows"], {"Amazônia": 1})
            self.assertEqual(item["state_rows"], {"Pará": 1})
            self.assertEqual(item["unique_ua"], 1)
            self.assertFalse(item["carbon_stock_ready"])

    def test_expected_columns_required(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "ifn_bad_header", "url": URL,
                       "license": "CC BY", "role": "litter",
                       "expected_columns": ["Profundidade"]}]}
            result = fetch_sources(registry, temp,
                opener=lambda request, timeout: io.BytesIO(b"parcela,valor\\n1,2\\n".replace(b"\\n", b"\n")))
            self.assertEqual(result["resources"][0]["status"], "download_failed")

    def test_html_error_response_not_saved_as_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "bad_csv", "url": URL, "license": "CC BY", "role": "litter"}]}
            def fake_open(request, timeout):
                return io.BytesIO(b"<!doctype html><html>maintenance</html>")
            result = fetch_sources(registry, temp, opener=fake_open)
            self.assertEqual(result["resources"][0]["status"], "download_failed")
            self.assertFalse((Path(temp) / "bad_csv.csv").exists())

    def test_header_only_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "empty_csv", "url": URL, "license": "CC BY", "role": "litter"}]}
            def fake_open(request, timeout):
                return io.BytesIO(b"parcela,serapilheira\\n")
            result = fetch_sources(registry, temp, opener=fake_open)
            self.assertEqual(result["resources"][0]["status"], "download_failed")

    def test_redirect_outside_official_host_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "redirected", "url": URL, "license": "CC BY", "role": "litter"}]}
            class RedirectedResponse(io.BytesIO):
                def geturl(self):
                    return "https://example.org/ifn.csv"
            def fake_open(request, timeout):
                return RedirectedResponse(b"parcela,serapilheira\\n1,2.4\\n")
            result = fetch_sources(registry, temp, opener=fake_open)
            self.assertEqual(result["resources"][0]["status"], "download_failed")

    def test_invalid_resource_id_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "../escape", "url": URL, "license": "CC BY", "role": "litter"}]}
            result = fetch_sources(registry, temp)
            self.assertEqual(result["resources"][0]["status"], "blocked")

    def test_unapproved_host_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "bad", "url": "https://example.org/data.csv",
                                     "license": "unknown", "role": "unknown"}]}
            result = fetch_sources(registry, temp)
            self.assertEqual(result["resources"][0]["status"], "blocked")
            self.assertEqual(list(Path(temp).iterdir()), [])

if __name__ == "__main__":
    unittest.main()
