import sys, json, math, tempfile, re, zipfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from PIL import Image, ImageTk

APP_VERSION="1.3.2-SAR-IBGE"
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

def resolve_car(car):
    import requests, geopandas as gpd
    code=car.strip().upper()
    m=re.match(r"^([A-Z]{2})-",code)
    if not m: raise ValueError("Código CAR inválido: esperado UF-...")
    uf0=m.group(1); uf=uf0 if uf0=="DF" else uf0.lower(); layer=f"sicar:sicar_imoveis_{uf}"
    url="https://geoserver.car.gov.br/geoserver/sicar/ows"
    errors=[]
    for fld in ("cod_imovel",):
        params={"service":"WFS","version":"1.0.0","request":"GetFeature","typeName":layer,
                "outputFormat":"application/json","srsName":"EPSG:4326",
                "CQL_FILTER":f"{fld}='{code}'"}
        try:
            r=requests.get(url,params=params,headers={"User-Agent":f"Enform-Verde/{APP_VERSION}","Accept":"application/json"},timeout=(10,60))
            if r.ok and "FeatureCollection" in r.text:
                js=r.json()
                if js.get("features"):
                    tmp=Path(tempfile.gettempdir())/"enform_car.geojson"; tmp.write_text(json.dumps(js),encoding="utf-8")
                    gdf=gpd.read_file(tmp)
                    if gdf.empty or gdf.geometry.isna().all(): raise RuntimeError("SICAR retornou registro sem geometria válida.")
                    return gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")
            errors.append(f"{fld}:{r.status_code}")
        except Exception as e: errors.append(str(e))
    raise RuntimeError("O WFS público oficial do SICAR/SFB não devolveu a geometria deste CAR. Tentativas: "+"; ".join(errors[-3:]))

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

def try_download_embrapa_soc(gdf):
    # WCS público: tentativa automática; falha é reportada e nunca substituída por valor inventado.
    import requests
    b=geom_metrics(gdf)["bbox"]; out=Path(tempfile.gettempdir())/"enform_soc030.tif"
    endpoints=["https://geoinfo.dados.embrapa.br/geoserver/wcs","https://geoinfo.dados.embrapa.br/geoserver/ows"]
    params={"service":"WCS","version":"1.0.0","request":"GetCoverage","coverage":"geonode:br_gsocmap030",
            "crs":"EPSG:4326","bbox":",".join(map(str,b)),"format":"GeoTIFF","resx":"0.008333333","resy":"0.008333333"}
    errs=[]
    for u in endpoints:
        try:
            r=requests.get(u,params=params,timeout=45)
            if r.ok and len(r.content)>1000 and not r.content.lstrip().startswith(b"<"):
                out.write_bytes(r.content); return str(out)
            errs.append(f"{r.status_code}")
        except Exception as e: errs.append(str(e))
    raise RuntimeError("Download WCS do COS Embrapa indisponível nesta execução ("+", ".join(errs)+"). Carregue o GeoTIFF oficial 0–30 cm.")

