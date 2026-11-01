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


def xlsx(records):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    root = ET.Element("worksheet", xmlns=ns)
    data = ET.SubElement(root, "sheetData")
    for n, record in enumerate([FIELDS] + records, 1):
        row = ET.SubElement(data, "row", r=str(n))
        for i, value in enumerate(record):
            col = chr(65 + i)
            cell = ET.SubElement(row, "c", r=f"{col}{n}", t="inlineStr")
            ET.SubElement(ET.SubElement(cell, "is"), "t").text = str(value)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", ET.tostring(root, encoding="utf-8"))
    return stream.getvalue()


def fixture(mismatch=False, bad_meta=False):
    litter, wood = {}, {}
    for sid, uf in LITTER_IDS.items():
        name = "Mato Grosso" if uf == "MT" else "Mato Grosso do Sul"
        ua = uf + "_1"
        lines = [f"Pantanal;{name};{ua};Mun;-57,5;-17,4;2018;14;{i};0\n"
                 for i in range(1, 6)]
        litter[sid] = (LITTER_HEADER + "".join(lines)).encode()
    for sid, uf in WOOD_IDS.items():
        name = "Mato Grosso" if uf == "MT" else "Mato Grosso do Sul"
        ua = uf + "_1"
        lon = "-58" if bad_meta and uf == "MT" else "-57.5"
        def row(flag, diam):
            values = {"bioma": "Pantanal", "uf": name, "mun": "Mun",
                      "lon_pc": lon, "lat_pc": "-17.4", "ua": ua,
                      "data": "2018", "Uso_terra_PC": "14",
                      "Ausen_necro": flag, "diam": diam}
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
        self.assertEqual(report["wood_ua_with_mixed_absence_flags"], 1)
        self.assertEqual(report["wood_rows_with_numeric_diameter"], 1)
        self.assertIsNone(report["carbon_stock_tC_ha"])
        self.assertFalse(report["scientific_validation"])

    def test_conflicting_centroid_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "centroid"):
            audit(*fixture(bad_meta=True))

    def test_source_sha256_is_mandatory(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit(*fixture(mismatch=True))


if __name__ == "__main__":
    unittest.main()
