import unittest
from carbon_report_clarity import uncertainty_display

class CarbonReportClarityTests(unittest.TestCase):
    def test_supported_value_has_explicit_nonmeasurable_uncertainty_label(self):
        result=uncertainty_display(12.5, uncertainty_note="erro de transferência sem dados")
        self.assertIn("incerteza não mensurável",result)
        self.assertIn("estimativa mantida",result)
        self.assertIn("erro de transferência sem dados",result)

if __name__ == "__main__":
    unittest.main()
