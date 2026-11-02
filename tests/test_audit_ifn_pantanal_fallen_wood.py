"""Synthetic regression tests for IFN Pantanal litter × fallen wood screening."""
import hashlib
import io
import unittest
import xml.etree.ElementTree as ET
import zipfile

from tools.audit_ifn_pantanal_fallen_wood import LITTER_IDS, WOOD_IDS, audit

FIELDS = ["bioma", "uf", "mun", "lon_pc", "lat_pc", "ua", "data",
          "Uso_terra_PC", "Ausen_necro", "transecto", "decomp_nivel",
          "n_gr", "diam", "Lotes"]
LITTER_HEADER = "bioma;uf;ua;mun;lon_pc;lat_pc;data;Uso_terra_PC;Ponto;Profundidade\n"


def xlsx(records, row_number_overrides=None, fields=FIELDS):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    root = ET.Element("worksheet", xmlns=ns)
    data = ET.SubElement(root, "sheetData")
    for n, record in enumerate([fields] + records, 1):
        n = (row_number_overrides or {}).get(n, n)
        row = ET.SubElement(data, "row", r=str(n))
        for i, value in enumerate(record):
            col = chr(65 + i)
            cell = ET.SubElement(row, "c", r=f"{col}{n}", t="inlineStr")
            ET.SubElement(ET.SubElement(cell, "is"), "t").text = str(value)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", ET.tostring(root, encoding="utf-8"))
    return stream.getvalue()


def fixture(mismatch=False, bad_meta=False, land_code="14", wood_date_override=None, litter_date="2018"):
    litter, wood = {}, {}
    for sid, uf in LITTER_IDS.items():
        name = "Mato Grosso" if uf == "MT" else "Mato Grosso do Sul"
        ua = uf + "_1"
        lines = [f"Pantanal;{name};{ua};Mun;-57,5;-17,4;{litter_date};{land_code};{i};0\n"
                 for i in range(1, 6)]
        litter[sid] = (LITTER_HEADER + "".join(lines)).encode()
    for sid, uf in WOOD_IDS.items():
        name = "Mato Grosso" if uf == "MT" else "Mato Grosso do Sul"
        ua = uf + "_1"
        lon = "-58" if bad_meta and uf == "MT" else "-57.5"
        def row(flag, diam):
            values = {"bioma": "Pantanal", "uf": name, "mun": "Mun",
                      "lon_pc": lon, "lat_pc": "-17.4", "ua": ua,
                      "data": (wood_date_override if wood_date_override is not None and uf == "MT" else litter_date),
                      "Uso_terra_PC": land_code,
                      "Ausen_necro": flag, "transecto": "1" if flag == "N" else "", "diam": diam,
                      "decomp_nivel": "3" if diam else ""}
            return [values.get(k, "") for k in FIELDS]
        wood[sid] = xlsx([row("S", "")] if uf == "MT"
                         else [row("S", ""), row("N", "9")])
    sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
    if mismatch:
        sha[next(iter(WOOD_IDS))] = "0" * 64
    return litter, wood, sha


