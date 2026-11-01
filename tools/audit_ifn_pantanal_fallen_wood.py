#!/usr/bin/env python3
"""Fail-closed observational screen: IFN Pantanal litter versus fallen wood.

Same physical UA and matching centroid metadata do not establish a carbon
stock, a sampling-design variance, a fitophysiognomy or a SAR plot-pixel pair.
"""
import argparse
import hashlib
import io
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from tools.audit_ifn_pantanal_litter_necromass import rows, number, LITTER_FIELDS
from tools.ifn_state_identity import canonical_state, canonical_ua

LITTER_IDS = {
    "ifn_serapilheira_mato_grosso_retificada_2025": "MT",
    "ifn_serapilheira_mato_grosso_do_sul_retificada_2025": "MS",
}
WOOD_IDS = {
    "ifn_madeira_caida_mato_grosso_2025": "MT",
    "ifn_madeira_caida_mato_grosso_do_sul_2025": "MS",
}
WOOD_FIELDS = {"bioma", "uf", "ua", "mun", "lon_pc", "lat_pc",
               "Uso_terra_PC", "Ausen_necro", "diam", "decomp_nivel"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def xlsx_rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if "xl/worksheets/sheet1.xml" not in names or archive.testzip():
            raise ValueError("invalid IFN XLSX sheet")
        if sum(x.file_size for x in archive.infolist()) > 100_000_000:
            raise ValueError("IFN XLSX decompressed size limit")
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in item.findall(".//m:t", NS))
                      for item in root.findall("m:si", NS)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        xml_rows = root.findall(".//m:sheetData/m:row", NS)
        if len(xml_rows) < 2:
            raise ValueError("empty IFN XLSX")
        def extract(row):
            row_number = row.get("r", "")
            if not re.fullmatch(r"[1-9][0-9]*", row_number):
                raise ValueError("invalid IFN XLSX row reference")
            cells = {}
            for cell in row.findall("m:c", NS):
                ref = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell.get("r", ""))
                if not ref or ref.group(2) != row_number or ref.group(1) in cells:
                    raise ValueError("invalid or duplicate IFN XLSX cell")
                if cell.find("m:f", NS) is not None:
                    raise ValueError("formula not an IFN observation")
                typ = cell.get("t")
                if typ == "inlineStr":
                    value = "".join(t.text or "" for t in cell.findall(".//m:t", NS))
                else:
                    node = cell.find("m:v", NS)
                    value = node.text if node is not None else ""
                    if typ == "s":
                        value = shared[int(value)]
                cells[ref.group(1)] = value or ""
            return cells
        header = extract(xml_rows[0])
        normalized = [unicodedata.normalize("NFKC", v).strip().casefold()
                      for v in header.values()]
        if not all(normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("duplicate or blank IFN XLSX headers")
        if not WOOD_FIELDS.issubset(header.values()):
            raise ValueError("missing IFN wood fields")
        result = []
        for row in xml_rows[1:]:
            values = extract(row)
            if any(k not in header and str(v).strip() for k, v in values.items()):
                raise ValueError("unexpected IFN XLSX column")
            if any(str(v).strip() for v in values.values()):
                result.append({name: values.get(column, "") for column, name in header.items()})
        return result


def identity(row):
    return (str(row["mun"]).strip(),
            number(row["lon_pc"], Decimal(-180), Decimal(180)),
            number(row["lat_pc"], Decimal(-90), Decimal(90)),
            str(row["Uso_terra_PC"]).strip())


def audit(litter_by_id, wood_by_id, expected_sha256):
    all_sources = {**litter_by_id, **wood_by_id}
    if set(litter_by_id) != set(LITTER_IDS) or set(wood_by_id) != set(WOOD_IDS):
        raise ValueError("incomplete IFN Pantanal source set")
    if set(expected_sha256) != set(all_sources):
        raise ValueError("incomplete IFN Pantanal SHA256 manifest")
    digests = {}
    for sid, raw in all_sources.items():
        digest = hashlib.sha256(raw).hexdigest()
        if digest != str(expected_sha256[sid]).lower():
            raise ValueError("IFN SHA256 mismatch: " + sid)
        digests[sid] = digest
    litter = {}
    for sid, uf in LITTER_IDS.items():
        points = defaultdict(set)
        for row in rows(litter_by_id[sid], LITTER_FIELDS):
            if canonical_state(row["uf"]) != uf:
                raise ValueError("IFN litter state mismatch")
            if row["bioma"].strip() != "Pantanal":
                continue
            key = (uf, canonical_ua(row["ua"]))
            if not key[1]:
                raise ValueError("missing IFN litter UA")
            point = number(row["Ponto"], Decimal(1), Decimal(5))
            if point != point.to_integral_value() or int(point) in points[key]:
                raise ValueError("invalid or duplicate IFN litter point")
            points[key].add(int(point))
            number(row["Profundidade"], Decimal(0), Decimal("Infinity"))
            meta = identity(row)
            if not meta[0] or not meta[3]:
                raise ValueError("incomplete IFN litter metadata")
            if key in litter and litter[key] != meta:
                raise ValueError("conflicting IFN litter UA metadata")
            litter[key] = meta
        if any(v != {1, 2, 3, 4, 5} for v in points.values()):
            raise ValueError("incomplete IFN litter five-point UA")
    wood = {}
    flags = defaultdict(set)
    flag_rows = Counter()
    pantanal_rows = diameter_rows = 0
    decay_levels = Counter()
    for sid, uf in WOOD_IDS.items():
        for row in xlsx_rows(wood_by_id[sid]):
            if canonical_state(row["uf"]) != uf:
                raise ValueError("IFN fallen wood state mismatch")
            if str(row["bioma"]).strip() != "Pantanal":
                continue
            pantanal_rows += 1
            key = (uf, canonical_ua(row["ua"]))
            if not key[1]:
                raise ValueError("missing IFN fallen wood UA")
            meta = identity(row)
            if not meta[0] or not meta[3]:
                raise ValueError("incomplete IFN fallen wood metadata")
            if key in wood and wood[key] != meta:
                raise ValueError("conflicting IFN fallen wood UA metadata")
            wood[key] = meta
            flag = str(row["Ausen_necro"]).strip().upper()
            if flag not in {"S", "N"}:
                raise ValueError("unknown IFN fallen wood absence flag")
            flags[key].add(flag)
            flag_rows[flag] += 1
            diameter = str(row["diam"]).strip()
            if diameter:
                number(diameter, Decimal(0), Decimal("Infinity"))
                level = str(row["decomp_nivel"]).strip()
                if level not in {"1", "2", "3"}:
                    raise ValueError("invalid IFN wood decay level")
                decay_levels[level] += 1
                diameter_rows += 1
    overlap = set(litter) & set(wood)
    for key in overlap:
        if litter[key] != wood[key]:
            raise ValueError("IFN litter/wood UA centroid or land-code mismatch")
    mixed = sorted(key for key, values in flags.items() if len(values) > 1)
    return {
        "report_type": "licensed_IFN_Pantanal_litter_fallen_wood_screening_only",
        "source_sha256": digests,
        "pantanal_litter_physical_ua": len(litter),
        "pantanal_wood_rows": pantanal_rows,
        "pantanal_wood_physical_ua": len(wood),
        "litter_wood_same_physical_ua_with_matching_centroid_and_land_code": len(overlap),
        "wood_raw_absence_flag_rows": dict(sorted(flag_rows.items())),
        "wood_rows_with_numeric_diameter": diameter_rows,
        "wood_diameter_decay_level_rows": dict(sorted(decay_levels.items())),
        "diameter_unit": "cm",
        "decay_levels_official": {"1": "novo", "2": "decomposição inicial",
                                  "3": "decomposição avançada"},
        "wood_ua_with_mixed_absence_flags": len(mixed),
        "mixed_flag_ua_ids_for_audit": [list(k) for k in mixed],
        "absence_flag_dictionary_version_verified": True,
        "absence_flag_meanings_official": {"S": "ausência de necromassa: sim",
                                           "N": "ausência de necromassa: não"},
        "source_field_dictionary": "https://dados.florestal.gov.br/pt_BR/dataset/be526045-c776-4f69-a4ce-53ffdb96e38d/resource/1a25f349-0ba4-40b7-af4a-952da3725abd/download/metadados_ifn_madeira-caida_disp-set2025.pdf",
        "ibge_fitophysiognomy_verified": False,
        "plot_pixel_sar_validation": False,
        "sampling_design_and_wood_density_verified": False,
        "carbon_stock_tC_ha": None,
        "confidence_interval_95": None,
        "scientific_validation": False,
        "warning": "Matched UAs are not independent carbon stocks. S means necromass absent and N means present per official 2025 metadata; mixed flags within one UA require transect-level review. No dry litter mass, wood volume/area, density, sampling variance or SAR plot-pixel proof."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--download-audit", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    registry = json.loads(Path(args.download_audit).read_text(encoding="utf-8"))
    resources = {r["id"]: r for r in registry["resources"]}
    ids = set(LITTER_IDS) | set(WOOD_IDS)
    if not ids.issubset(resources):
        raise ValueError("missing licensed IFN Pantanal source")
    raw, sha = {}, {}
    for sid in ids:
        entry = resources[sid]
        suffix = ".csv" if sid in LITTER_IDS else ".xlsx"
        if (entry["status"] != "downloaded_unvalidated"
                or entry.get("local_file") != sid + suffix):
            raise ValueError("unvalidated or unexpected IFN source format")
        raw[sid] = (Path(args.raw_dir) / entry["local_file"]).read_bytes()
        sha[sid] = entry["sha256"]
    result = audit({k: raw[k] for k in LITTER_IDS},
                   {k: raw[k] for k in WOOD_IDS}, sha)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"pantanal_wood_ua": result["pantanal_wood_physical_ua"],
                      "litter_wood_overlap": result["litter_wood_same_physical_ua_with_matching_centroid_and_land_code"],
                      "scientific_validation": False}))


if __name__ == "__main__":
    main()
