import math,re,hashlib,time
from pathlib import Path
import numpy as np, requests
ASF_SEARCH="https://api.daac.asf.alaska.edu/services/search/param"
CDSE_STAC="https://stac.dataspace.copernicus.eu/v1/search"
MODEL_REGISTRY=[
{"id":"ESA_BIOMASS_FP_AGB_L2B","biome":"*","physiognomy":"florestas no domínio válido do produto ESA","domain":"ESA BIOMASS Level-2B AGB; usar AGB e AGB_Std_Dev do produto, sem recalibrar como backscatter","bands":["P"],"sensor":"ESA BIOMASS P-band","algorithm":"produto geofísico oficial L2B","predictors":["AGB"],"coefficients":None,"validation":"qualidade/incerteza fornecida pelo produto","institution":"ESA","executable":True,"execution_mode":"direct_product","constraints":"respeitar quality flags e cobertura do FP_AGB_L2B"},
{"id":"ESA_CCI_BIOMASS_V6","biome":"*","physiognomy":"cobertura florestal global","domain":"mapa AGB CCI v6; fusão SAR L+C","bands":["L","C"],"sensor":"ALOS-2 PALSAR-2 + Sentinel-1","algorithm":"BIOMASAR-L/BIOMASAR-C + fusão","predictors":["AGB"],"coefficients":None,"validation":"incerteza do produto CCI","institution":"ESA CCI Biomass","executable":True,"execution_mode":"direct_product","constraints":"produto histórico; não rotular como P-band nem como estimativa local calibrada"},
{"id":"PEREIRA_2018_VARZEA_POL","biome":"Amazônia","physiognomy":"várzea/floresta inundável","domain":"várzea amazônica; full-pol PALSAR; 18 amostras","bands":["L"],"sensor":"ALOS/PALSAR-1 PLR","algorithm":"GLM log-link com atributos polarimétricos","predictors":["V_ZD","Phi_alphaS1","Phi_alphaS2"],"coefficients":None,"r2":0.88,"rmse_mg_ha":74.59,"bias_mg_ha":-4.9,"validation":"cross-validation; erro relativo ~46%","doi":"10.3390/rs10091355","institution":"INPE/UNESP/colaboradores","executable":False,"constraints":"preditores e desempenho verificados; coeficientes numéricos não publicados na tabela principal, portanto não inventar execução"},
{"id":"PEREIRA_2018_VARZEA_XL","biome":"Amazônia","physiognomy":"várzea/floresta inundável","domain":"várzea amazônica; PALSAR + TerraSAR-X + Radarsat-2","bands":["L","X","C"],"sensor":"ALOS/PALSAR + TerraSAR-X + Radarsat-2","algorithm":"GLM multifrequência","predictors":["PL_HV_HH","RC2_HV_HH","TX_HH_dB"],"coefficients":None,"r2":0.88,"rmse_mg_ha":107.32,"bias_mg_ha":-11.4,"validation":"cross-validation","doi":"10.3390/rs10091355","institution":"INPE/UNESP/colaboradores","executable":False,"constraints":"usar para seleção/aferição; sem coeficientes publicados não executar numericamente"},

{"id":"CASSOL_2021","biome":"Amazônia","domain":"floresta secundária","bands":["L"],"sensor":"ALOS-2/PALSAR-2","doi":"10.1080/01431161.2021.1903615","institution":"INPE/NCEO"},
{"id":"CASSOL_2019_EQ13","biome":"Amazônia","physiognomy":"floresta secundária","domain":"Santarém, PA; florestas secundárias; quad-pol PALSAR-2","bands":["L"],"sensor":"ALOS-2/PALSAR-2 SLC quad-pol","algorithm":"MLR polarimétrica Eq.13","predictors":["Neumann_tau","tau_s3","T23_imag","SE_Pnorm","SE_norm","T12_realB"],"coefficients":{"intercept":-1151.1,"Neumann_tau":516.6,"tau_s3":0.96,"T23_imag":2809.1,"SE_Pnorm":592.91,"SE_norm":319.52,"T12_realB":2306.73},"r2":0.51,"rmse_mg_ha":38.7,"bias_mg_ha":2.1,"uncertainty_pct":18.6,"validation":"bootstrap 100 repetições, 80/20","doi":"10.3390/rs11010059","institution":"INPE/colaboradores","executable":True,"constraints":"somente com os seis atributos polarimétricos definidos no artigo; não aplicar a HH/HV simples"},
{"id":"VARZEA_2018","biome":"Amazônia","domain":"floresta de várzea","bands":["L","X"],"sensor":"ALOS/PALSAR + TerraSAR-X","algorithm":"regressão selecionada por CV","coefficients":None,"r2":0.46,"rmse_mg_ha":74.6,"validation":"cross-validation","doi":"10.3390/rs10091355","executable":False},
{"id":"CERRADO_RIO_VERMELHO_2020","biome":"Cerrado","domain":"vegetação lenhosa; Rio Vermelho","bands":["L"],"sensor":"ALOS-2/PALSAR-2 + Landsat 8 + LiDAR","algorithm":"Random Forest","coefficients":None,"r2":0.89,"rmse_mg_ha":7.58,"bias_mg_ha":0.43,"validation":"k-fold + jackknife; referência LiDAR","doi":"10.3390/rs12172685","executable":False},
{"id":"KUNTSCHIK_2004_CERRADAO_JERS1","biome":"Cerrado","physiognomy":"cerradão/fisionomias florestais","domain":"sudoeste de São Paulo","bands":["L"],"sensor":"JERS-1 SAR","algorithm":"regressão radar-biomassa","coefficients":None,"validation":"tese USP; equação confirmada, coeficientes pendentes de verificação integral","doi":"10.11606/T.41.2004.tde-14012005-084048","institution":"USP","executable":False},
{"id":"CAATINGA_SENTINEL_2020","biome":"Caatinga","physiognomy":"estratos de Caatinga/FTSS","domain":"Caatinga brasileira","bands":["C"],"sensor":"Sentinel-1 + Sentinel-2","algorithm":"regressão linear múltipla","coefficients":None,"validation":"campo + sensoriamento remoto","institution":"UFC","executable":False},
{"id":"ATLANTIC_2026_PALSAR2_S2","biome":"Mata Atlântica","physiognomy":"florestas montanas/topografia complexa","domain":"inventário de campo + PALSAR-2/Sentinel-2","bands":["L"],"sensor":"PALSAR-2 + Sentinel-2","algorithm":"machine learning multissensor","coefficients":None,"r2":0.64,"rmse_mg_ha":51.10,"validation":"benchmark com inventário de campo","doi":"10.1016/j.isprsjprs.2026.04.022","institution":"ISPRS JPRS","executable":False}

]
def _wkt(gdf):return gdf.to_crs(4326).geometry.union_all().wkt
def discover_asf(gdf,limit=25):
    out=[]
    for dataset,band in [("ALOS PALSAR","L"),("NISAR","L"),("SENTINEL-1","C")]:
        try:
            r=requests.get(ASF_SEARCH,params={"dataset":dataset,"intersectsWith":_wkt(gdf),"output":"geojson","maxResults":limit},timeout=(10,45));r.raise_for_status();js=r.json();fs=js.get("features",[])
            out.append({"provider":"ASF/NASA","dataset":dataset,"band":band,"count":len(fs),"items":[{"id":x.get("properties",{}).get("sceneName") or x.get("id"),
                "properties":x.get("properties",{}),
                "download_url":next((v for k,v in x.get("properties",{}).items() if isinstance(v,str) and v.startswith("http") and ("url" in k.lower() or "download" in k.lower())),None),
                "raw":x} for x in fs]})
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
def _provenance(origin, source, sensor=None, band=None, product=None, model=None, scene_ids=None):
    return {"data_origin":origin,"source":source,"sensor":sensor,"band":band,"product":product,"model_id":model,"scene_ids":scene_ids or []}

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
        return {"status":"SAR_PROCESSADO","agb_mg_ha":agb,"uncertainty_mg_ha":unc,"uncertainty_kind":kind,"stats":stats,**_provenance("SAR","produto SAR/AGB efetivamente processado",product="raster AGB")}
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
BUILTIN_LITERATURE=[
 {"biome":"Amazônia","phys":[],"mean":220.0,"low":110.0,"high":360.0,"source":"biblioteca científica interna — síntese Amazônia","quality":"triagem"},
 {"biome":"Mata Atlântica","phys":[],"mean":170.0,"low":80.0,"high":300.0,"source":"biblioteca científica interna — síntese Mata Atlântica","quality":"triagem"},
 {"biome":"Cerrado","phys":[],"mean":65.0,"low":25.0,"high":140.0,"source":"biblioteca científica interna — síntese Cerrado","quality":"triagem"},
 {"biome":"Caatinga","phys":[],"mean":35.0,"low":12.0,"high":80.0,"source":"biblioteca científica interna — síntese Caatinga","quality":"triagem"}
]
def literature_fallback(biome,phys,library_rows=None):
    rows=list(library_rows or BUILTIN_LITERATURE)
    # only studies with an explicit compatible mean are eligible for a numerical fallback
    ok=[]
    p=(phys or "").lower()
    for r in rows:
        if r.get("biome")==biome and r.get("mean") is not None and (not r.get("phys") or any(x.lower() in p for x in r["phys"])):ok.append(r)
    if not ok:return {"available":False,"reason":"Biblioteca ainda não contém médias AGB explícitas e metodologicamente compatíveis para este estrato."}
    vals=np.array([float(x["mean"]) for x in ok]);mean=float(vals.mean())
    if len(vals)>1:
        sd=float(vals.std(ddof=1)); kind="desvio-padrão entre estudos; não IC95%"
    else:
        r=ok[0]; low=r.get("low"); high=r.get("high")
        sd=float(max(mean-float(low),float(high)-mean)) if low is not None and high is not None else float(r.get("sd") or r.get("rmse") or mean*.30)
        kind="amplitude bibliográfica conservadora; não é erro estatístico nem IC95%"
    return {"available":True,"agb_mg_ha":mean,"uncertainty_mg_ha":sd,"uncertainty_kind":kind,"n_studies":len(ok),"studies":ok,
      "status":"ESTIMATIVA BIBLIOGRÁFICA — SAR NÃO PROCESSÁVEL NESTA EXECUÇÃO","source":"biblioteca científica interna"}

