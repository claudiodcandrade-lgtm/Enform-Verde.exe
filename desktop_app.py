Warning: truncated output (original token count: 70889)
Total output lines: 4082

import sys, json, math, tempfile, re, zipfile, threading, queue, traceback, base64, io, os, requests, uuid
import tls_setup  # V87.39: one TLS trust store for requests AND GDAL (Windows store + certifi + OS)
tls_setup.configure()
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox, simpledialog
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

APP_VERSION="3.26.26-PRECAMPO-EXPERIMENTAL"
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

def _xy_coords(coords):
    """Return 2D map coordinates from KML rings, ignoring optional altitude."""
    return [(float(coord[0]),float(coord[1])) for coord in coords]

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
    g=gdf.to_crs(4326); union=g.geometry.union_all()
    c=union.centroid; lon,lat=float(c.x),float(c.y)
    zone=max(1,min(60,int((lon+180)//6)+1)); epsg=(32700 if lat<0 else 32600)+zone
    gm=gdf.to_crs(epsg)
    area_utm=float(gm.geometry.union_all().area/10000)
    area_equal=float(gdf.to_crs("EPSG:6933").geometry.union_all().area/10000)
    b=union.bounds
    return {"area_ha":area_equal,"area_utm_ha":area_utm,
            "area_crs":"EPSG:6933","centroid":[lon,lat],
            "bbox":[float(x) for x in b],"utm_epsg":epsg}

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
            exact=[x for x in feats if str((x.get("properties") or {}).get("cod_imovel","")).strip().upper()==code]
            if not exact:
                # A WFS response may ignore the CQL filter. Never accept an
                # unrelated property as the requested CAR polygon.
                attempts.append(f"{version}:no_exact_cod_imovel")
                continue
            if len(exact)>1:raise RuntimeError("SICAR retornou registros múltiplos para o mesmo código.")
            props=exact[0].get("properties") or {}
            if not exact[0].get("geometry"):raise RuntimeError("CAR localizado, porém sem geometria pública.")
            # In-memory construction avoids a shared temporary GeoJSON path:
            # concurrent queries must never overwrite each other's geometry.
            gdf=gpd.GeoDataFrame.from_features(exact,crs="EPSG:4326")
            gdf.attrs.update({"sicar_cod_imovel":props.get("cod_imovel",code),"sicar_status":props.get("status_imovel") or props.get("condicao"),
              "sicar_area_declarada_ha":props.get("area"),"sicar_municipio":props.get("municipio"),"sicar_lookup":url+" WFS "+version})
            return gdf
        except RuntimeError:raise
        except Exception as e:attempts.append(version+":"+type(e).__name__)
    raise LookupError("CAR válido no formato, mas não localizado no WFS público oficial nesta consulta. Tentativas: "+", ".join(attempts)+". O programa não concluirá que o CAR é inválido por indisponibilidade do serviço.")

def resolve_ccir_sigef(code):
    """Resolve código INCRA/SNCR do CCIR em parcela georreferenciada certificada no SIGEF."""
    import requests, geopandas as gpd
    digits=re.sub(r"\D","",code or "")
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

def _download_zip(url,folder,tag):
    """Official IBGE ZIP cache with atomic integrity check and transient retries."""
    from tools.ibge_official_zip import download_ibge_zip
    return download_ibge_zip(url, folder, tag, APP_VERSION)

def _read_zip_bbox(zpath,bbox4326,preferred=("area",)):
    """Read only polygons intersecting the property bbox directly from ZIP (GDAL /vsizip)."""
    import pyogrio
    from pyproj import Transformer
    vsi="zip://"+Path(zpath).as_posix()
    layers=pyogrio.list_layers(vsi)
    candidates=[]
    for row in layers:
        name=str(row[0]); geom=str(row[1] or "")
        if "polygon" in geom.lower():
            score=sum(10 for x in preferred if x.lower() in name.lower())+(5 if "brasil" in name.lower() else 0)
            candidates.append((score,name))
    if not candidates:raise RuntimeError("Pacote IBGE sem camada poligonal reconhecida.")
    layer=max(candidates)[1]
    info=pyogrio.read_info(vsi,layer=layer)
    crs=info.get("crs")
    bb=tuple(float(x) for x in bbox4326)
    if crs and str(crs).upper() not in ("EPSG:4326","EPSG:4674"):
        tr=Transformer.from_crs("EPSG:4326",crs,always_xy=True)
        x1,y1=tr.transform(bb[0],bb[1]); x2,y2=tr.transform(bb[2],bb[3]); bb=(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2))
    g=pyogrio.read_dataframe(vsi,layer=layer,bbox=bb,use_arrow=False)
    if g.empty:raise RuntimeError("A camada IBGE não retornou polígonos no envelope da propriedade.")
    return g

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
    p=project.to_crs("EPSG:6933"); t=theme.to_crs("EPSG:6933")  # equal-area for Brazil
    try:
        import shapely
        p["geometry"]=p.geometry.map(lambda g:shapely.make_valid(g) if g is not None and not g.is_valid else g)
        t["geometry"]=t.geometry.map(lambda g:shapely.make_valid(g) if g is not None and not g.is_valid else g)
    except Exception: pass
    inter=gpd.overlay(t,p[["geometry"]],how="intersection",keep_geom_type=False)
    # Reject overlapping IBGE polygons rather than double count native hectares.
    # The test is performed after clipping every feature to the AOI.
    inter=inter[inter.geometry.notna() & ~inter.geometry.is_empty].copy()
    if inter.empty:return []
    union_area=float(inter.geometry.union_all().area)
    summed_area=float(inter.geometry.area.sum())
    if summed_area-union_area > max(1.0,union_area*1e-8):
        raise ValueError("Sobreposição entre polígonos IBGE: área ambígua; classificação bloqueada.")
    inter["_ha"]=inter.geometry.area/10000
    total=float(inter["_ha"].sum())
    if total<=0:return []
    out=[]
    aoi_area=float(p.geometry.union_all().area/10000)
    covered=min(total,aoi_area)
    missing=max(0.0,aoi_area-covered)
    for field in fields:
        if field and field in inter.columns:
            g=inter.groupby(field,dropna=False)["_ha"].sum().sort_values(ascending=False)
            classes=[(str(k) if pd.notna(k) else "Não classificado",float(v),float(v/aoi_area*100)) for k,v in g.items() if v>0]
            if missing>max(0.01,aoi_area*1e-8):classes.append(("Sem cobertura IBGE",missing,float(missing/aoi_area*100)))
            out.append((field,classes))
    return out

def _shares_with_code(project,theme,name_field,code_field):
    """Area-weighted IBGE region names retaining their official phytoregion code."""
    import geopandas as gpd
    p=project.to_crs("EPSG:6933"); t=theme.to_crs("EPSG:6933")  # equal-area for Brazil
    try:
        import shapely
        p["geometry"]=p.geometry.map(lambda g:shapely.make_valid(g) if g is not None and not g.is_valid else g)
        t["geometry"]=t.geometry.map(lambda g:shapely.make_valid(g) if g is not None and not g.is_valid else g)
    except Exception: pass
    columns=["geometry",name_field]+([code_field] if code_field else [])
    inter=gpd.overlay(t[columns],p[["geometry"]],how="intersection",keep_geom_type=False)
    # Reject overlapping IBGE polygons rather than double count native hectares.
    # The test is performed after clipping every feature to the AOI.
    inter=inter[inter.geometry.notna() & ~inter.geometry.is_empty].copy()
    if inter.empty:return []
    union_area=float(inter.geometry.union_all().area)
    summed_area=float(inter.geometry.area.sum())
    if summed_area-union_area > max(1.0,union_area*1e-8):
        raise ValueError("Sobreposição entre polígonos IBGE: área ambígua; classificação bloqueada.")
    inter["_ha"]=inter.geometry.area/10000; total=float(inter["_ha"].sum())
    if total<=0:return []
    keys=[name_field]+([code_field] if code_field else [])
    out=inter.groupby(keys,dropna=False)["_ha"].sum().sort_values(ascending=False)
    aoi_area=float(p.geometry.union_all().area/10000.0)
    if aoi_area<=0:raise ValueError("AOI sem área mensurável para região fitoecológica.")
    records=[{"name":str(key[0] if isinstance(key,tuple) else key),
             "code":(str(key[1]) if code_field and isinstance(key,tuple) and key[1] is not None else None),
             "area_ha":float(area),"percent":float(area/aoi_area*100)}
             for key,area in out.items() if area>0]
    # Percentages describe the whole AOI, including any unmapped remainder.
    missing=max(0.0,aoi_area-union_area/10000.0)
    if missing>max(0.01,aoi_area*1e-8):
        records.append({"name":"Sem cobertura IBGE","code":None,"area_ha":missing,
                        "percent":missing/aoi_area*100})
    return records

def primary_ibge_physiognomy(diagnosis):
    """Return the dominant current IBGE phytogeographic region (legend_1).

    legend_2 describes the predominant vegetation cover class and is useful as
    a secondary descriptor, but it is not a substitute for the phytogeographic
    region requested for model-domain selection.
    """
    for group in (diagnosis or {}).get("vegetacao",[]):
        if str(group.get("campo","")).casefold()=="legenda_1":
            classes=group.get("classes") or []
            if classes:return str(classes[0][0])
    return ""

def ibge_area_summary_lines(diagnosis):
    """Readable IBGE coverage summary with correct area/percentage ordering."""
    groups={str(x.get("campo","")).casefold():x.get("classes") or []
            for x in (diagnosis or {}).get("vegetacao",[])}
    lines=[]
    labels=(("legenda_1","Região fitoecológica POTENCIAL IBGE (não comprova cobertura atual)"),
            ("legenda_2","Cobertura vegetal cartográfica IBGE (legenda_2; referência, não comprova cobertura atual)"))
    for field,label in labels:
        rows=groups.get(field) or []
        if not rows:
            continue
        lines.append(label+":")
        for row in rows:
            if len(row)<3:
                continue
            name,area_ha,percent=row[:3]
            try:
                lines.append(f"  {name} — {format_ptbr(float(area_ha),2)} ha "
                             f"({format_ptbr(float(percent),2)}% da AOI)")
            except (TypeError,ValueError):
                continue
    if not any(line.startswith("Região fitoecológica POTENCIAL") for line in lines):
        error=(diagnosis or {}).get("vegetacao_error")
        lines.append("Região fitoecológica POTENCIAL IBGE (legenda_1, não cobertura atual): "
                     +("não disponível — "+str(error) if error else "sem classe intersectada"))
    return lines

def load_ibge_land_use_reference(project):
    """Use the official cached/bbox IBGE polygons for the fallback partition."""
    root=_ibge_cache()/"vegetacao_2026"
    archive=_download_zip(IBGE_VEGE_2026_URL,root,"vege_area_2026")
    layer=_read_zip_bbox(archive,tuple(project.to_crs("EPSG:4326").total_bounds),("vege_area","area","brasil"))
    field=_field(layer.columns,["legenda_1"])
    if not field:raise ValueError("Camada oficial IBGE sem legenda_1.")
    return layer,field

def native_carbon_analysis(aoi,land,biome,sar_options=None,sar_paths=None):
    import geopandas as gpd
    classes=gpd.read_file(land["vector_path"])
    options=dict(sar_options or {})
    # Optional externally licensed, class-specific inventory observations.
    # Never forward a data manifest as a SAR model parameter.
    inventory_evidence=options.pop("inventory_evidence",None)
    inventory_manifest=options.pop("inventory_evidence_manifest",None)
    biodiversity_inventory_records=options.pop("biodiversity_inventory_records",None)
    catalog_cache={}
    def sar_estimator(frame,b,p):
        if sar_paths:return process_real_sar(frame,sar_paths,b,p)
        # Search official BIOMASS collections once against the full AOI, then
        # reuse the discovered products while reading each native stratum's
        # own pixel window. This avoids repeated catalog round trips per class.
        if "biomass_catalog" not in catalog_cache:
            try:
                from sar_pipeline import biomass_l2b_search
                found=biomass_l2b_search(aoi,limit=100,return_audit=True)
                if isinstance(found,tuple) and len(found)==2:
                    catalog_cache["biomass_catalog"]=(found[0],found[1])
                else:
                    catalog_cache["biomass_catalog"]=(found,{
                        "queries":[],"errors":["AUDIT_METADATA_UNAVAILABLE"],
                        "height_queries_complete":False})
            except Exception as exc:
                catalog_cache["biomass_catalog"]=([],{
                    "queries":[],"errors":[type(exc).__name__],
                    "height_queries_complete":False,
                    "technical_error":type(exc).__name__+": "+str(exc)[:180]})
        items,audit=catalog_cache["biomass_catalog"]
        return automatic_pipeline(frame,b,p,biomass_catalog_items=items,
                                  biomass_search_audit=audit,**options)
    def estimator(frame,phys):
        return estimate_native_components(frame,phys,biome,sar_estimator,pronasolos_soc_profiles,
                                          property_aoi=aoi,inventory_evidence=inventory_evidence)
    result=summarize_native_carbon(aoi,classes,estimator,(land.get("validation") or {}).get("class_metadata"))
    native_strata=[st for st in result.get("strata",[]) if float(st.get("area_ha") or 0)>0]
    height_certs=[(st.get("sar_details") or {}).get("height_absence_certificate") for st in native_strata]
    height_certs=[c for c in height_certs if isinstance(c,dict)]
    if height_certs and all(c==height_certs[0] for c in height_certs):
        result["height_absence_certificate"]=height_certs[0]
    if not biodiversity_inventory_records:
        result["biodiversity_references"]=[{"status":"N/D","reason":"INVENTARIO_FITOSSOCIOLOGICO_NAO_CARREGADO"}]
    elif not native_strata:
        result["biodiversity_references"]=[{"status":"N/D","reason":"NENHUM_ESTRATO_NATIVO_ATUAL_CONFIRMADO_POR_SAR"}]
    else:
        try:
            from crop_yield_scenario import microregion_of
            micro=microregion_of(aoi)["dominant"]
            from biodiversity_inventory import summarize_top10_species
            result["biodiversity_references"]=[summarize_top10_species(
                biodiversity_inventory_records,biome=biome,
                physiognomy=st.get("physiognomy") or st.get("class_name"),
                microregion=micro.get("name") or micro.get("code")) for st in native_strata]
        except Exception as exc:
            result["biodiversity_references"]=[{"status":"N/D","reason":"CONSULTA_MICRORREGIONAL_FALHOU_"+
                type(exc).__name__+": "+str(exc)[:180]}]
    # Separate conditional inventory scenario. The wrapper first tries the
    # open IFN plot data for the matching physiognomy/region, then the existing
    # published regional hierarchy. Exhausted-route technical failures stay
    # visible; they are not relabelled as no-scene/no-pixel evidence.
    # A SAR-native stratum with N/D components is still not a carbon result.
    # Run the explicitly conditional inventory route whenever no carbon stock
    # was quantified; checking only for an empty stratum list skipped the
    # fallback whenever the classifier had drawn a polygon but estimation
    # failed downstream.
    if result.get('known_total_tc') is None:
        from ifn_carbon_fallback import estimate_inventory_carbon_scenario
        scenarios=[]
        for potential in land.get('potential_physiognomy_intersections') or []:
            physiognomy=str(potential.get('name') or '')
            if not physiognomy or physiognomy == 'Sem cobertura IBGE':
                continue
            try:
                sar_result=sar_estimator(aoi,biome,physiognomy)
                scenario=estimate_inventory_carbon_scenario(
                    biome=biome,physiognomy=physiognomy,
                    area_ha=float(potential.get('area_ha') or 0),
                    sar_result=sar_result,
                    aoi=aoi,
                    centroid_lon=float(aoi.to_crs('EPSG:4326').geometry.union_all().centroid.x),
                    centroid_lat=float(aoi.to_crs('EPSG:4326').geometry.union_all().centroid.y))
                scenario['sar_status']=sar_result.get('status') if isinstance(sar_result,dict) else None
                scenario['sar_reason']=sar_result.get('reason') if isinstance(sar_result,dict) else None
                if scenario.get('status')=='CENARIO_CONDICIONAL_INVENTARIO_SEM_AGB_ALTURA_SAR':
                    scenarios.append(scenario)
            except Exception as exc:
                result['inventory_scenario_diagnostic']={
                    'status':'ERRO_TECNICO_SEM_FALLBACK',
                    'reason':type(exc).__name__+': '+str(exc)[:300],
                    'physiognomy':physiognomy}
        if scenarios:
            result['conditional_inventory_scenarios']=scenarios
        elif not result.get('inventory_scenario_diagnostic'):
            result['inventory_scenario_diagnostic']={
                'status':'N/D',
                'reason':'Nenhum cenário elegível: SAR com pixels, falha técnica pendente ou inventário compatível indisponível.'}
    if inventory_manifest is not None:
        # File hash proves input identity, not scientific validity.
        result["external_inventory_manifest"]=inventory_manifest
    return result

def diagnose_ibge(project):
    """IBGE diagnosis with bbox-only reads; national 355 MB vegetation ZIP is never expanded/read wholesale."""
    root=_ibge_cache(); veg=root/"vegetacao_2026"; bio=root/"biomas_2025"
    bbox=tuple(project.to_crs("EPSG:4326").total_bounds)
    bz=_download_zip(IBGE_BIOMAS_2025_URL,bio,"biomas_2025")
    bg=_read_zip_bbox(bz,bbox,("bioma","area"))
    bfield=_field(bg.columns,["Bioma","Nome_Bioma","nm_bioma","bioma_1"])
    bs=_shares(project,bg,[bfield])
    if not bs or not bs[0][1]:raise RuntimeError("O polígono não interceptou a camada oficial de Biomas do IBGE.")
    result={"bioma_field":bfield,"biomas":bs[0][1],"vegetacao_fields":[],"vegetacao":[],
            "fonte_bioma":"IBGE — Biomas do Brasil, revisão 2025, 1:250.000",
            "fonte_vegetacao":"IBGE — Vegetação/Regiões Fitoecológicas, versão 2026, 1:250.000"}
    try:
        vz=_download_zip(IBGE_VEGE_2026_URL,veg,"vege_area_2026")
        vg=_read_zip_bbox(vz,bbox,("vege_area","area","brasil"))
        # In the official BDIA 1:250,000 schema, legenda_1 is the name of the
        # phytogeographic region; legenda_2 is the predominant cover class.
        # Do not silently substitute the latter for the former.
        l1=_field(vg.columns,["legenda_1"])
        l2=_field(vg.columns,["legenda_2"])
        vs=_shares(project,vg,[l1,l2])
        result["vegetacao_fields"]=[x[0] for x in vs]
        result["vegetacao"]=[{"campo":x[0],"classes":x[1]} for x in vs]
        fito_code=_field(vg.columns,["cd_fito"])
        result["regioes_fitoecologicas"]=_shares_with_code(project,vg,l1,fito_code) if l1 else []
        if not any(x[0]=="legenda_1" and x[1] for x in vs):
            result["vegetacao_error"]="A camada foi lida, mas não retornou Região Fitoecológica IBGE em legenda_1 para a AOI. A análise não deve tratar a cobertura de legenda_2 como substituta."
    except Exception as e:
        result["vegetacao_error"]=str(e)
    return result

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

def _attach_embrapa_official_soc_bounds(gdf, stock_result, stock_paths):
    """Attach official marginal prediction bounds without erasing valid SOC."""
    top = stock_result.get("0–100 cm") or {}
    if top.get("tc_ha") is None:
        return stock_result
    try:
        from soil_soc_official_uncertainty import fetch_official_bounds
        from soil_pronasolos_zonal import mapped_soil_0_100_on_polygon
        bounds = fetch_official_bounds(gdf.to_crs(4326).geometry.union_all())
        measured = mapped_soil_0_100_on_polygon(
            gdf, stock_paths, official_bound_paths=bounds["paths"],
            official_provenance=bounds["provenance"])
        verified = measured.get("0–100 cm") or {}
        if verified.get("tc_ha") is None or abs(verified["tc_ha"]-top["tc_ha"])>1e-5:
            raise ValueError("Estoque divergiu ao validar os limites oficiais")
        status = verified.get("official_uncertainty") or {}
        if status.get("status") != "ENVELOPE_MARGINAL_OFICIAL":
            raise ValueError(status.get("reason") or "Limites oficiais incompletos")
    except Exception as exc:
        status = {"status":"N/D",
                  "reason":type(exc).__name__+": "+str(exc).split("https://")[0][:180],
                  "predictive_uncertainty_quantified":False}
    top["official_uncertainty"] = status
    top["predictive_uncertainty_quantified"] = bool(
        status.get("predictive_uncertainty_quantified"))
    stock_result.setdefault("_diagnostic",{})["official_uncertainty"] = status
    return stock_result


def pronasolos_soc_profiles(gdf,max_points=36):
    """PronaSolos/Embrapa Solos 90 m SOC stocks (Mg C/ha).
    Exact polygon × raw-raster intersection is preferred. Identify-point
    sampling is a last resort and only accepted as a complete, single-service
    sample over the whole AOI × physiognomy stratum."""
    from soil_pronasolos_zonal import verified_local_horizons, mapped_soil_0_100_on_polygon
    local_paths=verified_local_horizons()
    local_audit=None
    if local_paths:
        local_result=mapped_soil_0_100_on_polygon(gdf,local_paths)
        if local_result.get("0–100 cm",{}).get("tc_ha") is not None:
            return _attach_embrapa_official_soc_bounds(gdf,local_result,local_paths)
        local_audit=local_result.get("_diagnostic")
    wcs_audit=None
    try:
        from pronasolos_wcs import fetch_horizons
        acquired=fetch_horizons(gdf.to_crs(4326).geometry.union_all())
        wcs_result=mapped_soil_0_100_on_polygon(
            gdf,acquired["paths"],
            source_label="Embrapa Solos/PronaSolos 90 m v2021 — rasters brutos via WCS GeoInfo")
        wcs_result.setdefault("_diagnostic",{})["wcs_provenance"]=acquired["provenance"]
        if wcs_result.get("0–100 cm",{}).get("tc_ha") is not None:
            return _attach_embrapa_official_soc_bounds(gdf,wcs_result,acquired["paths"])
        wcs_audit=wcs_result.get("_diagnostic")
    except Exception as exc:
        wcs_audit={"target_status":"WCS_INDISPONIVEL","reason":type(exc).__name__+": "+str(exc)[:300]}
    import requests
    gg=gdf.to_crs(3857); geom=gg.geometry.union_all()
    minx,miny,maxx,maxy=geom.bounds
    from pronasolos_identify import SERVICE_CANDIDATES, build_identify_params, extract_paired_horizons
    layer_ids=[2,3,4,5,6]
    from pronasolos_identify import sample_points_in_stratum
    points=sample_points_in_stratum(geom,max_points)
    if not points:
        return {"_diagnostic":{"target_status":"SEM_PONTOS_AMOSTRAIS","target_0_100_available":False,
                "local_raster_audit":local_audit,"wcs_raster_audit":wcs_audit}}
    session=requests.Session()
    attempts=[]
    observations=None
    selected_service=None
    # Do not mix products in a profile OR within the same stratum. A service
    # must return all five horizons at every reproducible area-uniform point.
    for endpoint in SERVICE_CANDIDATES:
        current=[]
        errors=[]
        for point in points:
            params=build_identify_params(point.x,point.y,(minx,miny,maxx,maxy),layer_ids)
            try:
                response=session.get(endpoint,params=params,timeout=(5,12))
                response.raise_for_status()
                current.append(extract_paired_horizons(response.json(),layer_ids))
            except Exception as exc:
                current.append({})
                errors.append(type(exc).__name__+": "+str(exc)[:160])
        valid=sum(all(layer in profile for layer in (2,3,4,5,6)) for profile in current)
        attempts.append({"service":endpoint,"complete_points":valid,
                         "requested_points":len(points),"errors":errors[:3]})
        if valid==len(points):
            observations=current
            selected_service=endpoint
            break
    if observations is None:
        return {"_diagnostic":{"target_status":"SERVICO_SEM_AMOSTRA_COMPLETA",
                "reason":"Nenhum serviço retornou os cinco horizontes em todos os pontos amostrais; estoque 0–100 cm mantido como N/D. "+ " | ".join(error for attempt in attempts for error in attempt["errors"])[:300],
                "services_checked":attempts,"samples_requested":len(points),
                "query_points_inside_stratum":len(points),"target_0_100_available":False,
                "no_partial_sample_extrapolation":True,
                "local_raster_audit":local_audit,"wcs_raster_audit":wcs_audit}}
    from soil_profile_stats import summarize_paired_soil_profiles
    out=summarize_paired_soil_profiles(observations)
    out["_diagnostic"]={"samples_requested":len(points),
        "valid_by_layer":{"0–5":len(points),"5–15":len(points),"15–30":len(points),
                          "30–60":len(points),"60–100":len(points)},
        "service":selected_service,"services_checked":attempts,
        "selected_points_by_service":{endpoint:(len(points) if endpoint==selected_service else 0) for endpoint in SERVICE_CANDIDATES},
        "no_cross_service_horizon_combination":True,"single_service_for_entire_stratum":True,
        "query_points_inside_stratum":len(points),"target_depth_cm":100,
        "target_0_100_available":"0–100 cm" in out,
        "local_raster_audit":local_audit,"wcs_raster_audit":wcs_audit,
        "method":"identify_point_sampling_fallback",
        "target_status":"AMOSTRA_COMPLETA_SERVICO_UNICO",
        "spatial_sampling_note":"Amostra espacial reprodutível dentro do polígono; sem intervalo preditivo nem erro do mapa."}
    return out

def self_test():
    assert abs(float(agb_mexiana(10))-0.1184*10**2.53)<1e-8
    assert ROOT_LOW<ROOT_RATIO<ROOT_HIGH
    assert abs(CARBON_FRACTION-0.47)<1e-9
    assert format_ptbr(12345.678,2)=="12.345,68" and format_ptbr(1234567.8,2)=="1.234.567,80" and format_ptbr(12.5,0)=="13" and format_ptbr(-1234.5,1)=="-1.234,5" and format_result_json({"a":12345.25})=={"a":"12.345,250000"}
    if sys.stdout is not None:print("ENFORM_VERDE_SELF_TEST_OK")

def acceptance_test(kmz_path):
    """Run the real Tapajós SAR acceptance path from the compiled executable."""
    gdf=read_vector(kmz_path)
    if gdf.empty:raise RuntimeError("AOI de aceitação sem feições.")
    metrics=geom_metrics(gdf)
    result=automatic_pipeline(gdf,"Amazônia","Floresta Ombrófila Densa das Terras Baixas",
                              cache=str(Path(tempfile.gettempdir())/"enform_verde_acceptance_sar"))
    audit=result.get("audit") or {}
    processed=list(audit.get("processed_without_agb") or [])
    pixel_count=sum(int(s.get("n",0)) for item in processed for s in item.get("stats",[]))
    pixel_count+=sum(int(s.get("n",0)) for s in result.get("stats",[]))
    if pixel_count<=0:raise RuntimeError("Nenhum pixel SAR foi processado dentro da AOI Tapajós.")
    agb=result.get("agb_mg_ha")
    if agb is None:
        lit=result.get("literature_reference") or {}
        if not lit.get("available") or not lit.get("sar_processed"):
            raise RuntimeError("Pixels SAR foram processados, mas a referência regional Tapajós não foi selecionada corretamente.")
    elif not str(result.get("data_origin","")).startswith("SAR"):
        raise RuntimeError("Origem AGB incompatível: resultado numérico sem proveniência SAR.")
    summary={"status":result.get("status"),"area_ha":metrics["area_ha"],"pixel_count":pixel_count,
             "data_origin":result.get("data_origin"),"scene_count":len(audit.get("alos_palsar_public",{}).get("scene_ids",[]))+len(audit.get("sentinel1_public",{}).get("scene_ids",[])),
             "fallback_agb_mg_ha":(result.get("literature_reference") or {}).get("agb_mg_ha")}
    (Path(tempfile.gettempdir())/"enform_verde_acceptance_result.json").write_text(json.dumps(summary,ensure_ascii=True),encoding="utf-8")
    return summary

def ui_smoke_test():
    root=App(); root.after(1200,root.destroy); root.mainloop()

def sentinel2_preview(gdf,out_h=700,extent_factor=1.36):
    """Recent low-cloud Sentinel-2 L2A RGB preview and AOI pixel coordinates; no user API key."""
    import rasterio
    from rasterio.warp import transform_bounds, transform, transform_geom
    from rasterio.windows import from_bounds
    from rasterio.features import geometry_mask
    g=gdf.to_crs(4326).copy(); geom=g.geometry.union_all().__geo_interface__
    body={"collections":["sentinel-2-l2a"],"intersects":geom,"limit":30,
          "sortby":[{"field":"properties.datetime","direction":"desc"}]}
    # Retry transient STAC gateway outages, keeping identical AOI/search terms.
    import time
    for attempt in range(2):
        try:
            rr=requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search",
                             json=body,timeout=(5,8))
            rr.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            code=getattr(getattr(exc,'response',None),'status_code',None)
            retryable=(code in (429,500,502,503,504) or isinstance(
                exc,(requests.exceptions.Timeout,requests.exceptions.ConnectionError)))
            if not retryable or attempt==1:
                raise
            time.sleep(2*(attempt+1))
    items=rr.json().get("features",[]); cand=[]
    for it in items:
        visual=(it.get("assets") or {}).get("visual")
        if not visual or not visual.get("href"):continue
        props=it.get("properties") or {}
        cloud=float(props.get("eo:cloud_cover",100.0) if props.get("eo:cloud_cover") is not None else 100.0)
        dt=str(props.get("datetime") or "")
        cand.append((cloud,dt,it,visual["href"]))
    if not cand:raise RuntimeError("Nenhuma cena Sentinel-2 L2A RGB encontrada para a AOI.")
    low=[x for x in cand if x[0]<=20.0]
    chosen=sorted(low,key=lambda x:x[1],reverse=True)[0] if low else sorted(cand,key=lambda x:(x[0],x[1]))[0]
    cloud,dt,it,unsigned=chosen
    href=None; sign_error=None
    for attempt in range(3):
        try:
            sg=requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/sign",params={"href":unsigned},timeout=(10,45))
            sg.raise_for_status(); href=sg.json()["href"]; break
        except Exception as e:
            sign_error=e
            if attempt<2:
                import time; time.sleep(1.2*(attempt+1))
    if not href:raise RuntimeError("Falha temporária ao assinar ativo Sentinel-2 após 3 tentativas: "+str(sign_error))
    import tls_setup
    with rasterio.Env(**tls_setup.gdal_env(),GDAL_HTTP_MULTIRANGE="SERIAL",GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="NO",CPL_VSIL_CURL_USE_HEAD="NO",GDAL_HTTP_VERSION="1.1"):
        with rasterio.open(href) as src:
            b=list(map(float,g.total_bounds)); bx=transform_bounds("EPSG:4326",src.crs,*b,densify_pts=21)
            dx=max(bx[2]-bx[0],1.0); dy=max(bx[3]-bx[1],1.0)
            factor=max(0.30,min(8.0,float(extent_factor))); cx=(bx[0]+bx[2])/2; cy=(bx[1]+bx[3])/2
            wb=(cx-dx*factor/2,cy-dy*factor/2,cx+dx*factor/2,cy+dy*factor/2)
            win=from_bounds(*wb,transform=src.transform).round_offsets().round_lengths()
            out_w=max(700,min(1200,round(out_h*max(float(win.width),1.0)/max(float(win.height),1.0))))
            arr=src.read(indexes=[1,2,3],window=win,out_shape=(3,out_h,out_w),
                         resampling=rasterio.enums.Resampling.bilinear,boundless=True,fill_value=0)
            rgb=np.moveaxis(arr,0,2)
            valid=np.isfinite(rgb).all(axis=2)&(rgb>0).any(axis=2)
            target_transform=src.window_transform(win)*rasterio.Affine.scale(
                float(win.width)/out_w,float(win.height)/out_h)
            aoi_geometry=transform_geom("EPSG:4326",src.crs,geom)
            aoi_mask=geometry_mask([aoi_geometry],out_shape=(out_h,out_w),
                                   transform=target_transform,invert=True)
            aoi_coverage=float((valid&aoi_mask).sum()/max(1,int(aoi_mask.sum())))
            if aoi_coverage<0.95:
                raise RuntimeError("Sentinel-2 Planetary Computer não cobre 95% dos pixels da AOI")
            if rgb.dtype!=np.uint8:
                valid=rgb[np.isfinite(rgb)&(rgb>0)]
                hi=float(np.percentile(valid,99)) if valid.size else 1.0
                rgb=np.clip(rgb/max(hi,1e-9)*255,0,255).astype(np.uint8)
            view=Image.fromarray(rgb,"RGB"); wt=src.window_transform(win); polygons=[]
            for geom0 in g.geometry:
                geoms=list(geom0.geoms) if geom0.geom_type=="MultiPolygon" else ([geom0] if geom0.geom_type=="Polygon" else [])
                for poly in geoms:
                    coords=list(poly.exterior.coords)
                    lon=[p[0] for p in coords]; lat=[p[1] for p in coords]
                    xx,yy=transform("EPSG:4326",src.crs,lon,lat); pts=[]
                    for x,y in zip(xx,yy):
                        col,row=(~wt)*(x,y)
                        pts.extend([float(col)*out_w/max(float(win.width),1.0),float(row)*out_h/max(float(win.height),1.0)])
                    if len(pts)>=6:polygons.append(pts)
    return {"image":view,"polygons":polygons,"scene_id":it.get("id"),"datetime":dt,"cloud_cover":cloud,
            "provider":"Sentinel-2 L2A / Microsoft Planetary Computer","asset":"visual",
            "aoi_coverage_fraction":aoi_coverage}



def _fetch_stac_features_paged(url,body,*,timeout=(8,45),max_pages=20):
    """Fetch paged STAC results so a first-page limit cannot hide AOI scenes."""
    response=requests.post(url,json=body,timeout=timeout)
    response.raise_for_status();payload=response.json()
    features=list(payload.get("features") or []);pages=1
    while pages<max_pages:
        link=next((x for x in payload.get("links",[]) if x.get("rel")=="next" and x.get("href")),None)
        if not link:break
        if str(link.get("method","GET")).upper()=="POST":
            response=requests.post(link["href"],json=link.get("body") or body,
                                   headers=link.get("headers") or {},timeout=timeout)
        else:
            response=requests.get(link["href"],timeout=timeout)
        response.raise_for_status();payload=response.json()
        page=payload.get("features") or []
        if not page:break
        features.extend(page);pages+=1
    return features


def sentinel2_earthsearch_preview(gdf,out_w=1000,out_h=560,extent_factor=1.36):
    """Real Sentinel-2 RGB COG pixels, scene fallback and pixel-aligned AOI overlay.

    Search results are only candidates: an actual three-band raster read with
    nonblank pixels is required before declaring any image loaded.
    """
    import time
    import rasterio
    from rasterio.warp import transform_bounds, transform, transform_geom, reproject, Resampling
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds, Window
    g=gdf.to_crs(4326).copy()
    geom=g.geometry.union_all().__geo_interface__
    body={"collections":["sentinel-2-l2a"],"intersects":geom,"limit":60,
          "sortby":[{"field":"properties.datetime","direction":"desc"}]}
    errors=[]
    items=[]
    for attempt in range(3):
        try:
            items=_fetch_stac_features_paged("https://earth-search.aws.element84.com/v1/search",
                                              body,timeout=(8,35),max_pages=20)
            break
        except requests.exceptions.RequestException as exc:
            if attempt==2:raise RuntimeError("Earth Search STAC indisponível: "+type(exc).__name__) from None
            time.sleep(1.2*(attempt+1))
    choices=[]
    for item in items:
        assets=item.get("assets") or {}
        if not all((assets.get(k) or {}).get("href") for k in ("red","green","blue")):continue
        props=item.get("properties") or {}
        dt=str(props.get("datetime") or "")
        try:cloud=float(props.get("eo:cloud_cover",100.0))
        except (ValueError,TypeError):cloud=100.0
        choices.append((cloud,dt,item,assets))
    if not choices:raise RuntimeError("Catálogo Earth Search sem cenas L2A RGB na AOI")
    # Prefer recent clear scenes, but NEVER fail just because the first COG
    # is inaccessible or its viewport contains no actual data.
    clear=sorted((x for x in choices if x[0]<=20),key=lambda x:x[1],reverse=True)
    other=sorted((x for x in choices if x[0]>20),key=lambda x:(x[0],x[1]))
    pool=(clear+other)[:80]
    bounds=tuple(map(float,g.total_bounds))
    out_width=max(320,min(1600,int(out_w)))
    out_height=max(240,min(1200,int(out_h)))
    # Keyless Sentinel-2 transport on Windows: avoid multipart byte ranges
    # and HEAD negotiation rejected by some TLS-inspecting proxies.
    base_env={"GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR","GDAL_HTTP_TIMEOUT":"35",
         "GDAL_HTTP_MAX_RETRY":"2",**tls_setup.gdal_env()}
    # Repeat each scene with independent GDAL transports before abandoning its
    # pixels; this specifically handles WinHTTP/TLS proxies that reject one
    # Range/HEAD combination for every candidate scene.
    expanded_pool=[(c,dt,item,assets,strategy) for c,dt,item,assets in pool
                   for strategy in range(3)]
    for cloud,dt,item,assets,strategy in expanded_pool:
        try:
            env=dict(base_env)
            env.update({"GDAL_HTTP_MULTIRANGE":"YES"})
            if strategy==1:
                env.update({"GDAL_HTTP_MULTIRANGE":"SERIAL","CPL_VSIL_CURL_USE_HEAD":"NO",
                            "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES":"NO","GDAL_HTTP_VERSION":"1.1"})
            elif strategy==2:
                env.update({"GDAL_HTTP_MULTIRANGE":"SERIAL","GDAL_HTTP_MULTIPLEX":"NO",
                            "CPL_VSIL_CURL_USE_HEAD":"NO","GDAL_HTTP_VERSION":"1.1"})
            with rasterio.Env(**env):
                with rasterio.open(assets["red"]["href"]) as red_src:
                    crs=red_src.crs
                    if not crs:raise RuntimeError("red band sem CRS")
                    minx,miny,maxx,maxy=transform_bounds("EPSG:4326",crs,*bounds,densify_pts=21)
                    dx=max(maxx-minx,1.0);dy=max(maxy-miny,1.0)
                    factor=max(0.30,min(8.0,float(extent_factor)))
                    cx=(minx+maxx)/2;cy=(miny+maxy)/2
                    viewport=(cx-dx*factor/2,cy-dy*factor/2,cx+dx*factor/2,cy+dy*factor/2)
                    window=from_bounds(*viewport,transform=red_src.transform).round_offsets().round_lengths()
                    window=window.intersection(Window(0,0,red_src.width,red_src.height))
                    if window.width<2 or window.height<2:raise RuntimeError("red band não cobre a AOI")
                    tr=red_src.window_transform(window)
                    rgb=[]
                    for band in ("red","green","blue"):
                        with rasterio.open(assets[band]["href"]) as src:
                            if not src.crs:raise RuntimeError(band+" sem CRS")
                            native_bounds=transform_bounds(crs,src.crs,*rasterio.windows.bounds(window,red_src.transform),densify_pts=21)
                            win=from_bounds(*native_bounds,transform=src.transform)
                            win=win.round_offsets().round_lengths()
                            try:win=win.intersection(Window(0,0,src.width,src.height))
                            except rasterio.errors.WindowError:raise RuntimeError(band+" sem interseção") from None
                            if win.width<2 or win.height<2:raise RuntimeError(band+" fora da cena")
                            source=src.read(1,window=win,out_shape=(min(1200,max(100,int(win.height))),
                                                               min(1600,max(100,int(win.width)))),
                                            masked=True,resampling=Resampling.bilinear)
                            data=np.ma.filled(source.astype(np.float32),np.nan)
                            dest=np.full((out_height,out_width),np.nan,dtype=np.float32)
                            # Rasterio window transform must account for out_shape
                            scaled_transform=src.window_transform(win)*rasterio.Affine.scale(
                                float(win.width)/data.shape[1],float(win.height)/data.shape[0])
                            target_transform=tr*rasterio.Affine.scale(
                                float(window.width)/out_width,float(window.height)/out_height)
                            reproject(data,dest,src_transform=scaled_transform,src_crs=src.crs,
                                      src_nodata=np.nan,dst_transform=target_transform,dst_crs=crs,
                                      dst_nodata=np.nan,resampling=Resampling.bilinear)
                            rgb.append(dest)
                    stack=np.stack(rgb,axis=2)
                    valid=np.isfinite(stack).all(axi…40889 tokens truncated…              ["Entrada","Sensor/produto selecionado",None,None,"Informado","SAR/multissensor","ESA/fornecedor",self.sensor.get()],
                ["Resultado","Soma parcial por hectare" if is_partial else "Carbono total por hectare",total,totalco2,"PARCIAL" if is_partial else "CONSOLIDADO","soma dos compartimentos elegíveis","Enform","inclui somente compartimentos calculados e elegíveis"],
                ["Resultado","Soma parcial da propriedade" if is_partial else "Carbono total da propriedade",None,None,"PARCIAL" if is_partial else "CONSOLIDADO","tC/ha × área","Enform",f"{format_ptbr(self.project.get('total_tc'),2)} tC | {format_ptbr(self.project.get('total_tco2e'),2)} tCO₂e; não extrapolar da área nativa para toda a AOI"]])
        # Carbon totals are stored as tonnes over the actually quantified native
        # intersections. Never multiply a native-area density by the entire AOI,
        # and never disguise missing pools as zeros or a complete total.
        sh_total=wb.create_sheet("Totais tCO2e")
        setup(sh_total,"Enform Verde — estoques quantificados (tCO₂e)")
        for j,h in enumerate(["Compartimento","Área quantificada (ha)",
                              "Densidade sobre área nativa (tC/ha)",
                              "Densidade sobre área nativa (tCO₂e/ha)",
                              "Estoque quantificado (tC)",
                              "Estoque quantificado (tCO₂e)",
                              "Situação","Nota de auditoria"],1):
            sh_total.cell(3,j,h).value=h
        source_native=self.project.get("native_carbon") or {}
        native_area=float(source_native.get("native_area_ha") or 0)
        rows_total=[]
        for component in source_native.get("components") or []:
            stock=component.get("known_total_tc")
            stock=float(stock) if stock is not None else None
            quantified=float(component.get("quantified_area_ha") or 0)
            rows_total.append([
                component.get("parametro"),quantified,
                stock/native_area if stock is not None and native_area>0 else None,
                (stock/native_area)*(44/12) if stock is not None and native_area>0 else None,
                stock,stock*(44/12) if stock is not None else None,
                "PARCIAL" if float(component.get("missing_native_area_ha") or 0)>0 else (
                    "QUANTIFICADO" if stock is not None else "N/D"),
                "Densidade distribuída sobre a área nativa total; parcelas não quantificadas não valem zero."])
        known=source_native.get("known_total_tc")
        known=float(known) if known is not None else None
        rows_total.append([
            "TOTAL CONHECIDO (não extrapolado)",native_area,
            known/native_area if known is not None and native_area>0 else None,
            (known/native_area)*(44/12) if known is not None and native_area>0 else None,
            known,known*(44/12) if known is not None else None,
            "PARCIAL — faltam compartimentos" if source_native and not source_native.get("complete") else (
                "CONSOLIDADO" if source_native and known is not None else "N/D"),
            "Soma apenas dos estoques elegíveis calculados. tCO₂e = tC × 44/12; não implica validação em campo."])
        put(sh_total,rows_total)
        sh_total.column_dimensions["A"].width=40
        sh_total.column_dimensions["B"].width=23
        sh_total.column_dimensions["C"].width=34
        sh_total.column_dimensions["D"].width=35
        sh_total.column_dimensions["E"].width=29
        sh_total.column_dimensions["F"].width=31
        sh_total.column_dimensions["G"].width=34
        sh_total.column_dimensions["H"].width=95
        sh_total.freeze_panes="C4"
        sh_total.auto_filter.ref=f"A3:H{3+len(rows_total)}"
        if not ar:
            for row_number,label in [(9,"Carbono por hectare"),(10,"Carbono da propriedade")]:
                ws.cell(row_number,2).value=label
                ws.cell(row_number,3).value=None;ws.cell(row_number,4).value=None
                ws.cell(row_number,5).value="NÃO CALCULADO"
                ws.cell(row_number,8).value="Execução de uso do solo sem estimativa de carbono."
        native=self.project.get("native_carbon")
        if native:
            ws.cell(9,2).value="Carbono/ha nativo — soma conhecida";ws.cell(9,3).value=(native["known_total_tc"]/native["native_area_ha"] if native.get("known_total_tc") is not None and native["native_area_ha"] else None)
            ws.cell(9,4).value=(ws.cell(9,3).value*44/12 if ws.cell(9,3).value is not None else None)
            ws.cell(9,8).value="Denominador: área nativa confirmada; lacunas não são zero."
            ws.cell(10,2).value="Carbono nas formações nativas";ws.cell(10,3).value=None;ws.cell(10,4).value=None
            ws.cell(10,8).value=(format_ptbr(native["known_total_tc"],2)+" tC; "+format_ptbr(native["known_total_tco2"],2)+" tCO₂e; "+("total" if native["complete"] else "soma parcial") if native.get("known_total_tc") is not None else "NÃO ESTIMADO")
            sh=wb.create_sheet("Carbono por Formação");setup(sh,"Enform Verde — carbono apenas nas interseções nativas")
            for j,h in enumerate(["Fitofisionomia","Área nativa (ha)","% da AOI","Compartimento",
                                   "tC/ha","tCO₂e/ha","Estoque tC","Estoque tCO₂e",
                                   "Fonte","Limitação / incerteza"],1):sh.cell(3,j,h).value=h
            put(sh,[[st["physiognomy"],st["area_ha"],st["area_pct"],r["parametro"],
                     r.get("tc"),
                     r["tc"]*44/12 if r.get("tc") is not None else None,
                     r.get("total_tc"),
                     r["total_tc"]*44/12 if r.get("total_tc") is not None else None,
                     r.get("fonte"),st["physiognomy_resolution"]+
                     "; classe reconhecida: "+st["class_name"]+"; "+str(r.get("obs"))]
                     for st in native["strata"] for r in st["components"]])
            sh.column_dimensions["I"].width=42
            sh.column_dimensions["J"].width=92
            sh.auto_filter.ref=f"A3:J{3+sum(len(st['components']) for st in native['strata'])}"
            sh=wb.create_sheet("Solo por Formação");setup(sh,"Enform Verde — perfis de solo nas interseções nativas")
            from soil_intersection_report import soil_intersection_summary
            for j,h in enumerate(["Fitofisionomia","Área nativa (ha)","% da AOI","Profundidade","tC/ha","DP espacial","Fonte","Uso no total","Método","Área mapeada (ha)","Cobertura do mapa (%)","Pixels"],1):sh.cell(3,j,h).value=h
            def _soil_row(st,depth,profile):
                info=soil_intersection_summary(st.get("soil_profiles"))
                use=("Somado (só área mapeada)" if profile.get("partial_coverage") else "Somado") if depth=="0–100 cm" else "Informativo; não somado novamente"
                return [st["physiognomy"],st["area_ha"],st["area_pct"],depth,profile.get("tc_ha"),profile.get("spatial_sd_tc_ha"),"Embrapa/PronaSolos",use,info["method"],info["mapped_area_ha"],info["coverage_pct"],info["pixels"]]
            put(sh,[_soil_row(st,depth,profile) for st in native["strata"] for depth,profile in (st.get("soil_profiles") or {}).items() if isinstance(profile,dict) and profile.get("tc_ha") is not None])
            sh=wb.create_sheet("Incerteza Oficial do Solo")
            setup(sh,"Enform Verde — limites marginais oficiais SOC (não IC95% conjunto)")
            for j,h in enumerate(["Fitofisionomia","Horizonte (cm)","Limite inferior (tC/ha)",
                                   "Limite superior (tC/ha)","Estado dos limites",
                                   "Envelope somado 0–100 (tC/ha)","Envelope estoque (tC)",
                                   "Fonte","Interpretação"],1):
                sh.cell(3,j,h).value=h
            soil_unc_rows=[]
            for st in native["strata"]:
                top=(st.get("soil_profiles") or {}).get("0–100 cm") or {}
                official=top.get("official_uncertainty") or {}
                horizons=official.get("marginal_horizon_bounds") or {}
                lohi=official.get("sum_bounds_envelope_tc_ha") or []
                stock=official.get("sum_bounds_envelope_stock_tC") or []
                if not horizons:
                    soil_unc_rows.append([st["physiognomy"],"0–100",None,None,
                        "N/D — "+str(official.get("reason") or "raster de limite indisponível")[:180],
                        None,None,None,"DP espacial não substitui incerteza oficial"])
                else:
                    for depth,bounds in horizons.items():
                        soil_unc_rows.append([st["physiognomy"],depth,
                            bounds.get("lower_tc_ha"),bounds.get("upper_tc_ha"),
                            official.get("status"),
                            (str(lohi) if lohi else None),(str(stock) if stock else None),
                            (official.get("provenance") or {}).get("source"),
                            "Envelope somado de limites marginais; NÃO é IC95% conjunto"])
            put(sh,soil_unc_rows or [["N/D","0–100",None,None,"N/D",None,None,None,
                                       "Nenhuma área nativa com mapa de solo"]])
        sh=wb.create_sheet("Compartimentos"); setup(sh,"Enform Verde — Compartimentos de carbono")
        put(sh,[["Resultado — "+r.get("origem","N/D"),r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in ar])
        for sheet,param in [("Biomassa Aérea","Biomassa aérea"),("Biomassa Subterrânea","Biomassa subterrânea"),("Necromassa","Necromassa"),("Serapilheira","Serapilheira")]:
            sh=wb.create_sheet(sheet); setup(sh,"Enform Verde — "+sheet)
            rr=rows_for_compartment(ar,param)
            data=[["Resultado",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]] for r in rr]
            if not data:data=[["Resultado",param,None,None,"NÃO CALCULADO","—","—","Não houve dado válido nesta execução; nenhum valor foi inventado."]]
            put(sh,data)
        sh=wb.create_sheet("Auditoria Gravimétrica"); setup(sh,"Serapilheira — origem, equação, incerteza e auditoria")
        litter_audit_rows=[]
        for st in (self.project.get("native_carbon") or {}).get("strata",[]):
            for c in st.get("components",[]):
                if c.get("parametro")!="Serapilheira": continue
                litter_audit_rows.append([st.get("physiognomy"),st.get("area_ha"),
                    c.get("status") or ("CENÁRIO EXPERIMENTAL" if c.get("origin")=="EXPERIMENTAL_FISICO" else "N/D"),
                    c.get("tc"),c.get("source"),c.get("source_url"),c.get("method"),
                    c.get("uncertainty_kind"),json.dumps(c.get("uncertainty") or {},ensure_ascii=False,sort_keys=True),
                    json.dumps(c.get("calculation_trace") or {},ensure_ascii=False,sort_keys=True),
                    "; ".join(map(str,c.get("limitations") or [])),
                    "IFN profundidade não equivale a massa; estoque de C requer fração medida."])
        if not litter_audit_rows:
            litter_audit_rows=[["N/D",None,"N/D",None,"SFB/IFN: profundidade apenas",None,
                "Sem conversão; aguarda pares de massa seca e profundidade compatíveis",None,None,None,
                "Nenhuma calibração gravimétrica pareada validada foi fornecida para esta classe/região.",
                "Não converter profundidade em massa com constante nacional."]]
        put(sh,[["Fitofisionomia","Área nativa (ha)","Situação","tC/ha (fora do total conhecido se experimental)",
                 "Fonte","URL / fontes","Método","Tipo de incerteza","Incerteza e interpretação",
                 "Equação e trilha de cálculo","Limites / transferência","Regra de leitura"],*litter_audit_rows])
        sh.freeze_panes="A4"; sh.auto_filter.ref=f"A3:L{3+len(litter_audit_rows)}"
        sar_result=self.project.get("sar_result") or {}
        class_layers=(sar_result.get("fitofisionomia_raster_stats") or {})
        class_rows=(class_layers.get("AGB") or {}).get("classes",[])
        sh=wb.create_sheet("AGB por Fitofisionomia"); setup(sh,"Enform Verde — AGB SAR por interseção IBGE")
        class_headers=["Classe IBGE","Área (ha)","Área (%)","AGB média (Mg/ha)","AGB total (Mg)","Pixels válidos","Incerteza média do produto","Altura média (m)"]
        for j,h in enumerate(class_headers,1): sh.cell(3,j,h).value=h
        unc_by={x.get("physiognomy"):x for x in (class_layers.get("UNCERTAINTY") or {}).get("classes",[])}
        hgt_by={x.get("physiognomy"):x for x in (class_layers.get("HEIGHT") or {}).get("classes",[])}
        data=[]
        for cr in class_rows:
            name=cr.get("physiognomy")
            data.append([name,cr.get("area_ha"),cr.get("area_share_pct"),cr.get("agb_mean_mg_ha"),
                         cr.get("agb_total_mg"),cr.get("n"),unc_by.get(name,{}).get("mean"),hgt_by.get(name,{}).get("mean")])
        if not data:data=[["NÃO CALCULADO — camada IBGE de fitofisionomias ausente ou sem raster AGB",None,None,None,None,None,None,None]]
        put(sh,data)
        sh["A2"]="Interseção espacial AOI × classe IBGE; erro do produto e altura são camadas separadas. AGB total = média Mg/ha × área da classe."
        sh.merge_cells("A2:H2")
        sh["A2"].alignment=Alignment(wrap_text=True,vertical="center")
        sh=wb.create_sheet("Carbono do Solo"); setup(sh,"Enform Verde — Carbono orgânico do solo")
        soil_rows=[r for r in ar if r["parametro"].startswith("Solo ")]
        soil_data=[["MAPEAMENTO — PronaSolos",r["parametro"],r["tc"],r["tco2"],r["status"],r["metodo"],r["fonte"],r["obs"]+" | "+r.get("erro_metrica","")] for r in soil_rows]
        if not soil_data: soil_data=[["MAPEAMENTO","Carbono do solo",None,None,"NÃO CALCULADO","PronaSolos 90 m","Embrapa Solos/PronaSolos","Sem valores válidos nesta execução."]]
        put(sh,soil_data)
        sh=wb.create_sheet("Diagnóstico IBGE"); setup(sh,"Enform Verde — Diagnóstico territorial IBGE")
        diag=self.project.get("ibge_diagnosis",{})
        idata=[]
        for n,ha,pct in diag.get("biomas",[]): idata.append(["Bioma",n,None,None,"IBGE oficial","interseção espacial","IBGE — Biomas 2025",f"{format_ptbr(ha,2)} ha | {format_ptbr(pct,2)}% da área"])
        for grp in diag.get("vegetacao",[]):
            for n,ha,pct in grp.get("classes",[]): idata.append(["Vegetação "+grp.get("campo",""),n,None,None,"IBGE oficial 2026","interseção espacial","IBGE — Vegetação 2026",f"{format_ptbr(ha,2)} ha | {format_ptbr(pct,2)}% da área"])
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
        pedo=self.project.get("soil_pedology") or {}
        sh=wb.create_sheet("Classificação de Solos")
        setup(sh,"Enform Verde — classes pedológicas Embrapa (não é estoque de carbono)")
        for j,h in enumerate(["Unidade de mapeamento","Símbolo","Área (ha)","% da AOI",
                              "Componentes (sem percentual próprio)","Origem / escala",
                              "Incerteza","Limitações"],1):sh.cell(3,j,h).value=h
        pedo_rows=[[r.get("mapping_unit"),r.get("symbol"),r.get("area_ha"),
                    r.get("area_pct_aoi"),"; ".join(r.get("components") or []),
                    "Embrapa Solos — 1:5.000.000",None,
                    "Não é a área individual de cada componente; verificar licença comercial"]
                   for r in pedo.get("soil_mapping_units") or []]
        put(sh,pedo_rows or [["N/D",None,None,None,None,pedo.get("source"),
                             None,pedo.get("reason") or "Cartografia não recuperada"]])
        fertility=self.project.get("soil_fertility") or {}
        sh=wb.create_sheet("Fertilidade do Solo")
        setup(sh,"Enform Verde — estimativas cartográficas Embrapa 90 m (não são análises de laboratório)")
        for j,h in enumerate(["Unidade cartográfica","Atributo","Profundidade cm","Média predita",
                              "Unidade","DP espacial (não IC95%)","Pixels","Área mapeada ha",
                              "Cobertura %","Erro preditivo","Cobertura WCS","SHA256 raster"],1):
            sh.cell(3,j,h).value=h
        rows_fert=[]
        for unit_name,measurements in (fertility.get("units") or {}).items():
            for measure in measurements:
                if measure.get("mean") is not None:
                    rows_fert.append([unit_name,measure.get("label"),measure.get("depth_cm"),
                                     measure.get("mean"),measure.get("unit"),measure.get("spatial_sd"),
                                     measure.get("valid_pixels"),measure.get("mapped_area_ha"),
                                     measure.get("coverage_pct"),measure.get("uncertainty"),
                                     measure.get("wcs_coverage_id"),measure.get("raster_sha256")])
        put(sh,rows_fert or [["N/D",fertility.get("reason") or "sem pixels numéricos oficiais",
                             None,None,None,None,None,None,None,"N/D",None,None]])
        model_manifest=self.project.get("modeled_field_predictions") or {}
        sh=wb.create_sheet("Modelo Para Campo")
        setup(sh,"Enform Verde — resultados experimentais, NÃO medições de campo")
        sh.column_dimensions["I"].width=48
        sh.column_dimensions["J"].width=80
        sh.column_dimensions["K"].width=34
        sh.row_dimensions[3].height=58
        sh.freeze_panes="D4"
        for j,h in enumerate(["ID previsão","Fitofisionomia","Compartimento/cultura",
                              "Status","Estimativa (tC/ha ou t/ha)","Área (ha)",
                              "Faixa condicional","Tipo de incerteza","Origem",
                              "Protocolo de campo","Valor medido em campo (EM BRANCO)"],1):
            cell=sh.cell(3,j,h)
            cell.font=Font(bold=True,color=white)
            cell.fill=PatternFill("solid",fgColor=orange)
            cell.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
            cell.border=Border(top=thin,bottom=thin,left=thin,right=thin)
        model_rows=[]
        for prediction in model_manifest.get("predictions") or []:
            model_rows.append([prediction.get("prediction_id"),
                prediction.get("physiognomy"),prediction.get("compartment"),
                prediction.get("status"),
                prediction.get("density_predicted_tc_ha",
                               prediction.get("predicted_t_ha")),
                prediction.get("area_basis_ha"),
                str(prediction.get("density_range_tc_ha") or
                    prediction.get("prediction_range_t_ha") or "N/D"),
                prediction.get("uncertainty_kind"),prediction.get("source"),
                prediction.get("field_protocol"),None])
        put(sh,model_rows or [["N/D",None,None,"SEM RESULTADOS MODELADOS",None,None,
                              "N/D","N/D","N/D","Executar análise",None]])
        sh.auto_filter.ref=f"A3:K{max(4,3+len(model_rows))}"
        # Field observations must be inserted by the operator after real sampling.
        for row_i in range(4,4+max(1,len(model_rows))):
            sh.cell(row_i,11).value=None
        land=self.project.get("land_use")
        if land:
            sh=wb.create_sheet("Uso do Solo"); setup(sh,"Enform Verde — classes de uso e cobertura")
            for j,h in enumerate(["Classe","Área (ha)","Área (%)","Origem","Legenda","Confiança","Método de área","Arquivo vetorial"],1):sh.cell(3,j,h).value=h
            put(sh,[[r["class_name"],r["area_ha"],r["area_pct"],r["source"],r["taxonomy"],
                     "Validação no JSON; confiança cartográfica não inferida" if not r["source"].startswith("SAR_VALIDADO") else "IC95% da precisão por classe no JSON",
                     land["method"],land["vector_path"]] for r in land["classes"]])
            sh=wb.create_sheet("Validação Uso SAR");setup(sh,"Enform Verde — confiança independente obrigatória")
            val=land.get("validation") or {}
            for j,h in enumerate(["Nível","Classe","n independente","Acertos","Precisão","Limite inferior IC95%","Elegível","Observação"],1):sh.cell(3,j,h).value=h
            data=[]
            for level,report in [("detalhado",val),("grupo",val.get("parent_validation",{}))]:
                for label,gate in report.get("gates",{}).items():
                    data.append([level,label,gate["n_independent"],gate["correct"],gate["precision"],gate["precision_wilson95_lower"],str(gate["eligible"]),report.get("uncertainty")])
            put(sh,data or [["Sem validação",None,None,None,None,None,"NÃO","; ".join(land.get("warnings",[]))]])
        catalog=self.project.get("sar_catalog") or []
        if catalog:
            sh=wb.create_sheet("Aquisições SAR")
            for col,value in enumerate(["Catálogo","Produto","Cena","Aquisição Brasília (UTC−3)","Aquisição UTC","Situação","Observação"],1):
                sh.cell(1,col,value)
            line=2
            for source in catalog:
                for scene in source.get("items",[]):
                    values=[source.get("provider"),source.get("dataset"),scene.get("id"),
                            scene.get("acquisition_brasilia"),scene.get("acquisition_utc"),
                            scene.get("acquisition_status"),
                            "Descoberta no catálogo; não comprova que a cena tenha sido processada"]
                    for col,value in enumerate(values,1):
                        sh.cell(line,col,value)
                    line+=1
            sh.freeze_panes="A2"
            sh.column_dimensions["A"].width=25
            sh.column_dimensions["B"].width=25
            sh.column_dimensions["C"].width=42
            sh.column_dimensions["D"].width=30
            sh.column_dimensions["E"].width=30
            sh.column_dimensions["F"].width=37
            sh.column_dimensions["G"].width=76
        # Charts use only inventory references already matched to each native
        # stratum and SAR height pixels actually read inside that stratum.
        chart_native=self.project.get("native_carbon") or {}
        bio_refs=chart_native.get("biodiversity_references") or []
        native_strata=chart_native.get("strata") or []
        def inventory_source_labels(refs):
            labels=set()
            for ref in refs:
                institution=str(ref.get("institutions") or "Instituição não identificada")
                institutions=ref.get("institutions") or []
                urls=ref.get("source_urls") or []
                for url in urls:
                    labels.add(f"{', '.join(institutions) if institutions else institution} — {url}")
            return sorted(labels)
        chart=wb.create_sheet("Gráficos")
        from openpyxl.chart import BarChart, LineChart, Reference
        chart.sheet_view.showGridLines=False
        chart.merge_cells("A1:L1");chart["A1"]="Enform Verde — distribuições estruturais e biodiversidade"
        chart["A1"].font=Font(size=16,bold=True,color=white);chart["A1"].fill=PatternFill("solid",fgColor=green)
        chart["A1"].alignment=Alignment(vertical="center");chart.row_dimensions[1].height=30
        for span in ("A2:C2","A3:C3","D2:F2","D3:F3","G2:L2","G3:L3"):
            chart.merge_cells(span)
        for col in "ABCDEFGHIJKL":chart.column_dimensions[col].width=17
        chart.column_dimensions["A"].width=20;chart.column_dimensions["D"].width=22;chart.column_dimensions["G"].width=28
        for c in ("A2","A3","A4","D2","D3","D4","G2","G3","G4"):
            chart[c].alignment=Alignment(wrap_text=True,vertical="center")
        chart["A2"]="Distribuição diamétrica média e participação da área basal por classe DAP."
        chart["A2"].font=Font(bold=True,color=green)
        chart["A4"]="Classe DAP";chart["B4"]="Árvores médias (ind./ha)"
        chart["C4"]="Área basal média (m²/ha)";chart["D4"]="Frequência de árvores (%)"
        chart["E4"]="Área basal da classe (%)"
        dbh_bins=[("5–10 cm","dbh_5_10_cm"),("10–20 cm","dbh_10_20_cm"),
            ("20–30 cm","dbh_20_30_cm"),("30–40 cm","dbh_30_40_cm"),
            ("40–60 cm","dbh_40_60_cm"),("≥60 cm","dbh_60_plus_cm")]
        dbh_by_stratum=[];dbh_contributing_refs=[]
        for idx,ref in enumerate(bio_refs):
            if ref.get("status")!="REFERENCIA_FITOSSOCIOLOGICA_REGIONAL":continue
            st=native_strata[idx] if idx<len(native_strata) else {}
            area=float(st.get("area_ha") or 0)
            rows={x.get("bin_id"):x for x in ref.get("dbh_distribution_by_plot_mean") or []}
            if area>0 and all(key in rows for _,key in dbh_bins):
                dbh_by_stratum.append((area,rows))
                dbh_contributing_refs.append(ref)
        if dbh_by_stratum:
            area_sum=sum(x[0] for x in dbh_by_stratum)
            means=[]
            for row,(label,key) in enumerate(dbh_bins,5):
                mean_stems=sum(area*float(rows[key]["mean_stems_ha"]) for area,rows in dbh_by_stratum)/area_sum
                mean_basal=sum(area*float(rows[key]["mean_basal_area_m2_ha"]) for area,rows in dbh_by_stratum)/area_sum
                means.append((mean_stems,mean_basal))
                chart.cell(row,1,label);chart.cell(row,2,mean_stems);chart.cell(row,3,mean_basal)
            total_stems=sum(x[0] for x in means);total_basal=sum(x[1] for x in means)
            chart["A40"]="Dados auxiliares das curvas diamétricas"
            chart["A41"]="Classe DAP";chart["B41"]="Frequência de árvores (%)";chart["C41"]="Área basal da classe (%)"
            for row,((label,_),(mean_stems,mean_basal)) in enumerate(zip(dbh_bins,means),42):
                chart.cell(row,1,label)
                chart.cell(row,2,100*mean_stems/total_stems if total_stems else 0)
                chart.cell(row,3,100*mean_basal/total_basal if total_basal else 0)
            dbh_refs=[ref for ref in dbh_contributing_refs if ref.get("source_urls")]
            dbh_sources=inventory_source_labels(dbh_refs)
            chart["A3"]="Médias por DAP ponderadas pela área dos estratos nativos; curvas mostram frequência relativa de indivíduos e participação da área basal. Fontes (instituição — URL): "+("; ".join(dbh_sources) or "N/D")
            lc=LineChart();lc.title="Distribuição diamétrica média e área basal";lc.y_axis.title="Participação média (%)";lc.x_axis.title="DAP"
            lc.add_data(Reference(chart,min_col=2,max_col=3,min_row=41,max_row=47),titles_from_data=True)
            lc.set_categories(Reference(chart,min_col=1,min_row=42,max_row=47));lc.height=8;lc.width=16;chart.add_chart(lc,"A12")
        else:
            chart["A5"]="N/D — sem inventário compatível e carregado para os estratos nativos confirmados."
            # Keep the missing-inventory note inside the left chart panel;
            # columns D:F belong to the height panel and its own N/D note.
            chart.merge_cells("A5:C5")
            chart["A5"].alignment=Alignment(wrap_text=True,vertical="center")
            chart.row_dimensions[5].height=32
            chart["A3"]="Fonte/escopo: N/D; não substituir por média de outra fitofisionomia ou região sem identificação."

        chart["D2"]="Altura: distribuição observada por pixels SAR; se ausência certificada, referência de alturas de árvores inventariadas."
        chart["D2"].font=Font(bold=True,color=green);chart["D4"]="Faixa de altura (m)";chart["E4"]="Frequência (%)"
        sar_bins={};sar_pixel_total=0;strata_with_height=0
        for st in native_strata:
            info=(st.get("sar_details") or {}).get("height_pixel_distribution") or {}
            if info.get("status")!="SAR_PIXELS_HISTOGRAMMED":continue
            strata_with_height+=1
            for b in info.get("bins") or []:
                key=b.get("label");sar_bins[key]=sar_bins.get(key,0)+int(b.get("pixel_count") or 0)
                sar_pixel_total+=int(b.get("pixel_count") or 0)
        height_source=""
        if sar_pixel_total:
            labels=[("0–5 m",0), ("5–10 m",1), ("10–15 m",2), ("15–20 m",3),
                ("20–25 m",4), ("25–30 m",5), ("30–35 m",6), ("35–40 m",7),
                ("40–45 m",8), ("45–50 m",9), ("50–55 m",10), ("55–60 m",11), ("≥60 m",12)]
            for row,(label,_) in enumerate(labels,5):
                chart.cell(row,4,label);chart.cell(row,5,100*sar_bins.get(label,0)/sar_pixel_total)
            height_source=("Pixels SAR válidos lidos em "+str(strata_with_height)+" estrato(s) nativo(s); n="+
                str(sar_pixel_total)+" pixels. Fonte: "+"; ".join(sorted({str((st.get("sar_details") or {}).get("source") or (st.get("sar_details") or {}).get("product") or "produto SAR" ) for st in native_strata if (st.get("sar_details") or {}).get("height_pixel_distribution")})))
            chart["D3"]=height_source+". Pixels sem dado não foram preenchidos."
        else:
            cert=(chart_native.get("height_absence_certificate") or
                  (self.project.get("sar_result") or {}).get("height_absence_certificate"))
            from sar_height_absence import regional_height_fallback_decision
            allow_region,absence_reason=regional_height_fallback_decision(cert)
            regional=[]
            if allow_region:
                regional_pairs=[(ref,ref.get("inventory_tree_height_distribution") or {}) for ref in bio_refs
                    if ref.get("status")=="REFERENCIA_FITOSSOCIOLOGICA_REGIONAL" and ref.get("source_urls") and ref.get("institutions")]
                regional_pairs=[(ref,dist) for ref,dist in regional_pairs
                    if dist.get("status")=="REFERENCIA_ALTURA_INVENTARIO_REGIONAL" and float(dist.get("n_plots") or 0)>0]
                regional_refs=[ref for ref,_ in regional_pairs]
                regional=[dist for _,dist in regional_pairs]
            if allow_region and regional:
                plot_weights=[float(x.get("n_plots") or 0) for x in regional]
                weight_sum=sum(plot_weights)
                for row,(i,label) in enumerate(enumerate(["0–5 m","5–10 m","10–15 m","15–20 m","20–25 m","25–30 m","30–35 m","35–40 m","40–45 m","45–50 m","50–55 m","55–60 m","≥60 m"]),5):
                    value=sum(w*float(x["bins"][i]["mean_frequency_pct"]) for x,w in zip(regional,plot_weights))/weight_sum
                    chart.cell(row,4,label);chart.cell(row,5,value)
                sources=inventory_source_labels(regional_refs)
                height_source="Fallback regional autorizado por ausência SAR certificada. Médias de alturas medidas em inventários compatíveis ("+str(sum(plot_weights))+" parcelas). Fontes (instituição — URL): "+"; ".join(sources)
                chart["D3"]=height_source+". Altura de árvores inventariadas, não altura do dossel SAR nem medição da propriedade."
            else:
                if allow_region and not regional:
                    absence_reason="SEM_INVENTARIO_COMPATIVEL_COM_FONTE_IDENTIFICAVEL"
                chart["D5"]="N/D — "+absence_reason+"; médias regionais sem fonte rastreável ou falhas técnicas não substituem a observação SAR."
                # Keep the no-data note within the height panel; extending
                # through column G overwrote the Top-10 species table.
                chart.merge_cells("D5:F5")
                chart["D3"]="Sem altura SAR válida; contingência microrregional/regional bloqueada até comprovar ausência de cobertura."
        if sar_pixel_total or (allow_region and regional):
            hc=LineChart();hc.title="Distribuição de altura";hc.y_axis.title="Frequência (%)";hc.x_axis.title="Altura"
            hc.add_data(Reference(chart,min_col=5,min_row=4,max_row=17),titles_from_data=True)
            hc.set_categories(Reference(chart,min_col=4,min_row=5,max_row=17));hc.height=8;hc.width=16;chart.add_chart(hc,"H12")

        chart["G2"]="10 espécies dominantes — frequência média de ocorrência nas parcelas compatíveis."
        chart["G2"].font=Font(bold=True,color=green);chart["G4"]="Espécie";chart["H4"]="Frequência média (%)"
        species_values={};species_weights={}
        for ref in bio_refs:
            if ref.get("status")!="REFERENCIA_FITOSSOCIOLOGICA_REGIONAL":continue
            weight=float(ref.get("inventory_n_plots") or 0)
            for item in ref.get("top10_by_plot_incidence") or []:
                name=str(item.get("species") or "");freq=float(item.get("frequency_pct") or 0)
                if name:
                    species_values[name]=species_values.get(name,0)+freq*weight
                    species_weights[name]=species_weights.get(name,0)+weight
        species_rank=sorted(((name,species_values[name]/species_weights[name]) for name in species_values if species_weights[name]>0),key=lambda x:(-x[1],x[0]))[:10]
        if species_rank:
            for row,(name,freq) in enumerate(species_rank,5):chart.cell(row,7,name);chart.cell(row,8,freq)
            species_refs=[ref for ref in bio_refs if ref.get("status")=="REFERENCIA_FITOSSOCIOLOGICA_REGIONAL" and ref.get("source_urls")]
            species_sources=inventory_source_labels(species_refs)
            chart["G3"]="Inventários microrregionais/regionais compatíveis; média ponderada por parcelas. Fontes (instituição — URL): "+("; ".join(species_sources) or "N/D")
            bc=BarChart();bc.type="bar";bc.style=10;bc.title="10 espécies mais frequentes";bc.x_axis.title="Frequência média (%)";bc.y_axis.title="Espécie"
            bc.add_data(Reference(chart,min_col=8,min_row=4,max_row=4+len(species_rank)),titles_from_data=True)
            bc.set_categories(Reference(chart,min_col=7,min_row=5,max_row=4+len(species_rank)));bc.height=8;bc.width=16;chart.add_chart(bc,"A29")
        else:
            chart["G5"]="N/D — inventário compatível não carregado ou não encontrado."
            chart.merge_cells("G5:L5");chart["G3"]="Fonte: N/D; espécies não serão inferidas de inventários incompatíveis."
        chart.freeze_panes="A4";chart.sheet_view.zoomScale=85
        # Single-screen executive index. Numeric stocks remain numeric so the
        # operator can audit or reuse them; no missing pool is treated as zero.
        dashboard=wb.create_sheet("PAINEL EXECUTIVO",0)
        setup(dashboard,"ENFORM VERDE — PAINEL EXECUTIVO DA PROPRIEDADE")
        dash_headers=["Seção","Indicador","tC/ha","tCO₂e/ha","Estoque tC",
                      "Estoque tCO₂e","Situação","Área / fonte / observação"]
        for col,label in enumerate(dash_headers,1):
            dashboard.cell(3,col,label)
        dash=[]
        dn=self.project.get("native_carbon") or {}
        dl=self.project.get("land_use") or {}
        d_ha=dn.get("area_aoi_ha") or self.project.get("area_ha")
        d_native=dn.get("native_area_ha")
        d_known=dn.get("known_total_tc")
        def drow(section,label,tc=None,tco2=None,stock=None,status="INFORMATIVO",note=""):
            dash.append([section,label,tc,tco2,stock,
                         (stock*44/12 if stock is not None else None),status,note])
        drow("IMÓVEL","Área da AOI",status="GEOMETRIA",note=(format_ptbr(d_ha,2)+" ha | EPSG:6933") if d_ha is not None else "N/D")
        drow("IMÓVEL","Bioma IBGE",status="CARTOGRÁFICO",note=self.biome.get())
        drow("VEGETAÇÃO","Região fitoecológica IBGE",status="POTENCIAL IBGE",note=self.phys.get())
        drow("VEGETAÇÃO","Cobertura nativa mapeada",status="MAPA, NÃO CAMPO",
             note=(format_ptbr(d_native,2)+" ha") if d_native is not None else "N/D")
        drow("VEGETAÇÃO","Outros usos",status="CARTOGRÁFICO",note=
             format_ptbr(dn.get("excluded_other_uses_ha"),2)+" ha" if dn.get("excluded_other_uses_ha") is not None else "N/D")
        drow("VEGETAÇÃO","Cobertura não determinada",status="N/D / MAPA",note=
             format_ptbr(dn.get("unknown_cover_area_ha"),2)+" ha" if dn.get("unknown_cover_area_ha") is not None else "N/D")
        from executive_carbon_report import litter_dashboard_summaries
        litter_rows=litter_dashboard_summaries(dn)
        for part in dn.get("components") or []:
            if str(part.get("parametro") or "").casefold() in ("serapilheira","serrapilheira"):
                continue
            stock=part.get("known_total_tc")
            drow("CARBONO",part.get("parametro") or "Compartimento",
                 (stock/d_native if stock is not None and d_native else None),
                 (stock/d_native*44/12 if stock is not None and d_native else None),
                 stock,"PARCIAL" if part.get("missing_native_area_ha") else
                 ("QUANTIFICADO" if stock is not None else "N/D"),
                 "Área quantificada: "+format_ptbr(part.get("quantified_area_ha"),2)+" ha; "
                 "não somar sem evidência independente")
        drow("CARBONO","TOTAL CONHECIDO",
             d_known/d_native if d_known is not None and d_native else None,
             d_known/d_native*44/12 if d_known is not None and d_native else None,
             d_known,"PARCIAL" if not dn.get("complete") else "CONSOLIDADO",
             "Somente estoques elegíveis; densidade sobre área NATIVA; não extrapolado.")
        if litter_rows:
            for litter in litter_rows:
                label="Serapilheira — "+str(litter["physiognomy"])
                drow("CARBONO",label,litter.get("tc_ha"),litter.get("tco2e_ha"),
                     litter.get("stock_tc"),litter.get("status"),litter.get("note"))
        else:
            diagnostic=next((c for st in dn.get("strata",[]) for c in st.get("components",[])
                             if c.get("parametro")=="Serapilheira"),{})
            audit=dn.get("litter_gravimetric_audit") or {}
            reason=(diagnostic.get("obs") or diagnostic.get("uncertainty_kind") or
                    audit.get("reason") or audit.get("status") or
                    "Nenhuma referência de estoque compatível foi aceita; sem substituir por zero.")
            drow("CARBONO","Serapilheira",status="N/D — MOTIVO REGISTRADO",note=str(reason))
        dp=self.project.get("soil_pedology") or {}
        soil_units=dp.get("soil_mapping_units") or []
        if soil_units:
            for unit in soil_units:
                drow("PEDOLOGIA",unit.get("mapping_unit") or "Unidade de solo",
                     status="MAPA REGIONAL",note=format_ptbr(unit.get("area_ha"),2)+
                     " ha; associação: "+", ".join(unit.get("components") or []))
        else:
            drow("PEDOLOGIA","Classificação de solos",status="N/D",
                 note=dp.get("reason") or "Sem interseção oficial disponível")
        df=self.project.get("soil_fertility") or {}
        fertile=[(unit,x) for unit,recs in (df.get("units") or {}).items()
                 for x in recs if x.get("mean") is not None]
        if fertile:
            for zone,measurement in fertile:
                drow("FERTILIDADE",str(measurement.get("label") or "")+" ["+
                     str(measurement.get("depth_cm") or "?")+" cm]",status="MAPA PREDITIVO",
                     note=str(zone)+": "+format_ptbr(measurement["mean"],2)+" "+
                     str(measurement.get("unit") or "")+"; cobertura "+
                     format_ptbr(measurement.get("coverage_pct"),2)+"%")
        else:
            drow("FERTILIDADE","CTC, pH, CE e textura",status="N/D",
                 note=df.get("reason") or "Sem dados numéricos oficiais processados")
        for item in (dl.get("classes") or []):
            drow("USO DO SOLO",item.get("class_name") or "Classe",status="MAPEADO",
                 note=format_ptbr(item.get("area_ha"),2)+" ha; "+str(item.get("source") or ""))
        # Source-grounded minimum/most-probable/maximum: the central stock is
        # displayed at the midpoint. Unknown uncertainties remain N/D; their
        # omission must not be misrepresented as a property-wide interval.
        from carbon_scenario_envelopes import scenario_envelope
        envelope=scenario_envelope(dn)
        dash.extend([
            ["CENÁRIOS","ESTOQUE MÍNIMO — fontes quantificadas",None,
             envelope["minimum_known_tco2e_ha"],envelope["minimum_known_tc"],
             envelope["minimum_known_tco2e"],"ENVELOPE / N/D",
             "Limites somente quando todas as fontes quantificadas fornecem faixa defensável."],
            ["CENÁRIOS","ESTOQUE MAIS PROVÁVEL — soma conhecida",None,
             envelope["central_known_tco2e_ha"],envelope["known_total_tc"],
             envelope["central_known_tco2e"],"PARCIAL" if not dn.get("complete") else "ESTIMATIVA CENTRAL",
             "Soma conhecida. Não pressupõe estoque nulo nos compartimentos N/D."],
            ["CENÁRIOS","ESTOQUE MÁXIMO — fontes quantificadas",None,
             envelope["maximum_known_tco2e_ha"],envelope["maximum_known_tc"],
             envelope["maximum_known_tco2e"],"ENVELOPE / N/D",
             "Não é IC95% conjunto; desvios da fonte espelhados em torno da estimativa central."],
        ])
        scenario=wb.create_sheet("Cenários e Incertezas")
        setup(scenario,"Enform Verde — Cenários por estrato e compartimento")
        for j,h in enumerate(["Fitofisionomia","Compartimento","Área (ha)",
                              "Mínimo (tCO₂e)","Mais provável (tCO₂e)",
                              "Máximo (tCO₂e)","Status","Tipo de incerteza"],1):
            scenario.cell(3,j,h).value=h
        scenario_rows=[
            [part["physiognomy"],part["compartment"],part["area_ha"],
             part["low_tc"]*44/12 if part["low_tc"] is not None else None,
             part["central_tc"]*44/12,
             part["high_tc"]*44/12 if part["high_tc"] is not None else None,
             part["status"],str(part.get("uncertainty_kind") or "N/D")]
            for part in envelope["rows"]]
        if not scenario_rows:
            scenario_rows=[["N/D","Sem estoque quantificado",None,None,None,None,
                            "N/D","Não inventar limites"]]
        put(scenario,scenario_rows)
        scenario["A2"]="Cenários aritméticos simétricos de limites de fonte; não equivalem a intervalo estatístico conjunto de confiança."
        scenario.merge_cells("A2:H2")
        scenario["A2"].alignment=Alignment(wrap_text=True)
        scenario.auto_filter.ref=f"A3:H{3+len(scenario_rows)}"
        # Display the three carbon-stock scenarios at the TOP of the
        # executive sheet, immediately after AOI area; they must not be hidden
        # below potentially dozens of fertility and land-cover rows.
        dash=dash[:1]+dash[-3:]+dash[1:-3]
        put(dashboard,dash)
        dashboard.auto_filter.ref=f"A3:H{3+len(dash)}"
        dashboard.freeze_panes="C8"
        dashboard.sheet_view.zoomScale=85
        for scenario_row in (5,6,7):
            for cell in dashboard[scenario_row]:
                cell.font=Font(bold=True,color=green)

        # Brazilian number formatting and readable dimensions on ALL worksheets.
        # Wrapped long text is sized by its displayed line count, not clipped
        # into a fixed-height row. Excel column letters may extend beyond H.
        from openpyxl.utils import get_column_letter
        import math as _math
        for sheet in wb.worksheets:
            sheet.sheet_view.showGridLines=False
            col_widths={}
            for record in sheet.iter_rows():
                for cell in record:
                    if cell.value is None:continue
                    if isinstance(cell.value,(int,float)) and not isinstance(cell.value,bool):
                        cell.number_format='#,##0.00'
                        needed=max(14,len(f"{cell.value:,.2f}")+3)
                    else:
                        content=str(cell.value)
                        needed=min(104,max(13,min(62,len(content)+3)))
                    col_widths[cell.column]=max(col_widths.get(cell.column,13),needed)
            for col,width in col_widths.items():
                letter=get_column_letter(col)
                if col>8 and sheet.title in ("Fertilidade do Solo","Modelo Para Campo"):
                    width=max(width,24)
                sheet.column_dimensions[letter].width=min(106,max(14,width+2))
            for record in sheet.iter_rows():
                if record[0].row<=3:continue
                max_lines=1
                for cell in record:
                    if cell.value is None:continue
                    width=sheet.column_dimensions[get_column_letter(cell.column)].width or 18
                    body=str(cell.value)
                    if isinstance(cell.value,(int,float)) and not isinstance(cell.value,bool):
                        body=f"{cell.value:,.2f}"
                    lines=sum(max(1,_math.ceil(len(piece)/max(8,int(width)-4)))
                              for piece in body.split("\n"))
                    max_lines=max(max_lines,lines)
                    cell.alignment=Alignment(vertical="top",wrap_text=True)
                sheet.row_dimensions[record[0].row].height=min(405,max(30,16*max_lines+10))
            sheet.sheet_properties.pageSetUpPr.fitToPage=True
            sheet.page_setup.fitToWidth=1
            sheet.sheet_view.zoomScale=85
        wb.save(p); self.status.set("Excel exportado com sucesso.")

    def save_report(self):
        txt=self.res.get("1.0","end").strip()
        if not txt:return
        p=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Relatório TXT","*.txt")])
        if p:Path(p).write_text(txt+"\n\nFONTES\n"+self.src.get("1.0","end"),encoding="utf-8"); self.status.set("Relatório salvo.")

