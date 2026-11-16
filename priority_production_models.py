"""Explicit mathematical routes for Enform Verde's priority production targets.

Annual crops use crop-specific PAM units, weather windows and SAR inputs.
Forage, planted forests and integrated systems have different response units
and cannot be passed through a grain-yield model. Their calculators accept
measured/modelled inputs and abstain when those inputs are absent.
"""
from __future__ import annotations

TARGETS = {
    "Soja": {
        "group": "annual_crop", "unit": "kg/ha de grão; t de grão",
        "status": "PANEL_CALIBRADO_EXPERIMENTAL",
        "equation": "y=a_u+b_u*t+beta_g*RY_FAO56+residuo_condicionado_por_vigor",
        "inputs": ("PAM N9", "cena SAR VV/VH datada", "ciclo/fenologia", "Tmin/Tmax/chuva",
                   "água disponível no solo", "área e incerteza da máscara"),
    },
    "Milho": {
        "group": "annual_crop", "unit": "kg/ha de grão; t de grão",
        "status": "PANEL_CALIBRADO_EXPERIMENTAL",
        "equation": "y=a_u+b_u*t+beta_g*RY_FAO56+residuo_condicionado_por_vigor",
        "inputs": ("PAM N9", "cena SAR VV/VH datada", "safra principal ou safrinha", "Tmin/Tmax/chuva",
                   "água disponível no solo", "área e incerteza da máscara"),
    },
    "Arroz": {
        "group": "annual_crop", "unit": "kg/ha de arroz em casca; t",
        "status": "PAM_CLIMA_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "arroz irrigado ou terras altas", "calendário", "chuva/temperatura",
                   "lâmina/inundação quando irrigado", "SAR VV/VH por fase"),
        "blockers": ("regime hídrico precisa ser distinguido; chuva não substitui lâmina/inundação"),
    },
    "Café": {
        "group": "perennial_crop", "unit": "kg/ha de café beneficiado; t",
        "status": "PAM_CLIMA_CENARIO_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "idade/renovação do cafezal", "cultivar e calendário", "chuva/temperatura/água no solo",
                   "SAR VV/VH por fase"),
        "blockers": ("idade, bienalidade e manejo do cafezal não estão no produto PAM por pixel",),
    },
    "Algodão": {
        "group": "annual_crop", "unit": "kg/ha de algodão em caroço; t",
        "status": "PAM_CLIMA_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9 algodão herbáceo", "calendário/cultivar", "Tmin/Tmax/chuva", "água no solo",
                   "SAR VV/VH por fase"),
        "blockers": ("pluma só pode ser derivada com fator de beneficiamento documentado"),
    },
    "Sorgo": {
        "group": "annual_crop", "unit": "kg/ha de grão; t",
        "status": "PAM_CLIMA_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "calendário", "Tmin/Tmax/chuva", "água no solo", "SAR VV/VH por fase"),
    },
    "Feijão": {
        "group": "annual_crop", "unit": "kg/ha de grão; t",
        "status": "PAM_CLIMA_CENARIO_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "safra das águas/seca/inverno", "calendário", "chuva/temperatura/água no solo",
                   "SAR VV/VH por fase"),
        "blockers": ("safras do feijão precisam de calendário e rótulos separados para evitar mistura de ciclos",),
    },
    "Citros": {
        "group": "perennial_crop", "unit": "kg/ha de laranja; t",
        "status": "PAM_CLIMA_CENARIO_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "idade/porta-enxerto", "cultivar", "chuva/temperatura/água no solo", "SAR VV/VH por fase"),
        "blockers": ("idade, variedade e destino da produção não estão individualizados no PAM por pixel",),
    },
    "Cana-de-açúcar": {
        "group": "annual_crop", "unit": "t/ha de colmos frescos; t",
        "status": "PAM_CLIMA_EXPERIMENTAL_SEM_PAINEL_PROPRIO",
        "equation": "baseline_PAM + resposta_climatica_por_tercis + efeito_condicional_de_vigor",
        "inputs": ("PAM N9", "cana-planta ou soca", "data do corte", "idade da soca", "Tmin/Tmax/chuva",
                   "água no solo", "SAR VV/VH"),
        "blockers": ("cana-planta/soca e data de corte necessárias para ciclo compatível"),
    },
    "Pastagens": {
        "group": "forage", "unit": "kg MS/ha por período e t MS/ha",
        "status": "MODELO_FORRAGEIRO_REQUER_COEFICIENTES_E_MANEJO",
        "equation": "MS=f(graus-dia,unidade_fototermica,agua,radiacao,especie,manejo,cortes/pastejo)",
        "inputs": ("espécie/cultivar forrageira", "altura e massa seca de referência", "pastejo/corte e lotação",
                   "temperatura/radiação/chuva", "água no solo", "SAR temporal"),
        "blockers": ("PAM não fornece rendimento de forragem; produção pecuária não equivale a biomassa de pasto"),
    },
    "Silvicultura": {
        "group": "planted_forest", "unit": "m³/ha/ano de incremento e m³/ha por idade de corte",
        "status": "MODELO_DENDROMETRICO_REQUER_DADOS_DO_TALHAO",
        "equation": "V=f(especie,idade,site_index,area_basal,distribuicao_DAP,altura,densidade,manejo)",
        "inputs": ("espécie plantada", "idade/rotação", "DAP e altura por classe", "área basal/densidade",
                   "desbastes/corte", "SAR de estrutura/altura compatível"),
        "blockers": ("PEVS é referência regional de produção e área, não substitui idade e inventário do talhão"),
    },
    "ILP": {
        "group": "integrated_system", "unit": "saídas separadas: grão, forragem MS e produto animal",
        "status": "MODELO_ACOPLADO_REQUER_UNIDADE_E_COMPONENTES",
        "equation": "Y_sistema={Y_lavoura,Y_forragem,Y_animal}+interacoes(agua,radiacao,nutrientes,manejo)",
        "inputs": ("mesma unidade de manejo/período", "cultura e calendário", "forrageira e lotação",
                   "solo/clima", "SAR temporal de cada componente"),
        "blockers": ("não somar kg de grão, MS e produto animal nem presumir integração pela vizinhança"),
    },
    "IPF": {
        "group": "integrated_system", "unit": "saídas separadas: produto animal e madeira",
        "status": "MODELO_ACOPLADO_REQUER_UNIDADE_E_COMPONENTES",
        "equation": "Y_sistema={Y_animal,Y_madeira}+interacoes(sombra,agua,nutrientes,lotacao,manejo)",
        "inputs": ("mesma unidade/período", "rebanho e lotação", "espécies e idade das árvores",
                   "inventário florestal", "SAR de dossel e pastagem"),
        "blockers": ("não inferir sistema silvipastoril apenas pela coexistência espacial de árvores e pasto"),
    },
    "ILPF": {
        "group": "integrated_system", "unit": "saídas separadas: grão, forragem MS, produto animal e madeira",
        "status": "MODELO_ACOPLADO_REQUER_UNIDADE_E_COMPONENTES",
        "equation": "Y_sistema={Y_lavoura,Y_forragem,Y_animal,Y_madeira}+interacoes(agua,radiacao,nutrientes,manejo)",
        "inputs": ("mesma unidade/período", "cultura e calendário", "forrageira/lotação", "espécie/idade arbórea",
                   "inventário de árvores", "SAR temporal de todos os estratos"),
        "blockers": ("não somar produtos de unidades diferentes nem classificar integração sem evidência de manejo"),
    },
}

