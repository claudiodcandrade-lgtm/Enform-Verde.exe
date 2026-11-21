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
        "embrapa_evidence": {
            "route": "PlanetScope temporal + EVI2 (estudo de monitoramento de soja); modelo agrometeorológico regionalizado como referência independente",
            "scope": "experimento/áreas de pesquisa no Brasil; não é modelo nacional transferível",
            "status": "publicado_experimental_sem_solver_empacotado",
            "source_urls": ["https://www.embrapa.br/pt/agencia-de-noticias-embrapa/busca-de-noticias/-/noticia/102906472/modelo-preve-produtividade-agricola-com-uso-de-imagens-de-satelite", "https://apct.sede.embrapa.br/pab/pt_BR/article/view/7609"],
            "limitation": "a notícia informa 71% de acerto no estudo com soja, mas não fornece n nem intervalo para aplicação externa; exigir validação por talhão/região antes de integrar",
        },
    },
    "Milho": {
        "mechanistic": "DSSAT CERES-Maize / IXIM-Maize", "family": "cereal C4 anual",
        "critical_stages": ("crescimento vegetativo", "pendoamento VT", "florescimento R1", "enchimento R2–R5"),
        "sar_features": ("VH/VV temporal", "textura por dossel", "uniformidade", "mudança de fase"),
        "climate_features": ("graus-dia", "déficit hídrico VT–R1", "calor na polinização", "radiação"),
        "yield_basis": "grão t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
        "embrapa_evidence": {
            "route": "modelo agrometeorológico nacional com produtividade potencial/atingível condicionada ao nível tecnológico",
            "scope": "avaliação brasileira em várias regiões e safras 2000/01–2007/08",
            "status": "publicado_com_avaliacao_original; coeficientes e protocolo precisam de auditoria antes de reimplementar",
            "source_urls": ["https://apct.sede.embrapa.br/pab/pt_BR/article/view/23530"],
            "reported_metrics": "R² 0,76–0,92; MRE −0,9 a 2,4%; MAE <70 kg/ha nos níveis tecnológicos avaliados",
            "limitation": "não equivale à previsão do talhão atual e não inclui vigor SAR do Enform",
        },
    },
    "Sorgo": {
        "mechanistic": "DSSAT CERES-Sorghum", "family": "cereal C4 anual",
        "critical_stages": ("estabelecimento", "diferenciação floral", "emissão de panícula", "enchimento"),
        "sar_features": ("VH/VV temporal", "textura", "mudança de fase", "uniformidade"),
        "climate_features": ("graus-dia", "déficit por estádio", "calor na floração", "água no solo"),
        "yield_basis": "grão t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
        "embrapa_evidence": {
            "route": "Agritec/Zarc fornece recomendações de época e cultivar; previsão quantitativa de produtividade não localizada para sorgo na documentação consultada",
            "scope": "Zarc nacional; sem modelo de produtividade identificado nesta revisão",
            "status": "lacuna_de_modelo_quantitativo_embrapa",
            "source_urls": ["https://www.portal.agroapi.cnptia.embrapa.br/api-docs/agritec/v2"],
            "limitation": "não converter Zarc, vigor ou analogia com milho em produtividade de sorgo",
        },
    },
    "Feijão": {
        "mechanistic": "DSSAT CROPGRO-Drybean", "family": "leguminosa anual",
        "critical_stages": ("floração", "formação de vagens", "enchimento de grãos"),
        "sar_features": ("VH temporal", "RVI calibrado", "uniformidade", "mudança entre cenas"),
        "climate_features": ("ETa/ETc na floração", "calor", "excesso hídrico", "temperatura"),
        "yield_basis": "grão seco t/ha",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
        "embrapa_evidence": {
            "route": "Agritec produtividade; estudo de produtividade potencial de feijão e milho baseado em modelos de processos",
            "scope": "API por município/data de plantio/cultivar/CAD; estudo potencial em mesorregiões de MG",
            "status": "servico_api_e_modelo_potencial; nao calibrado para talhao nacional",
            "source_urls": ["https://www.portal.agroapi.cnptia.embrapa.br/api-docs/agritec/v2", "https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/906455/modelos-de-estimativa-de-produtividade-potencial-para-as-culturas-do-feijao-e-do-milho"],
            "limitation": "os modelos potenciais diferiram substancialmente entre si; selecionar método e domínio com critério",
        },
    },
    "Arroz": {
        "mechanistic": "IRRI ORYZA v3 / DSSAT CERES-Rice", "family": "cereal inundável ou sequeiro",
        "critical_stages": ("semeadura/transplante", "perfilhamento", "emborrachamento", "panícula", "enchimento"),
        "sar_features": ("VH/VV temporal", "mínimo de retroespalhamento da inundação", "inclinação VH", "padrão de dupla reflexão"),
        "climate_features": ("regime de inundação", "temperatura noturna", "radiação", "água e nitrogênio"),
        "yield_basis": "arroz em casca t/ha",
        "source": "https://sites.google.com/view/oryzamodel/home",
        "embrapa_evidence": {
            "route": "Agritec produtividade; modelo agrometeorológico brasileiro por nível tecnológico; SimulArroz para arroz irrigado por inundação no RS",
            "scope": "API nacional por parâmetros de cultivo; SimulArroz calibrado para cultivares e ambiente do Sul",
            "status": "servico_api_e_modelos_de_dominios_distintos",
            "source_urls": ["https://www.portal.agroapi.cnptia.embrapa.br/api-docs/agritec/v2", "https://apct.sede.embrapa.br/pab/pt_BR/article/view/12664", "https://apct.sede.embrapa.br/pab/pt_BR/article/view/26666"],
            "limitation": "separar irrigado/sequeiro e arroz em casca; não transferir calibração do RS para outros ambientes",
        },
    },
    "Cana-de-açúcar": {
        "mechanistic": "APSIM-Sugarcane / DSSAT CANEGRO", "family": "gramínea perene de cortes",
        "critical_stages": ("brotação", "perfilhamento", "crescimento dos colmos", "maturação", "soca"),
        "sar_features": ("VH temporal", "mudança de colmos/dossel", "textura", "data de corte"),
        "climate_features": ("radiação interceptada", "eficiência do uso da radiação", "água", "temperatura", "idade da soca"),
        "yield_basis": "colmos frescos t/ha; ATR é variável distinta",
        "source": "https://builds.apsim.info/api/nextgen/docs/Sugarcane.pdf",
        "embrapa_evidence": {
            "route": "PlanetScope temporal + GNDVI e modelos estatísticos/ML para previsão durante o crescimento",
            "scope": "talhões comerciais avaliados em pesquisa Embrapa/Coplacana; artigo aberto de 2025",
            "status": "publicado_experimental_requer_calibracao_local",
            "source_urls": ["https://www.embrapa.br/busca-de-publicacoes/-/publicacao/1174128/predicting-sugarcane-yield-through-temporal-analysis-of-satellite-imagery-during-the-growth-phase", "https://www.mdpi.com/2073-4395/15/4/793"],
            "reported_metrics": "divulgação Embrapa reporta até 89% de acerto; notícia não especifica n/IC para transferência",
            "limitation": "dependente de série PlanetScope, fase de crescimento, variedade, corte/soca e calibração por região; não generalizar a partir da acurácia divulgada",
        },
    },
    "Algodão": {
        "mechanistic": "DSSAT CROPGRO-Cotton", "family": "fibra anual",
        "critical_stages": ("botões florais", "florescimento", "formação de maçãs", "abertura"),
        "sar_features": ("VH/VV temporal", "textura", "uniformidade", "mudança de fase"),
        "climate_features": ("temperatura acumulada", "calor reprodutivo", "déficit", "radiação"),
        "yield_basis": "algodão em caroço t/ha; pluma exige fator de beneficiamento observado",
        "source": "https://dssat.net/plant-growth-modules-in-dssat-csm/",
        "embrapa_evidence": {
            "route": "regressões de produtividade com séries temporais MODIS EVI/TVI",
            "scope": "281 talhões comerciais no Cerrado; 167 treino e 114 teste; janelas úteis aproximadamente 90–150 dias após semeadura",
            "status": "publicado_experimental_dominio_cerrado",
            "source_urls": ["https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/1164361/estimating-cotton-yield-in-the-brazilian-cerrado-using-linear-regression-models-from-modis-vegetation-index-time-series"],
            "reported_metrics": "melhor caso reportado: R²≈0,70 e RMSE≈750 kg/ha",
            "limitation": "algodão em caroço; exige máscara/cultura, data de semeadura e estágio; não transferir para pluma ou outras regiões sem validação",
        },
    },
    "Café": {
        "mechanistic": "Regressão agrometeorológica fenológica brasileira / bienalidade Arábica; calibrar Conilon separadamente",
        "family": "arbórea perene",
        "critical_stages": ("indução floral", "florada", "pegamento", "granação", "maturação"),
        "sar_features": ("VH/VV temporal com sensibilidade limitada", "textura/estrutura", "mudança sazonal multianual"),
        "climate_features": ("déficit por fenofase", "temperatura e radiação", "produção do ano anterior", "bienalidade", "irrigação"),
        "yield_basis": "café beneficiado t/ha; sacas de 60 kg/ha quando produto compatível",
        "source": "https://www.alice.cnptia.embrapa.br/alice/handle/doc/909323",
        "embrapa_evidence": {
            "route": "modelo agrometeorológico fenológico para monitorar quebra de produtividade; déficit hídrico por fase, extremos térmicos e produção anterior",
            "scope": "trabalhos Embrapa Café em arábica no estado de SP, com avaliações em talhão/propriedade/município; outras pesquisas em MG distinguem anos de alta/baixa bienalidade",
            "status": "publicado_com_dominio_regional_e_especie_especifica",
            "source_urls": ["https://www.alice.cnptia.embrapa.br/alice/handle/doc/909323", "https://www.embrapa.br/busca-de-publicacoes/-/publicacao/26420/previsao-de-produtividade-anual-de-cafe-arabica-por-meio-do-deficit-hidrico"],
            "limitation": "não misturar arábica e conilon; requer ano de alta/baixa, fenologia, irrigação e histórico de produção",
        },
    },
    "Citros": {
        "mechanistic": "Regressão fenológica laranja Valencia/Hamlin (frutos/planta)", "family": "arbórea perene",
        "critical_stages": ("fluxo vegetativo", "pré-floração", "florescimento", "pegamento", "crescimento dos frutos"),
        "sar_features": ("VH/VV temporal com sensibilidade limitada", "textura/estrutura persistente"),
        "climate_features": ("chuvas e temperaturas por fenofase", "idade pomar", "irrigação", "calibre e peso de frutos"),
        "yield_basis": "frutos/planta -> t/ha só com densidade de plantas e massa média do fruto",
        "source": "https://doi.org/10.1590/S0103-90162007000100001",
        "embrapa_evidence": {
            "route": "regressões agrometeorológicas para número de frutos por planta em laranja Valencia/Hamlin",
            "scope": "15 safras 1990/91–2004/05, Limeira-SP; classes de idade do pomar; dados de indústria citrícola",
            "status": "publicado_regional_variedade_especifica",
            "source_urls": ["https://www.alice.cnptia.embrapa.br/alice/handle/doc/15902", "https://www.scielo.br/j/sa/a/hDrcFPRm7wS47BqZ6sLwXvH/?lang=en"],
            "limitation": "estima frutos/planta, não t/ha; conversão exige densidade de árvores e massa média observada dos frutos",
        },
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
            "embrapa_evidence": dict(r.get("embrapa_evidence") or {}),
            "existing_panel_available": crop in CURRENT_CALIBRATED_PANEL,
            "warning": ("Modelo científico identificado, porém solver não integrado nem calibrado "
                        "para a AOI. O painel PAM/FAO existente não equivale a esse modelo. "
                        "SAR só entra no rendimento quando houve validação da relação observada.")}
