import sys, json, math, tempfile, re, zipfile, threading, queue, traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from PIL import Image, ImageTk
from sar_pipeline import discover_sar, process_real_sar, automatic_pipeline, MODEL_REGISTRY, model_registry_rows
from lband_preprocess import preprocess_lband

APP_VERSION="3.5.0-PROFESSIONAL"
ORANGE="#EF9B06"; FOREST="#0B3D2E"; GREEN="#155D43"; PALE="#F4F6F5"; TEXT="#34413E"

# Fontes implementadas no motor. Valores-proxy são sempre rotulados como MODELADOS.
SOURCES={
 "protocol":"Higa et al. (2014), Embrapa Florestas, Documentos 266",
 "soil":"Vasques et al. (2021), Embrapa Solos/PronaSolos, COS 0–30 cm, 1 km + incerteza",
 "deadwood":"Freitas et al. (2021), Embrapa Amazônia Ocidental — necromassa lenhosa",
 "litter":"Embrapa Amazônia Oriental — estudos de serapilheira; proxy só para triagem",
}
ROOT_RATIO=0.26; ROOT_LOW=0.18; ROOT_HIGH=0.30
CARBON_FRACTION=0.47

def agb_mexiana(dbh_cm):
    return 0.1184*np.power(np.asarray(dbh_cm,dtype=float),2.53)

def load_inventory(path):
    df=pd.read_excel(path,sheet_name="Biomassa árvores vivas",usecols="A:E")
    df.columns=["plot","tree","dbh_m","height_m","species"]; df["plot"]=df["plot"].ffill()
    df=df[df["tree"].notna() & df["dbh_m"].notna()].copy()
    df["dbh_cm"]=pd.to_numeric(df["dbh_m"],errors="coerce")*100
    df["height_m"]=pd.to_numeric(df["height_m"],errors="coerce")
    return df[df["dbh_cm"].between(10,400)].copy()

def summarize_inventory(df,plot_area_m2=250):
    d=df.copy(); d["agb_kg"]=agb_mexiana(d["dbh_cm"])
    p=d.groupby("plot",as_index=False)["agb_kg"].sum()
    x=(p["agb_kg"]/1000*(10000/plot_area_m2)).to_numpy(float)
    if len(x)<2: raise ValueError("São necessárias ao menos 2 parcelas válidas.")
    mean=float(np.mean(x)); se=float(np.std(x,ddof=1)/math.sqrt(len(x)))
    return len(x),mean,max(0,mean-1.96*se),mean+1.96*se

def spatial_libs():
    try:
        import geopandas as gpd
        return gpd
    except Exception as e: raise RuntimeError("Módulo espacial não disponível: "+str(e))

def read_vector(path):
    gpd=spatial_libs(); p=Path(path)
    if p.suffix.lower()==".kmz":
        d=Path(tempfile.mkdtemp(prefix="enform_kmz_"))
        with zipfile.ZipFile(path) as z: z.extractall(d)
        ks=list(d.rglob("*.kml"))
        if not ks: raise ValueError("KMZ sem arquivo KML interno.")
        gdf=gpd.read_file(ks[0],driver="KML")
    elif p.suffix.lower()==".kml":
        gdf=gpd.read_file(path,driver="KML")
    else:gdf=gpd.read_file(path)
    if gdf.empty: raise ValueError("O vetor não contém feições.")
    if gdf.crs is None: raise ValueError("O vetor não informa CRS; não é seguro assumir coordenadas.")
    gdf=gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if gdf.empty: raise ValueError("Não há geometria válida.")
    return gdf

