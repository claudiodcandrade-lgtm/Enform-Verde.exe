"""Readable native-carbon executive summary with honest per-pool uncertainty units."""
from __future__ import annotations
import math
import json


def litter_dashboard_summaries(native):
    """Return one auditable dashboard row per native stratum with litter stock.

    Consolidated stocks and experimental-only stocks are kept distinct. The
    function reads stratum components because pool totals intentionally omit
    experimental-only scenarios.
    """
    output=[]
    for stratum in native.get("strata",[]):
        for component in stratum.get("components",[]):
            if component.get("parametro")!="Serapilheira":
                continue
            experimental=component.get("experimental_total_tc")
            known=component.get("total_tc")
            if experimental is not None:
                stock=float(experimental)
                area=float(component.get("area_ha") or stratum.get("area_ha") or 0)
                status="CENÁRIO EXPERIMENTAL — FORA DO TOTAL CONHECIDO"
            elif known is not None:
                stock=float(known)
                area=float(component.get("quantified_area_ha") or component.get("area_ha") or 0)
                status=str(component.get("status") or "ESTOQUE QUANTIFICADO")
            else:
                continue
            density=(stock/area if area>0 else component.get("tc"))
            source=str(component.get("fonte") or component.get("source") or "fonte N/D")
            source_url=component.get("source_url") or component.get("url")
            method=component.get("metodo") or component.get("method")
            uncertainty=(component.get("uncertainty_kind") or
                         component.get("uncertainty") or "incerteza não quantificada")
            note=(f"Área: {area:.4f} ha; fonte: {source}; "
                  f"método: {method or 'N/D'}; incerteza: {uncertainty}; "
                  f"URL/fontes: {source_url or 'N/D'}")
            output.append({"physiognomy":stratum.get("physiognomy") or stratum.get("class_name") or "N/D",
                           "area_ha":area,"stock_tc":stock,"tc_ha":density,
                           "tco2e_ha":density*44/12 if density is not None else None,
                           "status":status,"note":note,"experimental":experimental is not None})
    return output

