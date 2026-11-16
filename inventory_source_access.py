"""Hierarchical discovery of Brazilian forest-inventory sources.

The collector searches public machine-readable catalogs and writes a durable
manifest of candidate studies. Discovery metadata never becomes a plot or a
model input by itself. Open records, reports and restricted portals retain
separate access/evidence states for later scientific review.
"""
from __future__ import annotations

import csv
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import requests
except ImportError:  # Offline use can still open the catalog and portal links.
    requests = None

from national_inventory_database import discover_ckan_datasets

ROOT = Path(__file__).resolve().parent
PORTALS = ROOT / "data" / "national_inventory_portals_v1.csv"
SEARCH_TERMS = (
    '"inventário florestal"', 'fitossociologia parcelas',
    'parcelas permanentes floresta', 'estrutura diamétrica floresta',
    'área basal inventário floresta', 'biomassa inventário florestal',
)
MATCH = re.compile(r"invent.rio|fitossoci|parcelas?|floresta|biomassa|diam.tr", re.I)

# Only endpoints declared in the source register or well-known public APIs are
# queried. Other sources remain one-click/manual routes in the same manifest.
MACHINE_SOURCES = {
    "SFB_IFN": {"adapter": "ckan", "tier": 1,
        "queries": ("inventário florestal", "unidades amostrais IFN", "parcelas IFN")},
    "IBAMA_SINAFLOR": {"adapter": "ckan", "tier": 4,
        "queries": ("inventário florestal", "plano de manejo", "PMFS", "POA")},
    "EMBRAPA_REDAPE": {"adapter": "dataverse", "tier": 1,
        "queries": SEARCH_TERMS},
    "EMBRAPA_ALICE": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "EMBRAPA_INFOTECA": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFLA_RIUFLA": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFRRJ_REPOSITORY": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFMS_REPOSITORY": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "UNB_REPOSITORY": {"adapter": "oai", "tier": 1,
        "queries": SEARCH_TERMS},
    "INPA_REPOSITORY": {"adapter": "dspace", "tier": 1,
        "queries": SEARCH_TERMS},
    "MUSEU_GOELDI": {"adapter": "dspace", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFRA_RIUFRA": {"adapter": "dspace", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFV_LOCUS": {"adapter": "dspace", "tier": 1,
        "queries": SEARCH_TERMS},
    "UFPR_ACERVO": {"adapter": "dspace", "tier": 1,
        "queries": SEARCH_TERMS},
    "ZENODO": {"adapter": "zenodo", "tier": 1,
        "queries": SEARCH_TERMS},
}

TIER_LABELS = {
    1: "INSTITUCIONAL_ABERTO_PARCELAS_OU_DADOS_PRIMARIOS",
    2: "INSTITUCIONAL_PUBLICADO_TOTALIZADO_COM_ESTATISTICA",
    3: "INVENTARIO_ANEXO_COM_ACEITE_EXPRESSO_COMPROVADO",
    4: "BASE_OFICIAL_OU_ADMINISTRATIVA_PARA_TRIAGEM",
    5: "PORTAL_LOCALIZADOR_SEM_API_DE_COLETA_CONFIRMADA",
}


def _session(session=None):
    if session is not None:
        return session
    if requests is None:
        raise RuntimeError("requests ausente; instalação necessária para busca online")
    s = requests.Session()
    s.headers.update({"User-Agent": "Enform-Verde-Inventarios/1.0 (catalog harvest)"})
    return s


def _read_portals():
    with PORTALS.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _portal_map():
    return {r["source_id"]: r for r in _read_portals()}


def _source_url(portal):
    return portal.get("api_url") or portal.get("portal_url") or ""


def _is_candidate(text):
    return bool(MATCH.search(text or ""))


def _ckan_source(source_id, portal, cfg, session):
    api = _source_url(portal)
    records = discover_ckan_datasets(api, cfg["queries"], session=session, rows=100, max_pages=20)
    out = []
    for item in records:
        rid = str(item.get("id") or item.get("name") or "")
        if not rid:
            continue
        out.append({"record_id": f"{source_id}:{rid}", "source_id": source_id,
            "title": item.get("title") or item.get("name") or rid,
            "url": item.get("url") or portal.get("portal_url"), "api_record_id": rid,
            "description": item.get("notes") or "", "record_type": "catalog_lead",
            "access_state": "PUBLIC_METADATA_RESOURCE_ACCESS_TO_VERIFY"})
    return out


