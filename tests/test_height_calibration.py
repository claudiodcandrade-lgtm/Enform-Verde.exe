import unittest
import pandas as pd
from height_calibration import validate_sar_height_pairs


class SarHeightAgreementTests(unittest.TestCase):
    def test_inventory_field_heights_do_not_replace_primary_sar_height(self):
        out=validate_sar_height_pairs(pd.DataFrame({"field_height_m":[10]}))
        self.assertEqual(out["status"],"SAR_HEIGHT_CALIBRATION_BLOCKED")
        self.assertEqual(out["height_estimate_source"],"produto SAR direto, quando disponível")
        self.assertIsNone(out["calibrated_height_m"])
        self.assertIsNone(out["local_validation_error_m"])


if __name__ == "__main__":
    unittest.main()

    def test_gtdx_height_keeps_product_standard_error_and_not_h100(self):
        from sar_pipeline import _gtdx_height_summary
        out=_gtdx_height_summary(
            {"mean":31.2,"sd":2.5,"n":12},
            {"mean":1.6,"sd":0.4,"n":12},
            "height_amazon_25m.tif","height_uncertainty_amazon_25m.tif")
        self.assertEqual(out["height_standard_error_m"],1.6)
        self.assertFalse(out["height_definition_compatible_with_H100"])
        self.assertEqual(out["height_n_valid_pixels"],12)
        self.assertIn("TanDEM-X",out["sensor"])

    def test_gtdx_height_rejects_negative_or_nonfinite_error(self):
        from sar_pipeline import _gtdx_height_summary
        with self.assertRaises(ValueError):
            _gtdx_height_summary(
                {"mean":31.2,"sd":2.5,"n":12},
                {"mean":-1,"sd":0,"n":12},
                "height_amazon_25m.tif","height_uncertainty_amazon_25m.tif")
