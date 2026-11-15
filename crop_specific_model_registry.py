"""Scientific crop-specific model selection and remote-sensing feature contract.

This registry deliberately does NOT implement or assert that DSSAT, APSIM,
ORYZA or fruit-tree models are executable. It defines crop-appropriate
inputs/physics and an explicit integration gate for future calibrated
adapters, so a generic PAN forecast cannot be misrepresented as crop-specific.

Provenance:
DSSAT species/modules https://dssat.net/plant-growth-modules-in-dssat-csm/
FAO AquaCrop https://www.fao.org/aquacrop/en
APSIM sugarcane https://builds.apsim.info/api/nextgen/docs/Sugarcane.pdf
IRRI ORYZA https://sites.google.com/view/oryzamodel/home
Coffee doi:10.1016/j.agsy.2024.104181 and doi:10.1590/S0100-204X2018001200002
Oranges doi:10.1590/S0103-90162007000100001
Radar rice doi:10.1016/j.rsase.2024.101435

Do not use radar proxies as measured leaf area, canopy health, or grain yield;
calibration of crop × stage × orbit/incidence × region is mandatory.
"""
from __future__ import annotations

MODEL_REGISTRY = {
    "Soja": {
        "mechanistic": "DSSAT CROPGRO-Soybean", "family": "leguminosa anual",
        "critical_stages": ("floração R1–R2", "formação de vagens R3–R4", "enchimento R5–R6"),
        "sar_features": ("VH/VV temporal", "RVI calibrado", "textura e uniformidade", "mudança entre cenas"),
        "climate_features": ("ETa/ETc em R1–R6", "dias de calor reprodutivo", "radiação", "água disponível"),
        "yield_basis": "grão seco t/ha e sacas de 60 kg/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
    },
    "Milho": {
        "mechanistic": "DSSAT CERES-Maize / IXIM-Maize", "family": "cereal C4 anual",
        "critical_stages": ("crescimento vegetativo", "pendoamento VT", "florescimento R1", "enchimento R2–R5"),
        "sar_features": ("VH/VV temporal", "textura por dossel", "uniformidade", "mudança de fase"),
        "climate_features": ("graus-dia", "déficit hídrico VT–R1", "calor na polinização", "radiação"),
        "yield_basis": "grão t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
    },
    "Sorgo": {
        "mechanistic": "DSSAT CERES-Sorghum", "family": "cereal C4 anual",
        "critical_stages": ("estabelecimento", "diferenciação floral", "emissão de panícula", "enchimento"),
        "sar_features": ("VH/VV temporal", "textura", "mudança de fase", "uniformidade"),
        "climate_features": ("graus-dia", "déficit por estádio", "calor na floração", "água no solo"),
        "yield_basis": "grão t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
    },
    "Feijão": {
        "mechanistic": "DSSAT CROPGRO-Drybean", "family": "leguminosa anual",
        "critical_stages": ("floração", "formação de vagens", "enchimento de grãos"),
        "sar_features": ("VH temporal", "RVI calibrado", "uniformidade", "mudança entre cenas"),
        "climate_features": ("ETa/ETc na floração", "calor", "excesso hídrico", "temperatura"),
        "yield_basis": "grão seco t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
    },
    "Arroz": {
        "mechanistic": "IRRI ORYZA v3 / DSSAT CERES-Rice", "family": "cereal inundável ou sequeiro",
        "critical_stages": ("semeadura/transplante", "perfilhamento", "emborrachamento", "panícula", "enchimento"),
        "sar_features": ("VH/VV temporal", "mínimo de retroespalhamento da inundação", "inclinação VH", "padrão de dupla reflexão"),
        "climate_features": ("regime de inundação", "temperatura noturna", "radiação", "água e nitrogênio"),
        "yield_basis": "arroz em casca t/ha",
        "source": "https://sites.google.com/view/oryzamodel/home",
    },
    "Cana-de-açúcar": {
        "mechanistic": "APSIM-Sugarcane / DSSAT CANEGRO", "family": "gramínea perene de cortes",
        "critical_stages": ("brotação", "perfilhamento", "crescimento dos colmos", "maturação", "soca"),
        "sar_features": ("VH temporal", "mudança de colmos/dossel", "textura", "data de corte"),
        "climate_features": ("radiação interceptada", "eficiência do uso da radiação", "água", "temperatura", "idade da soca"),
        "yield_basis": "colmos frescos t/ha; ATR é variável distinta",
        "source": "https://builds.apsim.info/api/nextgen/docs/Sugarcane.pdf",
    },
    "Algodão": {
        "mechanistic": "DSSAT CROPGRO-Cotton", "family": "fibra anual",
        "critical_stages": ("botões florais", "florescimento", "formação de maçãs", "abertura"),
        "sar_features": ("VH/VV temporal", "textura", "uniformidade", "mudança de fase"),
        "climate_features": ("temperatura acumulada", "calor reprodutivo", "déficit", "radiação"),
        "yield_basis": "algodão em caroço t/ha; pluma exige fator de beneficiamento observado",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
    },
    "Café": {
        "mechanistic": "Regressão agrometeorológica fenológica brasileira / bienalidade Arábica; calibrar Conilon separadamente",
        "family": "arbórea perene",
        "critical_stages": ("indução floral", "florada", "pegamento", "granação", "maturação"),
        "sar_features": ("VH/VV temporal com sensibilidade limitada", "textura/estrutura", "mudança sazonal multianual"),
        "climate_features": ("déficit por fenofase", "temperatura e radiação", "produção do ano anterior", "bienalidade", "irrigação"),
        "yield_basis": "café beneficiado t/ha; sacas de 60 kg/ha quando produto compatível",
        "source": "https://doi.org/10.1016/j.agsy.2024.104181",
    },
    "Citros": {
        "mechanistic": "Regressão fenológica laranja Valencia/Hamlin (frutos/planta)", "family": "arbórea perene",
        "critical_stages": ("fluxo vegetativo", "pré-floração", "florescimento", "pegamento", "crescimento dos frutos"),
        "sar_features": ("VH/VV temporal com sensibilidade limitada", "textura/estrutura persistente"),
        "climate_features": ("chuvas e temperaturas por fenofase", "idade pomar", "irrigação", "calibre e peso de frutos"),
        "yield_basis": "frutos/planta -> t/ha só com densidade de plantas e massa média do fruto",
        "source": "https://doi.org/10.1590/S0103-90162007000100001",
    },
}

# Models actually trained and packaged in the current Enform Verde (PAM + FAO
# balance) are separate from the mechanistic candidates above.
CURRENT_CALIBRATED_PANEL = frozenset(("Soja", "Milho"))


def model_contract(crop):
    """Return architecture without claiming a third-party solver was executed."""
    if crop not in MODEL_REGISTRY:
        return {"status": "N/D", "reason": "cultura sem módulo específico pesquisado"}
    r = MODEL_REGISTRY[crop]
    return {"status": "research_backed_not_integrated",
            "crop": crop, "recommended_model": r["mechanistic"],
            "phenological_stages": list(r["critical_stages"]),
            "sar_features": list(r["sar_features"]),
            "climate_features": list(r["climate_features"]),
            "yield_basis": r["yield_basis"], "source": r["source"],
            "existing_panel_available": crop in CURRENT_CALIBRATED_PANEL,
            "warning": ("Modelo científico identificado, porém solver não integrado nem calibrado "
                        "para a AOI. O painel PAM/FAO existente não equivale a esse modelo. "
                        "SAR só entra no rendimento quando houve validação da relação observada.")}