class IFNFallenWoodPantanalTests(unittest.TestCase):
    def test_same_ua_screened_without_carbon_promotion(self):
        report = audit(*fixture())
        self.assertEqual(report["pantanal_litter_physical_ua"], 2)
        self.assertEqual(report["pantanal_wood_rows"], 3)
        self.assertEqual(report["pantanal_wood_physical_ua"], 2)
        self.assertEqual(report["litter_wood_same_physical_ua_with_matching_centroid_and_land_code"], 2)
        self.assertEqual(report["wood_raw_absence_flag_rows"], {"N": 1, "S": 2})
        self.assertEqual(report["overlap_ua_by_ifn_land_code_unverified_ibge"], {"14": 2})
        self.assertEqual(report["overlap_ua_ifn_code_45_cultivated_pasture_excluded_from_native_carbon"], 0)
        self.assertIsNone(report["ibge_confirmed_native_carbon_ua"])
        self.assertEqual(report["wood_ua_with_mixed_absence_flags"], 1)
        self.assertEqual(report["wood_ua_with_only_S_flags"], 1)
        self.assertEqual(report["wood_ua_with_any_N_flag"], 1)
        self.assertEqual(report["wood_ua_with_only_N_flags"], 0)
        self.assertEqual(report["wood_present_flag_without_diameter_rows"], 0)
        self.assertEqual(report["wood_rows_missing_transect_id"], 2)
        self.assertEqual(report["wood_rows_missing_collection_date"], 0)
        self.assertFalse(report["cross_source_collection_date_equivalence_verified"])
        self.assertEqual(report["cross_source_same_field_collection_date_ua"], 2)
        self.assertEqual(report["cross_source_same_reported_year_ua"], 2)
        self.assertEqual(report["cross_source_same_exact_field_day_ua"], 0)
        self.assertEqual(report["cross_source_unverified_day_resolution_ua"], 2)
        self.assertEqual(report["cross_source_different_field_collection_date_ua"], 0)
        self.assertFalse(report["sar_acquisition_date_equivalence_verified"])
        self.assertEqual(report["wood_ua_with_mixed_flags_within_same_nonblank_transect"], 0)
        self.assertEqual(report["wood_ua_with_mixed_flags_and_blank_transect"], 1)
        self.assertEqual(report["mixed_blank_transect_ua_ids_for_audit"], [["MS", "ms_1"]])
        self.assertEqual(report["wood_rows_with_numeric_diameter"], 1)
        self.assertEqual(report["wood_diameter_decay_level_rows"], {"3": 1})
        self.assertTrue(report["absence_flag_dictionary_version_verified"])
        self.assertEqual(report["diameter_unit"], "cm")
        self.assertIn("ausência", report["absence_flag_meanings_official"]["S"])
        self.assertIsNone(report["carbon_stock_tC_ha"])
        self.assertFalse(report["scientific_validation"])

    def test_conflicting_centroid_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "centroid"):
            audit(*fixture(bad_meta=True))

    def test_source_sha256_is_mandatory(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit(*fixture(mismatch=True))

    def test_absence_flag_with_measured_diameter_is_rejected(self):
        litter, wood, _ = fixture()
        sid = next(iter(WOOD_IDS))
        wood[sid] = xlsx([["Pantanal", "Mato Grosso", "Mun", "-57.5",
                           "-17.4", "MT_1", "2018", "14", "S", "", "3",
                           "", "9", ""]])
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "contradicts measured diameter"):
            audit(litter, wood, sha)

    def test_zero_diameter_is_not_a_measured_log(self):
        litter, wood, _ = fixture()
        sid = next(iter(WOOD_IDS))
        wood[sid] = xlsx([["Pantanal", "Mato Grosso", "Mun", "-57.5",
                           "-17.4", "MT_1", "2018", "14", "N", "", "3",
                           "", "0", ""]])
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "nonpositive"):
            audit(litter, wood, sha)

    def test_presence_without_diameter_remains_incomplete_not_zero(self):
        litter, wood, _ = fixture()
        sid = next(iter(WOOD_IDS))
        wood[sid] = xlsx([["Pantanal", "Mato Grosso", "Mun", "-57.5",
                           "-17.4", "MT_1", "2018", "14", "N", "", "",
                           "", "", ""]])
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        report = audit(litter, wood, sha)
        self.assertEqual(report["wood_present_flag_without_diameter_rows"], 1)
        self.assertEqual(report["wood_rows_with_numeric_diameter"], 1)
        self.assertIsNone(report["carbon_stock_tC_ha"])


    def test_same_nonblank_transect_with_mixed_flags_requires_review(self):
        litter, wood, _ = fixture()
        sid = next(k for k, v in WOOD_IDS.items() if v == "MS")
        def row(flag, diameter):
            values = {"bioma": "Pantanal", "uf": "Mato Grosso do Sul",
                      "mun": "Mun", "lon_pc": "-57.5", "lat_pc": "-17.4",
                      "ua": "MS_1", "data": "2018", "Uso_terra_PC": "14",
                      "Ausen_necro": flag, "transecto": "1",
                      "diam": diameter, "decomp_nivel": "3" if diameter else ""}
            return [values.get(k, "") for k in FIELDS]
        wood[sid] = xlsx([row("S", ""), row("N", "9")])
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        report = audit(litter, wood, sha)
        self.assertEqual(report["wood_ua_with_mixed_flags_within_same_nonblank_transect"], 1)
        self.assertEqual(report["wood_ua_with_mixed_flags_and_blank_transect"], 0)
        self.assertFalse(report["scientific_validation"])

    def test_duplicate_xml_row_reference_is_rejected(self):
        litter, wood, _ = fixture()
        sid = next(k for k, v in WOOD_IDS.items() if v == "MS")
        record = ["Pantanal", "Mato Grosso do Sul", "Mun", "-57.5",
                  "-17.4", "MS_1", "2018", "14", "S", "", "", "", "", ""]
        wood[sid] = xlsx([record, record], row_number_overrides={3: 2})
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "non-increasing IFN XLSX row"):
            audit(litter, wood, sha)

    def test_reordered_xml_row_reference_is_rejected(self):
        litter, wood, _ = fixture()
        sid = next(k for k, v in WOOD_IDS.items() if v == "MS")
        record = ["Pantanal", "Mato Grosso do Sul", "Mun", "-57.5",
                  "-17.4", "MS_1", "2018", "14", "S", "", "", "", "", ""]
        wood[sid] = xlsx([record, record], row_number_overrides={2: 3, 3: 2})
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "non-increasing IFN XLSX row"):
            audit(litter, wood, sha)

    def test_missing_transect_column_cannot_masquerade_as_unknown_ids(self):
        litter, wood, _ = fixture()
        sid = next(iter(WOOD_IDS))
        columns = [field for field in FIELDS if field != "transecto"]
        record = ["Pantanal", "Mato Grosso", "Mun", "-57.5", "-17.4",
                  "MT_1", "2018", "14", "S", "", "", "", ""]
        wood[sid] = xlsx([record], fields=columns)
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "missing IFN wood fields"):
            audit(litter, wood, sha)

    def test_missing_collection_date_column_blocks_temporal_provenance(self):
        litter, wood, _ = fixture()
        sid = next(iter(WOOD_IDS))
        columns = [field for field in FIELDS if field != "data"]
        record = ["Pantanal", "Mato Grosso", "Mun", "-57.5", "-17.4",
                  "MT_1", "14", "S", "", "", "", "", ""]
        wood[sid] = xlsx([record], fields=columns)
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in {**litter, **wood}.items()}
        with self.assertRaisesRegex(ValueError, "missing IFN wood fields"):
            audit(litter, wood, sha)

    def test_cultivated_pasture_code_45_is_not_promoted_as_native(self):
        report = audit(*fixture(land_code="45"))
        self.assertEqual(report["litter_wood_same_physical_ua_with_matching_centroid_and_land_code"], 2)
        self.assertEqual(report["overlap_ua_by_ifn_land_code_unverified_ibge"], {"45": 2})
        self.assertEqual(report["overlap_ua_ifn_code_45_cultivated_pasture_excluded_from_native_carbon"], 2)
        self.assertEqual(report["overlap_ua_not_code_45_still_unverified_ibge"], 0)
        self.assertIsNone(report["ibge_confirmed_native_carbon_ua"])
        self.assertIsNone(report["carbon_stock_tC_ha"])
        self.assertFalse(report["scientific_validation"])

    def test_different_field_dates_do_not_prove_temporal_equivalence(self):
        report = audit(*fixture(wood_date_override="2019"))
        self.assertEqual(report["litter_wood_same_physical_ua_with_matching_centroid_and_land_code"], 2)
        self.assertEqual(report["cross_source_same_field_collection_date_ua"], 1)
        self.assertEqual(report["cross_source_different_field_collection_date_ua"], 1)
        self.assertEqual(report["cross_source_missing_field_collection_date_ua"], 0)
        self.assertFalse(report["cross_source_collection_date_equivalence_verified"])
        self.assertIsNone(report["carbon_stock_tC_ha"])

    def test_missing_field_date_does_not_prove_temporal_equivalence(self):
        report = audit(*fixture(wood_date_override=""))
        self.assertEqual(report["cross_source_same_field_collection_date_ua"], 1)
        self.assertEqual(report["cross_source_missing_field_collection_date_ua"], 1)
        self.assertEqual(report["wood_rows_missing_collection_date"], 1)
        self.assertFalse(report["cross_source_collection_date_equivalence_verified"])
        self.assertFalse(report["scientific_validation"])

    def test_full_calendar_dates_are_required_for_exact_day_proof(self):
        report = audit(*fixture(litter_date="2018-04-01"))
        self.assertEqual(report["cross_source_same_reported_year_ua"], 2)
        self.assertEqual(report["cross_source_same_exact_field_day_ua"], 2)
        self.assertEqual(report["cross_source_unverified_day_resolution_ua"], 0)
        self.assertTrue(report["cross_source_collection_date_equivalence_verified"])
        self.assertFalse(report["scientific_validation"])

    def test_official_ifn_timestamp_format_proves_calendar_day_not_hour(self):
        report = audit(*fixture(litter_date="2018/07/09 00:00:00"))
        self.assertEqual(report["cross_source_same_exact_field_day_ua"], 2)
        self.assertEqual(report["cross_source_unverified_day_resolution_ua"], 0)
        self.assertTrue(report["cross_source_collection_date_equivalence_verified"])
        self.assertFalse(report["sar_acquisition_date_equivalence_verified"])
        self.assertFalse(report["scientific_validation"])

    def test_same_year_different_days_cannot_be_called_temporally_equivalent(self):
        report = audit(*fixture(litter_date="2018-04-01",
                                wood_date_override="2018-04-02"))
        self.assertEqual(report["cross_source_same_reported_year_ua"], 2)
        self.assertEqual(report["cross_source_same_exact_field_day_ua"], 1)
        self.assertEqual(report["cross_source_different_exact_field_day_ua"], 1)
        self.assertFalse(report["cross_source_collection_date_equivalence_verified"])
        self.assertIsNone(report["carbon_stock_tC_ha"])

    def test_invalid_calendar_date_is_not_inferred_from_year(self):
        report = audit(*fixture(litter_date="2018-02-30"))
        self.assertEqual(report["cross_source_same_exact_field_day_ua"], 0)
        self.assertEqual(report["cross_source_unverified_day_resolution_ua"], 2)
        self.assertFalse(report["cross_source_collection_date_equivalence_verified"])

if __name__ == "__main__":
    unittest.main()
