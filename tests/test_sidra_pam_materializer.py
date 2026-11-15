import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import build_sidra_pam_microregion_series as pam


class SidraPamMaterializerTests(unittest.TestCase):
    def test_suppressed_values_are_not_converted_to_zero(self):
        payload = [
            {"D1C": "Código", "D1N": "Território", "D2C": "Variável"},
            {"D1C": "11001", "D1N": "Porto Velho - RO", "D2C": "112", "D2N": "Rendimento médio da produção", "D3C": "2015", "MC": "33", "MN": "Quilogramas por Hectare", "V": "..."},
            {"D1C": "11001", "D1N": "Porto Velho - RO", "D2C": "214", "D2N": "Quantidade produzida", "D3C": "2015", "MC": "1", "MN": "Toneladas", "V": "10"},
            {"D1C": "11001", "D1N": "Porto Velho - RO", "D2C": "216", "D2N": "Área colhida", "D3C": "2015", "MC": "3", "MN": "Hectares", "V": "100"},
        ]

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps(payload).encode()

        with patch.object(pam, "urlopen", return_value=Response()):
            key, url, records = pam.fetch_product("soja_grao", ("Soja (em grão)", "40124"))
        self.assertEqual(key, "soja_grao")
        self.assertTrue(url.startswith("https://apisidra.ibge.gov.br/"))
        yield_row = next(row for row in records if row["variable_code"] == "112")
        self.assertEqual(yield_row["value_original"], "...")
        self.assertEqual(yield_row["value_numeric"], "")
        self.assertEqual(yield_row["observation_status"], "suppressed_or_missing")
        self.assertEqual(next(row for row in records if row["variable_code"] == "214")["value_numeric"], "10")

    def test_materialized_series_is_complete_and_has_auditable_checksum(self):
        csv_path = pam.ROOT / "data" / "pam_microregion_yield_2015_2024.csv.gz"
        metadata_path = pam.ROOT / "data" / "pam_microregion_yield_2015_2024.metadata.json"
        self.assertTrue(csv_path.exists(), "run tools/build_sidra_pam_microregion_series.py first")
        with gzip.open(csv_path, "rt", encoding="utf-8", newline="") as f:
            import csv
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 133_920)
        self.assertEqual(len({(r["product_code"], r["territory_code"], r["year"], r["variable_code"]) for r in rows}), len(rows))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["row_count"], len(rows))
        self.assertEqual(metadata["sha256"], __import__("hashlib").sha256(csv_path.read_bytes()).hexdigest())
        self.assertEqual(len(metadata["products"]), 8)
        self.assertTrue(all(item["yield_reconciliation"]["numeric_triplets"] > 0 for item in metadata["products"].values()))


if __name__ == "__main__":
    unittest.main()
