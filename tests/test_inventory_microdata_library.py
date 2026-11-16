import unittest
import tempfile
from pathlib import Path

from inventory_microdata_library import summarize_inventory_microdata
from national_inventory_database import initialize_database


class InventoryMicrodataLibraryTests(unittest.TestCase):
    def test_mexiana_uses_confirmed_plot_area_and_keeps_nonspatial_status(self):
        data=summarize_inventory_microdata()
        mex=data["inventories"]["MX_SANTO_AMBROSIO_2025"]
        self.assertEqual(data["tree_record_count"],2390)
        self.assertEqual(mex["tree_record_count"],2144)
        self.assertEqual(mex["plot_count"],167)
        self.assertAlmostEqual(mex["mean_plot_agb_allometric_mg_ha"],418.66155,places=4)
        self.assertAlmostEqual(mex["mean_plot_basal_area_m2_ha"],36.42564,places=4)
        self.assertFalse(mex["plot_georeferenced"])
        self.assertFalse(mex["sar_pair_available"])
        self.assertIn("não separar FOD aluvial",mex["limitation"])
        self.assertIn("allométrica",mex["agb_kind"])

    def test_jalapao_keeps_area_normalized_metrics_unavailable(self):
        data=summarize_inventory_microdata()
        jal=data["inventories"]["CE_JALAPAO_FOREST_2026"]
        self.assertEqual(jal["tree_record_count"],246)
        self.assertEqual(jal["plot_count"],10)
        self.assertFalse(jal["area_normalized_metrics_available"])
        self.assertIsNone(jal["mean_plot_stems_ha"])
        self.assertIsNone(jal["mean_plot_basal_area_m2_ha"])
        self.assertFalse(jal["plot_georeferenced"])

    def test_catalog_registers_both_project_inventories_without_promoting_to_sar(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary=initialize_database(Path(tmp)/"inventories.sqlite")
            self.assertEqual(summary["locally_harmonized_project_inventory_datasets"],2)
            # The two owner-provided inventories plus IFN and ORNL/Tapajós
            # are local primary datasets. Only IFN and ORNL are plot-level
            # harmonized datasets; project files retain their limitations.
            self.assertEqual(summary["locally_usable_primary_inventory_datasets"],4)
            self.assertEqual(summary["locally_harmonized_plot_level_datasets"],2)


if __name__=="__main__":
    unittest.main()
