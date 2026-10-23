"""Discover and archive public Sinaflor inventory/management-plan resources.

PNLA is treated as a federated discovery portal. Its public service documents
process metadata, not a stable bulk API for all agency attachments. The module
therefore records the PNLA search route and ingests openly downloadable
Sinaflor datasets without scraping authentication-only interfaces.
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # Classification helpers remain usable without network extras.
    requests = None  # type: ignore[assignment]


def _new_session():
    if requests is None:
        raise RuntimeError("A biblioteca requests é necessária para consultar os catálogos online.")
    return requests.Session()

SINAFLOR_CKAN = "https://dadosabertos.ibama.gov.br/api/3/action"
SINAFLOR_PORTAL = "https://dadosabertos.ibama.gov.br/"
SINAFLOR_OFFICIAL_PAGE = (
    "https://www.gov.br/ibama/pt-br/assuntos/biodiversidade/flora-e-madeira/"
    "sistema-nacional-de-controle-da-origem-dos-produtos-florestais-sinaflor/"
    "sistema-nacional-de-controle-da-origem-dos-produtos-florestais-sinaflor"
)
REDAPE_BASE = "https://www.redape.dados.embrapa.br"
REDAPE_SEARCH_API = f"{REDAPE_BASE}/api/search"
REDAPE_DATASET_API = f"{REDAPE_BASE}/api/datasets/:persistentId/"
RESEARCH_TERMS = (
    '"inventário florestal"',
    '"parcelas permanentes" floresta',
    '"estrutura florestal" biomassa',
    '"biomassa" inventário',
    '"fitossociologia" floresta parcelas',
    '"manejo florestal" inventário parcelas',
)
INSTITUTIONAL_PORTALS = [
    {"institution": "Embrapa — REDAPE", "url": "https://www.redape.dados.embrapa.br/",
     "machine_route": REDAPE_SEARCH_API, "method": "Dataverse Search API"},
    {"institution": "Embrapa — Alice", "url": "https://www.alice.cnptia.embrapa.br/alice/",
     "machine_route": "https://www.alice.cnptia.embrapa.br/oai/request",
     "method": "OAI-PMH metadata; public records/downloads subject to repository license"},
    {"institution": "Embrapa — Infoteca-e", "url": "https://www.infoteca.cnptia.embrapa.br/",
     "machine_route": "https://www.infoteca.cnptia.embrapa.br/oai/request",
     "method": "OAI-PMH metadata; publications and technical reports"},
    {"institution": "INPA — Repositório Institucional", "url": "https://repositorio.inpa.gov.br/",
     "machine_route": "", "method": "Public institutional search; harvest route to be confirmed"},
    {"institution": "Museu Paraense Emílio Goeldi — Repositório", "url": "https://repositorio.museu-goeldi.br/home",
     "machine_route": "", "method": "Public institutional search; harvest route to be confirmed"},
    {"institution": "UFRA — RIUFRA", "url": "https://www.repositorio.ufra.edu.br/jspui/",
     "machine_route": "", "method": "Public institutional search; harvest route to be confirmed"},
    {"institution": "UFV — Locus", "url": "https://locus.ufv.br/",
     "machine_route": "", "method": "Public DSpace search; institutional inventory/forestry collections"},
    {"institution": "UFLA — RIUFLA", "url": "https://repositorio.ufla.br/",
     "machine_route": "", "method": "Public DSpace search; institutional inventory/forestry collections"},
    {"institution": "UFT — RIUFT", "url": "https://repositorio.uft.edu.br/?locale=pt_BR",
     "machine_route": "", "method": "Public institutional search; harvest route to be confirmed"},
    {"institution": "UFPR — Acervo Digital / BDC", "url": "https://acervodigital.ufpr.br/",
     "machine_route": "", "method": "Institutional repository and research-data catalog; access/search availability varies"},
    {"institution": "UnB — Repositório Institucional", "url": "https://repositorio.unb.br/",
     "machine_route": "", "method": "Public institutional search; harvest route to be confirmed"},
]
PNLA_PORTAL = "https://pnla.mma.gov.br/"
PNLA_HELP = "https://pnla.mma.gov.br/como-funciona-o-pnla"
PNLA_PUBLIC_SCOPE = (
    "O PNLA permite consulta pública de metadados de processos; documentos e "
    "anexos dependem da publicação pelo órgão licenciador. Não há API nacional "
    "de download em lote documentada pelo serviço oficial."
)

# Selection hierarchy is applied before any estimate or calibration. Dataset
# discovery rank and component-data quality are independent dimensions.
SOURCE_HIERARCHY = [
    {"rank": 1, "label": "institucional_parcela_aberta",
     "description": "Embrapa, INPA, Museu Goeldi, universidades públicas e repositórios científicos; microdados georreferenciados de parcelas."},
    {"rank": 2, "label": "institucional_totalizado_com_erro",
     "description": "Inventário publicado por instituição reconhecida, já totalizado, com classe, unidade, n e margem de erro verificáveis."},
    {"rank": 3, "label": "base_publica_oficial",
     "description": "Mesmo nível de origem institucional para IFN/SFB e dados públicos oficiais do Sinaflor; distinguir inventário medido de registro de autorização/processo."},
    {"rank": 4, "label": "metadado_publico_de_licenciamento",
     "description": "PNLA e metadados de processos: ajudam a localizar estudos/documentos, mas não são por si só observações de inventário."},
    {"rank": 5, "label": "inventario_privado_de_licenciamento",
     "description": "Último recurso; somente com acesso autorizado, compatibilidade espacial/fitofisionômica e margem de erro publicada no estudo."},
]

SEARCH_TERMS = (
    "Sinaflor",
    "plano de manejo florestal",
    "inventário florestal",
)
RELEVANT = re.compile(
    r"sinaflor|plano.{0,8}manejo|pmfs|poa|invent.rio florestal", re.I
)
SUPPORTED_EXTENSIONS = {
    ".csv", ".json", ".xml", ".xlsx", ".xls", ".pdf", ".zip",
    ".geojson", ".gpkg", ".shp",
}
DEFAULT_MAX_RESOURCE_BYTES = 250 * 1024 * 1024
DEFAULT_TOTAL_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024


def _safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return (value or "recurso")[:150]


def _extension(resource: dict[str, Any]) -> str:
    name = str(resource.get("name") or resource.get("url") or "")
    suffix = Path(urlparse(name).path).suffix.lower()
    return suffix or "." + str(resource.get("format") or "").lower().lstrip(".")


def _ckan_action(session: requests.Session, action: str, **params: Any) -> dict[str, Any]:
    response = session.get(f"{SINAFLOR_CKAN}/{action}", params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"Falha na API CKAN ({action}): {payload.get('error')}")
    return payload["result"]


def discover_redape_datasets(session: requests.Session | None = None) -> list[dict[str, Any]]:
    """Search Embrapa's public Dataverse for inventory/plot research datasets."""
    session = session or _new_session()
    session.headers.setdefault("User-Agent", "Enform-Verde-Inventario/1.0")
    records: dict[str, dict[str, Any]] = {}
    for term in RESEARCH_TERMS:
        response = session.get(
            REDAPE_SEARCH_API,
            params={"q": term, "type": "dataset", "per_page": 100},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {})
        for item in data.get("items", []):
            persistent_id = str(item.get("global_id") or item.get("identifier") or item.get("id") or "")
            if persistent_id:
                records[persistent_id] = item
        time.sleep(0.05)
    return sorted(records.values(), key=lambda x: str(x.get("name", "")).casefold())


