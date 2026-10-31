#!/usr/bin/env python3
"""Materialize official IBGE PAM microregion yield, production and area data.

The output is a long-form, gzipped CSV with one row per product, year,
microregion and SIDRA variable. Suppressed observations remain explicit and
are never converted to zero. The script is deterministic apart from the
retrieval timestamp recorded in the sidecar metadata.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "pam_microregion_yield_2015_2024.csv.gz"
META = ROOT / "data" / "pam_microregion_yield_2015_2024.metadata.json"
BASE = "https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112,214,216/p/2015-2024/c782/{}"
VARIABLES = {"112": "Rendimento médio da produção", "214": "Quantidade produzida", "216": "Área colhida"}
PRODUCTS = {
    "arroz_grao": ("Arroz (em casca)", "40102"),
    "cafe_total": ("Café (em grão)", "40139"),
    "cana_acucar": ("Cana-de-açúcar", "40106"),
    "feijao_grao": ("Feijão (em grão)", "40112"),
    "laranja": ("Laranja", "40151"),
    "milho_grao": ("Milho (em grão)", "40122"),
    "soja_grao": ("Soja (em grão)", "40124"),
    "sorgo_grao": ("Sorgo (em grão)", "40125"),
}
FIELDS = ["product_key", "product_name", "product_code", "year", "territory_code",
          "territory_name", "variable_code", "variable_name", "unit_code", "unit_name",
          "value_original", "value_numeric", "observation_status", "source_url",
          "retrieved_at_utc"]
SUPPRESSED = {"", "..", "...", "-", "X"}


def fetch_product(key: str, product: tuple[str, str], attempts: int = 4) -> tuple[str, str, list[dict]]:
    name, code = product
    url = BASE.format(quote(code, safe=""))
    last_error = None
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "Enform-Verde-PAM-materializer/1.0"})
            with urlopen(req, timeout=90) as response:
                payload = json.load(response)
            if not isinstance(payload, list) or not payload or "D1C" not in payload[0]:
                raise ValueError(f"Unexpected SIDRA schema for {key}")
            records = []
            for raw in payload[1:]:
                original = str(raw.get("V", "")).strip()
                try:
                    numeric = float(original.replace(",", ".")) if original not in SUPPRESSED else None
                except ValueError:
                    numeric = None
                status = "suppressed_or_missing" if original in SUPPRESSED else ("numeric" if numeric is not None else "unparsed")
                records.append({
                    "product_key": key, "product_name": name, "product_code": code,
                    "year": raw.get("D3C", ""), "territory_code": raw.get("D1C", ""),
                    "territory_name": raw.get("D1N", ""), "variable_code": raw.get("D2C", ""),
                    "variable_name": raw.get("D2N", ""), "unit_code": raw.get("MC", ""),
                    "unit_name": raw.get("MN", ""), "value_original": original,
                    "value_numeric": "" if numeric is None else format(numeric, ".15g"),
                    "observation_status": status, "source_url": url,
                })
            return key, url, records
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"SIDRA request failed for {key}: {last_error}")


def main() -> None:
    retrieved = datetime.now(timezone.utc).isoformat()
    by_key = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_product, key, value): key for key, value in PRODUCTS.items()}
        for future in as_completed(futures):
            key, url, rows = future.result()
            by_key[key] = {"url": url, "rows": rows}
    records = []
    product_metadata = {}
    for key in PRODUCTS:
        item = by_key[key]
        rows = item["rows"]
        for row in rows:
            row["retrieved_at_utc"] = retrieved
        seen = {(r["territory_code"], r["year"], r["variable_code"]) for r in rows}
        expected_variables = set(VARIABLES)
        if not rows or len(seen) != len(rows):
            raise ValueError(f"Empty or duplicate SIDRA cells for {key}")
        if {r["variable_code"] for r in rows} != expected_variables:
            raise ValueError(f"Unexpected variables in SIDRA response for {key}")
        cells = {(r["territory_code"], r["year"]): set() for r in rows}
        for row in rows:
            cells[(row["territory_code"], row["year"])].add(row["variable_code"])
        if any(values != expected_variables for values in cells.values()):
            raise ValueError(f"Incomplete yield/production/area triplets for {key}")
        years = sorted({r["year"] for r in rows})
        territories = sorted({r["territory_code"] for r in rows})
        if years != [str(y) for y in range(2015, 2025)]:
            raise ValueError(f"SIDRA year coverage incomplete for {key}: {years}")
        counts = {var: sum(r["variable_code"] == var for r in rows) for var in expected_variables}
        cells_by_key = {}
        for row in rows:
            cells_by_key.setdefault((row["territory_code"], row["year"]), {})[row["variable_code"]] = row
        relative_errors = []
        reconciled = 0
        for values in cells_by_key.values():
            raw_yield = values["112"]["value_numeric"]
            raw_production = values["214"]["value_numeric"]
            raw_area = values["216"]["value_numeric"]
            if not raw_yield or not raw_production or not raw_area:
                continue
            published = float(raw_yield)
            area_implied = float(raw_production) * 1000.0 / float(raw_area) if float(raw_area) > 0 else math.nan
            if published > 0 and math.isfinite(area_implied):
                reconciled += 1
                relative_errors.append(abs(published-area_implied)/published)
        product_metadata[key] = {"product_name": PRODUCTS[key][0], "product_code": PRODUCTS[key][1],
                                 "source_url": item["url"], "rows": len(rows),
                                 "microregions": len(territories), "years": years,
                                 "rows_by_variable": counts,
                                 "yield_reconciliation": {
                                     "numeric_triplets": reconciled,
                                     "median_absolute_relative_difference": (
                                         sorted(relative_errors)[len(relative_errors)//2] if relative_errors else None),
                                     "within_2_percent": sum(e <= 0.02 for e in relative_errors),
                                     "method": "published kg/ha compared with production tonnes × 1000 / harvested area ha; diagnostic only"},
                                 "suppressed_or_missing_by_variable": {
                                     var: sum(r["variable_code"] == var and r["observation_status"] != "numeric" for r in rows)
                                     for var in expected_variables}}
        records.extend(rows)
    records.sort(key=lambda r: (r["product_code"], r["territory_code"], r["year"], r["variable_code"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    with OUT.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            gz.write(buffer.getvalue().encode("utf-8"))
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    metadata = {"source_agency": "IBGE", "source_product": "Produção Agrícola Municipal (PAM)",
                "sidra_table": "5457", "territorial_level": "N9 — Microrregião Geográfica (classificação antiga)",
                "variables": VARIABLES, "period": [2015, 2024], "retrieved_at_utc": retrieved,
                "license": "IBGE public statistics; verify current IBGE terms before redistribution in commercial products",
                "output": OUT.name, "sha256": digest, "row_count": len(records),
                "products": product_metadata,
                "quality_rules": ["Suppressed and missing SIDRA markers are retained as nonnumeric, never zero.",
                                  "Production and harvested area remain separate; yield reconciliation must use same product, year and territory.",
                                  "N9 is the pre-2017 microregion geography; do not join to later municipal boundaries without a documented crosswalk."],
                "reconciliation_note": "For numeric production and area, compare published kg/ha yield with (production tonnes × 1000) / harvested area hectares; keep official yield and discrepancy separately."}
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"csv": str(OUT), "rows": len(records), "sha256": digest,
                      "products": {k: {"rows": v["rows"], "microregions": v["microregions"]}
                                   for k, v in product_metadata.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
