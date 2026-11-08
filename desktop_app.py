import sys, json, math, tempfile, re, zipfile, threading, queue, traceback, base64, io, os, requests, uuid
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from PIL import Image, ImageTk
from sar_pipeline import discover_sar, process_real_sar, automatic_pipeline, MODEL_REGISTRY, model_registry_rows, scientific_calibration_report, cdse_access_token
from lband_preprocess import preprocess_lband
from inventory_structure import summarize_inventory_csv
from official_inventory_harvest import harvest_redape, harvest_sinaflor, PNLA_PORTAL, INSTITUTIONAL_PORTALS, SOURCE_HIERARCHY
from gravimetric_stock import litter_stock_from_quadrats, litter_depth_mass_calibration, necromass_line_intersect_stock, carbon_stock_from_mass
from carbon_compartments import tapajos_litter_stock_component, santo_ambrosio_litter_stock_component, pantanal_nhecolandia_litter_carbon_component, tapajos_necromass_components, ifn_necromass_component, infer_uf_from_aoi, rows_for_compartment, component_has_confidence_interval
from mapbiomas_zonal import mapbiomas_class_percentages
from land_use_sar import run_land_use, report_lines as land_use_report_lines
from native_carbon import summarize_native_carbon, estimate_native_components

APP_VERSION="3.26.5-PRECAMPO-EXPERIMENTAL"
ORANGE="#EF9B06"; FOREST="#0B3D2E"; GREEN="#155D43"; PALE="#F4F6F5"; TEXT="#34413E"

# Fontes implementadas no motor. Valores-proxy são sempre rotulados como MODELADOS.
SOURCES={
 "protocol":"Higa et al. (2014), Embrapa Florestas, Documentos 266",
 "soil":"PronaSolos/Embrapa Solos, estoque de carbono orgânico 90 m, perfis 0–30/60/100 cm + diagnóstico de incerteza",
 "deadwood":"SFB/IFN — médias de inventário por estrato; raízes finas mortas no Tapajós: NASA LBA-ECO / ORNL DAAC 1116",
 "litter":"Nunes (2015) + Nascimento et al. (2024) — Pantanal/Nhecolândia com IC95% amostral; também Tapajós e Santo Ambrósio geocercados",
}
ROOT_RATIO=0.26; ROOT_LOW=0.18; ROOT_HIGH=0.30
CARBON_FRACTION=0.47

def format_ptbr(value,decimals=2):
    """Format a numeric result for Brazilian readers with half-up rounding."""
    if value is None:return "N/D"
    places=int(decimals)
    rounded=Decimal(str(value)).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP)
    raw=f"{rounded:,.{places}f}"
    return raw.replace(",","\x00").replace(".",",").replace("\x00",".")

