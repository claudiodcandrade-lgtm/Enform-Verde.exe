"""Conditional state-level AGB scenario from public SFB/IFN observations.

This is called only after SAR routes report no quantitative pixels usable in
the AOI and the pipeline's own inventory fallback gate accepts the absence.
It never confirms current native cover: the area basis is explicitly the
potential IBGE phytoregion intersection. The spread across independent IFN
sampling units is descriptive, not an AOI confidence/prediction interval.
"""
from __future__ import annotations

import csv
import math
import statistics
import unicodedata
from pathlib import Path

DATA = Path(__file__).parent / "data" / "ifn_fesv_mato_grosso_agb_candidates_v1.csv"
SOURCE_URL = "https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono"
SOURCE_PANEL_SHA256 = "8f4dbd3c22904632447796d39ee575f60ea36ce483a3e5f3849ddff762c1cc6e"
CARBON_FRACTION = 0.47  # existing application convention; its uncertainty is not included


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


def no_valid_sar_pixels(sar_result):
    """Fail closed: technical/read failures and SAR observations block transfer."""
    if not isinstance(sar_result, dict) or sar_result.get("status") != "SAR_NAO_PROCESSADO":
        return False
    audit = sar_result.get("audit") or {}
    gate = sar_result.get("inventory_fallback_gate") or audit.get("inventory_fallback_gate") or {}
    if gate.get("eligible") is not True or audit.get("processed_without_agb") or audit.get("biomass_height", {}).get("zonal_height"):
        return False
    warnings = [str(x).casefold() for x in audit.get("warnings", [])]
    # A transport/authentication/read error is not evidence that suitable scenes
    # do not exist. Do not mask a technical failure with an inventory scenario.
    return not any(any(term in w for term in (
        "erro", "falha", "failed", "authentication", "pixel read",
        "não pôde ser lido", "nao pode ser lido", "timeout")) for w in warnings)


