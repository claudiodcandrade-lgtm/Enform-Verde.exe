"""Contracts for clearly framed summaries on every primary application tab."""
import ast
from pathlib import Path
import unittest


class ExecutivePanelContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(Path("desktop_app.py").read_text(encoding="utf-8"))
        cls.app = next(n for n in cls.tree.body
                       if isinstance(n, ast.ClassDef) and n.name == "App")

    def test_every_primary_tab_builds_a_bordered_executive_card(self):
        methods = ("_project", "_spatial", "_remote", "_results", "_sources",
                   "_cultivated_results")
        for name in methods:
            with self.subTest(tab=name):
                method = next(n for n in self.app.body
                              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                              and n.name == name)
                calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "_executive_card"]
                self.assertTrue(calls, f"{name} must create a framed executive card")

    def test_full_detail_areas_are_separately_labelled(self):
        source = Path("desktop_app.py").read_text(encoding="utf-8")
        for label in ("Detalhes do perímetro e diagnóstico",
                      "Detalhes técnicos e proveniência SAR / AGB",
                      "Relatório detalhado e auditoria",
                      "Métodos, fontes e limites de aplicação",
                      "Rastreabilidade, fontes e diagnósticos"):
            with self.subTest(label=label):
                self.assertIn(label, source)


if __name__ == "__main__":
    unittest.main()
