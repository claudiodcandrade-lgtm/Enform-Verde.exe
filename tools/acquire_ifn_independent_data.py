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
import unicodedata
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
    # Check EOF integrity BEFORE csv.Sniffer: truncated final records can
    # prevent delimiter detection, hiding the recoverable transport failure.
    if "equacoes" in decoded.splitlines()[0].casefold() and not raw.endswith((b"\n", b"\r")):
        raise ValueError("truncated CSV: IFN equation panel lacks terminal newline")
    try:
        dialect = csv.Sniffer().sniff(decoded[:8192], delimiters=",;")
        reader = csv.DictReader(io.StringIO(decoded, newline=""), dialect=dialect)
        header = reader.fieldnames or []
        if len(header) < 2:
            raise ValueError("CSV lacks multi-column header")
        # DictReader silently overwrites duplicate names and stores surplus
        # fields under a None key. Neither can be accepted as clean evidence.
        normalized_header = [unicodedata.normalize("NFKC", str(name or "")).strip().casefold()
                             for name in header]
        if not all(normalized_header) or len(set(normalized_header)) != len(header):
            raise ValueError("CSV duplicate or blank observational header")
        if any(column not in header for column in expected_columns):
            raise ValueError("CSV missing expected observational columns")
        counts, biomes, states, units = 0, Counter(), Counter(), set()
        missing_biome_rows = missing_state_rows = unresolved_ua_identity_rows = 0
        ua_by_biome, typology_by_ua, strata_ua, equations_by_ua = (
            defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set))
        for row in reader:
            if None in row:
                raise ValueError("CSV observation row contains unexpected extra columns")
            if any(value is None for value in row.values()):
                raise ValueError("truncated CSV: observation row has missing fields")
            if not any(value for value in row.values()):
                continue
            counts += 1
            # Official CSV exports can have empty cells parsed as None.
            # Never sort mixed None/string keys or call a missing UF a plot.
            biome = str(row.get("bioma") or "").strip()
            state = str(row.get("uf") or "").strip()
            ua = str(row.get("ua") or "").strip()
            if "bioma" in row:
                if biome:
                    biomes[biome] += 1
                else:
                    missing_biome_rows += 1
            if "uf" in row:
                if state:
                    states[state] += 1
                else:
                    missing_state_rows += 1
            if ua:
                if not biome or not state:
                    unresolved_ua_identity_rows += 1
                    continue
                key = (biome, state, ua)
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
            "missing_biome_rows": missing_biome_rows,
            "missing_state_rows": missing_state_rows,
            "unresolved_ua_identity_rows": unresolved_ua_identity_rows,
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
            # A cell assigned to a different XML row or calculated by a
            # spreadsheet formula cannot be accepted as a primary observation.
            row_number = row.get("r", "")
            if not re.fullmatch(r"[1-9][0-9]*", row_number):
                raise ValueError("XLSX invalid row reference")
            result = {}
            for cell in row.findall("m:c", namespace):
                match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell.get("r", ""))
                if match is None or match.group(2) != row_number:
                    raise ValueError("XLSX invalid or mismatched cell reference")
                if cell.find("m:f", namespace) is not None:
                    raise ValueError("XLSX formula cell is not a primary observation")
                column = match.group(1)
                if column in result:
                    raise ValueError("XLSX duplicate cell column")
                result[column] = cell_text(cell)
            return result
        headers = cells(rows[0])
        columns = list(headers.values())
        normalized_columns = [unicodedata.normalize("NFKC", str(name or "")).strip().casefold()
                              for name in columns]
        if not all(normalized_columns) or len(set(normalized_columns)) != len(columns):
            raise ValueError("XLSX duplicate or blank observational header")
        if any(column not in columns for column in expected_columns):
            raise ValueError("XLSX missing expected observational columns")
        biome_col = next((k for k, v in headers.items() if v == "bioma"), None)
        state_col = next((k for k, v in headers.items() if v == "uf"), None)
        ua_col = next((k for k, v in headers.items() if v == "ua"), None)
        biomes, states, units = Counter(), Counter(), set()
        ua_by_biome = defaultdict(set)
        count = 0
        missing_biome_rows = missing_state_rows = unresolved_ua_identity_rows = 0
        for row in rows[1:]:
            values = cells(row)
            # Extra populated columns absent from the header must not be
            # silently discarded, even if they appear late in the workbook.
            if any(column not in headers and str(value).strip()
                   for column, value in values.items()):
                raise ValueError("XLSX observation row contains unexpected columns")
            if not any(values.values()):
                continue
            count += 1
            biome = str(values.get(biome_col, "") if biome_col else "").strip()
            state = str(values.get(state_col, "") if state_col else "").strip()
            ua = str(values.get(ua_col, "") if ua_col else "").strip()
            if biome_col:
                if biome:
                    biomes[biome] += 1
                else:
                    missing_biome_rows += 1
            if state_col:
                if state:
                    states[state] += 1
                else:
                    missing_state_rows += 1
            if ua:
                if not biome or not state:
                    unresolved_ua_identity_rows += 1
                    continue
                # Missing biome/UF cannot establish a distinct physical UA.
                key = (biome, state, ua)
                units.add(key)
                ua_by_biome[key[0]].add(key)
        if count == 0:
            raise ValueError("XLSX has no observation rows")
        return {"xlsx_header": columns[:100], "xlsx_data_rows": count,
                "missing_biome_rows": missing_biome_rows,
                "missing_state_rows": missing_state_rows,
                "unresolved_ua_identity_rows": unresolved_ua_identity_rows,
                "biome_rows": dict(sorted(biomes.items())),
                "state_rows": dict(sorted(states.items())), "unique_ua": len(units),
                "unique_ua_by_biome": {b: len(v) for b, v in sorted(ua_by_biome.items())}}


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
        record["declared_file_extension"] = target_suffix
        # Retry once only for a demonstrably incomplete payload; never
        # salvage partial rows or publish a truncated file as observed data.
        for attempt in range(1, 3):
            record["download_attempts"] = attempt
            try:
                with opener(urllib.request.Request(url, headers={"User-Agent": "EnformVerde-Scientific-Audit/1.0"}), timeout=90) as response:
                    final_url = response.geturl() if hasattr(response, "geturl") else url
                    final_parts = urllib.parse.urlsplit(final_url)
                    if final_parts.scheme != "https" or final_parts.hostname != "dados.florestal.gov.br":
                        raise ValueError("download redirected outside the official HTTPS source host")
                    digest = hashlib.sha256()
                    size = 0
                    temp = output / (source["id"] + ".partial")
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
                        declared_size = (response.headers.get("Content-Length")
                                         if hasattr(response, "headers") else None)
                        if declared_size is not None and str(declared_size).isdigit() and size != int(declared_size):
                            raise ValueError("download length mismatch: incomplete HTTP body")
                        expected = source.get("expected_columns", [])
                        with temp.open("rb") as raw:
                            signature = raw.read(4)
                            raw.seek(0)
                            sample = raw.read(4096).lstrip().lower()
                        # SFB metadata, URL suffix and actual bytes can disagree.
                        # The validated format MUST follow the payload, never MIME.
                        if signature.startswith(b"PK\x03\x04"):
                            if not zipfile.is_zipfile(temp):
                                raise ValueError("XLSX signature has invalid ZIP structure")
                            validated_suffix = ".xlsx"
                            record.update(_profile_xlsx(temp, expected))
                        else:
                            if sample.startswith((b"<!doctype html", b"<html")):
                                raise ValueError("CSV endpoint returned an HTML error page")
                            validated_suffix = ".csv"
                            record.update(_profile_csv(temp, expected))
                        target = output / (source["id"] + validated_suffix)
                        temp.replace(target)
                        record["validated_file_extension"] = validated_suffix
                    finally:
                        temp.unlink(missing_ok=True)
                    record.update(status="downloaded_unvalidated", sha256=digest.hexdigest(),
                                  byte_size=size, local_file=target.name)
            except (OSError, ValueError, TimeoutError) as exc:
                reason = str(exc)
                if attempt < 2 and (reason.startswith("truncated CSV:") or
                                    reason.startswith("download length mismatch:")):
                    continue
                record.update(status="download_failed", reason=reason[:400])
            break
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
