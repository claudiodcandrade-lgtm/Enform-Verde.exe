"""Embrapa pedological map intersections; separate from soil organic carbon.

Map: Embrapa Solos / PronaSolos national pedology 1:5,000,000.
Map units are ASSOCIATIONS of soils: map-unit area must never be allocated
as confirmed area of each soil component or as a farm laboratory assay.
GeoInfo metadata labels the original dataset CC BY-NC 3.0 BR; professional
or commercial reuse requires licensing review. This code does not bundle it.
"""
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime,timezone
from hashlib import sha256
from math import isfinite
from urllib.parse import urlencode
from urllib.request import Request,urlopen

SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/embrapa_solos_brasil_5kk/FeatureServer/0"
METADATA="https://geoinfo.dados.embrapa.br/datasets/geoinfo_data:geonode:brasil_solos_5m_20201104/metadata_detail"
FIELDS="objectid,simbolos,leg_desc,comp1,comp2,comp3,ordem1,ordem2,ordem3"
LICENSE="CC BY-NC 3.0 BR; verificar autorização para utilização profissional/comercial"
MAX_FEATURES=4000
DEPTHS=("0–5 cm","5–15 cm","15–30 cm","30–60 cm","60–100 cm","100–200 cm")
# Authoritative 90 m map IDs; not interpreted as field observations.
FERTILITY_LAYERS={
    "ctc_cmolc_kg":dict(zip(DEPTHS,range(37,43))),
    "ph":dict(zip(DEPTHS,range(44,50))),
    "electrical_conductivity_ds_m":dict(zip(DEPTHS,range(51,57))),
    "sand_g_kg":dict(zip(DEPTHS,range(16,22))),
    "clay_g_kg":dict(zip(DEPTHS,range(23,29))),
    "silt_g_kg":dict(zip(DEPTHS,range(30,36))),
    "organic_carbon_g_kg":dict(zip(DEPTHS,range(9,15)))
}
FERTILITY_SERVICE="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/atributos_solo_90m/MapServer"

def unavailable(reason):
    return {"status":"N/D","reason":str(reason)[:450],
            "source":SERVICE,"map_scale":"1:5.000.000","soil_mapping_units":[],
            "area_aoi_ha":None,"covered_area_ha":None,
            "unmapped_area_ha":None,"classification_uncertainty_ha":None,
            "area_by_soil_component_ha":None,"license":LICENSE,
            "carbon_stock_independent":True}

def _validate_geo(aoi):
    if aoi is None or aoi.crs is None:
        raise ValueError("AOI sem CRS")
    wgs=aoi.to_crs(4326).geometry.union_all()
    equal=aoi.to_crs(6933).geometry.union_all()
    if wgs.is_empty or equal.is_empty or not wgs.is_valid:
        raise ValueError("Geometria da AOI inválida")
    if equal.area<=0 or not isfinite(equal.area):
        raise ValueError("Área da AOI inválida")
    return wgs,equal

def fetch_embrapa_units(aoi,*,opener=urlopen,timeout=25):
    """Request bbox-intersecting polygons; fail on incomplete pagination."""
    wgs,_=_validate_geo(aoi)
    xmin,ymin,xmax,ymax=map(float,wgs.bounds)
    items=[]
    for offset in range(0,MAX_FEATURES,500):
        args={"f":"geojson","where":"1=1","outFields":FIELDS,
              "geometryType":"esriGeometryEnvelope",
              "geometry":json.dumps({"xmin":xmin,"ymin":ymin,"xmax":xmax,"ymax":ymax,
                                     "spatialReference":{"wkid":4326}},separators=(",",":")),
              "inSR":4326,"outSR":4326,"spatialRel":"esriSpatialRelIntersects",
              "geometryPrecision":6,"resultOffset":offset,"resultRecordCount":500,
              "returnGeometry":"true"}
        req=Request(SERVICE+"/query?"+urlencode(args),headers={"Accept":"application/geo+json,application/json",
                    "User-Agent":"Enform-Verde/soil-pedology"})
        with opener(req,timeout=timeout) as response:
            payload=json.load(response)
        if not isinstance(payload,dict) or payload.get("error"):
            raise ValueError("Serviço pedológico recusou consulta: "+str(
                (payload or {}).get("error",{}).get("code","erro remoto")))
        feats=payload.get("features")
        if not isinstance(feats,list):
            raise ValueError("Serviço pedológico não retornou GeoJSON de polígonos")
        items.extend(feats)
        if len(feats)<500 and not payload.get("exceededTransferLimit"):
            return {"type":"FeatureCollection","features":items}
    raise ValueError("Limite seguro da consulta atingido; mapa incompleto, área não inferível")