def format_result_json(value):
    """Render diagnostic numeric values using pt-BR separators without changing stored data."""
    if isinstance(value,bool) or value is None:return value
    if isinstance(value,(int,float,Decimal)):
        return format_ptbr(value,0 if isinstance(value,int) else 6)
    if isinstance(value,dict):return {str(k):format_result_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [format_result_json(v) for v in value]
    return value

def app_resource(name):
    base=Path(getattr(sys,"_MEIPASS",Path(sys.executable).parent)) if getattr(sys,"frozen",False) else Path(__file__).parent
    p=base/name
    if p.exists():return p
    # onedir builds may keep data beside the executable rather than inside _internal
    q=Path(sys.executable).parent/name if getattr(sys,"frozen",False) else p
    return q

OFFLINE_BRAZIL_BOUNDS=(-75.0,-35.0,-33.0,6.0)  # west,south,east,north
_OFFLINE_IBGE_CACHE=None
_OFFLINE_IBGE_TILE_CACHE=OrderedDict()
def _offline_ibge_layers(bx=None):
    global _OFFLINE_IBGE_CACHE,_OFFLINE_IBGE_TILE_CACHE
    if _OFFLINE_IBGE_CACHE is None:
        index=app_resource("offline_ibge_tiles/index.json")
        if index.exists():
            try:_OFFLINE_IBGE_CACHE={"_tile_root":index.parent,"_manifest":json.loads(index.read_text(encoding="utf-8"))}
            except Exception:_OFFLINE_IBGE_CACHE={}
        else:
            p=app_resource("offline_ibge_map.json.gz")
            if not p.exists():_OFFLINE_IBGE_CACHE={}
            else:
                try:
                    import gzip
                    with gzip.open(p,"rt",encoding="utf-8") as fh:_OFFLINE_IBGE_CACHE=json.load(fh)
                except Exception:_OFFLINE_IBGE_CACHE={}
    if "_manifest" in _OFFLINE_IBGE_CACHE:
        if bx is None:return {"__manifest__":_OFFLINE_IBGE_CACHE["_manifest"]}
        from offline_map_tiles import load_quadrants_for_bbox
        return load_quadrants_for_bbox(_OFFLINE_IBGE_CACHE["_tile_root"],bx,_OFFLINE_IBGE_CACHE["_manifest"],_OFFLINE_IBGE_TILE_CACHE,max_cached_tiles=8)
    return _OFFLINE_IBGE_CACHE

def _feature_intersects_bbox(feat,bx):
    b=feat.get("bbox")
    if not b:return True
    return not (b[2]<bx[0] or b[0]>bx[2] or b[3]<bx[1] or b[1]>bx[3])

def _geom_lines(geom):
    typ=(geom or {}).get("type"); c=(geom or {}).get("coordinates") or []
    if typ=="LineString":yield c
    elif typ=="MultiLineString":
        for ln in c:yield ln
    elif typ=="Polygon":
        if c:yield c[0]
    elif typ=="MultiPolygon":
        for poly in c:
            if poly:yield poly[0]
    elif typ=="Point":
        yield [c]

def _draw_offline_ibge(d,bx,ow,oh):
    layers=_offline_ibge_layers(bx)
    span=max(bx[2]-bx[0],bx[3]-bx[1])
    def px(lon,lat):
        return ((float(lon)-bx[0])/max(bx[2]-bx[0],1e-12)*ow,
                (bx[3]-float(lat))/max(bx[3]-bx[1],1e-12)*oh)
    def draw_lines(layer,fill,width=1):
        for feat in layers.get(layer,[]):
            if not _feature_intersects_bbox(feat,bx):continue
            for line in _geom_lines(feat.get("geometry")):
                pts=[px(c[0],c[1]) for c in line if len(c)>=2]
                if len(pts)>=2:d.line(pts,fill=fill,width=width,joint="curve")
    # Subtle municipality fills improve the thematic base while preserving boundaries.
    if span<=14.0:
        for feat in layers.get("municipios",[]):
            if not _feature_intersects_bbox(feat,bx):continue
            geom=feat.get("geometry") or {}; typ=geom.get("type"); coords=geom.get("coordinates") or []
            polys=([coords] if typ=="Polygon" else coords if typ=="MultiPolygon" else [])
            for poly in polys:
                if not poly:continue
                ring=poly[0]; pts=[px(c[0],c[1]) for c in ring if len(c)>=2]
                if len(pts)>=4:d.polygon(pts,fill=(227,236,222,255))
    # administrative context
    draw_lines("ufs",(54,75,61,235),max(2,round(ow/700)))
    for feat in layers.get("ufs",[]):
        if not _feature_intersects_bbox(feat,bx):continue
        props=feat.get("properties") or {}; c=props.get("label")
        if not c:continue
        x,y=px(c[0],c[1]); label=props.get("sigla") or props.get("name")
        if label and 6<x<ow-6 and 6<y<oh-6:
            d.text((x,y),str(label),anchor="mm",fill=(48,66,53,255),stroke_width=2,stroke_fill=(248,247,239,240))
    if span<=14.0:draw_lines("municipios",(139,151,137,190),max(1,round(ow/1600)))
    # infrastructure from official IBGE BC250
    draw_lines("rodovias",(191,91,43,225),max(1,round(ow/900)))
    draw_lines("ferrovias",(91,79,71,235),max(1,round(ow/900)))
    if span<=18.0:draw_lines("hidrovias",(35,126,176,235),max(1,round(ow/1100)))
    if span<=12.0:draw_lines("drenagem",(80,157,190,190),1)
    # point infrastructure/localities
    for layer,fill,radius,maxspan in [
        ("aeroportos",(185,75,43,245),3,18.0),
        ("portos",(191,119,38,245),3,18.0),
        ("localidades",(62,82,68,240),2,7.0)]:
        if span>maxspan:continue
        for feat in layers.get(layer,[]):
            if not _feature_intersects_bbox(feat,bx):continue
            g=feat.get("geometry") or {}
            if g.get("type")!="Point":continue
            c=g.get("coordinates") or []
            if len(c)<2:continue
            x,y=px(c[0],c[1]); d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=fill,outline=(0,0,0,180))
            name=(feat.get("properties") or {}).get("name")
            if name and span<=3.5:d.text((x+4,y-3),str(name)[:34],fill=(255,255,255,235),stroke_width=2,stroke_fill=(0,0,0,170))
    # municipal labels only when zoomed sufficiently
    if span<=3.0:
        for feat in layers.get("municipios",[]):
            if not _feature_intersects_bbox(feat,bx):continue
            props=feat.get("properties") or {}
            c=props.get("label")
            if not c:continue
            x,y=px(c[0],c[1])
            if 4<x<ow-4 and 4<y<oh-4:d.text((x,y),str(props.get("name") or "")[:30],anchor="mm",fill=(45,61,50,245),stroke_width=2,stroke_fill=(248,247,239,240))
    # compact orientation legend
    legend="IBGE 2025: UF | municípios | rodovias | ferrovias | hidrovias | hidrografia | aeroportos/portos | localidades"
    d.rectangle((6,oh-42,min(ow-6,720),oh-8),fill=(250,249,242,235),outline=(93,111,97,220))
    d.text((12,oh-25),legend,anchor="lm",fill=(42,60,48,255))

