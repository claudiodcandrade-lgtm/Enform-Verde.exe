"""The dashboard renders local land-use overlays without an optical basemap."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "desktop_app.py"
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows.yml"


class LocalThematicMapContract(unittest.TestCase):
    def test_windows_build_does_not_require_an_optical_preview_fixture(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("synthetic_optical_preview", workflow)
        self.assertNotIn("app.cbers4a_wfi_preview=", workflow)

    def test_map_legend_reports_land_use_class_area_percent_and_source(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertIn("Mapa temático local de uso/cobertura após a análise", src)
        self.assertIn("Legenda com classes, área, percentual e origem", src)
        thematic = src[src.index("def _draw_land_use_map"):src.index(
            "def _draw_aoi_outline", src.index("def _draw_land_use_map")
        )]
        for token in ("USO E COBERTURA — classificação da análise",
                      "class_name", "area_ha", "area_pct", "source"):
            self.assertIn(token, thematic)

    def test_loading_vector_renders_local_map_without_optical_search(self):
        src = SOURCE.read_text(encoding="utf-8")
        geometry = src[src.index("def _show_geom"):src.index(
            "def _poll_ibge", src.index("def _show_geom")
        )]
        self.assertIn("_draw_land_use_map", geometry)
        self.assertNotIn("show_google_map", geometry)
        self.assertNotIn("_schedule_optical_map_fit", geometry)


if __name__ == "__main__":
    unittest.main()
