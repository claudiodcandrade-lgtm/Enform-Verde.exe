#!/usr/bin/env python3
"""Acquire independently published IFN data; NEVER mark models as validated.

Uses only explicitly configured source URLs. Preserves raw bytes and records sha256.
No plot-to-pixel calibration or confidence intervals are inferred by this tool.
"""
import argparse
import csv
import io
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET
import datetime as dt
import hashlib
import json
import pathlib
import re
import zipfile
import urllib.parse
import urllib.request

MAX_BYTES = 300_000_000

def _profile_csv(path, expected_columns=()):
    raw = pathlib.Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            decoded = raw.decode(encoding, errors="strict")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("CSV encoding cannot be decoded without replacement")
    if "\ufffd" in decoded:
        raise ValueError("CSV contains Unicode replacement characters")
    try:
        dialect = csv.Sniffer().sniff(decoded[:8192], delimiters=",;")
        reader = csv.DictReader(io.StringIO(decoded, newline=""), dialect=dialect)
        header = reader.fieldnames or []
        if len(header) < 2:
            raise ValueError("CSV lacks multi-column header")
        if any(column not in header for column in expected_columns):
            raise ValueError("CSV missing expected observational columns")
        counts, biomes, states, units = 0, Counter(), Counter(), set()
        ua_by_biome, typology_by_ua, strata_ua, equations_by_ua = (
            defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set))
        for row in reader:
            if not any(value for value in row.values()):
                continue
            counts += 1
            if "bioma" in row:
                biomes[row["bioma"]] += 1
            if "uf" in row:
                states[row["uf"]] += 1
            if row.get("ua"):
                key = (row.get("bioma", ""), row.get("uf", ""), row["ua"])
                units.add(key)
                ua_by_biome[key[0]].add(key)
                if row.get("tipologia_da_vegetacao"):
                    typology = row["tipologia_da_vegetacao"]
                    typology_by_ua[key].add(typology)
                    strata_ua[(key[0], typology)].add(key)
                if row.get("equacoes"):
                    equations_by_ua[key].add(row["equacoes"])
    except csv.Error as exc:
        raise ValueError("CSV parsing failed") from exc
    if counts == 0:
        raise ValueError("CSV has no observation rows")
    return {"csv_encoding": encoding, "csv_header": header[:100],
            "csv_data_rows": counts, "biome_rows": dict(sorted(biomes.items())),
            "state_rows": dict(sorted(states.items())), "unique_ua": len(units),
            "unique_ua_by_biome": {b: len(v) for b, v in sorted(ua_by_biome.items())},
            "strata_ua_counts": [
                {"biome": b, "typology": t, "unique_ua": len(v)}
                for (b, t), v in sorted(strata_ua.items())],
            "ua_with_multiple_inferred_typologies":
                sum(len(v) > 1 for v in typology_by_ua.values()),
            "max_equations_per_ua": max((len(v) for v in equations_by_ua.values()), default=0),
            "equation_rows_not_independent_sampling_units": "equacoes" in header,
            "strata_are_independently_validated": False}


def _profile_xlsx(path, expected_columns=()):
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if "xl/workbook.xml" not in names or "xl/worksheets/sheet1.xml" not in names or archive.testzip():
            raise ValueError("invalid XLSX workbook structure")
        if sum(info.file_size for info in archive.infolist()) > 100_000_000:
            raise ValueError("XLSX decompressed content exceeds safety limit")
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//m:t", namespace))
                      for si in root.findall("m:si", namespace)]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = sheet.findall(".//m:sheetData/m:row", namespace)
        if len(rows) < 2:
            raise ValueError("XLSX has no observation rows")
        def cell_text(cell):
            typ = cell.get("t")
            if typ == "inlineStr":
                return "".join(t.text or "" for t in cell.findall(".//m:t", namespace))
            value = cell.find("m:v", namespace)
            if value is None:
                return ""
            if typ == "s":
                return shared[int(value.text)]
            return value.text or ""
        def cells(row):
            return {re.match(r"[A-Z]+", cell.get("r", "")).group(): cell_text(cell)
                    for cell in row.findall("m:c", namespace)
                    if re.match(r"[A-Z]+", cell.get("r", ""))}
        headers = cells(rows[0])
        columns = list(headers.values())
        if any(column not in columns for column in expected_columns):
            raise ValueError("XLSX missing expected observational columns")
        biome_col = next((k for k, v in headers.items() if v == "bioma"), None)
        state_col = next((k for k, v in headers.items() if v == "uf"), None)
        ua_col = next((k for k, v in headers.items() if v == "ua"), None)
        biomes, states, units = Counter(), Counter(), set()
        count = 0
        for row in rows[1:]:
            values = cells(row)
            if not any(values.values()):
                continue
            count += 1
            if biome_col:
                biomes[values.get(biome_col, "")] += 1
            if state_col:
                states[values.get(state_col, "")] += 1
            if ua_col and values.get(ua_col):
                units.add(values[ua_col])
        if count == 0:
            raise ValueError("XLSX has no observation rows")
        return {"xlsx_header": columns[:100], "xlsx_data_rows": count,
                "biome_rows": dict(sorted(biomes.items())),
                "state_rows": dict(sorted(states.items())), "unique_ua": len(units)}


