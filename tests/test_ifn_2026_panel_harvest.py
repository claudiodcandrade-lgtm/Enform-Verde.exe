"""Offline verification of the 2026 SFB field-evidence acquisition route."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.harvest_ifn_field_data import (DATASETS, PANEL_RESOURCES, harvest_sfb_2026_panel,
                                         infer_state, inspect_csv, inspect_workbook)


class Reply:
    def __init__(self, *, text="", body=b""):
        self.text = text
        self.content = body

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, license_ok=True, html_csv=False):
        self.license_ok = license_ok
        self.html_csv = html_csv
        self.urls = []

    def get(self, url, timeout=None):
        self.urls.append(url)
        if "dataset/painel-de-biomassa-e-carbono" in url:
            return Reply(text=("Creative Commons Attribution 4.0"
                               if self.license_ok else "no declared license"))
        if self.html_csv:
            return Reply(body=b"<!doctype html><html>access denied</html>")
        return Reply(body=("bioma;ua;necromassa_t_por_ha\n"
                           "Amazônia;UA001;2.3\n").encode("utf-8"))


class SFBPanelHarvestTests(unittest.TestCase):
    def test_cc_by_records_archived_with_hash_and_not_homologated(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            session = Session()
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(session, report)
            self.assertEqual(set(report["datasets"]), set(PANEL_RESOURCES))
            self.assertEqual(report["failures"], [])
            for name in PANEL_RESOURCES:
                item = report["datasets"][name]
                self.assertEqual(item["status"], "harvested_not_validated")
                row = item["resources"][0]
                self.assertEqual(row["unique_ua_by_biome"]["Amazônia"], 1)
                blob = Path(tmp, name, row["filename"]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), row["sha256"])
                self.assertEqual(row["bytes"], len(blob))

    def test_equation_equivalence_resource_mislabeled_csv_is_parsed_as_xlsx(self):
        # Official SFB resource a7396a8a-... advertises an XLSX MIME while
        # the published filename ends in .csv. Do not silently drop its data.
        from io import BytesIO
        from openpyxl import Workbook

        workbook = Workbook()
        ws = workbook.active
        ws.append(["bioma", "uf", "ua", "teste_equivalencia"])
        ws.append(["Cerrado", "GO", "UA008", "not_independent_SAR_validation"])
        stream = BytesIO()
        workbook.save(stream)
        xlsx_bytes = stream.getvalue()
        self.assertTrue(xlsx_bytes.startswith(b"PK\\x03\\x04"))

        class MixedFormatSession(Session):
            def get(self, url, timeout=None):
                if "dadosabertos_testeequacoes_" in url:
                    self.urls.append(url)
                    return Reply(body=xlsx_bytes)
                return super().get(url, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(MixedFormatSession(), report)
            self.assertEqual(report["failures"], [])
            record = report["datasets"]["panel_equation_tests"]["resources"][0]
            self.assertEqual(record["payload_format_detected"], "xlsx")
            self.assertTrue(record["filename"].endswith(".csv"))
            self.assertEqual(record["unique_ua_by_biome"]["Cerrado"], 1)
            self.assertTrue(record["equation_equivalence_not_independent_sar_validation"])
            self.assertEqual(hashlib.sha256(xlsx_bytes).hexdigest(), record["sha256"])

    def test_missing_license_stops_download(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            session = Session(license_ok=False)
            harvest_sfb_2026_panel(session, report)
            self.assertEqual(len(session.urls), 1)
            self.assertEqual(report["datasets"], {})
            self.assertTrue(any("license" in error for error in report["failures"]))

    def test_html_failure_never_claims_harvest(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(Session(html_csv=True), report)
            self.assertEqual(len(report["failures"]), len(PANEL_RESOURCES))
            self.assertTrue(all(item["status"] == "access_or_schema_error"
                                for item in report["datasets"].values()))


    def test_licensed_2025_ifn_land_use_is_harvest_candidate_not_carbon_validation(self):
        route, license_policy = DATASETS["land_use_subplots"]
        self.assertEqual(route, "/pt_BR/dataset/ifn-uso-da-terra-por-uf_disp-set2025")
        self.assertEqual(license_policy, "cc_by")
        self.assertEqual(infer_state("IFN_Uso-da-terra_Mato_Grosso_do_Sul_disp-set2025.xlsx"), "MS")
        self.assertEqual(infer_state("IFN_Uso-da-terra_Mato_Grosso_disp-set2025.xlsx"), "MT")
        self.assertEqual(infer_state("IFN_Uso-da-terra_Para_disp-set2025.xlsx"), "PA")

    def test_ua_identity_is_composite_of_state_and_plot_in_csv(self):
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Amazônia;PA;UA001;-3.1;-54.9\n"
                "Amazônia;AM;UA001;-3.2;-60.1\n"
                "Amazônia;PA;UA001;-3.1;-54.9\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_by_biome"]["Amazônia"], 2)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Amazônia"], 2)
        self.assertEqual(report["nonempty_data_rows"], 3)
        self.assertTrue(report["ua_identity_state_disambiguated"])
        self.assertIsNone(report["ua_identity_warning"])

    def test_missing_uf_does_not_claim_state_disambiguation(self):
        body = b"bioma;ua;lat_pc;lon_pc\nCerrado;UA001;-15;-47\n"
        report = inspect_csv(body)
        self.assertFalse(report["ua_identity_state_disambiguated"])
        self.assertEqual(report["ua_rows_missing_state"], 1)
        self.assertIn("UF missing", report["ua_identity_warning"])

    def test_missing_uf_in_per_state_csv_uses_auditable_filename_hint(self):
        body = ("bioma;ua;lat_pc;lon_pc\n"
                "Amazônia;UA001;-3.1;-54.9\n"
                "Amazônia;UA001;-3.1;-54.9\n").encode("utf-8")
        result = inspect_csv(body, source_uf="PA")
        self.assertTrue(result["ua_identity_state_disambiguated"])
        self.assertEqual(result["ua_rows_state_inferred_from_filename"], 2)
        self.assertEqual(result["source_uf_filename_hint"], "PA")
        self.assertEqual(result["unique_ua_by_biome"]["Amazônia"], 1)
        self.assertEqual(result["ua_rows_missing_state"], 0)

    def test_conflicting_state_in_per_state_csv_is_rejected(self):
        body = b"bioma;uf;ua\nCerrado;GO;UA001\n"
        with self.assertRaisesRegex(ValueError, "conflicts"):
            inspect_csv(body, source_uf="TO")
        with self.assertRaisesRegex(ValueError, "invalid source UF"):
            inspect_csv(body, source_uf="XX")

    def test_full_state_names_and_accents_canonicalize_to_uf(self):
        body = ("bioma;estado;ua\n"
                "Pantanal;Mato Grosso do Sul;UA009\n"
                "Pantanal;MS;UA009\n"
                "Mata Atlântica;Espírito Santo;UA010\n").encode("utf-8")
        result = inspect_csv(body)
        self.assertEqual(result["unique_ua_by_biome"]["Pantanal"], 1)
        self.assertEqual(result["unique_ua_by_biome"]["Mata Atlântica"], 1)
        self.assertTrue(result["ua_identity_state_disambiguated"])

    def test_full_state_name_matches_source_uf_and_unknown_state_rejected(self):
        valid = "bioma;estado;ua\nPantanal;Mato Grosso do Sul;UA009\n".encode("utf-8")
        result = inspect_csv(valid, source_uf="MS")
        self.assertEqual(result["unique_ua_by_biome"]["Pantanal"], 1)
        invalid = b"bioma;estado;ua\nPantanal;Estado Inexistente;UA009\n"
        with self.assertRaisesRegex(ValueError, "unrecognized UF"):
            inspect_csv(invalid)
        with self.assertRaisesRegex(ValueError, "unrecognized UF"):
            inspect_csv(b"bioma;uf;ua\nPantanal;ZZ;UA009\n")

    def test_per_state_xlsx_without_uf_uses_filename_hint(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ifn_go.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["bioma", "ua", "lat_pc", "lon_pc"])
            ws.append(["Cerrado", "UA007", -15.0, -47.0])
            wb.save(path)
            report = inspect_workbook(path, source_uf="GO")
        self.assertTrue(report["sheets"][0]["ua_identity_state_disambiguated"])
        self.assertEqual(report["sheets"][0]["ua_rows_state_inferred_from_filename"], 1)
        self.assertEqual(report["unique_ua_by_biome"]["Cerrado"], 1)

    def test_zero_coordinate_placeholder_is_not_georeferenced(self):
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Pantanal;MS;UA001;0;0\n"
                "Pantanal;MS;UA002;-18.5;-56.8\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_by_biome"]["Pantanal"], 2)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Pantanal"], 1)
        self.assertEqual(report["ua_rows_invalid_coordinates"], 1)

    def test_conflicting_centroids_do_not_count_as_georeferenced_ua(self):
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Amazônia;PA;UA001;-3.1;-54.9\n"
                "Amazônia;PA;UA001;-3.2;-54.9\n"
                "Amazônia;PA;UA002;-3.3;-54.8\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_by_biome"]["Amazônia"], 2)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Amazônia"], 1)
        self.assertEqual(report["ua_with_conflicting_coordinates_by_biome"]["Amazônia"], 1)

    def test_mixed_valid_invalid_centroids_quarantine_entire_ua(self):
        # Previously a valid row hid a zero/invalid row for the same UA.
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Pantanal;MS;UA001;-18.5;-56.8\n"
                "Pantanal;MS;UA001;0;0\n"
                "Pantanal;MS;UA002;-18.6;-56.9\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_by_biome"]["Pantanal"], 2)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Pantanal"], 1)
        self.assertEqual(report["ua_rows_invalid_coordinates"], 1)
        self.assertEqual(report["ua_with_invalid_coordinate_rows_by_biome"]["Pantanal"], 1)

    def test_missing_uf_cannot_claim_georeferenced_independent_ua(self):
        body = ("bioma;ua;lat_pc;lon_pc\n"
                "Cerrado;UA001;-15;-47\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertFalse(report["ua_identity_state_disambiguated"])
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"], {})
        self.assertEqual(report["ua_with_valid_coordinates_but_missing_state_by_biome"]["Cerrado"], 1)

    def test_mixed_valid_invalid_xlsx_centroids_quarantine_ua(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ifn_ms.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["bioma", "uf", "ua", "lat_pc", "lon_pc"])
            ws.append(["Pantanal", "MS", "UA001", -18.5, -56.8])
            ws.append(["Pantanal", "MS", "UA001", 0, 0])
            ws.append(["Pantanal", "MS", "UA002", -18.6, -56.9])
            wb.save(path)
            report = inspect_workbook(path)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Pantanal"], 1)
        self.assertEqual(report["sheets"][0]["ua_with_invalid_coordinate_rows_by_biome"]["Pantanal"], 1)

    def test_repeated_subplots_same_centroid_remain_one_ua(self):
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Cerrado;GO;UA001;-15.0;-47.0\n"
                "Cerrado;GO;UA001;-15.000;-47.000\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Cerrado"], 1)
        self.assertEqual(report["ua_with_conflicting_coordinates_by_biome"], {})
        self.assertEqual(report["ua_rows_invalid_coordinates"], 0)

    def test_nonfinite_or_out_of_bounds_coordinates_are_rejected(self):
        body = ("bioma;uf;ua;lat_pc;lon_pc\n"
                "Caatinga;CE;UA001;nan;-39.0\n"
                "Caatinga;CE;UA002;-9.0;200.0\n"
                "Caatinga;CE;UA003;-9.1;-39.1\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["unique_ua_with_coordinates_by_biome"]["Caatinga"], 1)
        self.assertEqual(report["ua_rows_invalid_coordinates"], 2)

    def test_tab_delimiter_and_state_aware_ua_are_supported(self):
        body = ("bioma\tuf\tua\n"
                "Cerrado\tGO\tUA001\n"
                "Cerrado\tTO\tUA001\n").encode("utf-8")
        report = inspect_csv(body)
        self.assertEqual(report["delimiter"], "\t")
        self.assertEqual(report["unique_ua_by_biome"]["Cerrado"], 2)

    def test_xlsx_uses_same_state_aware_ua_identity(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plots.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["bioma", "uf", "ua", "lat_pc", "lon_pc"])
            ws.append(["Pantanal", "MS", "UA009", -18.0, -57.0])
            ws.append(["Pantanal", "MT", "UA009", -16.0, -56.0])
            wb.save(path)
            report = inspect_workbook(path)
        self.assertEqual(report["unique_ua_by_biome"]["Pantanal"], 2)
        self.assertTrue(report["sheets"][0]["ua_identity_state_disambiguated"])
        self.assertTrue(report["ua_counts_aggregated_from_sheets_not_globally_deduplicated"])


    def test_equations_panel_retains_other_category_without_fake_ua(self):
        # Observed in official harvest 41174387124: UF='Outro' blocked
        # the entire licensed equations CSV. This is not a valid Brazilian UF.
        raw = ("bioma;uf;ua;equacoes\n"
               "Amazônia;Outro;UA001;equacao_x\n"
               "Amazônia;PA;UA001;equacao_y\n").encode("utf-8")
        report = inspect_csv(raw, allow_non_state_uf=True)
        self.assertEqual(report["nonempty_data_rows"], 2)
        self.assertEqual(report["non_state_uf_rows_excluded_from_ua_counts"], 1)
        self.assertEqual(report["observation_rows_by_biome"]["Amazônia"], 2)
        self.assertEqual(report["unique_ua_by_biome"]["Amazônia"], 1)
        self.assertTrue(report["ua_identity_state_disambiguated"])
        self.assertIn("never counted", report["non_state_uf_policy"])

    def test_other_uf_rejected_for_field_data_and_unrecognized_uf_still_rejected(self):
        raw = b"bioma;uf;ua\nPantanal;Outro;UA001\n"
        with self.assertRaisesRegex(ValueError, "unrecognized UF"):
            inspect_csv(raw)
        with self.assertRaisesRegex(ValueError, "unrecognized UF"):
            inspect_csv(b"bioma;uf;ua\nPantanal;ZZ;UA001\n",
                        allow_non_state_uf=True)

    def test_live_panel_equations_other_category_does_not_abort_harvest(self):
        class OfficialPanelSession(Session):
            def get(self, url, timeout=None):
                if "dadosabertos_equacoes_" in url:
                    self.urls.append(url)
                    return Reply(body=("bioma;uf;ua;equacoes\n"
                                       "Cerrado;Outro;UA009;modelo_a\n"
                                       "Cerrado;GO;UA009;modelo_b\n").encode("utf-8"))
                return super().get(url, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(OfficialPanelSession(), report)
            self.assertEqual(report["failures"], [])
            equations = report["datasets"]["panel_equations"]
            self.assertEqual(equations["status"], "harvested_not_validated")
            record = equations["resources"][0]
            self.assertEqual(record["non_state_uf_rows_excluded_from_ua_counts"], 1)
            self.assertEqual(record["unique_ua_by_biome"]["Cerrado"], 1)
            self.assertTrue(Path(tmp, "panel_equations", record["filename"]).is_file())

if __name__ == "__main__":
    unittest.main()