def _dataverse_source(source_id, portal, cfg, session):
    base = _source_url(portal).rstrip("/")
    rows = {}
    for term in cfg["queries"]:
        response = session.get(base, params={"q": term, "type": "dataset", "per_page": 100}, timeout=(10, 60))
        response.raise_for_status()
        payload = response.json()
        for item in (payload.get("data") or {}).get("items", []):
            rid = str(item.get("global_id") or item.get("identifier") or item.get("id") or "")
            if rid:
                rows[rid] = item
    out = []
    for rid, item in rows.items():
        out.append({"record_id": f"{source_id}:{rid}", "source_id": source_id,
            "title": item.get("name") or rid, "url": item.get("url") or portal.get("portal_url"),
            "api_record_id": rid, "description": item.get("description") or "",
            "record_type": "catalog_lead", "access_state": "PUBLIC_METADATA_RESOURCE_ACCESS_TO_VERIFY"})
    return out


def _oai_source(source_id, portal, cfg, session, *, max_pages=30):
    endpoint = _source_url(portal)
    # First confirm that the repository implements OAI-PMH and advertises DC.
    response = session.get(endpoint, params={"verb": "Identify"}, timeout=(10, 45))
    response.raise_for_status()
    identify = ET.fromstring(response.content)
    errors = identify.findall(".//{*}error")
    if errors:
        raise RuntimeError("endpoint não confirmou OAI-PMH: " + (errors[0].text or errors[0].get("code", "erro")))
    records = {}
    params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
    truncated = False
    for page_no in range(max_pages):
        response = session.get(endpoint, params=params, timeout=(10, 60))
        response.raise_for_status()
        root = ET.fromstring(response.content)
        for record in root.findall(".//{*}record"):
            header = record.find("{*}header")
            metadata = record.find("{*}metadata")
            if header is None or metadata is None or header.get("status") == "deleted":
                continue
            ident = header.findtext("{*}identifier", default="").strip()
            values = {}
            for el in metadata.iter():
                if el.text and el.text.strip():
                    key = el.tag.rsplit("}", 1)[-1].casefold()
                    values.setdefault(key, []).append(el.text.strip())
            title = " ".join(values.get("title", []))
            desc = " ".join(values.get("description", []))
            subject = " ".join(values.get("subject", []))
            haystack = " ".join((title, desc, subject))
            if ident and _is_candidate(haystack):
                link = next((x for x in values.get("identifier", []) if x.startswith("http")), "")
                records[ident] = {"record_id": f"{source_id}:{ident}", "source_id": source_id,
                    "title": title or ident, "url": link or portal.get("portal_url"),
                    "api_record_id": ident, "description": desc[:5000],
                    "subjects": subject[:2000], "record_type": "catalog_lead",
                    "access_state": "PUBLIC_METADATA_FULLTEXT_AND_LICENSE_TO_VERIFY"}
        token = root.findtext(".//{*}resumptionToken", default="").strip()
        if not token:
            break
        if page_no + 1 >= max_pages:
            truncated = True
            break
        params = {"verb": "ListRecords", "resumptionToken": token}
    rows = list(records.values())
    for row in rows:
        row["harvest_completeness"] = "PARTIAL_PAGE_LIMIT" if truncated else "COMPLETE"
    return rows


def _zenodo_source(source_id, portal, cfg, session):
    out = {}
    endpoint = "https://zenodo.org/api/records"
    for term in cfg["queries"]:
        response = session.get(endpoint, params={"q": term, "type": "dataset", "size": 100}, timeout=(10, 60))
        response.raise_for_status()
        for item in response.json().get("hits", {}).get("hits", []):
            meta = item.get("metadata") or {}
            rid = str(item.get("id") or "")
            if rid:
                out[rid] = {"record_id": f"{source_id}:{rid}", "source_id": source_id,
                    "title": meta.get("title") or rid, "url": item.get("links", {}).get("self_html") or portal.get("portal_url"),
                    "api_record_id": rid, "description": meta.get("description") or "",
                    "doi": meta.get("doi"), "license": (meta.get("license") or {}).get("id"),
                    "record_type": "catalog_lead", "access_state": "PUBLIC_DATASET_LICENSE_AND_CONTENT_TO_VERIFY"}
    return list(out.values())