def module_check():
    """Offline check, run on the COMPILED EXE: new modules are packaged and
    their bundled data resolve under sys._MEIPASS. Writes a JSON summary."""
    out={"version":APP_VERSION}
    import numpy as np, rasterio, geopandas as gpd
    from rasterio.transform import from_origin
    from shapely.geometry import Point, box
    import pronasolos_wcs, soil_intersection_report, crop_model_priority, crop_vigor
    import crop_climate_favorability, crop_forecast_pipeline
    from soil_pronasolos_zonal import mapped_soil_0_100_on_polygon
    from crop_yield_scenario import load_microregion_yields, microregion_of
    tmp=Path(tempfile.mkdtemp(prefix="enform_modcheck_")); px=pronasolos_wcs.PIXEL_DEG; paths={}
    for lid in range(2,7):
        f=tmp/f"h{lid}.tif"
        with rasterio.open(f,"w",driver="GTiff",height=10,width=10,count=1,dtype="float32",crs="EPSG:4326",
                           transform=from_origin(-55.0,-3.0,px,px),nodata=-9999) as d:
            d.write(np.full((10,10),float(lid),dtype="float32"),1)
        paths[lid]=f
    soil=mapped_soil_0_100_on_polygon(gpd.GeoDataFrame(geometry=[box(-55+px,-3-9*px,-55+9*px,-3-px)],crs=4326),paths)
    if abs(soil["0–100 cm"]["tc_ha"]-20.0)>1e-6:raise RuntimeError("interseção exata EPSG:4326 incorreta")
    out["soil_exact_intersection"]="ok"
    # The compiled EXE must include the pre-field modeling engine and stamped SHA.
    from modeled_field_validation import build_pre_field_manifest, field_measurement_rows
    model_check=build_pre_field_manifest({"strata":[],"native_area_ha":0,
        "known_total_tc":None},analysis_id="WINDOWS_MODULE_CHECK")
    if model_check["scientifically_homologated"] or field_measurement_rows(model_check):
        raise RuntimeError("Modelo pré-campo fabricou observações ou homologação")
    out["pre_field_model_contract"]="ok"
    # Verify the three executable research classifiers are importable both in
    # source Python and inside the clean frozen Windows distribution.
    from sar_algorithm_portfolio import ALGORITHMS, FEATURE_SCHEMA, _models
    available=_models()
    if set(available)!=set(ALGORITHMS) or len(FEATURE_SCHEMA)<6:
        raise RuntimeError("SAR experimental algorithm portfolio unavailable")
    out["sar_experimental_algorithms"]={
        "available":sorted(available),"trained_and_locally_validated":False,
        "scope":"trainable only with independent reference samples"}

    try:
        from enform_build_source import SOURCE_SHA
    except ImportError:
        SOURCE_SHA=None
    if getattr(sys,"frozen",False) and not (
            isinstance(SOURCE_SHA,str) and re.fullmatch("[0-9a-fA-F]{40}",SOURCE_SHA)):
        raise RuntimeError("EXE sem identificação do SHA exato dos fontes compilados")
    out["compiled_source_sha"]=SOURCE_SHA
    m=microregion_of(gpd.GeoDataFrame(geometry=[Point(-55.7,-12.5).buffer(.01)],crs=4326))["dominant"]
    y=load_microregion_yields("Soja",m["code"])
    if m["code"]!="51006" or len(y)<10:raise RuntimeError("dados PAM/microrregiões não empacotados")
    out.update(microregion=m["name"],pam_years=len(y))
    from crop_panel_yield_model import load_artifact
    art=load_artifact()
    if not art or "Soja" not in art.get("crops",{}):raise RuntimeError("modelo de produtividade calibrado não empacotado")
    out["yield_panel_model"]={c:{g:round(v["loyo"]["skill_vs_trend"],3) for g,v in d.items()} for c,d in art["crops"].items()}
    # Enforce Python-source / frozen-EXE parity of the INSTALLED SAR model.
    # Import alone is insufficient: resolve the bundled joblib and verify its SHA.
    from sar_landcover_lemplus import load as load_sar_rf, agricultural_year
    from datetime import date as _date
    rf,rf_manifest=load_sar_rf()
    if rf_manifest.get("model_id")!="ENFORM_SAR_BRASIL_RF_V2":
        raise RuntimeError("Modelo SAR instalado nao corresponde ao manifesto esperado")
    months,season=agricultural_year(_date(2026,11,10))
    if season!="2025/2026" or len(months)!=12:
        raise RuntimeError("Janela retrospectiva do modelo SAR divergente")
    out["sar_model"]={"model_id":rf_manifest["model_id"],
                      "sha256":rf_manifest["sha256"],"season":season,
                      "months":len(months)}
    from crop_water_balance_yield import sowing_dates, _kc
    out["crop_water"]={"soy_sowing_dates":str(sowing_dates("Soja",-12.5,2025)),
                       "soy_kc_day_50":round(float(_kc("Soja",50)),6)}
    (Path(tempfile.gettempdir())/"enform_verde_module_check.json").write_text(json.dumps(out,ensure_ascii=False),encoding="utf-8")
    return out

