"""Conservative numeric sampling fallback for official Embrapa 90m raster layers.

ArcGIS MapServer Identify responds with per-pixel *numeric* values. It is not a
renderer/export-image: color-coded pixels, strings and nodata are rejected.
This is a sparse sample of an official raster, NOT an area-weighted zonal
calculation or a laboratory measurement. Never invent raster coverage or CI95.
"""
from __future__ import annotations
import math
import re
from datetime import datetime,timezone
from statistics import fmean,pstdev

MAPSERVER="https://geoportal.sgb.gov.br/server/rest/services/pronasolos/atributos_solo_90m/MapServer"
DEPTHS=("0-5","5-15","15-30","30-60","60-100","100-200")
FIELDS={
    "ctc":("CTC","cmolc/kg",37),
    "ph":("pH","",44),
    "ce":("Condutividade elétrica","dS/m",51),
    "sand":("Areia","g/kg",16),
    "clay":("Argila","g/kg",23),
    "silt":("Silte","g/kg",30),
    "organic_carbon":("Carbono orgânico (teor)","g/kg",9),
}
UNAVAILABLE=("Saturação de bases (V%)","Fósforo disponível (P)",
             "Potássio trocável (K)","Cálcio (Ca)","Magnésio (Mg)")
LAYER_IDS={first+i:(key,label,unit,depth) for key,(label,unit,first) in FIELDS.items()
           for i,depth in enumerate(DEPTHS)}


def numeric_result(value):
    """Accept one finite scalar only; reject RGB, CSS, labels, NoData."""
    if isinstance(value,bool):
        return None
    if isinstance(value,(int,float)):
        number=float(value)
    elif isinstance(value,str) and re.fullmatch(r"\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*",value):
        number=float(value)
    else:
        return None
    return number if math.isfinite(number) and -1e8<number<1e8 else None


def point_values(payload):
    """Return raw numeric MapServer Identify observations indexed by layer ID."""
    out={}
    for feature in (payload.get("results") or []):
        try:
            layer=int(feature["layerId"])
        except (KeyError,ValueError,TypeError):
            continue
        if layer not in LAYER_IDS:
            continue
        attrs=feature.get("attributes") or {}
        candidate=feature.get("value")
        if candidate is None:
            candidate=next((attrs[key] for key in ("Pixel Value","PixelValue","pixel_value")
                            if key in attrs),None)
        value=numeric_result(candidate)
        if value is None or value<=-9990:
            continue
        name=LAYER_IDS[layer][0]
        if name=="ph" and not 0<value<=14:continue
        if name in ("sand","clay","silt") and not 0<=value<=1000:continue
        if name not in ("ph","sand","clay","silt") and value<0:continue
        out[layer]=value
    return out


def identify_request(lon,lat,*,session=None,timeout=(8,24),url=MAPSERVER):
    import requests
    session=session or requests.Session()
    xmin,ymin,xmax,ymax=lon-.025,lat-.025,lon+.025,lat+.025
    args={"f":"json","geometry":f"{lon:.7f},{lat:.7f}",
          "geometryType":"esriGeometryPoint","sr":4326,
          "layers":"all:"+",".join(str(i) for i in LAYER_IDS),
          "tolerance":1,
          "mapExtent":f"{xmin:.7f},{ymin:.7f},{xmax:.7f},{ymax:.7f}",
          "imageDisplay":"1200,1200,96","returnGeometry":"false"}
    response=session.get(url+"/identify",params=args,timeout=timeout)
    response.raise_for_status()
    payload=response.json()
    if not isinstance(payload,dict) or "error" in payload or not isinstance(payload.get("results"),list):
        raise ValueError("ArcGIS Identify did not return valid numerical results")
    return point_values(payload)


def sample_points(geometry,*,grid_size=5,max_points=25):
    """Deterministic points within geometry, no point outside AOI."""
    from shapely.geometry import Point
    geom=geometry
    xmin,ymin,xmax,ymax=geom.bounds
    coords=[]
    for row in range(grid_size):
        lat=ymin+(row+.5)*(ymax-ymin)/grid_size
        for col in range(grid_size):
            lon=xmin+(col+.5)*(xmax-xmin)/grid_size
            if geom.covers(Point(lon,lat)):
                coords.append((lon,lat))
    if not coords:
        pos=geom.representative_point()
        coords=[(float(pos.x),float(pos.y))]
    if len(coords)>max_points:
        stride=math.ceil(len(coords)/max_points)
        coords=coords[::stride][:max_points]
    return coords


def sample_official_fertility(aoi,*,session=None,fetch=None,max_points=16):
    """Official numeric raster point observations, no inferred area coverage."""
    result={"status":"N/D","source":MAPSERVER,"method":"ArcGIS Identify numerico 90 m — pontos da AOI",
            "units":{},"layers":[],"unavailable_attributes":list(UNAVAILABLE),
            "laboratory_samples":None,"ic95":None,"carbon_stock_independent":True,
            "retrieved_utc":datetime.now(timezone.utc).isoformat()}
    if aoi is None or aoi.crs is None:
        result["reason"]="AOI sem CRS"
        return result
    geo=aoi.to_crs(4326).geometry.union_all()
    points=sample_points(geo,max_points=max_points)
    errors=[];measurements={k:[] for k in LAYER_IDS}
    reader=fetch or (lambda x,y:identify_request(x,y,session=session))
    for lon,lat in points:
        try:
            values=reader(lon,lat)
            if not isinstance(values,dict):raise ValueError("Identify must return layer-value dictionary")
            for layer,value in values.items():
                if layer in measurements and numeric_result(value) is not None:
                    measurements[layer].append(float(value))
        except Exception as exc:
            errors.append(type(exc).__name__)
    items=[]
    for layer,(attr,label,unit,depth) in LAYER_IDS.items():
        vals=measurements[layer]
        if not vals:continue
        mean=fmean(vals)
        items.append({"attribute":attr,"label":label,"unit":unit,"depth_cm":depth,
            "mean":mean,"spatial_sd":pstdev(vals) if len(vals)>1 else None,
            "valid_pixels":None,"sampled_points":len(vals),"total_sample_points":len(points),
            "coverage_pct":None,"mapped_area_ha":None,"mapserver_layer_id":layer,
            "wcs_coverage_id":None,"raster_sha256":None,
            "uncertainty":"N/D — variabilidade de pontos não equivale a erro de predição nem IC95%",
            "method":"amostragem de valores numericos MapServer Identify; nao e media zonal ponderada"})
    if not items:
        result["reason"]="MapServer Identify não retornou valores escalares válidos; erros: "+",".join(sorted(set(errors)))
        return result
    result.update({"status":"MAPA_PREDITIVO_AMOSTRAL","units":{"PROPRIEDADE — AMOSTRA DE PIXELS":items},
                   "layers":items,"sampled_points":len(points),
                   "reason":"Valores reais de pontos MapServer; não extrapolar para média exata por hectare, cobertura ou IC95%",
                   "uncertainty_note":"Amostragem de pixels por geometria; erro preditivo e representatividade espacial N/D",
                   "license":"Embrapa Solos/PronaSolos — verificar licença comercial"})
    return result