def _dspace_source(source_id, portal, cfg, session):
    """Try the public DSpace 7 REST search route; retain route errors in manifest."""
    home = (portal.get("portal_url") or "").split("/jspui", 1)[0].rstrip("/")
    endpoint = home + "/server/api/core/items"
    out = {}
    for term in cfg["queries"]:
        response = session.get(endpoint, params={"query": term, "size": 100, "page": 0}, timeout=(10, 60))
        response.raise_for_status()
        payload = response.json()
        items = payload.get("_embedded", {}).get("items", [])
        for item in items:
            uuid = str(item.get("uuid") or item.get("id") or "")
            if not uuid:
                continue
            links = item.get("_links") or {}
            self_link = (links.get("self") or {}).get("href", "")
            if "/server/api/core/items/" in self_link:
                self_link = self_link.replace("/server/api/core/items/", "/items/", 1)
            out[uuid] = {"record_id": f"{source_id}:{uuid}", "source_id": source_id,
                "title": item.get("name") or item.get("title") or uuid,
                "url": self_link or portal.get("portal_url"), "api_record_id": uuid,
                "description": "", "record_type": "catalog_lead",
                "access_state": "PUBLIC_REPOSITORY_RECORD_FULLTEXT_AND_LICENSE_TO_VERIFY"}
    return list(out.values())


def _write_html_index(path, records, runs):
    groups = {}
    for row in records:
        groups.setdefault(int(row.get("source_tier", 9)), []).append(row)
    parts = ["<!doctype html><html lang='pt-br'><meta charset='utf-8'>",
        "<title>Fontes hierarquizadas de inventários florestais</title>",
        "<style>body{font:16px Arial,sans-serif;max-width:1100px;margin:2rem auto;color:#17352a}"
        "h1,h2{color:#096b3b}li{margin:.45rem 0}.status{color:#555;font-size:.9em}</style>",
        "<h1>Acesso às fontes hierarquizadas de inventários</h1>",
        "<p>Use os links na ordem indicada. A página oferece acesso à fonte ou ao registro descoberto; metadados não equivalem a inventário validado.</p>"]
    for tier, rows in sorted(groups.items()):
        parts.append(f"<h2>Nível {tier}: {html.escape(TIER_LABELS.get(tier, 'Fonte'))}</h2><ul>")
        seen = set()
        for row in rows:
            url = str(row.get("url") or row.get("api_url") or "")
            if not url.startswith("https://") or (row.get("source_id"), url) in seen:
                continue
            seen.add((row.get("source_id"), url))
            title = html.escape(str(row.get("title") or row.get("source_id")))
            source = html.escape(str(row.get("source_id") or ""))
            parts.append(f"<li><a href='{html.escape(url, quote=True)}'>{title}</a> <span class='status'>[{source}]</span></li>")
        parts.append("</ul>")
    parts.append("<h2>Estado das consultas automatizadas</h2><ul>")
    for run in runs:
        parts.append("<li>" + html.escape(str(run.get("source_id"))) + ": " +
            html.escape(str(run.get("status"))) + f" — {int(run.get('records', 0))} registros " +
            html.escape(str(run.get("error", ""))) + "</li>")
    parts.append("</ul><p>Elegibilidade depende de fitofisionomia, microrregião/região, licença, desenho, unidade amostral, variáveis, incerteza e auditoria do documento. Inventário anexo de licenciamento só entra no último nível com aceite expresso do próprio inventário.</p></html>")
    Path(path).write_text("\n".join(parts), encoding="utf-8")