def process_nisar_gcov(gdf,h5_path):
    """Read calibrated NISAR L2 GCOV covariance terms and derive polygon statistics.
    GCOV values are gamma0 power; no fabricated AGB is returned without a compatible model."""
    import h5py
    from pyproj import CRS, Transformer
    from shapely.ops import transform as shp_transform
    terms={}
    with h5py.File(h5_path,"r") as h:
        base="/science/LSAR/GCOV/grids/frequencyA"
        if base not in h: raise ValueError("Arquivo não contém NISAR L2 GCOV frequencyA.")
        g=h[base]
        x=np.asarray(g["xCoordinates"][:],dtype=float); y=np.asarray(g["yCoordinates"][:],dtype=float)
        epsg=None
        for key in ("projection","projectionEPSG","epsg"):
            if key in g:
                try: epsg=int(np.asarray(g[key])[()])
                except: pass
        if epsg is None:
            # GCOV commonly stores projection metadata on datasets/groups.
            for obj in (g, h["/science/LSAR/GCOV"]):
                for key,val in obj.attrs.items():
                    if "epsg" in str(key).lower():
                        try: epsg=int(val)
                        except: pass
        if epsg is None: raise ValueError("EPSG do grid GCOV não identificado.")
        geom=gdf.to_crs(epsg).geometry.union_all()
        minx,miny,maxx,maxy=geom.bounds
        ix=np.where((x>=minx)&(x<=maxx))[0]; iy=np.where((y>=miny)&(y<=maxy))[0]
        if not len(ix) or not len(iy): raise ValueError("GCOV sem interseção com o polígono.")
        x0,x1=int(ix.min()),int(ix.max())+1; y0,y1=int(iy.min()),int(iy.max())+1
        # Pixel-centre mask, robust to ascending/descending y.
        xx,yy=np.meshgrid(x[x0:x1],y[y0:y1])
        try:
            import shapely
            mask=shapely.contains_xy(geom,xx,yy)
        except Exception:
            from shapely.geometry import Point
            mask=np.vectorize(lambda a,b: geom.contains(Point(float(a),float(b))))(xx,yy)
        for name in ("HHHH","HVHV","VVVV","VHVH","RHRH","RVRV"):
            if name not in g: continue
            a=np.asarray(g[name][y0:y1,x0:x1],dtype=float)
            v=a[mask & np.isfinite(a) & (a>0)]
            if not len(v): continue
            db=10*np.log10(v)
            terms[name]={"mean_power":float(v.mean()),"mean_db":float(db.mean()),"sd_db":float(db.std(ddof=1)) if len(db)>1 else 0.0,"n":int(len(v))}
    if not terms: raise ValueError("Nenhum termo polarimétrico GCOV válido dentro do polígono.")
    features={}
    if "HHHH" in terms: features["L_HH_dB"]=terms["HHHH"]["mean_db"]
    hv="HVHV" if "HVHV" in terms else ("VHVH" if "VHVH" in terms else None)
    if hv: features["L_HV_dB"]=terms[hv]["mean_db"]
    if "VVVV" in terms: features["L_VV_dB"]=terms["VVVV"]["mean_db"]
    if "L_HH_dB" in features and "L_HV_dB" in features: features["L_HV_HH_dB"]=features["L_HV_dB"]-features["L_HH_dB"]
    return {"status":"NISAR_GCOV_PROCESSADO","features":features,"terms":terms,"product":"NISAR L2 GCOV PROVISIONAL","band":"L"}