def harvest_redape(
    destination: str | Path,
    *,
    max_resource_bytes: int = DEFAULT_MAX_RESOURCE_BYTES,
    total_download_bytes: int = DEFAULT_TOTAL_DOWNLOAD_BYTES,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download public Embrapa REDAPE dataset files within a bounded budget."""
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    session = session or _new_session()
    session.headers.setdefault("User-Agent", "Enform-Verde-Inventario/1.0")
    search_items = discover_redape_datasets(session)
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    downloaded_total = 0
    for item in search_items:
        persistent_id = str(item.get("global_id") or item.get("identifier") or "")
        item_name = str(item.get("name") or persistent_id or "dataset")
        row_base = {
            "source": "Embrapa / REDAPE — dados de pesquisa",
            "source_hierarchy_rank": 1,
            "source_hierarchy_label": "institucional_parcela_aberta",
            "dataset": item_name,
            "persistent_id": persistent_id,
            "dataset_url": item.get("url") or f"{REDAPE_BASE}/dataset.xhtml?persistentId={persistent_id}",
            "download_status": "metadado_encontrado",
            "evidence_tier": "registro_institucional_para_triagem",
            "priority": 1,
            "usable_for_calibration": False,
            "reason": "Fonte institucional prioritária; arquivos e desenho amostral ainda exigem auditoria.",
        }
        if not persistent_id:
            entries.append(row_base)
            continue
        try:
            response = session.get(
                REDAPE_DATASET_API,
                params={"persistentId": persistent_id},
                timeout=60,
            )
            response.raise_for_status()
            detail = response.json().get("data", {})
            version = detail.get("latestVersion", {})
            files = version.get("files", [])
        except Exception as exc:
            row = dict(row_base, download_status="falha_metadados",
                       reason=f"{type(exc).__name__}: {exc}")
            entries.append(row)
            failures.append({"dataset": persistent_id, "error": row["reason"]})
            continue
        if not files:
            entries.append(row_base)
            continue
        for file_item in files:
            data_file = file_item.get("dataFile", file_item)
            file_id = str(data_file.get("id") or "")
            label = str(data_file.get("filename") or data_file.get("label") or file_id or "arquivo")
            size = int(data_file.get("filesize") or data_file.get("size") or 0)
            entry = dict(row_base)
            entry.update({"resource_id": file_id, "resource_name": label, "size_bytes": size,
                          "resource_url": f"{REDAPE_BASE}/api/access/datafile/{file_id}" if file_id else "",
                          "format": Path(label).suffix.lower().lstrip(".")})
            if not file_id:
                entry.update({"download_status": "link_de_arquivo_ausente",
                              "reason": "Metadado Dataverse não informou ID de arquivo."})
                entries.append(entry)
                continue
            if size and size > max_resource_bytes:
                entry.update({"download_status": "excede_limite_de_arquivo",
                              "reason": f"Arquivo acima de {max_resource_bytes} bytes; manter link/metadado."})
                entries.append(entry)
                continue
            if size and downloaded_total + size > total_download_bytes:
                entry.update({"download_status": "excede_limite_total",
                              "reason": f"Limite total de coleta ({total_download_bytes} bytes) alcançado."})
                entries.append(entry)
                continue
            ext = Path(label).suffix.lower() or ".dat"
            target = root / _safe_filename(persistent_id) / f"{_safe_filename(file_id)}_{_safe_filename(Path(label).name)}"
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with session.get(entry["resource_url"], stream=True, timeout=(30, 180)) as response:
                    response.raise_for_status()
                    received = 0
                    with target.open("wb") as output:
                        for chunk in response.iter_content(1024 * 1024):
                            if not chunk:
                                continue
                            received += len(chunk)
                            if received > max_resource_bytes or downloaded_total + received > total_download_bytes:
                                raise ValueError("Limite de tamanho da coleta excedido.")
                            output.write(chunk)
                downloaded_total += received
                entry.update({"local_path": str(target), "download_status": "baixado",
                              "size_bytes": received, "format": ext.lstrip(".")})
                entry.update(classify_tabular_resource(target))
            except Exception as exc:
                target.unlink(missing_ok=True)
                entry.update({"download_status": "falha_download",
                              "reason": f"{type(exc).__name__}: {exc}"})
                failures.append({"resource": file_id, "error": entry["reason"]})
            entries.append(entry)
    manifest = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "institution": {"name": "Embrapa", "repository": "REDAPE",
                        "search_api": REDAPE_SEARCH_API,
                        "dataset_count": len(search_items),
                        "downloaded_bytes": downloaded_total},
        "resources": entries,
        "download_failures": failures,
        "limitations": [
            "REDAPE é prioritário por ser repositório institucional de dados de pesquisa; relevância de cada resultado precisa ser conferida.",
            "Licença, citação, integridade dos arquivos e condições de reúso devem ser conservadas.",
            "Nenhum arquivo é automaticamente promovido a calibração: verificar parcelas independentes, georreferenciamento, fitofisionomia, época, método e erro.",
        ],
    }
    (root / "manifest_redape_inventarios.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (root / "catalogo_redape_inventarios.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["source_hierarchy_rank", "source_hierarchy_label", "priority", "evidence_tier",
                  "dataset", "persistent_id", "resource_name", "resource_id", "format",
                  "download_status", "size_bytes", "local_path", "dataset_url", "resource_url", "reason"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)
    return manifest


def discover_sinaflor_datasets(session: requests.Session | None = None) -> list[dict[str, Any]]:
    """Return distinct official CKAN datasets matching PMFS/POA/inventory terms."""
    session = session or _new_session()
    session.headers.setdefault("User-Agent", "Enform-Verde-Inventario/1.0")
    found: dict[str, dict[str, Any]] = {}
    for term in SEARCH_TERMS:
        result = _ckan_action(session, "package_search", q=term, rows=100)
        for item in result.get("results", []):
            title = str(item.get("title") or item.get("name") or "")
            notes = str(item.get("notes") or "")
            if RELEVANT.search(title + " " + notes):
                found[str(item.get("id") or item.get("name"))] = item
        time.sleep(0.05)
    detailed = []
    for package_id, summary in found.items():
        package = _ckan_action(session, "package_show", id=package_id)
        detailed.append(package)
    return sorted(detailed, key=lambda p: (str(p.get("title", "")).casefold(), p.get("name", "")))


def classify_tabular_resource(path: str | Path) -> dict[str, Any]:
    """Conservatively rank a CSV as open plots, totalized summary, or lead only."""
    path = Path(path)
    if path.suffix.lower() != ".csv":
        return {
            "evidence_tier": "documento_para_triagem",
            "priority": 3,
            "usable_for_calibration": False,
            "reason": "Documento/arquivo geoespacial requer extração e revisão de schema.",
            "columns": [],
        }
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as stream:
        sample = stream.read(16384)
    if not sample.strip():
        return {"evidence_tier": "vazio", "priority": 4, "usable_for_calibration": False,
                "reason": "CSV vazio.", "columns": []}
    try:
        dialect = csv.Sniffer().sniff(sample[:8192], delimiters=";,\t|")
    except csv.Error:
        dialect = csv.excel
    columns = next(csv.reader([sample.splitlines()[0]], dialect), [])
    norm = {re.sub(r"[^a-z0-9]+", "_", c.casefold()).strip("_") for c in columns}
    plot = bool(norm & {"parcela", "plot", "plot_id", "id_parcela", "unidade_amostral", "ua"})
    dbh = bool(norm & {"dap", "dbh", "dap_cm", "diametro", "diametro_cm", "diameter_cm"})
    coord_x = bool(norm & {"longitude", "lon", "long", "coord_x", "x"})
    coord_y = bool(norm & {"latitude", "lat", "coord_y", "y"})
    inventory = bool(norm & {"inventario", "inventory", "id_inventario", "processo", "numero_processo"})
    summary = bool(norm & {"media", "mean", "media_dap", "area_basal", "g_m2_ha", "volume_total"})
    georef = coord_x and coord_y
    if plot and dbh and georef:
        tier, priority = "parcela_aberta_georreferenciada", 1
        reason = "Há campos de parcela, DAP e coordenadas; validar sistema de referência, unidade e metadados."
        usable = False  # eligibility follows full QA, taxonomy and method audit
    elif plot and dbh:
        tier, priority = "parcela_aberta_sem_georreferenciamento_confirmado", 2
        reason = "Há parcela e DAP, mas faltam coordenadas explícitas; não parear com raster."
        usable = False
    elif summary:
        tier, priority = "inventario_totalizado_candidato", 3
        reason = "Há campos agregados; conferir classe, área, n, pesos e variância antes de usar."
        usable = False
    else:
        tier, priority = "registro_ou_documento_para_triagem", 4
        reason = "Não foi reconhecida uma tabela de parcelas ou resumo estatístico utilizável."
        usable = False
    return {"evidence_tier": tier, "priority": priority, "usable_for_calibration": usable,
            "reason": reason, "columns": columns, "georeferenced_fields_detected": georef}


def evaluate_private_licensing_inventory(
    *,
    authorized_access: bool,
    published_margin_of_error: bool,
    class_match: bool,
    spatial_match: bool,
    independent_sample_units: int | None,
) -> dict[str, Any]:
    """Apply the user's last-resort rule to private licensing inventories."""
    checks = {
        "acesso_autorizado": bool(authorized_access),
        "margem_de_erro_publicada": bool(published_margin_of_error),
        "fitofisionomia_compativel": bool(class_match),
        "dominio_espacial_compativel": bool(spatial_match),
        "unidades_amostrais_independentes": bool(independent_sample_units and independent_sample_units >= 2),
    }
    eligible = all(checks.values())
    return {
        "source_hierarchy_rank": 5,
        "source_hierarchy_label": "inventario_privado_de_licenciamento",
        "may_support_estimate": eligible,
        "include_in_sar_calibration": False,
        "checks": checks,
        "decision": (
            "Elegível apenas como referência de último nível, após auditoria da metodologia e transferência."
            if eligible else
            "Não usar numericamente; falta ao menos um requisito obrigatório de acesso, erro publicado, "
            "classe, domínio ou unidades independentes."
        ),
    }


def evaluate_totalized_inventory(
    *,
    recognized_institution: bool,
    published_margin_of_error: bool,
    class_match: bool,
    spatial_match: bool,
    independent_sample_units: int | None,
) -> dict[str, Any]:
    """Require reported sampling error before totalized data can support estimates."""
    checks = {
        "instituicao_reconhecida": bool(recognized_institution),
        "margem_de_erro_publicada": bool(published_margin_of_error),
        "fitofisionomia_compativel": bool(class_match),
        "dominio_espacial_compativel": bool(spatial_match),
        "unidades_amostrais_independentes": bool(independent_sample_units and independent_sample_units >= 2),
    }
    eligible = all(checks.values())
    return {
        "source_hierarchy_rank": 2 if recognized_institution else 5,
        "source_hierarchy_label": (
            "institucional_totalizado_com_erro" if recognized_institution
            else "inventario_privado_de_licenciamento"
        ),
        "may_support_estimate": eligible,
        "include_in_sar_calibration": False,
        "checks": checks,
        "decision": (
            "Elegível como estimativa secundária totalizada após auditoria de unidade, estatística e transferência."
            if eligible else
            "Não usar numericamente; inventário totalizado requer instituição identificada, margem de erro publicada, "
            "classe/domínio compatíveis e unidades independentes."
        ),
    }


def harvest_sinaflor(
    destination: str | Path,
    *,
    max_resource_bytes: int = DEFAULT_MAX_RESOURCE_BYTES,
    total_download_bytes: int = DEFAULT_TOTAL_DOWNLOAD_BYTES,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download all public supported resources from relevant official datasets.

    Returns a manifest that separates raw/plot candidates, totals, and leads.
    Nothing is automatically promoted to SAR training or carbon estimates.
    """
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    session = session or _new_session()
    session.headers.setdefault("User-Agent", "Enform-Verde-Inventario/1.0")
    packages = discover_sinaflor_datasets(session)
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    resource_ids: set[str] = set()
    downloaded_total = 0
    for package in packages:
        slug = _safe_filename(str(package.get("name") or package.get("id")))
        for resource in package.get("resources", []):
            rid = str(resource.get("id") or resource.get("url") or "")
            if not rid or rid in resource_ids:
                continue
            resource_ids.add(rid)
            url = str(resource.get("url") or "")
            ext = _extension(resource)
            row: dict[str, Any] = {
                "source": "IBAMA / Sinaflor — Dados Abertos",
                "source_hierarchy_rank": 3,
                "source_hierarchy_label": "base_publica_oficial",
                "dataset_id": package.get("id"),
                "dataset": package.get("title") or package.get("name"),
                "dataset_url": package.get("url") or f"{SINAFLOR_PORTAL}dataset/{slug}",
                "resource_id": rid,
                "resource_name": resource.get("name"),
                "resource_url": url,
                "format": resource.get("format"),
                "license": package.get("license_title"),
                "modified": resource.get("last_modified") or package.get("metadata_modified"),
                "local_path": "",
                "download_status": "not_attempted",
                "evidence_tier": "registro_ou_documento_para_triagem",
                "priority": 4,
                "usable_for_calibration": False,
                "reason": "Recurso oficial precisa de triagem de conteúdo, domínio e qualidade.",
            }
            if ext not in SUPPORTED_EXTENSIONS:
                row["download_status"] = "formato_nao_arquivado"
                row["reason"] = f"Formato {ext or 'desconhecido'} mantido como link; não baixado."
                entries.append(row)
                continue
            if (not url.startswith("https://")
                    or urlparse(url).hostname not in {"dadosabertos.ibama.gov.br"}):
                row["download_status"] = "bloqueado_url_insegura"
                failures.append({"resource": rid, "error": "URL fora do host oficial HTTPS do catálogo IBAMA"})
                entries.append(row)
                continue
            declared_size = resource.get("size")
            if declared_size and int(declared_size) > max_resource_bytes:
                row["download_status"] = "excede_limite_de_tamanho"
                row["reason"] = f"Recurso acima do limite atual de {max_resource_bytes} bytes."
                entries.append(row)
                continue
            if declared_size and downloaded_total + int(declared_size) > total_download_bytes:
                row["download_status"] = "excede_limite_total"
                row["reason"] = f"Limite total de coleta ({total_download_bytes} bytes) alcançado."
                entries.append(row)
                continue
            filename = _safe_filename(str(resource.get("name") or rid)) + ext
            target = root / slug / f"{_safe_filename(rid)}_{filename}"
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                if target.exists() and target.stat().st_size <= max_resource_bytes:
                    size = target.stat().st_size
                else:
                    with session.get(url, stream=True, timeout=(30, 180)) as response:
                        response.raise_for_status()
                        content_length = int(response.headers.get("Content-Length") or 0)
                        if content_length > max_resource_bytes:
                            raise ValueError(f"Recurso acima do limite: {content_length} bytes")
                        size = 0
                        with target.open("wb") as output:
                            for chunk in response.iter_content(1024 * 1024):
                                if not chunk:
                                    continue
                                size += len(chunk)
                                if size > max_resource_bytes or downloaded_total + size > total_download_bytes:
                                    raise ValueError(f"Limite da coleta excedido: {size} bytes")
                                output.write(chunk)
                    downloaded_total += size
                row.update({"local_path": str(target), "download_status": "baixado", "size_bytes": size})
                row.update(classify_tabular_resource(target))
            except Exception as exc:
                target.unlink(missing_ok=True)
                row["download_status"] = "falha_download"
                row["reason"] = f"{type(exc).__name__}: {exc}"
                failures.append({"resource": rid, "error": row["reason"]})
            entries.append(row)
    entries.sort(key=lambda e: (e.get("priority", 9), str(e.get("dataset", "")), str(e.get("resource_name", ""))))
    manifest = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sinaflor": {"portal": SINAFLOR_PORTAL, "official_info": SINAFLOR_OFFICIAL_PAGE,
                     "api": SINAFLOR_CKAN, "datasets_found": len(packages)},
        "downloaded_bytes": downloaded_total,
        "pnla": {"portal": PNLA_PORTAL, "help": PNLA_HELP, "scope": PNLA_PUBLIC_SCOPE},
        "priority_order": [
            "1: tabelas abertas de parcela georreferenciada com DAP/estrutura",
            "2: tabelas abertas de parcela sem coordenada confirmada",
            "3: inventários já totalizados com classe, n e erro estatístico verificáveis",
            "4: metadados de processo e documentos ainda não extraídos/validados",
        ],
        "source_hierarchy": SOURCE_HIERARCHY,
        "private_licensing_rule": (
            "Último nível: somente arquivos obtidos por acesso autorizado e com margem de erro publicada, "
            "classe/domínio compatíveis e unidades amostrais independentes. Nunca entram automaticamente "
            "em calibração SAR."
        ),
        "institutional_repository_routes": INSTITUTIONAL_PORTALS,
        "limitations": [
            "Registros de autorização/PMFS/POA não são automaticamente observações de inventário.",
            "Nenhum recurso é usado em calibração SAR ou cálculo de carbono sem QA de parcelas, geografia, classe, unidade, desenho amostral e incerteza.",
            "Documentos PNLA/Sinaflor não públicos exigem acesso legítimo pelo órgão/sistema; o conector não contorna autenticação.",
        ],
        "resources": entries,
        "download_failures": failures,
    }
    (root / "manifest_sinaflor_inventarios.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (root / "catalogo_sinaflor_inventarios.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["priority", "evidence_tier", "usable_for_calibration", "dataset", "dataset_id",
                  "resource_name", "resource_id", "format", "download_status", "size_bytes",
                  "local_path", "resource_url", "reason"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)
    return manifest


def pnla_discovery_record() -> dict[str, str]:
    """Stable public discovery links; PNLA is not represented as a bulk file API."""
    return {"portal": PNLA_PORTAL, "help": PNLA_HELP, "scope": PNLA_PUBLIC_SCOPE}
