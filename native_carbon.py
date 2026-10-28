"""Carbon accounting restricted to confirmed native intersections.

The estimator is called independently for each class geometry. A density from
one class is never propagated to another class or multiplied by the whole AOI.
"""
from __future__ import annotations
import math
import unicodedata

COMPARTMENTS=('Biomassa aérea','Biomassa subterrânea','Necromassa aérea','Necromassa subterrânea','Serapilheira','Solo 0–30 cm')


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD',str(value or '').casefold()) if unicodedata.category(c)!='Mn')


def native_class(name, source, class_metadata=None):
    """IBGE phytoregion alone is potential vegetation, not current native cover."""
    text=normalize(name)
    # Requisito eliminatório: silvicultura jamais integra carbono nativo,
    # mesmo com fonte IBGE+MAPBIOMAS ou rótulo SAR supostamente validado.
    planted_terms=('silvicultura','floresta plantada','florestas plantadas',
                   'floresta de producao','reflorestamento','eucalipt',
                   'eucalyptus','pinus','pinheiro plantado','plantio florestal')
    if any(term in text for term in planted_terms):
        return False
    uncertain_terms=('cobertura arborea','origem nao determinada',
                     'floresta de origem incerta','natural ou plantada')
    if any(term in text for term in uncertain_terms):
        return None
    meta=(class_metadata or {}).get(name,{})
    if isinstance(meta,dict):
        if meta.get('planted_forest') is True or meta.get('is_silviculture') is True:
            return False
        if meta.get('native_origin_confirmed') is False:
            return None
    if any(word in text for word in ('areas cultivadas','area cultivada','soja','milho','sorgo','cafe','citr','cacau','cocoa','banana','silvicultura','plantad','eucalipt','pinus','agroflorest','lavoura','agricultura','antropic','urbaniz','mineracao')):
        return False
    if 'pastagem' in text and 'nativ' not in text:return False
    if source=='SEM_COBERTURA':return None
    if source=='SAR_VALIDADO':
        if text.startswith('grupo: '):return text=='grupo: vegetacao natural'
        meta=(class_metadata or {}).get(name,{})
        return meta.get('parent')=='vegetação natural' if meta else None
    if source in ('IBGE+MAPBIOMAS','SAR_VALIDADO+IBGE'):return True
    if source=='IBGE':return None
    if source=='MAPBIOMAS':
        from mapbiomas_zonal import LEGEND
        native_codes={3,4,5,6,7,11,12,49,50}
        for code,(label,_) in LEGEND.items():
            if name==label:return code in native_codes
    return None


