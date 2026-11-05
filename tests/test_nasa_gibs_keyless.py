import ast
import unittest
from pathlib import Path


class KeylessSatellitePreviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] / "desktop_app.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def _function_source(self, name):
        node = next(
            node for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        )
        return ast.get_source_segment(self.source, node)

    def test_public_nasa_gibs_visualization_has_no_auth_requirement(self):
        source = self._function_source("nasa_gibs_preview")
        self.assertIn("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi", source)
        self.assertIn("VIIRS_SNPP_CorrectedReflectance_TrueColor", source)
        self.assertIn('"TIME":day', source)
        self.assertIn("range(1,8)", source)
        self.assertNotIn("Authorization", source)
        self.assertNotIn('"key"', source)
        self.assertNotIn("GOOGLE_MAPS_API_KEY", source)

    def test_anonymous_sentinel2_aws_preview_uses_public_cogs(self):
        source = self._function_source("sentinel2_earthsearch_preview")
        self.assertIn("https://earth-search.aws.element84.com/v1/search", source)
        self.assertIn('"sentinel-2-l2a"', source)
        self.assertIn('("red","green","blue")', source)
        self.assertIn("public COGs", source)
        self.assertNotIn("Authorization", source)
        self.assertNotIn('"key"', source)

    def test_keyless_optical_previews_run_before_esri_and_offline_fallback(self):
        source = self._function_source("show_google_map")
        earthsearch = source.index("sentinel2_earthsearch_preview(")
        nasa = source.index("nasa_gibs_preview(")
        esri_imagery = source.index('esri_export(rs,"World_Imagery"')
        offline = source.index("offline_brazil_preview(")
        self.assertLess(earthsearch, nasa)
        self.assertLess(nasa, esri_imagery)
        self.assertLess(esri_imagery, offline)

    def test_nasa_provider_is_marked_as_visual_context(self):
        source = self._function_source("nasa_gibs_preview")
        self.assertIn("visual context only", source)
        self.assertIn("NASA GIBS / VIIRS SNPP true color", source)


if __name__ == "__main__":
    unittest.main()
