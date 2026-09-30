import math,re
from pathlib import Path
import numpy as np, requests
ASF_SEARCH="https://api.daac.asf.alaska.edu/services/search/param"
CDSE_STAC="https://stac.dataspace.copernicus.eu/v1/search"
MODEL_REGISTRY=[
{"id":"CASSOL_2021","biome":"Amazônia","domain":"floresta secundária","bands":["L"],"sensor":"ALOS-2/PALSAR-2","doi":"10.1080/01431161.2021.1903615","institution":"INPE/NCEO"},
{"id":"CASSOL_2019","biome":"Amazônia","domain":"floresta secundária","bands":["L"],"sensor":"ALOS-2/PALSAR-2","doi":"10.3390/rs11010059","institution":"INPE/NCEO"},
{"id":"VARZEA_2018","biome":"Amazônia","domain":"várzea","bands":["L","X"],"sensor":"ALOS/PALSAR + TerraSAR-X","doi":"10.3390/rs10091355","rmse_mg_ha":74.6},
{"id":"CERRADO_2021","biome":"Cerrado","domain":"vegetação nativa","bands":["L"],"sensor":"ALOS/ALOS-2 + Landsat","r2":0.53,"rel_rmse_pct":57.0}
]
def _wkt(gdf):return gdf.to_crs(4326).geometry.union_all().wkt
def discover_asf(gdf,limit=25):
    out=[]
    for dataset,band in [("ALOS PALSAR","L"),("NISAR","L"),("SENTINEL-1","C")]:
        try:
            r=requests.get(ASF_SEARCH,params={"dataset":dataset,"intersectsWith":_wkt(gdf),"output":"geojson","maxResults":limit},timeout=(10,45));r.raise_for_status();js=r.json();fs=js.get("features",[])
            out.append({"provider":"ASF/NASA","dataset":dataset,"band":band,"count":len(fs),"items":[{"id":x.get("properties",{}).get("sceneName") or x.get("id"),"properties":x.get("properties",{})} for x in fs]})
        except Exception as e:out.append({"provider":"ASF/NASA","dataset":dataset,"band":band,"count":0,"items":[],"error":str(e)})
    return out
def discover_cdse(gdf,limit=25):
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__
    try:
        r=requests.post(CDSE_STAC,json={"collections":["sentinel-1-grd"],"intersects":geom,"limit":limit},timeout=(10,45));r.raise_for_status();fs=r.json().get("features",[])
        return {"provider":"Copernicus Data Space","dataset":"Sentinel-1 GRD","band":"C","count":len(fs),"items":[{"id":x.get("id"),"datetime":x.get("properties",{}).get("datetime")} for x in fs]}
    except Exception as e:return {"provider":"Copernicus Data Space","dataset":"Sentinel-1 GRD","band":"C","count":0,"items":[],"error":str(e)}
def discover_sar(gdf):return discover_asf(gdf)+[discover_cdse(gdf)]
def _zonal(gdf,path):
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    with rasterio.open(path) as src:
        gj=transform_geom("EPSG:4326",src.crs,gdf.to_crs(4326).geometry.union_all().__geo_interface__)
        arr,_=mask(src,[gj],crop=True,filled=False);a=np.ma.array(arr[0]).compressed();a=a[np.isfinite(a)]
        if src.nodata is not None:a=a[a!=src.nodata]
        if not len(a):raise ValueError("Raster sem pixels válidos dentro do polígono.")
        return {"mean":float(a.mean()),"sd":float(a.std(ddof=1)) if len(a)>1 else 0.0,"n":int(len(a)),"min":float(a.min()),"max":float(a.max())}
def role(path):
    n=Path(path).name.lower()
    if any(x in n for x in ["uncert","sigma","stderr","stddev","rmse"]):return "UNCERTAINTY"
    if any(x in n for x in ["agb","biomass","biomassa"]):return "AGB"
    for p in ("hh","hv","vv","vh"):
        if re.search(r"(^|[_-])"+p+r"([_.-]|$)",n):return p.upper()
    return "SAR"
def process_real_sar(gdf,paths,biome="",phys=""):
    if not paths:raise ValueError("Nenhum produto SAR/raster de biomassa foi fornecido.")
    stats=[];agb=None;unc=None
    for p in paths:
        rr=role(p);z=_zonal(gdf,p);z.update({"path":str(p),"role":rr});stats.append(z)
        if rr=="AGB":agb=z["mean"]
        elif rr=="UNCERTAINTY":unc=z["mean"]
    if agb is not None:
        if not 0<=agb<=1500:raise ValueError("Raster AGB fora de faixa plausível; confirme unidades Mg/ha.")
        if unc is None:
            a=next(x for x in stats if x["role"]=="AGB");unc=a["sd"]/math.sqrt(max(a["n"],1));kind="erro-padrão espacial; não substitui erro do modelo"
        else:kind="camada de incerteza do produto"
        return {"status":"SAR_PROCESSADO","agb_mg_ha":agb,"uncertainty_mg_ha":unc,"uncertainty_kind":kind,"stats":stats,"source":"produto SAR/AGB efetivamente processado"}
    refs=[m for m in MODEL_REGISTRY if m["biome"]==biome]
    return {"status":"SAR_ATRIBUTOS_SEM_MODELO","agb_mg_ha":None,"uncertainty_mg_ha":None,"stats":stats,"references":refs,"message":"SAR processado, mas sem modelo executável validado com atributos compatíveis; AGB não foi inventada."}