PAM_CLIMATE_SCENARIO_CROPS = frozenset(("Arroz", "Algodão", "Sorgo", "Cana-de-açúcar",
                                        "Café", "Feijão", "Citros"))

ALIASES = {
    "pastagem": "Pastagens", "pastagens": "Pastagens", "pasto": "Pastagens",
    "floresta plantada": "Silvicultura", "florestas plantadas": "Silvicultura",
    "silvicultura": "Silvicultura", "ilp": "ILP", "ipf": "IPF", "ilpf": "ILPF",
}


def priority_target(label):
    raw = str(label or "").strip()
    return ALIASES.get(raw.casefold(), raw)


def model_contract(target):
    name = priority_target(target)
    route = TARGETS.get(name)
    if route is None:
        return {"target": name, "status": "N/D", "reason": "fora da lista de produção prioritária"}
    return {"target": name, **route, "inputs": list(route["inputs"]),
            "blockers": list(route.get("blockers", ())) }


def estimate_forage_dry_matter(daily, *, rue_g_mj, rue_sd_g_mj=None):
    """Estimate accumulated forage dry matter from supplied daily inputs.

    Required daily keys: ``par_mj_m2``, ``fipar`` (0..1), ``water_stress``
    (0..1). RUE is an explicit site/species parameter, never silently defaulted.
    Output is kg DM/ha for the supplied period. Uncertainty is unmeasurable
    unless an independently supported RUE standard deviation is provided.
    """
    if not daily or rue_g_mj is None or float(rue_g_mj) <= 0:
        return {"status": "N/D", "reason": "série diária e RUE positiva da espécie/local são obrigatórias",
                "uncertainty": "incerteza não mensurável"}
    total = 0.0
    for row in daily:
        try:
            par, fipar, water = (float(row[k]) for k in ("par_mj_m2", "fipar", "water_stress"))
        except (KeyError, TypeError, ValueError):
            return {"status": "N/D", "reason": "PAR, fIPAR e estresse hídrico são obrigatórios em cada dia",
                    "uncertainty": "incerteza não mensurável"}
        if par < 0 or not 0 <= fipar <= 1 or not 0 <= water <= 1:
            return {"status": "N/D", "reason": "entrada diária fora dos limites físicos",
                    "uncertainty": "incerteza não mensurável"}
        total += 10.0 * par * float(rue_g_mj) * fipar * water
    out = {"status": "experimental", "dry_matter_kg_ha": total,
           "period_days": len(daily), "rue_g_mj": float(rue_g_mj),
           "method": "Σ(10 × PAR × RUE × fIPAR × fágua)",
           "uncertainty": "incerteza não mensurável"}
    if rue_sd_g_mj is not None and float(rue_sd_g_mj) >= 0:
        sd = total * float(rue_sd_g_mj) / float(rue_g_mj)
        out.update({"rue_sd_g_mj": float(rue_sd_g_mj), "sd_from_rue_kg_ha": sd,
                    "uncertainty": "parcial: apenas erro de RUE; demais fontes não propagadas"})
    return out


