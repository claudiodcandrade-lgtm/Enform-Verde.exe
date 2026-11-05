"""Regression for failure to prepare analysis after CAR/KML geometry loads."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "desktop_app.py"

class TestCarKmlMapSetup(unittest.TestCase):
    def test_map_setup_has_no_unbound_redraw_callback(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        candidates = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_schedule_offline_map_fit"]
        self.assertEqual(len(candidates), 1)
        fn = candidates[0]
        # The AOI outline and online/offline fallback are handled by bound methods.
        call_names = [n.func.attr for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertIn("_draw_aoi_outline", call_names)
        self.assertIn("show_google_map", call_names)
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "after":
                self.assertFalse(any(isinstance(arg, ast.Name) and arg.id == "redraw" for arg in n.args))

    def test_car_and_vector_share_geometry_preparation(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        funcs = {n.name:n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for name in ("car_lookup", "pick_vector"):
            self.assertIn(name, funcs)
            calls = [n.func.attr for n in ast.walk(funcs[name]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
            self.assertIn("_show_geom",calls)
        self.assertIn("_schedule_offline_map_fit", [n.func.attr for n in ast.walk(funcs["_show_geom"]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)])
        self.assertIn("_poll_ibge",[n.func.attr for n in ast.walk(funcs["_show_geom"]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)])

if __name__ == "__main__":
    unittest.main()
