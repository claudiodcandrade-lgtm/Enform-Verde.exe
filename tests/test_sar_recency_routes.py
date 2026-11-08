"""Regression for newest compatible SAR acquisition, not newest publication date."""
import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone

from sar_acquisition_time import acquisition_utc, order_by_acquisition, newest_acquisitions
from sar_pipeline import _newest_first, biomass_l2b_search, maap_search, CCI_V7_YEARS

def item(key, when, product="FP_AGB_L2B"):
    return {"id":key, "properties":{"datetime":when}, "assets":{},
            "_product_type":product}

class SarRecencyRouteTests(unittest.TestCase):
    def test_offsets_and_unknown_dates_have_correct_order(self):
        scenes = [
            item("older", "2026-09-08T20:00:00Z"),
            item("future-download-not-acquisition", None),
            item("newest", "2026-10-28T12:00:00-03:00"),
        ]
        scenes[1]["properties"]["published"]="2028-01-01T00:00:00Z"
        self.assertEqual([x["id"] for x in _newest_first(scenes)],
                         ["newest","older","future-download-not-acquisition"])
        self.assertEqual(acquisition_utc(scenes[0]).tzinfo, timezone.utc)

    def test_nested_asf_sensor_timestamp_precedes_product_ingestion(self):
        scene={"id":"nisar", "raw":{"properties":{"startTime":"2026-10-28T21:00:00Z"}},
               "properties":{"processingDate":"2028-12-01"}}
        self.assertEqual(acquisition_utc(scene).isoformat(), "2026-10-28T21:00:00+00:00")
        self.assertEqual(newest_acquisitions([{"id":"unknown"},scene])[0]["id"],"nisar")

    def test_scientific_product_priority_then_latest_acquisition(self):
        data=[item("agb-old","2026-01-01T00:00:00Z"),
              item("agb-new","2026-10-20T00:00:00Z"),
              item("height-newest","2026-10-28T00:00:00Z","FP_FH__L2B")]
        for x in data:x["_collection"]="BiomassLevel2b"
        with patch("sar_pipeline.maap_search") as api:
            def find(gdf, collection, limit=100, product_type=None):
                # Test only this fixture's operational collection. IOC items
                # come from a different STAC collection and must not be cloned.
                return [x for x in data if x["_product_type"] == product_type
                        and collection == "BiomassLevel2b"]
            api.side_effect=find
            out=biomass_l2b_search(object())
        self.assertEqual([x["id"] for x in out],["agb-new","agb-old","height-newest"])

    def test_ioc_more_recent_does_not_automatically_override_operational(self):
        operational=item("operational", "2026-01-05T00:00:00Z")
        ioc=item("ioc-newer", "2026-10-25T00:00:00Z")
        with patch("sar_pipeline.maap_search") as api:
            api.side_effect=lambda gdf,collection,limit=100,product_type=None: (
                [operational] if collection=="BiomassLevel2b" and product_type=="FP_AGB_L2B"
                else [ioc] if collection=="BiomassLevel2bIOC" and product_type=="FP_AGB_L2B"
                else [])
            out=biomass_l2b_search(object())
        self.assertEqual(out[0]["_stage"],"OPERATIONAL")
        self.assertEqual(out[1]["_stage"],"IOC")

    def test_maap_requests_catalog_descending_and_resorts_response(self):
        fake=Mock()
        fake.status_code=200
        fake.json.return_value={"features":[item("old","2025-01-01T00:00:00Z"),
                                             item("new","2026-10-28T00:00:00Z")]}
        import geopandas as gpd
        from shapely.geometry import box
        aoi=gpd.GeoDataFrame(geometry=[box(-54.98,-3.05,-54.96,-3.03)],
                             crs="EPSG:4326")
        with patch("sar_pipeline.requests.post",return_value=fake) as call:
            out=maap_search(aoi, "BiomassLevel2b", limit=10)
        body=call.call_args.kwargs["json"]
        self.assertEqual(body["sortby"][0]["direction"],"desc")
        self.assertEqual([x["id"] for x in out],["new","old"])

    def test_annual_cci_latest_candidate_is_checked_before_2024(self):
        now=datetime.now(timezone.utc).year
        self.assertEqual(CCI_V7_YEARS[0],max(2024,now))
        self.assertIn(2024,CCI_V7_YEARS)
        self.assertEqual(len(CCI_V7_YEARS),len(set(CCI_V7_YEARS)))

if __name__=="__main__":
    unittest.main()
