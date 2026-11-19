"""All compatible forest-inventory AGB references for comparison with CCI.

The SFB panel contains per-hectare AGB candidates, while the expanded IFN
SQLite contains the primary tree observations and the official IBGE crosswalk.
IFN sampling units are joined by physical identity. Published AGB aggregates
from every harmonized source are always consulted independently of IFN file
availability, and remain separate when their designs cannot be pooled. This
regional comparison is never added to the carbon stock and never replaces a
successful ESA BIOMASS FH + inventory structural estimate.
"""
from __future__ import annotations

import csv
from functools import lru_cache
import hashlib
import math
import sqlite3
import statistics
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "data" / "ifn_fesv_mato_grosso_agb_candidates_v1.csv"
DB = ROOT / "data" / "national_inventory_microdata_v1.sqlite"
UF_NAME = {"MT": "Mato Grosso"}
PANEL_SHA256 = "f677e2fbc8288b36e5614c1e3ada47fdc5becd3694fccb8d150d9e2d6e361ea8"
AGGREGATE_PANEL = ROOT / "data" / "structural_aggregate_evidence_v1.csv"


@lru_cache(maxsize=16)
def _aggregate_rows_cached(path_text, size_bytes, mtime_ns):
    """Parse aggregate evidence once per file revision for all report readers."""
    with Path(path_text).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = tuple(reader.fieldnames or ())
        rows = tuple(dict(row) for row in reader)
    return fields, rows


def _aggregate_rows(path):
    """Use a stat-keyed in-memory index; edits/replacements invalidate it."""
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return _aggregate_rows_cached(str(resolved), stat.st_size, stat.st_mtime_ns)


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in value if ch.isalnum() and not unicodedata.combining(ch))


_IBGE_PHYSIOGNOMY_SUFFIXES = {
    "dasterrasbaixas", "aluvial", "submontana", "montana", "altomontana",
}


def _physiognomy_match_level(reference, target):
    """Match exact IBGE formations or a known parent/subformation relation.

    Broader and narrower matches are for separately displayed references only;
    callers must not pool them or treat them as plot-level calibration data.
    """
    ref, tgt = _norm(reference), _norm(target)
    if not ref or not tgt:
        return None
    if ref == tgt:
        return "EXATA"
    if tgt.startswith(ref) and tgt[len(ref):] in _IBGE_PHYSIOGNOMY_SUFFIXES:
        return "REFERENCIA_DE_FITOFISIONOMIA_PAI"
    if ref.startswith(tgt) and ref[len(tgt):] in _IBGE_PHYSIOGNOMY_SUFFIXES:
        return "REFERENCIA_DE_SUBFITOFISIONOMIA"
    return None


