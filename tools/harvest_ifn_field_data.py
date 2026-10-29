#!/usr/bin/env python3
"""Harvest licensed, plot-level SFB IFN biophysical records for audit and pairing.

This collector archives source workbooks and emits a schema/coverage manifest. It
never turns catalog rows or field data into a validation pass; SAR pairing,
spatial holdout, and component-specific error analysis remain separate steps.
"""
from __future__ import annotations

import csv
import hashlib
import io
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
    "dap10": ("/pt_BR/dataset/ifn-dap-10-por-uf_disp-set2025", "cc_by"),
    "fallen_wood": ("/pt_BR/dataset/ifn-madeira-caida-por-uf_disp-set2025", "cc_by"),
    "litter_corrected": ("/pt_BR/dataset/ifn-serapilheira-por-uf_disp-set2025", "cc_by"),
    # SFB's CKAN record has no license; inspect its metadata but do not download.
    "necromass": ("/dataset/necromassa-por-uf-ifn", "blocked_no_license"),
}
# Official SFB/IFN 2026 panel: these are actual CKAN resource downloads
# from a dataset explicitly licensed Creative Commons Attribution.
# Plot-level identifiers do NOT imply publicly available geocoordinates.
PANEL_DATASET_PAGE = BASE + "/pt_BR/dataset/painel-de-biomassa-e-carbono"
PANEL_RESOURCES = {
    "panel_biomass": (
        "06203c8a-c13e-498c-8804-f32e991c17ba",
        "dadosabertos_dadosbiomassa_painelbiomassacarbono_snif_fonte_ifn_sfb.csv",
    ),
    "panel_dead_trees": (
        "979419d0-96b2-411f-baec-3759c61f09ce",
        "dadosabertos_dadosarvoresmortas_painelbiomassacarbono_snif_fonte_ifn_sfb.csv",
    ),
    "panel_necromass": (
        "f5902766-14e3-46b8-bdc4-99bc09693161",
        "dadosabertos_dadosnecromassa_painelbiomassacarbono_snif_fonte_ifn_sfb.csv",
    ),
    "panel_equations": (
        "a209cbbe-1dd6-4217-8662-658ed1e7e1e6",
        "dadosabertos_equacoes_painelbiomassacarbono_snif_fonte_ifn_sfb.csv",
    ),
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


def _summarize_rows(rows, headers, *, encoding=None, delimiter=None):
    normalized = {norm(name): i for i, name in enumerate(headers) if name}
    def idx(*names):
        return next((normalized[norm(name)] for name in names if norm(name) in normalized), None)
    ua_i = idx("UA", "UNIDADE_AMOSTRAL", "UNIDADE_DE_AMOSTRAGEM")
    bio_i = idx("BIOMA", "NM_BIOMA")
    lat_i = idx("LAT_PC", "LATITUDE", "LAT")
    lon_i = idx("LON_PC", "LONGITUDE", "LON", "LONG")
    unique_ua = {}
    coordinate_ua = {}
    row_counts = {}
    row_count = 0
    for row in rows:
        values = list(row)
        if not any(v not in (None, "") for v in values):
            continue
        row_count += 1
        def val(i):
            return values[i] if i is not None and i < len(values) else None
        biome = str(val(bio_i) or "").strip()
        ua = str(val(ua_i) or "").strip()
        if biome:
            row_counts[biome] = row_counts.get(biome, 0) + 1
        if biome and ua:
            unique_ua.setdefault(biome, set()).add(ua)
            try:
                lat = float(str(val(lat_i)).replace(",", "."))
                lon = float(str(val(lon_i)).replace(",", "."))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    coordinate_ua.setdefault(biome, set()).add(ua)
            except (TypeError, ValueError):
                pass
    columns = [norm(h) for h in headers]
    return {
        "headers": [str(h) for h in headers],
        "normalized_headers": sorted(h for h in columns if h),
        "nonempty_data_rows": row_count,
        "unique_ua_by_biome": {k: len(v) for k, v in sorted(unique_ua.items())},
        "unique_ua_with_coordinates_by_biome": {k: len(v) for k, v in sorted(coordinate_ua.items())},
        "observation_rows_by_biome": dict(sorted(row_counts.items())),
        "encoding": encoding,
        "delimiter": delimiter,
    }


def inspect_workbook(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    summaries = []
    totals = {}
    for ws in wb.worksheets:
        iterator = iter(ws.iter_rows(values_only=True))
        headers = None
        header_index = None
        preview = []
        for idx, raw in enumerate(iterator):
            values = [str(v).strip() if v is not None else "" for v in raw]
            if not any(values):
                continue
            if len(preview) < 3:
                preview.append(values[:30])
            tokens = {norm(v) for v in values if v}
            has_plot_id = bool(tokens & {"UA", "UNIDADE_AMOSTRAL", "UNIDADE_DE_AMOSTRAGEM"})
            has_biome = bool(tokens & {"BIOMA", "NM_BIOMA"})
            has_coords = bool(tokens & {"LON_PC", "LAT_PC", "LONGITUDE", "LATITUDE"})
            if idx < 30 and (has_plot_id or has_biome or has_coords):
                headers = values
                header_index = idx + 1
                break
        if headers is None:
            summaries.append({"sheet": ws.title, "header_row_1based": None,
                              "headers": [], "preview": preview})
            continue
        result = _summarize_rows(iterator, headers)
        for biome, count in result["unique_ua_by_biome"].items():
            totals.setdefault(biome, set()).update((ws.title, str(i)) for i in range(count))
        summaries.append({"sheet": ws.title, "header_row_1based": header_index,
                          "preview": preview, **result})
    wb.close()
    # Sheets within a workbook can overlap; report sums only as an upper-bound count.
    ua_by_biome = {}
    coordinate_ua_by_biome = {}
    row_by_biome = {}
    for sheet in summaries:
        for biome, value in sheet.get("unique_ua_by_biome", {}).items():
            ua_by_biome[biome] = ua_by_biome.get(biome, 0) + value
        for biome, value in sheet.get("unique_ua_with_coordinates_by_biome", {}).items():
            coordinate_ua_by_biome[biome] = coordinate_ua_by_biome.get(biome, 0) + value
        for biome, value in sheet.get("observation_rows_by_biome", {}).items():
            row_by_biome[biome] = row_by_biome.get(biome, 0) + value
    return {"sheets": summaries, "unique_ua_by_biome": ua_by_biome,
            "unique_ua_with_coordinates_by_biome": coordinate_ua_by_biome,
            "observation_rows_by_biome": row_by_biome}


def inspect_csv(body):
    try:
        text = body.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        text = body.decode("cp1252")
        encoding = "cp1252"
    sample = text[:8192]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\\t|").delimiter
    except csv.Error:
        delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    normalized = {norm(name): name for name in headers if name}
    ua_name = next((normalized[norm(x)] for x in ("UA", "Unidade amostral") if norm(x) in normalized), None)
    bio_name = next((normalized[norm(x)] for x in ("bioma", "nm_bioma") if norm(x) in normalized), None)
    lat_name = next((normalized[norm(x)] for x in ("lat_pc", "latitude") if norm(x) in normalized), None)
    lon_name = next((normalized[norm(x)] for x in ("lon_pc", "longitude") if norm(x) in normalized), None)
    ua_by_biome, coords_by_biome, rows_by_biome = {}, {}, {}
    row_count = 0
    for record in reader:
        row_count += 1
        biome = str(record.get(bio_name) or "").strip() if bio_name else ""
        ua = str(record.get(ua_name) or "").strip() if ua_name else ""
        if biome:
            rows_by_biome[biome] = rows_by_biome.get(biome, 0) + 1
        if biome and ua:
            ua_by_biome.setdefault(biome, set()).add(ua)
            try:
                lat = float(str(record.get(lat_name)).replace(",", ".")) if lat_name else None
                lon = float(str(record.get(lon_name)).replace(",", ".")) if lon_name else None
                if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
                    coords_by_biome.setdefault(biome, set()).add(ua)
            except (TypeError, ValueError):
                pass
    return {
        "headers": headers, "normalized_headers": sorted(norm(x) for x in headers if x),
        "nonempty_data_rows": row_count,
        "unique_ua_by_biome": {k: len(v) for k, v in sorted(ua_by_biome.items())},
        "unique_ua_with_coordinates_by_biome": {k: len(v) for k, v in sorted(coords_by_biome.items())},
        "observation_rows_by_biome": dict(sorted(rows_by_biome.items())),
        "encoding": encoding, "delimiter": delimiter,
    }

def harvest_sfb_2026_panel(session, report):
    """Download explicitly licensed SFB panel CSVs with provenance and schema audits.

    Dataset-level access is verified before download. Records are only potential
    calibration/validation inputs and are never approved as plot-pixel pairs
    without independent locations and true field measurements.
    """
    try:
        response = session.get(PANEL_DATASET_PAGE, timeout=45)
        response.raise_for_status()
        license_text = find_license(response.text)
        if not re.search(r"Creative Commons.{0,100}(?:Atribui[cç][aã]o|Attribution)",
                         response.text, re.I):
            raise RuntimeError("official SFB panel dataset CC BY license not confirmed")
    except Exception as exc:
        report["failures"].append(f"sfb_2026_panel: license/source verification failed: {type(exc).__name__}: {exc}")
        return
    for label, (resource_id, filename) in PANEL_RESOURCES.items():
        url = (BASE + "/dataset/2d579a3b-29f7-41af-b35c-8fb8f51ef819/"
               + "resource/" + resource_id + "/download/" + filename)
        entry = {"dataset_page": PANEL_DATASET_PAGE, "license": license_text,
                 "license_policy": "cc_by", "status": "not_downloaded",
                 "resources_found": 1, "resources": []}
        report["datasets"][label] = entry
        try:
            received = session.get(url, timeout=120)
            received.raise_for_status()
            body = received.content
            if not body or len(body) > 100_000_000:
                raise RuntimeError(f"invalid resource size {len(body)} bytes")
            if body[:50].lower().startswith(b"<!doctype html") or body[:5].lower() == b"<html":
                raise RuntimeError("unexpected HTML content instead of source CSV")
            output = OUT / label / filename
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(body)
            entry["resources"].append({
                "filename": filename, "source_url": url, "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                **inspect_csv(body),
            })
            entry["status"] = "harvested_not_validated"
        except Exception as exc:
            entry["status"] = "access_or_schema_error"
            report["failures"].append(f"{label}: {type(exc).__name__}: {exc}")


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
    for key, (route, license_policy) in DATASETS.items():
        page_url = urljoin(BASE, route)
        try:
            response = session.get(page_url, timeout=45)
            response.raise_for_status()
            page = response.text
            license_text = find_license(page)
            licensed = bool(re.search(r"Creative Commons.{0,100}(?:Atribui[cç][aã]o|Attribution)", page, re.I))
            if license_policy == "blocked_no_license":
                report["datasets"][key] = {
                    "dataset_page": page_url, "license": license_text,
                    "status": "not_downloaded_license_not_provided",
                    "resources_found": 0, "resources": [],
                }
                continue
            if license_policy == "cc_by" and not licensed:
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
                      "license_policy": license_policy, "status": "licensed_harvest",
                      "resources_found": len(links), "resources": []}
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
                        record.update(inspect_csv(body))
                    result["resources"].append(record)
                except Exception as exc:
                    report["failures"].append(f"{key}/{filename}: {type(exc).__name__}: {exc}")
            report["datasets"][key] = result
        except Exception as exc:
            report["datasets"][key] = {"dataset_page": page_url, "license": "unknown",
                                       "resources_found": 0, "resources": []}
            report["failures"].append(f"{key}: {type(exc).__name__}: {exc}")
    # National panel samples supplement, never replace, fitophysiognomy-specific IFN validation.
    harvest_sfb_2026_panel(session, report)
    report["unique_ua_by_dataset_and_biome"] = {}
    for key, dataset in report["datasets"].items():
        counts = {}
        for resource in dataset.get("resources", []):
            for label, value in resource.get("unique_ua_by_biome", {}).items():
                counts[label] = counts.get(label, 0) + value
        report["unique_ua_by_dataset_and_biome"][key] = counts
    report["validation_status"] = "harvested_not_validated"
    output = OUT / "ifn_field_harvest_manifest.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": str(output),
        "datasets": {k: {"license": v.get("license"), "status": v.get("status"),
                         "resources_found": v.get("resources_found"),
                         "downloaded": len(v.get("resources", [])),
                         "unique_ua_by_biome": {b:sum(r.get("unique_ua_by_biome",{}).get(b,0) for r in v.get("resources",[]))
                                                 for b in ("Amazônia","Caatinga","Cerrado","Mata Atlântica","Pantanal")}}
                     for k, v in report["datasets"].items()},
        "soil": report["soil_license"],
        "failures": report["failures"],
        "validation_status": report["validation_status"],
    }, ensure_ascii=False, indent=2))
    if not any(ds.get("resources") for ds in report["datasets"].values()):
        raise SystemExit("No licensed IFN field resources downloaded")


if __name__ == "__main__":
    main()
