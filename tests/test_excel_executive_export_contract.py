"""Export regression: executive workbook, audited totals and readable numbers."""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "desktop_app.py"

class ExcelExecutiveContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls.export = next(fn for fn in ast.walk(tree)
                          if isinstance(fn, ast.FunctionDef) and fn.name=="export_excel")
        cls.src = ast.unparse(cls.export)

    def test_summary_precedes_all_existing_tabs(self):
        self.assertIn('create_sheet(\'PAINEL EXECUTIVO\', 0)',self.src)
        self.assertIn('create_sheet(\'Totais tCO2e\')',self.src)

    def test_total_uses_stock_not_multiplication_by_full_aoi(self):
        self.assertIn("self.project.get('total_tco2e')",self.src)
        self.assertNotIn('totalco2 * area',self.src)
        self.assertIn('stock * 44 / 12',self.src)

    def test_all_numeric_cells_use_brazilian_two_decimals(self):
        self.assertIn("cell.number_format = '#,##0.00'",self.src)
        self.assertIn('sheet.row_dimensions',self.src)
        self.assertIn('wrap_text=True',self.src)
        self.assertIn('sheet.column_dimensions',self.src)

    def test_graphs_show_inventory_stems_basal_area_and_sar_height(self):
        self.assertIn("create_sheet('Gráficos')",self.src)
        self.assertIn('mean_stems_ha',self.src)
        self.assertIn('mean_basal_area_m2_ha',self.src)
        self.assertIn('height_pixel_distribution',self.src)
        self.assertIn('height_absence_certificate',self.src)
        self.assertIn('regional_height_fallback_decision',self.src)
        self.assertIn('top10_by_plot_incidence',self.src)
        self.assertEqual(self.src.count('LineChart()'),2)
        self.assertEqual(self.src.count('BarChart()'),1)
        self.assertIn('Fonte:',self.src)
        self.assertIn('Pixels SAR',self.src)

    def test_diameter_chart_data_isolated_from_height_panel(self):
        # Diameter values and their chart helper series stay in A:C and rows
        # 40:47; D:E are exclusively the visible height distribution panel.
        start = self.src.index("dbh_bins =")
        end = self.src.index("chart['D2'] =")
        diameter = self.src[start:end]
        self.assertIn("chart['A40']", diameter)
        self.assertIn("chart['A41']", diameter)
        self.assertIn("min_row=41, max_row=47", diameter)
        self.assertIn("max_col=3", diameter)
        self.assertNotRegex(diameter, r"chart(?:\.cell\([^)]*,\\s*[45]\\s*,|\\[['\\\"](?:D|E)\\d)")
        height = self.src[end:]
        self.assertIn("chart['D4'] = 'Faixa de altura (m)'", height)
        self.assertIn("chart['E4'] = 'Frequência (%)'", height)
        self.assertIn("chart.cell(row, 4, label)", height)

    def test_missing_litter_never_fabricated_as_zero(self):
        self.assertIn('N/D — NÃO SOMADA',self.src)
        self.assertIn('Serapilheira',self.src)

if __name__=='__main__':
    unittest.main()
