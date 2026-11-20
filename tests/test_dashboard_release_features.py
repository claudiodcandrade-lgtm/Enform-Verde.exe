"""Contracts for requested map, carbon dashboard, and separate workbooks."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/"desktop_app.py").read_text(encoding="utf-8"))
FUNCS={node.name:node for node in ast.walk(TREE) if isinstance(node,ast.FunctionDef)}

class DashboardReleaseFeatureTests(unittest.TestCase):
    def source(self,name):return ast.unparse(FUNCS[name])

    def test_geometry_setup_does_not_start_optical_search(self):
        source=self.source("_show_geom")
        self.assertIn("_draw_land_use_map",source)
        self.assertNotIn("_schedule_optical_map_fit",source)
        renderer=self.source("_draw_land_use_map")
        for token in ("class_name","source","area_ha","area_pct","vector_path"):
            self.assertIn(token,renderer)

    def test_excel_menu_distinguishes_carbon_and_agricultural_workbooks(self):
        menu=self.source("export_excel")
        self.assertIn("export_carbon_excel",menu)
        self.assertIn("export_monitoring_excel",menu)
        self.assertIn("Planilha de carbono nativo",menu)
        self.assertIn("Planilha de monitoramento agrícola",menu)
        agricultural=self.source("export_monitoring_excel")
        self.assertIn("Vigor e Safra",agricultural)
        self.assertIn("BarChart",agricultural)

    def test_carbon_stock_highlight_shows_both_units_and_partial_status(self):
        ui=self.source("_refresh_overall_executive_summary")
        self.assertIn("carbon_stock_var",ui)
        self.assertIn("tCO₂e",ui)
        self.assertIn("SOMA PARCIAL CONHECIDA",ui)

    def test_carbon_table_has_bordered_cells_and_uncertainty_percent(self):
        source=(ROOT/"desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("class CarbonTableGrid:",source)
        self.assertIn('relief="solid",borderwidth=1',source)
        populate=ast.unparse(FUNCS["_populate_carbon_dashboard"])
        self.assertIn("uncertainty_percent",populate)
        self.assertIn("sensitivity_percent",populate)
        self.assertIn("tCO₂e/ha",populate)

    def test_monitoring_workbook_contains_classes_chart_and_crop_report(self):
        from openpyxl import load_workbook
        with TemporaryDirectory() as temp:
            path=Path(temp)/"monitor.xlsx"
            calls=[]
            fn=FUNCS["export_monitoring_excel"]
            isolated=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(isolated)
            fake_file_dialog=SimpleNamespace(asksaveasfilename=lambda **_:str(path))
            fake_messagebox=SimpleNamespace(showinfo=lambda *args:calls.append(args),
                                             showwarning=lambda *args:calls.append(args),
                                             showerror=lambda *args:calls.append(args))
            namespace={"Path":Path,"filedialog":fake_file_dialog,"messagebox":fake_messagebox}
            exec(compile(isolated,str(ROOT/"desktop_app.py"),"exec"),namespace)
            stub=SimpleNamespace(
                project={"analysis_aoi_hash":"hash","area_ha":12,
                         "land_use":{"status":"SAR_MODELO_EXPERIMENTAL","area_aoi_ha":12,
                           "classes":[{"class_name":"Soja","source":"SAR_EXPERIMENTAL_MODELO",
                             "area_ha":8,"area_pct":66.7,"taxonomy":"cultura provável"}]}},
                gdf=object(),name=SimpleNamespace(get=lambda:"Teste"),
                crop_res=SimpleNamespace(get=lambda *_:"Vigor: N/D — sem pixels contemporâneos"),
                project_state=None)
            contract=SimpleNamespace(geometry_hash=lambda _:"hash")
            with patch.dict("sys.modules",{"analysis_pipeline_contract":contract}):
                namespace["export_monitoring_excel"](stub)
            wb=load_workbook(path)
            self.assertEqual(wb["Painel Executivo"]["A8"].value,"Soja")
            self.assertEqual(len(wb["Painel Executivo"]._charts),1)
            self.assertIn("Vigor: N/D",wb["Vigor e Safra"]["A4"].value)

if __name__=="__main__":unittest.main()
