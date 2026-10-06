"""Hierarchical national AGB fallback for Enform Verde.

This module is intentionally conservative. It is used only after the configured
SAR/direct biomass routes have been exhausted or processed SAR pixels have no
compatible quantitative AGB model. Values are Brazilian published evidence,
selected by biome + physiognomy keywords. They are never represented as SAR.

Uncertainty rule:
- use published CI directly when the source supplies it;
- otherwise use published SD/IQR/range and expose the exact kind;
- when several heterogeneous studies are pooled, use a robust median and a
  transfer envelope that covers the source-specific uncertainty/range.
The transfer envelope is an operational uncertainty bound, not a confidence
interval for the target AOI.
"""
import math
import statistics

SUPPORTED_BIOMES=("Amazônia","Cerrado","Caatinga","Mata Atlântica","Pantanal")

def _norm(x):
    return str(x or "").casefold().replace("ã","a").replace("á","a").replace("â","a").replace("é","e").replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o").replace("õ","o").replace("ú","u").replace("ç","c")

def _aoi_distance_km(aoi, lon, lat):
    if aoi is None:
        return None
    try:
        from pyproj import Geod
        c=aoi.to_crs("EPSG:4326").geometry.union_all().centroid
        _,_,d=Geod(ellps="WGS84").inv(float(c.x),float(c.y),float(lon),float(lat))
        return abs(float(d))/1000.0
    except Exception:
        return None

def _record(center, low, high, source, url, basis, n=None, uncertainty_kind="envelope de transferência"):
    center=float(center); low=max(0.0,float(low)); high=max(center,float(high))
    return {"center":center,"low":low,"high":high,"source":source,"url":url,"basis":basis,
            "n":n,"uncertainty_kind":uncertainty_kind}

def _robust_pool(records, label):
    centers=[r["center"] for r in records]
    center=float(statistics.median(centers))
    lows=[r["low"] for r in records]; highs=[r["high"] for r in records]
    if len(centers)>=3:
        mad=statistics.median([abs(x-center) for x in centers])
        robust_sigma=1.4826*mad
        robust_low=max(0.0,center-1.96*robust_sigma)
        robust_high=center+1.96*robust_sigma
        low=min(min(lows),robust_low); high=max(max(highs),robust_high)
        stat=f"mediana robusta de {len(records)} referências; MAD×1,4826 e envelope das fontes"
    else:
        low=min(lows); high=max(highs)
        stat=f"mediana de {len(records)} referências e envelope das fontes"
    return {"center":center,"low":low,"high":high,"stat":stat,"label":label,"records":records}

_NO_COVERAGE_MARKERS = (
    "sem pixels", "no pixels", "sem cena", "sem cenas", "no scene", "no scenes",
    "nenhuma cena", "nenhum produto", "sem produto", "no products", "no items",
    "sem cobertura", "no coverage", "sem resultados", "empty result",
)

def inventory_fallback_gate(sar_processed, warnings=()):
    """Permit inventory/literature AGB only after confirmed SAR unavailability.

    Unknown warnings are treated as unresolved technical/access failures and
    block fallback; processed SAR pixels or a valid SAR height product always
    block the non-SAR estimate.
    """
    warning_list=[str(w) for w in (warnings or ())]
    if sar_processed:
        return {"eligible":False,"reason":"SAR foi processado; fallback não-SAR não pode substituir AGB SAR ausente.",
                "unresolved_warnings":[],"evidence":"observável SAR processado"}
    unresolved=[w for w in warning_list
                if not any(marker in w.casefold() for marker in _NO_COVERAGE_MARKERS)]
    if unresolved:
        return {"eligible":False,"reason":"falha técnica/acesso não resolvida; ausência de SAR ainda não foi comprovada.",
                "unresolved_warnings":unresolved,"evidence":"avisos que exigem resolução"}
    return {"eligible":True,"reason":"rotas SAR consultadas sem falha técnica pendente e sem observáveis/pixels utilizáveis.",
            "unresolved_warnings":[],"evidence":"ausência operacional de cobertura/processamento confirmada"}

