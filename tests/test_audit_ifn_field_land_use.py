"""Synthetic primary-field source joins, not observational validation."""
import csv
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
from tools.audit_ifn_field_land_use import audit, digest, SOURCES


class FieldSubplotCrossCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.candidates = self.base / "candidates.csv"
        with self.candidates.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["uf", "ua", "bioma_declarado", "classe_nativa_declarada",
                                               "legenda_1_ibge_verificada", "par_sar_validado"])
            w.writeheader()
            for uf, ua, biome in [("MT", "1", "Cerrado"), ("MT", "2", "Cerrado"),
                                  ("MS", "3", "Pantanal"), ("PA", "4", "Amazônia")]:
                w.writerow({"uf": uf, "ua": ua, "bioma_declarado": biome,
                            "classe_nativa_declarada": "native",
                            "legenda_1_ibge_verificada": "false", "par_sar_validado": "false"})
        self.paths = {}
        self.report = {"resources": []}
        self.samples = {
            "MT": [("Cerrado", "MT", "1", "1", "1", "S", "A"),
                   ("Cerrado", "MT", "1", "1", "2", "S", "A"),
                   ("Cerrado", "MT", "2", "1", "1", "S", "B"),
                   ("Cerrado", "MT", "2", "1", "2", "N", "C")],
            "MS": [("Pantanal", "MS", "3", "1", "1", "N", "D")],
            "PA": [("Amazônia", "PA", "7", "1", "1", "S", "A")],
        }
        self._save()

    def _save(self):
        self.report = {"resources": []}
        for sid, uf in SOURCES.items():
            wb = Workbook()
            ws = wb.active
            ws.append(["bioma", "uf", "ua", "sub", "subp", "cobertura_florestal", "uso_da_terra"])
            for row in self.samples[uf]:
                ws.append(row)
            path = self.base / (sid + ".xlsx")
            wb.save(path)
            self.paths[sid] = path
            self.report["resources"].append({"id": sid, "status": "downloaded_unvalidated",
                "validated_file_extension": ".xlsx", "sha256": digest(path)})

    def test_unique_ua_and_mixed_subplots_not_independent(self):
        r = audit(self.candidates, self.paths, self.report)
        self.assertEqual(r["field_unique_physical_ua"], 4)
        self.assertEqual(r["matched_unique_physical_ua"], 3)
        cerrado = r["by_declared_biome"]["cerrado"]
        self.assertEqual(cerrado["matched_physical_ua"], 2)
        self.assertEqual(cerrado["all_recorded_subplots_forest_S"], 1)
        self.assertEqual(cerrado["mixed_forest_S_N_subplots"], 1)
        self.assertEqual(r["by_declared_biome"]["pantanal"]["all_recorded_subplots_forest_N"], 1)
        self.assertEqual(r["by_declared_biome"]["amazônia"]["no_matching_field_ua"], 1)
        self.assertIsNone(r["confidence_interval_95"])
        self.assertFalse(r["scientific_validation"])

    def test_duplicate_subplot_quarantined(self):
        self.samples["MT"].append(("Cerrado", "MT", "1", "1", "1", "S", "A"))
        self._save()
        r = audit(self.candidates, self.paths, self.report)
        self.assertEqual(r["by_declared_biome"]["cerrado"]["field_identity_or_biome_unresolved"], 1)

    def test_conflicting_biome_quarantined(self):
        self.samples["MT"].append(("Amazônia", "MT", "1", "1", "3", "S", "A"))
        self._save()
        r = audit(self.candidates, self.paths, self.report)
        self.assertEqual(r["by_declared_biome"]["cerrado"]["field_identity_or_biome_unresolved"], 1)

    def test_source_hash_and_status_must_match(self):
        self.report["resources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit(self.candidates, self.paths, self.report)
        self.report["resources"][0]["status"] = "download_failed"
        with self.assertRaisesRegex(ValueError, "missing, failed"):
            audit(self.candidates, self.paths, self.report)

    def test_formula_rejected_as_field_data(self):
        self.samples["MS"][0] = ("Pantanal", "MS", "3", "1", "1", "=1+1", "D")
        self._save()
        with self.assertRaisesRegex(ValueError, "formula"):
            audit(self.candidates, self.paths, self.report)

    def test_panel_cannot_claim_ibge_validation(self):
        raw = self.candidates.read_text(encoding="utf-8").replace("false,false", "true,false", 1)
        self.candidates.write_text(raw, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cannot assert"):
            audit(self.candidates, self.paths, self.report)


if __name__ == "__main__":
    unittest.main()
