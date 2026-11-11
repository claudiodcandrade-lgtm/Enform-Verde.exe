import unittest

from tools.live_gui_optical_sinop import rendered_optical_status


class TestLiveGuiOpticalSinop(unittest.TestCase):
    def test_cbers_image_rendered_on_canvas_passes(self):
        self.assertEqual(
            rendered_optical_status("CBERS-4A/WFI • INPE", True, (900, 420), 1),
            "PASS_CBERS",
        )

    def test_sentinel2_image_rendered_on_canvas_passes_as_fallback(self):
        self.assertEqual(
            rendered_optical_status(
                "Sentinel-2 L2A / Earth Search AWS public COGs", True, (900, 420), 1
            ),
            "PASS_SENTINEL2_FALLBACK",
        )

    def test_cache_passes_only_when_source_is_optical(self):
        self.assertEqual(
            rendered_optical_status(
                "CACHE ÓPTICO • Sentinel-2 L2A", True, (900, 420), 1
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
