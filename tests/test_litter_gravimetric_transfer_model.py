"""Gravimetric litter transfer contracts; synthetic observations only."""
import unittest
from national_litter_inventory_registry import inventory_litter_transfer_model

class LitterTransferTests(unittest.TestCase):
    def setUp(self):
        self.data=dict(biome="Amazônia",physiognomy="Floresta Ombrófila Densa",
                       source_tier="microrregional",source_url="https://example.org/study",
                       institution="Fixture institution",measurement="standing_litter_dry_mass",
                       standing_dry_mass_mg_ha=8.0,independent_sample_units=25,dry_mass_sd_mg_ha=2.5)
    def test_class_matched_but_no_transfer_sd_has_no_interval(self):
        result=inventory_litter_transfer_model(self.data,biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        self.assertAlmostEqual(result["mean_tc_ha"],3.76)
        self.assertFalse(result["include_in_total"])
        self.assertNotIn("range_tc_ha",result)
        self.assertIsNone(inventory_litter_transfer_model(self.data,biome="Amazônia",physiognomy="Savana Arborizada"))
        self.assertIsNone(inventory_litter_transfer_model({**self.data,"measurement":"annual_litterfall"},biome="Amazônia",physiognomy="Floresta Ombrófila Densa"))
    def test_independently_validated_transfer_sd_is_explicit(self):
        data={**self.data,"externally_validated_transfer_sd_mg_ha":1.5,
              "transfer_validation_independent":True,
              "transfer_validation_physiognomy":"Floresta Ombrófila Densa",
              "transfer_validation_region":"independent regional holdout"}
        result=inventory_litter_transfer_model(data,biome="Amazônia",physiognomy="Floresta Ombrófila Densa")
        self.assertEqual(len(result["range_tc_ha"]),2)
        self.assertLess(result["range_tc_ha"][0],result["mean_tc_ha"])
        self.assertGreater(result["range_tc_ha"][1],result["mean_tc_ha"])
        self.assertIn("não é IC95%",result["uncertainty_kind"])
        self.assertFalse(result["include_in_total"])
        data["transfer_validation_independent"]=False
        self.assertNotIn("range_tc_ha",inventory_litter_transfer_model(data,biome="Amazônia",physiognomy="Floresta Ombrófila Densa"))

if __name__=="__main__":
    unittest.main()
