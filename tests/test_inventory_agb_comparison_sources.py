import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import inventory_agb_comparison as comparison
from inventory_agb_comparison import canonical_panel_sha256, published_agb_references


class InventoryAgbComparisonSourceTests(unittest.TestCase):
    def test_panel_hash_is_stable_across_windows_line_endings(self):
        lf = b"a,b\n1,2\n"
        crlf = lf.replace(b"\n", b"\r\n")
        self.assertEqual(canonical_panel_sha256(lf), canonical_panel_sha256(crlf))
        self.assertNotEqual(canonical_panel_sha256(lf), canonical_panel_sha256(lf + b"3,4\n"))

    def test_published_references_are_all_returned_separately_and_filtered(self):
        content = (
            "source_id,institution,biome,physiognomy,region,metric,center,sd,ci95_low,ci95_high,n_plots,n_sites,citation,url,statistical_use\n"
            "A,Embrapa,Amazônia,Floresta X,Região 1,AGB,100,10,,,,5,1,Artigo A,https://a,comparável\n"
            "B,UFLA,Amazônia,Floresta X,Região 2,AGB,120,,90,150,8,2,Artigo B,https://b,comparável\n"
            "C,UFV,Amazônia,Floresta Y,AGB,AGB,999,,,,1,1,Artigo C,https://c,fora\n"
            "D,UFV,Amazônia,Floresta X,Região 4,total_biomass,999,,,,1,1,Artigo D,https://d,outra métrica\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.csv"
            path.write_text(content, encoding="utf-8")
            rows = published_agb_references(biome="Amazônia", physiognomy="Floresta X", path=path)
        self.assertEqual([row["source_id"] for row in rows], ["A", "B"])
        self.assertEqual(rows[1]["ci95_low_mg_ha"], 90.0)
        self.assertTrue(all(row["not_added_to_stock_total"] for row in rows))

    def test_published_sources_work_without_ifn_and_are_not_pooled(self):
        refs = [
            {"status":"REFERENCIA_AGREGADA_PUBLICADA","source_id":"EMBRAPA",
             "institution":"Embrapa","region":"Região A","agb_mean_mg_ha":110,
             "citation":"Estudo A","not_added_to_stock_total":True},
            {"status":"REFERENCIA_AGREGADA_PUBLICADA","source_id":"UFV",
             "institution":"UFV","region":"Região B","agb_mean_mg_ha":145,
             "citation":"Estudo B","not_added_to_stock_total":True},
        ]
        with patch.object(comparison, "DB", Path("/missing/ifn.sqlite")), \
             patch.object(comparison, "PANEL", Path("/missing/ifn.csv")), \
             patch.object(comparison, "published_agb_references", return_value=refs):
            result = comparison.estimate_inventory_agb_comparison(
                biome="Amazônia", physiognomy="Floresta X", area_ha=10,
                centroid_lon=-55, centroid_lat=-11)
        self.assertEqual(result["status"], "COMPARACAO_REFERENCIAS_PUBLICADAS")
        self.assertEqual(result["published_aggregate_count"], 2)
        self.assertEqual(result["usable_inventory_sources_consulted"], ["EMBRAPA", "UFV"])
        self.assertEqual([r["agb_mean_mg_ha"] for r in result["inventory_references"]], [110, 145])
        self.assertTrue(result["not_added_to_stock_total"])


if __name__ == "__main__":
    unittest.main()