def uncertainty_for_pool(row, carbon_fraction=0.47):
    value=row.get("tc")
    if not isinstance(value,(int,float)) or value<=0:
        return {"absolute_tc_ha":None,"percent":None,"kind":"não quantificada"}
    interval=row.get("range_tc_ha")
    # A hypothetical physical endpoint envelope is NOT an observed error, a
    # published CI, nor a transferable AOI prediction interval. Keep its
    # statistics N/D and display the scenario bounds in a separate field.
    if row.get("origem") == "EXPERIMENTAL_FISICO":
        from math import isfinite
        bounds=(list(interval) if isinstance(interval,(list,tuple))
                and len(interval)==2 and all(type(x) in (int,float) and isfinite(x)
                                             for x in interval)
                and 0 <= interval[0] <= value <= interval[1] else None)
        return {"absolute_tc_ha":None,"percent":None,
                "kind":"faixa exploratória de cenários físicos, NÃO é IC95%, erro medido ou intervalo preditivo",
                "scenario_range_tc_ha":bounds}
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
    aoi_ha=float(native.get("area_aoi_ha") or 0)
    pct=(100*area/aoi_ha) if aoi_ha>0 else None
    others=float(native.get("excluded_other_uses_ha") or 0)
    cover_complete=(native.get("cover_completeness")=="COMPLETE")
    # Compact, bounded stock table. Aggregate each pool by summed stock and
    # only publish a per-area density when the pool covers the full native area.
    table=["+-----------------------------------------------+",
           "| COMPARTIMENTO / TOTAL | tC/ha | tCO2e/ha | INCERTEZA tCO2e/ha | INCERTEZA % |",
           "+-----------------------------------------------+"]
    all_components=[c for st in native.get("strata",[]) for c in st.get("components",[])]
    pool_results={}
    for pool in ("Biomassa aérea","Biomassa subterrânea","Necromassa aérea",
                 "Necromassa subterrânea","Serapilheira","Solo 0–100 cm"):
        rows=[r for r in all_components if r.get("parametro")==pool]
        quantified=[r for r in rows if isinstance(r.get("total_tc"),(int,float))
                    and isinstance(r.get("tc"),(int,float))]
        covered=sum(float(r.get("quantified_area_ha",r.get("area_ha") or 0)) for r in quantified)
        stock=sum(float(r["total_tc"]) for r in quantified) if quantified else None
        density=(stock/area if stock is not None and area>0 and
                 abs(covered-area)<=max(1e-6,area*1e-8) else None)
        row_unc=[]
        for r in quantified:
            u=uncertainty_for_pool(r)
            if u.get("absolute_tc_ha") is not None and u.get("percent") is not None:
                row_unc.append((float(u["absolute_tc_ha"]),float(u["percent"])))
        if density is not None and row_unc and len(row_unc)==len(quantified):
            # A single stratum needs no cross-stratum covariance. Multiple
            # strata combine by area-weighted variance only when independence
            # is explicitly documented; otherwise uncertainty stays N/D.
            independent=(len(quantified)==1 or all(
                r.get("uncertainty_independence")=="independent_strata" for r in quantified))
            if independent and len(quantified)==1:
                sigma=row_unc[0][0]
            elif independent:
                sigma=math.sqrt(sum((float(r.get("quantified_area_ha",r.get("area_ha")))*u[0])**2
                                    for r,u in zip(quantified,row_unc)))/area
            else:
                sigma=None
            unc_abs=(sigma*44/12 if sigma is not None else None)
            unc_pct=(100*sigma/density if sigma is not None and density>0 else None)
        else:
            unc_abs=unc_pct=None
        pool_results[pool]=(density,unc_abs)
        table.append("| "+pool+" | "+fmt(density) if density is not None else "| "+pool+" | N/D")
        table[-1]+=" | "+fmt(density*44/12) if density is not None else " | N/D"
        table[-1]+=" | "+fmt(unc_abs) if unc_abs is not None else " | N/D"
        table[-1]+=" | "+fmt(unc_pct)+"% |" if unc_pct is not None else " | N/D |"
    total_uncertainty_rule=None
    if complete and area>0 and known is not None:
        total_density=known/area
        joint=native.get("total_uncertainty") or {}
        se_total=joint.get("se_tC")
        total_unc_abs=(float(se_total)/area*44/12 if isinstance(se_total,(int,float)) else None)
        total_unc_pct=(100*float(se_total)/known if isinstance(se_total,(int,float)) and known>0 else None)
        if total_unc_abs is None:
            # Owner decision 08/11/2026 (question 7 = B): declared correlation.
            # Biomass-derived pools (aboveground, roots, necromass) are fully
            # correlated (rho = 1, they share the biomass estimate); litter and
            # soil are independent (rho = 0). Never a simple sum of all errors.
            bio=("Biomassa aérea","Biomassa subterrânea","Necromassa aérea","Necromassa subterrânea")
            present={k:v for k,v in pool_results.items() if v[0] is not None}
            if present and all(v[1] is not None for v in present.values()):
                corr_sum=sum(v[1] for k,v in present.items() if k in bio)
                indep=sum(v[1]**2 for k,v in present.items() if k not in bio)
                total_unc_abs=math.sqrt(corr_sum**2+indep)
                total_unc_pct=100*total_unc_abs/(total_density*44/12) if total_density>0 else None
                total_uncertainty_rule=("correlação declarada: biomassa aérea, raízes e necromassa ρ=1; "
                                        "serapilheira e solo independentes (ρ=0)")
        total_label="TOTAL — soma dos compartimentos"
    else:
        total_density=total_unc_abs=total_unc_pct=None
        total_label="TOTAL — parcial / incompleto"
    table.append("+-----------------------------------------------+")
    table.append("| "+total_label+" | "+(fmt(total_density) if total_density is not None else "N/D")+
                 " | "+(fmt(total_density*44/12) if total_density is not None else "N/D")+
                 " | "+(fmt(total_unc_abs) if total_unc_abs is not None else "N/D")+
                 " | "+(fmt(total_unc_pct)+"%" if total_unc_pct is not None else "N/D")+" |")
    table.append("+-----------------------------------------------+")
    biodiversity=native.get("biodiversity_references") or []
    biodiversity_lines=["PERSPECTIVA DE BIODIVERSIDADE E ESTRUTURA — INVENTÁRIOS REGIONAIS",
        "Referência fitossociológica compatível; não representa inventário medido na propriedade."]
    if not biodiversity:
        biodiversity_lines.append("N/D — resumo de inventário não foi executado.")
    else:
        for ref in biodiversity:
            if ref.get("status")!="REFERENCIA_FITOSSOCIOLOGICA_REGIONAL":
                biodiversity_lines.append("N/D — "+str(ref.get("reason") or "sem referência compatível")+
                    "; fitofisionomia: "+str(ref.get("target",{}).get("physiognomy","N/D")))
                continue
            biodiversity_lines.append(
                str(ref.get("physiognomy"))+" / "+str(ref.get("microregion"))+": "+
                str(ref.get("inventory_n_plots"))+" parcelas; "+
                str(ref.get("inventory_n_live_stems"))+" indivíduos vivos; "+
                str(ref.get("species_richness_observed"))+" espécies observadas; "+
                "DAP mínimo "+fmt(ref.get("inclusion_threshold_dap_cm"))+" cm.")
            biodiversity_lines.append("Área basal média de toda a comunidade: "+
                fmt(ref.get("community_mean_basal_area_m2_ha"))+" m²/ha; DP entre parcelas "+
                fmt(ref.get("community_sd_between_plots_m2_ha"))+" m²/ha; IC95% da região de origem "+
                (json.dumps(ref.get("community_ci95_source_region_m2_ha"),ensure_ascii=False)
                 if ref.get("community_ci95_source_region_m2_ha") else "N/D pelo delineamento amostral")+
                ". Erro de transferência para a fazenda não quantificado.")
            biodiversity_lines.append("Riqueza e Shannon H′ são descritivos da amostra, sem IC de transferência: "+
                str(ref.get("species_richness_observed"))+" espécies; H′="+
                fmt(ref.get("shannon_h_descriptive"))+".")
            biodiversity_lines.append("Top 10 por frequência nas parcelas — frequência | área basal média (m²/ha) | IC95% amostral da região:")
            for row in ref.get("top10_by_plot_incidence",[]):
                ci=row.get("ci95_source_region_m2_ha")
                biodiversity_lines.append("  "+str(row.get("species"))+" — "+
                    fmt(row.get("frequency_pct"))+"% | "+fmt(row.get("mean_basal_area_m2_ha"))+" | "+
                    (fmt(ci[0])+"–"+fmt(ci[1]) if ci else "N/D"))
            biodiversity_lines.append("Soma da área basal média das 10 espécies: "+
                fmt(ref.get("top10_mean_basal_area_sum_m2_ha"))+" m²/ha. A estimativa da comunidade mantém todas as espécies; espécies raras não são descartadas.")
            biodiversity_lines.append("Fontes: "+"; ".join(ref.get("institutions") or [])+
                " — "+"; ".join(ref.get("source_urls") or []))
    lines=["PAINEL EXECUTIVO — ESTOQUES DE CARBONO",
           "ÁREA TOTAL ANALISADA: "+fmt(aoi_ha)+" ha (100%)",
           "VEGETAÇÃO NATIVA MAPEADA: "+
               (fmt(area)+" ha"+(" ("+fmt(pct)+"% da AOI)" if pct is not None else "")
                if area>0 or unknown<=0 else "N/D — nenhuma área nativa confirmada; área não confirmada: "+fmt(unknown)+" ha"),
           "OUTROS USOS (não entram no estoque nativo): "+
               (fmt(others)+" ha" if others>0 or unknown<=0 else "N/D — usos não nativos não confirmados"),
           "Cobertura não confirmada: "+fmt(unknown)+" ha — não equivale a zero de vegetação nativa; pode conter vegetação não mapeada",
           "A formação IBGE nomeia SOMENTE a interseção nativa; NÃO é cobertura de toda a AOI.",
           "Cobertura nativa: "+("N/D — cobertura não integralmente verificada" if unknown>0 else
                                  (fmt(pct)+"% da AOI conforme classes mapeadas" if pct is not None else "N/D")),
           *biodiversity_lines,
           "Cobertura cartográfica: "+("completa dentro da precisão de área" if cover_complete
                                    else "parcial — área sem classe; não inferir sua cobertura"),
           "COMPARTIMENTOS DE CARBONO: "+("todos quantificados" if complete
                                              else "PARCIAIS — um ou mais compartimentos sem estoque defensável"),
           "Estoque "+("conhecido" if complete else "parcial conhecido")+": "+
           (fmt(known)+" tC | "+fmt(known*44/12)+" tCO₂e" if known is not None else "não estimado"),
           "Densidade sobre a área NATIVA mapeada: "+
           (fmt(known/area)+" tC/ha | "+fmt(known/area*44/12)+" tCO₂e/ha"
            if known is not None and area else "N/D"),
           "INCERTEZA POR COMPARTIMENTO — quadro executivo (estoques em tC/ha e tCO₂e/ha; incertezas em tCO₂e/ha e %):",
           *table,
           ("Incerteza do total: "+total_uncertainty_rule+"." if total_uncertainty_rule else
            "Incertezas entre estratos só são combinadas quando sua independência está explicitamente documentada; total exige incerteza em todos os compartimentos. Sem isso, N/D.")]
    for st in native.get("strata",[]):
        if not st.get("area_ha"):
            continue
        lines.append(st["class_name"]+" — "+fmt(st["area_ha"])+" ha")
        for row in st.get("components",[]):
            v=row.get("tc")
            u=uncertainty_for_pool(row)
            if not isinstance(v,(int,float)):
                lines.append("  "+row["parametro"]+": não estimado; incerteza: N/D tC/ha | N/D tCO₂e/ha | N/D %")
                if row["parametro"] == "Serapilheira":
                    lines.append("    Origem/diagnóstico: "+str(row.get("fonte") or "nenhuma referência gravimétrica compatível")+" — "+str(row.get("obs") or "N/D"))
                    lines.append("    IFN/SFB: espessura (cm) não é massa seca (Mg/ha); conversão exige pares de campo compatíveis, validação agrupada e fração de C medida.")
                continue
            abs_u=u["absolute_tc_ha"]
            error=(fmt(abs_u)+" tC/ha | "+fmt(abs_u*44/12)+" tCO₂e/ha | "+fmt(u["percent"])+"%" if abs_u is not None and u["percent"] is not None else
                   (fmt(abs_u)+" tC/ha | "+fmt(abs_u*44/12)+" tCO₂e/ha | N/D" if abs_u is not None else
                    "N/D tC/ha | N/D tCO₂e/ha | N/D % — incerteza não quantificada"))
            pool_name=(row["parametro"]+" — CENÁRIO EXPERIMENTAL (fora do estoque conhecido)"
                       if row.get("origem")=="EXPERIMENTAL_FISICO" else row["parametro"])
            lines.append("  "+pool_name+": "+fmt(v)+" tC/ha | "+fmt(v*44/12)+" tCO₂e/ha | incerteza: "+error)
            lines.append("    Natureza: "+u["kind"])
            if row["parametro"] == "Serapilheira":
                lines.append("    Fonte/método gravimétrico: "+str(row.get("fonte") or "N/D")+" | "+str(row.get("metodo") or "N/D"))
                if row.get("calculation_trace"):
                    lines.append("    Trilha de cálculo: "+json.dumps(row["calculation_trace"],ensure_ascii=False,sort_keys=True))
                if row.get("limitations"):
                    lines.append("    Limites de transferência: "+"; ".join(map(str,row["limitations"])))
            scenario=u.get("scenario_range_tc_ha")
            if scenario is not None:
                lo,hi=scenario
                lines.append("    CENÁRIOS FÍSICOS (sem cobertura estatística): "+
                             fmt(lo)+"–"+fmt(hi)+" tC/ha | "+
                             fmt(lo*44/12)+"–"+fmt(hi*44/12)+" tCO₂e/ha")
    experimental=native.get("experimental_only_total_tc")
    if isinstance(experimental,(int,float)):
        lines.append("Subtotal APENAS EXPERIMENTAL: "+fmt(experimental)+
                     " tC | "+fmt(experimental*44/12)+
                     " tCO₂e; excluído do estoque parcial conhecido e sem IC95%.")
    lines.extend(["ATENÇÃO: as medidas acima têm naturezas estatísticas distintas; não somar como erros independentes.",
                  "Não há IC95% defensável do total sem covariâncias, validação de transferência e erro de área.",
                  "Componentes sem estimativa permanecem excluídos do estoque parcial conhecido.",""])
    return lines
