"""Crop-aware display units for validated crop yield and production estimates."""
from __future__ import annotations
import unicodedata

# Brazilian official crop reports and CONAB commodity tables commonly express
# these grain/bean yields as 60 kg sacks. Sugarcane and citrus remain t/ha.
SACK_60_CROPS = {
    "soja": ("Soja", "IBGE LSPA: https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/9767-asi-pam-2013-com-precos-convidativos-brasil-tem-mais-uma-safra-recorde-de-graos-em-2013"),
    "milho": ("Milho", "IBGE LSPA: https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/30721-em-abril-ibge-preve-safra-de-264-5-milhoes-de-toneladas-para-2021"),
    "cafe": ("Café em grão", "IBGE LSPA: https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/44449-em-agosto-ibge-preve-safra-de-341-2-milhoes-de-toneladas-para-2025"),
    "arroz": ("Arroz em casca", "Embrapa/IBGE: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1122648/1/Cap13-EvolucaoProducaoArroz.pdf (confirmar padrão comercial regional)"),
    "feijao": ("Feijão em grão", "IBGE LSPA: https://ftp.ibge.gov.br/Producao_Agricola/Levantamento_Sistematico_da_Producao_Agricola_%5Bmensal%5D/Fasciculo/2017/lspa_201709.pdf"),
    "sorgo": ("Sorgo em grão", "CONAB unidade de comercialização 60 kg: https://www.conab.gov.br/info-agro/precos/receita-bruta-dos-produtos-brasileiros/item/download/1621_4ffe0c63c59b35e36e8511a5d322b060"),
    "trigo": ("Trigo", "CONAB unidade de comercialização 60 kg: https://portaldecomercializacao.conab.gov.br/"),
}


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def sack_standard(crop):
    key = _norm(crop)
    for token, (label, source) in SACK_60_CROPS.items():
        if token in key:
            return {"crop_label": label, "kg_per_sack": 60.0, "source_basis": source}
    return None


def probable_productivity(yield_t_ha, crop):
    """Return value, unit and explicit conversion basis; input is metric t/ha."""
    value = float(yield_t_ha)
    if value < 0:
        raise ValueError("yield cannot be negative")
    standard = sack_standard(crop)
    if standard is None:
        return {"value": value, "unit": "t/ha", "conversion": None}
    return {"value": value * 1000.0 / standard["kg_per_sack"],
            "unit": "sacas/ha", "conversion": standard}


def probable_production(yield_t_ha, area_ha, crop):
    """Return total crop production over mapped crop area inside the AOI."""
    yield_t_ha, area_ha = float(yield_t_ha), float(area_ha)
    if yield_t_ha < 0 or area_ha < 0:
        raise ValueError("yield and crop area cannot be negative")
    tonnes = yield_t_ha * area_ha
    standard = sack_standard(crop)
    return {"value_t": tonnes,
            "sacks": tonnes * 1000.0 / standard["kg_per_sack"] if standard else None,
            "conversion": standard}
