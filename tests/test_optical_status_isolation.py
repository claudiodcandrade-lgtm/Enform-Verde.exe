"""The visual map has its own status and cannot replace analysis status."""
import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "desktop_app.py"


class OpticalStatusIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def _method(self, name):
        node = next(n for n in ast.walk(self.tree)
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        return ast.get_source_segment(self.source, node)

    def test_map_status_is_separate_and_visible(self):
        self.assertIn('self.map_status=tk.StringVar', self.source)
        self.assertIn('textvariable=self.map_status', self.source)
        self.assertIn('self.status=tk.StringVar', self.source)

    def test_optical_routes_never_write_analysis_status(self):
        for name in ("show_google_map", "_finish_satellite_map",
                     "_draw_offline_brazil_basemap"):
            with self.subTest(method=name):
                self.assertNotIn("self.status.set(", self._method(name))

    def test_map_success_and_failure_are_labeled_visual_only(self):
        finish = self._method("_finish_satellite_map")
        self.assertIn("não altera a análise quantitativa", finish)
        self.assertIn("não alimenta cálculos", finish)
        start = self._method("show_google_map")
        self.assertIn("self.map_status.set(", start)


if __name__ == "__main__":
    unittest.main()