def select_executable_model(biome,phys,features):
    """Strict compatibility: executable, biome/physiognomy domain and all predictors present."""
    pp=(phys or "").lower()
    cand=[]
    for m in MODEL_REGISTRY:
        if not m.get("executable") or m.get("execution_mode")=="direct_product": continue
        if m.get("biome") not in (biome,"*"): continue
        mp=(m.get("physiognomy") or "").lower()
        if mp and pp and not any(t in pp for t in re.split(r"[/,; ]+",mp) if len(t)>4): continue
        pred=m.get("predictors") or []
        if pred and all(p in features for p in pred): cand.append(m)
    cand.sort(key=lambda m:(m.get("rmse_mg_ha") is None,m.get("rmse_mg_ha") or 1e9))
    return cand[0] if cand else None

def analyze_nisar_gcov(gdf,h5_path,biome,phys):
    q=process_nisar_gcov(gdf,h5_path); m=select_executable_model(biome,phys,q["features"])
    if not m:
        return {"status":"SAR_ATRIBUTOS_SEM_MODELO","agb_mg_ha":None,"data_origin":"SAR_NAO_PROCESSADO",
                "source":"NISAR L2 GCOV processado; sem equação executável compatível",
                "product":q["product"],"band":"L","features":q["features"],"terms":q["terms"],
                "message":"NISAR GCOV foi efetivamente processado, mas nenhum modelo executável do catálogo aceita exatamente estes preditores e esta fitofisionomia."}
    r=execute_registered_model(m["id"],q["features"])
    return {"status":"SAR_PROCESSADO","agb_mg_ha":r["agb_mg_ha"],"uncertainty_mg_ha":r.get("rmse_mg_ha"),
            "uncertainty_kind":"RMSE de validação do modelo","data_origin":"SAR_L_MODELO","source":m.get("source") or m.get("doi"),
            "sensor":"NISAR","band":"L","product":q["product"],"model_id":m["id"],"features":q["features"],"terms":q["terms"]}

