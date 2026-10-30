import io
import zipfile
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

    def test_multiple_equations_do_not_inflate_primary_sampling_units(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = {"sources": [{"id": "ifn_models", "url": URL,
                       "license": "CC BY", "role": "biomass"}]}
            raw = ("bioma;uf;ua;tipologia_da_vegetacao;equacoes;agb_media_kg_por_ha\n"
                   "Cerrado;Goiás;GO_1;Savana;Eq.1;1000\n"
                   "Cerrado;Goiás;GO_1;Savana;Eq.2;1200\n"
                   "Cerrado;Goiás;GO_2;Savana;Eq.1;1400\n").encode("utf-8")
            result = fetch_sources(registry, temp,
                opener=lambda request, timeout: io.BytesIO(raw))
            item = result["resources"][0]
            self.assertEqual(item["csv_data_rows"], 3)
            self.assertEqual(item["unique_ua"], 2)
            self.assertEqual(item["unique_ua_by_biome"], {"Cerrado": 2})
            self.assertEqual(item["strata_ua_counts"][0]["unique_ua"], 2)
            self.assertEqual(item["max_equations_per_ua"], 2)
            self.assertTrue(item["equation_rows_not_independent_sampling_units"])
            self.assertFalse(item["strata_are_independently_validated"])

    def test_official_mislabeled_csv_url_with_xlsx_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("xl/workbook.xml", "<workbook/>")
                archive.writestr("xl/worksheets/sheet1.xml",
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>bioma</t></is></c>'
                    '<c r="B1" t="inlineStr"><is><t>equivalente</t></is></c></row>'
                    '<row r="2"><c r="A2" t="inlineStr"><is><t>Cerrado</t></is></c>'
                    '<c r="B2" t="inlineStr"><is><t>Sim</t></is></c></row></sheetData></worksheet>')
            registry = {"sources": [{"id": "ifn_equivalence", "url": URL,
                       "license": "CC BY", "role": "equivalence", "format_override": "xlsx",
                       "expected_columns": ["bioma", "equivalente"]}]}
            result = fetch_sources(registry, temp,
                opener=lambda request, timeout: io.BytesIO(buffer.getvalue()))
            item = result["resources"][0]
            self.assertEqual(item["status"], "downloaded_unvalidated")
            self.assertEqual(item["validated_file_extension"], ".xlsx")
            self.assertEqual(item["source_url_extension"], ".csv")
            self.assertEqual(item["xlsx_data_rows"], 1)
            self.assertEqual(item["biome_rows"], {"Cerrado": 1})

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