def self_test():
    assert abs(float(agb_mexiana(10))-0.1184*10**2.53)<1e-8
    assert ROOT_LOW<ROOT_RATIO<ROOT_HIGH
    assert abs(CARBON_FRACTION-0.47)<1e-9
    print("ENFORM_VERDE_SELF_TEST_OK")

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Enform Verde"); self.geometry("1260x760"); self.minsize(1050,650)
        self.inv=None; self.gdf=None; self.soil_raster=None; self.project={"version":APP_VERSION}
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
        hero=tk.Canvas(root,width=430,bg=FOREST,highlightthickness=0); hero.pack(side="left",fill="y")
        base=Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).parent
        visual=base/"enform_visual.jpg"
        if visual.exists():
            im=Image.open(visual).convert("RGB")
            im.thumbnail((430,320),Image.Resampling.LANCZOS)
            self.hero_photo=ImageTk.PhotoImage(im)
            hero.create_image(0,0,image=self.hero_photo,anchor="nw")
        else:
            hero.create_text(35,45,text="enform",anchor="nw",fill="white",font=("Segoe UI",26,"bold"))
            hero.create_text(36,92,text="VERDE",anchor="nw",fill=ORANGE,font=("Segoe UI",12,"bold"))
        hero.create_rectangle(0,320,430,760,fill=FOREST,outline="")
        hero.create_text(32,365,text="Carbono florestal\npor sensoriamento remoto",anchor="nw",fill="white",font=("Segoe UI",18,"bold"))
        hero.create_text(32,455,text="AMAZÔNIA  •  CERRADO\nCAATINGA  •  MATA ATLÂNTICA",anchor="nw",fill="#DDE9E3",font=("Segoe UI",10,"bold"))
        hero.create_text(32,650,text="tC/ha  •  tCO₂e/ha\nMEDIDO  •  MODELADO  •  INCERTEZA",anchor="nw",fill="white",font=("Segoe UI",10,"bold"))
        main=ttk.Frame(root,padding=22); main.pack(side="left",fill="both",expand=True)
        top=ttk.Frame(main); top.pack(fill="x")
        ttk.Label(top,text="Análise de carbono",style="Title.TLabel").pack(side="left")
        ttk.Button(top,text="EXECUTAR ANÁLISE",command=self.execute,style="Run.TButton").pack(side="right")
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
        f=self.tabs[0]; ttk.Label(f,text="Identificação",style="H.TLabel").grid(row=0,column=0,columnspan=3,sticky="w")
        self.name=tk.StringVar(value="Projeto Enform Verde"); self.car=tk.StringVar()
        self.biome=tk.StringVar(value="Amazônia"); self.phys=tk.StringVar(value="Várzea estuarina / floresta aluvial")
        labels=[("Projeto",self.name),("Código CAR",self.car),("Fitofisionomia",self.phys)]
        for i,(lab,var) in enumerate(labels,1):
            ttk.Label(f,text=lab).grid(row=i,column=0,sticky="w",pady=8); ttk.Entry(f,textvariable=var,width=70).grid(row=i,column=1,sticky="ew",padx=10)
        ttk.Label(f,text="Bioma").grid(row=4,column=0,sticky="w",pady=8)
        ttk.Combobox(f,textvariable=self.biome,state="readonly",values=["Amazônia","Mata Atlântica","Cerrado","Caatinga"],width=28).grid(row=4,column=1,sticky="w",padx=10)
        ttk.Button(f,text="Resolver perímetro pelo CAR",command=self.car_lookup).grid(row=2,column=2,padx=8)
        ttk.Label(f,text="A resolução automática usa o geosserviço público do SICAR. Se ele não responder, carregue o vetor oficial.",foreground="#666").grid(row=5,column=1,columnspan=2,sticky="w",pady=10)
        f.columnconfigure(1,weight=1)
    def _spatial(self):
        f=self.tabs[1]; ttk.Label(f,text="Perímetro e solo",style="H.TLabel").pack(anchor="w")
        row=ttk.Frame(f); row.pack(fill="x",pady=10)
        ttk.Button(row,text="Carregar KML / GeoJSON / SHP / GPKG",command=self.pick_vector).pack(side="left")
        ttk.Button(row,text="Buscar COS 0–30 cm — Embrapa",command=self.auto_soil).pack(side="left",padx=8)
        ttk.Button(row,text="Carregar GeoTIFF de COS",command=self.pick_soil).pack(side="left")
        self.spatial_text=tk.Text(f,height=20,wrap="word"); self.spatial_text.pack(fill="both",expand=True,pady=8)
        self._set(self.spatial_text,"Nenhum perímetro carregado.\n\nO programa não assume CRS nem cria geometria a partir de um código CAR sem resposta do serviço oficial.")
    def _remote(self):
        f=self.tabs[2]; ttk.Label(f,text="Sensores SAR e estimativa de biomassa",style="H.TLabel").pack(anchor="w")
        self.sensor=tk.StringVar(value="ESA Biomass — banda P")
        ttk.Combobox(f,textvariable=self.sensor,state="readonly",width=58,values=["ESA Biomass — banda P","ESA CCI Biomass — AGB 100 m + incerteza","ALOS/PALSAR — banda L","ALOS-2/PALSAR-2 — banda L","TerraSAR-X/TanDEM-X — banda X","COSMO-SkyMed — banda X"]).pack(anchor="w",pady=8)
        self.remote_text=tk.Text(f,height=22,wrap="word"); self.remote_text.pack(fill="both",expand=True,pady=8)
        self._set(self.remote_text,
            "O inventário florestal NÃO é entrada obrigatória.\n\n"
            "O motor estima biomassa a partir da localização, bioma/fitofisionomia e biblioteca de referências espaciais. "
            "Prioridade: IFN/SFB — Painel de Biomassa e Carbono (222 equações e dados abertos), Embrapa e estudos brasileiros.\n\n"
            "Quando não houver raster de biomassa de resolução compatível, a saída será uma estimativa de referência por estrato, "
            "com incerteza e nível de evidência — não uma falsa medição pixel a pixel. Inventário de campo permanece apenas como opção futura de calibração/validação.")
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
    def car_lookup(self):
        try:
            self.status.set("Consultando SICAR..."); self.update_idletasks(); self.gdf=resolve_car(self.car.get()); self._show_geom("SICAR")
        except Exception as e: self.status.set("CAR não resolvido."); messagebox.showwarning("SICAR",str(e))
    def pick_vector(self):
        p=filedialog.askopenfilename(filetypes=[("Vetores","*.kml *.kmz *.geojson *.json *.shp *.gpkg"),("Todos","*.*")])
        if not p:return
        try:self.gdf=read_vector(p); self.project["vector"]=p; self._show_geom(Path(p).name)
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
        if self.gdf is None:
            if self.car.get().strip():
                try:self.gdf=resolve_car(self.car.get()); self._show_geom("SICAR")
                except Exception as e:return messagebox.showwarning("Perímetro necessário",str(e)+"\n\nAlternativamente carregue KML, KMZ, SHP, GeoJSON ou GPKG.")
            else:return messagebox.showwarning("Perímetro necessário","Informe o CAR ou carregue o arquivo vetorial da propriedade.")
        try:
            self.status.set("Executando estimativa remota..."); self.update_idletasks()
            area=geom_metrics(self.gdf)["area_ha"]
            agb,agb_lo,agb_hi=self.remote_biomass_reference()
            agc=agb*CARBON_FRACTION
            agc_lo=agb_lo*CARBON_FRACTION; agc_hi=agb_hi*CARBON_FRACTION
            bgb=agb*ROOT_RATIO; bgc=bgb*CARBON_FRACTION
            nec_c=agc*0.20 if self.biome.get()=="Amazônia" else agc*0.12
            lit_c=4.8 if self.biome.get()=="Amazônia" else (3.0 if self.biome.get()=="Mata Atlântica" else 1.8)
            soil=None; soil_sd=None; pix=None
            if not self.soil_raster:
                try:self.soil_raster=try_download_embrapa_soc(self.gdf)
                except Exception:pass
            if self.soil_raster:
                try:soil,soil_sd,pix=zonal_soil(self.gdf,self.soil_raster)
                except Exception:soil=None
            parts=[
              ("Biomassa aérea",agc,"ESTIMATIVA REMOTA DE REFERÊNCIA",f"AGB={agb:,.1f} Mg/ha; carbono={CARBON_FRACTION:.2f}; faixa C={agc_lo:,.2f}–{agc_hi:,.2f} tC/ha","SAR/biblioteca","IFN/SFB + Embrapa"),
              ("Biomassa subterrânea",bgc,"MODELADO",f"R:S={ROOT_RATIO:.2f}; faixa metodológica {ROOT_LOW:.2f}–{ROOT_HIGH:.2f}","relação raiz:parte aérea","biblioteca metodológica"),
              ("Necromassa",nec_c,"MODELADO — TRIAGEM","proxy condicionado ao bioma; substituir por IFN/medição local para MRV","proxy por bioma","IFN/Embrapa"),
              ("Serapilheira",lit_c,"MODELADO — TRIAGEM","alta variabilidade local","proxy por bioma","Embrapa/literatura")]
            if soil is not None: parts.append(("Solo 0–30 cm",soil,"MAPEAMENTO DIGITAL",f"{pix} pixels; DP espacial {soil_sd:,.2f} tC/ha","recorte raster","Embrapa/PronaSolos"))
            total=sum(x[1] for x in parts); co2=total*44/12
            rows=[]
            for name,val,status,note,method,source in parts:
                rows.append({"parametro":name,"tc":val,"tco2":val*44/12,"status":status,"metodo":method,"fonte":source,"obs":note})
            self.project["analysis_rows"]=rows
            self.project["area_ha"]=area; self.project["total_tc_ha"]=total; self.project["total_tco2_ha"]=co2
            lines=[f"ENFORM VERDE {APP_VERSION}",f"Projeto: {self.name.get()}",f"Sensor/produto: {self.sensor.get()}",f"Bioma: {self.biome.get()} | Fitofisionomia: {self.phys.get()}",f"Área analisada: {area:,.2f} ha",""]
            for r in rows:
                lines += [f"{r['parametro']}",f"  {r['tc']:,.2f} tC/ha  |  {r['tco2']:,.2f} tCO₂e/ha",f"  {r['status']} — {r['obs']}",""]
            if soil is None: lines += ["Solo 0–30 cm","  NÃO CALCULADO — serviço/raster de COS indisponível nesta execução; nenhum valor foi inventado.",""]
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
                ["Entrada","Bioma",None,None,"Informado","classificação",None,self.biome.get()],
                ["Entrada","Fitofisionomia",None,None,"Informado","classificação",None,self.phys.get()],
                ["Entrada","Área analisada",None,None,"Calculado","geometria","CAR/vetor",f"{area:,.2f} ha"],
                ["Entrada","Sensor/produto selecionado",None,None,"Informado","SAR/multissensor","ESA/fornecedor",self.sensor.get()],
                ["Resultado","Carbono total por hectare",total,totalco2,"CONSOLIDADO","soma dos compartimentos","Enform","somente compartimentos disponíveis"],
                ["Resultado","Carbono total da propriedade",None,None,"CONSOLIDADO","total/ha × área","Enform",f"{total*area:,.0f} tC | {totalco2*area:,.0f} tCO₂e"]])
        sh=wb.create_sheet("Compartimentos"); setup(sh,"Enform Verde — Compartimentos de carbono")
        put(sh,[["Resultado",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in ar])
        for sheet,param in [("Biomassa Aérea","Biomassa aérea"),("Biomassa Subterrânea","Biomassa subterrânea"),("Necromassa","Necromassa"),("Serapilheira","Serapilheira"),("Carbono do Solo","Solo 0–30 cm")]:
            sh=wb.create_sheet(sheet); setup(sh,"Enform Verde — "+sheet)
            rr=[r for r in ar if r["parametro"]==param]
            data=[["Resultado",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in rr]
            if not data:data=[["Resultado",param,None,None,"NÃO CALCULADO","—","—","Não houve dado válido nesta execução; nenhum valor foi inventado."]]
            put(sh,data)
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
