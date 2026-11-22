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
from datetime import date, datetime
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
               "Uso_terra_PC", "Ausen_necro", "diam", "decomp_nivel",
               "transecto", "data"}
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
        # Spreadsheet row references must identify unique physical records.
        # Repeated or reordered XML row IDs can otherwise inflate IFN counts.
        previous_row = 0
        for xml_row in xml_rows:
            row_ref = xml_row.get("r", "")
            if not re.fullmatch(r"[1-9][0-9]*", row_ref):
                raise ValueError("invalid IFN XLSX row reference")
            current_row = int(row_ref)
            if current_row <= previous_row:
                raise ValueError("non-increasing IFN XLSX row references")
            previous_row = current_row
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
            str(row["Uso_terra_PC"]).strip(),
            str(row["data"]).strip())


def parsed_field_date(value):
    """Return (reported year, exact ISO day); year-only is never an exact date.

    The official IFN 'data' field can contain only a collection year. Matching
    year labels establish annual overlap, not simultaneous field measurement.
    Unrecognized or invalid dates remain N/D, without guessed day/month.
    """
    value = str(value).strip()
    if re.fullmatch(r"[0-9]{4}", value):
        year = int(value)
        return (year if 1900 <= year <= 2100 else None, None)
    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            day = date.fromisoformat(value)
        elif re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", value):
            dd, mm, yyyy = (int(part) for part in value.split("/"))
            day = date(yyyy, mm, dd)
        elif re.fullmatch(r"[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", value):
            # Official IFN 2025 XLSX/CSV stores full collection dates this way.
            # Midnight can be an export placeholder: prove the day, not time.
            day = datetime.strptime(value, "%Y/%m/%d %H:%M:%S").date()
        else:
            return (None, None)
    except ValueError:
        return (None, None)
    return (day.year, day.isoformat())


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
    n_rows_by_ua = Counter()
    n_rows_with_diameter_and_transect_by_ua = Counter()
    transect_flags = defaultdict(lambda: defaultdict(set))
    ua_with_blank_transect = set()
    presence_without_diameter_rows = 0
    missing_transect_rows = missing_collection_date_rows = 0
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
            if flag == "N":
                n_rows_by_ua[key] += 1
            # A missing transect column is rejected at ingestion. A blank
            # value in a present column remains explicitly unknown, not a
            # presumed independent transect or evidence of absence.
            transect = str(row["transecto"]).strip()
            if not str(row["data"]).strip():
                missing_collection_date_rows += 1
            if not transect:
                missing_transect_rows += 1
            if transect:
                transect_flags[key][transect].add(flag)
            else:
                ua_with_blank_transect.add(key)
            diameter = str(row["diam"]).strip()
            if diameter:
                measured_diameter = number(diameter, Decimal(0), Decimal("Infinity"))
                if measured_diameter <= 0:
                    raise ValueError("nonpositive IFN fallen wood diameter")
                if flag == "S":
                    raise ValueError("IFN fallen wood absence flag contradicts measured diameter")
                level = str(row["decomp_nivel"]).strip()
                if level not in {"1", "2", "3"}:
                    raise ValueError("invalid IFN wood decay level")
                decay_levels[level] += 1
                diameter_rows += 1
                if flag == "N" and transect:
                    n_rows_with_diameter_and_transect_by_ua[key] += 1
            elif flag == "N":
                presence_without_diameter_rows += 1
    overlap = set(litter) & set(wood)
    for key in overlap:
        if litter[key][:4] != wood[key][:4]:
            raise ValueError("IFN litter/wood UA centroid or land-code mismatch")
    mixed = sorted(key for key, values in flags.items() if len(values) > 1)
    mixed_same_transect = sorted(key for key, transects in transect_flags.items()
                                 if any(len(values) > 1 for values in transects.values()))
    mixed_with_blank_transect = sorted(set(mixed) & ua_with_blank_transect)
    # This is a strict metadata-only review queue, NOT a field protocol,
    # complete transect census, biomass estimate or carbon calibration.
    # Mixed S/N UAs remain outside this queue even if some logs have diameters.
    diameter_review_ua = sorted(
        key for key, values in flags.items()
        if values == {"N"} and n_rows_by_ua[key] > 0
        and n_rows_with_diameter_and_transect_by_ua[key] == n_rows_by_ua[key]
    )
    incomplete_n_ua = sum(
        n_rows_with_diameter_and_transect_by_ua[key] < count
        for key, count in n_rows_by_ua.items()
    )
    # IFN code 45 is cultivated pasture in the official 2024 dictionary.
    # Preserve the raw physical-UA join but quarantine anthropic use from
    # any future native-carbon evidence promotion.
    overlap_land_codes = Counter(litter[key][3] for key in overlap)
    pasture_ua = overlap_land_codes.get("45", 0)
    # Same physical UA and centroid do not imply simultaneous measurements.
    # Compare the original field collection-date strings, without inventing
    # temporal equivalence when either source omitted the date.
    # Preserve raw-string matches for audit/backward compatibility, but do
    # not call year-only (e.g. "2018") an exact coincident collection date.
    same_date_ua = sum(bool(litter[key][4]) and litter[key][4] == wood[key][4]
                       for key in overlap)
    different_date_ua = sum(bool(litter[key][4]) and bool(wood[key][4])
                            and litter[key][4] != wood[key][4] for key in overlap)
    unknown_date_ua = len(overlap) - same_date_ua - different_date_ua
    same_year_ua = exact_day_ua = different_exact_day_ua = unresolved_day_ua = 0
    for key in overlap:
        left_year, left_day = parsed_field_date(litter[key][4])
        right_year, right_day = parsed_field_date(wood[key][4])
        if left_year is not None and left_year == right_year:
            same_year_ua += 1
        if left_day is None or right_day is None:
            unresolved_day_ua += 1
        elif left_day == right_day:
            exact_day_ua += 1
        else:
            different_exact_day_ua += 1
    return {
        "report_type": "licensed_IFN_Pantanal_litter_fallen_wood_screening_only",
        "source_sha256": digests,
        "pantanal_litter_physical_ua": len(litter),
        "pantanal_wood_rows": pantanal_rows,
        "pantanal_wood_physical_ua": len(wood),
        "litter_wood_same_physical_ua_with_matching_centroid_and_land_code": len(overlap),
        "overlap_ua_by_ifn_land_code_unverified_ibge": dict(sorted(overlap_land_codes.items())),
        "overlap_ua_ifn_code_45_cultivated_pasture_excluded_from_native_carbon": pasture_ua,
        "overlap_ua_not_code_45_still_unverified_ibge": len(overlap) - pasture_ua,
        "ibge_confirmed_native_carbon_ua": None,
        "ifn_land_code_45_2024_dictionary": "pastagem cultivada",
        "ifn_land_code_dictionary_2024_source": "https://dados.florestal.gov.br/pt_BR/dataset/a9f00fc5-176f-4c9c-94b3-08db2f2b5ce1/resource/4f30a6ca-b31d-43b4-b673-59ac26c908b2/download/metadados_necromassa_ifn.pdf",
        "ifn_2025_land_code_dictionary_equivalence_verified": False,
        "wood_raw_absence_flag_rows": dict(sorted(flag_rows.items())),
        "wood_ua_with_only_S_flags": sum(values == {"S"} for values in flags.values()),
        "wood_ua_with_any_N_flag": sum("N" in values for values in flags.values()),
        "wood_ua_with_only_N_flags": sum(values == {"N"} for values in flags.values()),
        "wood_ua_with_any_N_row_missing_diameter_or_transect_id": incomplete_n_ua,
        "wood_ua_with_only_N_flags_and_every_N_row_has_diameter_and_transect_id_for_metadata_review": len(diameter_review_ua),
        "wood_diameter_metadata_review_ua_ids_not_stock": [list(key) for key in diameter_review_ua],
        "wood_present_flag_without_diameter_rows": presence_without_diameter_rows,
        "wood_rows_missing_transect_id": missing_transect_rows,
        "wood_rows_missing_collection_date": missing_collection_date_rows,
        "cross_source_same_field_collection_date_ua": same_date_ua,
        "cross_source_different_field_collection_date_ua": different_date_ua,
        "cross_source_missing_field_collection_date_ua": unknown_date_ua,
        "cross_source_same_reported_year_ua": same_year_ua,
        "cross_source_same_exact_field_day_ua": exact_day_ua,
        "cross_source_different_exact_field_day_ua": different_exact_day_ua,
        "cross_source_unverified_day_resolution_ua": unresolved_day_ua,
        "cross_source_collection_date_equivalence_verified": bool(overlap) and exact_day_ua == len(overlap),
        "sar_acquisition_date_equivalence_verified": False,
        "wood_rows_with_numeric_diameter": diameter_rows,
        "wood_diameter_decay_level_rows": dict(sorted(decay_levels.items())),
        "diameter_unit": "cm",
        "decay_levels_official": {"1": "novo", "2": "decomposição inicial",
                                  "3": "decomposição avançada"},
        "wood_ua_with_mixed_absence_flags": len(mixed),
        "mixed_flag_ua_ids_for_audit": [list(k) for k in mixed],
        "wood_ua_with_mixed_flags_within_same_nonblank_transect": len(mixed_same_transect),
        "mixed_same_transect_ua_ids_for_audit": [list(k) for k in mixed_same_transect],
        "wood_ua_with_mixed_flags_and_blank_transect": len(mixed_with_blank_transect),
        "mixed_blank_transect_ua_ids_for_audit": [list(k) for k in mixed_with_blank_transect],
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
        "warning": "Matched UAs are not independent carbon stocks. IFN code 45 indicates cultivated pasture in the published 2024 dictionary and is excluded from native-carbon candidates; all other codes still require IBGE and current-cover verification. S/N flags describe individual records, not UA-wide absence. Mixed flags require transect-level review; blank transect IDs cannot be assigned to a transect. Presence without diameter or a transect identifier is incomplete, not zero biomass. The strict all-N diameter-metadata review queue is not proof of complete field sampling, density, biomass or carbon. Matching year-only collection labels do not establish the same field day. No dry litter mass, wood volume/area, density, sampling variance or SAR plot-pixel proof."
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
