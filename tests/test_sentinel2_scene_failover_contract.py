"""Sentinel-2 visual fallback safety: never treat a catalog hit as loaded pixels."""
import ast
import pathlib
import unittest

SOURCE=pathlib.Path(__file__).resolve().parents[1]/"desktop_app.py"

class Sentinel2SceneFailoverContract(unittest.TestCase):
    def test_real_pixels_and_multiple_scenes_required(self):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
        funcs=[f for f in ast.walk(tree) if isinstance(f,ast.FunctionDef)
               and f.name=="sentinel2_earthsearch_preview"]
        self.assertEqual(len(funcs),1)
        fn=funcs[0]
        calls=[n.func.attr for n in ast.walk(fn) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute)]
        self.assertIn("reproject",calls)
        self.assertIn("read",calls)
        self.assertIn("resize",calls)
        self.assertIn("transform",calls)
        self.assertIn("isfinite",calls)
        literals=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant)
                  and isinstance(n.value,str)]
        self.assertTrue(any("pixels RGB válidos" in value for value in literals))
        self.assertTrue(any("Nenhuma das" in value for value in literals))
        # Distinct source band windows, not reusing red's exact pixel window.
        self.assertIn("win=from_bounds(",ast.get_source_segment(SOURCE.read_text(encoding="utf-8"),fn))

    def test_satellite_render_keeps_fallback(self):
        src=SOURCE.read_text(encoding="utf-8")
        tree=ast.parse(src)
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)
                and n.name=="show_google_map")
        body=ast.get_source_segment(src,fn)
        self.assertIn("sentinel2_earthsearch_preview",body)
        self.assertIn("sentinel2_preview",body)
        self.assertIn("nasa_gibs_preview",body)
        self.assertIn("offline_brazil_preview",body)

if __name__=="__main__":
    unittest.main()
