"""Readable native-carbon executive summary with honest per-pool uncertainty units."""
from __future__ import annotations

def uncertainty_for_pool(row, carbon_fraction=0.47):
    value=row.get("tc")
    if not isinstance(value,(int,float)) or value<=0:
        return {"absolute_tc_ha":None,"percent":None,"kind":"não quantificada"}
    interval=row.get("range_tc_ha")
    if isinstance(interval,(list,tuple)) and len(interval)==2:
        lo,hi=interval
        if isinstance(lo,(int,float)) and isinstance(hi,(int,float)) and lo<=hi:
            return {"absolute_tc_ha":(hi-lo)/2,"percent":100*(hi-lo)/(2*value),
                    "kind":"semiamplitude de IC/faixa publicada; transferência espacial excluída",
                    "interval_tc_ha":[lo,hi]}
    dry=row.get("range_dry_mg_ha")
    if isinstance(dry,(list,tuple)) and len(dry)==2 and all(isinstance(x,(int,float)) for x in dry):
        # Published dry-mass bounds can be converted only when a documented C fraction is supplied.
        fraction=row.get("carbon_fraction")
        if not isinstance(fraction,(int,float)) or not 0<fraction<=1:
            return {"absolute_tc_ha":None,"percent":None,"kind":"IC em massa seca disponível, mas fração de carbono específica não documentada"}
        lo,hi=(x*fraction for x in dry)
        if lo<=hi:
            return {"absolute_tc_ha":(hi-lo)/2,"percent":100*(hi-lo)/(2*value),
                    "kind":"semiamplitude de IC amostral convertido de massa seca; transferência excluída",
                    "interval_tc_ha":[lo,hi]}
    sd=row.get("agb_uncertainty_mg_ha")
    if isinstance(sd,(int,float)) and sd>=0:
        fraction=row.get("carbon_fraction",carbon_fraction)
        if not isinstance(fraction,(int,float)) or not 0<fraction<=1:
            return {"absolute_tc_ha":None,"percent":None,"kind":"fração de carbono da AGB não documentada"}
        absolute=sd*fraction
        return {"absolute_tc_ha":absolute,"percent":100*absolute/value,
                "kind":"incerteza do produto AGB (Mg/ha) convertida a tC/ha; NÃO é IC95%"}
    spatial=row.get("spatial_sd_tc_ha")
    if isinstance(spatial,(int,float)) and spatial>=0:
        return {"absolute_tc_ha":spatial,"percent":100*spatial/value,
                "kind":("desvio-padrão espacial zero na amostra/mapa; NÃO significa incerteza de predição zero" if spatial==0 else "desvio-padrão espacial; NÃO é erro de predição nem IC95%")}
    return {"absolute_tc_ha":None,"percent":None,
            "kind":"erro residual/transferência não quantificado"}

def executive_carbon_lines(native, fmt):
    area=native.get("native_area_ha") or 0
    unknown=native.get("unknown_cover_area_ha") or 0
    known=native.get("known_total_tc")
    complete=bool(native.get("complete"))
    lines=["PAINEL EXECUTIVO — ESTOQUES DE CARBONO",
           "Área total: "+fmt(native.get("area_aoi_ha"))+" ha | Área nativa: "+fmt(area)+" ha",
           "Cobertura nativa: "+(fmt(100*area/native["area_aoi_ha"])+"%" if native.get("area_aoi_ha") and not unknown else "N/D — cobertura não integralmente verificada"),
           "Cobertura não confirmada: "+fmt(unknown)+" ha"+(" — fonte de cobertura atual indisponível; não equivale a zero de vegetação nativa" if unknown else ""),
           "Estoque "+("total" if complete else "parcial conhecido")+": "+
           (fmt(known)+" tC | "+fmt(known*44/12)+" tCO₂e" if known is not None else "não estimado"),
           "Densidade nativa: "+(fmt(known/area)+" tC/ha | "+fmt(known/area*44/12)+" tCO₂e/ha" if known is not None and area else "N/D"),
           "INCERTEZA POR COMPARTIMENTO — valor ± medida disponível (tC/ha; %)"]
    for st in native.get("strata",[]):
        if not st.get("area_ha"):
            continue
        lines.append(st["class_name"]+" — "+fmt(st["area_ha"])+" ha")
        for row in st.get("components",[]):
            v=row.get("tc")
            u=uncertainty_for_pool(row)
            if not isinstance(v,(int,float)):
                lines.append("  "+row["parametro"]+": não estimado; incerteza: N/D tC/ha | N/D tCO₂e/ha | N/D %")
                continue
            abs_u=u["absolute_tc_ha"]
            error=(fmt(abs_u)+" tC/ha | "+fmt(abs_u*44/12)+" tCO₂e/ha | "+fmt(u["percent"])+"%" if abs_u is not None and u["percent"] is not None else
                   (fmt(abs_u)+" tC/ha | "+fmt(abs_u*44/12)+" tCO₂e/ha | N/D" if abs_u is not None else
                    "N/D tC/ha | N/D tCO₂e/ha | N/D % — incerteza não quantificada"))
            lines.append("  "+row["parametro"]+": "+fmt(v)+" tC/ha | "+fmt(v*44/12)+" tCO₂e/ha | incerteza: "+error)
            lines.append("    Natureza: "+u["kind"])
    lines.extend(["ATENÇÃO: as medidas acima têm naturezas estatísticas distintas; não somar como erros independentes.",
                  "Não há IC95% defensável do total sem covariâncias, validação de transferência e erro de área.",
                  "Componentes sem estimativa permanecem excluídos do estoque parcial conhecido.",""])
    return lines
