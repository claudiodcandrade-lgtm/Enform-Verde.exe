#!/usr/bin/env python3
"""Harvest licensed, plot-level SFB IFN biophysical records for audit and pairing.

This collector archives source workbooks and emits a schema/coverage manifest. It
never turns catalog rows or field data into a validation pass; SAR pairing,
spatial holdout, and component-specific error analysis remain separate steps.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from openpyxl import load_workbook

BASE = "https://dados.florestal.gov.br"
OUT = Path("ifn_field_harvest")
USER_AGENT = "Enform-Verde-IFN-field-harvest/1.0"
STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapa",
    "BA": "Bahia", "CE": "Ceara", "DF": "Distrito Federal", "ES": "Espirito Santo",
    "GO": "Goias", "MA": "Maranhao", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Para", "PB": "Paraiba", "PE": "Pernambuco",
    "PI": "Piaui", "PR": "Parana", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondonia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "Sao Paulo", "TO": "Tocantins",
}
TARGET_UFS = ("AM", "PA", "GO", "TO", "CE", "PI", "PR", "ES", "MT", "MS")
DATASETS = {
    "dap10": ("/pt_BR/dataset/ifn-dap-10-por-uf_disp-set2025", True),
    "fallen_wood": ("/pt_BR/dataset/ifn-madeira-caida-por-uf_disp-set2025", True),
    "litter_corrected": ("/pt_BR/dataset/ifn-serapilheira-por-uf_disp-set2025", True),
    "necromass": ("/dataset/ifn-necromassa-por-uf_disp-mai2024", True),
}
DOWNLOAD_RE = re.compile(r'href=["\']([^"\']+/download/[^"\']+)["\']', re.I)
EXTENSIONS = (".xlsx", ".csv")


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"[^A-Z0-9]+", "_", "".join(c for c in value if not unicodedata.combining(c)).upper()).strip("_")


def infer_state(filename):
    n = norm(filename)
    for code, name in sorted(STATE_NAMES.items(), key=lambda item: len(item[1]), reverse=True):
        if norm(name) in n:
            return code
    for code in STATE_NAMES:
        if re.search(rf"(?:^|_){code}(?:_|\.|$)", n):
            return code
    return None


def find_license(page):
    clean = re.sub(r"<[^>]+>", " ", page)
    clean = re.sub(r"\s+", " ", clean)
    m = re.search(r"Creative Commons.{0,100}(?:Atribui[cç][aã]o|Attribution)(?:.{0,40}(?:4\.0|BY))?", clean, re.I)
    return m.group(0).strip() if m else "not_explicitly_identified"


def inspect_workbook(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    sheets = []
    total_rows = 0
    plot_ids = set()
    coordinate_rows = 0
    biomes = {}
    headers_seen = set()
    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        candidate_header = None
        header_index = None
        preview = []
        nonempty = 0
        for idx, raw in enumerate(rows):
            vals = [str(v).strip() if v is not None else "" for v in raw]
            if not any(vals):
                continue
            nonempty += 1
            if len(preview) < 3:
                preview.append(vals[:30])
            if candidate_header is None and idx < 30:
                tokens = {norm(v) for v in vals if v}
                has_ua = any(t in {"UA", "UNIDADE_AMOSTRAL", "UNIDADE_DE_AMOSTRAGEM"} for t in tokens)
                has_bio = any(t in {"BIOMA", "NM_BIOMA"} for t in tokens)
                has_plot = has_ua or has_bio or any(t in {"LON_PC", "LAT_PC", "LONGITUDE", "LATITUDE"} for t in tokens)
                if has_plot:
                    candidate_header, header_index = vals, idx
                    headers_seen.update(norm(v) for v in vals if v)
                    continue
            if candidate_header is not None and idx > header_index:
                row = dict(zip(candidate_header, vals))
                upper = {norm(k): v for k, v in row.items()}
                ua = next((upper[k] for k in ("UA", "UNIDADE_AMOSTRAL", "UNIDADE_DE_AMOSTRAGEM") if k in upper), "")
                if ua:
                    plot_ids.add(ua)
                lat = next((upper[k] for k in ("LAT_PC", "LATITUDE", "LAT") if k in upper), "")
                lon = next((upper[k] for k in ("LON_PC", "LONGITUDE", "LON", "LONG") if k in upper), "")
                if lat and lon:
                    try:
                        if -90 <= float(lat.replace(",", ".")) <= 90 and -180 <= float(lon.replace(",", ".")) <= 180:
                            coordinate_rows += 1
                    except ValueError:
                        pass
                biome = next((upper[k] for k in ("BIOMA", "NM_BIOMA") if k in upper), "")
                if biome:
                    biomes[biome] = biomes.get(biome, 0) + 1
        sheets.append({"sheet": ws.title, "nonempty_rows": nonempty,
                       "header_row_1based": None if header_index is None else header_index + 1,
                       "headers": candidate_header or [], "preview": preview})
        total_rows += max(0, nonempty - (1 if header_index is not None else 0))
    wb.close()
    return {"sheets": sheets, "nonempty_data_rows_approx": total_rows,
            "unique_ua_count": len(plot_ids), "coordinate_rows": coordinate_rows,
            "biome_row_counts": biomes, "normalized_headers": sorted(headers_seen)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    report = {
        "agency": "Serviço Florestal Brasileiro",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "harvest and schema coverage only; not model validation",
        "target_ufs": list(TARGET_UFS),
        "datasets": {}, "failures": [], "soil_license": {
            "dataset_page": BASE + "/pt_BR/dataset/solos_ifn",
            "status": "not_downloaded_license_not_provided",
            "reason": "official CKAN page indicates no license; require permission before reuse",
        },
    }
    for key, (route, expect_cc_by) in DATASETS.items():
        page_url = urljoin(BASE, route)
        try:
            response = session.get(page_url, timeout=45)
            response.raise_for_status()
            page = response.text
            license_text = find_license(page)
            licensed = bool(re.search(r"Creative Commons.{0,100}(?:Atribui[cç][aã]o|Attribution)", page, re.I))
            if expect_cc_by and not licensed:
                raise RuntimeError("explicit CC BY license not found on the official dataset page")
            links = {}
            for href in DOWNLOAD_RE.findall(page):
                full = urljoin(BASE, href.replace("&amp;", "&"))
                filename = unquote(Path(urlsplit(full).path).name)
                if filename.lower().endswith(EXTENSIONS):
                    uf = infer_state(filename)
                    if uf in TARGET_UFS:
                        links[(uf, filename)] = full
            result = {"dataset_page": page_url, "license": license_text,
                      "expected_cc_by": expect_cc_by, "resources_found": len(links),
                      "resources": []}
            if not links:
                report["failures"].append(f"{key}: no target-state CSV/XLSX links")
            for (uf, filename), url in sorted(links.items()):
                try:
                    download = session.get(url, timeout=120)
                    download.raise_for_status()
                    body = download.content
                    if not body or len(body) > 100_000_000:
                        raise RuntimeError(f"invalid resource size {len(body)} bytes")
                    digest = hashlib.sha256(body).hexdigest()
                    target = OUT / key / uf / filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(body)
                    record = {"uf": uf, "filename": filename, "source_url": url,
                              "bytes": len(body), "sha256": digest}
                    if filename.lower().endswith(".xlsx"):
                        record.update(inspect_workbook(target))
                    else:
                        record["csv_header"] = body[:4096].decode("utf-8-sig", "replace").splitlines()[:5]
                    result["resources"].append(record)
                except Exception as exc:
                    report["failures"].append(f"{key}/{filename}: {type(exc).__name__}: {exc}")
            report["datasets"][key] = result
        except Exception as exc:
            report["datasets"][key] = {"dataset_page": page_url, "license": "unknown",
                                       "resources_found": 0, "resources": []}
            report["failures"].append(f"{key}: {type(exc).__name__}: {exc}")
    biome_counts = {}
    for dataset in report["datasets"].values():
        for resource in dataset.get("resources", []):
            for label, count in resource.get("biome_row_counts", {}).items():
                biome_counts[label] = biome_counts.get(label, 0) + count
    report["biome_row_counts_from_downloaded_records"] = biome_counts
    report["biome_source_presence"] = {
        biome: {"observed_rows": sum(count for label, count in biome_counts.items()
                                     if norm(label) == norm(biome))}
        for biome in ("Amazônia", "Cerrado", "Caatinga", "Mata Atlântica", "Pantanal")
    }
    report["validation_status"] = "harvested_not_validated"
    output = OUT / "ifn_field_harvest_manifest.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": str(output),
        "datasets": {k: {"license": v.get("license"), "resources_found": v.get("resources_found"),
                         "downloaded": len(v.get("resources", []))}
                     for k, v in report["datasets"].items()},
        "soil": report["soil_license"],
        "failures": report["failures"],
        "validation_status": report["validation_status"],
    }, ensure_ascii=False, indent=2))
    if not any(ds.get("resources") for ds in report["datasets"].values()):
        raise SystemExit("No licensed IFN field resources downloaded")


if __name__ == "__main__":
    main()
