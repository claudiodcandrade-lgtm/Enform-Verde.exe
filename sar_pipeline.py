import math,re
from pathlib import Path
import numpy as np, requests
ASF_SEARCH="https://api.daac.asf.alaska.edu/services/search/param"
CDSE_STAC="https://stac.dataspace.copernicus.eu/v1/search"
MODEL_REGISTRY=[
{"id":"CASSOL_2021","biome":"Amazônia","domain":"floresta secundária","bands":["L"],"sensor":"ALOS-2/PALSAR-2","doi":"10.1080/01431161.2021.1903615","institution":"INPE/NCEO"},
{"id":"CASSOL_2019","biome":"Amazônia","domain":"floresta secundária; Santarém","bands":["L"],"sensor":"ALOS-2/PALSAR-2","algorithm":"MLR polarimétrica","coefficients":None,"r2":0.51,"rmse_mg_ha":38.7,"bias_mg_ha":2.1,"uncertainty_pct":18.6,"validation":"bootstrap 100 repetições, 80/20","doi":"10.3390/rs11010059","institution":"INPE/NCEO","executable":False},
{"id":"VARZEA_2018","biome":"Amazônia","domain":"floresta de várzea","bands":["L","X"],"sensor":"ALOS/PALSAR + TerraSAR-X","algorithm":"regressão selecionada por CV","coefficients":None,"r2":0.46,"rmse_mg_ha":74.6,"validation":"cross-validation","doi":"10.3390/rs10091355","executable":False},
{"id":"CERRADO_RIO_VERMELHO_2020","biome":"Cerrado","domain":"vegetação lenhosa; Rio Vermelho","bands":["L"],"sensor":"ALOS-2/PALSAR-2 + Landsat 8 + LiDAR","algorithm":"Random Forest","coefficients":None,"r2":0.89,"rmse_mg_ha":7.58,"bias_mg_ha":0.43,"validation":"k-fold + jackknife; referência LiDAR","doi":"10.3390/rs12172685","executable":False}
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


MAAP_STAC="https://catalog.maap.eo.esa.int/catalogue/"
MAAP_TOKEN_URL="https://iam.maap.eo.esa.int/realms/esa-maap/protocol/openid-connect/token"
def maap_access_token(offline_token):
    if not offline_token:raise ValueError("Informe o offline token ESA MAAP. Ele não é armazenado pelo Enform Verde.")
    r=requests.post(MAAP_TOKEN_URL,data={"client_id":"offline-token","client_secret":"p1eL7uonXs6MDxtGbgKdPVRAmnGxHpVE","grant_type":"refresh_token","refresh_token":offline_token,"scope":"offline_access openid"},timeout=(10,45));r.raise_for_status()
    t=r.json().get("access_token")
    if not t:raise RuntimeError("A ESA MAAP não retornou access_token.")
    return t
def maap_search(gdf,collection,limit=50,product_type=None):
    geom=gdf.to_crs(4326).geometry.union_all().__geo_interface__
    body={"collections":[collection],"intersects":geom,"limit":limit}
    r=requests.post(MAAP_STAC+"search",json=body,timeout=(10,60));r.raise_for_status()
    fs=r.json().get("features",[])
    if product_type:
        fs=[x for x in fs if product_type in (x.get("id","")+" "+str(x.get("properties",{})))]
    return fs
def _download(url,out,token=None):
    h={"Authorization":"Bearer "+token} if token else {}
    with requests.get(url,headers=h,stream=True,timeout=(10,180)) as r:
        r.raise_for_status()
        with open(out,"wb") as f:
            for c in r.iter_content(8*1024*1024):
                if c:f.write(c)
    return str(out)
def _raster_assets(item):
    out=[]
    for k,a in (item.get("assets") or {}).items():
        href=a.get("href",""); typ=(a.get("type") or "").lower()
        if href and (href.lower().endswith((".tif",".tiff")) or "geotiff" in typ):out.append((k,href))
    return out
def download_maap_agb(gdf,offline_token,cache):
    items=maap_search(gdf,"BiomassLevel2b",limit=100,product_type="FP_AGB_L2B")
    if not items:return {"available":False,"paths":[],"items":0,"reason":"FP_AGB_L2B sem cobertura no polígono"}
    token=maap_access_token(offline_token);Path(cache).mkdir(parents=True,exist_ok=True);paths=[]
    for it in items:
        for k,url in _raster_assets(it):
            if any(x in k.lower()+url.lower() for x in ["agb","biomass","uncert","std","sigma"]):
                p=Path(cache)/(it.get("id","biomass")+"_"+Path(url.split("?")[0]).name)
                if not p.exists():_download(url,p,token)
                paths.append(str(p))
    return {"available":True,"paths":paths,"items":len(items),"reason":None}
def cci_history(gdf,cache,offline_token=None):
    # ESA MAAP local collection. Search is public; asset access may require ESA bearer token.
    items=maap_search(gdf,"CCIBiomassV5.01",limit=100)
    if not items:return {"available":False,"paths":[],"items":0}
    token=maap_access_token(offline_token) if offline_token else None
    Path(cache).mkdir(parents=True,exist_ok=True);paths=[]
    for it in items:
        for k,url in _raster_assets(it):
            if any(x in k.lower()+url.lower() for x in ["agb","biomass","uncert","std"]):
                p=Path(cache)/("cci_"+Path(url.split("?")[0]).name)
                try:
                    if not p.exists():_download(url,p,token)
                    paths.append(str(p))
                except Exception:pass
    return {"available":True,"paths":paths,"items":len(items)}
LITERATURE=[
{"biome":"Amazônia","phys":["secund","sucess"],"mean":None,"rmse":38.7,"bias":2.1,"r2":0.51,"cv":"bootstrap 100 repetições; 80/20","source":"Cassol et al. 2019","doi":"10.3390/rs11010059","note":"referência de desempenho; média AGB não extraída para fallback"},
{"biome":"Amazônia","phys":["várzea","varzea","aluvial"],"mean":None,"rmse":74.6,"bias":None,"r2":0.46,"cv":"cross-validation","source":"Martins et al. 2018","doi":"10.3390/rs10091355","note":"referência L-band várzea; média não usada sem valor compatível"},
{"biome":"Cerrado","phys":["cerrado","savanna","savana"],"mean":None,"rmse":7.58,"bias":0.43,"r2":0.89,"cv":"k-fold/jackknife","source":"Silva et al. 2020","doi":"10.3390/rs12172685","note":"Rio Vermelho; referência de desempenho, não média nacional"}
]
def literature_fallback(biome,phys,library_rows=None):
    rows=list(library_rows or [])
    # only studies with an explicit compatible mean are eligible for a numerical fallback
    ok=[]
    p=(phys or "").lower()
    for r in rows:
        if r.get("biome")==biome and r.get("mean") is not None and (not r.get("phys") or any(x.lower() in p for x in r["phys"])):ok.append(r)
    if not ok:return {"available":False,"reason":"Biblioteca ainda não contém médias AGB explícitas e metodologicamente compatíveis para este estrato."}
    vals=np.array([float(x["mean"]) for x in ok]);mean=float(vals.mean())
    sd=float(vals.std(ddof=1)) if len(vals)>1 else float(ok[0].get("sd") or ok[0].get("rmse") or mean*.30)
    return {"available":True,"agb_mg_ha":mean,"uncertainty_mg_ha":sd,"n_studies":len(ok),"studies":ok,"status":"ESTIMATIVA BIBLIOGRÁFICA — SAR INDISPONÍVEL"}
def automatic_pipeline(gdf,biome,phys,offline_token="",cache=None,library_rows=None):
    cache=cache or str(Path.home()/".enform_verde"/"sar")
    audit={"biomass_l2b":None,"cci":None,"asf":None}
    # Priority 1: ESA BIOMASS P-band L2B AGB.
    l2items=maap_search(gdf,"BiomassLevel2b",limit=100,product_type="FP_AGB_L2B")
    audit["biomass_l2b"]={"count":len(l2items)}
    if l2items:
        if not offline_token:return {"status":"SAR_AVAILABLE_AUTH_REQUIRED","audit":audit,"message":"FP_AGB_L2B existe no polígono. Informe o token ESA MAAP; fallback bibliográfico é proibido porque SAR está disponível."}
        d=download_maap_agb(gdf,offline_token,Path(cache)/"biomass")
        if d["paths"]:
            r=process_real_sar(gdf,d["paths"],biome,phys);r["audit"]=audit;r["paths"]=d["paths"];return r
        return {"status":"SAR_AVAILABLE_PROCESSING_FAILED","audit":audit,"message":"FP_AGB_L2B existe, mas nenhum raster AGB utilizável foi obtido. Fallback bibliográfico é proibido."}
    # Priority 2: L-band discovery. Presence blocks literature fallback.
    asf=discover_asf(gdf,limit=50);audit["asf"]=asf
    lcount=sum(x["count"] for x in asf if x["band"]=="L")
    if lcount:
        return {"status":"SAR_L_AVAILABLE_DOWNLOAD_REQUIRED","audit":audit,"message":f"{lcount} produto(s) L-band encontrados. Configure credencial NASA Earthdata/ASF para download; fallback bibliográfico é proibido."}
    # CCI is SAR-derived historical AGB and should be used before literature.
    try:
        cci=cci_history(gdf,Path(cache)/"cci",offline_token or None);audit["cci"]={"count":cci["items"],"downloaded":len(cci["paths"])}
        if cci["paths"]:
            r=process_real_sar(gdf,cci["paths"],biome,phys);r["audit"]=audit;r["paths"]=cci["paths"];r["historical"]=True;return r
    except Exception as e:audit["cci"]={"error":str(e)}
    # Only here is literature allowed: no P-band L2B and no L-band coverage and no usable CCI.
    r=literature_fallback(biome,phys,library_rows);r["audit"]=audit
    return r
