"""Deterministic MAAP STAC contracts: not evidence of real FH pixel coverage."""
import unittest
from unittest.mock import patch
import geopandas as gpd
from shapely.geometry import box

import sar_pipeline as sp


class FakeResponse:
    def __init__(self, features=None, links=None, code=200):
        self.features=features if features is not None else []
        self.links=links if links is not None else []
        self.status_code=code
    def raise_for_status(self):
        import requests
        if self.status_code>=400:
            raise requests.HTTPError("fake status")
    def json(self):
        return {"features":self.features, "links":self.links}


class MAAPDiscoveryContracts(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(108,-4.66,119,8.05)],crs=4326)

    def test_official_get_bbox_fallback_and_pagination(self):
        fh={"id":"BIOMASS_FP_FH__L2A_one","collection":"BiomassLevel2a",
            "properties":{"datetime":"2026-08-11T00:00:00Z"}}
        page1=FakeResponse(features=[fh],
            links=[{"rel":"next","href":"https://catalog.maap.eo.esa.int/catalogue/search?page=2"}])
        page2=FakeResponse(features=[dict(fh),{"id":"BIOMASS_FP_FH__L2A_two",
            "properties":{"datetime":"2026-08-12T00:00:00Z"}}])
        with patch("sar_pipeline.requests.post",return_value=FakeResponse(code=405)) as post, \\
             patch("sar_pipeline.requests.get",side_effect=[page1,page2]) as get:
            result=sp.maap_search(self.aoi,"BiomassLevel2a",limit=100,
                                  product_type="FP_FH__L2A")
        self.assertEqual(len(result),2)
        self.assertEqual(post.call_count,1)
        self.assertEqual(get.call_count,2)
        kwargs=get.call_args_list[0].kwargs
        self.assertIn("bbox",kwargs["params"])
        self.assertEqual(kwargs["params"]["collections"],"BiomassLevel2a")

    def test_catalog_http_failure_is_not_no_coverage(self):
        with patch("sar_pipeline.requests.post",return_value=FakeResponse(code=503)), \\
             patch("sar_pipeline.requests.get",return_value=FakeResponse(code=503)):
            with self.assertRaisesRegex(RuntimeError,"MAAP_STAC_SEARCH_FAILED"):
                sp.maap_search(self.aoi,"BiomassLevel2a")
            with self.assertRaisesRegex(RuntimeError,"MAAP_ALL_COLLECTION_SEARCHES_FAILED"):
                sp.biomass_l2b_search(self.aoi)

    def test_pagination_rejects_untrusted_host(self):
        with patch("sar_pipeline.requests.post",return_value=FakeResponse(
                features=[],links=[{"rel":"next","href":"https://malicious.invalid/search"}])):
            with self.assertRaisesRegex(RuntimeError,"MAAP_STAC_UNTRUSTED_NEXT_PAGE"):
                sp.maap_search(self.aoi,"BiomassLevel2a")

    def test_zipper_archive_without_zip_suffix(self):
        item={"id":"BIOMASS_FP_FH__L2A_test",
              "properties":{"datetime":"2026-08-11T00:00:00Z"},
              "assets":{"product":{"href":"https://catalog.maap.eo.esa.int/data/zipper/abc",
                                   "type":"application/octet-stream","roles":["data"]}}}
        assets=sp._biomass_product_assets(item,"FP_FH__L2A")
        self.assertEqual(len(assets),1)
        self.assertIn("/zipper/",assets[0][1])

    def test_next_link_page_limit_fails_closed(self):
        page=FakeResponse(features=[],links=[
            {"rel":"next","href":"https://catalog.maap.eo.esa.int/catalogue/search?page=2"}])
        with patch("sar_pipeline.requests.post",return_value=page), \\
             patch("sar_pipeline.requests.get",return_value=page):
            with self.assertRaisesRegex(RuntimeError,"MAAP_STAC_PAGINATION_INCOMPLETE"):
                sp.maap_search(self.aoi,"BiomassLevel2a")


if __name__=="__main__":
    unittest.main()
