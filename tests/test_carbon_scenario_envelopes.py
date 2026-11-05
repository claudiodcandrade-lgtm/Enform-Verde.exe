"""Source-bound carbon scenario calculations never fake missing accuracy."""
import unittest
from carbon_scenario_envelopes import scenario_envelope


def native(rows, complete=True):
    return {"native_area_ha":10.0, "complete":complete,
            "strata":[{"physiognomy":"Floresta Ombrófila Densa",
                       "components":rows}]}


def component(name, density, bounds=None, basis=10.0):
    item={"parametro":name,"tc":density,
          "total_tc":density*basis if density is not None else None,
          "quantified_area_ha":basis}
    if bounds is not None:item["range_tc_ha"]=bounds
    return item


class ScenarioEnvelopeTests(unittest.TestCase):
    def test_central_is_midpoint_when_source_interval_is_asymmetric(self):
        value=scenario_envelope(native([component("Serapilheira",5.0,[3.0,6.0])]))
        self.assertAlmostEqual((value["minimum_known_tc"]+value["maximum_known_tc"])/2,50)
        self.assertEqual(value["minimum_known_tc"],30)
        self.assertEqual(value["maximum_known_tc"],70)

    def test_bounds_not_imagined_for_missing_uncertainty(self):
        value=scenario_envelope(native([component("Biomassa subterrânea",8.0)]))
        self.assertEqual(value["known_total_tc"],80)
        self.assertIsNone(value["minimum_known_tc"])
        self.assertIsNone(value["maximum_known_tc"])
        self.assertEqual(len(value["missing_bounds"]),1)

    def test_missing_pool_is_not_zero(self):
        value=scenario_envelope(native([component("Serapilheira",None)]))
        self.assertIsNone(value["known_total_tc"])
        self.assertIsNone(value["central_known_tco2e"])
        self.assertFalse(value["complete"])
        self.assertEqual(len(value["missing_stocks"]),1)

    def test_soil_official_bounds_are_not_joint_ci(self):
        c=component("Solo 0–100 cm",20.0)
        c["official_uncertainty"]={"sum_bounds_envelope_tc_ha":[17.0,23.0]}
        value=scenario_envelope(native([c]))
        self.assertAlmostEqual(value["minimum_known_tco2e"],170*44/12)
        self.assertAlmostEqual(value["maximum_known_tco2e"],230*44/12)
        self.assertIn("NÃO é IC95%",value["interpretation"])

    def test_stocked_and_missing_bounds_prevents_false_total_envelope(self):
        value=scenario_envelope(native([
            component("Biomassa aérea",15.0,[14.0,16.0]),
            component("Biomassa subterrânea",10.0)
        ]))
        self.assertIsNone(value["minimum_known_tc"])
        self.assertAlmostEqual(value["known_total_tc"],250)

if __name__=="__main__":
    unittest.main()
