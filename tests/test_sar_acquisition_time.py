import unittest
from sar_acquisition_time import acquisition_utc, newest_acquisitions, summarize_catalog_acquisition, acquisition_display
class AcquisitionTests(unittest.TestCase):
    def test_brasilia_display_and_newest(self):
        a={"id":"older","properties":{"startTime":"2026-01-20T11:00:00Z"}}
        b={"id":"newer","properties":{"datetime":"2026-10-22T21:35:40Z"}}
        x=newest_acquisitions([a,{"id":"unknown"},b])
        self.assertEqual([i["id"] for i in x],["newer","older","unknown"])
        self.assertEqual(x[0]["acquisition_brasilia"],"22/10/2026 18:35:40")
        self.assertEqual(x[0]["acquisition_utc"],"2026-10-22T21:35:40Z")
        self.assertIsNone(x[-1]["acquisition_brasilia"])
    def test_naive_timestamp_not_assumed_utc(self):
        self.assertIsNone(acquisition_utc({"datetime":"2026-10-22T21:35:40"}))
    def test_cci_annual_not_instantaneous_acquisition(self):
        a=acquisition_display({"path":r"C:\\Users\\Example\\cci\\N00W060_ESACCI-BIOMASS-L4-AGB-MERGED-100m-2024-fv7.0.tif"})
        self.assertEqual(a["reference_period"],"2024")
        self.assertIn("NÃO SE APLICA",a["brasilia"])
        self.assertIn("anual",a["explanation"])

    def test_individual_scene_utc_preserved(self):
        a=acquisition_display({"path":"scene.tif","acquisition_utc":"2026-10-23T12:00:00Z","acquisition_brasilia":"23/10/2026 09:00:00"})
        self.assertEqual(a["utc"],"2026-10-23T12:00:00Z")

    def test_latest_unknown_only(self):
        self.assertIsNone(summarize_catalog_acquisition([{"id":"no time"}])["latest"])
    def test_nested_property_and_offset(self):
        q=newest_acquisitions([{"properties":{"start_datetime":"2026-10-22T18:00:00-03:00"}}])
        self.assertEqual(q[0]["acquisition_utc"],"2026-10-22T21:00:00Z")
if __name__=="__main__":
    unittest.main()
