#!/usr/bin/env python3
"""Download and profile the SFB IFN DAP10 state workbooks (Sep 2025)."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "external_raw" / "ifn_dap10_set2025"
MANIFEST = ROOT / "data" / "ifn_dap10_set2025_harvest_manifest.json"
API = "https://dados.florestal.gov.br/api/3/action/package_show"
PACKAGE = "ifn-dap-10-por-uf_disp-set2025"
HEADERS = {
    "Lotes", "UA", "bioma", "uf", "mun", "lon_pc", "lat_pc",
    "Subunidade", "Subparcela", "Data", "DAP", "HT", "scientificName",
}


def request_retry(url: str, *, params=None, timeout=(10, 180)):
    error = None
    for attempt in range(6):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            error = exc
            if attempt < 5:
                time.sleep(min(30, 2**attempt))
    raise RuntimeError(f"GET failed ({type(error).__name__})") from None


def _download(item):
    name = item["name"]
    target = OUT / name
    if target.exists() and item.get("size") and target.stat().st_size == int(item["size"]):
        data = target.read_bytes()
    else:
        response = request_retry(item["url"])
        data = response.content
        if item.get("size") and len(data) != int(item["size"]):
            raise RuntimeError(f"SIZE_MISMATCH:{name}:{len(data)}:{item['size']}")
        target.write_bytes(data)
    return name, target, len(data), hashlib.sha256(data).hexdigest()


def _profile(name, path, size, digest):
    wb = load_workbook(path, read_only=True, data_only=True)
    sheet = wb.active
    iterator = sheet.iter_rows(values_only=True)
    header = [str(v).strip() if v is not None else "" for v in next(iterator)]
    if not HEADERS.issubset(set(header)):
        raise RuntimeError(f"SCHEMA_UNEXPECTED:{name}")
    idx = {key: header.index(key) for key in HEADERS}
    row_count = 0
    units = set()
    biomes = set()
    municipalities = set()
    dates = []
    valid_dap = 0
    valid_height = 0
    species = set()
    for row in iterator:
        if not row or all(x is None for x in row):
            continue
        row_count += 1
        if row[idx["UA"]] is not None:
            units.add(str(row[idx["UA"]]))
        if row[idx["bioma"]] is not None:
            biomes.add(str(row[idx["bioma"]]))
        if row[idx["mun"]] is not None:
            municipalities.add(str(row[idx["mun"]]))
        if row[idx["Data"]]:
            dates.append(str(row[idx["Data"]]))
        try:
            valid_dap += float(row[idx["DAP"]]) > 0
        except (TypeError, ValueError):
            pass
        try:
            valid_height += float(row[idx["HT"]]) > 0
        except (TypeError, ValueError):
            pass
        if row[idx["scientificName"]]:
            species.add(str(row[idx["scientificName"]]).strip())
    wb.close()
    return {
        "filename": name, "size_bytes": size, "sha256": digest,
        "sheet": sheet.title, "row_count": row_count,
        "unique_sampling_units": len(units),
        "unit_ids": sorted(units),
        "biomes": sorted(biomes), "municipalities": len(municipalities),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "valid_dap_records": int(valid_dap),
        "valid_total_height_records": int(valid_height),
        "distinct_scientific_name_values": len(species),
        "headers": header,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    payload = request_retry(API, params={"id": PACKAGE}, timeout=(10, 90)).json()
    if not payload.get("success"):
        raise RuntimeError("CKAN_PACKAGE_SHOW_FAILED")
    package = payload["result"]
    resources = [r for r in package.get("resources", [])
                 if str(r.get("format", "")).upper() == "XLSX"
                 and str(r.get("name", "")).endswith(".xlsx")]
    if len(resources) != 27:
        raise RuntimeError(f"EXPECTED_27_STATE_WORKBOOKS_GOT_{len(resources)}")
    downloaded = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_download, row) for row in resources]
        for future in concurrent.futures.as_completed(futures):
            downloaded.append(future.result())
    profiled = []
    for name, path, size, digest in sorted(downloaded):
        profiled.append(_profile(name, path, size, digest))
    manifest = {
        "source": "Serviço Florestal Brasileiro — Inventário Florestal Nacional",
        "package_id": PACKAGE,
        "package_url": f"https://dados.florestal.gov.br/dataset/{PACKAGE}",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "release": "disponibilizada em setembro de 2025",
        "license": package.get("license_title") or package.get("license_id"),
        "downloaded_state_workbooks": len(profiled),
        "total_rows": sum(x["row_count"] for x in profiled),
        "total_unique_state_local_ua_ids": sum(x["unique_sampling_units"] for x in profiled),
        "total_valid_dap_records": sum(x["valid_dap_records"] for x in profiled),
        "total_valid_tree_height_records": sum(x["valid_total_height_records"] for x in profiled),
        "state_workbooks": profiled,
        "interpretation": (
            "Registros de árvores/subunidades do programa IFN, não inventários independentes por UF. "
            "Coordenadas identificam UA/centro da unidade e não a localização individual da árvore. "
            "DAP e altura são medições de campo; fatores de expansão e desenho amostral precisam "
            "ser usados para qualquer inferência populacional."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in (
        "downloaded_state_workbooks", "total_rows", "total_unique_state_local_ua_ids",
        "total_valid_dap_records", "total_valid_tree_height_records", "license")},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
