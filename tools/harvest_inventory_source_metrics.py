"""Count official inventory/licensing source records without retaining PII.

Downloads bounded official CSV/ZIP resources to temporary files, computes
source-level counts, hashes the captured files and writes only aggregate
statistics. It never saves names, CPF/CNPJ, CAR identifiers, or raw rows.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import hashlib
import tempfile
import time
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "national_inventory_source_metrics_v1.json"
MAX_RESOURCE_BYTES = 100 * 1024 * 1024
SOURCES = {
    "SINAFLOR_PMFS_AMAZONIA": {
        "url": "https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/dados/SINAFLOR/pmfs/AmazoniaLegal/pmfsAmazoniaLegal.csv",
        "format": "csv", "dataset_url": "https://dadosabertos.ibama.gov.br/dataset/sinaflor-pmfs-amazonia-legal",
        "last_catalog_update": "2026-07-08",
    },
    "SINAFLOR_VOLUMES_IF100": {
        "url": "https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/dados/SINAFLOR/VolumesExploradosIf100/volumes_explorados_if_100_csv.zip",
        "format": "zip", "dataset_url": "https://dadosabertos.ibama.gov.br/dataset/volumes-explorados-if-100",
        "last_catalog_update": "2026-10-08",
    },
    "IBAMA_LICENSES_FEDERAL": {
        "url": "https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/dados/SISLIC/sislic-licencas.csv",
        "format": "csv", "dataset_url": "https://dadosabertos.ibama.gov.br/dataset/licencas-ambientais-de-atividades-e-empreendimentos-licenciados-pelo-ibama",
        "last_catalog_update": "2026-05-29",
    },
}


def _download(url: str, destination: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Enform-Verde-Inventory-Catalog/1.0"})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as out:
        declared = int(response.headers.get("Content-Length") or 0)
        if declared > MAX_RESOURCE_BYTES:
            raise ValueError(f"Recurso excede o limite de {MAX_RESOURCE_BYTES} bytes")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_RESOURCE_BYTES:
                raise ValueError(f"Recurso excede o limite de {MAX_RESOURCE_BYTES} bytes")
            digest.update(chunk)
            out.write(chunk)
    return digest.hexdigest()


def _rows_csv(stream):
    text = io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace", newline="")
    return csv.DictReader(text, delimiter=";")


def _private_id_hash(value):
    return hashlib.sha256(str(value).strip().encode("utf-8")).hexdigest()


def summarize_pmfs_rows(rows, *, authorization_hashes=None):
    registers, authorizations, ufs, biomes, physiognomies = set(), set(), set(), set(), set()
    with_coordinates = 0
    per_uf = defaultdict(lambda: {"records": set(), "authorizations": set()})
    count = 0
    for row in rows:
        count += 1
        reg, auth, uf = (row.get("NRO_REGISTRO", "").strip(),
                         row.get("NRO_AUTORIZACAO", "").strip(),
                         row.get("UF", "").strip().upper())
        if reg:
            registers.add(reg)
            if uf: per_uf[uf]["records"].add(reg)
        if auth:
            authorizations.add(auth)
            if authorization_hashes is not None: authorization_hashes.add(_private_id_hash(auth))
            if uf: per_uf[uf]["authorizations"].add(auth)
        if uf: ufs.add(uf)
        if row.get("BIOMA", "").strip(): biomes.add(row["BIOMA"].strip())
        if row.get("FITOFISIONOMIA", "").strip(): physiognomies.add(row["FITOFISIONOMIA"].strip())
        if row.get("LATITUDE_EMPREENDIMENTO", "").strip() and row.get("LONGITUDE_EMPREENDIMENTO", "").strip():
            with_coordinates += 1
    return {"source_record_rows": count, "distinct_registry_ids": len(registers),
            "distinct_authorization_ids": len(authorizations), "ufs": sorted(ufs),
            "biomes_reported": sorted(biomes), "physiognomies_reported": sorted(physiognomies),
            "rows_with_enterprise_centroid": with_coordinates,
            "records_by_uf": {uf: {"distinct_registry_ids": len(x["records"]),
                                  "distinct_authorization_ids": len(x["authorizations"])}
                             for uf, x in sorted(per_uf.items())},
            "inventory_count_interpretation": "distinct authorizations/registry identifiers are licensing-plan records, not confirmed independent scientific inventories or plot campaigns"}


def summarize_volume_csvs(csv_files, *, authorization_hashes=None):
    authorizations, registry_ids, ufs, taxa = set(), set(), set(), set()
    per_year = {}
    rows_total = coordinate_rows = tree_number_rows = 0
    for year, stream in csv_files:
        rows_year = 0
        for row in _rows_csv(stream):
            rows_year += 1
            auth = row.get("NRO_AUTORIZACAO", "").strip()
            reg = row.get("NRO_REGISTRO", "").strip()
            if auth: authorizations.add(auth)
            if auth and authorization_hashes is not None: authorization_hashes.add(_private_id_hash(auth))
            if reg: registry_ids.add(reg)
            uf = row.get("UF", "").strip().upper()
            if uf: ufs.add(uf)
            scientific = row.get("NOME_CIENTIFICO", "").strip()
            if scientific and scientific.casefold() != "diversos": taxa.add(scientific)
            if row.get("LATITUDE_ARVORE", "").strip() and row.get("LONGITUDE_ARVORE", "").strip():
                coordinate_rows += 1
            if row.get("NRO_ARVORE_EXPLORADA", "").strip(): tree_number_rows += 1
        per_year[str(year)] = rows_year
        rows_total += rows_year
    return {"source_record_rows": rows_total, "rows_by_year": per_year,
            "distinct_registry_ids": len(registry_ids), "distinct_authorization_ids": len(authorizations),
            "ufs_observed": sorted(ufs), "scientific_names_reported": len(taxa),
            "rows_with_tree_coordinates": coordinate_rows, "rows_with_tree_number": tree_number_rows,
            "inventory_count_interpretation": "unique authorization/registry identifiers in selective exploitation records; not independent random plots or complete ecosystem inventories",
            "ecological_use_limit": "explored-tree/species records are selectively harvested and cannot represent natural stand dominance, basal area or ungrazed species frequency"}


def summarize_license_rows(rows):
    processes, asv_processes = set(), set()
    license_types, typologies = Counter(), Counter()
    total = asv_rows = 0
    for row in rows:
        total += 1
        process = row.get("NUM_PROCESSO_IBAMA", "").strip()
        if process: processes.add(process)
        license_type = row.get("DES_TIPOLICENCA", "").strip()
        typology = row.get("DES_TIPOLOGIA", "").strip()
        if license_type: license_types[license_type] += 1
        if typology: typologies[typology] += 1
        if "supress" in license_type.casefold() and "veget" in license_type.casefold():
            asv_rows += 1
            if process: asv_processes.add(process)
    return {"license_rows": total, "distinct_federal_process_ids": len(processes),
            "asv_license_rows": asv_rows, "distinct_processes_with_asv": len(asv_processes),
            "license_rows_by_type": dict(sorted(license_types.items())),
            "license_rows_by_typology_top20": dict(typologies.most_common(20)),
            "inventory_count_interpretation": "processes/licenses are candidate document locations; the number of published inventory studies must be counted after retrieving and deduplicating environmental studies"}


def collect(output: str | Path = OUTPUT) -> dict:
    result = {"captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "privacy": "Only source-level counts and SHA-256 digests are retained; no names, CPF/CNPJ, CAR IDs, process IDs, or raw rows.",
              "sources": {}}
    with tempfile.TemporaryDirectory(prefix="enform_inventory_") as temp:
        temp = Path(temp)
        paths = {}
        for source_id, cfg in SOURCES.items():
            path = temp / (source_id + (".zip" if cfg["format"] == "zip" else ".csv"))
            sha = _download(cfg["url"], path)
            paths[source_id] = path
            result["sources"][source_id] = {"url": cfg["url"], "dataset_url": cfg["dataset_url"],
                "catalog_last_updated": cfg["last_catalog_update"], "captured_file_sha256": sha,
                "captured_file_bytes": path.stat().st_size}
        pmfs_authorization_hashes=set()
        volume_authorization_hashes=set()
        with paths["SINAFLOR_PMFS_AMAZONIA"].open(encoding="utf-8-sig", newline="") as stream:
            result["sources"]["SINAFLOR_PMFS_AMAZONIA"]["summary"] = summarize_pmfs_rows(
                csv.DictReader(stream, delimiter=";"),authorization_hashes=pmfs_authorization_hashes)
        with zipfile.ZipFile(paths["SINAFLOR_VOLUMES_IF100"]) as archive:
            files = []
            for name in archive.namelist():
                if name.casefold().endswith(".csv"):
                    year = Path(name).stem.rsplit("_", 1)[-1]
                    files.append((year, archive.open(name)))
            try:
                result["sources"]["SINAFLOR_VOLUMES_IF100"]["summary"] = summarize_volume_csvs(
                    files,authorization_hashes=volume_authorization_hashes)
            finally:
                for _, stream in files: stream.close()
        with paths["IBAMA_LICENSES_FEDERAL"].open(encoding="utf-8-sig", newline="") as stream:
            result["sources"]["IBAMA_LICENSES_FEDERAL"]["summary"] = summarize_license_rows(
                csv.DictReader(stream, delimiter=";"))
        result["cross_source_deduplication"]={
            "sinaflor_pmfs_if100_shared_authorization_ids":len(pmfs_authorization_hashes & volume_authorization_hashes),
            "sinaflor_pmfs_if100_union_authorization_ids":len(pmfs_authorization_hashes | volume_authorization_hashes),
            "method":"SHA-256 IDs held only in memory for exact join; raw authorization IDs and hashes are not persisted",
            "interpretation":"union remains count of administrative authorizations, not independent forest inventories"}
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(collect(), ensure_ascii=False, indent=2))
