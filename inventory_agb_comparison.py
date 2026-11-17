"""Exploratory, same-physiognomy IFN AGB reference for comparison with CCI.

The SFB panel contains per-hectare AGB candidates, while the expanded IFN
SQLite contains the primary tree observations and the official IBGE crosswalk.
The two are joined by physical sampling-unit identity. This is a regional
comparison only; it is never added to the carbon stock and never replaces a
successful ESA BIOMASS FH + inventory structural estimate.
"""
from __future__ import annotations

import csv
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


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in value if ch.isalnum() and not unicodedata.combining(ch))


def _distance_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def estimate_ifn_agb_comparison(*, biome, physiognomy, area_ha,
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
    panel_sha = hashlib.sha256(PANEL.read_bytes()).hexdigest()
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
        return {"status": "N/D", "reason": "MENOS_DE_CINCO_UAS_COMPATIVEIS_NA_MESMA_FITOFISIONOMIA",
                "n_ua_compativeis": len(selected), "raio_km": float(max_distance_km),
                "base_ifn_expandida_usada": True}

    values = [r["agb_mg_ha"] for r in selected]
    mean, sd = statistics.mean(values), statistics.stdev(values)
    cfrac = 0.47
    return {
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
        "source": "SFB/IFN Painel de Biomassa e Carbono (AGB_Chave), vinculado à base IFN DAP10 expandida e ao cruzamento IFN × IBGE Vegetação legenda_1",
        "source_url": "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono",
        "candidate_file_sha256": panel_sha,
        "source_panel_sha256": "8f4dbd3c22904632447796d39ee575f60ea36ce483a3e5f3849ddff762c1cc6e",
        "uncertainty": (
            f"DP amostral entre {len(selected)} UAs: {sd:.2f} Mg AGB/ha; "
            f"faixa observada {min(values):.2f}–{max(values):.2f} Mg/ha. "
            "Essa dispersão descreve as UAs selecionadas, não é IC95% nem intervalo preditivo da propriedade. "
            "Erro da equação AGB_Chave, expansão do desenho amostral, precisão posicional e transferência espacial não quantificados."
        ),
        "confidence": "BAIXA; comparação regional experimental, sem validação independente na propriedade",
        "calculation_trace": {
            "selection": "bioma + MT + Floresta Natural + tipologia idêntica + legenda_1 IBGE idêntica; cinco UAs físicas mais próximas em até 250 km",
            "mean_formula": "média aritmética não ponderada das AGB mg/ha por UA independente",
            "sample_sd_formula": "DP amostral entre UAs; não usar como erro da AOI",
            "carbon_formula": "AGB × fração operacional 0,47; estoque comparativo = tC/ha × área da classe",
            "inventory_db_sha256": "9ffeb84e582d2fa2c5c892bd798346f227adc2080d7976a75cea71238ba75389",
            "area_basis": "mesma área de classe nativa confirmada por SAR usada no estrato CCI",
            "not_included": ["erro do fator 0,47", "incerteza de expansão", "erro AGB_Chave", "transferência para a AOI"]
        },
        "not_added_to_stock_total": True,
        "limitations": [
            "AGB_Chave é a opção publicada pelo painel, mas sua escolha não foi auditada independentemente para esta fitofisionomia",
            "coordenadas do painel têm precisão posicional não quantificada",
            "a base IFN DAP10 é um programa nacional; UAs não equivalem a inventários independentes por UF",
            "não é validação local nem deve ser somada ao estoque ESA CCI",
        ],
    }