def national_agb_fallback(biome, physiognomy, aoi=None):
    """Return a mandatory modelled AGB estimate for the four scoped Brazilian biomes.

    The caller must only invoke this after SAR/direct-product routes are exhausted.
    It is deliberately broad outside well-studied strata and must remain labelled
    as MODELAGEM_LITERATURA, never as pixel-wise SAR.
    """
    b=_norm(biome); p=_norm(physiognomy)
    rec=[]; label=""

    if "caatinga" in b:
        # 70 field sites: median 43, IQR 25–61, empirical range 5–118 Mg/ha.
        # Robust 95%-equivalent spread from IQR: sigma ~= IQR/1.349.
        q1,q3=25.0,61.0; med=43.0; sigma=(q3-q1)/1.349
        lo=max(5.0,med-1.96*sigma); hi=min(118.0,med+1.96*sigma)
        rec=[_record(med,lo,hi,
          "Castanho et al. (2020), A close look at above ground biomass of a large and heterogeneous Seasonally Dry Tropical Forest — Caatinga in North East of Brazil",
          "https://www.scielo.br/j/aabc/a/5ddbcBL7kk4QDFGJz6JLtGP/?lang=en",
          "70 sítios de campo; mediana 43 Mg/ha; IQR 25–61; faixa observada 5–118 Mg/ha",
          n=70,uncertainty_kind="faixa robusta operacional derivada do IQR, limitada pela faixa empírica; não é IC95% do alvo")]
        label="Caatinga — síntese de campo multi-sítio"
        if any(k in p for k in ("floresta montana","montanh","evergreen","perenif")):
            rec.append(_record(80,40,118,"Castanho et al. (2020)","https://www.scielo.br/j/aabc/a/5ddbcBL7kk4QDFGJz6JLtGP/?lang=en",
                               "fisionomias mais úmidas/montanas no estudo; grande heterogeneidade",uncertainty_kind="envelope fitofisionômico observado"))

    elif "cerrado" in b:
        d_df=_aoi_distance_km(aoi,-47.93,-15.95)
        if d_df is not None and d_df <= 100.0 and not "cerradao" in p:
            rec=[_record(16.55,7.95,25.15,
                  "Oliveira et al. (2024), Artificial Neural Network and Remote Sensing combined to predict the Aboveground Biomass in the Cerrado biome",
                  "https://doi.org/10.1590/0001-3765202420221041",
                  "Distrito Federal; inventário de campo + sensoriamento remoto; média 16,55 ± 8,6 Mg/ha",
                  uncertainty_kind="média ± DP publicada no estudo local; não é IC95% da AOI")]
            label="Cerrado — referência microrregional do Distrito Federal"
        else:
            rec=[]
        base=[
          _record(16.55,7.95,25.15,"Oliveira et al. (2024), An. Acad. Bras. Ciênc. 96(3):e20221041",
                  "https://www.scielo.br/j/aabc/a/ydXCX3FjW5TzrWMWF9sZBhk/?lang=en",
                  "inventário/modelagem no Distrito Federal; média 16,55 ± 8,6 Mg/ha",uncertainty_kind="média ± DP publicada"),
          _record(18.66,7.0,35.0,"Bispo et al. (2020), Remote Sensing 12:2685",
                  "https://doi.org/10.3390/rs12172685",
                  "Rio Vermelho/GO; referência brasileira multissensor, média reportada 18,66 Mg/ha",uncertainty_kind="envelope de transferência conservador"),
          _record(19.72,8.0,40.0,"Costa et al. (2021), áreas protegidas do Cerrado, síntese citada por Oliveira et al. (2024)",
                  "https://www.scielo.br/j/aabc/a/ydXCX3FjW5TzrWMWF9sZBhk/?lang=en",
                  "média reportada 19,72 Mg/ha em áreas protegidas",uncertainty_kind="envelope de transferência conservador")]
        if "cerradao" in p:
            rec=[_record(61.0,40.0,82.0,"Delitti et al. (2006), Biomass and mineralmass estimates in a cerrado ecosystem",
                         "https://doi.org/10.1590/S0100-84042006000400003",
                         "síntese por fisionomia; cerradão ~61 Mg/ha",uncertainty_kind="envelope de transferência fitofisionômica")]
            label="Cerradão — referência fitofisionômica"
        elif any(k in p for k in ("campo sujo","campo limpo","cerrado ralo","campo cerrado","savana gram")):
            rec=[_record(14.8,5.9,32.8,"Delitti et al. (2006), Biomass and mineralmass estimates in a cerrado ecosystem",
                         "https://doi.org/10.1590/S0100-84042006000400003",
                         "compilação brasileira: campo sujo/campo cerrado/cerrado aberto com ampla variação",uncertainty_kind="envelope empírico entre fisionomias abertas comparáveis")]
            label="Cerrado aberto/ralo — referência fitofisionômica"
        elif not rec:
            rec=base; label="Cerrado — síntese brasileira multiestudo"

    elif "mata atlantica" in b:
        if any(k in p for k in ("secund","regener","restaur")):
            rec=[_record(175.6,94.3,256.9,
                  "Pyles et al. (2024), Carbon stock in aboveground biomass and necromass in the Atlantic Forest",
                  "https://www.scielo.br/j/aabc/a/sKrrTS6D4BDStCmWZxn6vft/?lang=en",
                  "revisão 2000–2021; florestas secundárias 175,6 ± 81,3 Mg/ha",
                  uncertainty_kind="média ± DP entre estudos; não é IC95% da AOI")]
            label="Mata Atlântica — floresta secundária"
        elif any(k in p for k in ("madura","primaria","avancad")):
            rec=[_record(267.0,181.2,352.8,
                  "Pyles et al. (2024), Carbon stock in aboveground biomass and necromass in the Atlantic Forest",
                  "https://www.scielo.br/j/aabc/a/sKrrTS6D4BDStCmWZxn6vft/?lang=en",
                  "revisão 2000–2021; florestas maduras 267 ± 85,8 Mg/ha",
                  uncertainty_kind="média ± DP entre estudos; não é IC95% da AOI")]
            label="Mata Atlântica — floresta madura"
        elif "semidecid" in p:
            d_vicosa=_aoi_distance_km(aoi,-42.88,-20.75)
            rec=[
              _record(74.3,62.8,85.8,"Torres et al. (2024), Biomass Equations and Carbon Stock Estimates for the Southeastern Brazilian Atlantic Forest",
                      "https://doi.org/10.3390/f15091568",
                      "IFN-RJ, Floresta Estacional Semidecidual; 63 UAs; 74,3 ± 11,5 Mg/ha (IC publicado)",
                      n=63,uncertainty_kind="IC publicado para o estrato estadual; transferência para outra AOI amplia o envelope"),
              _record(181.48,103.67,259.29,"Amaro et al. / estudo de Viçosa (2013), estoque de biomassa em Floresta Estacional Semidecidual",
                      "https://www.scielo.br/j/rarv/a/4qcwXR4kPDwGnkDGQzmmLHK/?lang=pt",
                      "15 parcelas; AGB total 181,48 Mg/ha; DP do total de biomassa usado apenas como limite conservador de transferência",
                      n=15,uncertainty_kind="envelope conservador de transferência; não é IC da AGB")]
            if d_vicosa is not None and d_vicosa <= 100.0:
                label="Mata Atlântica — Floresta Estacional Semidecidual, referência microrregional Viçosa/MG"
            else:
                label="Mata Atlântica — Floresta Estacional Semidecidual"
        else:
            rec=[_record(218.0,123.8,312.2,
                  "Pyles et al. (2024), Carbon stock in aboveground biomass and necromass in the Atlantic Forest",
                  "https://www.scielo.br/j/aabc/a/sKrrTS6D4BDStCmWZxn6vft/?lang=en",
                  "revisão 2000–2021; total 218 ± 94,2 Mg/ha",
                  uncertainty_kind="média ± DP entre estudos; não é IC95% da AOI")]
            label="Mata Atlântica — síntese ampla"

    elif "pantanal" in b:
        # Local field evidence from the Southeast Pantanal (Barros et al., 2022).
        # Only two classes with numeric means and reported dispersion are enabled;
        # the paper's other classes are not assigned values from the abstract.
        # Values are aboveground carbon (Mg C/ha), converted to dry biomass with
        # the app's explicit operational carbon fraction. The source does not
        # identify whether ± is SD or SE, so it is carried as a descriptive
        # envelope and never presented as an AOI confidence interval.
        if any(k in p for k in ("floresta riparia","floresta ripária","mata ciliar","floresta ciliar")):
            carbon_mean, carbon_spread = 184.1, 42.0
            class_label = "floresta ripária"
        elif any(k in p for k in ("savana gramineo-lenhosa","savana gramíneo-lenhosa","gramineo-lenhosa","gramíneo-lenhosa")):
            carbon_mean, carbon_spread = 26.6, 19.1
            class_label = "savana gramíneo-lenhosa"
        else:
            return None
        fraction=0.47
        mean=carbon_mean/fraction
        spread=carbon_spread/fraction
        rec=[_record(mean,max(0.0,mean-spread),mean+spread,
             "Barros et al. (2022), Aboveground carbon stock in phytophysiognomies of the Southeast Pantanal, Brazil",
             "https://doi.org/10.1007/s40415-022-00808-1",
             f"estoque de C publicado para {class_label}: {carbon_mean} ± {carbon_spread} Mg C/ha; convertido em biomassa seca com fração C operacional {fraction}; dispersão ± sem tipo especificado no resumo",
             uncertainty_kind="dispersão publicada ± (tipo não informado no resumo), convertida por fração C operacional; envelope descritivo, não IC95% do alvo")]
        label=f"Pantanal sudeste — {class_label}; transferência espacial restrita ao domínio do estudo"
        if aoi is not None:
            # Evidence is geographically limited to southeast Pantanal; do not
            # export this fallback to the whole biome on a biome label alone.
            d=_aoi_distance_km(aoi,-57.7,-19.5)
            if d is not None and d>200.0:
                return None

    elif "amazonia" in b:
        if "floresta ombrofila aberta" in p or "floresta aberta" in p:
            rec=[_record(313.0,288.0,346.0,"Cummings et al. (2002), Forest Ecology and Management 163:293–307",
                         "https://doi.org/10.1016/S0378-1127(01)00587-4",
                         "20 sítios no sudoeste da Amazônia brasileira; floresta aberta 288–346, média 313 Mg/ha",
                         uncertainty_kind="faixa empírica publicada; transferência regional")]
            label="Amazônia — Floresta Ombrófila Aberta"
        elif "floresta ombrofila densa" in p or "floresta densa" in p:
            rec=[
              _record(377.0,298.0,533.0,"Cummings et al. (2002), Forest Ecology and Management 163:293–307",
                      "https://doi.org/10.1016/S0378-1127(01)00587-4",
                      "sudoeste da Amazônia brasileira; floresta densa 298–533, média 377 Mg/ha",
                      uncertainty_kind="faixa empírica publicada; transferência regional"),
              _record(397.7,367.7,427.7,"Laurance et al. (2001/2002), Total aboveground biomass in central Amazonian rainforests",
                      "https://doi.org/10.1016/S0378-1127(01)00749-6",
                      "20 parcelas de terra firme na Amazônia Central; média 397,7 ± 30,0 Mg/ha",
                      n=20,uncertainty_kind="média ± dispersão publicada; transferência regional")
            ]
            label="Amazônia — Floresta Ombrófila Densa/terra firme"
        else:
            rec=[_record(174.0,72.0,276.0,
                  "Longo et al. (2023), A biomass map of the Brazilian Amazon from multisource remote sensing, Scientific Data",
                  "https://www.nature.com/articles/s41597-023-02575-4",
                  "mapa EBA calibrado/validado com inventários e ALS; média amazônica 174 e DP 102 Mg/ha",
                  uncertainty_kind="média ± 1 DP espacial do produto; usado como limite de transferência, não como incerteza pixel a pixel")]
            label="Amazônia — fallback amplo EBA"

    else:
        return None

    pooled=_robust_pool(rec,label)
    return {
      "available":True,
      "agb_mg_ha":pooled["center"],
      "agb_range_mg_ha":[pooled["low"],pooled["high"]],
      "uncertainty_mg_ha":max(pooled["center"]-pooled["low"],pooled["high"]-pooled["center"]),
      "uncertainty_kind":"limite de incerteza operacional por "+pooled["stat"]+"; não é validação SAR nem IC95% universal da AOI",
      "data_origin":"MODELAGEM_LITERATURA_HIERARQUICA",
      "method":"fallback hierárquico obrigatório após esgotamento das rotas SAR/produtos espaciais; seleção por bioma + fitofisionomia e síntese robusta das referências brasileiras/regionais disponíveis",
      "source":"; ".join(dict.fromkeys(r["source"] for r in rec)),
      "url":"; ".join(dict.fromkeys(r["url"] for r in rec)),
      "n_sources":len(rec),
      "evidence":[dict(r) for r in rec],
      "sar_processed":False,
      "sar_metrics":{"RMSE":None,"MAE":None,"bias":None,"R2":None},
      "limits":[
        "estimativa modelada secundária; não é biomassa SAR por pixel",
        "a faixa incorpora heterogeneidade entre estudos e transferência ecológica/espacial",
        "quanto menor a proximidade regional/fitofisionômica, maior deve ser a interpretação conservadora do envelope",
        "substituir por calibração local/parcela–pixel assim que dados independentes adequados estiverem disponíveis"
      ],
      "note":"AGB fornecida obrigatoriamente como fallback modelado com limite de incerteza explícito."
    }
