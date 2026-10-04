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