def _distance_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def canonical_panel_sha256(data):
    """Hash CSV content independently of LF versus Windows CRLF endings."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _published_aggregate_source_ids(path=AGGREGATE_PANEL):
    """Inventory every source represented in the harmonized AGB register."""
    sources=set()
    try:
        _, rows = _aggregate_rows(path)
        for row in rows:
            source=str(row.get("source_id") or "").strip()
            if source:sources.add(source)
    except (OSError,csv.Error):
        return []
    return sorted(sources)


def published_agb_references(*, biome, physiognomy, path=AGGREGATE_PANEL):
    """All exact or explicitly hierarchical published AGB references, kept separate."""
    rows=[]; seen=set()
    try:
        _, indexed_rows = _aggregate_rows(path)
        for row in indexed_rows:
                match_level=_physiognomy_match_level(row.get("physiognomy"),physiognomy)
                if (_norm(row.get("metric")) != "agb"
                        or _norm(row.get("biome")) != _norm(biome)
                        or match_level is None):
                    continue
                value=_optional_float(row.get("center"))
                if value is None or value < 0: continue
                key=(row.get("source_id"),row.get("region"),row.get("citation"),value)
                if key in seen: continue
                seen.add(key)
                rows.append({"status":"REFERENCIA_AGREGADA_PUBLICADA",
                    "source_id":row.get("source_id"), "institution":row.get("institution"),
                    "region":row.get("region"), "agb_mean_mg_ha":value,
                    "physiognomy_match_level":match_level,"reference_only":True,
                    "sd_mg_ha":_optional_float(row.get("sd")),
                    "ci95_low_mg_ha":_optional_float(row.get("ci95_low")),
                    "ci95_high_mg_ha":_optional_float(row.get("ci95_high")),
                    "n_plots":row.get("n_plots"), "n_sites":row.get("n_sites"),
                    "citation":row.get("citation"), "url":row.get("url"),
                    "statistical_use":row.get("statistical_use"),
                    "not_added_to_stock_total":True})
    except (OSError, csv.Error):
        return []
    return rows


def published_structural_references(*, biome, physiognomy, path=AGGREGATE_PANEL):
    """Return published horizontal-structure summaries for exact/hierarchical domains.

    Aggregate-only publications are valid regional/physiognomic references,
    but are not plot observations and cannot calibrate a SAR model on their
    own. Each source, campaign, stratum and metric remains a separate record.
    """
    rows=[]; seen=set()
    try:
        _, indexed_rows = _aggregate_rows(path)
        for row in indexed_rows:
                metric=_norm(row.get("metric"))
                if metric in {"agb", "totalbiomass", "carbon", "agc"}:
                    continue
                match_level=_physiognomy_match_level(row.get("physiognomy"),physiognomy)
                if (_norm(row.get("biome")) != _norm(biome)
                        or match_level is None):
                    continue
                center=_optional_float(row.get("center"))
                if center is None or center < 0:
                    continue
                key=(row.get("source_id"),row.get("region"),row.get("metric"),
                     row.get("center_type"),center,row.get("citation"))
                if key in seen: continue
                seen.add(key)
                rows.append({"status":"REFERENCIA_ESTRUTURAL_AGREGADA_PUBLICADA",
                    "source_id":row.get("source_id"),
                    "institution":row.get("institution"),
                    "biome":row.get("biome"),"physiognomy":row.get("physiognomy"),
                    "physiognomy_match_level":match_level,
                    "region":row.get("region"),"metric":row.get("metric"),
                    "unit":row.get("unit"),"center_type":row.get("center_type"),
                    "center":center,"sd":_optional_float(row.get("sd")),
                    "se":_optional_float(row.get("se")),
                    "ci95_low":_optional_float(row.get("ci95_low")),
                    "ci95_high":_optional_float(row.get("ci95_high")),
                    "iqr_low":_optional_float(row.get("iqr_low")),
                    "iqr_high":_optional_float(row.get("iqr_high")),
                    "range_low":_optional_float(row.get("range_low")),
                    "range_high":_optional_float(row.get("range_high")),
                    "n_plots":row.get("n_plots"),"n_sites":row.get("n_sites"),
                    "citation":row.get("citation"),"url":row.get("url"),
                    "statistical_use":row.get("statistical_use"),
                    "not_plot_level_data":True,"not_added_to_stock_total":True})
    except (OSError,csv.Error):
        return []
    return rows


def published_inventory_evidence(*, biome, physiognomy, path=AGGREGATE_PANEL):
    """Compact, auditable AGB and horizontal-reference bundle for pipeline reports."""
    try:
        fields, _ = _aggregate_rows(path)
        required={"source_id","biome","physiognomy","metric","center"}
        if not required.issubset(set(fields)):
            raise csv.Error("required evidence columns are missing")
    except (OSError,csv.Error) as exc:
        return {"status":"ERRO_TECNICO_LEITURA_REGISTRO",
            "diagnostic":type(exc).__name__,"agb_references":[],
            "horizontal_structure_references":[],"agb_reference_count":0,
            "horizontal_reference_count":0,"sources":[],
            "use_when_plot_microdata_unavailable":None,
            "uncertainty_rule":None,"not_added_to_stock_total":True}
    agb=published_agb_references(biome=biome,physiognomy=physiognomy,path=path)
    horizontal=published_structural_references(
        biome=biome,physiognomy=physiognomy,path=path)
    return {
        "status":"REFERENCIAS_PUBLICADAS_LISTADAS" if agb or horizontal else "SEM_REFERENCIA_COMPATIVEL",
        "matching":"bioma exato; fitofisionomia exata ou relação hierárquica IBGE explicitamente reconhecida",
        "agb_references":agb,
        "horizontal_structure_references":horizontal,
        "agb_reference_count":len(agb),
        "horizontal_reference_count":len(horizontal),
        "sources":sorted({str(row.get("source_id")) for row in agb+horizontal
                          if row.get("source_id")}),
        "use_when_plot_microdata_unavailable":(
            "baliza regional/fitofisionômica e checagem de plausibilidade; não equivale a parcela, "
            "pareamento pixel-parcela nem validação independente"),
        "uncertainty_rule":(
            "preservar SD/SE/IC/faixas publicados; se ausentes, marcar incerteza da referência como N/D; "
            "não inferir erro-padrão a partir de média ou n sem desenho e variância"),
        "not_added_to_stock_total":True,
        "reference_only":True,
        "hierarchical_matches_are_not_pooled_or_used_as_calibration":True,
    }


def tapajos_acceptance_inventory_references(agb_mg_ha, pixel_count, evidence):
    """Gate compiled acceptance on a quantitative estimate or real inventory refs.

    Published aggregates can satisfy the reference branch only; they are never
    converted to the selected estimate and never fill `agb_mg_ha`.
    """
    refs=list((evidence or {}).get("agb_references") or [])
    eligible=[]
    if agb_mg_ha is None and int(pixel_count or 0)>0:
        for row in refs:
            value=_optional_float(row.get("agb_mean_mg_ha"))
            if (row.get("status")=="REFERENCIA_AGREGADA_PUBLICADA"
                    and value is not None and value>=0
                    and row.get("not_added_to_stock_total") is True):
                eligible.append(row)
    return {
        "acceptance_status":(
            "ESTIMATIVA_QUANTITATIVA_DISPONIVEL" if agb_mg_ha is not None else
            "SAR_E_REFERENCIAS_INVENTARIO_OK_AGB_N_D" if eligible else
            "SEM_AGB_E_SEM_REFERENCIA_INVENTARIO_ELEGIVEL"),
        "inventory_reference_eligible":bool(eligible),
        "eligible_inventory_references":eligible,
        "agb_quantitative_estimate_available":agb_mg_ha is not None,
    }


def _estimate_ifn_agb_comparison(*, biome, physiognomy, area_ha,
                                centroid_lon, centroid_lat,
                                max_distance_km=250.0, max_units=5):
    """Return a cautious AGB/carbon comparison, or N/D when the evidence fails.

    Eligibility requires a unique IFN-to-IBGE `legenda_1` match and the same
    unit in the expanded tree database. The published SFB AGB_Chave selection
    is not independently audited; the output therefore remains experimental.
    """
    try:
        area, lon, lat = float(area_ha), float(centroid_lon), float(centroid_lat)
        if not all(math.isfinite(v) for v in (area, lon, lat)) or area <= 0:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        return {"status": "N/D", "reason": "AREA_OU_CENTROIDE_INVALIDO"}
    if not DB.is_file() or not PANEL.is_file():
        return {"status": "N/D", "reason": "BASE_IFN_EXPANDIDA_OU_PAINEL_AGB_INDISPONIVEL"}
    # Windows checkouts may normalize LF to CRLF. Hash the canonical text
    # representation so line-ending policy does not disable a valid dataset.
    panel_sha = canonical_panel_sha256(PANEL.read_bytes())
    if panel_sha != PANEL_SHA256:
        return {"status": "N/D", "reason": "HASH_DO_PAINEL_IFN_AGB_DIVERGENTE",
                "observed_sha256": panel_sha}
    try:
        from inventory_microdata_library import official_inventory_database_status
        db_status = official_inventory_database_status(DB)
        if db_status.get("operational_for_tree_selection") is not True:
            return {"status": "N/D", "reason": "BASE_IFN_EXPANDIDA_INCOMPLETA_OU_DIVERGENTE",
                    "database_status": db_status}
    except Exception as exc:
        return {"status": "N/D", "reason": "VALIDACAO_DA_BASE_IFN_FALHOU",
                "diagnostic": type(exc).__name__}

    # The currently harvested AGB_Chave candidate table covers MT only.
    try:
        with sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            matches = list(conn.execute(
                "SELECT x.ua_id,x.uf,x.source_biome,x.ibge_legenda_1,x.match_status, "
                "s.observation_count,s.mean_dbh_cm,s.mean_total_height_m,s.summed_sample_basal_area_m2 "
                "FROM ifn_sampling_unit_ibge_crosswalk x "
                "JOIN ifn_sampling_unit_summary s ON s.ua_id=x.ua_id AND s.uf=x.uf "
                "WHERE x.match_status='MATCH_UNICO_PONTO_INTERIOR' AND x.uf=?",
                (UF_NAME["MT"],)))
    except (sqlite3.Error, KeyError) as exc:
        return {"status": "N/D", "reason": "CONSULTA_BASE_IFN_EXPANDIDA_FALHOU",
                "diagnostic": type(exc).__name__}

    crosswalk = {_norm(r["ua_id"]): dict(r) for r in matches
                 if _norm(r["source_biome"]) == _norm(biome)
                 and _norm(r["ibge_legenda_1"]) == _norm(physiognomy)}
    candidates, seen = [], set()
    try:
        with PANEL.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                if (_norm(row.get("bioma")) != _norm(biome)
                        or row.get("uf") != "MT"
                        or row.get("classe_uso_da_terra") != "Floresta Natural"
                        or row.get("source_equation") != "AGB_Chave"
                        or _norm(row.get("tipologia_da_vegetacao")) != _norm(physiognomy)
                        or _norm(row.get("ua")) not in crosswalk):
                    continue
                ua = crosswalk[_norm(row["ua"])]
                physical_key = (ua["uf"], ua["ua_id"])
                if physical_key in seen:
                    continue
                agb = float(row["agb_mg_ha"])
                ua_lon, ua_lat = float(row["lon_pc"]), float(row["lat_pc"])
                if not all(math.isfinite(v) for v in (agb, ua_lon, ua_lat)) or agb < 0:
                    continue
                distance = _distance_km(lon, lat, ua_lon, ua_lat)
                if distance <= float(max_distance_km):
                    seen.add(physical_key)
                    candidates.append({"ua_id": ua["ua_id"], "agb_mg_ha": agb,
                        "distance_km": distance, "observation_count": ua["observation_count"],
                        "mean_dbh_cm": ua["mean_dbh_cm"],
                        "mean_total_height_m": ua["mean_total_height_m"],
                        "sample_basal_area_m2": ua["summed_sample_basal_area_m2"],
                        "ibge_legenda_1": ua["ibge_legenda_1"]})
    except (OSError, csv.Error, KeyError, TypeError, ValueError) as exc:
        return {"status": "N/D", "reason": "PAINEL_IFN_AGB_INVALIDO",
                "diagnostic": type(exc).__name__}

    candidates.sort(key=lambda r: (r["distance_km"], r["ua_id"]))
    selected = candidates[:max(1, min(int(max_units), 20))]
    if len(selected) < 5:
        ifn_result = {"status": "N/D", "reason": "MENOS_DE_CINCO_UAS_COMPATIVEIS_NA_MESMA_FITOFISIONOMIA",
                      "n_ua_compativeis": len(selected), "raio_km": float(max_distance_km),
                      "base_ifn_expandida_usada": True}
    else:
        values = [r["agb_mg_ha"] for r in selected]
        mean, sd = statistics.mean(values), statistics.stdev(values)
        cfrac = 0.47
        ifn_result = {
        "status": "COMPARACAO_EXPERIMENTAL_IFN_AGB",
        "label": "Comparação regional por médias de UAs IFN compatíveis — experimental",
        "base_ifn_expandida_usada": True,
        "inventory_n_unique_sampling_units": len(selected),
        "inventory_tree_observations_in_selected_units": sum(int(r["observation_count"] or 0) for r in selected),
        "agb_mean_mg_ha": mean, "agb_sample_sd_mg_ha": sd,
        "agb_observed_range_mg_ha": [min(values), max(values)],
        "carbon_fraction": cfrac, "carbon_mean_tc_ha": mean * cfrac,
        "carbon_sample_sd_tc_ha": sd * cfrac,
        "carbon_total_tc_comparison": mean * cfrac * area,
        "carbon_total_sample_sd_tc": sd * cfrac * area,
        "carbon_total_tco2e_comparison": mean * cfrac * area * 44 / 12,
        "carbon_total_sample_sd_tco2e": sd * cfrac * area * 44 / 12,
        "area_ha": area, "biome": biome, "physiognomy": physiognomy,
        "selection_radius_km": float(max_distance_km),
        "nearest_ua_distance_km": selected[0]["distance_km"],
        "mean_selected_ua_distance_km": statistics.mean(r["distance_km"] for r in selected),
        "selected_units": selected,
        "source": "SFB/IFN Painel de Biomassa e Carbono (AGB_Chave), vinculado à base IFN DAP10 expandida",
        "source_url": "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono",
        "candidate_file_sha256": panel_sha,
        "uncertainty": (f"DP amostral entre {len(selected)} UAs: {sd:.2f} Mg AGB/ha; faixa observada "
            f"{min(values):.2f}–{max(values):.2f} Mg/ha. Não é IC95% nem intervalo preditivo; "
            "erros da equação, expansão, posição e transferência não quantificados."),
        "confidence": "BAIXA; comparação regional experimental, sem validação independente na propriedade",
        "not_added_to_stock_total": True,
        }

    # Include every verified published aggregate with AGB in the local
    # evidence register. Preserve each study as its own reference: unlike
    # plot microdata, these records cannot be pooled or distance-ranked.
    published = published_agb_references(biome=biome,physiognomy=physiognomy)
    result = dict(ifn_result)
    result["inventory_references"] = ([ifn_result] if ifn_result.get("status") != "N/D" else []) + published
    result["usable_inventory_sources_consulted"] = ["SFB_IFN_DAP10", "REGISTRO_AGREGADOS_PUBLICADOS"]
    result["published_aggregate_count"] = len(published)
    if result["status"] == "N/D" and published:
        result["status"] = "COMPARACAO_REFERENCIAS_PUBLICADAS"
        result["reason"] = "IFN microdados não elegíveis; referências agregadas compatíveis listadas separadamente"
    if not result["inventory_references"]:
        result["reason"] = result.get("reason", "SEM_REFERENCIAS_DE_AGB_COMPATIVEIS_NA_BASE_UTILIZAVEL")
    return result


def estimate_inventory_agb_comparison(*, biome, physiognomy, area_ha,
                                      centroid_lon, centroid_lat,
                                      max_distance_km=250.0, max_units=5):
    """Use all source-level AGB evidence, independent of IFN availability.

    The IFN per-UA comparison is one evidence tier, not the inventory base.
    Every compatible published aggregate in the harmonized register is
    included as a distinct reference even when IFN microdata are unavailable.
    Do not pool studies with noncomparable designs or uncertainty semantics.
    """
    kwargs={"biome":biome,"physiognomy":physiognomy,"area_ha":area_ha,
            "centroid_lon":centroid_lon,"centroid_lat":centroid_lat,
            "max_distance_km":max_distance_km,"max_units":max_units}
    try:
        result=_estimate_ifn_agb_comparison(**kwargs)
    except Exception as exc:
        result={"status":"N/D","reason":"COMPARACAO_IFN_NAO_CONCLUIDA",
                "diagnostic":type(exc).__name__}
    published=published_agb_references(biome=biome,physiognomy=physiognomy)
    structural=published_structural_references(biome=biome,physiognomy=physiognomy)
    refs=list(result.get("inventory_references") or [])
    seen={(r.get("source_id"),r.get("region"),r.get("citation")) for r in refs}
    for ref in published:
        key=(ref.get("source_id"),ref.get("region"),ref.get("citation"))
        if key not in seen:
            refs.append(ref); seen.add(key)
    ifn_valid=result.get("status")=="COMPARACAO_EXPERIMENTAL_IFN_AGB"
    if not ifn_valid and published:
        result["status"]="COMPARACAO_REFERENCIAS_PUBLICADAS"
        result["reason"]="Referências AGB de inventários compatíveis listadas por fonte; IFN não elegível ou indisponível; não há média conjunta sem desenho e incerteza harmonizados."
    elif not ifn_valid and not published:
        result["status"]="N/D"
        result["reason"]=result.get("reason") or "SEM_REFERENCIAS_DE_AGB_COMPATIVEIS_NA_BASE_UTILIZAVEL"
    result["inventory_references"]=refs
    result["published_structural_references"]=structural
    result["published_structural_reference_count"]=len(structural)
    result["matched_published_structural_sources"]=sorted({
        str(ref.get("source_id")) for ref in structural if ref.get("source_id")})
    result["published_aggregate_count"]=len(published)
    usable_sources={
        str(ref.get("source_id")) for ref in refs if ref.get("source_id")}
    if ifn_valid:usable_sources.add("SFB_IFN_DAP10")
    result["usable_inventory_sources_consulted"]=sorted(usable_sources)
    # Distinguish a source being searched from a source yielding a compatible
    # AGB value. This prevents an empty match list from implying that only IFN
    # was consulted or that the published inventory register was skipped.
    result["inventory_sources_searched"]=[
        "IFN_EXPANDED_TREE_MICRODATA","SFB_IFN_DAP10_AGB_PANEL",
        "HARMONIZED_PUBLISHED_AGB_REGISTER",
        "HARMONIZED_PUBLISHED_STRUCTURAL_REGISTER"]
    result["registered_published_inventory_sources"]=_published_aggregate_source_ids()
    result["matched_published_inventory_sources"]=sorted({
        str(ref.get("source_id")) for ref in published if ref.get("source_id")})
    result["inventory_source_query_scope"]={
        "biome":str(biome),"physiognomy":str(physiognomy),
        "matching":"exact normalized biome; exact or explicit IBGE parent/subformation relation for cited comparison only",
        "ifn_tree_microdata_available":bool(result.get("base_ifn_expandida_usada")),
        "harmonized_register_available":AGGREGATE_PANEL.is_file()}
    result["inventory_base_scope"]="todas as fontes com AGB harmonizada e compatibilidade exata disponíveis no registro; cada fonte preservada separadamente; IFN é apenas uma das bases"
    result["ifn_microdata_available"]=bool(result.get("base_ifn_expandida_usada"))
    result["not_added_to_stock_total"]=True
    return result


# Backward-compatible name for callers/tests that request the IFN tier directly.
estimate_ifn_agb_comparison=estimate_inventory_agb_comparison

def _optional_float(value):
    try:
        out=float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None
