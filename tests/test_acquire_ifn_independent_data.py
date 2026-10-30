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
            self.assertFalse(result["scientific_validation"])
            self.assertTrue((Path(temp) / "ifn_pa.csv").exists())

    def test_unapproved_host_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "bad", "url": "https://example.org/data.csv",
                                     "license": "unknown", "role": "unknown"}]}
            result = fetch_sources(registry, temp)
            self.assertEqual(result["resources"][0]["status"], "blocked")
            self.assertEqual(list(Path(temp).iterdir()), [])

if __name__ == "__main__":
    unittest.main()
