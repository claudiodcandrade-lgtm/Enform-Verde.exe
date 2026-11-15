import unittest

from sensor_contingency import fallback_plan


class SensorContingencyTests(unittest.TestCase):
    def test_sentinel1_is_primary_and_substitution_is_prohibited_without_validation(self):
        plan = fallback_plan()
        self.assertEqual(plan["priority_sensor"], "Sentinel-1")
        self.assertEqual(plan["routes"][0]["sensor"], "Sentinel-1")
        self.assertTrue(all(route["substitutable"] is False for route in plan["routes"]))

    def test_missing_data_technical_failure_and_validation_gap_are_distinct(self):
        states = fallback_plan()["status_vocabulary"]
        self.assertIn("N/D_DADOS", states)
        self.assertIn("ERRO_TECNICO", states)
        self.assertIn("N/D_VALIDACAO", states)
        self.assertNotEqual(states["N/D_DADOS"], states["ERRO_TECNICO"])


if __name__ == "__main__":
    unittest.main()
