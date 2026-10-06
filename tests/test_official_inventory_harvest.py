import csv
import tempfile
import unittest
from pathlib import Path

from official_inventory_harvest import (
    classify_tabular_resource,
    evaluate_private_licensing_inventory,
    evaluate_totalized_inventory,
    SOURCE_HIERARCHY,
)


class OfficialInventoryHarvestTests(unittest.TestCase):
    def test_open_georeferenced_plot_csv_is_highest_data_quality_tier(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "parcelas.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["inventario_id", "parcela", "dap_cm", "latitude", "longitude"])
                writer.writerow(["A", "P01", "20", "-3.1", "-54.9"])
            result = classify_tabular_resource(path)
        self.assertEqual(result["evidence_tier"], "parcela_aberta_georreferenciada")
        self.assertEqual(result["priority"], 1)
        self.assertFalse(result["usable_for_calibration"])

    def test_totalized_inventory_is_only_a_candidate_until_error_is_audited(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "resumo.csv"
            path.write_text("fitofisionomia;media_dap;area_basal\nFloresta;22;18\n", encoding="utf-8")
            result = classify_tabular_resource(path)
        self.assertEqual(result["evidence_tier"], "inventario_totalizado_candidato")
        self.assertFalse(result["usable_for_calibration"])

    def test_private_licensing_inventory_requires_every_last_resort_gate(self):
        good = evaluate_private_licensing_inventory(
            authorized_access=True,
            published_margin_of_error=True,
            class_match=True,
            spatial_match=True,
            independent_sample_units=8,
        )
        self.assertTrue(good["may_support_estimate"])
        self.assertFalse(good["include_in_sar_calibration"])
        bad = evaluate_private_licensing_inventory(
            authorized_access=True,
            published_margin_of_error=False,
            class_match=True,
            spatial_match=True,
            independent_sample_units=8,
        )
        self.assertFalse(bad["may_support_estimate"])

    def test_totalized_institutional_inventory_requires_published_error(self):
        allowed = evaluate_totalized_inventory(
            recognized_institution=True,
            published_margin_of_error=True,
            class_match=True,
            spatial_match=True,
            independent_sample_units=12,
        )
        self.assertTrue(allowed["may_support_estimate"])
        self.assertEqual(allowed["source_hierarchy_rank"], 2)
        blocked = evaluate_totalized_inventory(
            recognized_institution=True,
            published_margin_of_error=False,
            class_match=True,
            spatial_match=True,
            independent_sample_units=12,
        )
        self.assertFalse(blocked["may_support_estimate"])

    def test_source_hierarchy_puts_recognized_research_before_licensing_records(self):
        self.assertEqual([x["rank"] for x in SOURCE_HIERARCHY], [1, 2, 3, 4, 5])
        self.assertEqual(SOURCE_HIERARCHY[0]["label"], "institucional_parcela_aberta")
        self.assertEqual(SOURCE_HIERARCHY[2]["label"], "base_publica_oficial")
        self.assertEqual(SOURCE_HIERARCHY[-1]["label"], "inventario_privado_de_licenciamento")


if __name__ == "__main__":
    unittest.main()
