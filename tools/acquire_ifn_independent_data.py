#!/usr/bin/env python3
"""Acquire independently published IFN data; NEVER mark models as validated.

Uses only explicitly configured source URLs. Preserves raw bytes and records sha256.
No plot-to-pixel calibration or confidence intervals are inferred by this tool.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
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
