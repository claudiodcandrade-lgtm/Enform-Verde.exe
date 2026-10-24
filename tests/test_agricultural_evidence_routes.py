import csv
import gzip
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from agricultural_evidence_routes import build_pam_sar_panel, plan_evidence_routes
from sentinel1_mpc import _aware, _signed_href, extract_cog_polygon, search_sentinel1_rtc


class EvidenceRouteTests(unittest.TestCase):
    def test_route_plan_keeps_pseudolabels_out_of_validation(self):
        plan = plan_evidence_routes(task="crop_mask", crop="soja",
                                    available_sources=["mapbiomas_agriculture"])
        by_id = {r["source_id"]: r for r in plan["ordered_routes"]}
        self.assertFalse(by_id["mapbiomas_agriculture"]["eligible_as_independent_validation"])
        self.assertFalse(plan["release_ready"])
        self.assertTrue(plan["blockers"])

    def test_non_yieldsat_crop_explains_alternative_reference_gap(self):
        plan = plan_evidence_routes(task="crop_mask", crop="cafe")
        self.assertTrue(any("não lista referência brasileira" in x for x in plan["blockers"]))

    def test_pam_sar_join_requires_approved_independent_mask(self):
        with tempfile.TemporaryDirectory() as td:
            pam_path = Path(td)/"pam.csv.gz"
            with gzip.open(pam_path,"wt",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["product_key","territory_code","year","variable_code","value_numeric","source_url"])
                w.writeheader(); w.writerow({"product_key":"soja_grao","territory_code":"11001","year":"2020","variable_code":"112","value_numeric":"3000","source_url":"https://sidra.ibge.gov.br/"})
            sar_path = Path(td)/"sar.csv"
            fields=["product_key","territory_code","year","mask_validation_status","mask_model_sha256","crop_mask_source","latest_acquisition_utc","age_days","scenes_in_window","crop_phase","sar_vv_median"]
            with sar_path.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                w.writerow(dict(product_key="soja_grao",territory_code="11001",year="2020",mask_validation_status="INDEPENDENT_VALIDATION_APPROVED",mask_model_sha256="a"*64,crop_mask_source="YieldSAT field records",latest_acquisition_utc="2020-02-01T12:00:00Z",age_days="2",scenes_in_window="4",crop_phase="vegetative",sar_vv_median="0.42"))
                w.writerow(dict(product_key="soja_grao",territory_code="11001",year="2021",mask_validation_status="MAP_PSEUDOLABEL_ONLY",mask_model_sha256="",crop_mask_source="MapBiomas",latest_acquisition_utc="2021-02-01T12:00:00Z",age_days="2",scenes_in_window="4",crop_phase="vegetative",sar_vv_median="0.44"))
            result=build_pam_sar_panel(pam_path,sar_path)
            self.assertEqual(result["rows"],1)
            self.assertEqual(result["approved_mask_rows"],1)

    def test_mpc_href_signing_refuses_untrusted_host_and_keeps_secret_in_url_only(self):
        with self.assertRaises(ValueError):
            _signed_href("https://evil.invalid/a.tif", "sv=secret")
        signed=_signed_href("https://sentinel1euwestrtc.blob.core.windows.net/a.tif", "sv=temporary")
        self.assertIn("sv=temporary",signed)
        self.assertEqual(_aware("2026-10-24T00:00:00Z").utcoffset(),timedelta(0))

    def test_polygon_extractor_rejects_missing_field_geometry(self):
        with self.assertRaisesRegex(ValueError,"verified Polygon"):
            extract_cog_polygon("https://sentinel1euwestrtc.blob.core.windows.net/a.tif",
                                polygon_geojson={"type":"Point","coordinates":[0,0]},
                                polarization="vv",token="mock")

    def test_mpc_discovery_contract_requires_aoi_and_utc(self):
        with self.assertRaisesRegex(ValueError,"AOI"):
            search_sentinel1_rtc({"type":"Point","coordinates":[0,0]},
                                 start_utc="2026-10-01T00:00:00Z",end_utc="2026-10-10T00:00:00Z")
        with self.assertRaises(ValueError):
            search_sentinel1_rtc({"type":"Polygon","coordinates":[]},
                                 start_utc="2026-10-01",end_utc="2026-10-10T00:00:00Z")

    def test_mpc_stac_pagination_deduplicates_scenes(self):
        class Response:
            def __init__(self, value): self.value=value
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self):
                import json
                return json.dumps(self.value).encode()
        pages=[{"features":[{"id":"s1","properties":{"datetime":"2026-10-09T00:00:00Z"},"assets":{}}],
                 "links":[{"rel":"next","href":"https://planetarycomputer.microsoft.com/api/stac/v1/search?page=2","method":"POST","body":{"page":2}}]},
                {"features":[{"id":"s1","properties":{"datetime":"2026-10-09T00:00:00Z"},"assets":{}},
                              {"id":"s2","properties":{"datetime":"2026-10-08T00:00:00Z"},"assets":{}}],"links":[]}]
        def opener(*args,**kwargs): return Response(pages.pop(0))
        result=search_sentinel1_rtc({"type":"Polygon","coordinates":[]},
            start_utc="2026-10-01T00:00:00Z",end_utc="2026-10-10T00:00:00Z",opener=opener)
        self.assertEqual(result["scene_count"],2)
        self.assertTrue(result["pagination_complete"])


if __name__ == "__main__":
    unittest.main()
