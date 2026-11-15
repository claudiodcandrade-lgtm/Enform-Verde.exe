import csv
import tempfile
import unittest
from pathlib import Path

from official_inventory_harvest import (
    classify_tabular_resource,
    evaluate_private_licensing_inventory,
    evaluate_totalized_inventory,
    SOURCE_HIERARCHY,
    discover_sinaflor_metadata_fast,
)


class OfficialInventoryHarvestTests(unittest.TestCase):
    def test_actual_sinaflor_discovery_paginates_without_redundant_package_show(self):
        from unittest.mock import patch
        from official_inventory_harvest import discover_sinaflor_datasets
        class Session:
            headers = {}
        calls = []
        def fake_ckan(session, action, **kwargs):
            calls.append((action, kwargs))
            if action != "package_search":
                raise AssertionError("Complete summaries must not trigger package_show")
            if kwargs["start"] == 0:
                return {"results": [
                    {"id": str(i), "title": "Inventário florestal", "resources": []}
                    for i in range(100)
                ], "count": 101}
            return {"results": [
                {"id": "100", "title": "Plano de manejo florestal", "resources": []}
            ], "count": 101}
        with patch("official_inventory_harvest.SEARCH_TERMS", ("inventario",)), patch(
            "official_inventory_harvest._ckan_action", side_effect=fake_ckan
        ):
            results = discover_sinaflor_datasets(Session())
        self.assertEqual(len(results), 101)
        self.assertEqual([args["start"] for _, args in calls], [0, 100])
        self.assertTrue(all(action == "package_search" for action, _ in calls))

    def test_actual_sinaflor_discovery_fetches_missing_resource_details(self):
        from unittest.mock import patch
        from official_inventory_harvest import discover_sinaflor_datasets
        class Session:
            headers = {}
        with patch("official_inventory_harvest.discover_sinaflor_metadata_fast",
                   return_value=[{"id": "a", "title": "Inventário florestal"}]), patch(
                       "official_inventory_harvest._ckan_action",
                       return_value={"id": "a", "title": "Inventário florestal", "resources": []}
                   ) as get:
            results = discover_sinaflor_datasets(Session())
        get.assert_called_once_with(get.call_args.args[0], "package_show", id="a")
        self.assertEqual(len(results), 1)


    def test_fast_discovery_without_count_still_reaches_second_page(self):
        from unittest.mock import patch
        class Session:
            headers = {}
        calls = []
        def fake_ckan(session, action, **kwargs):
            calls.append(kwargs["start"])
            if kwargs["start"] == 0:
                return {"results": [{"id": "one", "title": "Inventário florestal"}]}
            if kwargs["start"] == 1:
                return {"results": [{"id": "two", "title": "Plano de manejo florestal"}]}
            return {"results": []}
        with patch("official_inventory_harvest._ckan_action", side_effect=fake_ckan):
            results = discover_sinaflor_metadata_fast(Session(), rows=1, max_pages_per_term=3)
        self.assertEqual(len(results), 2)
        self.assertIn(1, calls)

    def test_incomplete_ckan_search_is_not_silently_treated_as_full_inventory(self):
        from unittest.mock import patch
        class Session:
            headers = {}
        def fake_ckan(session, action, **kwargs):
            return {"results": [{"id": str(kwargs["start"]), "title": "Inventário florestal"}],
                    "count": 300}
        with patch("official_inventory_harvest._ckan_action", side_effect=fake_ckan):
            with self.assertRaisesRegex(RuntimeError, "Consulta CKAN incompleta"):
                discover_sinaflor_metadata_fast(Session(), rows=1, max_pages_per_term=2)

    def test_fast_discovery_paginates_and_deduplicates_without_download(self):
        from unittest.mock import patch
        class Session:
            headers = {}
        calls = []
        def fake_ckan(session, action, **kwargs):
            calls.append((action, kwargs))
            if kwargs["start"] == 0:
                return {"results": [{"id": "one", "title": "Inventário florestal"}], "count": 2}
            return {"results": [{"id": "two", "title": "Plano de manejo florestal"}], "count": 2}
        with patch("official_inventory_harvest._ckan_action", side_effect=fake_ckan):
            results = discover_sinaflor_metadata_fast(Session(), rows=1, max_pages_per_term=3)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(action == "package_search" for action, _ in calls))
        self.assertTrue(all("start" in args for _, args in calls))

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
