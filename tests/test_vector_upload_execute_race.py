"""Regression for Execute pressed while an uploaded vector is still loading."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "desktop_app.py"


class VectorUploadExecuteRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls.functions = {
            node.name: node for node in ast.walk(cls.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_execute_is_queued_until_async_vector_validation_finishes(self):
        fn = self.functions["execute"]
        source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)
        self.assertLess(source.index("if self._vector_load_pending"), source.index("if self.gdf is None"))
        self.assertIn("self._pending_execute=True", source)
        self.assertIn("a análise começará automaticamente", source)

    def test_successful_upload_does_not_clear_queued_execute_request(self):
        fn = self.functions["pick_vector"]
        # One reset at the start invalidates old results. A second reset in the
        # success callback used to erase the user's queued Execute request.
        resets = [node for node in ast.walk(fn)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "_reset_analysis_state"]
        self.assertEqual(len(resets), 1)
        self.assertIn("self._vector_load_pending=False", ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn))

    def test_failed_upload_clears_deferred_execution(self):
        fn = self.functions["pick_vector"]
        source = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)
        error_branch = source[source.index('if kind!="ok"'):source.index("# The analysis state was already cleared")]
        self.assertIn("self._vector_load_pending=False", error_branch)
        self.assertIn("self._pending_execute=False", error_branch)


if __name__ == "__main__":
    unittest.main()