def fetch_sources(registry, output, opener=None):
    opener = opener or urllib.request.urlopen
    output = pathlib.Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for source in registry["sources"]:
        record = {key: source[key] for key in ("id", "url", "license", "role")}
        record["observed_measurement"] = source.get("observed_measurement", "unspecified")
        record["carbon_stock_ready"] = False  # raw depth/diameter alone is not tC/ha
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", str(source["id"])):
            record.update(status="blocked", reason="invalid resource id")
            results.append(record)
            continue
        record["retrieved_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        url = source["url"]
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in {"dados.florestal.gov.br"}:
            record.update(status="blocked", reason="source host not allowlisted")
            results.append(record)
            continue
        actual_suffix = pathlib.Path(parsed.path).suffix.lower()
        override = source.get("format_override")
        if override not in (None, "xlsx", "csv"):
            record.update(status="blocked", reason="unsupported source format override")
            results.append(record)
            continue
        target_suffix = "." + override if override else actual_suffix
        if target_suffix not in (".xlsx", ".csv"):
            record.update(status="blocked", reason="unsupported source extension")
            results.append(record)
            continue
        record["source_url_extension"] = actual_suffix
        record["validated_file_extension"] = target_suffix
        target = output / (source["id"] + target_suffix)
        try:
            with opener(urllib.request.Request(url, headers={"User-Agent": "EnformVerde-Scientific-Audit/1.0"}), timeout=90) as response:
                final_url = response.geturl() if hasattr(response, "geturl") else url
                final_parts = urllib.parse.urlsplit(final_url)
                if final_parts.scheme != "https" or final_parts.hostname != "dados.florestal.gov.br":
                    raise ValueError("download redirected outside the official HTTPS source host")
                digest = hashlib.sha256()
                size = 0
                temp = target.with_suffix(target.suffix + ".partial")
                try:
                    with temp.open("wb") as stream:
                        while True:
                            block = response.read(1024 * 1024)
                            if not block:
                                break
                            size += len(block)
                            if size > MAX_BYTES:
                                raise ValueError("download exceeds size limit")
                            digest.update(block)
                            stream.write(block)
                    if size == 0:
                        raise ValueError("empty response")
                    expected = source.get("expected_columns", [])
                    if target.suffix == ".xlsx":
                        if not zipfile.is_zipfile(temp):
                            raise ValueError("xlsx response is not a ZIP workbook")
                        record.update(_profile_xlsx(temp, expected))
                    elif target.suffix == ".csv":
                        with temp.open("rb") as raw:
                            sample = raw.read(4096).lstrip().lower()
                        if sample.startswith((b"<!doctype html", b"<html")):
                            raise ValueError("CSV endpoint returned an HTML error page")
                        record.update(_profile_csv(temp, expected))
                    else:
                        raise ValueError("unsupported observational file format")
                    temp.replace(target)
                finally:
                    temp.unlink(missing_ok=True)
                record.update(status="downloaded_unvalidated", sha256=digest.hexdigest(),
                              byte_size=size, local_file=target.name)
        except (OSError, ValueError, TimeoutError) as exc:
            record.update(status="download_failed", reason=str(exc)[:400])
        results.append(record)
    return {"source_registry_only": True, "scientific_validation": False, "resources": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="validation/ifn_sources.json")
    parser.add_argument("--out", default="validation/raw_ifn")
    parser.add_argument("--report", default="validation/ifn_download_audit.json")
    args = parser.parse_args()
    registry = json.loads(pathlib.Path(args.registry).read_text(encoding="utf-8"))
    result = fetch_sources(registry, args.out)
    pathlib.Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": sum(r["status"] == "downloaded_unvalidated" for r in result["resources"]),
                      "failed_or_blocked": sum(r["status"] != "downloaded_unvalidated" for r in result["resources"]),
                      "scientifically_validated": 0}))
    return 0 if all(r["status"] == "downloaded_unvalidated" for r in result["resources"]) else 1

if __name__ == "__main__":
    raise SystemExit(main())
