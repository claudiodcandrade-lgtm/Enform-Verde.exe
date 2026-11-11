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
    """Allow the contingency only after every configured route is exhausted.

    Technical failures are retained as failures, never relabelled as catalogue
    absence. They can still trigger the inventory contingency after the audit
    confirms that configured routes ran and no SAR pixel/height was processed.
    """
    if not isinstance(sar_result, dict) or sar_result.get("status") != "SAR_NAO_PROCESSADO":
        return False
    audit = sar_result.get("audit") or {}
    gate = sar_result.get("inventory_fallback_gate") or audit.get("inventory_fallback_gate") or {}
    if (gate.get("eligible") is not True
            or audit.get("sar_sources_exhausted") is not True
            or audit.get("processed_without_agb")
            or audit.get("biomass_height", {}).get("zonal_height")
            or audit.get("gtdx_height", {}).get("available") is True):
        return False
    return audit.get("sar_pixel_processing_status") == "NENHUM_PIXEL_SAR_UTILIZAVEL_APOS_ROTAS_CONFIGURADAS"


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


def estimate_inventory_carbon_scenario(*, biome, physiognomy, area_ha, sar_result,
                                       aoi=None, centroid_lon=None, centroid_lat=None):
    """Use open IFN plots first, then the existing regional/national literature hierarchy.

    The returned number is a conditional AGB-derived carbon scenario on the
    potential IBGE phytoregion area. It never confirms current native cover and
    is never added to the SAR-measured stock.
    """
    if not no_valid_sar_pixels(sar_result):
        return {"status":"BLOQUEADO","reason":"ROTAS_SAR_NAO_ESGOTADAS_OU_OBSERVAVEL_SAR_PROCESSADO"}
    primary = estimate_fesv_state_scenario(
        biome=biome, physiognomy=physiognomy, area_ha=area_ha,
        sar_result=sar_result, centroid_lon=centroid_lon, centroid_lat=centroid_lat)
    if primary.get("status") == "CENARIO_CONDICIONAL_INVENTARIO_SEM_PIXELS_SAR":
        return primary

    if not isinstance(area_ha, (int, float)) or not math.isfinite(float(area_ha)) or float(area_ha) <= 0:
        return {"status":"N/D","reason":"AREA_IBGE_POTENCIAL_INVALIDA"}
    reference=(sar_result or {}).get("literature_reference") or {}
    if not reference.get("available") or reference.get("agb_mg_ha") is None:
        try:
            from national_fallback import national_agb_fallback
            reference=national_agb_fallback(biome,physiognomy,aoi=aoi) or {}
        except Exception as exc:
            return {"status":"N/D","reason":"FONTE_REGIONAL_COMPATIVEL_INDISPONIVEL",
                    "diagnostic":type(exc).__name__}
    if not reference.get("available") or reference.get("agb_mg_ha") is None:
        return {"status":"N/D","reason":"SEM_INVENTARIO_OU_REFERENCIA_PUBLICADA_COMPATIVEL_NESTA_FITOFISIONOMIA",
                "potential_area_ha":float(area_ha),
                "sar_gate":(sar_result or {}).get("inventory_fallback_gate")}
    try:
        agb=float(reference["agb_mg_ha"])
        if not math.isfinite(agb) or agb < 0:
            raise ValueError("AGB inválida")
        fraction=CARBON_FRACTION
        area=float(area_ha)
        carbon=agb*fraction
        stock=carbon*area
        bounds=reference.get("agb_range_mg_ha")
        if not bounds and reference.get("uncertainty_mg_ha") is not None:
            u=abs(float(reference["uncertainty_mg_ha"]))
            bounds=[max(0.0,agb-u),agb+u]
        if bounds and len(bounds)>=2:
            low_agb,high_agb=sorted((max(0.0,float(bounds[0])),float(bounds[1])))
            low_stock=low_agb*fraction*area
            high_stock=high_agb*fraction*area
            uncertainty=(
                f"Envelope da fonte: AGB {low_agb:.2f}–{high_agb:.2f} Mg/ha; "
                f"carbono condicional {low_stock:.2f}–{high_stock:.2f} tC. "
                "Esse envelope não é IC95% nem incerteza da AOI; erro de transferência para a propriedade e fração C permanecem não mensurados."
            )
            estimate_label="cenário condicional com envelope da fonte; incerteza de transferência não mensurada"
        else:
            low_agb=high_agb=low_stock=high_stock=None
            uncertainty=("estimativa com incerteza não mensurada. A fonte não fornece dispersão compatível para a AOI; "
                         "transferência espacial, erro da equação e fração de carbono não quantificados.")
            estimate_label="estimativa com incerteza não mensurada"
    except (TypeError,ValueError,OverflowError) as exc:
        return {"status":"N/D","reason":"REFERENCIA_AGB_INVALIDA","diagnostic":type(exc).__name__}

    audit=(sar_result or {}).get("audit") or {}
    gate=(sar_result or {}).get("inventory_fallback_gate") or audit.get("inventory_fallback_gate") or {}
    evidence=reference.get("evidence") or []
    return {
        "status":"CENARIO_CONDICIONAL_INVENTARIO_SEM_PIXELS_SAR",
        "estimate_label":estimate_label,
        "current_native_cover_confirmed":False,
        "area_basis":"interseção AOI × IBGE legenda_1 (potencial; não é máscara SAR de cobertura atual)",
        "area_ha":area,"biome":biome,"physiognomy":physiognomy,
        "geographic_tier":reference.get("label") or "referência publicada hierárquica; domínio conforme a fonte",
        "inventory_n_unique_sampling_units":reference.get("n"),
        "agb_mean_mg_ha":agb,"agb_range_mg_ha":[low_agb,high_agb] if bounds else None,
        "carbon_fraction":fraction,"carbon_fraction_uncertainty":"não fornecida pela fonte; fração operacional 0,47",
        "carbon_mean_tc_ha":carbon,"carbon_total_tc_scenario":stock,
        "carbon_total_tco2e_scenario":stock*44/12,
        "uncertainty":uncertainty,"confidence":"BAIXA; cenário condicional, sem validação na propriedade",
        "source":reference.get("source"),"source_url":reference.get("url"),"source_evidence":evidence,
        "sar_availability_status":gate.get("status") or gate.get("evidence"),
        "sar_technical_failures":gate.get("unresolved_warnings") or [],
        "calculation_trace":{
            "source_priority":"IFN/parcelas abertas microrregionais ou regionais; em seguida síntese publicada regional/nacional compatível",
            "selected_reference_method":reference.get("method") or reference.get("basis"),
            "agb_mg_ha":agb,"agb_interval_mg_ha":[low_agb,high_agb] if bounds else None,
            "carbon_fraction_formula":"AGB × fração de carbono 0,47",
            "carbon_density_tc_ha":carbon,
            "area_formula":"interseção exata AOI × IBGE legenda_1 em EPSG:6933; uso potencial",
            "area_ha":area,"stock_formula":"carbono tC/ha × área potencial ha",
            "stock_tc":stock,"co2e_formula":"estoque tC × 44/12",
            "stock_tco2e":stock*44/12,
            "not_included_in_uncertainty":["confirmação de cobertura atual", "transferência espacial para a propriedade", "erro de classificação SAR", "incerteza da fração de carbono"]
        },
        "limitations":["não confirma vegetação nativa atual", "não substitui altura SAR nem pixels SAR", "não somar ao estoque medido", "faixa de fonte não é intervalo de confiança da AOI"]
    }
