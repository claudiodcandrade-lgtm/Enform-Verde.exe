import io
import unittest

from tools.harvest_inventory_source_metrics import (
    summarize_license_rows,
    summarize_pmfs_rows,
    summarize_volume_csvs,
)


class InventorySourceMetricsTests(unittest.TestCase):
    def test_pmfs_counts_unique_permit_ids_and_excludes_personal_data(self):
        rows=[
            {"NRO_REGISTRO":"R1","NRO_AUTORIZACAO":"A1","UF":"PA","BIOMA":"Amazônia",
             "FITOFISIONOMIA":"Floresta Ombrófila","LATITUDE_EMPREENDIMENTO":"-2","LONGITUDE_EMPREENDIMENTO":"-54",
             "CPF_CNPJ_DETENTOR":"123"},
            {"NRO_REGISTRO":"R1","NRO_AUTORIZACAO":"A2","UF":"PA","BIOMA":"Amazônia",
             "FITOFISIONOMIA":"Floresta Ombrófila","LATITUDE_EMPREENDIMENTO":"-2","LONGITUDE_EMPREENDIMENTO":"-54",
             "CPF_CNPJ_DETENTOR":"123"},
        ]
        result=summarize_pmfs_rows(rows)
        self.assertEqual(result["source_record_rows"],2)
        self.assertEqual(result["distinct_registry_ids"],1)
        self.assertEqual(result["distinct_authorization_ids"],2)
        self.assertNotIn("CPF_CNPJ_DETENTOR",str(result))

    def test_cross_dataset_authorizations_can_be_deduplicated_without_saving_ids(self):
        left=set();right=set()
        summarize_pmfs_rows([{"NRO_REGISTRO":"R1","NRO_AUTORIZACAO":"A1","UF":"PA"}],
                            authorization_hashes=left)
        data=("NRO_REGISTRO;NRO_AUTORIZACAO;UF\nR2;A1;PA\nR3;A2;PA\n")
        summarize_volume_csvs([("2026",io.BytesIO(data.encode()))],authorization_hashes=right)
        self.assertEqual(len(left&right),1)
        self.assertEqual(len(left|right),2)
        self.assertNotIn("A1",str(left|right))

    def test_exploration_rows_are_not_described_as_independent_inventory_plots(self):
        data=("NRO_REGISTRO;NRO_AUTORIZACAO;UF;NOME_CIENTIFICO;LATITUDE_ARVORE;LONGITUDE_ARVORE;NRO_ARVORE_EXPLORADA\n"
              "R1;A1;PA;Bertholletia excelsa;-2;-54;T1\n"
              "R1;A1;PA;Bertholletia excelsa;-2;-54;T2\n")
        result=summarize_volume_csvs([("2026",io.BytesIO(data.encode("utf-8")))])
        self.assertEqual(result["source_record_rows"],2)
        self.assertEqual(result["distinct_authorization_ids"],1)
        self.assertEqual(result["scientific_names_reported"],1)
        self.assertEqual(result["rows_with_tree_coordinates"],2)
        self.assertIn("selectively harvested",result["ecological_use_limit"])

    def test_license_rows_are_process_leads_not_inventory_counts(self):
        result=summarize_license_rows([
            {"NUM_PROCESSO_IBAMA":"P1","DES_TIPOLICENCA":"Autorização de Supressão de Vegetação","DES_TIPOLOGIA":"Rodovia"},
            {"NUM_PROCESSO_IBAMA":"P1","DES_TIPOLICENCA":"Retificação de Autorização de Supressão de Vegetação","DES_TIPOLOGIA":"Rodovia"},
            {"NUM_PROCESSO_IBAMA":"P2","DES_TIPOLICENCA":"Licença de Operação","DES_TIPOLOGIA":"Rodovia"},
        ])
        self.assertEqual(result["license_rows"],3)
        self.assertEqual(result["distinct_federal_process_ids"],2)
        self.assertEqual(result["distinct_processes_with_asv"],1)
        self.assertIn("document locations",result["inventory_count_interpretation"])


if __name__=="__main__":
    unittest.main()