def offline_brazil_preview(gdf,extent_factor=1.36,out_size=(1000,600)):
    """Rasterize IBGE municipal/admin/infrastructure layers locally, with no network or imagery dependency."""
    g=gdf.to_crs(4326).copy(); minx,miny,maxx,maxy=map(float,g.total_bounds)
    dx=max(maxx-minx,1e-8); dy=max(maxy-miny,1e-8); f=max(0.30,min(8.0,float(extent_factor)))
    cx=(minx+maxx)/2; cy=(miny+maxy)/2
    bx=[cx-dx*f/2,cy-dy*f/2,cx+dx*f/2,cy+dy*f/2]
    W,S,E,N=OFFLINE_BRAZIL_BOUNDS
    bx=[max(W,bx[0]),max(S,bx[1]),min(E,bx[2]),min(N,bx[3])]
    if bx[0]>=bx[2] or bx[1]>=bx[3]:raise ValueError("AOI fora da cobertura do mapa IBGE offline do Brasil")
    layers=_offline_ibge_layers()
    manifest=layers.get("__manifest__")
    municipality_count=manifest.get("feature_counts",{}).get("municipios",0) if manifest else len(layers.get("municipios",[]))
    if municipality_count<5000:
        raise FileNotFoundError("Camada de municípios IBGE offline ausente ou incompleta.")
    ow,oh=map(int,out_size)
    midlat=(bx[1]+bx[3])/2; coslat=max(0.25,math.cos(math.radians(midlat)))
    target=max(ow,1)/max(oh,1); xspan=(bx[2]-bx[0])*coslat; yspan=bx[3]-bx[1]
    if xspan/yspan<target:
        new_lon_span=yspan*target/coslat
        bx[0]=max(W,cx-new_lon_span/2); bx[2]=min(E,cx+new_lon_span/2)
    else:
        new_lat_span=xspan/target
        bx[1]=max(S,cy-new_lat_span/2); bx[3]=min(N,cy+new_lat_span/2)
    crop=Image.new("RGB",(ow,oh),(238,241,232))
    from PIL import ImageDraw
    d=ImageDraw.Draw(crop,"RGBA")
    _draw_offline_ibge(d,bx,ow,oh)
    overlay=Image.new("RGBA",(ow,oh),(0,0,0,0))
    overlay_draw=ImageDraw.Draw(overlay,"RGBA")
    for geom in g.geometry:
        geoms=list(geom.geoms) if geom.geom_type=="MultiPolygon" else ([geom] if geom.geom_type=="Polygon" else [])
        for poly in geoms:
            pts=[]
            for coord in poly.exterior.coords:
                lon,lat=float(coord[0]),float(coord[1])
                x=(lon-bx[0])/max(bx[2]-bx[0],1e-12)*ow
                y=(bx[3]-lat)/max(bx[3]-bx[1],1e-12)*oh
                pts.append((x,y))
            if len(pts)>=4:
                overlay_draw.polygon(pts,fill=(255,138,0,28),outline=(255,138,0,155))
                overlay_draw.line(pts,width=max(2,round(ow/650)),fill=(255,138,0,155),joint="curve")
    crop=Image.alpha_composite(crop.convert("RGBA"),overlay).convert("RGB")
    return crop,bx

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
        with zipfile.ZipFile(path) as z:
            ks=[i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".kml")]
            if not ks: raise ValueError("KMZ sem arquivo KML interno.")
            # Only the first KML document is needed. Never extract arbitrary archive
            # paths (a crafted KMZ could otherwise overwrite files outside the temp dir).
            info=ks[0]
            if info.file_size>50*1024*1024: raise ValueError("O KML interno do KMZ excede 50 MiB.")
            target=d/"document.kml"
            with z.open(info) as src, target.open("wb") as dst:
                while True:
                    chunk=src.read(1024*1024)
                    if not chunk: break
                    dst.write(chunk)
        gdf=gpd.read_file(target,driver="KML")
    elif p.suffix.lower()==".kml":
        gdf=gpd.read_file(path,driver="KML")
    else:gdf=gpd.read_file(path)
    if gdf.empty: raise ValueError("O vetor não contém feições.")
    if gdf.crs is None: raise ValueError("O vetor não informa CRS; não é seguro assumir coordenadas.")
    gdf=gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if gdf.empty: raise ValueError("Não há geometria válida.")
    return gdf

def geom_metrics(gdf):
    g=gdf.to_cr