def intersect_soil_units(aoi,features,*,service=SERVICE):
    """Compute area in EPSG:6933 per EXCLUSIVE map-unit, not per component."""
    import geopandas as gpd
    from shapely.geometry import shape
    wgs,metric=_validate_geo(aoi)
    if not isinstance(features,dict) or not isinstance(features.get("features"),list):
        raise ValueError("GeoJSON pedológico ausente ou malformado")
    polys=[];bad=0
    for item in features["features"]:
        try:
            geometry=shape(item.get("geometry"))
            if geometry.is_empty:continue
            attrs=item.get("properties") or {}
            legend=str(attrs.get("leg_desc") or "").strip()
            symbol=str(attrs.get("simbolos") or "").strip()
            if not legend and not symbol:continue
            polys.append((geometry,attrs,legend,symbol))
        except (TypeError,ValueError,KeyError):
            bad+=1
    if bad:
        raise ValueError("Polígonos pedológicos inválidos: "+str(bad))
    if not polys: return unavailable("Sem unidade pedológica encontrada na interseção da AOI")
    frame=gpd.GeoSeries([p[0] for p in polys],crs=4326).to_crs(6933)
    area_total=float(metric.area)/10000
    covered=metric.buffer(0).difference(metric.buffer(0))
    rows={}
    # Exclusive coverage ensures no double-counting across overlapping map units.
    remaining=metric.buffer(0)
    for (_,attrs,legend,symbol),geom in zip(polys,frame):
        try:
            inter=remaining.intersection(geom)
        except Exception as exc:
            raise ValueError("Falha topológica de interseção pedológica: "+type(exc).__name__)
        if inter.is_empty:continue
        hectares=inter.area/10000
        if hectares<=1e-8:continue
        remaining=remaining.difference(inter)
        key=(legend or symbol,symbol)
        if key not in rows:
            rows[key]={"mapping_unit":legend or symbol,"symbol":symbol,
                "area_ha":0.0,
                "components":[str(attrs.get(c) or "").strip() for c in ("comp1","comp2","comp3")
                              if str(attrs.get(c) or "").strip()],
                "orders":[str(attrs.get(c) or "").strip() for c in ("ordem1","ordem2","ordem3")
                          if str(attrs.get(c) or "").strip()]}
        rows[key]["area_ha"]+=hectares
    output=[]
    for row in sorted(rows.values(),key=lambda r:-r["area_ha"]):
        ha=row["area_ha"]
        output.append({**row,"area_ha":round(ha,6),"area_pct_aoi":round(100*ha/area_total,4),
          "interpretation":"Área da UNIDADE pedológica; componentes associados não possuem área individual inferível"})
    mapped=sum(row["area_ha"] for row in output)
    unclassified=float(remaining.area)/10000
    if mapped>area_total+.1:
        raise ValueError("Dupla contagem de áreas pedológicas")
    return {"status":"MAPEAMENTO_REGIONAL" if output else "N/D",
        "source":service,"source_metadata":METADATA,"map_scale":"1:5.000.000",
        "area_crs":"EPSG:6933","aoi_sha256_wgs84":sha256(wgs.wkb).hexdigest(),
        "processed_utc":datetime.now(timezone.utc).isoformat(),
        "area_aoi_ha":round(area_total,6),
        "covered_area_ha":round(mapped,6),"unmapped_area_ha":round(unclassified,6),
        "coverage_pct_aoi":round(100*mapped/area_total,4),
        "soil_mapping_units":output,
        "area_by_soil_component_ha":None,
        "classification_uncertainty_ha":None,"classification_accuracy":None,
        "uncertainty_note":"Escala 1:5 milhões; posição dos limites e composição pedológica sem IC95% local. "
                           "Não corresponde a levantamento de detalhe da fazenda.",
        "carbon_stock_independent":True,
        "license":LICENSE,
        "fertility_available_layers":FERTILITY_LAYERS,
        "fertility_status":"CATALOGO_VERIFICADO_SEM_VALORES_ZONAIS",
        "not_available":["V%","P disponível","K trocável","Ca trocável","Mg trocável","SB"],
        "method":"Área = área de interseção AOI × unidade cartográfica, projetada em EPSG:6933 / 10000"}

def analyze_embrapa_pedology(aoi,*,fetcher=None):
    try:
        features=(fetcher or fetch_embrapa_units)(aoi)
        return intersect_soil_units(aoi,features)
    except Exception as exc:
        # URLs from remote requests are not included in user-facing diagnostics.
        return unavailable(type(exc).__name__+": "+str(exc).split("https://")[0])

def pedology_report_lines(result,fmt):
    lines=["","CLASSIFICAÇÃO PEDOLÓGICA — EMBRAPA SOLOS / PRONASOLOS (NÃO É ESTOQUE DE CARBONO)"]
    if result.get("status")!="MAPEAMENTO_REGIONAL":
        return lines+["N/D — "+str(result.get("reason") or "fonte indisponível")]
    lines+=["Mapa regional SiBCS, escala "+str(result.get("map_scale"))+
            "; área cartográfica, não confirmação pedológica da fazenda.",
            "Área da AOI: "+fmt(result["area_aoi_ha"],2)+" ha; abrangida: "+
            fmt(result["covered_area_ha"],2)+" ha ("+fmt(result["coverage_pct_aoi"],2)+"%)."]
    for unit in result["soil_mapping_units"]:
        lines.append("  "+unit["mapping_unit"]+": "+fmt(unit["area_ha"],2)+" ha ("+
                     fmt(unit["area_pct_aoi"],2)+"% da propriedade)")
        if unit["components"]:
            lines.append("    Componentes da unidade (SEM divisão individual de área): "+
                         "; ".join(unit["components"]))
    if result["unmapped_area_ha"]>0:
        lines.append("  Sem classe mapeada: "+fmt(result["unmapped_area_ha"],2)+" ha.")
    lines+=["Incerteza espacial: N/D — limites de unidades não validados localmente; sem IC95% da área.",
            "Fertilidade 90 m: CTC, pH, CE, textura e carbono mapeados em camadas próprias; valores NÃO calculados nesta consulta.",
            "Saturação de bases V%, P, K, Ca, Mg e soma de bases: N/D; não inferidos pela classe pedológica.",
            "Fonte: "+str(result["source"]),"Licença: "+str(result["license"])]
    return lines