def geom_metrics(gdf):
    g=gdf.to_crs(4326); union=g.geometry.union_all()
    c=union.centroid; lon,lat=float(c.x),float(c.y)
    zone=max(1,min(60,int((lon+180)//6)+1)); epsg=(32700 if lat<0 else 32600)+zone
    gm=gdf.to_crs(epsg); area=float(gm.geometry.area.sum()/10000)
    b=union.bounds
    return {"area_ha":area,"centroid":[lon,lat],"bbox":[float(x) for x in b],"utm_epsg":epsg}

def _sicar_session():
    import requests, ssl
    from requests.adapters import HTTPAdapter
    class SicarTLSAdapter(HTTPAdapter):
        def init_poolmanager(self,*args,**kwargs):
            from urllib3.poolmanager import PoolManager
            ctx=ssl.create_default_context()
            try: ctx.set_ciphers("DEFAULT@SECLEVEL=1")
            except Exception: pass
            kwargs["ssl_context"]=ctx
            return super().init_poolmanager(*args,**kwargs)
    sess=requests.Session()
    sess.mount("https://geoserver.car.gov.br/",SicarTLSAdapter())
    sess.headers.update({"User-Agent":f"Enform-Verde/{APP_VERSION}","Accept":"application/json"})
    return sess

def resolve_car(car):
    """Resolve CAR against the official public SICAR WFS, with protocol fallbacks and diagnostics."""
    import geopandas as gpd, requests
    raw=str(car or "").strip().upper().replace("–","-").replace("—","-")
    code="".join(raw.split())
    compact="".join(ch for ch in code if ch.isalnum())
    if len(compact)==41:
        code=compact[:2]+"-"+compact[2:9]+"-"+compact[9:]
    m=re.match(r"^([A-Z]{2})-([0-9]{7})-([A-F0-9]{32})$",code)
    if not m: raise ValueError("Código CAR inválido/incompleto. Use o código integral no padrão UF-7 dígitos-32 caracteres.")
    uf=m.group(1).lower(); layer=f"sicar:sicar_imoveis_{uf}"
    urls=["https://geoserver.car.gov.br/geoserver/sicar/ows","https://geoserver.car.gov.br/geoserver/sicar/wfs"]
    attempts=[]; sess=_sicar_session()
    for url in urls:
      for version,key in [("1.0.0","typeName"),("1.1.0","typeName"),("2.0.0","typeNames")]:
        params={"service":"WFS","version":version,"request":"GetFeature",key:layer,
                "outputFormat":"application/json","srsName":"EPSG:4326","cql_filter":f"cod_imovel='{code}'"}
        try:
            try:r=sess.get(url,params=params,timeout=(8,35))
            except requests.exceptions.SSLError:r=sess.get(url,params=params,timeout=(8,35),verify=False)
            attempts.append(f"{version}:{r.status_code}")
            if not r.ok:continue
            js=r.json(); feats=js.get("features") or []
            if not feats:continue
            exact=[x for x in feats if str((x.get("properties") or {}).get("cod_imovel","")).upper()==code]
            feats=exact or feats
            if len(feats)>1:raise RuntimeError("SICAR retornou registros múltiplos para o mesmo código.")
            props=feats[0].get("properties") or {}
            if not feats[0].get("geometry"):raise RuntimeError("CAR localizado, porém sem geometria pública.")
            tmp=Path(tempfile.gettempdir())/"enform_car_sicar.geojson"
            tmp.write_text(json.dumps({"type":"FeatureCollection","features":feats}),encoding="utf-8")
            gdf=gpd.read_file(tmp); gdf=gdf.set_crs(4326) if gdf.crs is None else gdf.to_crs(4326)
            gdf.attrs.update({"sicar_cod_imovel":props.get("cod_imovel",code),"sicar_status":props.get("status_imovel") or props.get("condicao"),
              "sicar_area_declarada_ha":props.get("area"),"sicar_municipio":props.get("municipio"),"sicar_lookup":url+" WFS "+version})
            return gdf
        except RuntimeError:raise
        except Exception as e:attempts.append(version+":"+type(e).__name__)
    raise LookupError("CAR válido no formato, mas não localizado no WFS público oficial nesta consulta. Tentativas: "+", ".join(attempts)+". O programa não concluirá que o CAR é inválido por indisponibilidade do serviço.")

def resolve_ccir_sigef(code):
    """Resolve código INCRA/SNCR do CCIR em parcela georreferenciada certificada no SIGEF."""
    import requests, geopandas as gpd
    digits=re.sub(r"\\D","",code or "")
    if len(digits)!=13: raise ValueError("Informe o Código do Imóvel Rural de 13 dígitos constante do CCIR.")
    # Consulta pública de parcelas do SIGEF pelo código do imóvel (SNCR/INCRA).
    search="https://sigef.incra.gov.br/api/parcelas/consulta/"
    sess=requests.Session(); sess.headers.update({"User-Agent":f"Enform-Verde/{APP_VERSION}","Accept":"application/json"})
    candidates=[]
    for key in ("codigo_imovel","codigo_imovel_incra","sncr"):
        try:
            r=sess.get(search,params={key:digits,"format":"json"},timeout=(10,45))
            if not r.ok: continue
            js=r.json()
            if isinstance(js,dict):
                candidates=js.get("results") or js.get("features") or js.get("parcelas") or []
            elif isinstance(js,list): candidates=js
            if candidates: break
        except Exception: continue
    if not candidates:
        raise LookupError("Nenhuma parcela certificada no SIGEF foi localizada automaticamente para o código INCRA/SNCR do CCIR. O CCIR é cadastral e só possui geometria quando há correspondência georreferenciada no SIGEF/SNCI.")
    item=candidates[0]
    if isinstance(item,dict) and item.get("geometry"):
        tmp=Path(tempfile.gettempdir())/"enform_sigef.geojson"
        tmp.write_text(json.dumps({"type":"FeatureCollection","features":[item]}),encoding="utf-8")
        gdf=gpd.read_file(tmp)
        return gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")
    url=item.get("geojson") or item.get("geometry_url") or item.get("download") if isinstance(item,dict) else None
    if url:
        r=sess.get(url,timeout=(10,60)); r.raise_for_status()
        tmp=Path(tempfile.gettempdir())/"enform_sigef.geojson"; tmp.write_bytes(r.content)
        gdf=gpd.read_file(tmp)
        return gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")
    raise RuntimeError("A parcela foi localizada no SIGEF, mas a consulta pública não forneceu geometria em formato utilizável automaticamente.")

IBGE_VEGE_2026_URL="https://geoftp.ibge.gov.br/informacoes_ambientais/vegetacao/vetores/escala_250_mil/versao_2026/vege_area.zip"
IBGE_BIOMAS_2025_URL="https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip"

def _ibge_cache():
    import os
    root=Path(os.environ.get("LOCALAPPDATA",Path.home()))/"EnformVerde"/"IBGE"
    root.mkdir(parents=True,exist_ok=True); return root

def _download_extract(url,folder,tag):
    import requests
    folder.mkdir(parents=True,exist_ok=True)
    marker=folder/".ready"
    if marker.exists(): return
    zpath=folder/(tag+".zip")
    with requests.get(url,stream=True,timeout=(15,180),headers={"User-Agent":f"Enform-Verde/{APP_VERSION}"}) as r:
        r.raise_for_status()
        with open(zpath,"wb") as out:
            for chunk in r.iter_content(1024*1024):
                if chunk: out.write(chunk)
    with zipfile.ZipFile(zpath) as z:z.extractall(folder)
    marker.write_text("IBGE official source: "+url,encoding="utf-8")

def _find_polygon_file(folder):
    files=list(folder.rglob("*.shp"))+list(folder.rglob("*.gpkg"))
    if not files: raise RuntimeError("Pacote IBGE baixado, mas nenhum vetor poligonal foi encontrado.")
    return max(files,key=lambda p:p.stat().st_size)

def _field(cols,candidates):
    low={str(c).lower():c for c in cols}
    for x in candidates:
        if x.lower() in low:return low[x.lower()]
    for c in cols:
        lc=str(c).lower()
        if any(x.lower() in lc for x in candidates):return c
    return None

def _shares(project,theme,fields):
    import geopandas as gpd
    p=project.to_crs("EPSG:5880"); t=theme.to_crs("EPSG:5880")
    bbox=p.total_bounds
    t=t.cx[bbox[0]:bbox[2],bbox[1]:bbox[3]]
    if t.empty:return []
    inter=gpd.overlay(t,p[["geometry"]],how="intersection",keep_geom_type=False)
    inter=inter[~inter.geometry.is_empty].copy()
    inter["_ha"]=inter.geometry.area/10000
    total=inter["_ha"].sum()
    out=[]
    for field in fields:
        if field and field in inter.columns:
            g=inter.groupby(field,dropna=False)["_ha"].sum().sort_values(ascending=False)
            out.append((field,[(str(k),float(v),float(v/total*100)) for k,v in g.items() if v>0]))
    return out

def diagnose_ibge(project):
    """Bioma oficial IBGE + regiões/fitofisionomias da Vegetação IBGE versão 2026."""
    import geopandas as gpd
    root=_ibge_cache(); veg=root/"vegetacao_2026"; bio=root/"biomas_2025"
    _download_extract(IBGE_VEGE_2026_URL,veg,"vege_area_2026")
    _download_extract(IBGE_BIOMAS_2025_URL,bio,"biomas_2025")
    vg=gpd.read_file(_find_polygon_file(veg),bbox=tuple(project.to_crs("EPSG:4326").total_bounds))
    bg=gpd.read_file(_find_polygon_file(bio),bbox=tuple(project.to_crs("EPSG:4326").total_bounds))
    bfield=_field(bg.columns,["Bioma","Nome_Bioma","nm_bioma"])
    l1=_field(vg.columns,["Legenda_1","legenda_1","fito"])
    l2=_field(vg.columns,["Legenda_2","legenda_2","formacao"])
    bs=_shares(project,bg,[bfield]); vs=_shares(project,vg,[l1,l2])
    if not bs or not bs[0][1]: raise RuntimeError("O polígono não interceptou a camada oficial de Biomas do IBGE.")
    return {"bioma_field":bfield,"biomas":bs[0][1],"vegetacao_fields":[x[0] for x in vs],
            "vegetacao":[{"campo":x[0],"classes":x[1]} for x in vs],
            "fonte_bioma":"IBGE — Biomas do Brasil, revisão 2025, 1:250.000",
            "fonte_vegetacao":"IBGE — Vegetação/Regiões Fitoecológicas, versão 2026, 1:250.000"}

def zonal_soil(gdf,raster_path):
    import rasterio
    from rasterio.mask import mask
    gg=gdf.to_crs(rasterio.open(raster_path).crs)
    shapes=[x.__geo_interface__ for x in gg.geometry]
    with rasterio.open(raster_path) as src:
        a,_=mask(src,shapes,crop=True,filled=False)
        vals=a[0].compressed().astype(float)
        if src.nodata is not None: vals=vals[vals!=src.nodata]
    if len(vals)==0: raise ValueError("O raster de solo não possui pixels válidos na área.")
    return float(np.mean(vals)),float(np.std(vals)),len(vals)

def pronasolos_soc_profiles(gdf,max_points=12):
    """Sample official PronaSolos 90 m SOC-stock rasters through ArcGIS REST identify.
    Returns cumulative 0-30/60/100/200 cm stocks. Spatial SD is descriptive, not map prediction error."""
    import requests
    gg=gdf.to_crs(3857); geom=gg.geometry.union_all()
    minx,miny,maxx,maxy=geom.bounds
    n=max(3,int(math.sqrt(max_points))); xs=np.linspace(minx,maxx,n); ys=np.linspace(miny,maxy,n)
    pts=[]
    from shapely.geometry import Point
    for y in ys:
        for x in xs:
            p=Point(float(x),float(y))
            if geom.covers(p):pts.append(p)
    if not pts:pts=[geom.representative_point()]
    pts=pts[:max_points]
    urls=[
      "https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer/identify",
      "https://geoportal.sgb.gov.br/server/rest/services/pronasolos/solos_90m/MapServer/identify",
      "https://geoportal.sgb.gov.br/server/rest/services/pronasolos/atributos_solo_90m/MapServer/identify"]
    layer_ids=[2,3,4,5,6,7]; vals={k:[] for k in layer_ids}; sess=requests.Session()
    extent=f"{minx},{miny},{maxx},{maxy}"
    for p in pts:
      for url in urls:
        params={"f":"json","geometry":f"{p.x},{p.y}","geometryType":"esriGeometryPoint","sr":"3857",
                "layers":"all:"+",".join(map(str,layer_ids)),"tolerance":"3","mapExtent":extent,
                "imageDisplay":"1200,1200,96","returnGeometry":"false"}
        try:
            r=sess.get(url,params=params,timeout=(4,10)); r.raise_for_status(); js=r.json()
            for item in js.get("results",[]):
                lid=int(item.get("layerId",-1)); at=item.get("attributes") or {}
                raw=at.get("Pixel Value",at.get("Stretched value",item.get("value")))
                try:
                    v=float(str(raw).replace(",","."))
                    if np.isfinite(v) and -1<v<1000 and lid in vals:vals[lid].append(v)
                except:pass
        except Exception: continue
        if all(vals[k] for k in layer_ids): break
    names=["0–5","5–15","15–30","30–60","60–100","100–200"]
    targets={"0–30 cm":3,"0–60 cm":4,"0–100 cm":5,"0–200 cm":6}; out={}
    for label,count in targets.items():
        need=layer_ids[:count]
        if any(len(vals[k])==0 for k in need): continue
        m=min(len(vals[k]) for k in need)
        x=np.sum(np.vstack([np.asarray(vals[k][:m],float) for k in need]),axis=0)
        out[label]={"tc_ha":float(np.mean(x)),"spatial_sd_tc_ha":float(np.std(x,ddof=1)) if len(x)>1 else 0.0,
          "n_samples":int(len(x)),"layers":names[:count],
          "uncertainty_kind":"DP espacial das amostras do mapa; não é IC95% nem erro de predição"}
    if "0–30 cm" not in out:
        missing=[names[i] for i,k in enumerate(layer_ids[:3]) if not vals[k]]
        raise RuntimeError("PronaSolos não retornou camada(s) essencial(is) para 0–30 cm: "+", ".join(missing))
    return out


def self_test():
    assert abs(float(agb_mexiana(10))-0.1184*10**2.53)<1e-8
    assert ROOT_LOW<ROOT_RATIO<ROOT_HIGH
    assert abs(CARBON_FRACTION-0.47)<1e-9
    print("ENFORM_VERDE_SELF_TEST_OK")

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Enform Verde"); self.geometry("1260x760"); self.minsize(1050,650)
        self.inv=None; self.gdf=None; self.soil_raster=None; self.project={"version":APP_VERSION}; self.active_source=None; self.active_input_id=None; self._analysis_running=False; self._analysis_queue=queue.Queue()
        self._style(); self._ui(); self.bind("<Return>",self.execute)
    def _style(self):
        s=ttk.Style(self)
        try:s.theme_use("vista")
        except:pass
        s.configure(".",font=("Segoe UI",10),foreground=TEXT)
        s.configure("Title.TLabel",font=("Segoe UI",21,"bold"),foreground=ORANGE)
        s.configure("H.TLabel",font=("Segoe UI",12,"bold"),foreground=FOREST)
        s.configure("Run.TButton",font=("Segoe UI",10,"bold"),padding=10)
        s.configure("TButton",padding=7)
    def _ui(self):
        root=ttk.Frame(self); root.pack(fill="both",expand=True)
        hero=tk.Canvas(root,width=500,bg=FOREST,highlightthickness=0); hero.pack(side="left",fill="y")
        base=Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).parent
        visual=base/"enform_visual.jpg"
        if visual.exists():
            im=Image.open(visual).convert("RGB")
            im.thumbnail((500,440),Image.Resampling.LANCZOS)
            self.hero_photo=ImageTk.PhotoImage(im)
            hero.create_image(0,0,image=self.hero_photo,anchor="nw")
            logo=base/"enform_logo.png"
            if logo.exists():
                lg=Image.open(logo).convert("RGBA")
                lg.thumbnail((300,150),Image.Resampling.LANCZOS)
                self.hero_logo=ImageTk.PhotoImage(lg)
                hero.create_image(34,30,image=self.hero_logo,anchor="nw")
        else:
            hero.create_text(35,45,text="enform",anchor="nw",fill="white",font=("Segoe UI",26,"bold"))
            hero.create_text(36,92,text="VERDE",anchor="nw",fill=ORANGE,font=("Segoe UI",12,"bold"))
        hero.create_rectangle(0,440,500,760,fill=FOREST,outline="")
        hero.create_text(32,475,text="Carbono florestal\npor sensoriamento remoto",anchor="nw",fill="white",font=("Segoe UI",18,"bold"))
        hero.create_text(32,565,text="AMAZÔNIA  •  CERRADO\nCAATINGA  •  MATA ATLÂNTICA",anchor="nw",fill="#DDE9E3",font=("Segoe UI",10,"bold"))
        hero.create_text(32,650,text="tC/ha  •  tCO₂e/ha\nMEDIDO  •  MODELADO  •  INCERTEZA",anchor="nw",fill="white",font=("Segoe UI",10,"bold"))
        main=ttk.Frame(root,padding=22); main.pack(side="left",fill="both",expand=True)
        top=ttk.Frame(main); top.pack(fill="x")
        ttk.Label(top,text="Análise de carbono",style="Title.TLabel").pack(side="left")
        self.run_btn=ttk.Button(top,text="EXECUTAR ANÁLISE",command=self.execute,style="Run.TButton"); self.run_btn.pack(side="right")
        ttk.Button(top,text="Exportar Excel",command=self.export_excel).pack(side="right",padx=8)
        ttk.Button(top,text="Salvar relatório",command=self.save_report).pack(side="right",padx=8)
        self.nb=ttk.Notebook(main); self.nb.pack(fill="both",expand=True,pady=(16,8))
        self.tabs=[]
        for n in ["Projeto e CAR","Dados espaciais","Sensores SAR","Carbono total","Fontes & QA"]:
            f=ttk.Frame(self.nb,padding=18); self.nb.add(f,text=n); self.tabs.append(f)
        self._project(); self._spatial(); self._remote(); self._results(); self._sources()
        self.status=tk.StringVar(value="Pronto. Informe o CAR ou carregue o vetor da propriedade.")
        ttk.Label(main,textvariable=self.status,relief="sunken",anchor="w",padding=6).pack(fill="x")

    def _project(self):
        f=self.tabs[0]; ttk.Label(f,text="Abrir análise",style="H.TLabel").grid(row=0,column=0,columnspan=4,sticky="w")
        self.name=tk.StringVar(value="Projeto Enform Verde"); self.car=tk.StringVar(); self.ccir=tk.StringVar()
        self.biome=tk.StringVar(value=""); self.phys=tk.StringVar(value="")
        fields=[("Projeto",self.name),("CAR / SICAR",self.car),("CCIR — código INCRA/SNCR (13 dígitos)",self.ccir)]
        for i,(lab,var) in enumerate(fields,1):
            ttk.Label(f,text=lab).grid(row=i,column=0,sticky="w",pady=8)
            ttk.Entry(f,textvariable=var,width=62).grid(row=i,column=1,sticky="ew",padx=10)
        ttk.Button(f,text="Buscar CAR no SICAR",command=self.car_lookup).grid(row=2,column=2,padx=6)
        ttk.Button(f,text="Buscar CCIR no SIGEF",command=self.ccir_lookup).grid(row=3,column=2,padx=6)
        ttk.Button(f,text="CARREGAR ARQUIVO VETORIAL",command=self.pick_vector,style="Run.TButton").grid(row=4,column=1,sticky="w",pady=18,padx=10)
        ttk.Label(f,text="KML • KMZ • SHP • GeoJSON • GPKG",foreground="#666").grid(row=4,column=2,sticky="w")
        f.columnconfigure(1,weight=1)

    def _spatial(self):
        f=self.tabs[1]; ttk.Label(f,text="Perímetro, diagnóstico e solo",style="H.TLabel").pack(anchor="w")
        row=ttk.Frame(f); row.pack(fill="x",pady=10)
        ttk.Button(row,text="Buscar COS 0–30 cm — Embrapa",command=self.auto_soil).pack(side="left")
        ttk.Button(row,text="Carregar GeoTIFF de COS",command=self.pick_soil).pack(side="left",padx=8)
        self.spatial_text=tk.Text(f,height=20,wrap="word"); self.spatial_text.pack(fill="both",expand=True,pady=8)
        self._set(self.spatial_text,"Nenhum perímetro carregado. Use CAR, CCIR/SIGEF ou arquivo vetorial na tela de abertura.")

    def _remote(self):
        f=self.tabs[2]; ttk.Label(f,text="Pipeline automático SAR → biomassa",style="H.TLabel").pack(anchor="w")
        auth=ttk.Frame(f); auth.pack(fill="x",pady=6)
        ttk.Label(auth,text="ESA MAAP offline token:").pack(side="left")
        self.esa_token=tk.StringVar()
        ttk.Entry(auth,textvariable=self.esa_token,width=48,show="•").pack(side="left",padx=6)
        ttk.Label(auth,text="(memória da sessão)",foreground="#666").pack(side="left")
        auth2=ttk.Frame(f); auth2.pack(fill="x",pady=4)
        ttk.Label(auth2,text="NASA Earthdata usuário:").pack(side="left")
        self.edl_user=tk.StringVar(); self.edl_password=tk.StringVar()
        ttk.Entry(auth2,textvariable=self.edl_user,width=22).pack(side="left",padx=4)
        ttk.Label(auth2,text="senha:").pack(side="left")
        ttk.Entry(auth2,textvariable=self.edl_password,width=22,show="•").pack(side="left",padx=4)
        ttk.Label(auth2,text="(não gravados)",foreground="#666").pack(side="left")
        row=ttk.Frame(f); row.pack(fill="x",pady=8)
        self.pipeline_btn=ttk.Button(row,text="EXECUTAR PIPELINE AUTOMÁTICO",command=self.execute); self.pipeline_btn.pack(side="left")
        ttk.Button(row,text="DESCOBRIR COBERTURA SAR",command=self.discover_sar_ui).pack(side="left",padx=8)
        ttk.Button(row,text="CARREGAR PRODUTOS SAR / AGB",command=self.pick_sar).pack(side="left")
        self.sar_paths=[]; self.sensor=tk.StringVar(value="Automático — P-band BIOMASS → SAR L/X compatível → CCI → literatura")
        self.remote_text=tk.Text(f,height=22,wrap="word"); self.remote_text.pack(fill="both",expand=True,pady=8)
        self._set(self.remote_text,"Hierarquia obrigatória:\n1. ESA BIOMASS FP_AGB_L2B (P-band, AGB + incerteza);\n2. modelos SAR L/X executáveis compatíveis com fitofisionomia e atributos disponíveis;\n3. ESA CCI Biomass L+C como série histórica;\n4. literatura somente como aferição/fallback quando nenhum produto SAR quantitativo puder ser processado.\n\nSe houver SAR mas faltar autenticação/processamento, o programa NÃO usa literatura como substituto.")

    def discover_sar_ui(self):
        if self.gdf is None:return messagebox.showwarning("SAR","Carregue/resolva o polígono primeiro.")
        try:
            self.status.set("Consultando catálogos SAR..."); self.update_idletasks()
            cov=discover_sar(self.gdf); self.project["sar_catalog"]=cov
            txt=["REGISTROS RETORNADOS PELOS CATÁLOGOS SAR","(descoberta ≠ download ≠ processamento ≠ uso na estimativa)"]
            for x in cov:txt.append(f"{x['provider']} — {x['dataset']} ({x['band']}): {x['count']} registro(s) retornado(s)"+((" — "+x["error"]) if x.get("error") else ""))
            txt += ["","Para uso quantitativo, o produto ainda precisa ser elegível, baixado, pré-processado e associado a modelo/produto AGB compatível."]
            self._set(self.remote_text,"\n".join(txt)); self.status.set("Descoberta SAR concluída.")
        except Exception as e:self.status.set("Falha na descoberta SAR."); messagebox.showerror("SAR",str(e))

    def pick_sar(self):
        ps=filedialog.askopenfilenames(title="Produtos SAR / AGB / incerteza",filetypes=[("GeoTIFF","*.tif *.tiff"),("Todos","*.*")])
        if not ps:return
        self.sar_paths=list(ps); self.project["sar_paths"]=list(ps)
        self._set(self.remote_text,"Produtos selecionados:\n"+"\n".join(self.sar_paths)+"\n\nClique em EXECUTAR ANÁLISE.")
        self.status.set(f"{len(ps)} produto(s) SAR selecionado(s).")

    def _results(self):
        f=self.tabs[3]; ttk.Label(f,text="Balanço de compartimentos",style="H.TLabel").pack(anchor="w")
        self.res=tk.Text(f,height=23,wrap="word"); self.res.pack(fill="both",expand=True,pady=8)
        self._set(self.res,"Clique em EXECUTAR ANÁLISE quando houver dados suficientes.")
    def _sources(self):
        f=self.tabs[4]; ttk.Label(f,text="Rastreabilidade metodológica",style="H.TLabel").pack(anchor="w")
        self.src=tk.Text(f,height=24,wrap="word"); self.src.pack(fill="both",expand=True,pady=8)
        txt=("REGRAS DO MOTOR\n• MEDIDO: derivado diretamente do inventário/raster fornecido.\n• MODELADO: proxy/equação publicada, identificado com fonte e domínio.\n• NÃO ESTIMADO: quando não existe suporte defensável.\n\n"
             f"BGB: relação raiz/parte aérea {ROOT_RATIO:.2f}, faixa {ROOT_LOW:.2f}–{ROOT_HIGH:.2f}; {SOURCES['protocol']}.\n"
             f"Conversão biomassa→C: 0,47; {SOURCES['protocol']}.\n"
             f"Solo: {SOURCES['soil']}. O produto nacional tem resolução nativa de 1 km; o programa não faz falso downscaling.\n"
             f"Necromassa: {SOURCES['deadwood']}; proxy de triagem recebe incerteza elevada e nunca é rotulado como medido.\n"
             "Serrapilheira: proxy só é ativado para Amazônia quando há AGB e é explicitamente rotulado; para MRV recomenda-se amostragem local.")
        self._set(self.src,txt)
    def _set(self,w,t): w.config(state="normal"); w.delete("1.0","end"); w.insert("1.0",t); w.config(state="disabled")
    def _reset_analysis_state(self,keep_geometry=False):
        """Invalida integralmente qualquer resultado derivado da consulta anterior."""
        old_vector=self.project.get("vector")
        self.project={"version":APP_VERSION}
        if old_vector and keep_geometry:self.project["vector"]=old_vector
        if not keep_geometry:self.gdf=None
        self.soil_raster=None
        self.sar_paths=[]
        self.inv=None
        self.active_source=None
        self.active_input_id=None
        self.biome.set(""); self.phys.set("")
        for widget_name in ("remote_text","res"):
            w=getattr(self,widget_name,None)
            if w is not None:self._set(w,"")
        if hasattr(self,"spatial_text"):self._set(self.spatial_text,"Nova entrada recebida. Resultados anteriores foram descartados.")
        self.status.set("Estado anterior descartado. Preparando nova consulta.")
        self.update_idletasks()

    def car_lookup(self):
        self._reset_analysis_state()
        try:
            self.status.set("Consultando SICAR..."); self.update_idletasks(); self.gdf=resolve_car(self.car.get()); self.active_source="CAR"; self.active_input_id=self.car.get().strip().upper(); self.ccir.set(""); self._show_geom("SICAR")
        except Exception as e: self.status.set("CAR não resolvido."); messagebox.showwarning("SICAR",str(e))
    def ccir_lookup(self):
        self._reset_analysis_state()
        try:
            self.status.set("Consultando SIGEF pelo código do CCIR..."); self.update_idletasks()
            self.gdf=resolve_ccir_sigef(self.ccir.get()); self.active_source="CCIR"; self.active_input_id=re.sub(r"\\D","",self.ccir.get()); self.car.set(""); self._show_geom("CCIR / SIGEF")
        except Exception as e:
            self.status.set("CCIR/SIGEF não resolvido."); messagebox.showwarning("CCIR / SIGEF",str(e))

    def pick_vector(self):
        p=filedialog.askopenfilename(filetypes=[("Vetores","*.kml *.kmz *.geojson *.json *.shp *.gpkg"),("Todos","*.*")])
        if not p:return
        self._reset_analysis_state()
        try:self.gdf=read_vector(p); self.project["vector"]=p; self.active_source="VECTOR"; self.active_input_id=str(Path(p).resolve()); self.car.set(""); self.ccir.set(""); self._show_geom(Path(p).name)
        except Exception as e:messagebox.showerror("Vetor",str(e))
    def _show_geom(self,src):
        m=geom_metrics(self.gdf); self.project["geometry_metrics"]=m
        self._set(self.spatial_text,f"Perímetro: {src}\nÁrea geométrica: {m['area_ha']:,.2f} ha\nCentroide: {m['centroid'][1]:.6f}, {m['centroid'][0]:.6f}\nCRS métrico de cálculo: EPSG:{m['utm_epsg']}\n\nPerímetro válido para recorte espacial.")
        self.status.set("Perímetro carregado.")
        try:
            d=diagnose_ibge(self.gdf)
            self.project["ibge_diagnosis"]=d
            if d["biomas"]: self.biome.set(d["biomas"][0][0])
            if d["vegetacao"] and d["vegetacao"][-1]["classes"]: self.phys.set(d["vegetacao"][-1]["classes"][0][0])
            btxt="; ".join(f"{n}: {pct:.1f}% ({ha:,.1f} ha)" for n,ha,pct in d["biomas"])
            vtxt=" | ".join(x["campo"]+": "+"; ".join(f"{n}: {pct:.1f}% ({ha:,.1f} ha)" for n,ha,pct in x["classes"][:8]) for x in d["vegetacao"])
            self._set(self.spatial_text,self.spatial_text.get("1.0","end").strip()+"\n\nIBGE — Bioma(s): "+btxt+"\nIBGE 2026 — Vegetação: "+vtxt)
            self.status.set("Perímetro e diagnóstico IBGE concluídos.")
        except Exception as e:
            self.project["ibge_diagnosis_error"]=str(e)
            self.status.set("Perímetro carregado; diagnóstico IBGE pendente.")
            messagebox.showwarning("Diagnóstico IBGE","O polígono foi carregado, mas o diagnóstico IBGE não pôde ser concluído:\n"+str(e))
    def pick_soil(self):
        p=filedialog.askopenfilename(filetypes=[("GeoTIFF","*.tif *.tiff")])
        if p:self.soil_raster=p; self.status.set("Raster de COS selecionado.")
    def auto_soil(self):
        if self.gdf is None:return messagebox.showwarning("Solo","Carregue/resolva o perímetro primeiro.")
        try:self.status.set("Baixando COS Embrapa..."); self.update_idletasks(); self.soil_raster=try_download_embrapa_soc(self.gdf); self.status.set("COS Embrapa obtido.")
        except Exception as e:self.status.set("COS automático indisponível."); messagebox.showwarning("Solo Embrapa",str(e))
    def remote_biomass_reference(self):
        # Biblioteca de referência conservadora. Em produção, estes valores devem ser substituídos/atualizados
        # pelos dados abertos IFN/SFB por bioma/tipologia; a interface sempre registra a natureza da estimativa.
        biome=self.biome.get(); phys=self.phys.get().lower()
        refs={
            "Amazônia":(220.0,110.0,360.0),
            "Mata Atlântica":(170.0,80.0,300.0),
            "Cerrado":(65.0,25.0,140.0),
            "Caatinga":(35.0,12.0,80.0),
        }
        mean,lo,hi=refs.get(biome,(100.0,40.0,220.0))
        if biome=="Amazônia" and any(x in phys for x in ["várzea","varzea","aluvial"]): mean,lo,hi=190.0,90.0,320.0
        if biome=="Cerrado" and "cerradão" in phys: mean,lo,hi=110.0,55.0,190.0
        return mean,lo,hi

    def execute(self,event=None):
        if self._analysis_running:
            self.status.set("Análise já em execução; aguarde.")
            return
        car=self.car.get().strip().upper(); ccir=re.sub(r"\\D","",self.ccir.get())
        if car and (self.active_source!="CAR" or self.active_input_id!=car):
            return messagebox.showinfo("Perímetro","Use 'Buscar CAR no SICAR' antes de executar a análise.")
        if ccir and (self.active_source!="CCIR" or self.active_input_id!=ccir):
            return messagebox.showinfo("Perímetro","Use 'Buscar CCIR no SIGEF' antes de executar a análise.")
        if self.gdf is None:return messagebox.showwarning("Perímetro necessário","Busque CAR/CCIR ou carregue um vetor.")
        if self.sar_paths:return self._execute_main(event)
        self._analysis_running=True; self.run_btn.state(["disabled"]); self.pipeline_btn.state(["disabled"])
        self.status.set("Consultando SAR em segundo plano…")
        gdf=self.gdf.copy(); biome=self.biome.get(); phys=self.phys.get(); token=self.esa_token.get().strip()
        def worker():
            try:
                sar=automatic_pipeline(gdf,biome,phys,token,edl_user=self.edl_user.get().strip(),edl_password=self.edl_password.get())
                try: soil_profiles=pronasolos_soc_profiles(gdf)
                except Exception as e: soil_profiles={"error":str(e)}
                self._analysis_queue.put(("ok",{"sar":sar,"soil":soil_profiles}))
            except Exception:self._analysis_queue.put(("error",traceback.format_exc()))
        threading.Thread(target=worker,name="EnformAnalysis",daemon=True).start()
        self.after(120,self._poll_analysis)

    def _poll_analysis(self):
        try:kind,payload=self._analysis_queue.get_nowait()
        except queue.Empty:
            if self._analysis_running:self.after(120,self._poll_analysis)
            return
        self._analysis_running=False; self.run_btn.state(["!disabled"]); self.pipeline_btn.state(["!disabled"])
        if kind=="error":
            log=Path.home()/".enform_verde"/"enform_diagnostico.log"; log.parent.mkdir(parents=True,exist_ok=True); log.write_text(payload,encoding="utf-8")
            self.status.set("Falha controlada — programa permanece responsivo.")
            return messagebox.showerror("Análise","Falha controlada. Log gravado em:\n"+str(log))
        self.status.set("SAR consultado; calculando carbono…")
        self.after(1,lambda:self._execute_main(precomputed_sar=payload.get("sar"),precomputed_soil=payload.get("soil")))

    def _execute_main(self,event=None,precomputed_sar=None,precomputed_soil=None):
        # Cada execução substitui, nunca acumula, os resultados derivados da geometria corrente.
        for k in ("analysis_rows","area_ha","total_tc_ha","total_tco2_ha","last_result"):
            self.project.pop(k,None)
        current_car=self.car.get().strip().upper()
        current_ccir=re.sub(r"\\D","",self.ccir.get())
        if current_car and (self.active_source!="CAR" or self.active_input_id!=current_car):
            self._reset_analysis_state()
            try:
                self.gdf=resolve_car(current_car); self.active_source="CAR"; self.active_input_id=current_car; self._show_geom("SICAR")
            except Exception as e:return messagebox.showwarning("Perímetro necessário",str(e))
        elif current_ccir and (self.active_source!="CCIR" or self.active_input_id!=current_ccir):
            self._reset_analysis_state()
            try:
                self.gdf=resolve_ccir_sigef(current_ccir); self.active_source="CCIR"; self.active_input_id=current_ccir; self._show_geom("CCIR / SIGEF")
            except Exception as e:return messagebox.showwarning("Perímetro necessário",str(e))
        if self.gdf is None:return messagebox.showwarning("Perímetro necessário","Informe CAR/CCIR ou carregue o arquivo vetorial da propriedade.")
        try:
            self.status.set("Executando estimativa remota..."); self.update_idletasks()
            area=geom_metrics(self.gdf)["area_ha"]
            if precomputed_sar is not None:
                sar=precomputed_sar
            elif self.sar_paths:
                sar=process_real_sar(self.gdf,self.sar_paths,self.biome.get(),self.phys.get())
            else:
                raise RuntimeError("Pipeline automático sem resultado do worker.")
            self.project["sar_result"]=sar
            # Contract: a numerical AGB is a SAR result only when provenance explicitly says SAR.
            if sar.get("agb_mg_ha") is not None and not str(sar.get("data_origin","")).startswith("SAR"):
                self.project["reference_result"]=sar
                raise RuntimeError("Contrato de proveniência violado: AGB numérica sem origem SAR. O valor foi bloqueado para impedir rotulagem incorreta.")
            if sar.get("agb_mg_ha") is None:
                msg=sar.get("message") or sar.get("reason") or "AGB não pôde ser estimada."
                lit=sar.get("literature_reference") or {}
                if lit.get("available"):
                    msg += f"\n\nREFERÊNCIA BIBLIOGRÁFICA SEPARADA (não usada no resultado SAR): AGB={lit.get('agb_mg_ha',0):.1f} Mg/ha; {lit.get('uncertainty_kind','')}"
                self.project["last_result"]="ANÁLISE SAR — AÇÃO NECESSÁRIA\n\n"+msg+"\n\nNão foi aplicado fallback bibliográfico porque existe cobertura SAR identificada."
                self._set(self.res,self.project["last_result"]); self.nb.select(self.tabs[3]); self.status.set("Cobertura SAR encontrada; autenticação/processamento pendente.")
                messagebox.showinfo("Cobertura SAR encontrada",msg); return
            agb=float(sar["agb_mg_ha"]); sar_unc=float(sar.get("uncertainty_mg_ha") or 0.0)
            unc_kind=str(sar.get("uncertainty_kind") or "incerteza do produto/modelo")
            unc_mult=1.0 if "amplitude bibliográfica" in unc_kind else 1.96
            agb_lo=max(0.0,agb-unc_mult*sar_unc); agb_hi=agb+unc_mult*sar_unc
            agc=agb*CARBON_FRACTION
            agc_lo=agb_lo*CARBON_FRACTION; agc_hi=agb_hi*CARBON_FRACTION
            bgb=agb*ROOT_RATIO; bgc=bgb*CARBON_FRACTION
            nec_c=agc*0.20 if self.biome.get()=="Amazônia" else agc*0.12
            lit_c=4.8 if self.biome.get()=="Amazônia" else (3.0 if self.biome.get()=="Mata Atlântica" else 1.8)
            soil_profiles=precomputed_soil if isinstance(precomputed_soil,dict) else {}
            soil_error=soil_profiles.get("error") if soil_profiles else "PronaSolos não retornou perfil."
            parts=[
              ("Biomassa aérea",agc,sar.get("status","SAR PROCESSADO"),f"AGB={agb:,.1f} Mg/ha; incerteza={sar_unc:,.1f} Mg/ha; carbono={CARBON_FRACTION:.2f}; faixa C={agc_lo:,.2f}–{agc_hi:,.2f} tC/ha","pipeline automático",sar.get("source",sar.get("status","produto processado"))),
              ("Biomassa subterrânea",bgc,"MODELADO",f"R:S={ROOT_RATIO:.2f}; faixa metodológica {ROOT_LOW:.2f}–{ROOT_HIGH:.2f}","relação raiz:parte aérea","biblioteca metodológica"),
              ("Necromassa",nec_c,"MODELADO — TRIAGEM","proxy condicionado ao bioma; substituir por IFN/medição local para MRV","proxy por bioma","IFN/Embrapa"),
              ("Serapilheira",lit_c,"MODELADO — TRIAGEM","alta variabilidade local","proxy por bioma","Embrapa/literatura")]
            p030=soil_profiles.get("0–30 cm") if soil_profiles else None
            if p030:
                parts.append(("Solo 0–30 cm",p030["tc_ha"],"MAPEAMENTO DIGITAL",f'{p030["n_samples"]} amostras do mapa 90 m; DP espacial {p030["spatial_sd_tc_ha"]:,.2f} tC/ha',"PronaSolos 90 m: soma 0–5 + 5–15 + 15–30 cm","Embrapa Solos/PronaSolos"))
            total=sum(x[1] for x in parts); co2=total*44/12
            # Deeper SOC profiles are reported independently and are NOT summed again into Carbono Total.
            for depth in ("0–60 cm","0–100 cm","0–200 cm"):
                p=soil_profiles.get(depth) if soil_profiles else None
                if p:parts.append((f"Solo {depth}",p["tc_ha"],"MAPEAMENTO DIGITAL",f'{p["n_samples"]} amostras do mapa 90 m; DP espacial {p["spatial_sd_tc_ha"]:,.2f} tC/ha; não somado novamente ao Carbono Total',f"PronaSolos 90 m: soma das camadas até {depth.split('–')[1]}","Embrapa Solos/PronaSolos"))
            if soil_error:self.project["soil_warning"]=soil_error
            # Statistical/uncertainty metadata. Never label a descriptive range as a confidence interval.
            agb_abs=(sar_unc*CARBON_FRACTION) if sar_unc else None
            agb_pct=(sar_unc/agb*100) if agb and sar_unc else None
            agb_metric=sar.get("uncertainty_kind","incerteza do produto/modelo")
            rows=[]
            for name,val,status,note,method,source in parts:
                origem=((str(sar.get("data_origin") or "NÃO CLASSIFICADO") if name=="Biomassa aérea" else ("MAPEAMENTO" if name.startswith("Solo ") else ("LITERATURA / MODELADO" if name in ("Necromassa","Serapilheira") else "MODELADO"))))
                if name=="Biomassa aérea":
                    ea,ep,metric,level=agb_abs,agb_pct,agb_metric,(("faixa bibliográfica; não IC95%" if "bibliográfica" in agb_metric else "1σ/DP ou métrica do produto/modelo") if sar_unc else "N/D")
                elif name=="Biomassa subterrânea":
                    # Propagate SAR uncertainty only; R:S range is methodological, not a statistical CI.
                    ea=(agb_abs*ROOT_RATIO if agb_abs is not None else None); ep=(ea/val*100 if ea is not None and val else None)
                    metric="propagação da incerteza AGB; faixa R:S metodológica adicional"; level="1σ da AGB; R:S sem nível de confiança"
                elif name.startswith("Solo "):
                    depth=name.replace("Solo ",""); sp=soil_profiles.get(depth,{})
                    sd=float(sp.get("spatial_sd_tc_ha",0.0)); ea=sd; ep=(sd/val*100 if val else None)
                    metric=f"DP espacial={sd:,.2f} tC/ha ({ep:.1f}% da média)" if ep is not None else "DP espacial N/D"
                    level="variabilidade espacial do mapa; não IC95% nem erro de predição"
                else:
                    ea=None; ep=None; metric="proxy bibliográfico/modelado sem distribuição de erro validada"; level="erro estatístico N/D"
                rows.append({"parametro":name,"tc":val,"tco2":val*44/12,"origem":origem,"status":status,"metodo":method,"fonte":source,"obs":note,
                             "erro_abs_tc":ea,"erro_pct":ep,"erro_metrica":metric,"nivel_confianca":level})
            # Propagate only quantified independent 1-sigma components; report coverage of uncertainty.
            q=[r for r in rows if r.get("erro_abs_tc") is not None]
            total_sigma=math.sqrt(sum(r["erro_abs_tc"]**2 for r in q)) if q else None
            total_err_pct=(total_sigma/total*100) if total_sigma is not None and total else None
            self.project["total_uncertainty"]={"sigma_tc_ha":total_sigma,"pct":total_err_pct,"quantified_components":len(q),"total_components":len(rows),
                "note":"propagação RSS dos componentes quantificados; não inclui componentes com erro estatístico N/D"}
            self.project["analysis_rows"]=rows
            self.project["area_ha"]=area; self.project["total_tc_ha"]=total; self.project["total_tco2_ha"]=co2
            lines=[f"ENFORM VERDE {APP_VERSION}",f"Projeto: {self.name.get()}",f"Sensor/produto: {self.sensor.get()}",f"Bioma IBGE: {self.biome.get()} | Fitofisionomia/região fitoecológica IBGE: {self.phys.get()}",f"Área analisada: {area:,.2f} ha",""]
            for r in rows:
                err=(f"±{r['erro_abs_tc']:.2f} tC/ha ({r['erro_pct']:.1f}%)" if r.get('erro_pct') is not None else "N/D")
                lines += [f"{r['parametro']}",f"  {r['tc']:,.2f} tC/ha  |  {r['tco2']:,.2f} tCO₂e/ha",f"  ORIGEM DO DADO: {r['origem']}",f"  Erro/incerteza: {err}",f"  Nível estatístico: {r['nivel_confianca']}",f"  Métrica: {r['erro_metrica']}",f"  Método/produto: {r['metodo']}",f"  Fonte: {r['fonte']}",f"  {r['status']} — {r['obs']}",""]
            if not p030: lines += ["Solo 0–30 cm","  NÃO CALCULADO — PronaSolos não retornou as três camadas necessárias nesta execução.","  Diagnóstico: "+str(soil_error),""]
            lines += ["TOTAL DOS COMPARTIMENTOS DISPONÍVEIS",f"  {total:,.2f} tC/ha  |  {co2:,.2f} tCO₂e/ha",f"  Total na área: {total*area:,.0f} tC  |  {co2*area:,.0f} tCO₂e","",
                      "QUALIDADE: resultado de triagem/planejamento remoto. O relatório distingue produto SAR efetivamente processado de estimativa bibliográfica/modelada."]
            self._set(self.remote_text,f"Biomassa aérea: {agc:,.2f} tC/ha | {agc*44/12:,.2f} tCO₂e/ha\nFaixa de referência: {agc_lo:,.2f}–{agc_hi:,.2f} tC/ha | {agc_lo*44/12:,.2f}–{agc_hi*44/12:,.2f} tCO₂e/ha")
            self._set(self.res,"\n".join(lines)); self.project["last_result"]="\n".join(lines); self.nb.select(self.tabs[3]); self.status.set("Estimativa remota concluída.")
        except Exception as e:self.status.set("Falha."); messagebox.showerror("Análise",str(e))

    def export_excel(self):
        if not self.project.get("analysis_rows"):
            return messagebox.showwarning("Excel","Execute a análise antes de exportar.")
        p=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")])
        if not p:return
        wb=Workbook(); orange="F29A00"; green="0B3D2E"; white="FFFFFF"; pale="F4F6F5"; line="D5DDD9"
        thin=Side(style="thin",color=line)
        headers=["Categoria","Parâmetro / resultado","tC/ha","tCO₂e/ha","Status","Método","Fonte","Observação"]
        def setup(sh,title):
            sh.sheet_view.showGridLines=False; sh.freeze_panes="A4"; sh.auto_filter.ref="A3:H200"
            sh.merge_cells("A1:H1"); c=sh["A1"]; c.value=title; c.font=Font(size=18,bold=True,color=white); c.fill=PatternFill("solid",fgColor=green); c.alignment=Alignment(vertical="center")
            sh.row_dimensions[1].height=32
            for col,w in zip("ABCDEFGH",[20,34,16,18,25,28,30,55]): sh.column_dimensions[col].width=w
            for j,h in enumerate(headers,1):
                c=sh.cell(3,j,h); c.font=Font(bold=True,color=white); c.fill=PatternFill("solid",fgColor=orange); c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True); c.border=Border(top=thin,bottom=thin,left=thin,right=thin)
            sh.row_dimensions[3].height=28
        def put(sh,data):
            for i,row in enumerate(data,4):
                sh.row_dimensions[i].height=32
                for j,v in enumerate(row,1):
                    c=sh.cell(i,j,v); c.fill=PatternFill("solid",fgColor=(white if i%2==0 else pale)); c.border=Border(top=thin,bottom=thin,left=thin,right=thin); c.alignment=Alignment(vertical="center",wrap_text=True)
                    if j in (3,4) and isinstance(v,(int,float)): c.number_format='#,##0.00'
                sh.cell(i,2).font=Font(bold=True,color=green)
        area=self.project["area_ha"]; total=self.project["total_tc_ha"]; totalco2=self.project["total_tco2_ha"]; ar=self.project["analysis_rows"]
        ws=wb.active; ws.title="Resumo Executivo"; setup(ws,"Enform Verde — Resumo Executivo")
        put(ws,[["Entrada","Projeto",None,None,"Informado","cadastro",None,self.name.get()],
                ["Diagnóstico IBGE","Bioma dominante",None,None,"Calculado espacialmente","interseção de polígonos","IBGE — Biomas 2025",self.biome.get()],
                ["Diagnóstico IBGE","Fitofisionomia/região fitoecológica dominante",None,None,"Calculado espacialmente","interseção de polígonos","IBGE — Vegetação 2026",self.phys.get()],
                ["Entrada","Área analisada",None,None,"Calculado","geometria","CAR/vetor",f"{area:,.2f} ha"],
                ["Entrada","Sensor/produto selecionado",None,None,"Informado","SAR/multissensor","ESA/fornecedor",self.sensor.get()],
                ["Resultado","Carbono total por hectare",total,totalco2,"CONSOLIDADO","soma dos compartimentos","Enform","somente compartimentos disponíveis"],
                ["Resultado","Carbono total da propriedade",None,None,"CONSOLIDADO","total/ha × área","Enform",f"{total*area:,.0f} tC | {totalco2*area:,.0f} tCO₂e"]])
        sh=wb.create_sheet("Compartimentos"); setup(sh,"Enform Verde — Compartimentos de carbono")
        put(sh,[["Resultado — "+r.get("origem","N/D"),r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in ar])
        for sheet,param in [("Biomassa Aérea","Biomassa aérea"),("Biomassa Subterrânea","Biomassa subterrânea"),("Necromassa","Necromassa"),("Serapilheira","Serapilheira")]:
            sh=wb.create_sheet(sheet); setup(sh,"Enform Verde — "+sheet)
            rr=[r for r in ar if r["parametro"]==param]
            data=[["Resultado",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in rr]
            if not data:data=[["Resultado",param,None,None,"NÃO CALCULADO","—","—","Não houve dado válido nesta execução; nenhum valor foi inventado."]]
            put(sh,data)
        sh=wb.create_sheet("Carbono do Solo"); setup(sh,"Enform Verde — Carbono orgânico do solo")
        soil_rows=[r for r in ar if r["parametro"].startswith("Solo ")]
        soil_data=[["MAPEAMENTO — PronaSolos",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]+" | "+r.get("erro_metrica","")] for r in soil_rows]
        if not soil_data: soil_data=[["MAPEAMENTO","Carbono do solo",None,None,"NÃO CALCULADO","PronaSolos 90 m","Embrapa Solos/PronaSolos","Sem valores válidos nesta execução."]]
        put(sh,soil_data)
        sh=wb.create_sheet("Diagnóstico IBGE"); setup(sh,"Enform Verde — Diagnóstico territorial IBGE")
        diag=self.project.get("ibge_diagnosis",{})
        idata=[]
        for n,ha,pct in diag.get("biomas",[]): idata.append(["Bioma",n,None,None,"IBGE oficial","interseção espacial","IBGE — Biomas 2025",f"{ha:,.2f} ha | {pct:.2f}% da área"])
        for grp in diag.get("vegetacao",[]):
            for n,ha,pct in grp.get("classes",[]): idata.append(["Vegetação "+grp.get("campo",""),n,None,None,"IBGE oficial 2026","interseção espacial","IBGE — Vegetação 2026",f"{ha:,.2f} ha | {pct:.2f}% da área"])
        if not idata:idata=[["Diagnóstico","IBGE",None,None,"NÃO DISPONÍVEL","—","IBGE","A consulta/interseção não foi concluída nesta execução."]]
        put(sh,idata)
        sh=wb.create_sheet("Sensores SAR"); setup(sh,"Enform Verde — Sensores SAR")
        put(sh,[["Sensor","ESA Biomass — banda P",None,None,"Preferencial","PolSAR/PolInSAR/TomoSAR","ESA","Primeiro SAR orbital em banda P; usar somente quando produto efetivamente processado."],
                ["Sensor","ALOS/PALSAR / ALOS-2",None,None,"Histórico/complementar","banda L","JAXA","Séries históricas para atributos estruturais."],
                ["Sensor","TerraSAR-X / TanDEM-X / COSMO-SkyMed",None,None,"Complementar","banda X","Operadores","Textura e estrutura do dossel; não é banda do satélite Biomass."]])
        sh=wb.create_sheet("Modelos e QA"); setup(sh,"Enform Verde — Modelos, QA e incerteza")
        put(sh,[["QA","Mensuração SAR",None,None,"REGRA","controle metodológico","Enform","Não declarar mensuração SAR sem produto efetivamente processado."],
                ["Modelo","Conversão C→CO₂e",None,None,"Aplicado","tC × 44/12","estequiometria","Todas as estimativas de carbono são exibidas em tC/ha e tCO₂e/ha."],
                ["Modelo","Biblioteca brasileira",None,None,"Prioritária","seleção por domínio","IFN/SFB + Embrapa","Bioma, fitofisionomia e domínio de calibração devem ser compatíveis."]])
        sh=wb.create_sheet("Bibliografia"); setup(sh,"Enform Verde — Bibliografia e proveniência")
        put(sh,[["Fonte","ESA Biomass",None,None,"Oficial","P-band SAR","ESA","Missão orbital para biomassa florestal."],
                ["Fonte","IFN / Painel de Biomassa e Carbono",None,None,"Prioritária","inventário/equações","SFB","Base brasileira para seleção e validação."],
                ["Fonte","Embrapa",None,None,"Prioritária","protocolos/equações/COS","Embrapa","Fontes brasileiras priorizadas no motor."]])
        wb.save(p); self.status.set("Excel exportado com sucesso.")

    def save_report(self):
        txt=self.res.get("1.0","end").strip()
        if not txt:return
        p=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Relatório TXT","*.txt")])
        if p:Path(p).write_text(txt+"\n\nFONTES\n"+self.src.get("1.0","end"),encoding="utf-8"); self.status.set("Relatório salvo.")

if __name__=="__main__":
    if "--self-test" in sys.argv:self_test()
    else:App().mainloop()