def summarize_native_carbon(aoi, class_polygons, estimator, class_metadata=None):
    import geopandas as gpd
    from land_use_sar import AREA_CRS
    from carbon_compartments import aoi_to_wgs84
    aoi_geom=aoi_to_wgs84(aoi).to_crs(AREA_CRS).geometry.union_all()
    area_aoi=aoi_geom.area/10000
    if area_aoi<=0:raise ValueError('AOI sem área válida.')
    clipped=class_polygons.to_crs(AREA_CRS).copy()
    clipped['geometry']=clipped.geometry.make_valid().intersection(aoi_geom)
    clipped=clipped[~clipped.geometry.is_empty]
    if abs(clipped.geometry.area.sum()-clipped.geometry.union_all().area)>max(1e-4,aoi_geom.area*1e-8):
        raise ValueError('Classes sobrepostas: não é possível somar carbono sem dupla contagem.')
    class_polygons=clipped
    native_area=0.0; excluded_area=0.0; unknown_area=0.0; strata=[]
    for record in class_polygons.itertuples():
        geom=record.geometry
        frame=gpd.GeoDataFrame(geometry=[geom],crs=class_polygons.crs)
        area=float(frame.to_crs(AREA_CRS).geometry.area.iloc[0])/10000
        if area <= max(1e-9, area_aoi * 1e-12):
            continue
        flag=native_class(record.class_name,record.source,class_metadata)
        if flag is False:excluded_area+=area;continue
        if flag is None:unknown_area+=area;continue
        native_area+=area
        meta=(class_metadata or {}).get(record.class_name,{})
        physiognomy=record.class_name if record.source.startswith('SAR_VALIDADO') else (meta.get('physiognomy') or record.class_name)
        detail=('região/fitofisionomia identificada na legenda IBGE' if record.source in ('IBGE+MAPBIOMAS','SAR_VALIDADO+IBGE') else ('fitofisionomia declarada no modelo SAR' if meta.get('physiognomy') else 'classe de cobertura; subtipo fitofisionômico não determinado'))
        try: estimated=estimator(frame,physiognomy)
        except Exception as exc:estimated={'components':[], 'error':str(exc)}
        supplied={item['parametro']:item for item in estimated.get('components',[])}
        components=[]
        for name in COMPARTMENTS:
            row=dict(supplied.get(name) or {'parametro':name,'tc':None,'origem':'NAO_ESTIMADO','fonte':'Sem dado compatível','obs':estimated.get('error') or 'Sem fonte/modelo compatível para esta interseção.'})
            value=row.get('tc')
            if value is not None and (not math.isfinite(float(value)) or float(value)<0):raise ValueError('Densidade de carbono inválida.')
            included=value is not None and row.get('include_in_total',True) is not False
            row.update({'area_ha':area,'area_pct':100*area/area_aoi,'total_tc':float(value)*area if included else None,
                        'include_in_total':included})
            components.append(row)
        known=sum(c['total_tc'] for c in components if c['total_tc'] is not None)
        complete=all(c['total_tc'] is not None for c in components)
        strata.append({'class_name':record.class_name,'physiognomy':physiognomy,'physiognomy_resolution':detail,'source':record.source,
                       'area_ha':area,'area_pct':100*area/area_aoi,'components':components,
                       'known_total_tc':known,'complete':complete,'sar_audit':estimated.get('sar_audit'),'sar_details':estimated.get('sar_details'),'soil_profiles':estimated.get('soil_profiles')})
    totals=[]
    for name in COMPARTMENTS:
        entries=[c for st in strata for c in st['components'] if c['parametro']==name and c['total_tc'] is not None]
        covered=sum(c['area_ha'] for c in entries)
        known=sum(c['total_tc'] for c in entries)
        totals.append({'parametro':name,'known_total_tc':known if entries else None,
                       'quantified_area_ha':covered,'missing_native_area_ha':max(0,native_area-covered),
                       'tc_on_quantified_area':known/covered if covered else None,
                       'tc_on_all_native_area':known/native_area if native_area and abs(covered-native_area)<1e-6 else None})
    has_number=any(r['known_total_tc'] is not None for r in totals)
    known_total=sum(r['known_total_tc'] or 0 for r in totals) if has_number else None
    complete=bool(strata) and all(s['complete'] for s in strata) and unknown_area<1e-6
    return {'strata':strata,'components':totals,'area_aoi_ha':area_aoi,'native_area_ha':native_area,
            'excluded_other_uses_ha':excluded_area,'unknown_cover_area_ha':unknown_area,
            'known_total_tc':known_total,'known_total_tco2':known_total*44/12 if known_total is not None else None,
            'complete':complete,'total_uncertainty':None,
            'uncertainty_note':'Incertezas individuais preservadas por fonte/classe; covariâncias e erro de classificação/área não quantificados. Não se fornece IC95% do total.',
            'method':'C conhecido = soma por fitofisionomia nativa e compartimento de (tC/ha × hectares da interseção). Outras classes: ocorrência apenas.'}


