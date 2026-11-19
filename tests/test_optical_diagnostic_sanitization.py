"""Optical diagnostics must be copyable without exposing signed asset URLs."""
import ast
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "desktop_app.py"


class OpticalDiagnosticSanitizationTests(unittest.TestCase):
    def test_signed_urls_and_token_values_are_redacted(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        fn = next(node for node in tree.body
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "_sanitize_optical_diagnostic_text")
        module = ast.Module(body=[fn], type_ignores=[])
        ast.fix_missing_locations(module)
        namespace = {"re": re}
        exec(compile(module, str(SOURCE), "exec"), namespace)
        cleaned = namespace[fn.name](
            "COG failed https://example.invalid/scene.tif?token=secret&sig=private token=another-secret"
        )
        self.assertNotIn("example.invalid", cleaned)
        self.assertNotIn("secret", cleaned)
        self.assertNotIn("private", cleaned)
        self.assertIn("[URL_REDACTED]", cleaned)
        self.assertIn("token=[REDACTED]", cleaned)

    def test_map_has_copy_diagnostic_button(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('text="COPIAR DIAGNÓSTICO ÓPTICO",command=self.copy_optical_diagnostic', source)
        self.assertIn('"provider_failures"', source)


if __name__ == "__main__":
    unittest.main()