def _valid_raster_pixel_count(array):
    """Count unmasked pixels, including MaskedArray's scalar no-mask case."""
    return int(np.ma.count(array))


def network_check(attempts=3):
    """Compiled-EXE LIVE check (V87.37): real CBERS-4A pixels and real Sentinel-1
    RTC VV/VH pixels must be readable over a Brazilian AOI (Sinop) with TLS
    verification ON. Writes enform_verde_network_check.json; raises on failure."""
    import time
    import geopandas as gpd
    from shapely.geometry import box, mapping
    out={"version":APP_VERSION,"tls":tls_setup.configure()}
    aoi=gpd.GeoDataFrame(geometry=[box(-55.21,-11.89,-55.17,-11.855)],crs=4326)  # Sinop-MT
    def retry(fn):
        last=None
        for k in range(attempts):
            try:return fn()
            except Exception as exc:
                last=exc;time.sleep(3*(k+1))
        raise last
    try:
        p=retry(lambda:cbers4a_wfi_preview(aoi,out_w=320,out_h=200))
        out["cbers4a"]={"status":"OK","provider":p.get("provider"),"date_range":p.get("date_range") or p.get("datetime")}
    except Exception as exc:
        out["cbers4a"]={"status":"ERRO","reason":type(exc).__name__+": "+str(exc)[:300]}
    # A real Sentinel-2 image is sufficient if CBERS-4A is inaccessible.
    out["optical"]={"status":"OK","provider":"CBERS-4A/WFI"} if out["cbers4a"]["status"]=="OK" else {"status":"ERRO"}
    if out["optical"]["status"]!="OK":
        for label,fn in (("Sentinel-2 Earth Search",lambda:sentinel2_earthsearch_preview(aoi,out_w=320,out_h=200)),
                         ("Sentinel-2 MPC",lambda:sentinel2_preview(aoi))):
            try:
                optical=retry(fn)
                out["optical"]={"status":"OK","provider":label,
                                "acquisition_utc":optical.get("datetime")}
                break
            except Exception as exc:
                out["optical"].setdefault("failed_providers",[]).append(
                    label+": "+type(exc).__name__+": "+str(exc)[:180])
    try:
        from datetime import timedelta
        from sentinel1_sources import search_sentinel1_sources
        from sentinel1_mpc import get_runtime_sas_token, sign_asset_href
        from recent_sar_landcover import _open_signed_cog_via_https
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_geom
        from shapely.geometry import shape
        now=datetime.now(timezone.utc)
        found=retry(lambda:search_sentinel1_sources(mapping(aoi.geometry.iloc[0]),start_utc=now-timedelta(days=40),end_utc=now))
        scenes=[s for s in found.get("scenes",[]) if {"vv","vh"}<=set(s.get("assets") or {})]
        if not scenes:raise RuntimeError("catálogos sem cena VV/VH em 40 dias")
        s=scenes[0]
        def read():
            vals={};https_local={}
            for pol in ("vv","vh"):
                href=s["assets"][pol]["href"]
                if s.get("provider","MPC")=="MPC":
                    href=sign_asset_href(href)
                with rasterio.Env(**tls_setup.gdal_env()):
                    with rasterio.open(href) as src:
                        g=shape(transform_geom("EPSG:4326",src.crs,mapping(aoi.geometry.iloc[0])))
                        w=from_bounds(*g.bounds,transform=src.transform).round_offsets().round_lengths()
                        a=src.read(1,window=w,masked=True)
                        vals[pol]=_valid_raster_pixel_count(a)
                if s.get("provider","MPC")=="MPC":
                    # Exercise the independent Requests/TLS/local-COG path in
                    # the compiled Windows executable; GDAL-only success is
                    # not evidence that the recovery route works.
                    with _open_signed_cog_via_https(
                            s["assets"][pol]["href"],rasterio=rasterio,
                            token_fn=get_runtime_sas_token,item_id=s.get("id"),
                            asset_key=pol,geometry=mapping(aoi.geometry.iloc[0]),
                            collection=s.get("collection","sentinel-1-rtc")) as src:
                        geom=shape(transform_geom(
                            "EPSG:4326",src.crs,mapping(aoi.geometry.iloc[0])))
                        w=from_bounds(*geom.bounds,transform=src.transform)
                        a=src.read(1,window=w,masked=True)
                        https_local[pol]=_valid_raster_pixel_count(a)
            return {"gdal":vals,"https_local":https_local}
        px=retry(read)
        if min(px["gdal"].values())<100:raise RuntimeError("menos de 100 pixels SAR válidos via GDAL: "+str(px["gdal"]))
        if s.get("provider","MPC")=="MPC" and min(px["https_local"].values())<100:
            raise RuntimeError("menos de 100 pixels SAR válidos via HTTPS local: "+str(px["https_local"]))
        out["sentinel1"]={"status":"OK","scene_id":s.get("id"),"acquisition_utc":s.get("acquisition_utc"),
                          "provider":s.get("provider","MPC"),"valid_pixels":px["gdal"],
                          "https_local_valid_pixels":px["https_local"]}
    except Exception as exc:
        out["sentinel1"]={"status":"ERRO","reason":type(exc).__name__+": "+str(exc)[:300]}
    (Path(tempfile.gettempdir())/"enform_verde_network_check.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    bad=[k for k in ("optical","sentinel1") if out[k]["status"]!="OK"]
    if bad:raise RuntimeError("leitura real de pixels falhou: "+", ".join(bad))
    return out

def visual_check():
    """Compiled-EXE check: the approved shell (header, action bar, navigation,
    tabs, footer, styles) matches the packaged visual baseline."""
    import ui_visual_standard as uvs
    app=App()
    try:
        app.update(); shell=uvs._normalise({"static":{},"shell":uvs.shell_snapshot(app)})["shell"]
    finally:
        app.destroy()
    baseline=json.loads(uvs.packaged_baseline().read_text(encoding="utf-8"))["shell"]
    d=uvs.diff(baseline,shell)
    (Path(tempfile.gettempdir())/"enform_verde_visual_check.txt").write_text("\n".join(d) or "PADRAO_VISUAL_OK",encoding="utf-8")
    if d:raise RuntimeError("padrão visual alterado: "+"; ".join(d[:5]))

if __name__=="__main__":
    if "--network-check" in sys.argv:
        try:network_check()
        except Exception:
            (Path(tempfile.gettempdir())/"enform_verde_network_check_error.txt").write_text(traceback.format_exc(),encoding="utf-8")
            sys.exit(1)
    elif "--visual-check" in sys.argv:
        try:visual_check()
        except Exception:
            (Path(tempfile.gettempdir())/"enform_verde_visual_check_error.txt").write_text(traceback.format_exc(),encoding="utf-8")
            sys.exit(1)
    elif "--module-check" in sys.argv:
        try:module_check()
        except Exception:
            (Path(tempfile.gettempdir())/"enform_verde_module_check_error.txt").write_text(traceback.format_exc(),encoding="utf-8")
            sys.exit(1)
    elif "--acceptance-test" in sys.argv:
        try:acceptance_test(sys.argv[sys.argv.index("--acceptance-test")+1])
        except Exception:
            (Path(tempfile.gettempdir())/"enform_verde_acceptance_error.txt").write_text(traceback.format_exc(),encoding="utf-8")
            sys.exit(1)
    elif "--ui-smoke" in sys.argv:ui_smoke_test()
    elif "--self-test" in sys.argv:self_test()
    else:App().mainloop()
