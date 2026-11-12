"""Regression gates for real Sinop Windows failures (10 Nov 2026).

These tests verify implementation/retry behaviour, not remote availability,
real farm classification, or scientific validation.
"""
import ast
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import desktop_app as app
import recent_sar_landcover
import sar_landcover_lemplus

ROOT=Path(__file__).resolve().parents[1]


class SinopWindowsRecurrenceTests(unittest.TestCase):
    def test_optical_overlays_accept_3d_kml_coordinates(self):
        from shapely.geometry import Polygon
        ring=Polygon([(-55.21,-11.89,250),(-55.17,-11.89,251),
                      (-55.17,-11.85,252),(-55.21,-11.85,253),
                      (-55.21,-11.89,250)])
        coords=app._xy_coords(ring.exterior.coords)
        self.assertEqual(len(coords[0]),2)
        self.assertEqual(coords[0],(-55.21,-11.89))
        self.assertEqual(len(coords),5)
        for fn in (app.cbers4a_wfi_preview,app.nasa_gibs_preview):
            self.assertIn("_xy_coords(poly.exterior.coords)",inspect.getsource(fn))

    def test_sar_both_paths_have_four_transport_attempts(self):
        for fn in (recent_sar_landcover.run_recent_sar_screen,
                   sar_landcover_lemplus._monthly_features):
            src=inspect.getsource(fn)
            self.assertIn("for attempt in range(4):",src)
            self.assertIn('CPL_VSIL_CURL_USE_HEAD',src)
            self.assertIn('GDAL_HTTP_MULTIRANGE',src)
            self.assertIn('GDAL_HTTP_VERSION',src)
            self.assertIn('"1.1"',src)
            self.assertIn("asset_href_for_read_attempt(",src)
            self.assertIn("GDAL_HTTP_TIMEOUT",src)
            self.assertIn('"SINGLE_GET"',src)

    def test_map_refresh_uses_canvas_size_not_rendered_image_size(self):
        src=inspect.getsource(app.App._on_map_resize)
        self.assertIn("self._last_canvas_size",src)
        self.assertNotIn("size==self._last_map_size",src)
        src=inspect.getsource(app.App._finish_satellite_map)
        self.assertIn("self._last_map_size=",src)

    def test_providers_have_single_range_optical_transport(self):
        for fn in (app.cbers4a_wfi_preview,app.sentinel2_earthsearch_preview):
            src=inspect.getsource(fn)
            self.assertIn("CPL_VSIL_CURL_USE_HEAD",src)
            self.assertIn('GDAL_HTTP_MULTIRANGE":"SERIAL"',src)
            self.assertNotIn('GDAL_HTTP_MULTIRANGE":"NO"',src)
            self.assertIn('GDAL_HTTP_VERSION":"1.1"',src)

    def test_sar_retries_use_a_valid_serial_range_mode(self):
        for fn in (recent_sar_landcover.run_recent_sar_screen,
                   sar_landcover_lemplus._monthly_features):
            src=inspect.getsource(fn)
            self.assertIn('SERIAL',src)
            self.assertIn('SINGLE_GET',src)
            self.assertNotIn('GDAL_HTTP_MULTIRANGE":"NO"',src)
            self.assertIn("asset_href_for_read_attempt(",src)

    def test_mapbiomas_reader_has_independent_serial_transport(self):
        import mapbiomas_zonal
        src=inspect.getsource(mapbiomas_zonal.mapbiomas_class_percentages)
        self.assertIn('"GDAL_HTTP_MULTIRANGE":"SERIAL"',src)
        self.assertIn('"GDAL_HTTP_MULTIPLEX":"NO"',src)
        self.assertIn('"read_pixel_window"',src)

    def test_optical_pixels_retry_transport_per_candidate_scene(self):
        for fn,marker in ((app.sentinel2_earthsearch_preview,"expanded_pool"),
                          (app.cbers4a_wfi_preview,"expanded_scenes")):
            src=inspect.getsource(fn)
            self.assertIn(marker,src)
            self.assertIn("for strategy in range(3)",src)
            self.assertIn('GDAL_HTTP_MULTIPLEX',src)

    def test_optical_provider_errors_are_saved_and_redacted(self):
        with tempfile.TemporaryDirectory() as td:
            holder=type("FakeMap",(),{
                "_map_generation":9,
                "gdf":None,
            })()
            # Save routine uses HOME and no Tk methods when there is no AOI.
            with patch("pathlib.Path.home",return_value=Path(td)):
                app.App._save_optical_diagnostic(
                    holder,9,"IBGE_CARTOGRAFICO",
                    ["CBERS failed https://test.invalid/path?sig=PRIVATE&se=DATE",
                     "Sentinel2: UnicodeDecodeError"]
                )
            file=Path(td)/".enform_verde"/"ultimo_diagnostico_imagem_otica.json"
            data=json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(data["provider_displayed"],"IBGE_CARTOGRAFICO")
            self.assertEqual(len(data["attempt_errors"]),2)
            self.assertNotIn("PRIVATE",file.read_text(encoding="utf-8"))
            self.assertIn("[URL_REDACTED]",data["attempt_errors"][0])

    def test_ibge_names_remain_visible_but_explicitly_potential(self):
        src=inspect.getsource(app.App._poll_ibge)
        self.assertIn('Fitofisionomia POTENCIAL IBGE',src)
        self.assertIn('não comprova presença atual',src)
        src2=inspect.getsource(app.App._present_native_carbon)
        self.assertIn('POTENCIAL IBGE',src2)
        self.assertIn('não confirmado como nativo atual',src2)


if __name__=="__main__":
    unittest.main()
