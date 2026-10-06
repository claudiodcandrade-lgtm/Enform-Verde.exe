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
     "description": "IFN/SFB e catálogos públicos oficiais; usar somente no nível espacial e taxonômico que os dados realmente sustentam."},
    {"rank": 4, "label": "licenciamento_publico_complementar",
     "description": "Registros abertos de processos Sinaflor/PNLA; funcionam como catálogo de oportunidades, não como observação de inventário por si só."},
    {"rank": 5, "label": "inventario_privado_de_licenciamento",
     "description": "Último recurso; somente com acesso autorizado, compatibilidade espacial/fitofisionômica e margem de erro publicada no estudo."},
]

SEARCH_TERMS = (
    "Sinaflor PMFS",
    "Sinaflor POA",
    "inventário florestal plano de manejo",
)
RELEVANT = re.compile(
    r"sinaflor|plano.{0,8}manejo|pmfs|poa|invent.rio florestal", re.I
)
SUPPORTED_EXTENSIONS = {
    ".csv", ".json", ".xml", ".xlsx", ".xls", ".pdf", ".zip",
    ".geojson", ".gpkg", ".shp",
}
DEFAULT_MAX_RESOURCE_BYTES = 250 * 1024 * 1024


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


def harvest_sinaflor(
    destination: str | Path,
    *,
    max_resource_bytes: int = DEFAULT_MAX_RESOURCE_BYTES,
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
                "source_hierarchy_rank": 4,
                "source_hierarchy_label": "licenciamento_publico_complementar",
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
            if not url.startswith("https://"):
                row["download_status"] = "bloqueado_url_insegura"
                failures.append({"resource": rid, "error": "URL não HTTPS"})
                entries.append(row)
                continue
            declared_size = resource.get("size")
            if declared_size and int(declared_size) > max_resource_bytes:
                row["download_status"] = "excede_limite_de_tamanho"
                row["reason"] = f"Recurso acima do limite atual de {max_resource_bytes} bytes."
                entries.append(row)
                continue
            filename = _safe_filename(str(resource.get("name") or rid)) + ext
            target = root / slug / f"{_safe_filename(rid)}_{filename}"
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
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
                            if size > max_resource_bytes:
                                raise ValueError(f"Recurso excedeu limite durante download: {size} bytes")
                            output.write(chunk)
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
        "pnla": {"portal": PNLA_PORTAL, "help": PNLA_HELP, "scope": PNLA_PUBLIC_SCOPE},
        "priority_order": [
            "1: tabelas abertas de parcela georreferenciada com DAP/estrutura",
            "2: tabelas abertas de parcela sem coordenada confirmada",
            "3: inventários já totalizados com classe, n e erro estatístico verificáveis",
            "4: registros de processo e documentos ainda não extraídos/validados",
        ],
        "source_hierarchy": SOURCE_HIERARCHY,
        "private_licensing_rule": (
            "Último nível: somente arquivos obtidos por acesso autorizado e com margem de erro publicada, "
            "classe/domínio compatíveis e unidades amostrais independentes. Nunca entram automaticamente "
            "em calibração SAR."
        ),
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
