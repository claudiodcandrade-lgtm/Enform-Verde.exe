import unittest

from tools.live_gui_optical_sinop import (
    capture_bbox_is_visible,
    canvas_height_fitting_window,
    fit_window_geometry,
    rendered_optical_status,
    scroll_fraction_for_target,
    scale_canvas_bbox,
)


class TestLiveGuiOpticalSinop(unittest.TestCase):
    QUALITY={"p99_luminance":120,"std_luminance":28,"visible_fraction":0.72}

    def test_tk_canvas_bbox_scales_to_physical_desktop_pixels(self):
        self.assertEqual(
            scale_canvas_bbox(100,80,300,200,(1280,720),(1920,1080)),
            (150,120,600,420),
        )

    def test_tk_canvas_bbox_preserves_coordinates_without_dpi_scaling(self):
        self.assertEqual(
            scale_canvas_bbox(100,80,300,200,(1920,1080),(1920,1080)),
            (100,80,400,280),
        )

    def test_live_window_geometry_respects_application_minimum_width(self):
        self.assertEqual(fit_window_geometry((1024, 768)), "1024x680+0+0")
        self.assertEqual(fit_window_geometry((800, 600)), "800x600+0+0")

    def test_capture_rejects_canvas_partially_outside_desktop(self):
        self.assertTrue(capture_bbox_is_visible((10, 20, 900, 700), (1024, 768)))
        self.assertFalse(capture_bbox_is_visible((327, 740, 1000, 1302), (1024, 768)))
        self.assertFalse(capture_bbox_is_visible((-1, 0, 100, 100), (1024, 768)))

    def test_outer_scroll_positions_map_below_window_top(self):
        # Before scrolling the map is below the fold (y=714); after reaching
        # the bottom it overshoots above the screen (y=-85). Recompute the
        # actual scroll fraction from measured coordinates to land at y=340.
        fraction=scroll_fraction_for_target(-85,322,799/1132,1132,334)
        self.assertAlmostEqual(fraction,0.336,places=3)

    def test_map_height_fits_window_and_desktop_bounds(self):
        self.assertEqual(canvas_height_fitting_window(711,768,334),353)
        self.assertEqual(canvas_height_fitting_window(711,768,714),0)

    def test_ibge_cartography_never_counts_as_an_optical_image(self):
        self.assertIsNone(rendered_optical_status(
            "IBGE_POTENTIAL_FALLBACK",True,None,0,self.QUALITY,canvas_item_count=5))
        self.assertIsNone(rendered_optical_status(
            "IBGE_POTENTIAL_FALLBACK",True,None,0,
            {"p99_luminance":0,"std_luminance":0,"visible_fraction":0},canvas_item_count=5))

    def test_aoi_outline_never_counts_as_an_optical_image(self):
        self.assertIsNone(rendered_optical_status(
            "AOI_LOCAL_FALLBACK",True,None,0,self.QUALITY,canvas_item_count=8))

    def test_low_contrast_cartographic_pixels_never_count_as_an_image(self):
        pale_visible={"p99_luminance":232,"std_luminance":2.1,"visible_fraction":0.98}
        self.assertIsNone(rendered_optical_status(
            "AOI_LOCAL_FALLBACK",True,None,0,pale_visible,canvas_item_count=8))
        self.assertIsNone(rendered_optical_status(
            "AOI_LOCAL_FALLBACK",True,None,0,
            {"p99_luminance":0,"std_luminance":0,"visible_fraction":0},canvas_item_count=8))

    def test_black_canvas_does_not_pass_even_when_photo_item_exists(self):
        self.assertIsNone(rendered_optical_status("CBERS-4A/WFI",True,(900,420),1,
            {"p99_luminance":0,"std_luminance":0,"visible_fraction":0}))

    def test_cbers_image_rendered_on_canvas_passes(self):
        self.assertEqual(
            rendered_optical_status("CBERS-4A/WFI • INPE", True, (900, 420), 1, self.QUALITY),
            "PASS_CBERS",
        )

    def test_sentinel2_image_rendered_on_canvas_passes_as_fallback(self):
        self.assertEqual(
            rendered_optical_status(
                "Sentinel-2 L2A / Earth Search AWS public COGs", True, (900, 420), 1, self.QUALITY
            ),
            "PASS_SENTINEL2_FALLBACK",
        )

    def test_cache_passes_only_when_source_is_optical(self):
        self.assertEqual(
            rendered_optical_status(
                "CACHE ÓPTICO • Sentinel-2 L2A", True, (900, 420), 1, self.QUALITY
            ),
            "PASS_SENTINEL2_FALLBACK",
        )
        self.assertIsNone(
            rendered_optical_status("CACHE ÓPTICO • unknown", True, (900, 420), 1)
        )

    def test_text_status_without_canvas_image_does_not_pass(self):
        self.assertIsNone(
            rendered_optical_status("Sentinel-2 carregado", True, (900, 420), 0)
        )

    def test_actual_optical_fallbacks_satisfy_gate_only_with_visible_pixels(self):
        for provider in ("NASA GIBS VIIRS", "ESRI_WORLD_IMAGERY", "CACHE ÓPTICO • Sentinel-2"):
            with self.subTest(provider=provider):
                expected = ("PASS_SENTINEL2_FALLBACK" if "sentinel-2" in provider.casefold()
                            else "PASS_OPTICAL_IMAGE_FALLBACK")
                self.assertEqual(rendered_optical_status(provider, True, (900, 420), 1, self.QUALITY), expected)
        self.assertIsNone(rendered_optical_status("MAPA CARTOGRÁFICO IBGE",True,(900,420),1,self.QUALITY))

    def test_missing_photo_or_hidden_canvas_does_not_pass(self):
        self.assertIsNone(rendered_optical_status("CBERS-4A/WFI", True, None, 1))
        self.assertIsNone(rendered_optical_status("CBERS-4A/WFI", False, (900, 420), 1))


if __name__ == "__main__":
    unittest.main()
