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
        self.assertIn("GDAL_HTTP_TIMEOUT", source)
        self.assertIn("window=win", source)
        self.assertIn("dst_transform=target_transform", source)
        self.assertIn("cena sem pixels RGB válidos suficientes", source)
        self.assertIn("for band in (\"red\",\"green\",\"blue\")", source)
        self.assertIn("reproject(data,dest", source)
        self.assertNotIn("Authorization", source)
        self.assertNotIn('"key"', source)

    def test_sentinel2_and_cbers4a_are_the_only_optical_backdrop_routes(self):
        source = self._function_source("show_google_map")
        earthsearch = source.index("sentinel2_earthsearch_preview(")
        planetary = source.index("sentinel2_preview(")
        cbers = source.index("cbers4a_wfi_preview(")
        # V87.36/V87.38: CBERS-4A/WFI (INPE) first; Sentinel-2 only as contingency.
        self.assertLess(cbers, earthsearch)
        self.assertLess(earthsearch, planetary)
        calls = [node.func.id for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertNotIn("nasa_gibs_preview", calls)
        self.assertNotIn("esri_export", calls)
        # V87.38: labelled cartographic map allowed ONLY after every optical route.
        self.assertLess(planetary, source.index("offline_brazil_preview("))
        self.assertIn("contingência sem imagem óptica", source)

    def test_nasa_provider_is_marked_as_visual_context(self):
        source = self._function_source("nasa_gibs_preview")
        self.assertIn("visual context only", source)
        self.assertIn("NASA GIBS / VIIRS SNPP true color", source)


if __name__ == "__main__":
    unittest.main()
