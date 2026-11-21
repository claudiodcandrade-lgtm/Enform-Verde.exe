"""Large reports must yield to the Tk event loop while rendering."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "desktop_app.py"


class FakeText:
    def __init__(self):
        self._enform_render_generation = 0
        self.state = "disabled"
        self.value = ""
        self.callbacks = []
        self.exists = True

    def config(self, **kwargs):
        self.state = kwargs.get("state", self.state)

    def delete(self, *_args):
        self.value = ""

    def insert(self, _where, value):
        self.value += value

    def after_idle(self, callback):
        self.callbacks.append(callback)

    def after(self, _delay, callback):
        self.callbacks.append(callback)

    def winfo_exists(self):
        return self.exists

    def yview_moveto(self, _fraction):
        pass

    def drain(self):
        turns = 0
        while self.callbacks:
            self.callbacks.pop(0)()
            turns += 1
            if turns > 1000:
                raise AssertionError("report rendering did not terminate")


class ResponsiveReportRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        app = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "App")
        method = next(node for node in app.body
                      if isinstance(node, ast.FunctionDef) and node.name == "_set")
        module = ast.Module(body=[method], type_ignores=[])
        namespace = {}
        exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
        cls.set_text = staticmethod(namespace["_set"])
        helper = next(node for node in tree.body
                      if isinstance(node, ast.FunctionDef) and node.name == "_sar_details_report_excerpt")
        helper_module = ast.Module(body=[helper], type_ignores=[])
        helper_namespace = {}
        exec(compile(ast.fix_missing_locations(helper_module), str(SOURCE), "exec"), helper_namespace)
        cls.sar_excerpt = staticmethod(helper_namespace["_sar_details_report_excerpt"])

    def test_large_report_is_rendered_in_multiple_event_loop_turns(self):
        widget = FakeText()
        content = "relatorio;" * 12000
        self.set_text(None, widget, content)
        self.assertEqual(widget.value, "")
        self.assertTrue(widget.callbacks)
        self.assertEqual(widget.state, "disabled")
        widget.drain()
        self.assertEqual(widget.value, content)
        self.assertIsNone(widget._enform_pending_text)
        self.assertEqual(widget.state, "disabled")

    def test_new_report_cancels_stale_render_chunks(self):
        widget = FakeText()
        self.set_text(None, widget, "A" * 100000)
        self.set_text(None, widget, "novo relatório")
        widget.drain()
        self.assertEqual(widget.value, "novo relatório")

    def test_sar_report_excerpt_does_not_embed_massive_diagnostics(self):
        details = {"status":"ERRO_TECNICO_ROTA_PRIORITARIA", "data_origin":"SAR_NAO_PROCESSADO",
                   "audit":{"warnings":["x" * 1_200_000],
                            "inventory_fallback_gate":{"eligible":False,"reason":"rotas pendentes"},
                            "priority_height_route_gate":{"status":"ERRO_TECNICO","reason":"401"}},
                   "height_absence_certificate":{"status":"AUSENCIA_SAR_NAO_COMPROVADA",
                       "routes":[{"route":"ESA_BIOMASS_FH","technical_error_count":1,"errors":["x"*500_000]}]},
                   "inventory_agb_comparison":{"status":"N/D","reason":"menos de cinco UAs",
                       "selected_units":["ua"]*100_000}}
        excerpt = self.sar_excerpt(details)
        self.assertLess(len(repr(excerpt)), 2000)
        self.assertEqual(excerpt["inventory_fallback_gate"]["eligible"], False)
        self.assertEqual(excerpt["height_absence_certificate"]["routes"][0]["technical_error_count"], 1)

    def test_screen_report_references_sidecar_instead_of_dumping_sar_details(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("Resumo SAR/altura: "+'"+json.dumps(_sar_details_report_excerpt(sar_details)', source)
        self.assertNotIn('json.dumps(st.get("sar_details")', source)


if __name__ == "__main__":
    unittest.main()
