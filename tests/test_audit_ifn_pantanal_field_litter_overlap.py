"""Synthetic contract tests; no real carbon or SAR validation."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook

from tools.audit_ifn_field_land_use import SOURCES as FIELD_IDS
from tools.audit_ifn_pantanal_field_litter_overlap import LITTER_IDS, audit
from tools.audit_ifn_field_land_use import digest


class PantanalFieldLitterJoinTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.fd = self.root / "field"
        self.ld = self.root / "litter"
        self.fd.mkdir()
        self.ld.mkdir()
        self.field_rows = {
            "MT": [("Pantanal", "MT", "A", "1", "1", "S", "14"),
                   ("Pantanal", "MT", "A", "1", "2", "N", "14"),
                   ("Pantanal", "MT", "B", "1", "1", "S", "45")],
            "MS": [("Pantanal", "MS", "C", "1", "1", "N", "31")],
            "PA": [("Amazônia", "PA", "D", "1", "1", "S", "14")],
        }
        self.litter_codes = {"MT": {"A": "14", "E": "14"},
                             "MS": {"C": "45"}}
        self._save()

    def _save(self):
        self.fp, self.lp = {}, {}
        self.fr, self.lr = {"resources": []}, {"resources": []}
        for sid, uf in FIELD_IDS.items():
            path = self.fd / (sid + ".xlsx")
            wb = Workbook()
            ws = wb.active
            ws.append(["bioma", "uf", "ua", "lon_pc", "lat_pc", "sub", "subp",
                       "cobertura_florestal", "uso_da_terra"])
            for row in self.field_rows[uf]:
                ws.append([row[0], row[1], row[2], "-57,5", "-17,4", *row[3:]])
            wb.save(path)
            self.fp[sid] = path
            self.fr["resources"].append({"id": sid, "local_file": path.name,
                "status": "downloaded_unvalidated", "validated_file_extension": ".xlsx",
                "sha256": digest(path)})
        for sid, uf in LITTER_IDS.items():
            path = self.ld / (sid + ".csv")
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["bioma", "uf", "ua", "mun", "lon_pc", "lat_pc",
                                 "data", "Uso_terra_PC", "Ponto", "Profundidade"])
                for ua, code in self.litter_codes[uf].items():
                    for point in range(1, 6):
                        writer.writerow(["Pantanal", uf, ua, "Mun", "-57,5", "-17,4",
                                         "2018/07/09 00:00:00", code, point, "0"])
            self.lp[sid] = path
            self.lr["resources"].append({"id": sid, "local_file": path.name,
                "status": "downloaded_unvalidated", "validated_file_extension": ".csv",
                "sha256": digest(path)})

    def test_real_identity_only_and_land_code_disagreement(self):
        r = audit(self.fp, self.lp, self.fr, self.lr)
        self.assertEqual(r["field_pantanal_physical_ua"], 3)
        self.assertEqual(r["litter_pantanal_physical_ua"], 3)
        self.assertEqual(r["same_physical_ua_field_and_litter"], 2)
        self.assertEqual(r["field_only_pantanal_physical_ua"], 1)
        self.assertEqual(r["litter_only_pantanal_physical_ua"], 1)
        self.assertEqual(r["by_uf"]["MT"]["single_land_code_equal_across_sources"], 1)
        self.assertEqual(r["by_uf"]["MS"]["single_land_code_disagrees_across_sources"], 1)
        self.assertEqual(r["by_uf"]["MT"]["mixed_field_forest_flags"], 1)
        self.assertEqual(r["by_uf"]["MT"]["same_reported_centroid_not_independent_accuracy"], 1)
        self.assertEqual(r["by_uf"]["MS"]["same_reported_centroid_not_independent_accuracy"], 1)
        self.assertIsNone(r["carbon_stock_tC_ha"])
        self.assertIsNone(r["confidence_interval_95"])
        self.assertFalse(r["scientific_validation"])

    def test_field_biome_conflict_is_quarantined(self):
        self.field_rows["MT"].append(("Cerrado", "MT", "A", "1", "3", "S", "14"))
        self._save()
        r = audit(self.fp, self.lp, self.fr, self.lr)
        self.assertEqual(r["field_ua_with_conflicting_pantanal_biome_quarantined"], 1)
        self.assertEqual(r["same_physical_ua_field_and_litter"], 1)

    def test_duplicate_litter_point_rejected(self):
        sid = next(iter(LITTER_IDS))
        path = self.lp[sid]
        with path.open("a", encoding="utf-8") as f:
            f.write("Pantanal;MT;A;Mun;-57,5;-17,4;2018;14;1;0\n")
        self.lr["resources"][0]["sha256"] = digest(path)
        with self.assertRaisesRegex(ValueError, "duplicate litter point"):
            audit(self.fp, self.lp, self.fr, self.lr)

    def test_source_integrity_required(self):
        self.fr["resources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit(self.fp, self.lp, self.fr, self.lr)

    def test_missing_required_source_rejected(self):
        self.lr["resources"].pop()
        with self.assertRaisesRegex(ValueError, "missing required licensed source"):
            audit(self.fp, self.lp, self.fr, self.lr)

    def test_field_land_code_mixed_not_counted_as_agreement(self):
        self.field_rows["MT"][1] = ("Pantanal", "MT", "A", "1", "2", "N", "31")
        self._save()
        r = audit(self.fp, self.lp, self.fr, self.lr)
        self.assertEqual(r["by_uf"]["MT"]["field_land_code_mixed_or_missing"], 1)
        self.assertNotIn("single_land_code_equal_across_sources", r["by_uf"]["MT"])


    def _edit_reported_centroid(self, state, ua, longitude):
        sid = next(sid for sid, uf in FIELD_IDS.items() if uf == state)
        path = self.fp[sid]
        wb = load_workbook(path)
        ws = wb.active
        for row in ws.iter_rows(min_row=2):
            if row[2].value == ua:
                row[3].value = longitude
        wb.save(path)
        self.fr["resources"][list(FIELD_IDS).index(sid)]["sha256"] = digest(path)

    def test_reported_centroid_disagreement_not_promoted_to_accuracy(self):
        self._edit_reported_centroid("MS", "C", "-58,0")
        r = audit(self.fp, self.lp, self.fr, self.lr)
        self.assertEqual(r["by_uf"]["MS"]["reported_centroid_disagrees_between_sources"], 1)
        self.assertNotIn("same_reported_centroid_not_independent_accuracy", r["by_uf"]["MS"])
        self.assertFalse(r["ibge_fitophysiognomy_verified"])
        self.assertIsNone(r["carbon_stock_tC_ha"])

    def test_missing_reported_centroid_is_ND(self):
        self._edit_reported_centroid("MS", "C", None)
        r = audit(self.fp, self.lp, self.fr, self.lr)
        self.assertEqual(r["by_uf"]["MS"]["field_reported_centroid_missing_or_conflicting"], 1)
        self.assertFalse(r["scientific_validation"])


if __name__ == "__main__":
    unittest.main()
