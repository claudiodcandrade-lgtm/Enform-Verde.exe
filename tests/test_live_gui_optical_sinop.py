import unittest

from tools.live_gui_optical_sinop import rendered_optical_status


class TestLiveGuiOpticalSinop(unittest.TestCase):
    QUALITY={"p99_luminance":120,"std_luminance":28,"visible_fraction":0.72}

    def test_ibge_cartographic_fallback_passes_only_with_visible_canvas_pixels(self):
        self.assertEqual(rendered_optical_status(
            "IBGE_POTENTIAL_FALLBACK",True,None,0,self.QUALITY,canvas_item_count=5),
            "PASS_IBGE_FALLBACK")
        self.assertIsNone(rendered_optical_status(
            "IBGE_POTENTIAL_FALLBACK",True,None,0,
            {"p99_luminance":0,"std_luminance":0,"visible_fraction":0},canvas_item_count=5))

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

    def test_cartography_and_other_imagery_do_not_satisfy_optical_gate(self):
        for provider in ("MAPA CARTOGRÁFICO IBGE", "NASA GIBS VIIRS", "ESRI_WORLD_IMAGERY"):
            with self.subTest(provider=provider):
                self.assertIsNone(
                    rendered_optical_status(provider, True, (900, 420), 1)
                )

    def test_missing_photo_or_hidden_canvas_does_not_pass(self):
        self.assertIsNone(rendered_optical_status("CBERS-4A/WFI", True, None, 1))
        self.assertIsNone(rendered_optical_status("CBERS-4A/WFI", False, (900, 420), 1))


if __name__ == "__main__":
    unittest.main()