def collect_hierarchical_sources(destination, *, session=None, max_oai_pages=30):
    """Search available national/institutional APIs and save ordered source leads.

    This is a discovery pass: no record is counted as a distinct inventory or
    promoted to quantitative use until the attached data/document is inspected.
    """
    session = _session(session)
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    portals = _portal_map()
    found, runs = [], []
    adapters = {"ckan": _ckan_source, "dataverse": _dataverse_source,
                "zenodo": _zenodo_source, "dspace": _dspace_source}
    for source_id, cfg in MACHINE_SOURCES.items():
        portal = portals.get(source_id)
        if not portal:
            runs.append({"source_id": source_id, "status": "ROUTE_NOT_REGISTERED", "records": 0})
            continue
        try:
            if cfg["adapter"] == "oai":
                records = _oai_source(source_id, portal, cfg, session, max_pages=max_oai_pages)
            else:
                records = adapters[cfg["adapter"]](source_id, portal, cfg, session)
            for row in records:
                row.update({"source_tier": cfg["tier"], "source_tier_label": TIER_LABELS[cfg["tier"]],
                    "usable_for_estimation": False,
                    "triage_rule": "confirmar fonte, documento/dataset, licença, método, unidade amostral, fitofisionomia, escala, n e incerteza"})
            found.extend(records)
            partial = any(r.get("harvest_completeness") == "PARTIAL_PAGE_LIMIT" for r in records)
            runs.append({"source_id": source_id, "status": "PARTIAL" if partial else "OK",
                         "records": len(records), "adapter": cfg["adapter"]})
        except Exception as exc:
            runs.append({"source_id": source_id, "status": "ERROR", "records": 0,
                         "adapter": cfg["adapter"], "error": f"{type(exc).__name__}: {exc}"[:500]})

    # Keep routes that require portal search, login, LAI or individual document
    # retrieval visible and ordered. These are actionable access entries.
    run_by_source = {r["source_id"]: r for r in runs}
    for source_id, portal in portals.items():
        cfg = MACHINE_SOURCES.get(source_id)
        tier = cfg["tier"] if cfg else 5
        run = run_by_source.get(source_id, {})
        found.append({"record_id": f"route:{source_id}", "source_id": source_id,
            "title": portal.get("institution") or source_id, "url": portal.get("portal_url"),
            "api_url": portal.get("api_url") or "", "record_type": "source_route",
            "source_tier": tier, "source_tier_label": TIER_LABELS[tier],
            "access_state": ("API_" + str(run.get("status")) if cfg else
                             portal.get("access_status") or "PORTAL_ROUTE"),
            "api_status": run.get("status", "MANUAL_OR_UNCONFIRMED"),
            "usable_for_estimation": False,
            "triage_rule": run.get("error") or portal.get("notes") or "Busca manual/documental; conferir acesso e conteúdo."})
    found.sort(key=lambda r: (r.get("source_tier", 9), r.get("source_id", ""), r.get("title", "").casefold()))
    manifest = {"generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "ampliar descoberta e acesso às fontes hierarquizadas de inventários florestais e fitossociologia",
        "status": "METADADOS_DE_DESCOBERTA; nenhum lead equivale automaticamente a inventário independente ou dado elegível",
        "source_hierarchy": TIER_LABELS, "runs": runs, "candidate_or_route_count": len(found),
        "machine_discovered_count": sum(1 for x in found if x.get("record_type") == "catalog_lead"),
        "selection_policy": [
            "exigir a mesma fitofisionomia IBGE; nunca compensar classe diferente com proximidade",
            "buscar microrregião primeiro e ampliar para região/bioma compatível somente se não houver fonte local",
            "dentro do mesmo escopo, priorizar parcela aberta institucional georreferenciada; depois estatística institucional publicada; por último inventário ambiental com aceite explícito do anexo",
            "distância entra como desempate entre fontes do mesmo nível; metadado administrativo e ocorrência de espécie não são inventário nem dominância",
            "dados fitossociológicos elegíveis preservam parcela, DAP, área basal, abundância/frequência, nomes vulgar/científico, esforço, unidade, n, licença e incerteza",
        ],
        "records": found}
    (root / "manifest_fontes_hierarquizadas.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_html_index(root / "acesso_fontes_hierarquizadas.html", found, runs)
    fields = ["source_tier", "source_tier_label", "source_id", "record_id", "title", "url", "api_url",
              "access_state", "record_type", "usable_for_estimation", "triage_rule"]
    with (root / "fontes_hierarquizadas.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(found)
    # Persist searchable metadata leads beside the downloaded library. The DB
    # keeps every discovered lead ineligible until the actual content is QA'd.
    try:
        from national_inventory_database import initialize_database, register_discovered_records
        catalog_db = root / "catalogo_inventarios_fontes_hierarquizadas.sqlite"
        initialize_database(catalog_db)
        by_source = {}
        for row in found:
            if row.get("record_type") == "catalog_lead":
                by_source.setdefault(row["source_id"], []).append(row)
        persisted = 0
        for source_id, rows in by_source.items():
            persisted += register_discovered_records(catalog_db, source_id, rows)
        manifest["searchable_catalog_database"] = str(catalog_db)
        manifest["catalog_leads_registered"] = persisted
        (root / "manifest_fontes_hierarquizadas.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        manifest["catalog_database_status"] = f"ERROR: {type(exc).__name__}: {exc}"[:500]
        (root / "manifest_fontes_hierarquizadas.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Descobre inventários nas fontes brasileiras hierarquizadas")
    ap.add_argument("--output", default="Enform_Verde_Biblioteca_Inventarios")
    ap.add_argument("--max-oai-pages", type=int, default=30)
    args = ap.parse_args()
    print(json.dumps(collect_hierarchical_sources(args.output, max_oai_pages=args.max_oai_pages), ensure_ascii=False, indent=2))
