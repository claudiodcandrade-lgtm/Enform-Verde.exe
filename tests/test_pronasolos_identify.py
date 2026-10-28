"""Synthetic contract tests for batched PronaSolos MapServer soil queries."""
import unittest
from pronasolos_identify import (
    LAYER_IDS, SERVICE, build_identify_params, extract_paired_horizons,
    numeric_soil_stock,
)
from soil_profile_stats import summarize_paired_soil_profiles

class PronasolosIdentifyBatchTests(unittest.TestCase):
    def test_one_request_covers_all_six_horizons(self):
        params=build_identify_params(-4800000,-1200000,(-4900000,-1300000,-4700000,-1100000))
        self.assertEqual(params["layers"],"all:2,3,4,5,6,7")
        self.assertEqual(params["geometry"],"-4800000.0,-1200000.0")
        self.assertEqual(params["sr"],"3857")
        self.assertIn("/MapServer/identify",SERVICE)

    def test_all_horizons_are_paired_within_one_response(self):
        payload={"results":[{"layerId":lid,"value":str(10*lid)} for lid in LAYER_IDS]}
        paired=extract_paired_horizons(payload)
        self.assertEqual(paired,{lid:10*lid for lid in LAYER_IDS})
        soil=summarize_paired_soil_profiles([paired])
        self.assertEqual(soil["0–100 cm"]["tc_ha"],sum(10*i for i in LAYER_IDS[:5]))
        self.assertEqual(soil["0–100 cm"]["n_samples"],1)

    def test_partial_response_cannot_fake_deeper_profile(self):
        payload={"results":[{"layerId":2,"value":10},{"layerId":3,"value":20},
                            {"layerId":4,"value":30},{"layerId":6,"value":50}]}
        paired=extract_paired_horizons(payload)
        soil=summarize_paired_soil_profiles([paired])
        self.assertEqual(soil["0–30 cm"]["tc_ha"],60)
        self.assertNotIn("0–60 cm",soil)
        self.assertNotIn("0–100 cm",soil)

    def test_no_data_and_renderer_layers_not_substituted(self):
        payload={"results":[{"layerId":1,"value":500},{"layerId":2,"value":"NoData"},
                            {"layerId":3,"attributes":{"Pixel Value":"1,5"}},
                            {"layerId":4,"value":False}]}
        self.assertEqual(extract_paired_horizons(payload),{3:1.5})
        self.assertIsNone(numeric_soil_stock({"value":float("nan")}))
        self.assertIsNone(numeric_soil_stock({"value":-1}))

    def test_reject_conflicting_duplicate_values(self):
        with self.assertRaisesRegex(ValueError,"Conflicting"):
            extract_paired_horizons({"results":[{"layerId":2,"value":1},
                                                {"layerId":2,"value":3}]})

    def test_invalid_payload_or_service_error_fails_closed(self):
        for payload in (None,{},{"error":{"message":"not authorized"}},{"results":{}}):
            with self.subTest(payload=payload),self.assertRaises(ValueError):
                extract_paired_horizons(payload)

    def test_invalid_coordinates_and_layer_id_rejected(self):
        for coord in (float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                build_identify_params(coord,0,(0,0,1,1))
        with self.assertRaises(ValueError):
            build_identify_params(0,0,(0,0,1,1),[99])

if __name__=="__main__":
    unittest.main()