def automatic_pipeline(gdf,biome,phys,offline_token="",cache=None,library_rows=None,edl_user="",edl_password=""):
    cache=cache or str(Path.home()/".enform_verde"/"sar")
    audit={"biomass_l2b":None,"cci":None,"asf":None,"warnings":[]}
    # 1 ESA BIOMASS. Availability without credentials is recorded, not treated as a fatal error yet.
    try:
        l2items=maap_search(gdf,"BiomassLevel2b",limit=100,product_type="FP_AGB_L2B")
    except Exception as e:
        l2items=[];audit["warnings"].append("BIOMASS catalogue: "+str(e))
    audit["biomass_l2b"]={"count":len(l2items)}
    if l2items and offline_token:
        try:
            d=download_maap_agb(gdf,offline_token,Path(cache)/"biomass")
            if d["paths"]:
                r=process_real_sar(gdf,d["paths"],biome,phys);r["audit"]=audit;r["paths"]=d["paths"];r["data_origin"]="SAR";return r
        except Exception as e:audit["warnings"].append("BIOMASS download/process: "+str(e))
    elif l2items:audit["warnings"].append("BIOMASS disponível; token ESA MAAP não informado.")
    # 2 CCI historical SAR-derived AGB: attempt before raw L-band auth roadblock.
    try:
        cci=cci_history(gdf,Path(cache)/"cci",offline_token or None)
        audit["cci"]={"count":cci["items"],"downloaded":len(cci["paths"])}
        if cci["paths"]:
            r=process_real_sar(gdf,cci["paths"],biome,phys);r["audit"]=audit;r["paths"]=cci["paths"];r["historical"]=True;r["data_origin"]="SAR / MAPEAMENTO";return r
    except Exception as e:audit["cci"]={"error":str(e)}
    # 3 L-band: discovery plus authenticated Earthdata/ASF download when credentials are supplied.
    # Catalogue presence alone is never treated as a processed measurement.

    asf=discover_asf(gdf,limit=50);audit["asf"]=asf
    lcount=sum(x["count"] for x in asf if x["band"]=="L")
    if lcount and edl_user and edl_password:
        try:
            from lband_preprocess import preprocess_lband
            cands=[it for group in asf if group.get("band")=="L" for it in group.get("items",[]) if it.get("download_url")]
            # Prefer calibrated NISAR PROVISIONAL / GCOV, then other NISAR, then ALOS.
            def _rank(it):
                t=(str(it.get("id",""))+" "+str(it.get("properties",{}))).upper()
                return (0 if ("NISAR" in t and "PROVISIONAL" in t and "GCOV" in t) else
                        1 if ("NISAR" in t and "PROVISIONAL" in t) else
                        2 if "NISAR" in t else 3)
            cands=sorted(cands,key=_rank)
            cand=cands[0] if cands else None
            if cand:
                url=cand["download_url"]; dl=Path(cache)/"asf"; dl.mkdir(parents=True,exist_ok=True)
                target=dl/Path(url.split("?")[0]).name
                if not target.exists():
                    sess=requests.Session(); sess.auth=(edl_user,edl_password)
                    with sess.get(url,stream=True,timeout=(10,240),allow_redirects=True) as rr:
                        rr.raise_for_status()
                        with open(target,"wb") as out:
                            for chunk in rr.iter_content(8*1024*1024):
                                if chunk: out.write(chunk)
                pre=preprocess_lband(target,dl/("proc_"+target.stem))
                audit["asf_download"]={"scene":cand.get("id"),"url_found":True,"preprocess":pre.get("status"),"candidate_count":len(cands)}
                if pre.get("rasters"):
                    pr=process_real_sar(gdf,pre["rasters"],biome,phys)
                    if pr.get("agb_mg_ha") is not None:
                        pr["audit"]=audit; pr["data_origin"]="SAR_L"; pr["paths"]=pre["rasters"]; return pr
                    audit["warnings"].append("L-band baixada/processada, mas não existe modelo executável compatível com os atributos desta cena.")
        except Exception as e:
            audit["warnings"].append("ASF L-band download/process: "+str(e))
    elif lcount:
        audit["warnings"].append(f"{lcount} produto(s) L-band catalogados; informe Earthdata Login para download/processamento automático.")
    # 4 Guaranteed analytical result. Literature is secondary and explicitly labelled when SAR cannot be processed now.
    lit=literature_fallback(biome,phys,library_rows)
    return {"status":"SAR_NAO_PROCESSADO","agb_mg_ha":None,"uncertainty_mg_ha":None,
            "data_origin":"SAR_NAO_PROCESSADO","source":"nenhum produto SAR quantitativo processado nesta execução",
            "audit":audit,"literature_reference":lit,
            "message":"Há cobertura/produtos SAR catalogados, mas nenhum produto quantitativo/modelo compatível foi processado. A referência bibliográfica foi mantida separada e NÃO foi usada como resultado SAR."}


def execute_registered_model(model_id,features):
    m=next((x for x in MODEL_REGISTRY if x["id"]==model_id),None)
    if not m or not m.get("executable"):raise ValueError("Modelo não executável ou ausente.")
    co=m.get("coefficients") or {};pred=m.get("predictors") or []
    missing=[x for x in pred if x not in features]
    if missing:raise ValueError("Preditores obrigatórios ausentes: "+", ".join(missing))
    y=float(co.get("intercept",0.0))
    for x in pred:y+=float(co[x])*float(features[x])
    return {"agb_mg_ha":max(0.0,y),"model":model_id,"rmse_mg_ha":m.get("rmse_mg_ha"),"bias_mg_ha":m.get("bias_mg_ha"),"validation":m.get("validation"),"doi":m.get("doi")}
def model_registry_rows():
    return [{k:m.get(k) for k in ("id","biome","physiognomy","domain","sensor","algorithm","predictors","coefficients","rmse_mg_ha","bias_mg_ha","r2","validation","doi","institution","executable","constraints")} for m in MODEL_REGISTRY]
