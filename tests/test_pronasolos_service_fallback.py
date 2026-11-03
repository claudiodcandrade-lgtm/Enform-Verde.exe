"""Regression: two official PronaSolos services cannot produce a hybrid soil profile."""
import unittest
from unittest.mock import patch, Mock

import geopandas as gpd
from shapely.geometry import box

from pronasolos_identify import SERVICE, ALTERNATE_SERVICE, THIRD_SERVICE, SERVICE_CANDIDATES
from desktop_app import pronasolos_soc_profiles
from tools.probe_pronasolos_100cm import query_site

def payload(values):
    return {"results":[{"layerId":i,"value":v} for i,v in values.items()]}

def response(values):
    r=Mock()
    r.json.return_value=payload(values)
    r.status_code=200
    r.content=b"public test response (NOT real data)"
    return r

class SoilEndpointFallbackTests(unittest.TestCase):
    def setUp(self):
        self.aoi=gpd.GeoDataFrame(geometry=[box(-54.96,-3.04,-54.95,-3.03)],crs="EPSG:4326")

    def test_registry_contains_three_verified_services(self):
        self.assertEqual(SERVICE_CANDIDATES,(SERVICE,ALTERNATE_SERVICE,THIRD_SERVICE))
        self.assertTrue(all("pronasolos/" in x and x.endswith("/MapServer/identify")
                            for x in SERVICE_CANDIDATES))

    def test_primary_incomplete_alternate_complete_uses_alternate_only(self):
        primary=response({2:100,3:200})
        alt=response({2:1,3:2,4:3,5:4,6:5})
        session=Mock()
        session.get.side_effect=lambda url,**kwargs: alt if url==ALTERNATE_SERVICE else primary
        with patch("requests.Session",return_value=session):
            result=pronasolos_soc_profiles(self.aoi,max_points=1)
        self.assertEqual(result["0–100 cm"]["tc_ha"],15)
        self.assertTrue(result["_diagnostic"]["no_cross_service_horizon_combination"])
        self.assertGreater(result["_diagnostic"]["selected_points_by_service"][ALTERNATE_SERVICE],0)
        self.assertEqual(result["_diagnostic"]["selected_points_by_service"][SERVICE],0)

    def test_third_official_service_recovers_complete_profile(self):
        incomplete=response({2:10,3:20,4:30})
        third=response({2:1,3:2,4:3,5:4,6:5})
        session=Mock()
        session.get.side_effect=lambda url,**kwargs: (
            third if url==THIRD_SERVICE else incomplete)
        with patch("requests.Session",return_value=session):
            result=pronasolos_soc_profiles(self.aoi,max_points=1)
        self.assertEqual(result["0–100 cm"]["tc_ha"],15)
        self.assertEqual(result["_diagnostic"]["selected_points_by_service"][THIRD_SERVICE],1)
        self.assertEqual(result["_diagnostic"]["selected_points_by_service"][SERVICE],0)

    def test_two_incomplete_services_never_fake_complete_profile(self):
        primary=response({2:10,3:20,4:30})
        alt=response({5:40,6:50})
        session=Mock()
        session.get.side_effect=lambda url,**kwargs: alt if url==ALTERNATE_SERVICE else primary
        with patch("requests.Session",return_value=session):
            result=pronasolos_soc_profiles(self.aoi,max_points=1)
        self.assertEqual(result["0–30 cm"]["tc_ha"],60)
        self.assertNotIn("0–100 cm",result)
        self.assertEqual(result["_diagnostic"]["target_status"],"INCOMPLETO_NAO_EXTRAPOLAR")

    def test_local_verified_exact_pixel_intersection_precedes_http(self):
        result={"0–100 cm":{"tc_ha":107.5,"spatial_sd_tc_ha":3.2},
                "_diagnostic":{"target_status":"COMPLETO_POR_INTERSECAO_RASTER"}}
        with patch("soil_pronasolos_zonal.verified_local_horizons",return_value={i:object() for i in range(2,7)}), patch(
                "soil_pronasolos_zonal.mapped_soil_0_100_on_polygon",return_value=result) as mapped, patch(
                "requests.Session",side_effect=AssertionError("No HTTP when verified local map intersects AOI")):
            received=pronasolos_soc_profiles(self.aoi,max_points=1)
        self.assertEqual(received["0–100 cm"]["tc_ha"],107.5)
        mapped.assert_called_once()

    def test_no_raw_pixel_values_returns_explicit_nd_reason(self):
        session=Mock()
        session.get.side_effect=RuntimeError("Synthetic offline endpoint")
        with patch("requests.Session",return_value=session):
            result=pronasolos_soc_profiles(self.aoi,max_points=1)
        self.assertNotIn("0–100 cm",result)
        self.assertEqual(result["_diagnostic"]["target_status"],
                         "SERVICO_SEM_VALORES_BRUTOS_VALIDOS")
        self.assertIn("Synthetic offline endpoint",result["_diagnostic"]["reason"])

    def test_probe_records_each_attempt_without_blending(self):
        session=Mock()
        session.get.side_effect=lambda url,**kwargs: (
            response({2:10,3:20,4:30}) if url==SERVICE else
            response({5:40,6:50}))
        result=query_site(session,"synthetic",-54.95,-3.03)
        self.assertEqual(result["status"],"INCOMPLETE_NO_EXTRAPOLATION")
        self.assertEqual(len(result["attempts"]),3)
        self.assertNotIn("0–100 cm",result["profiles_tc_ha"])

if __name__=="__main__":
    unittest.main()
