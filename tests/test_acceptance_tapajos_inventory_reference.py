import unittest

from inventory_agb_comparison import tapajos_acceptance_inventory_references


class TapajosAcceptanceInventoryReferenceTests(unittest.TestCase):
    def test_published_reference_satisfies_reference_branch_without_fabricating_agb(self):
        evidence={"agb_references":[{
            "status":"REFERENCIA_AGREGADA_PUBLICADA",
            "source_id":"TAPAJOS_SANTOS_KM72",
            "agb_mean_mg_ha":298.11,
            "physiognomy_match_level":"REFERENCIA_DE_FITOFISIONOMIA_PAI",
            "not_added_to_stock_total":True,
        }]}
        gate=tapajos_acceptance_inventory_references(None,11,evidence)
        self.assertEqual(gate["acceptance_status"],"SAR_E_REFERENCIAS_INVENTARIO_OK_AGB_N_D")
        self.assertTrue(gate["inventory_reference_eligible"])
        self.assertFalse(gate["agb_quantitative_estimate_available"])
        self.assertEqual(gate["eligible_inventory_references"][0]["source_id"],"TAPAJOS_SANTOS_KM72")

    def test_reference_without_processed_sar_does_not_satisfy_this_acceptance_branch(self):
        evidence={"agb_references":[{
            "status":"REFERENCIA_AGREGADA_PUBLICADA","source_id":"TAPAJOS_SANTOS_KM72",
            "agb_mean_mg_ha":298.11,"not_added_to_stock_total":True}]}
        gate=tapajos_acceptance_inventory_references(None,0,evidence)
        self.assertEqual(gate["acceptance_status"],"SEM_AGB_E_SEM_REFERENCIA_INVENTARIO_ELEGIVEL")

    def test_reference_added_to_stock_total_is_rejected(self):
        evidence={"agb_references":[{
            "status":"REFERENCIA_AGREGADA_PUBLICADA","source_id":"TAPAJOS_SANTOS_KM72",
            "agb_mean_mg_ha":298.11,"not_added_to_stock_total":False}]}
        gate=tapajos_acceptance_inventory_references(None,11,evidence)
        self.assertFalse(gate["inventory_reference_eligible"])

    def test_quantitative_agb_is_reported_as_quantitative_without_inventory_fallback(self):
        gate=tapajos_acceptance_inventory_references(145.0,11,{"agb_references":[]})
        self.assertEqual(gate["acceptance_status"],"ESTIMATIVA_QUANTITATIVA_DISPONIVEL")
        self.assertTrue(gate["agb_quantitative_estimate_available"])


if __name__ == "__main__":
    unittest.main()