def estimate_native_components(aoi, physiognomy, biome, sar_estimator, soil_estimator):
    """Reuse existing domain-aware providers separately for every native stratum."""
    from carbon_compartments import (santo_ambrosio_litter_stock_component,tapajos_litter_stock_component,
        pantanal_nhecolandia_litter_carbon_component,tapajos_necromass_components,ifn_necromass_component,infer_uf_from_aoi)
    try:sar=sar_estimator(aoi,biome,physiognomy) or {}
    except Exception as exc:sar={'error':str(exc)}
    selected=sar if sar.get('agb_mg_ha') is not None else (sar.get('literature_reference') or {})
    agb=selected.get('agb_mg_ha')
    origin=str(selected.get('data_origin') or '')
    if agb is not None and not (origin.startswith('SAR') or origin in ('LITERATURA_MICRORREGIONAL','LITERATURA_SECUNDARIA','MODELAGEM_LITERATURA_HIERARQUICA')):
        agb=None
    rows=[];regional=dict(selected.get('regional_components') or {})
    regional.update(sar.get('regional_components') or {})
    regional.update(tapajos_necromass_components(biome,physiognomy,aoi))
    if not any(normalize(k).startswith('necromassa aerea') for k in regional):
        from pathlib import Path
        import sys
        root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
        table=root/'data'/'ifn_necromass_biome_uf_v1.csv'
        if not table.exists():table=Path(sys.executable).parent/'data'/'ifn_necromass_biome_uf_v1.csv'
        try:
            ref=ifn_necromass_component(biome,infer_uf_from_aoi(aoi),table)
            if ref:regional['Necromassa aérea']=ref
        except Exception:pass
    if not any('serapilheira' in normalize(k) for k in regional):
        for provider in (santo_ambrosio_litter_stock_component,tapajos_litter_stock_component,pantanal_nhecolandia_litter_carbon_component):
            component=provider(biome,physiognomy,aoi)
            if component:regional['Serapilheira']=component;break
    if agb is not None:
        rows.append({'parametro':'Biomassa aérea','tc':float(agb)*.47,'origem':origin,'fonte':selected.get('source','Produto/modelo SAR'),
                     'metodo':selected.get('method',selected.get('status','SAR')),'obs':'Somente pixels/referência desta interseção nativa.',
                     'uncertainty_kind':selected.get('uncertainty_kind'),'agb_uncertainty_mg_ha':selected.get('uncertainty_mg_ha'),
                     'agb_range_mg_ha':selected.get('agb_range_mg_ha')})
        p=normalize(physiognomy)
        # Never apply a generalized upland-forest root equation to grassland,
        # savanna, mangrove, floodplain, or planted formations.
        upland_forest=any(w in p for w in ('floresta','ombrofila','estacional')) and not any(w in p for w in ('aluvial','alag','mangue','varzea'))
        if float(agb)>0 and upland_forest and 'Biomassa subterrânea' not in regional:
            rows.append({'parametro':'Biomassa subterrânea','tc':math.exp(-1.0587+.8836*math.log(float(agb)))*.47,
                         'origem':'MODELAGEM_ALOMETRIA','fonte':'Cairns et al. (1997), doi:10.1007/s004420050201',
                         'metodo':'BGB=exp(-1,0587+0,8836 ln AGB); floresta tropical de terras altas, referência generalizada',
                         'obs':'Erro residual/transferência alométrica não quantificado; sem IC total.'})
    for raw_name,c in regional.items():
        key=next((k for k in COMPARTMENTS if normalize(raw_name).startswith(normalize(k))),None)
        if key is None:continue
        value=c.get('mean_tc_ha')
        if value is None and c.get('mean_dry_mg_ha') is not None:value=float(c['mean_dry_mg_ha'])*.47
        rows.append({'parametro':key,'tc':value,'origem':c.get('origin','INVENTARIO_REFERENCIA'),
                     'fonte':c.get('source'),'metodo':c.get('method'),'obs':c.get('uncertainty_kind'),
                     'include_in_total':c.get('include_in_total',True),
                     'range_tc_ha':c.get('range_tc_ha'),'range_dry_mg_ha':c.get('range_dry_mg_ha')})
    soil={}
    try:
        soil=soil_estimator(aoi) or {};top=soil.get('0–30 cm')
        if top and top.get('tc_ha') is not None:
            rows.append({'parametro':'Solo 0–30 cm','tc':float(top['tc_ha']),'origem':'MAPEAMENTO','fonte':'Embrapa Solos/PronaSolos',
                         'metodo':'Soma das camadas 0–5, 5–15, 15–30 cm na interseção nativa',
                         'obs':'Variabilidade espacial do mapa não equivale a erro de predição/IC.',
                         'spatial_sd_tc_ha':top.get('spatial_sd_tc_ha')})
    except Exception:pass
    return {'components':rows,'soil_profiles':soil,'sar_audit':sar.get('audit'), 'error':sar.get('error'),
            'sar_details':{k:sar[k] for k in ('status','data_origin','source','sensor','paths','stats','height_mean_m','height_interpretation','sar_validation_metrics','agb_blocker','message','reason') if k in sar}}
