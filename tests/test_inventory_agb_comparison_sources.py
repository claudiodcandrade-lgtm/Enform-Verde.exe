import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import inventory_agb_comparison as comparison
from inventory_agb_comparison import (canonical_panel_sha256, published_agb_references,
                                      published_structural_references,
                                      published_inventory_evidence,
                                      multisource_inventory_agb_mean,
                                      published_horizontal_inventory_baliza)


class InventoryAgbComparisonSourceTests(unittest.TestCase):
    def test_harmonized_aggregate_register_is_read_once_and_invalidated_on_change(self):
        import inventory_agb_comparison as module
        module._aggregate_rows_cached.cache_clear()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"evidence.csv"
            path.write_text(
                "source_id,biome,physiognomy,metric,center\nA,Amazônia,F,AGB,10\n",
                encoding="utf-8")
            first=module._aggregate_rows(path)
            second=module._aggregate_rows(path)
            self.assertIs(first,second)
            self.assertEqual(module._aggregate_rows_cached.cache_info().hits,1)
            path.write_text(
                "source_id,biome,physiognomy,metric,center\nA,Amazônia,F,AGB,10\nB,Amazônia,F,AGB,20\n",
                encoding="utf-8")
            changed=module._aggregate_rows(path)
            self.assertEqual(len(changed[1]),2)
            self.assertEqual(module._aggregate_rows_cached.cache_info().misses,2)

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
        self.assertIn("HARMONIZED_PUBLISHED_AGB_REGISTER",result["inventory_sources_searched"])
        self.assertEqual(result["matched_published_inventory_sources"],["EMBRAPA","UFV"])
        self.assertEqual([r["agb_mean_mg_ha"] for r in result["inventory_references"]], [110, 145])
        self.assertTrue(result["not_added_to_stock_total"])

    def test_inventory_contingency_averages_all_compatible_study_means_only(self):
        content=(
          "source_id,institution,biome,physiognomy,region,metric,unit,center_type,center,sd,n_plots,n_sites,data_level,citation,url\n"
          "A1,Embrapa,Amazônia,Floresta X,Sítio 1,AGB,Mg/ha,mean,100,10,4,1,published_aggregate,Estudo A,https://a1\n"
          "A2,Embrapa,Amazônia,Floresta X,Sítio 2,AGB,Mg/ha,mean,200,20,6,1,published_aggregate,Estudo A,https://a2\n"
          "B,UFV,Amazônia,Floresta X,Sítio 3,AGB,Mg/ha,mean,300,,10,1,published_aggregate,Estudo B,https://b\n"
          "C,UFV,Amazônia,Floresta X,Sítio 4,AGB,Mg/ha,median,900,,20,1,published_aggregate,Mediana,https://c\n"
          "D,UFV,Amazônia,Floresta Y,Sítio 5,AGB,Mg/ha,mean,800,,20,1,published_aggregate,Irmã,https://d\n")
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"evidence.csv";path.write_text(content,encoding="utf-8")
            result=multisource_inventory_agb_mean(
                biome="Amazônia",physiognomy="Floresta X",path=path)
        # Estudo A combines 100 and 200 weighted by their plot counts => 160;
        # the independent studies A and B then receive equal study weight.
        self.assertAlmostEqual(result["agb_mg_ha"],230.0)
        self.assertEqual(result["study_count"],2)
        self.assertEqual(result["matched_inventory_sources"],["A1","A2","B"])
        self.assertEqual(result["uncertainty_kind"],
            "DP entre médias de estudos compatíveis; não é IC95% nem erro total de transferência")
        self.assertFalse(result["reference_only"])
        self.assertTrue(result["not_added_to_stock_total"] is False)

    def test_no_exact_match_still_records_full_inventory_source_search(self):
        with patch.object(comparison,"DB",Path("/missing/ifn.sqlite")), \
             patch.object(comparison,"PANEL",Path("/missing/ifn.csv")), \
             patch.object(comparison,"published_agb_references",return_value=[]), \
             patch.object(comparison,"_published_aggregate_source_ids",
                          return_value=["EMBRAPA","INPA","UFV"]):
            result=comparison.estimate_inventory_agb_comparison(
                biome="Amazônia",physiognomy="Formação florestal",area_ha=10,
                centroid_lon=-55,centroid_lat=-11)
        self.assertEqual(result["status"],"N/D")
        self.assertEqual(result["published_aggregate_count"],0)
        self.assertEqual(result["matched_published_inventory_sources"],[])
        self.assertEqual(result["registered_published_inventory_sources"],
                         ["EMBRAPA","INPA","UFV"])
        self.assertEqual(result["inventory_sources_searched"],[
            "IFN_EXPANDED_TREE_MICRODATA","SFB_IFN_DAP10_AGB_PANEL",
            "HARMONIZED_PUBLISHED_AGB_REGISTER",
            "HARMONIZED_PUBLISHED_STRUCTURAL_REGISTER",
            "NATIONAL_INVENTORY_CANDIDATE_CATALOG"])

    def test_horizontal_aggregates_are_returned_as_references_not_plot_data(self):
        refs=published_structural_references(
            biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        matched=[r for r in refs if r["source_id"]=="EMBRAPA_ODF_CLASS1_GE15_BA"]
        self.assertEqual(len(matched),1)
        self.assertEqual(matched[0]["metric"],"basal_area")
        self.assertEqual(matched[0]["center"],27.36)
        self.assertTrue(matched[0]["not_plot_level_data"])
        self.assertIsNone(matched[0]["sd"])

    def test_inventory_evidence_bundle_declares_aggregate_as_benchmark(self):
        evidence=published_inventory_evidence(
            biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        self.assertIn("EMBRAPA_ODF_CLASS1_GE15_BA",evidence["sources"])
        self.assertGreater(evidence["horizontal_reference_count"],0)
        self.assertIn("baliza regional",evidence["use_when_plot_microdata_unavailable"])
        self.assertTrue(evidence["not_added_to_stock_total"])

    def test_published_basal_area_is_available_as_horizontal_baliza_without_plot_rows(self):
        baliza=published_horizontal_inventory_baliza(
            biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        refs=[r for r in baliza["references"]
              if r["source_id"]=="EMBRAPA_ODF_CLASS1_GE15_BA"]
        self.assertEqual(baliza["status"],"BALIZA_HORIZONTAL_PUBLICADA_CONSULTADA")
        self.assertEqual(len(refs),1)
        self.assertEqual(refs[0]["metric"],"basal_area")
        self.assertEqual(refs[0]["center"],27.36)
        self.assertTrue(baliza["not_used_as_plot_calibration"])

    def test_parent_forest_formation_matches_ibge_subformation_as_reference_only(self):
        refs=published_agb_references(
            biome="Amazônia",
            physiognomy="Floresta Ombrófila Densa das Terras Baixas")
        tapajos=[r for r in refs if r["source_id"] in {
            "TAPAJOS_SANTOS_KM72","TAPAJOS_SANTOS_KM117"}]
        self.assertEqual({r["source_id"] for r in tapajos},
                         {"TAPAJOS_SANTOS_KM72","TAPAJOS_SANTOS_KM117"})
        self.assertTrue(all(r["physiognomy_match_level"]=="REFERENCIA_DE_FITOFISIONOMIA_PAI"
                            and r["reference_only"] and r["not_added_to_stock_total"]
                            for r in tapajos))

    def test_parent_matching_does_not_treat_sibling_formations_as_compatible(self):
        self.assertIsNone(comparison._physiognomy_match_level(
            "Floresta Ombrófila Densa","Floresta Ombrófila Aberta"))

    def test_missing_inventory_register_is_not_reported_as_empty_ecological_domain(self):
        evidence=published_inventory_evidence(
            biome="Amazônia",physiognomy="Floresta X",path=Path("/missing/evidence.csv"))
        self.assertEqual(evidence["status"],"ERRO_TECNICO_LEITURA_REGISTRO")


if __name__ == "__main__":
    unittest.main()
