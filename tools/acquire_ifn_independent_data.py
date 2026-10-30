#!/usr/bin/env python3
"""Acquire independently published IFN data; NEVER mark models as validated.

Uses only explicitly configured source URLs. Preserves raw bytes and records sha256.
No plot-to-pixel calibration or confidence intervals are inferred by this tool.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import zipfile
import urllib.parse
import urllib.request

MAX_BYTES = 300_000_000

def fetch_sources(registry, output, opener=None):
    opener = opener or urllib.request.urlopen
    output = pathlib.Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for source in registry["sources"]:
        record = {key: source[key] for key in ("id", "url", "license", "role")}
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
        target = output / (source["id"] + pathlib.Path(parsed.path).suffix.lower())
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
                    if target.suffix == ".xlsx":
                        if not zipfile.is_zipfile(temp):
                            raise ValueError("xlsx response is not a ZIP workbook")
                        with zipfile.ZipFile(temp) as archive:
                            if "xl/workbook.xml" not in archive.namelist() or archive.testzip():
                                raise ValueError("invalid XLSX archive structure")
                    elif target.suffix == ".csv":
                        with temp.open("rb") as raw:
                            sample = raw.read(4096).lstrip().lower()
                        if sample.startswith((b"<!doctype html", b"<html")):
                            raise ValueError("CSV endpoint returned an HTML error page")
                    if target.suffix == ".csv":
                        with temp.open("r", encoding="utf-8-sig", errors="replace", newline="") as csv_file:
                            sample = csv_file.read(8192)
                            csv_file.seek(0)
                            try:
                                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
                                reader = csv.reader(csv_file, dialect)
                                header = next(reader, [])
                                data_rows = sum(bool(row) for row in reader)
                            except csv.Error as exc:
                                raise ValueError("CSV parsing failed") from exc
                        if len(header) < 2 or data_rows == 0:
                            raise ValueError("CSV lacks a multi-column header or data rows")
                        record["csv_header"] = header[:100]
                        record["csv_data_rows"] = data_rows
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