def estimate_fesv_state_scenario(*, biome, physiognomy, area_ha, sar_result,
                                 centroid_lon=None, centroid_lat=None):
    """Build a transparent conditional scenario for the currently supported domain."""
    if not no_valid_sar_pixels(sar_result):
        return {"status": "BLOQUEADO", "reason": "SAR_COM_PIXELS_OU_FALHA_TECNICA_NAO_RESOLVIDA"}
    if _norm(biome) != _norm("Amazônia") or _norm(physiognomy) not in (
            _norm("Floresta Estacional Sempre-Verde"),
            _norm("Floresta Estacional Sempre-Verde Submontana")):
        return {"status": "N/D", "reason": "SEM_INVENTARIO_ABERTO_COMPATIVEL_NESTA_FITOFISIONOMIA"}
    if not isinstance(area_ha, (int, float)) or not math.isfinite(float(area_ha)) or area_ha <= 0:
        return {"status": "N/D", "reason": "AREA_POTENCIAL_IBGE_INVALIDA"}
    if not all(isinstance(v, (int, float)) and math.isfinite(float(v))
               for v in (centroid_lon, centroid_lat)):
        return {"status": "N/D", "reason": "CENTROIDE_AOI_INDISPONIVEL_PARA_HIERARQUIA_GEOGRAFICA"}
    with DATA.open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream)
                if _norm(r.get("bioma")) == _norm("Amazônia")
                and r.get("uf") == "MT"
                and r.get("classe_uso_da_terra") == "Floresta Natural"
                and _norm(r.get("tipologia_da_vegetacao")) == _norm("Floresta Estacional Sempre-verde")]
    # One row per unique physical IFN sampling unit; exclude any row whose
    # source says the equation or transfer has been independently validated.
    rows = [r for r in rows if r.get("ua") and r.get("source_equation") == "AGB_Chave"
            and r.get("equation_choice_audited") == "false"
            and r.get("scientifically_validated") == "false"]
    def distance_km(row):
        lat1=math.radians(float(centroid_lat)); lat2=math.radians(float(row["lat_pc"]))
        dlat=lat2-lat1; dlon=math.radians(float(row["lon_pc"])-float(centroid_lon))
        h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return 6371.0088*2*math.asin(min(1.0,math.sqrt(h)))
    rows=[r for r in rows if distance_km(r)<=250.0]
    values = [float(r["agb_mg_ha"]) for r in rows]
    if len(values) < 5 or any(not math.isfinite(x) or x < 0 for x in values):
        return {"status": "N/D", "reason": "AMOSTRA_IFN_INSUFICIENTE_OU_INVALIDA", "n_ua": len(values)}
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    carbon = mean * CARBON_FRACTION
    area = float(area_ha)
    stock_tc = carbon * area
    return {
        "status": "CENARIO_CONDICIONAL_INVENTARIO_SEM_PIXELS_SAR",
        "estimate_label": "estimativa com incerteza não mensurada",
        "current_native_cover_confirmed": False,
        "area_basis": "interseção da AOI com fitofisionomia potencial IBGE legenda_1; não é máscara atual",
        "area_ha": area, "biome": "Amazônia", "physiognomy": physiognomy,
        "geographic_tier": "regional por proximidade (≤250 km) — unidades do IFN em Mato Grosso; microrregião não comprovada",
        "nearest_inventory_unit_distance_km": min(distance_km(r) for r in rows),
        "selection_radius_km": 250.0,
        "inventory_n_unique_sampling_units": len(values),
        "agb_mean_mg_ha": mean, "agb_sample_sd_mg_ha": sd,
        "agb_observed_range_mg_ha": [min(values), max(values)],
        "carbon_fraction": CARBON_FRACTION, "carbon_fraction_uncertainty": "NÃO QUANTIFICADA",
        "carbon_mean_tc_ha": carbon, "carbon_total_tc_scenario": stock_tc,
        "carbon_total_tco2e_scenario": stock_tc * 44 / 12,
        "calculation_trace": {
            "candidate_filter": "bioma Amazônia + UF MT + Floresta Natural + Floresta Estacional Sempre-verde + distância geodésica ao centroide <= 250 km; uma linha por UA física",
            "selected_ua_count": len(values), "sum_agb_mg_ha": sum(values),
            "agb_mean_formula": "sum(AGB_Chave das UAs selecionadas) / n",
            "agb_mean_mg_ha": mean, "agb_sample_sd_formula": "desvio-padrão amostral entre UAs independentes",
            "agb_sample_sd_mg_ha": sd,
            "carbon_density_formula": "AGB média × fator C 0,47",
            "carbon_density_tc_ha": carbon, "area_formula": "interseção exata AOI × IBGE legenda_1 (EPSG:6933)",
            "area_ha": area, "stock_formula": "carbono tC/ha × área condicional ha",
            "stock_tc_scenario": stock_tc, "co2e_formula": "estoque tC × 44/12",
            "stock_tco2e_scenario": stock_tc * 44 / 12,
            "not_included_in_uncertainty": ["transferência regional para a AOI", "erro da equação AGB_Chave", "incerteza do fator de carbono 0,47", "erro de classificação da cobertura potencial"],
        },
        "uncertainty": (
            f"estimativa com incerteza não mensurada. DP amostral conhecido entre {len(values)} unidades IFN únicas: {sd:.2f} Mg AGB/ha; "
            "faixa observada e DP são dispersão descritiva, não IC95%/intervalo preditivo da AOI. "
            "Erro de equação, transferência espacial, posição das unidades e fração de carbono não quantificados."
        ),
        "confidence": "BAIXA; cenário exploratório, sem validação na propriedade",
        "source": "Serviço Florestal Brasileiro — Painel de Biomassa e Carbono do IFN",
        "source_url": SOURCE_URL, "source_panel_sha256": SOURCE_PANEL_SHA256,
        "candidate_file": str(DATA.name), "equation": "AGB_Chave (equação publicada no painel; escolha não auditada independentemente)",
        "limitations": [
            "cobertura nativa atual não confirmada por SAR",
            "classe IBGE é potencial e serve apenas como área-base condicional",
            "amostra regional de até 250 km; raio define seleção, não valida transferência; sem estrato microregional verificado",
            "coordenadas IFN têm precisão posicional insuficiente para pareamento pixel-parcela",
            "conversão para carbono usa fração fixa 0,47 sem incerteza quantificada",
            "não somar ao estoque medido nem interpretar como resultado homologado",
        ],
    }
