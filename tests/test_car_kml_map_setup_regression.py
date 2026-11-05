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

    def test_basemap_failure_does_not_block_ibge_setup(self):
        """Execute _show_geom without Tk: a map failure still schedules IBGE."""
        import queue
        import types

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_show_geom")
        isolated = ast.Module(body=[fn], type_ignores=[])
        ast.fix_missing_locations(isolated)

        class DummyValue:
            def set(self, value):
                self.value = value

        class DummyGeometry:
            def copy(self):
                return self

        class ImmediateThread:
            def __init__(self, target, **kwargs):
                self.target = target
            def start(self):
                self.target()

        class DummyApp:
            def __init__(self):
                self.gdf = DummyGeometry()
                self.project = {}
                self.spatial_text = object()
                self.status = DummyValue()
                self.aoi_area_display = DummyValue()
                self.ibge_phys_display = DummyValue()
                self._ibge_generation = 0
                self._ibge_pending = False
                self._ibge_queue = queue.Queue()
                self.after_calls = []
            def _set(self, widget, value):
                self.spatial_report = value
            def _schedule_offline_map_fit(self, label):
                raise RuntimeError("visualization unavailable")
            def _draw_aoi_outline(self, label):
                raise RuntimeError("canvas unavailable")
            def update_idletasks(self):
                pass
            def _poll_ibge(self):
                pass
            def after(self, delay, callback):
                self.after_calls.append((delay, callback))

        ns = {
            "geom_metrics": lambda geometry: {"area_ha": 1, "centroid": (0, 0), "utm_epsg": 32721},
            "format_ptbr": lambda x, places: str(x),
            "diagnose_ibge": lambda geometry: {"biomas": []},
            "threading": types.SimpleNamespace(Thread=ImmediateThread),
        }
        # Import at runtime to avoid import-time Tk/GDAL dependencies.
        import sys
        import types as builtin_types
        mock_module = builtin_types.ModuleType("property_physiognomy_display")
        mock_module.equal_area_aoi_ha = lambda geometry: 1
        previous = sys.modules.get("property_physiognomy_display")
        try:
            sys.modules["property_physiognomy_display"] = mock_module
            exec(compile(isolated, str(SOURCE), "exec"), ns)
            app = DummyApp()
            ns["_show_geom"](app, "KML validado")
        finally:
            if previous is None:
                sys.modules.pop("property_physiognomy_display", None)
            else:
                sys.modules["property_physiognomy_display"] = previous
        self.assertIn("visualization unavailable", app.project.get("map_preview_error", ""))
        self.assertTrue(app._ibge_pending)
        self.assertEqual(app._ibge_queue.get_nowait()[1], "ok")
        self.assertEqual(len(app.after_calls), 1)
        self.assertEqual(app.after_calls[0][1].__name__, "_poll_ibge")

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