def estimate_wood_increment(start_volume_m3_ha, end_volume_m3_ha, elapsed_years,
                            *, start_sd=None, end_sd=None):
    """Annualized standing-volume increment from two inventory measurements."""
    try:
        v0, v1, years = map(float, (start_volume_m3_ha, end_volume_m3_ha, elapsed_years))
    except (TypeError, ValueError):
        return {"status": "N/D", "reason": "dois inventários e intervalo são obrigatórios",
                "uncertainty": "incerteza não mensurável"}
    if v0 < 0 or v1 < 0 or years <= 0:
        return {"status": "N/D", "reason": "volumes não negativos e intervalo positivo são obrigatórios",
                "uncertainty": "incerteza não mensurável"}
    increment = (v1 - v0) / years
    out = {"status": "experimental", "annual_volume_increment_m3_ha_yr": increment,
           "standing_volume_change_m3_ha": v1 - v0, "elapsed_years": years,
           "uncertainty": "incerteza não mensurável"}
    if start_sd is not None and end_sd is not None and float(start_sd) >= 0 and float(end_sd) >= 0:
        out["sd_m3_ha_yr"] = (float(start_sd)**2 + float(end_sd)**2)**0.5 / years
        out["uncertainty"] = "parcial: erros dos inventários tratados como independentes"
    return out


def integrated_system_components(components):
    """Keep ILP/IPF/ILPF yields as a typed component vector; never sum units."""
    if not isinstance(components, dict) or not components:
        return {"status": "N/D", "reason": "componentes e unidades da unidade de manejo são obrigatórios",
                "system_interaction": "N/D", "uncertainty": "incerteza não mensurável"}
    valid = {str(k): v for k, v in components.items()
             if isinstance(v, dict) and v.get("value") is not None and v.get("unit")}
    if not valid:
        return {"status": "N/D", "reason": "nenhum componente tem valor e unidade explícitos",
                "system_interaction": "N/D", "uncertainty": "incerteza não mensurável"}
    return {"status": "experimental_components_only", "components": valid,
            "system_interaction": "N/D — requer experimento/coeficientes do sistema integrado",
            "uncertainty": "incerteza não mensurável"}
