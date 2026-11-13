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

APP_VERSION="3.26.25-PRECAMPO-EXPERIMENTAL"
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
                    valid=np.isfinite(stack).all(axis=2)&(stack>0).any(axis=2)
                    if valid.sum()<max(80,stack.shape[0]*stack.shape[1]//200):
                        raise RuntimeError("cena sem pixels RGB válidos suficientes")
                    target_transform=tr*__import__("rasterio").Affine.scale(
                        float(window.width)/out_width,float(window.height)/out_height)
                    aoi_geom=transform_geom("EPSG:4326",crs,geom)
                    aoi_mask=geometry_mask([aoi_geom],out_shape=(out_height,out_width),
                                           transform=target_transform,invert=True)
                    aoi_pixel_count=max(1,int(aoi_mask.sum()))
                    aoi_coverage=float((valid&aoi_mask).sum()/aoi_pixel_count)
                    if aoi_coverage<0.95:
                        raise RuntimeError("cena não cobre 95% dos pixels da AOI")
                    pixels=stack[valid]
                    hi=float(np.percentile(pixels,99))
                    if hi<=0 or not np.isfinite(hi):raise RuntimeError("radiometria RGB inválida")
                    final=np.clip(np.nan_to_num(stack,nan=0.0)/hi*255,0,255).astype(np.uint8)
                    image=Image.fromarray(final,"RGB")
                    polygons=[]
                    for shape0 in g.geometry:
                        polys=list(shape0.geoms) if shape0.geom_type=="MultiPolygon" else ([shape0] if shape0.geom_type=="Polygon" else [])
                        for poly in polys:
                            coordinates=list(poly.exterior.coords)
                            xx,yy=transform("EPSG:4326",crs,[v[0] for v in coordinates],[v[1] for v in coordinates])
                            pts=[]
                            for px,py in zip(xx,yy):
                                col,row=(~tr)*(px,py)
                                pts.extend([float(col)*out_width/window.width,float(row)*out_height/window.height])
                            if len(pts)>=6:polygons.append(pts)
                    # RGB and polygon must be scaled by the same factor.
                    fx=float(out_w)/out_width;fy=float(out_h)/out_height
                    scaled_polygons=[[p*(fx if k%2==0 else fy) for k,p in enumerate(poly)] for poly in polygons]
                    return {"image":image.resize((int(out_w),int(out_h)),Image.Resampling.LANCZOS),
                            "polygons":scaled_polygons,"scene_id":item.get("id"),
                            "datetime":dt,"cloud_cover":cloud,
                            "provider":"Sentinel-2 L2A / Earth Search AWS public COGs",
                            "attempted_scenes":len({e.split(":",1)[0] for e in errors})+1,
                            "transport_attempts_for_scene":strategy+1,
                            "transport_strategy":("DEFAULT_MULTIRANGE" if strategy==0 else
                                                  "SERIAL_HTTP11" if strategy==1 else "SERIAL_NO_MULTIPLEX_HTTP11"),
                            "aoi_coverage_fraction":aoi_coverage}
        except (UnicodeError,OSError,RuntimeError,ValueError,rasterio.errors.RasterioError) as exc:
            errors.append(str(item.get("id",""))+": "+type(exc).__name__+": "+str(exc)[:100])
    raise RuntimeError("Nenhuma das "+str(len(pool))+" cenas Sentinel-2 forneceu RGB real. "+
                       "Erros: "+"; ".join(errors)[:480])


def cbers4a_wfi_preview(gdf,out_w=1000,out_h=560,extent_factor=1.36):
    """True-color CBERS-4A/WFI background from official INPE surface-reflectance COGs.

    The map is visual context only. RGB comes from BAND15/BAND14/BAND13 and
    CMASK=127 is treated as clear; cloud/no-data pixels are left for a newer
    intersecting scene to fill. We never substitute the IBGE cartographic raster.
    """
    import rasterio
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.transform import from_bounds
    from rasterio.windows import from_bounds as window_from_bounds, Window
    from rasterio.features import geometry_mask
    from datetime import datetime, timezone
    g=gdf.to_crs(4326).copy()
    minx,miny,maxx,maxy=map(float,g.total_bounds)
    dx=max(maxx-minx,1e-8);dy=max(maxy-miny,1e-8)
    cx=(minx+maxx)/2;cy=(miny+maxy)/2
    factor=max(0.30,min(8.0,float(extent_factor)))
    west,east=cx-dx*factor/2,cx+dx*factor/2
    south,north=cy-dy*factor/2,cy+dy*factor/2
    ratio=max(1.0,float(out_w))/max(1.0,float(out_h)); coslat=max(.25,math.cos(math.radians(cy)))
    if (east-west)*coslat/(north-south)<ratio:
        span=(north-south)*ratio/coslat;west,east=cx-span/2,cx+span/2
    else:
        span=(east-west)*coslat/ratio;south,north=cy-span/2,cy+span/2
    width=max(320,min(1600,int(out_w)));height=max(240,min(1200,int(out_h)))
    target_transform=from_bounds(west,south,east,north,width,height)
    aoi_mask=geometry_mask(list(g.geometry),out_shape=(height,width),transform=target_transform,invert=True)
    aoi_pixels=max(1,int(aoi_mask.sum()))
    geom=g.geometry.union_all().__geo_interface__
    body={"collections":["CB4A-WFI-L4-SR-1"],"intersects":geom,"limit":60,
          "sortby":[{"field":"properties.datetime","direction":"desc"}]}
    import time
    response=None;search_error=None
    for attempt in range(4):
        try:
            items=_fetch_stac_features_paged("https://data.inpe.br/bdc/stac/v1/search",
                                             body,timeout=(8,45),max_pages=20)
            break
        except requests.exceptions.RequestException as exc:
            search_error=exc
            status=getattr(getattr(exc,"response",None),"status_code",None)
            retryable=(status in (429,500,502,503,504) or isinstance(
                exc,(requests.exceptions.Timeout,requests.exceptions.ConnectionError)))
            if not retryable or attempt>=3:raise RuntimeError(
                "Busca STAC CBERS-4A/WFI indisponível após tentativas: "+type(exc).__name__) from None
            time.sleep(1.5*(attempt+1))
    if not items:raise RuntimeError("Catálogo INPE não retornou cenas CBERS-4A/WFI para a AOI")
    # Sort by acquisition date; newest clear pixels win. Older archived scenes
    # may fill geographic gaps, and the date range is reported to the user.
    scenes=[]
    for item in items:
        props=item.get("properties") or {};stamp=str(props.get("datetime") or "")
        try:
            dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
            scenes.append((dt,item))
        except (ValueError,OverflowError):continue
    if not scenes:raise RuntimeError("Catálogo INPE não forneceu datas de aquisição CBERS-4A/WFI válidas")
    scenes.sort(key=lambda pair:pair[0],reverse=True)
    rgb_clear=np.full((height,width,3),np.nan,dtype=np.float32)
    rgb_observed=np.full((height,width,3),np.nan,dtype=np.float32)
    source_dates=[];scene_ids=[];errors=[]

    def read_cog_window(href,categorical=False):
        """Read only the map viewport from a remote COG, never the full scene."""
        destination=np.zeros((height,width),dtype=np.uint8) if categorical else np.full((height,width),np.nan,dtype=np.float32)
        with rasterio.open(href) as src:
            if not src.crs:raise RuntimeError("COG sem CRS")
            bounds=transform_bounds("EPSG:4326",src.crs,west,south,east,north,densify_pts=21)
            win=window_from_bounds(*bounds,transform=src.transform).round_offsets().round_lengths()
            try:win=win.intersection(Window(0,0,src.width,src.height))
            except rasterio.errors.WindowError:return destination
            if win.width<2 or win.height<2:return destination
            ow=min(1600,max(100,int(win.width)));oh=min(1200,max(100,int(win.height)))
            method=Resampling.nearest if categorical else Resampling.bilinear
            raw=src.read(1,window=win,out_shape=(oh,ow),masked=True,resampling=method)
            if categorical:arr=raw.filled(0).astype(np.uint8,copy=False)
            else:arr=raw.astype(np.float32).filled(np.nan)
            src_transform=src.window_transform(win)*rasterio.Affine.scale(float(win.width)/ow,float(win.height)/oh)
            reproject(arr,destination,src_transform=src_transform,src_crs=src.crs,
                      src_nodata=(0 if categorical else np.nan),dst_transform=target_transform,
                      dst_crs="EPSG:4326",dst_nodata=(0 if categorical else np.nan),resampling=method)
        return destination

    attempts_by_scene={}
    successful_scene_ids=set()
    transport_counts={"DEFAULT_MULTIRANGE":0,"SERIAL_HTTP11":0,"SERIAL_NO_MULTIPLEX_HTTP11":0}
    expanded_scenes=[(dt,item,strategy) for dt,item in scenes[:120]
                     for strategy in range(3)]
    for dt,item,transport_strategy in expanded_scenes:
        scene_id=str(item.get("id",""))
        if scene_id in successful_scene_ids:continue
        attempts_by_scene[scene_id]=attempts_by_scene.get(scene_id,0)+1
        transport_counts[("DEFAULT_MULTIRANGE","SERIAL_HTTP11","SERIAL_NO_MULTIPLEX_HTTP11")[transport_strategy]]+=1
        assets=item.get("assets") or {}
        keys=("BAND15","BAND14","BAND13")
        if not all((assets.get(k) or {}).get("href") for k in keys) or not (assets.get("CMASK") or {}).get("href"):
            errors.append(str(item.get("id",""))+" sem RGB/CMASK");continue
        scene=np.full((height,width,3),np.nan,dtype=np.float32)
        try:
            env={"GDAL_HTTP_TIMEOUT":"40","GDAL_HTTP_MAX_RETRY":"2",
                 "GDAL_HTTP_MULTIRANGE":"YES",
                 "GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR",**tls_setup.gdal_env()}
            if transport_strategy==1:
                env.update({"GDAL_HTTP_MULTIRANGE":"SERIAL","GDAL_HTTP_MERGE_CONSECUTIVE_RANGES":"NO",
                            "CPL_VSIL_CURL_USE_HEAD":"NO","GDAL_HTTP_VERSION":"1.1"})
            elif transport_strategy==2:
                env.update({"GDAL_HTTP_MULTIRANGE":"SERIAL","GDAL_HTTP_MULTIPLEX":"NO",
                            "CPL_VSIL_CURL_USE_HEAD":"NO","GDAL_HTTP_VERSION":"1.1"})
            with rasterio.Env(**env):
                mask=read_cog_window(assets["CMASK"]["href"],categorical=True)
                # Current INPE catalogue collection defines CMASK: 127 clear,
                # 255 cloud, 0 no data. Pixels outside clear are never blended.
                clear=mask==127
                for band_idx,key in enumerate(keys):
                    band=read_cog_window(assets[key]["href"])
                    scene[:,:,band_idx]=band
            observed=np.isfinite(scene).all(axis=2) & (scene>0).any(axis=2) & (mask!=0)
            valid=clear & observed
            take_observed=observed & ~np.isfinite(rgb_observed).all(axis=2)
            take_clear=valid & ~np.isfinite(rgb_clear).all(axis=2)
            if take_observed.any():rgb_observed[take_observed]=scene[take_observed]
            if take_clear.any():rgb_clear[take_clear]=scene[take_clear]
            if take_observed.any() or take_clear.any():
                scene_ids.append(scene_id);successful_scene_ids.add(scene_id);source_dates.append(dt.date().isoformat())
            covered=int((np.isfinite(rgb_clear).all(axis=2)&aoi_mask).sum())
            observed_covered=int((np.isfinite(rgb_observed).all(axis=2)&aoi_mask).sum())
            if covered/aoi_pixels>=0.98 or observed_covered/aoi_pixels>=0.98:break
        except Exception as exc:
            try: detail=str(exc)
            except Exception: detail="mensagem da exceção não decodificável"
            errors.append(scene_id+" transporte="+str(transport_strategy+1)+": "+type(exc).__name__+": "+detail.encode("utf-8","replace").decode("utf-8")[:90])
    rgb=rgb_clear.copy()
    holes=~np.isfinite(rgb).all(axis=2)
    observed=np.isfinite(rgb_observed).all(axis=2)&(rgb_observed>0).any(axis=2)
    # Background imagery may include clouds if no clear pixel exists; keep it
    # explicitly labelled instead of silently showing an unrelated cartographic map.
    cloud_fallback_used=bool((holes&observed).any())
    rgb[holes&observed]=rgb_observed[holes&observed]
    valid=np.isfinite(rgb).all(axis=2)&(rgb>0).any(axis=2)
    if valid.sum()<max(80,height*width//200):
        raise RuntimeError("CBERS-4A/WFI sem pixels reais RGB suficientes na AOI. "+"; ".join(errors[:3]))
    aoi_coverage=float((valid&aoi_mask).sum()/aoi_pixels)
    if aoi_coverage<0.95:
        raise RuntimeError("CBERS-4A/WFI não cobre 95% dos pixels da AOI; cobertura="+
                           format(aoi_coverage,".3f")+". "+"; ".join(errors[:3]))
    hi=float(np.percentile(rgb[valid],99))
    if not np.isfinite(hi) or hi<=0:raise RuntimeError("Reflectância CBERS-4A inválida")
    image=Image.fromarray(np.clip(np.nan_to_num(rgb,nan=0.0)/hi*255,0,255).astype(np.uint8),"RGB")
    from PIL import ImageDraw
    draw=ImageDraw.Draw(image,"RGBA")
    for shape in g.geometry:
        geoms=list(shape.geoms) if shape.geom_type=="MultiPolygon" else ([shape] if shape.geom_type=="Polygon" else [])
        for poly in geoms:
            pts=[((x-west)/(east-west)*width,(north-y)/(north-south)*height)
                 for x,y in _xy_coords(poly.exterior.coords)]
            if len(pts)>=4:draw.polygon(pts,fill=(255,138,0,32),outline=(255,138,0,255));draw.line(pts,width=3,fill=(255,138,0,255))
    return {"image":image.resize((int(out_w),int(out_h)),Image.Resampling.LANCZOS),
            "datetime":max(source_dates),"date_range":[min(source_dates),max(source_dates)],"scene_ids":scene_ids,
            "provider":"CBERS-4A/WFI L4-SR / INPE STAC (COG, composição RGB de pixels claros)",
            "resolution_m":55,"pixel_count":int(valid.sum()),"aoi_coverage_fraction":aoi_coverage,
            "transport_attempt_count":sum(attempts_by_scene.values()),
            "transport_strategy_counts":transport_counts,
            "cloud_pixels_included":cloud_fallback_used,"polygons":[]}


def _satellite_preview_cache_paths(gdf,extent_factor,out_w,out_h):
    """Stable per-AOI/viewport cache; never depends on the process CWD."""
    import hashlib
    geom=gdf.to_crs(4326).geometry.union_all()
    token=hashlib.sha256(geom.wkb+f"|{float(extent_factor):.4f}|{int(out_w)}x{int(out_h)}".encode("ascii")).hexdigest()
    root=Path(os.environ.get("LOCALAPPDATA",Path.home()))/"EnformVerde"/"SatelliteCache"
    return root/(token+".png"),root/(token+".json")


def _store_satellite_preview_cache(gdf,extent_factor,out_w,out_h,image,polygons,provider,credit):
    try:
        image_path,meta_path=_satellite_preview_cache_paths(gdf,extent_factor,out_w,out_h)
        image_path.parent.mkdir(parents=True,exist_ok=True)
        image_tmp=image_path.with_suffix(".tmp.png");meta_tmp=meta_path.with_suffix(".tmp")
        image.save(image_tmp,format="PNG")
        meta={"provider":str(provider),"credit":str(credit),"stored_utc":datetime.now(timezone.utc).isoformat(),
              "polygons":polygons,"width":int(out_w),"height":int(out_h)}
        meta_tmp.write_text(json.dumps(meta,ensure_ascii=False),encoding="utf-8")
        image_tmp.replace(image_path);meta_tmp.replace(meta_path)
    except Exception:
        # Cache is only a resilience aid; a write failure cannot block display.
        return


def _read_satellite_preview_cache(gdf,extent_factor,out_w,out_h):
    try:
        image_path,meta_path=_satellite_preview_cache_paths(gdf,extent_factor,out_w,out_h)
        meta=json.loads(meta_path.read_text(encoding="utf-8"))
        with Image.open(image_path) as cached:image=cached.convert("RGB").copy()
        return image,meta
    except Exception:
        return None


def nasa_gibs_preview(gdf,out_w=1000,out_h=560,extent_factor=1.36):
    """Keyless public NASA GIBS VIIRS true-color preview; visual context only."""
    from datetime import timedelta
    from PIL import ImageDraw
    g=gdf.to_crs(4326).copy()
    minx,miny,maxx,maxy=map(float,g.total_bounds)
    dx=max(maxx-minx,1e-8); dy=max(maxy-miny,1e-8)
    cx=(minx+maxx)/2; cy=(miny+maxy)/2
    factor=max(0.30,min(8.0,float(extent_factor)))
    west,east=cx-dx*factor/2,cx+dx*factor/2
    south,north=cy-dy*factor/2,cy+dy*factor/2
    # Keep the requested image proportions while accounting for longitude scale.
    ratio=max(0.1,float(out_w))/max(1.0,float(out_h))
    coslat=max(0.25,math.cos(math.radians(cy)))
    lon_span=max(east-west,1e-8); lat_span=max(north-south,1e-8)
    if lon_span*coslat/lat_span < ratio:
        lon_span=lat_span*ratio/coslat
        west,east=cx-lon_span/2,cx+lon_span/2
    else:
        lat_span=lon_span*coslat/ratio
        south,north=cy-lat_span/2,cy+lat_span/2
    width=max(320,min(1600,int(out_w))); height=max(240,min(1200,int(out_h)))
    endpoint="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
    today=datetime.now(timezone.utc).date()
    errors=[]
    for days_back in range(1,8):
        day=(today-timedelta(days=days_back)).isoformat()
        params={"SERVICE":"WMS","VERSION":"1.1.1","REQUEST":"GetMap",
                "LAYERS":"VIIRS_SNPP_CorrectedReflectance_TrueColor","STYLES":"",
                "FORMAT":"image/jpeg","TRANSPARENT":"FALSE","SRS":"EPSG:4326",
                "BBOX":f"{west:.8f},{south:.8f},{east:.8f},{north:.8f}",
                "WIDTH":str(width),"HEIGHT":str(height),"TIME":day}
        try:
            rr=requests.get(endpoint,params=params,timeout=(8,30))
            rr.raise_for_status()
            if "image" not in (rr.headers.get("Content-Type") or "").lower():
                raise RuntimeError("NASA GIBS não retornou imagem")
            im=Image.open(io.BytesIO(rr.content)).convert("RGB")
            d=ImageDraw.Draw(im,"RGBA"); iw,ih=im.size
            def px(lon,lat):
                return ((float(lon)-west)/max(east-west,1e-12)*iw,
                        (north-float(lat))/max(north-south,1e-12)*ih)
            for geom in g.geometry:
                geoms=list(geom.geoms) if geom.geom_type=="MultiPolygon" else ([geom] if geom.geom_type=="Polygon" else [])
                for poly in geoms:
                    pts=[px(lon,lat) for lon,lat in _xy_coords(poly.exterior.coords)]
                    if len(pts)>=4:
                        d.polygon(pts,fill=(255,138,0,32),outline=(255,138,0,255))
                        d.line(pts,width=max(2,round(iw/500)),fill=(255,138,0,255),joint="curve")
            return {"image":im.resize((int(out_w),int(out_h),),Image.Resampling.LANCZOS),
                    "datetime":day,"provider":"NASA GIBS / VIIRS SNPP true color"}
        except Exception as exc:
            errors.append(f"{day}: {type(exc).__name__}: {exc}")
    raise RuntimeError("NASA GIBS sem imagem disponível nos últimos 7 dias: "+" | ".join(errors[-2:]))

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Enform Verde"); screen_w=self.winfo_screenwidth(); screen_h=self.winfo_screenheight(); win_w=max(1100,min(1713,screen_w-48)); win_h=max(620,min(918,screen_h-88)); self.geometry(f"{win_w}x{win_h}"); self.minsize(min(1024,win_w),min(600,win_h))
        self.inv=None; self.gdf=None; self.soil_raster=None; self.project={"version":APP_VERSION}; self.active_source=None; self.active_input_id=None; self._analysis_running=False; self._analysis_generation=0; self._analysis_queue=queue.Queue(); self._ibge_queue=queue.Queue(); self._ibge_generation=0; self._ibge_pending=False; self._pending_execute=False; self._map_generation=0; self._map_refresh_job=None; self._map_queue=queue.Queue(); self._weather_query_generation=0; self._crop_monitoring_base_report=""
        # Seed the user's confirmed token issuance date (08/11/2026) only
        # when no newer issuance/renewal record exists.
        try:
            from esa_maap_token_renewal import initialize_current_token_date
            initialize_current_token_date()
        except (OSError,ValueError):
            pass  # Filesystem failures must never prevent the GUI opening.
        self._style(); self._ui(); self.bind("<Return>",self.execute)
        self.after(1600,self._check_maap_token_renewal)
    def _style(self):
        s=ttk.Style(self)
        try:s.theme_use("vista")
        except:pass
        s.configure(".",font=("Segoe UI",10),foreground=TEXT)
        s.configure("Title.TLabel",font=("Segoe UI",20,"bold"),foreground=ORANGE)
        s.configure("H.TLabel",font=("Segoe UI",12,"bold"),foreground=FOREST)
        s.configure("Run.TButton",font=("Segoe UI",10,"bold"),padding=10)
        s.configure("TButton",padding=7)
    def _ui(self):
        # Professional dashboard shell based on the approved Enform Verde reference.
        root=ttk.Frame(self); root.pack(fill="both",expand=True)
        base=app_resource(".").resolve()

        # Approved high-resolution Enform mask; render once, preserve aspect ratio, add no text overlays.
        header_h=210
        header=tk.Canvas(root,height=header_h,bg="#063D26",highlightthickness=0); header.pack(fill="x",side="top")
        visual=base/"enform_header.png"
        self.header_source=Image.open(visual).convert("RGB") if visual.exists() else None
        def render_header(event=None):
            w=max(1,int(event.width if event else header.winfo_width() or 1400)); h=max(1,int(event.height if event else header_h))
            header.delete("all")
            if self.header_source is None:
                return
            # Aspect ratio is preserved; the whole approved mask stays visible at every window size.
            scale=min(w/self.header_source.width,h/self.header_source.height)
            iw=max(1,round(self.header_source.width*scale)); ih=max(1,round(self.header_source.height*scale))
            im=self.header_source.resize((iw,ih),Image.Resampling.LANCZOS)
            self.header_photo=ImageTk.PhotoImage(im)
            header.create_image((w-iw)//2,(h-ih)//2,image=self.header_photo,anchor="nw")
        header.bind("<Configure>",render_header); render_header()

        # Global action bar: EXECUTAR ANÁLISE must remain visible regardless of selected section.
        action=ttk.Frame(root,padding=(305,12,32,10)); action.pack(fill="x",side="top")
        ttk.Label(action,text="Análise de carbono",style="Title.TLabel").pack(side="left")
        ttk.Button(action,text="Salvar relatório",command=self.save_report).pack(side="right",padx=(8,0))
        ttk.Button(action,text="Exportar Excel",command=self.export_excel).pack(side="right",padx=(8,0))
        ttk.Button(action,text="APAGAR PESQUISA",command=self.clear_research).pack(side="right",padx=(8,0))
        self.global_execute_btn=ttk.Button(action,text="EXECUTAR ANÁLISE",command=self.execute,style="Run.TButton")
        self.global_execute_btn.pack(side="right",padx=(8,0))

        body=ttk.Frame(root); body.pack(fill="both",expand=True)
        nav=tk.Frame(body,width=288,bg="#F6F8F8",highlightbackground="#D8E0E0",highlightthickness=1)
        nav.pack(side="left",fill="y"); nav.pack_propagate(False)
        main=ttk.Frame(body,padding=(16,8,32,6)); main.pack(side="left",fill="both",expand=True)

        self.nb=ttk.Notebook(main); self.nb.pack(fill="both",expand=True)
        self.tabs=[]
        for n in ["Propriedade (CAR)","Mapas e limites","Carregar produtos SAR / AGB","Carbono — formações nativas","Base Científica e Modelos","Monitoramento — áreas cultivadas"]:
            f=ttk.Frame(self.nb,padding=14); self.nb.add(f,text=n); self.tabs.append(f)

        nav_items=[
          ("⌂   Início",0),("▣   Propriedade (CAR)",0),("◫   Mapas e limites",1),
          ("◈   Fitofisionomia (IBGE)",1),("◆   Carregar produtos\n     SAR / AGB",2),
          ("◉   Biomassa Aérea (AGB)",3),("♨   Carbono no Solo",3),
          ("●   Carbono Total",3),("▤   Resultados e Relatório",3),
          ("🌱   Monitoramento de\n     áreas cultivadas",5),("⚙   Configurações",2),("▥   Base Científica e\n     Modelos",4),("ⓘ   Sobre",4)]
        self.nav_buttons=[]
        for label,idx in nav_items:
            btn=tk.Button(nav,text=label,anchor="w",justify="left",relief="flat",bd=0,
                          bg="#F6F8F8",fg="#233B49",activebackground="#E5F0EB",
                          font=("Segoe UI",10),padx=20,pady=11,
                          command=lambda i=idx:self.nb.select(i))
            btn.pack(fill="x",pady=0); self.nav_buttons.append((btn,idx))
        def mark_tab(event=None):
            cur=self.nb.index(self.nb.select())
            for btn,idx in self.nav_buttons:
                if idx==cur:
                    btn.configure(bg="#08733F",fg="white",font=("Segoe UI",10,"bold"))
                else:
                    btn.configure(bg="#F6F8F8",fg="#233B49",font=("Segoe UI",10))
        self.nb.bind("<<NotebookTabChanged>>",mark_tab)

        self._project(); self._spatial(); self._remote(); self._results(); self._sources(); self._cultivated_results()
        mark_tab()
        footer=ttk.Frame(root,padding=(14,4)); footer.pack(fill="x",side="bottom")
        ttk.Label(footer,text="v"+APP_VERSION).pack(side="left")
        self.status=tk.StringVar(value="Pronto. Informe o CAR ou carregue o vetor da propriedade.")
        ttk.Label(footer,textvariable=self.status,anchor="center").pack(side="left",fill="x",expand=True)
        ttk.Label(footer,text="Sistema de Estimativa de Estoques de Carbono em Vegetação Nativa").pack(side="right")

    def _project(self):
        f=self.tabs[0]; ttk.Label(f,text="Abrir análise",style="H.TLabel").grid(row=0,column=0,columnspan=4,sticky="w")
        self.name=tk.StringVar(value="Projeto Enform Verde"); self.car=tk.StringVar(); self.ccir=tk.StringVar()
        self.biome=tk.StringVar(value=""); self.phys=tk.StringVar(value="")
        fields=[("Projeto",self.name),("CAR / SICAR",self.car),("CCIR — código INCRA/SNCR (13 dígitos)",self.ccir)]
        for i,(lab,var) in enumerate(fields,1):
            ttk.Label(f,text=lab).grid(row=i,column=0,sticky="w",pady=8)
            ttk.Entry(f,textvariable=var,width=62).grid(row=i,column=1,sticky="ew",padx=10)
        ttk.Label(f,text="A consulta CAR/SICAR ou CCIR/SIGEF ocorre automaticamente ao pressionar EXECUTAR ANÁLISE.",foreground="#52645E",wraplength=900).grid(row=4,column=0,columnspan=3,sticky="w",pady=(12,4))
        ttk.Button(f,text="CARREGAR ARQUIVO VETORIAL",command=self.pick_vector,style="Run.TButton").grid(row=5,column=1,sticky="w",pady=10,padx=10)
        ttk.Label(f,text="KML • KMZ • SHP • GeoJSON • GPKG",foreground="#666").grid(row=5,column=2,sticky="w")
        self.vector_status=tk.StringVar(value="Nenhum arquivo vetorial carregado.")
        ttk.Label(f,textvariable=self.vector_status,foreground="#155D43",wraplength=900).grid(row=6,column=1,columnspan=3,sticky="w",padx=10,pady=(2,8))
        f.columnconfigure(1,weight=1)

    def _spatial(self):
        host=self.tabs[1]
        tab_canvas=tk.Canvas(host,bg="#F4F6F5",highlightthickness=0)
        tab_v=ttk.Scrollbar(host,orient="vertical",command=tab_canvas.yview)
        tab_canvas.configure(yscrollcommand=tab_v.set)
        tab_canvas.pack(side="left",fill="both",expand=True); tab_v.pack(side="right",fill="y")
        f=ttk.Frame(tab_canvas,padding=(0,0,10,10))
        win=tab_canvas.create_window((0,0),window=f,anchor="nw")
        def sync_scroll(event=None):
            tab_canvas.configure(scrollregion=tab_canvas.bbox("all"))
            tab_canvas.itemconfigure(win,width=max(700,tab_canvas.winfo_width()))
        f.bind("<Configure>",sync_scroll); tab_canvas.bind("<Configure>",sync_scroll)

        ttk.Label(f,text="Perímetro, diagnóstico e solo",style="H.TLabel").pack(anchor="w")
        row=ttk.Frame(f); row.pack(fill="x",pady=8)
        ttk.Button(row,text="Baixar raster COS 0–30 cm (auxiliar)",command=self.auto_soil).pack(side="left")
        ttk.Button(row,text="Carregar GeoTIFF de COS",command=self.pick_soil).pack(side="left",padx=8)
        ttk.Button(row,text="VISUALIZAR SATÉLITE + POLÍGONO",command=self.show_google_map,style="Run.TButton").pack(side="left",padx=8)
        ttk.Button(row,text="−",width=3,command=self.map_zoom_out).pack(side="left",padx=(12,2))
        ttk.Button(row,text="+",width=3,command=self.map_zoom_in).pack(side="left",padx=2)
        ttk.Button(row,text="AJUSTAR AOI",command=self.map_zoom_fit).pack(side="left",padx=(2,8))
        ttk.Label(row,text="Zoom: botões ± ou roda do mouse",foreground="#666").pack(side="left",padx=(6,0))
        keyrow=ttk.Frame(f); keyrow.pack(fill="x",pady=(0,6))
        ttk.Label(keyrow,text="Chave Google Maps Static API (requer faturamento ativo):").pack(side="left")
        self.google_maps_key=tk.StringVar(value=os.environ.get("GOOGLE_MAPS_API_KEY",""))
        ttk.Entry(keyrow,textvariable=self.google_maps_key,show="•",width=48).pack(side="left",padx=8)
        ttk.Label(keyrow,text="Imagem orbital: CBERS-4A/WFI (55 m, INPE) prioritário; Sentinel-2 como alternativa; VIIRS/NASA apenas para contexto visual em contingência. Mapa cartográfico IBGE somente após falha das imagens.",foreground="#666").pack(side="left")

        ibgebox=ttk.LabelFrame(f,text="Classificação oficial IBGE",padding=(10,7)); ibgebox.pack(fill="x",pady=(0,6))
        self.ibge_biome_display=tk.StringVar(value="Aguardando perímetro.")
        self.ibge_phys_display=tk.StringVar(value="Aguardando mapeamento da vegetação nativa e interseção IBGE.")
        self.aoi_area_display=tk.StringVar(value="Aguardando perímetro.")
        ttk.Label(ibgebox,text="Bioma:",font=("Segoe UI",9,"bold")).grid(row=0,column=0,sticky="nw")
        ttk.Label(ibgebox,textvariable=self.ibge_biome_display,wraplength=840).grid(row=0,column=1,sticky="w",padx=(8,0))
        ttk.Label(ibgebox,text="Fitofisionomias (SAR atual / potencial IBGE):",font=("Segoe UI",9,"bold")).grid(row=1,column=0,sticky="nw",pady=(4,0))
        # Multiline read-only text: complete class names stay visible at any window width.
        phys_frame=ttk.Frame(ibgebox)
        phys_frame.grid(row=1,column=1,sticky="ew",padx=(8,0),pady=(4,0))
        self.ibge_phys_text=tk.Text(phys_frame,height=4,width=45,wrap="word",font=("Segoe UI",9),
                                   foreground="#155D43",background="#F4F6F5",relief="flat",
                                   borderwidth=0,highlightthickness=0,state="disabled")
        phys_scroll=ttk.Scrollbar(phys_frame,orient="vertical",command=self.ibge_phys_text.yview)
        self.ibge_phys_text.configure(yscrollcommand=phys_scroll.set)
        self.ibge_phys_text.pack(side="left",fill="both",expand=True)
        phys_scroll.pack(side="right",fill="y")
        phys_frame.columnconfigure(0,weight=1)
        def refresh_ibge_phys(*_):
            self.ibge_phys_text.configure(state="normal")
            self.ibge_phys_text.delete("1.0","end")
            self.ibge_phys_text.insert("1.0",self.ibge_phys_display.get())
            self.ibge_phys_text.configure(state="disabled")
        self.ibge_phys_display.trace_add("write",refresh_ibge_phys)
        refresh_ibge_phys()
        ttk.Label(ibgebox,text="Área do polígono:",font=("Segoe UI",9,"bold")).grid(row=2,column=0,sticky="nw",pady=(4,0))
        ttk.Label(ibgebox,textvariable=self.aoi_area_display,foreground="#155D43").grid(row=2,column=1,sticky="w",padx=(8,0),pady=(4,0))
        ibgebox.columnconfigure(1,weight=1)

        map_frame=ttk.Frame(f); map_frame.pack(fill="both",expand=True,pady=(2,6))
        self.map_status=tk.StringVar(value="Aguardando carregamento de imagem de referência.")
        ttk.Label(map_frame,textvariable=self.map_status,anchor="w",foreground="#52645E").grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,4))
        self.map_canvas=tk.Canvas(map_frame,height=560,bg="#DDE4E1",highlightthickness=1,highlightbackground="#B8C5C0",
                                  xscrollincrement=20,yscrollincrement=20)
        self.map_hscroll=ttk.Scrollbar(map_frame,orient="horizontal",command=self.map_canvas.xview)
        self.map_vscroll=ttk.Scrollbar(map_frame,orient="vertical",command=self.map_canvas.yview)
        self.map_canvas.configure(xscrollcommand=self.map_hscroll.set,yscrollcommand=self.map_vscroll.set)
        self.map_canvas.grid(row=1,column=0,sticky="nsew"); self.map_vscroll.grid(row=1,column=1,sticky="ns"); self.map_hscroll.grid(row=2,column=0,sticky="ew")
        map_frame.rowconfigure(1,weight=1); map_frame.columnconfigure(0,weight=1)
        self._map_redraw_job=None; self._satellite_map_visible=False; self._last_map_size=None; self._last_canvas_size=None; self._map_extent_factor=1.36; self._map_provider="SATELLITE_PENDING"
        self.map_canvas.bind("<Configure>",self._on_map_resize)
        self.map_canvas.bind("<MouseWheel>",self._on_map_wheel)
        self.map_canvas.bind("<Button-4>",lambda e:self.map_zoom_in())
        self.map_canvas.bind("<Button-5>",lambda e:self.map_zoom_out())
        self.map_canvas.bind("<Double-Button-1>",lambda e:self.map_zoom_fit())
        self.map_canvas.create_text(20,20,anchor="nw",text="Carregue CAR, CCIR ou vetor e visualize o satélite com o polígono.",fill="#455")
        self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all"))

        spatial_box=ttk.Frame(f); spatial_box.pack(fill="x",pady=4)
        self.spatial_text=tk.Text(spatial_box,height=7,wrap="none",
            yscrollcommand=lambda *a:spatial_scroll.set(*a),
            xscrollcommand=lambda *a:spatial_hscroll.set(*a))
        spatial_scroll=ttk.Scrollbar(spatial_box,orient="vertical",command=self.spatial_text.yview)
        spatial_hscroll=ttk.Scrollbar(spatial_box,orient="horizontal",command=self.spatial_text.xview)
        spatial_box.rowconfigure(0,weight=1); spatial_box.columnconfigure(0,weight=1)
        self.spatial_text.grid(row=0,column=0,sticky="nsew")
        spatial_scroll.grid(row=0,column=1,sticky="ns")
        spatial_hscroll.grid(row=1,column=0,sticky="ew")
        self._bind_text_scroll(self.spatial_text)
        self._set(self.spatial_text,"Nenhum perímetro carregado. Use CAR, CCIR/SIGEF ou arquivo vetorial na tela de abertura.")

    def _on_map_wheel(self,event):
        if self.gdf is None:return "break"
        if getattr(event,"delta",0)>0:self.map_zoom_in()
        elif getattr(event,"delta",0)<0:self.map_zoom_out()
        return "break"

    def _apply_map_zoom(self):
        if self.gdf is None:return
        self.show_google_map(refresh=True,prefer_public=True)

    def map_zoom_in(self):
        if self.gdf is None:return
        self._map_extent_factor=max(0.30,self._map_extent_factor/1.5)
        self._apply_map_zoom()

    def map_zoom_out(self):
        if self.gdf is None:return
        self._map_extent_factor=min(8.0,self._map_extent_factor*1.5)
        self._apply_map_zoom()

    def map_zoom_fit(self):
        if self.gdf is None:return
        self._map_extent_factor=1.36
        self._apply_map_zoom()

    def _save_optical_diagnostic(self,generation,provider,failures):
        """Persist source-by-source outcomes; redact remote URLs and secrets."""
        try:
            if generation!=self._map_generation:return
            root=Path.home()/".enform_verde"
            root.mkdir(parents=True,exist_ok=True)
            rows=[]
            for entry in failures:
                message=re.sub(r"https?://[^\s]+","[URL_REDACTED]",str(entry))
                message=re.sub(r"(?i)(sig|token|client_secret|password)=([^&\s]+)",
                               r"\1=[REDACTED]",message)
                rows.append(message[:350])
            area=geom_metrics(self.gdf)["area_ha"] if self.gdf is not None else None
            data={"diagnostic_version":1,"app_version":APP_VERSION,
                  "area_ha":area,"provider_displayed":str(provider),
                  "attempt_errors":rows,
                  "note":"Display backdrop only; no use in SAR classifier or carbon."}
            dest=root/"ultimo_diagnostico_imagem_otica.json"
            tmp=dest.with_suffix(".tmp")
            tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            tmp.replace(dest)
        except Exception:
            pass  # Never lose the image because the diagnostic could not be written.

    def show_google_map(self,refresh=False,prefer_public=False):
        """Visual-only CBERS-4A/WFI primary backdrop; Sentinel-2 fallback; never an analytical input."""
        if self.gdf is None:return messagebox.showwarning("Mapa","Carregue/resolva o polígono primeiro.")
        self._map_generation+=1; generation=self._map_generation
        g=self.gdf.to_crs(4326).copy()
        viewport_w=max(500,self.map_canvas.winfo_width()); viewport_h=max(280,self.map_canvas.winfo_height())
        display_scale=max(1.0,min(4.0,1.36/max(float(self._map_extent_factor),0.30)))
        w=max(500,round(viewport_w*display_scale)); h=max(280,round(viewport_h*display_scale))
        ratio=w/max(h,1)
        if ratio>=1:
            req_w=1200; req_h=max(320,min(1200,round(1200/ratio)))
        else:
            req_h=1200; req_w=max(320,min(1200,round(1200*ratio)))
        key=self.google_maps_key.get().strip(); extent_factor=max(0.30,min(8.0,float(self._map_extent_factor)))
        if not refresh:self.map_status.set("Carregando imagem de referência e perímetro… os cálculos são independentes deste mapa.")
        self.update_idletasks()

        def rings():
            out=[]
            span=max(float(g.total_bounds[2]-g.total_bounds[0]),float(g.total_bounds[3]-g.total_bounds[1]),1e-7)
            tol=max(span/1600.0,1e-7)
            for geom in g.geometry:
                geoms=list(geom.geoms) if geom.geom_type=="MultiPolygon" else ([geom] if geom.geom_type=="Polygon" else [])
                for poly in geoms:
                    coords=list(poly.simplify(tol,preserve_topology=True).exterior.coords)
                    if len(coords)>220:
                        step=max(1,math.ceil(len(coords)/220)); coords=coords[::step]
                        if coords[-1]!=coords[0]:coords.append(coords[0])
                    if len(coords)>=4:out.append(coords)
            return out

        def google_image(rs):
            if not key:return None
            target_ratio=w/max(h,1)
            if target_ratio >= 1:
                api_w=640
                api_h=max(1,round(api_w/target_ratio))
            else:
                api_h=640
                api_w=max(1,round(api_h*target_ratio))
            params=[("size",f"{api_w}x{api_h}"),("scale","2"),("maptype","satellite"),("format","png"),("key",key)]
            for coords in rs:
                pts="|".join(f"{lat:.6f},{lon:.6f}" for lon,lat in coords)
                params.append(("path","color:0xff8a00ff|weight:4|fillcolor:0xff8a0033|"+pts))
            rr=requests.get("https://maps.googleapis.com/maps/api/staticmap",params=params,timeout=(8,35))
            rr.raise_for_status()
            if "image" not in (rr.headers.get("Content-Type") or "").lower():
                raise RuntimeError("resposta Google não é imagem")
            return Image.open(io.BytesIO(rr.content)).convert("RGB").resize((w,h),Image.Resampling.LANCZOS)

        def esri_export(rs,service="World_Imagery",label="Esri"):

            minx,miny,maxx,maxy=map(float,g.total_bounds)
            dx=max(maxx-minx,1e-8); dy=max(maxy-miny,1e-8); cx=(minx+maxx)/2; cy=(miny+maxy)/2
            bx=(cx-dx*extent_factor/2,cy-dy*extent_factor/2,cx+dx*extent_factor/2,cy+dy*extent_factor/2)
            params={"bbox":",".join(f"{v:.8f}" for v in bx),"bboxSR":"4326","imageSR":"4326",
                    "size":f"{req_w},{req_h}","format":"jpg","f":"image","dpi":"96"}
            rr=requests.get(f"https://server.arcgisonline.com/ArcGIS/rest/services/{service}/MapServer/export",params=params,timeout=(8,35))
            rr.raise_for_status()
            if "image" not in (rr.headers.get("Content-Type") or "").lower():
                raise RuntimeError("resposta Esri não é imagem")
            im=Image.open(io.BytesIO(rr.content)).convert("RGB")
            from PIL import ImageDraw
            d=ImageDraw.Draw(im,"RGBA"); iw,ih=im.size
            def px(lon,lat):
                return ((lon-bx[0])/max(bx[2]-bx[0],1e-12)*iw,
                        (bx[3]-lat)/max(bx[3]-bx[1],1e-12)*ih)
            for coords in rs:
                pts=[px(float(lon),float(lat)) for lon,lat in coords]
                if len(pts)>=4:
                    d.polygon(pts,fill=(255,138,0,48),outline=(255,138,0,255))
                    d.line(pts,width=max(3,round(iw/400)),fill=(255,138,0,255),joint="curve")
            return im.resize((w,h),Image.Resampling.LANCZOS)

        def worker():
            errors=[]; rs=rings()
            if not rs:
                self._map_queue.put((generation,None,[],"Mapa",None,None,"geometria sem polígono utilizável"))
                return
            try:
                p=cbers4a_wfi_preview(g,out_w=w,out_h=h,extent_factor=extent_factor)
                dr=p.get("date_range") or [p.get("datetime") or "",p.get("datetime") or ""]
                cloud_note=" • nuvens em lacunas" if p.get("cloud_pixels_included") else " • pixels claros"
                copyright=f"CBERS-4A/WFI • INPE • 55 m • {dr[0]}–{dr[1]}{cloud_note}"
                _store_satellite_preview_cache(g,extent_factor,w,h,p["image"],[],p["provider"],copyright)
                self._save_optical_diagnostic(generation,p["provider"],errors)
                self._map_queue.put((generation,p["image"],[],p["provider"],None,copyright,None))
                return
            except Exception as e:errors.append("CBERS-4A/WFI INPE: "+str(e))
            try:
                p=sentinel2_earthsearch_preview(g,out_w=w,out_h=h,extent_factor=extent_factor)
                copyright=f"Sentinel-2 L2A • Earth Search/AWS • {(p.get('datetime') or '')[:10]} • nuvens {format_ptbr(float(p.get('cloud_cover',0)),1)}%"
                _store_satellite_preview_cache(g,extent_factor,w,h,p["image"],p["polygons"],p["provider"],copyright)
                self._save_optical_diagnostic(generation,p["provider"],errors)
                self._map_queue.put((generation,p["image"],p["polygons"],p["provider"],None,copyright,None))
                return
            except Exception as e:errors.append("Sentinel-2 Earth Search/AWS: "+str(e))
            try:
                p=sentinel2_preview(g,extent_factor=extent_factor)
                copyright=f"Sentinel-2 L2A • Planetary Computer • {(p.get('datetime') or '')[:10]} • nuvens da cena {format_ptbr(float(p.get('cloud_cover',0)),1)}%"
                _store_satellite_preview_cache(g,extent_factor,w,h,p["image"],p["polygons"],p["provider"],copyright)
                self._map_queue.put((generation,p["image"],p["polygons"],p["provider"],None,copyright,None))
                return
            except Exception as e:errors.append("Sentinel-2 Planetary Computer: "+str(e))
            # Independent, keyless global optical fallback. VIIRS is lower
            # resolution than CBERS/Sentinel-2 and is strictly visual context;
            # it never feeds classification, vigor, or carbon calculations.
            try:
                p=nasa_gibs_preview(g,out_w=w,out_h=h,extent_factor=extent_factor)
                copyright=f"NASA GIBS • VIIRS SNPP • imagem de {p.get('datetime','')} • contexto visual"
                _store_satellite_preview_cache(g,extent_factor,w,h,p["image"],p.get("polygons") or [],p["provider"],copyright)
                self._save_optical_diagnostic(generation,p["provider"],errors)
                self._map_queue.put((generation,p["image"],p.get("polygons") or [],p["provider"],None,copyright,None))
                return
            except Exception as e:errors.append("NASA GIBS VIIRS: "+str(e))
            # Last online optical context fallback: actual aerial/satellite imagery
            # mosaic. Acquisition date/sensor cannot be inferred from this API.
            # Do not use it for classifying SAR land cover or deriving carbon.
            try:
                im=esri_export(rs,service="World_Imagery")
                copyright="Esri World Imagery • mosaico óptico de referência • data e sensor N/D"
                _store_satellite_preview_cache(g,extent_factor,w,h,im,[],"ESRI_WORLD_IMAGERY",copyright)
                self._save_optical_diagnostic(generation,"ESRI_WORLD_IMAGERY",errors)
                self._map_queue.put((generation,im,[],"ESRI_WORLD_IMAGERY",None,copyright,None))
                return
            except Exception as e:errors.append("Esri World Imagery: "+type(e).__name__+": "+str(e)[:180])
            cached=_read_satellite_preview_cache(g,extent_factor,w,h)
            if cached:
                image,meta=cached
                original=str(meta.get("provider") or meta.get("credit") or "")
                optical=("CBERS" in original.upper() or "SENTINEL" in original.upper())
                if optical:
                    credit="Imagem óptica em cache local • fonte original: "+original
                    self._save_optical_diagnostic(generation,"CACHE_OPTICAL",errors)
                    self._map_queue.put((generation,image,meta.get("polygons") or [],
                                         "CACHE ÓPTICO • "+original,None,credit,None))
                    return
                errors.append("Cache recusado: a origem não foi identificada como imagem óptica")
            # Última contingência: mapa cartográfico claramente identificado.
            # Nunca apresentá-lo como imagem orbital ou como observação da cobertura.
            try:
                image,_=offline_brazil_preview(g,extent_factor,(w,h))
                label="MAPA CARTOGRÁFICO IBGE — contingência excepcional; CBERS-4A e Sentinel-2 indisponíveis"
                self._save_optical_diagnostic(generation,"IBGE_CARTOGRAFICO",errors)
                self._map_queue.put((generation,image,[],"MAPA CARTOGRÁFICO IBGE (contingência sem imagem óptica)",
                                     None,label+" • "+" | ".join(errors),None))
                return
            except Exception as exc:
                errors.append("Mapa cartográfico de contingência: "+type(exc).__name__+": "+str(exc)[:160])
            self._save_optical_diagnostic(generation,"NO_OPTICAL_IMAGE",errors)
            self._map_queue.put((generation,None,[],"CBERS-4A/Sentinel-2",None,None," | ".join(errors)))

        threading.Thread(target=worker,name="EnformMap",daemon=True).start()
        self.after(80,self._poll_map_queue)

    def _poll_map_queue(self):
        try:item=self._map_queue.get_nowait()
        except queue.Empty:
            if self.winfo_exists():self.after(100,self._poll_map_queue)
            return
        generation,view,polygons,provider,zoom,copyright,error=item
        if generation!=self._map_generation:
            # A prior satellite request can finish after a new AOI/zoom request.
            # Discard its image but KEEP polling for the current request.
            if self.gdf is not None:self.after(100,self._poll_map_queue)
            return
        self._finish_satellite_map(generation,view,polygons,provider,zoom,copyright,error)

    def _finish_satellite_map(self,generation,view,polygons,provider,zoom,copyright,error):
        if generation!=self._map_generation or self.gdf is None:return
        if error:
            self._satellite_map_visible=False
            self._draw_aoi_outline("Imagem Sentinel-2/CBERS-4A indisponível — perímetro mantido")
            self.map_status.set("Imagem óptica e contingência cartográfica indisponíveis; esta falha visual não altera a análise quantitativa.")
            self._set(self.spatial_text,self.spatial_text.get("1.0","end").strip()+"\n\nImagem Sentinel-2/CBERS-4A indisponível: "+error)
            return
        self._satellite_map_visible=True; self._last_map_size=(view.width,view.height)
        self.google_map_photo=ImageTk.PhotoImage(view); self.map_canvas.delete("all"); self.map_canvas.create_image(0,0,image=self.google_map_photo,anchor="nw")
        for pts in polygons:self.map_canvas.create_polygon(*pts,fill="",outline="#FF8A00",width=3)
        self.map_canvas.create_rectangle(0,view.height-24,view.width,view.height,fill="white",outline=""); self.map_canvas.create_text(view.width-8,view.height-12,anchor="e",text=copyright,fill="#333",font=("Segoe UI",8))
        self.map_canvas.configure(scrollregion=(0,0,view.width,view.height))
        self.map_canvas.xview_moveto(max(0.0,min(1.0,(view.width-max(1,self.map_canvas.winfo_width()))/(2*max(1,view.width)))))
        self.map_canvas.yview_moveto(max(0.0,min(1.0,(view.height-max(1,self.map_canvas.winfo_height()))/(2*max(1,view.height)))))
        self._map_provider=str(provider or "ONLINE")
        self.map_status.set(f"{provider} carregado com o perímetro. Zoom cartográfico {format_ptbr(1.36/max(self._map_extent_factor,1e-9),2)}×. Uso exclusivo para visualização; não alimenta cálculos.")

    def _on_map_resize(self,event=None):
        """Keep the selected basemap fitted after a real canvas resize."""
        if self.gdf is None:return
        size=(max(300,self.map_canvas.winfo_width()),max(220,self.map_canvas.winfo_height()))
        # Compare canvas to canvas, not the differently-sized image request.
        # Otherwise a scrollbar/Configure cycle can perpetually restart the worker.
        if size==self._last_canvas_size:return
        self._last_canvas_size=size
        if self._satellite_map_visible:
            if self._map_refresh_job is not None:
                try:self.after_cancel(self._map_refresh_job)
                except Exception:pass
            self._map_refresh_job=self.after(450,self._refresh_satellite_after_resize)
            return
        if self._map_redraw_job is not None:
            try:self.after_cancel(self._map_redraw_job)
            except Exception:pass
        self._map_redraw_job=self.after(100,self._redraw_map_after_resize)

    def _refresh_satellite_after_resize(self):
        self._map_refresh_job=None
        if self.gdf is not None:
            self.show_google_map(refresh=True,prefer_public=True)

    def _redraw_map_after_resize(self):
        self._map_redraw_job=None
        if self.gdf is None:return
        if not self._satellite_map_visible:
            self.show_google_map(refresh=True,prefer_public=True)

    def _draw_offline_brazil_basemap(self,label="Mapa cartográfico IBGE — offline"):
        if self.gdf is None:return False
        try:
            viewport_w=max(500,self.map_canvas.winfo_width()); viewport_h=max(280,self.map_canvas.winfo_height())
            display_scale=max(1.0,min(4.0,1.36/max(float(self._map_extent_factor),0.30)))
            w=max(500,round(viewport_w*display_scale)); h=max(280,round(viewport_h*display_scale))
            view,_=offline_brazil_preview(self.gdf,self._map_extent_factor,(w,h))
            self._satellite_map_visible=True; self._last_map_size=(w,h); self._map_provider="OFFLINE_IBGE"
            self.google_map_photo=ImageTk.PhotoImage(view); self.map_canvas.delete("all")
            self.map_canvas.create_image(0,0,image=self.google_map_photo,anchor="nw",tags=("offline_ibge","aoi_visible"))
            self.map_canvas.create_rectangle(0,h-24,w,h,fill="white",outline="")
            self.map_canvas.create_text(w-8,h-12,anchor="e",text="IBGE 2025/BC250 — mapa vetorial rasterizado localmente",fill="#333",font=("Segoe UI",8))
            self.map_canvas.create_text(10,10,anchor="nw",text=label,fill="white",font=("Segoe UI",9,"bold"))
            self.map_canvas.configure(scrollregion=(0,0,w,h))
            return True
        except Exception as exc:
            try:self.map_status.set(f"Falha ao carregar mapa cartográfico: {type(exc).__name__}: {exc}")
            except Exception:pass
            return False

    def _draw_aoi_outline(self,label="Pré-visualização da AOI"):
        """Render the AOI in a local metric projection and fit it to the live canvas."""
        if self.gdf is None:return
        self._satellite_map_visible=False
        g=self.gdf.to_crs(4326); union=g.geometry.union_all(); center=union.centroid
        from pyproj import CRS
        local=CRS.from_proj4(f"+proj=aeqd +lat_0={float(center.y)} +lon_0={float(center.x)} +datum=WGS84 +units=m +no_defs")
        projected=g.to_crs(local); minx,miny,maxx,maxy=map(float,projected.total_bounds)
        w=max(300,self.map_canvas.winfo_width()); h=max(220,self.map_canvas.winfo_height()); pad=max(30,min(70,int(min(w,h)*0.12)))
        dx=max(maxx-minx,1e-6); dy=max(maxy-miny,1e-6); scale=min((w-2*pad)/dx,(h-2*pad)/dy)
        draw_w=dx*scale; draw_h=dy*scale; ox=(w-draw_w)/2; oy=(h-draw_h)/2
        self._last_map_size=(w,h); self.map_canvas.delete("all"); self.map_canvas.configure(bg="#EAF0EC")
        # Offline map frame: always available and intentionally independent of tile/network services.
        for frac in (0.25,0.5,0.75):
            gx=pad+(w-2*pad)*frac; gy=pad+(h-2*pad)*frac
            self.map_canvas.create_line(gx,pad,gx,h-pad,fill="#C9D4CF",dash=(2,4))
            self.map_canvas.create_line(pad,gy,w-pad,gy,fill="#C9D4CF",dash=(2,4))
        self.map_canvas.create_text(w-14,14,anchor="ne",text="N",fill="#24382D",font=("Segoe UI",10,"bold"))
        self.map_canvas.create_line(w-20,48,w-20,24,fill="#24382D",width=2,arrow="first")
        def xy(x,y):return ox+(float(x)-minx)*scale,h-(oy+(float(y)-miny)*scale)
        for geom in projected.geometry:
            polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else ([geom] if geom.geom_type=="Polygon" else [])
            for poly in polys:
                pts=[]
                for coord in poly.exterior.coords:pts.extend(xy(coord[0],coord[1]))
                if len(pts)>=6:self.map_canvas.create_polygon(*pts,fill="#F8B44C",stipple="gray50",outline="#E87500",width=3)
        self.map_canvas.create_text(12,12,anchor="nw",text=label,fill="#24382D",font=("Segoe UI",10,"bold"))
        # Scale bar is calculated from the local projection; the AOI is never stretched to the panel.
        bar_m=max(1.0,draw_w*0.18/1000)*1000; bar_px=bar_m*scale; bx=max(18,w-pad-bar_px); by=h-24
        self.map_canvas.create_line(bx,by,bx+bar_px,by,fill="#24382D",width=3)
        self.map_canvas.create_line(bx,by-5,bx,by+4,fill="#24382D",width=2); self.map_canvas.create_line(bx+bar_px,by-5,bx+bar_px,by+4,fill="#24382D",width=2)
        self.map_canvas.create_text(bx+bar_px/2,by-7,text=f"{bar_m/1000:g} km",anchor="s",fill="#24382D",font=("Segoe UI",8,"bold"))
        b4326=g.total_bounds
        bbox_txt=f"{format_ptbr(b4326[0],5)}; {format_ptbr(b4326[1],5)}  →  {format_ptbr(b4326[2],5)}; {format_ptbr(b4326[3],5)}"
        self.map_canvas.create_text(12,h-12,anchor="sw",text=bbox_txt,fill="#4A5B54",font=("Segoe UI",8))

    def _maap_renewal_message(self):
        from esa_maap_token_renewal import renewal_status
        info=renewal_status()
        if info["state"]=="EXPIRED":
            return "ESA MAAP: prazo de 90 dias encerrado em "+info["expires_on"]+" — renovar o token."
        if info["state"]=="EXPIRING_SOON":
            return ("ESA MAAP: vencimento estimado em "+str(info["days_remaining"])+
                    " dia(s) ("+info["expires_on"]+").")
        if info["state"]=="VALID_ESTIMATED":
            return ("ESA MAAP: vencimento estimado em "+str(info["days_remaining"])+
                    " dias ("+info["expires_on"]+").")
        return "ESA MAAP: data de emissão não cadastrada; validade desconhecida."

    def _refresh_maap_renewal_label(self):
        if hasattr(self,"maap_renewal_message"):
            self.maap_renewal_message.set(self._maap_renewal_message())

    def _open_maap_renewal(self):
        from esa_maap_token_renewal import MAAP_TOKEN_PORTAL
        if not webbrowser.open(MAAP_TOKEN_PORTAL):
            messagebox.showinfo("Renovação ESA MAAP",
                "Abra a página oficial para gerar novo token:\n"+MAAP_TOKEN_PORTAL)

    def _focus_new_maap_token(self):
        if hasattr(self,"maap_token_input"):
            self.esa_token.set("")
            self.maap_token_input.focus_set()
            messagebox.showinfo("Novo token ESA MAAP",
                "Cole o token renovado no campo protegido ESA MAAP.\n"
                "O token substituído será descartado da interface. "
                "Em seguida registre a data real de emissão no portal.")

    def _record_maap_token_issue_date(self):
        from datetime import date
        from esa_maap_token_renewal import save_renewal_date
        value=simpledialog.askstring("Data de emissão do ESA MAAP",
            "Informe a data em que o token foi GERADO no portal ESA (AAAA-MM-DD).\n"
            "Não use a data em que um token antigo foi inserido no programa.\n"
            "O token em si não será salvo.",initialvalue=date.today().isoformat(),parent=self)
        if value is None:return
        try:
            info=save_renewal_date(value.strip())
        except (ValueError,OSError) as exc:
            return messagebox.showerror("Data inválida",str(exc))
        self._refresh_maap_renewal_label()
        messagebox.showinfo("Prazo registrado",
            "Data anotada: "+info["issued_on"]+"; vencimento estimado: "+
            info["expires_on"]+".\nSomente a data foi armazenada. Cole o novo token no campo ESA MAAP.")

    def _check_maap_token_renewal(self):
        from esa_maap_token_renewal import renewal_status
        self._refresh_maap_renewal_label()
        info=renewal_status()
        if info["state"] not in ("EXPIRED","EXPIRING_SOON"):return
        if messagebox.askyesno("Renovação ESA MAAP",
            self._maap_renewal_message()+
            "\n\nDeseja abrir agora a página oficial para gerar novo token?"):
            self._open_maap_renewal()

    def _remote(self):
        f=self.tabs[2]
        steps=ttk.Frame(f); steps.pack(fill="x",pady=(0,10))
        for j,t in enumerate(["1. Dados e Catálogos","2. Download e Pré-processamento","3. Modelagem e AGB","4. Resultados SAR"]):
            lab=tk.Label(steps,text=t,bg=("#08733F" if j==0 else "#EEF2F3"),fg=("white" if j==0 else "#233B49"),font=("Segoe UI",10,"bold"),padx=14,pady=9,bd=1,relief="solid")
            lab.pack(side="left",fill="x",expand=True,padx=(0,2))

        # Public routes remain automatic. Optional Earthdata Login unlocks protected NISAR/ASF scenes.
        self.edl_token=tk.StringVar(); self.edl_user=tk.StringVar(value=os.environ.get("EARTHDATA_USERNAME","")); self.edl_password=tk.StringVar()
        self.esa_token=tk.StringVar(); self.cdse_token=tk.StringVar(); self.cdse_client_id=tk.StringVar(); self.cdse_client_secret=tk.StringVar()
        edl=ttk.LabelFrame(f,text="Earthdata Login opcional — NISAR/ASF protegido",padding=8); edl.pack(fill="x",pady=(0,6))
        ttk.Label(edl,text="Usuário:").grid(row=0,column=0,sticky="w"); ttk.Entry(edl,textvariable=self.edl_user,width=28).grid(row=0,column=1,sticky="w",padx=(5,12))
        ttk.Label(edl,text="Senha:").grid(row=0,column=2,sticky="w"); ttk.Entry(edl,textvariable=self.edl_password,show="•",width=28).grid(row=0,column=3,sticky="w",padx=5)
        ttk.Label(edl,text="Não é armazenada. O programa também tenta EARTHDATA_* e _netrc/.netrc automaticamente.",foreground="#666").grid(row=1,column=0,columnspan=4,sticky="w",pady=(4,0))
        ttk.Label(edl,text="ESA MAAP Long Lasting Token (90 dias):").grid(row=2,column=0,sticky="w",pady=(5,0))
        self.maap_token_input=ttk.Entry(edl,textvariable=self.esa_token,show="•",width=58)
        self.maap_token_input.grid(row=2,column=1,columnspan=3,sticky="ew",padx=(5,5),pady=(5,0))
        ttk.Label(edl,text="Opcional; usado somente para baixar produtos BIOMASS protegidos e nunca gravado pelo programa.",foreground="#666").grid(row=3,column=0,columnspan=4,sticky="w",pady=(3,0))
        self.maap_renewal_message=tk.StringVar(value=self._maap_renewal_message())
        ttk.Label(edl,textvariable=self.maap_renewal_message,foreground="#9A4B16",
                  wraplength=720).grid(row=4,column=0,columnspan=4,sticky="w",pady=(6,2))
        renewal_row=ttk.Frame(edl); renewal_row.grid(row=5,column=0,columnspan=4,sticky="w",pady=(2,4))
        ttk.Button(renewal_row,text="RENOVAR TOKEN NO PORTAL ESA",
                   command=self._open_maap_renewal).pack(side="left")
        ttk.Button(renewal_row,text="SUBSTITUIR TOKEN",
                   command=self._focus_new_maap_token).pack(side="left",padx=8)
        ttk.Button(renewal_row,text="REGISTRAR DATA DE EMISSÃO / RENOVAÇÃO",
                   command=self._record_maap_token_issue_date).pack(side="left",padx=8)
        providers=ttk.LabelFrame(f,text="Fontes SAR automáticas — prioridade máxima",padding=12); providers.pack(fill="x",pady=(4,10))
        ttk.Label(providers,text="ESA BIOMASS — banda P",font=("Segoe UI",10,"bold")).grid(row=0,column=0,sticky="w")
        ttk.Label(providers,text="PRIORIDADE 1 — consulta automática das coleções BIOMASS L1/L2 e FP_AGB_L2B; processamento do produto disponível mais adequado.").grid(row=0,column=1,sticky="w",padx=8)
        ttk.Label(providers,text="ESA CCI Biomass v7",font=("Segoe UI",10,"bold")).grid(row=1,column=0,sticky="w",pady=5)
        ttk.Label(providers,text="AGB 100 m + incerteza por pixel — acesso automático como produto quantitativo SAR derivado.").grid(row=1,column=1,sticky="w",padx=8)
        ttk.Label(providers,text="Copernicus Sentinel-1",font=("Segoe UI",10,"bold")).grid(row=2,column=0,sticky="w")
        ttk.Label(providers,text="C-band VV/VH — consulta/processamento automático quando o serviço público permitir acesso direto.").grid(row=2,column=1,sticky="w",padx=8)
        ttk.Label(providers,text="NISAR / ALOS-PALSAR",font=("Segoe UI",10,"bold")).grid(row=3,column=0,sticky="w",pady=5)
        ttk.Label(providers,text="L-band — catálogo consultado automaticamente; produtos diretamente acessíveis são processados sem intervenção do usuário.").grid(row=3,column=1,sticky="w",padx=8)
        ttk.Label(providers,text="Arquivo local/licenciado",font=("Segoe UI",10,"bold")).grid(row=4,column=0,sticky="w")
        ttk.Label(providers,text="GeoTIFF/HDF5 SAR ou AGB continua disponível como rota adicional.").grid(row=4,column=1,sticky="w",padx=8)
        providers.columnconfigure(1,weight=1)

        row=ttk.Frame(f); row.pack(fill="x",pady=8)
        self.pipeline_btn=ttk.Button(row,text="EXECUTAR ANÁLISE SAR",command=self.execute,style="Run.TButton"); self.pipeline_btn.pack(side="left")
        ttk.Button(row,text="DESCOBRIR COBERTURA SAR",command=self.discover_sar_ui).pack(side="left",padx=8)
        ttk.Button(row,text="CARREGAR PRODUTOS SAR / AGB",command=self.pick_sar).pack(side="left")
        ttk.Button(row,text="CAMADA IBGE FITOFISIONOMIAS",command=self.pick_ibge_physiognomy).pack(side="left",padx=8)
        landrow=ttk.Frame(f); landrow.pack(fill="x",pady=4)
        ttk.Button(landrow,text="CONFIGURAR CLASSIFICAÇÃO SAR DE USO",command=self.pick_land_use_config).pack(side="left")
        ttk.Button(landrow,text="IDENTIFICAR USO DO SOLO",command=self.classify_land_use_ui).pack(side="left",padx=8)
        self.land_use_config=None; self._land_use_running=False
        self.land_use_state=tk.StringVar(value="Identificadores SAR instalados: busca automática; alternativa MapBiomas para cobertura atual e IBGE para fitofisionomia.")
        ttk.Label(landrow,textvariable=self.land_use_state,wraplength=500).pack(side="left",padx=8)
        native_row=ttk.Frame(f);native_row.pack(fill="x",pady=(2,6))
        self.inventory_evidence_data=None; self.inventory_evidence_manifest=None
        ttk.Button(native_row,text="CARREGAR EVIDÊNCIAS DE INVENTÁRIO (JSON)",
                   command=self.pick_inventory_evidence).pack(side="left")
        self.inventory_evidence_state=tk.StringVar(
            value="Opcional: referências licenciadas compatíveis com fitofisionomia; uso experimental, não homologado.")
        ttk.Label(native_row,textvariable=self.inventory_evidence_state,
                  wraplength=680).pack(side="left",padx=8)
        self.biodiversity_inventory_records=None
        biodiversity_row=ttk.Frame(f);biodiversity_row.pack(fill="x",pady=(0,6))
        ttk.Button(biodiversity_row,text="CARREGAR INVENTÁRIO FITOSSOCIOLÓGICO CSV",
                   command=self.pick_biodiversity_inventory).pack(side="left")
        self.biodiversity_inventory_state=tk.StringVar(
            value="Resumo regional de espécies e distribuição diamétrica; não representa medição da propriedade.")
        ttk.Label(biodiversity_row,textvariable=self.biodiversity_inventory_state,
                  wraplength=800).pack(side="left",padx=8)
        self.sar_paths=[]; self.ibge_physiognomy_gdf=None; self.ibge_class_field=None
        self.sensor=tk.StringVar(value="Automático — SAR primeiro: P → L → X → C → CCI; literatura/modelagem somente após falha documentada")
        remote_box=ttk.Frame(f); remote_box.pack(fill="both",expand=True,pady=8)
        self.remote_text=tk.Text(remote_box,height=18,wrap="word",yscrollcommand=lambda *a:remote_scroll.set(*a))
        remote_scroll=ttk.Scrollbar(remote_box,orient="vertical",command=self.remote_text.yview)
        self.remote_text.pack(side="left",fill="both",expand=True); remote_scroll.pack(side="right",fill="y")
        self._bind_text_scroll(self.remote_text)
        self._set(self.remote_text,"A análise é automática e SAR-FIRST. Rotas públicas são tentadas sem credenciais; Earthdata Login é opcional para liberar NISAR/ASF protegido.\n\nHierarquia obrigatória:\n1. ESA BIOMASS FP_AGB_L2B (P-band, AGB + incerteza);\n2. modelos SAR L/X executáveis compatíveis com fitofisionomia e atributos disponíveis;\n3. ESA CCI Biomass L+C como série histórica;\n4. literatura somente como aferição/fallback quando nenhum produto SAR quantitativo puder ser processado.\n\nRegra: SAR é SEMPRE tentado primeiro. Se for impossível processá-lo, a trilha registra o motivo e só então usa literatura/modelagem compatível, identificada como secundária e com incerteza explícita.")

    def pick_inventory_evidence(self):
        filename=filedialog.askopenfilename(
            title="Inventários para estimativas experimentais de carbono",
            filetypes=[("Manifesto JSON","*.json")])
        if not filename:
            return
        from native_evidence_manifest import load_native_inventory_manifest
        try:
            package=load_native_inventory_manifest(filename)
        except (OSError,ValueError) as exc:
            self.status.set("Manifesto de inventário recusado; não foi aplicado.")
            return messagebox.showwarning("Evidências de inventário",str(exc))
        # Preserve last accepted data if the new file fails validation; no
        # changes to native cover masks or previously approved SAR products.
        self.inventory_evidence_data=package["records"]
        self.inventory_evidence_manifest={
            "filename":package["filename"],
            "sha256":package["sha256"],
            "evidence_status":package["evidence_status"],
            "n_records":len(package["records"]),
        }
        self.inventory_evidence_state.set(
            str(len(package["records"]))+" registros — "+package["filename"]+
            " — estimativas secundárias experimentais; validação independente pendente.")
        self.status.set("Evidências externas carregadas com checksum; apenas classes compatíveis serão consideradas.")

    def pick_biodiversity_inventory(self):
        filename=filedialog.askopenfilename(title="Inventário fitossociológico georreferenciado",
            filetypes=[("CSV de árvores","*.csv"),("Todos","*.*")])
        if not filename:return
        try:
            from biodiversity_inventory import load_biodiversity_inventory_csv
            rows=load_biodiversity_inventory_csv(filename)
        except (OSError,ValueError) as exc:
            self.status.set("Inventário fitossociológico recusado; não foi aplicado.")
            return messagebox.showwarning("Inventário fitossociológico",str(exc))
        self.biodiversity_inventory_records=rows
        self.biodiversity_inventory_state.set(str(len(rows))+" árvores licenciadas — "+Path(filename).name+
            "; será filtrado por bioma, fitofisionomia e microrregião.")
        self.status.set("Inventário fitossociológico carregado; referência regional, não medição da propriedade.")

    def pick_land_use_config(self):
        p=filedialog.askopenfilename(title="Contrato de atributos e referências SAR",filetypes=[("Configuração JSON","*.json")])
        if p:
            self.land_use_config=p
            self.land_use_state.set("Configuração carregada: "+Path(p).name+"; elegibilidade será validada na execução.")

    def classify_land_use_ui(self):
        if self.gdf is None:return messagebox.showwarning("Uso do solo","Carregue o perímetro primeiro.")
        if self._land_use_running or self._analysis_running:return
        self._land_use_running=True
        generation=self._analysis_generation
        frame=self.gdf.copy(); config=self.land_use_config
        ibge=self.ibge_physiognomy_gdf.copy() if self.ibge_physiognomy_gdf is not None else None
        field=self.ibge_class_field or "legenda_1"
        output=Path.home()/".enform_verde"/"uso_solo"/uuid.uuid4().hex[:12]
        result_queue=queue.Queue()
        self.land_use_state.set("Classificando e verificando confiança em segundo plano…")
        def worker():
            try:
                reference=ibge;reference_field=field
                if reference is None:
                    try:reference,reference_field=load_ibge_land_use_reference(frame)
                    except Exception:pass
                result_queue.put((True,run_land_use(frame,output,config,ibge=reference,ibge_field=reference_field,sar_paths=getattr(self,'sar_paths',None))))
            except Exception as exc:result_queue.put((False,str(exc)))
        def poll():
            try:ok,result=result_queue.get_nowait()
            except queue.Empty:
                self.after(150,poll); return
            self._land_use_running=False
            if generation!=self._analysis_generation:return
            if not ok:
                self.land_use_state.set("Classificação não concluída: "+result); return
            for key in ("native_carbon","analysis_rows","total_tc_ha","total_tco2_ha","sar_result","total_uncertainty"):
                self.project.pop(key,None)
            self.project["land_use"]=result
            if not self.project.get("analysis_rows"):self.project["area_ha"]=result["area_aoi_ha"]
            text="\n".join(land_use_report_lines(result,lambda v:format_ptbr(v,2)))
            self.project["last_result"]=text
            self._set(self.res,text);self.nb.select(self.tabs[3])
            self.land_use_state.set(
                result["status"]+" — "+(
                    "Identificador SAR executado: "+Path(result["sar_model_config"]).name
                    if result.get("sar_model_config") else
                    "sem identificador SAR validado; fonte cartográfica explicitada"
                )+"; áreas e auditoria disponíveis."
            )
        threading.Thread(target=worker,name="EnformLandUse",daemon=True).start()
        self.after(150,poll)

    def _test_cdse(self):
        try:
            cid=self.cdse_client_id.get().strip(); sec=self.cdse_client_secret.get().strip()
            if not cid or not sec:
                self.cdse_state.set("Informe Client ID e Client Secret.")
                return
            cdse_access_token(cid,sec)
            self.cdse_state.set("CDSE conectado — OAuth2 válido.")
        except Exception as e:
            self.cdse_state.set("Falha CDSE: "+str(e)[:120])

    def discover_sar_ui(self):
        if self.gdf is None:return messagebox.showwarning("SAR","Carregue/resolva o polígono primeiro.")
        try:
            self.status.set("Consultando catálogos SAR..."); self.update_idletasks()
            cov=discover_sar(self.gdf); self.project["sar_catalog"]=cov
            txt=["REGISTROS RETORNADOS PELOS CATÁLOGOS SAR","(descoberta ≠ download ≠ processamento ≠ uso na estimativa)"]
            for x in cov:txt.append(f"{x['provider']} — {x['dataset']} ({x['band']}): {x['count']} registro(s) retornado(s)"+((" — "+x["error"]) if x.get("error") else ""))
            for x in cov:
                latest=x.get("latest_acquisition")
                if latest:
                    txt.append(f"  Aquisição mais recente no catálogo: {latest.get('acquisition_brasilia')} (Brasília) | UTC {latest.get('acquisition_utc')} | cena {latest.get('id')}")
                else:
                    txt.append("  Sem data/hora de aquisição verificável no retorno do catálogo.")
            txt += ["","Para uso quantitativo, o produto ainda precisa ser elegível, baixado, pré-processado e associado a modelo/produto AGB compatível."]
            self._set(self.remote_text,"\n".join(txt)); self.status.set("Descoberta SAR concluída.")
        except Exception as e:self.status.set("Falha na descoberta SAR."); messagebox.showerror("SAR",str(e))

    def pick_sar(self):
        ps=filedialog.askopenfilenames(title="Produtos SAR / AGB / incerteza",filetypes=[("GeoTIFF","*.tif *.tiff"),("Todos","*.*")])
        if not ps:return
        self.sar_paths=list(ps); self.project["sar_paths"]=list(ps)
        self._set(self.remote_text,"Produtos selecionados:\n"+"\n".join(self.sar_paths)+"\n\nClique em EXECUTAR ANÁLISE.")
        self.status.set(f"{len(ps)} produto(s) SAR selecionado(s).")

    def pick_ibge_physiognomy(self):
        p=filedialog.askopenfilename(title="Selecione a camada vetorial oficial de fitofisionomias do IBGE",
            filetypes=[("Vetores","*.gpkg *.shp *.geojson *.json *.zip"),("Todos","*.*")])
        if not p:return
        try:
            layer=read_vector(p)
            names=list(layer.columns)
            normalized={re.sub(r"[^a-z0-9]","",str(x).casefold()):x for x in names if str(x)!="geometry"}
            preferred=("legenda1","fitofisionomia","fisionomia","legenda","vegetacao","classe","descricao","nome")
            field=next((normalized[k] for k in preferred if k in normalized),None)
            if field is None:
                candidates=[x for x in names if str(x)!="geometry" and layer[x].notna().any()]
                if len(candidates)==1:field=candidates[0]
            if field is None:
                raise ValueError("Não identifiquei automaticamente o campo da classe IBGE. Campos disponíveis: "+", ".join(str(x) for x in names))
            self.ibge_physiognomy_gdf=layer; self.ibge_class_field=field
            self.project["ibge_physiognomy_vector"]=p; self.project["ibge_physiognomy_class_field"]=str(field)
            self.status.set("Camada de fitofisionomias IBGE carregada; classe: "+str(field))
            self._set(self.remote_text,"Camada de fitofisionomias selecionada: "+Path(p).name+"\\nCampo de classe: "+str(field)+"\\nAs estatísticas SAR serão calculadas em cada interseção AOI × classe IBGE.")
        except Exception as e:
            self.ibge_physiognomy_gdf=None; self.ibge_class_field=None
            self.status.set("Camada de fitofisionomias IBGE não carregada.")
            messagebox.showerror("Fitofisionomias IBGE",str(e))

    def _results(self):
        f=self.tabs[3]; ttk.Label(f,text="Balanço de compartimentos",style="H.TLabel").pack(anchor="w")
        result_box=ttk.Frame(f); result_box.pack(fill="both",expand=True,pady=8)
        self.res=tk.Text(result_box,height=23,wrap="word",yscrollcommand=lambda *a:result_scroll.set(*a))
        result_scroll=ttk.Scrollbar(result_box,orient="vertical",command=self.res.yview)
        self.res.pack(side="left",fill="both",expand=True); result_scroll.pack(side="right",fill="y")
        self._bind_text_scroll(self.res)
        self._set(self.res,"Clique em EXECUTAR ANÁLISE quando houver dados suficientes.")
    def _cultivated_results(self):
        """Separate concise executive results from traceable technical audit."""
        f=self.tabs[5]
        ttk.Label(f,text="Monitoramento de áreas cultivadas",style="H.TLabel").pack(anchor="w")
        ttk.Label(f,text="Detecção de áreas cultivadas primeiro; identificação da cultura somente quando a evidência e a validação permitirem.",
                  wraplength=1000).pack(anchor="w",pady=(4,8))
        ttk.Button(f,text="ATUALIZAR PAINEL METEOROLÓGICO — CLIMA DINÂMICO NASA POWER / CPTEC",command=self.query_crop_weather).pack(anchor="w",pady=(0,8))
        views=ttk.Notebook(f);views.pack(fill="both",expand=True)
        exec_frame=ttk.Frame(views);audit_frame=ttk.Frame(views)
        views.add(exec_frame,text="Painel executivo")
        views.add(audit_frame,text="Auditoria técnica")
        exec_box=ttk.Frame(exec_frame);exec_box.pack(fill="both",expand=True)
        audit_box=ttk.Frame(audit_frame);audit_box.pack(fill="both",expand=True)
        self.crop_res=tk.Text(exec_box,height=20,wrap="word",yscrollcommand=lambda *a:exec_scroll.set(*a))
        exec_scroll=ttk.Scrollbar(exec_box,orient="vertical",command=self.crop_res.yview)
        self.crop_res.pack(side="left",fill="both",expand=True);exec_scroll.pack(side="right",fill="y")
        self.crop_audit=tk.Text(audit_box,height=20,wrap="word",yscrollcommand=lambda *a:audit_scroll.set(*a))
        audit_scroll=ttk.Scrollbar(audit_box,orient="vertical",command=self.crop_audit.yview)
        self.crop_audit.pack(side="left",fill="both",expand=True);audit_scroll.pack(side="right",fill="y")
        self._bind_text_scroll(self.crop_res);self._bind_text_scroll(self.crop_audit)
        self._set(self.crop_res,"PAINEL EXECUTIVO — PREVISÃO DE SAFRAS\n\n"
                  "Idade provável da lavoura: INDISPONÍVEL — requer evidência fenológica SAR validada.\n"
                  "Estado fitossanitário aparente: INDISPONÍVEL — opções: Bom, Médio ou Ruim; requer modelo e evidência validados. Não é diagnóstico de doença ou praga.\n"
                  "Previsão de safra: após a análise — modelo calibrado no histórico PAM (soja e milho; experimental, validado fora da amostra), com vigor automático Sentinel-1 quando houver mapa de referência.\n\n"
                  "Execute a análise para consultar cobertura, cultura e disponibilidade dos dados.")
        self._set(self.crop_audit,"A trilha de auditoria da análise será apresentada aqui.")

    def _present_cultivated_monitoring(self,land):
        """Present concise results and keep full evidence in a separate audit view."""
        from agricultural_native_policy import has_cultivated_area
        self._weather_query_generation+=1
        self._last_land=land
        classes=land.get("classes",[])
        non_native=[item for item in classes if item.get("native_status") is False and
                    not str(item.get("source") or "").startswith("SAR_EXPERIMENTAL_MODELO") and
                    float(item.get("area_ha") or 0)>0]
        native=[item for item in classes if item.get("native_status") is True and float(item.get("area_ha") or 0)>0]
        classified_ha=sum(float(item.get("area_ha") or 0) for item in classes)
        aoi_ha=float(self.project.get("area_ha") or 0)
        complete_coverage=aoi_ha>0 and abs(classified_ha-aoi_ha)<=max(0.05,0.001*aoi_ha)
        native_occurrence=land.get("native_occurrence") if isinstance(land.get("native_occurrence"),dict) else {}
        native_area=(float(native_occurrence["area_ha"]) if native_occurrence.get("status")=="detected_by_validated_SAR" and native_occurrence.get("area_ha") is not None else None)
        native_summary=("Vegetação nativa detectada por SAR validado: "+format_ptbr(native_area,2)+
                        " ha; sem confirmação de campo." if native_area is not None and native_area>0 else
                        "Ocorrência de vegetação nativa: N/D — ausência de máscara semântica SAR validada não significa 0 ha.")
        if not has_cultivated_area(classes) and complete_coverage and land.get("status")=="SAR_ELEGIVEL":
            self._crop_monitoring_base_report="sem cultivos detectados\n"+native_summary
            self._crop_monitoring_audit_base="Nenhuma classe de cultivo foi encontrada na área totalmente coberta pela classificação.\n"+native_summary+"\n\nRastreabilidade da análise:\n"+json.dumps(land,ensure_ascii=False,indent=2,default=str)
            self._set(self.crop_res,self._crop_monitoring_base_report)
            self._set(self.crop_audit,self._crop_monitoring_audit_base)
            generation=self._weather_query_generation
            analysis_id=self.project.get("analysis_run_id")
            def start_weather_if_current():
                if (generation==self._weather_query_generation
                    and analysis_id==self.project.get("analysis_run_id")
                    and self.gdf is not None):
                    self.query_crop_weather()
            self.after(100,start_weather_if_current)
            return
        from crop_report_consistency import current_crop_area_by_semantic_sar
        crop_ha,generic_cultivated_ha=current_crop_area_by_semantic_sar(land)
        semantic_area_supported=crop_ha is not None
        measured_crop_ha=crop_ha or 0.0
        measured_generic_ha=generic_cultivated_ha or 0.0
        other_non_native_ha=sum(float(x.get("area_ha") or 0) for x in non_native)-measured_crop_ha-measured_generic_ha
        executive=["PAINEL EXECUTIVO — MONITORAMENTO AGRÍCOLA",
                   "Estado da classificação SAR atual: "+str(land.get("status","N/D"))+
                   " — MapBiomas não determina classes, áreas, vigor ou safra atuais.",
                   "ÁREA TOTAL DA AOI: "+format_ptbr(aoi_ha,2)+" ha (100%)",
                   "Área com classes semânticas SAR atuais: "+(format_ptbr(classified_ha,2)+" ha" if semantic_area_supported else "N/D — classificador SAR atual indisponível"),
                   "RESUMO EXCLUSIVO DE COBERTURA (os grupos não se sobrepõem):",
                   "  Vegetação nativa: "+(format_ptbr(native_area,2)+" ha ("+format_ptbr(100*native_area/aoi_ha if aoi_ha else 0,2)+"%)" if native_area is not None else "N/D — não converter ausência de máscara em 0 ha"),
                   "  Lavouras identificadas por classificador SAR atual validado: "+(format_ptbr(crop_ha,2)+" ha" if semantic_area_supported else "N/D — classificação atual indisponível; não equivale a 0 ha"),
                   "  Áreas agrícolas sem identificação de cultura: "+(format_ptbr(generic_cultivated_ha,2)+" ha" if semantic_area_supported else "N/D — classificação atual indisponível"),
                   "  Outros usos não nativos: "+(format_ptbr(max(0,other_non_native_ha),2)+" ha" if land.get("status")=="SAR_ELEGIVEL" else "N/D — classe semântica SAR não validada"),
                   "ATENÇÃO: área da AOI NÃO é integralmente floresta nem integralmente lavoura.",
                   "DISTRIBUIÇÃO ESPACIAL DAS CLASSES INTERSECTADAS NA AOI — ha e % (origem/status em cada linha):"]
        contingency=land.get("agriculture_historical_contingency") or {}
        if contingency.get("status")=="FALLBACK_HISTORICO_MAPBIOMAS_PAM":
            executive.extend(["", "CONTINGÊNCIA AGRÍCOLA HISTÓRICA — usada após esgotar as rotas SAR configuradas",
                "MapBiomas Collection "+str(contingency.get("mapbiomas_collection"))+", ano "+str(contingency.get("mapbiomas_year"))+
                "; área mapeada "+format_ptbr(contingency.get("mapped_area_ha"),2)+" ha. Isto é referência anual histórica, não cobertura atual observada.",
                "Microrregião PAM: "+str((contingency.get("pam_microregion") or {}).get("name","N/D"))+"; PAM não identifica cultura no polígono."])
            for item in contingency.get("classes") or []:
                row=("  "+str(item.get("label"))+": "+format_ptbr(item.get("area_ha"),2)+" ha — classe histórica MapBiomas")
                if item.get("pam_median_kg_ha") is not None:
                    row+="; PAM mediana "+format_ptbr(item["pam_median_kg_ha"]/1000,2)+" t/ha (2015–2024); produção condicional "+format_ptbr(item.get("conditional_reference_production_t"),2)+" t"
                    bounds=item.get("conditional_reference_production_p05_p95_t") or []
                    if len(bounds)==2:row+="; envelope histórico P05–P95 "+format_ptbr(bounds[0],2)+"–"+format_ptbr(bounds[1],2)+" t"
                    row+=" — estimativa com incerteza não mensurada"
                else:
                    row+="; PAM: "+str(item.get("pam_status","sem série compatível"))
                executive.append(row)
            executive.append(str(contingency.get("uncertainty") or "Incerteza de área MapBiomas e transferência não mensuradas."))
        elif contingency.get("status") not in (None,"BLOQUEADO_ATE_ESGOTAR_SAR"):
            why=str(contingency.get("reason") or contingency.get("status"))
            if contingency.get("stage"):why="etapa="+str(contingency["stage"])+"; "+why
            if contingency.get("detail"):why+="; detalhe="+str(contingency["detail"])
            executive.extend(["", "CONTINGÊNCIA MAPBIOMAS + PAM indisponível: "+why])
        from crop_report_consistency import executive_cover_distribution_lines
        executive.extend(executive_cover_distribution_lines(land,aoi_ha,format_ptbr))
        from crop_report_consistency import experimental_seasonal_sar_classes
        seasonal_sar=experimental_seasonal_sar_classes(land)
        seasonal_audit=land.get("sar_classifier_lemplus") or {}
        executive.append("CLASSIFICADOR SAZONAL SENTINEL-1 LEM+: "+
                         str(seasonal_audit.get("status","N/D"))+
                         "; tentativa na AOI integral="+
                         ("SIM" if seasonal_audit.get("model_call_attempted") else "NÃO")+
                         "; resultado aplicado="+
                         ("SIM" if seasonal_audit.get("result_applied_to_current_aoi") else "NÃO"))
        seasonal_reason=(seasonal_audit.get("reason") or
                         (seasonal_audit.get("acquisition_diagnostic") or {}).get("reason"))
        if seasonal_reason:
            executive.append("  Diagnóstico LEM+: "+str(seasonal_reason)[:220])
        seasonal_acquisition=seasonal_audit.get("acquisition_diagnostic") or {}
        if seasonal_acquisition.get("missing_months"):
            executive.append("  Meses sem pares VV/VH: "+
                             ", ".join(map(str,seasonal_acquisition["missing_months"])))
        if seasonal_sar:
            executive.extend(["", "CLASSIFICAÇÃO SAR EXPERIMENTAL — SAFRA COMPLETA OBSERVADA (não representa cobertura atual)",
                "Safra: "+str(seasonal_sar.get("season") or "N/D")+
                "; Sentinel-1: "+str(seasonal_sar.get("scenes_used") or "N/D")+" cenas; "+
                str(seasonal_sar.get("pixels") or "N/D")+" pixels classificados.",
                "Este resultado de pixels reais é sazonal e experimental; não equivale ao monitoramento atual nem a validação de campo."])
            for item in seasonal_sar["classes"]:
                executive.append("  "+item["class_name"]+": "+format_ptbr(item["area_ha"],2)+
                                 " ha — estimativa com incerteza não mensurada")
            executive.append("Modelo: "+str(seasonal_sar.get("model_id") or "N/D")+
                             "; SHA-256: "+str(seasonal_sar.get("model_sha256") or "N/D"))
            oa=seasonal_sar.get("landcover_overall_accuracy")
            ci=seasonal_sar.get("landcover_overall_accuracy_wilson95")
            crop_oa=seasonal_sar.get("crop_overall_accuracy")
            if isinstance(oa,(int,float)):
                accuracy_line="Acurácia global de uso/cobertura no holdout espacial do treinamento: "+format_ptbr(100*oa,1)+"%"
                if isinstance(ci,(list,tuple)) and len(ci)==2:
                    accuracy_line+=" (IC95% Wilson "+format_ptbr(100*float(ci[0]),1)+"–"+format_ptbr(100*float(ci[1]),1)+"%)"
                if isinstance(crop_oa,(int,float)):
                    accuracy_line+="; acurácia da identificação agrícola no treinamento: "+format_ptbr(100*crop_oa,1)+"%"
                executive.append(accuracy_line)
            executive.append("Acurácias e IC95% do modelo referem-se à avaliação espacial de treinamento, não à incerteza de área desta AOI.")
        executive.append(native_summary)
        national=land.get("national_audit") or {}
        if national:
            executive.append("AUDITORIA NACIONAL — "+str(national.get("current_sar_classification"))+
                             "; incerteza de área de máscara: N/D quando não validada")
            executive.append("Geometria SHA256 e fórmulas disponíveis no JSON de auditoria.")
        orbital=land.get("recent_sar_cover") or {}
        executive.append("TRIAGEM ORBITAL SAR ATUAL — "+str(orbital.get("status","N/D")))
        if orbital.get("status")=="SAR_REAL_EXPERIMENTAL_CANDIDATES":
            executive.append("Cenas VV/VH realmente lidas: "+str(orbital.get("scene_count"))+
                             "; aquisição mais recente UTC: "+str(orbital.get("latest_acquisition_utc")))
            for name,ha in (orbital.get("areas_ha") or {}).items():
                executive.append("  "+name+": "+format_ptbr(ha,2)+" ha — sem acurácia calibrada")
            executive.append("Mapa de radar atual: "+str(orbital.get("raster_path")))
            executive.append("ATENÇÃO: candidatos SAR não são áreas de soja/nativa confirmadas; não somar ao mapa anual.")
        else:
            executive.append("SAR atual N/D — "+str(orbital.get("reason","cenas/pixels indisponíveis"))[:190])
        executive.extend(["", "HISTÓRICO DE USO AGRÍCOLA — 150 DIAS",
            "Série experimental de candidatos a área cultivada baseada em Sentinel-1 VV/VH; não confirma cultura nem substitui validação de campo."])
        history=orbital.get("history_by_date") if isinstance(orbital.get("history_by_date"),list) else []
        if orbital.get("status")=="SAR_REAL_EXPERIMENTAL_CANDIDATES" and history:
            from datetime import datetime, timezone, timedelta
            utc_minus_3=timezone(timedelta(hours=-3))
            for point in history:
                instant=point.get("as_of_utc")
                if instant:
                    try:date_label=datetime.fromisoformat(str(instant).replace("Z","+00:00")).astimezone(utc_minus_3).strftime("%d/%m/%Y %H:%M BRT")
                    except (ValueError,TypeError):date_label=str(instant)
                else:date_label="Data N/D"
                if point.get("status")=="CANDIDATOS_EXPERIMENTAIS":
                    executive.append("  "+date_label+": "+
                        format_ptbr(point.get("cultivated_candidate_area_ha"),2)+
                        " ha de candidato agrícola no recorte temporal até a data; " +
                        str(point.get("scene_count"))+" cenas / "+
                        format_ptbr(point.get("span_days"),1)+" dias; cultura N/D; incerteza não quantificada.")
                else:
                    executive.append("  "+date_label+": sem área candidata calculável — "+
                        str(point.get("reason") or point.get("status") or "série insuficiente")[:180])
            executive.append("Área candidata por data: classificação experimental em janela móvel de até 150 dias; classes não são hectares agrícolas confirmados e os pontos não constituem observações de campo independentes.")
        else:
            executive.append("N/D — não houve série de cenas SAR compatível e legível para calcular candidatos experimentais por data.")
        # A mostly urban classification in an operator-supplied agricultural AOI
        # is a QA anomaly, not permission to erase real class-24 pixels or
        # relabel them as crops from the filename or historical location.
        urban_ha=sum(float(item.get("area_ha") or 0) for item in classes
                     if str(item.get("class_name") or "") == "Infraestrutura Urbana")
        if aoi_ha>0 and urban_ha/aoi_ha>=0.5:
            executive.append(
                "ALERTA DE CONSISTÊNCIA CARTOGRÁFICA: "+
                format_ptbr(urban_ha,2)+" ha ("+
                format_ptbr(100*urban_ha/aoi_ha,2)+
                "%) classificados como Infraestrutura Urbana no MapBiomas anual. "+
                "Verificar posicionamento/CRS do KMZ, mapa TIFF, classe 24, ano da imagem e "+
                "interseção de pixels antes de atribuir uso agrícola; nenhuma classe foi alterada automaticamente.")
        second_detections=land.get("second_crop_detection") if isinstance(land.get("second_crop_detection"),list) else []
        for detection in second_detections:
            try:
                detection_area=float(detection.get("overlap_area_ha") or 0)
            except (TypeError,ValueError):
                detection_area=0
            if detection_area>0:
                executive.append("Detecção complementar experimental de "+str(detection.get("crop"))+
                                 ": "+format_ptbr(detection_area,2)+" ha de sobreposição (safra 2; não somar à área total da propriedade).")
        age_assessment=land.get("probable_crop_age") if isinstance(land.get("probable_crop_age"),dict) else {}
        age_value=age_assessment.get("months") if (age_assessment.get("status")=="validated" and
                   age_assessment.get("freshness_status")=="cenas_recentes_identificadas") else None
        try:
            age_value=float(age_value)
            age_text=(format_ptbr(age_value,1)+" meses" if age_value>=0 else
                      "INDISPONÍVEL — sem estimativa fenológica SAR validada")
        except (TypeError,ValueError):
            age_text="INDISPONÍVEL — sem estimativa fenológica SAR validada"
        health=land.get("apparent_phytosanitary_state") if isinstance(land.get("apparent_phytosanitary_state"),dict) else {}
        health_value=str(health.get("category","")).strip().casefold()
        health_options={"bom":"Bom","médio":"Médio","medio":"Médio","ruim":"Ruim"}
        health_text=(health_options[health_value] if (health.get("status")=="validated" and
                     health.get("freshness_status")=="cenas_recentes_identificadas" and health_value in health_options) else
                     "INDISPONÍVEL — opções: Bom, Médio ou Ruim")
        forecast=land.get("yield_forecast") if isinstance(land.get("yield_forecast"),dict) else {}
        interval=forecast.get("prediction_interval_t_ha") if isinstance(forecast.get("prediction_interval_t_ha"),dict) else {}
        unit_conversion_audit=None
        productivity_text="BLOQUEADA — modelo/validação científica insuficientes"
        production_text="INDISPONÍVEL — área da cultura no polígono não quantificada"
        from experimental_audit import eligible_experimental_yield, audit_yield_forecast
        yield_is_experimental=eligible_experimental_yield(forecast)
        if forecast.get("status")=="previsao_validada" or yield_is_experimental:
            try:
                value=float(forecast["yield_t_ha"]); low=float(interval["lower"]); high=float(interval["upper"])
                if value>=0 and 0<=low<=value<=high:
                    from agricultural_yield_units import probable_productivity, probable_production
                    crop_name=forecast.get("crop", "")
                    product=probable_productivity(value,crop_name)
                    unit_conversion_audit=product["conversion"]
                    low_unit=probable_productivity(low,crop_name)
                    high_unit=probable_productivity(high,crop_name)
                    basis=" (sacas de 60 kg)" if product["unit"]=="sacas/ha" else ""
                    productivity_text=(format_ptbr(product["value"],2)+" "+product["unit"]+basis+
                        " ("+format_ptbr(low_unit["value"],2)+"–"+format_ptbr(high_unit["value"],2)+" "+product["unit"]+")")
                    crop_area=forecast.get("crop_area_ha")
                    if crop_area is not None and float(crop_area)>0:
                        total=probable_production(value,crop_area,crop_name)
                        lower_total=probable_production(low,crop_area,crop_name)["value_t"]
                        upper_total=probable_production(high,crop_area,crop_name)["value_t"]
                        production_text=(format_ptbr(total["value_t"],2)+" t no polígono ("+
                            format_ptbr(lower_total,2)+"–"+format_ptbr(upper_total,2)+" t), área da cultura: "+
                            format_ptbr(crop_area,2)+" ha")
                        if total["sacks"] is not None:
                            production_text+="; equivalente a "+format_ptbr(total["sacks"],2)+" sacas de 60 kg"
            except (KeyError,TypeError,ValueError):
                productivity_text="BLOQUEADA — intervalo preditivo ausente ou inválido"
        if yield_is_experimental:
            productivity_text="ESTIMATIVA EXPERIMENTAL (não homologada) — "+productivity_text
            if not production_text.startswith("INDISPONÍVEL"):
                production_text="ESTIMATIVA EXPERIMENTAL (não homologada) — "+production_text
        crop_labels=sorted({str(k) for k in ((land.get("yield_forecast") or {}).get("crop"),)
                            if k and str(k).strip()})
        crop_labels += sorted({str(item.get("class_name")).replace("Lavoura de ","") for item in classes
                               if str(item.get("class_name") or "").startswith("Lavoura de ")})
        crop_labels=list(dict.fromkeys(crop_labels))
        executive.extend(["","PAINEL EXECUTIVO — PREVISÃO DE SAFRAS",
                          "Tipo de cultivo: "+("; ".join(crop_labels) if crop_labels else "N/D — cultura não identificada"),
                          "Idade provável da lavoura: "+age_text,
                          "Estado fitossanitário aparente: "+health_text,
                          "Produtividade estimada no momento dessa análise: "+productivity_text,
                          "Produção provável: "+production_text,
                          "Estado aparente é um sinal remoto inespecífico; não é diagnóstico de doença ou praga.",
                          "Carbono nativo: calculado separadamente na aba de formações nativas."])
        audit=["AUDITORIA TÉCNICA — USO DO SOLO, CULTURAS E FONTES",
               "Método: "+str(land.get("method","não informado")),
               "Prioridade de fontes: "+str(land.get("priority","não informada")),
               "Incerteza da área/classificação: "+str(land.get("area_uncertainty") or "não quantificada"),
               "Fonte MapBiomas: "+str(land.get("mapbiomas_source","não disponível")),
               "Avisos:"]+[str(x) for x in land.get("warnings",[]) or ["nenhum"]]
        audit.extend(["","Classes, fontes e metadados:"])
        audit.extend(["", "Proveniência dos indicadores executivos:",
                      json.dumps({"agriculture_historical_contingency":contingency,
                                  "probable_crop_age":age_assessment,
                                  "apparent_phytosanitary_state":health,
                                  "yield_forecast":forecast,
                                  "experimental_seasonal_sar_classification":seasonal_sar,
                                  "yield_calculation_trace":audit_yield_forecast(forecast,analysis_id=self.project.get("analysis_run_id")),
                                  "yield_unit_conversion":unit_conversion_audit},ensure_ascii=False,indent=2,default=str)])
        for item in classes:
            audit.append(json.dumps(item,ensure_ascii=False,sort_keys=True,default=str))
        validation=land.get("validation")
        audit.extend(["","Validação e métricas:",json.dumps(validation,ensure_ascii=False,indent=2,default=str) if validation else "Nenhuma inferência SAR validada foi usada."])
        audit.extend(["","Distribuições originais das fontes:",json.dumps(land.get("original_source_distributions",[]),ensure_ascii=False,indent=2,default=str)])
        self._crop_monitoring_base_report="\n".join(executive)
        self._crop_monitoring_audit_base="\n".join(audit)
        self._set(self.crop_res,self._crop_monitoring_base_report)
        self._set(self.crop_audit,self._crop_monitoring_audit_base)
        generation=self._weather_query_generation
        analysis_id=self.project.get("analysis_run_id")
        def start_weather_if_current():
            if (generation==self._weather_query_generation
                and analysis_id==self.project.get("analysis_run_id")
                and self.gdf is not None):
                self.query_crop_weather()
        self.after(100,start_weather_if_current)

    def query_crop_weather(self):
        """Retrieve actual weather asynchronously; executive summary and audit remain separate."""
        if self.gdf is None:
            return messagebox.showwarning("Clima","Carregue primeiro o perímetro da área.")
        try:
            geo=self.gdf.to_crs("EPSG:4326")
            point=geo.geometry.union_all().centroid if hasattr(geo.geometry,"union_all") else geo.unary_union.centroid
            lat,lon=float(point.y),float(point.x)
        except Exception as exc:
            return messagebox.showwarning("Clima","Não foi possível determinar o centroide: "+str(exc))
        self._weather_query_generation+=1
        query_id=self._weather_query_generation
        analysis_id=self.project.get("analysis_run_id")
        base_report=getattr(self,"_crop_monitoring_base_report","")
        audit_base=getattr(self,"_crop_monitoring_audit_base","")
        self._set(self.crop_res,(base_report+"\n\n" if base_report else "")+
                  "Consultando meteorologia em segundo plano…\n"
                  "NASA POWER: histórico recente em grade, não medição local.\n"
                  "CPTEC/INPE: previsão futura.")
        self._set(self.crop_audit,(audit_base+"\n\n" if audit_base else "")+
                  "Consulta meteorológica pendente; resultados detalhados aparecerão aqui.")
        def worker():
            from inmet_weather_client import weather_executive_lines
            power_summary=None
            forecast_summary=None
            details=["CLIMA DINÂMICO — PROPRIEDADE / MONITORAMENTO AGRÍCOLA",
                     f"Centroide WGS84: {lat:.5f}, {lon:.5f}"]
            try:
                from agricultural_weather import fetch_daily_weather,summarize_weather
                weather=fetch_daily_weather(lat,lon,days=90)
                summary=summarize_weather(weather)
                power_summary=summary
                details.extend(["","NASA POWER — DADOS DIÁRIOS DA GRADE",
                                "Fonte: "+weather["source_url"],
                                "Período: "+weather["start"]+" a "+weather["end"],
                                "Consulta UTC: "+weather["retrieved_utc"],
                                "Dias com temperatura: "+str(summary["temperature_days"]),
                                "Temperatura média (°C): "+str(summary["mean_temperature_c"]),
                                "Precipitação acumulada (mm): "+str(summary["rain_mm"]),
                                "Graus-dia base 10 °C (°C dia): "+str(summary["gdd_c_day"]),
                                "GDD descritivo; não parametrizado por cultura ou cultivar."])
            except Exception as exc:
                details.append("NASA POWER: INDISPONÍVEL — "+str(exc))
            try:
                from cptec_forecast_client import forecast_by_coordinates
                forecast=forecast_by_coordinates(lat,lon)
                forecast_summary=forecast
                details.extend(["","CPTEC/INPE — PREVISÃO POR COORDENADAS",
                                "Fonte: "+forecast["source_url"],
                                "Consulta UTC: "+forecast["retrieved_utc"],
                                "Períodos retornados: "+str(len(forecast["periods"]))])
                for period in forecast["periods"][:7]:
                    details.append("  "+str(period))
            except Exception as exc:
                details.append("CPTEC/INPE: INDISPONÍVEL — "+str(exc))
            details.extend(["","INMET: o endpoint público testado não retornou observações acessíveis para a estação mais próxima.",
                            "BDMEP histórico: não consultado automaticamente; exportação pública exige solicitação.",
                            "Fenologia, vigor, estresse fitossanitário e produtividade não são inferidos só da meteorologia.",
                            "NASA POWER e CPTEC representam produtos distintos; não se calcula média ponderada sem datas e variáveis comparáveis e pesos validados.",
                            "Estimativas de carbono nativo permanecem independentes."])
            dashboard=weather_executive_lines(
                {"status":"indisponivel","reason":"histórico local de estação não disponível; painel usa NASA POWER em grade e CPTEC/INPE para previsão"},
                power_summary,forecast_summary,format_ptbr)
            executive=([base_report,""] if base_report else [])+dashboard
            audit_text=([audit_base,""] if audit_base else [])+details
            # Consolidated crop identification + automatic Sentinel-1 vigor +
            # calibrated yield forecast (experimental). Never blocks the panel.
            try:
                from crop_monitoring_forecast import monitoring_forecast
                land=getattr(self,"_last_land",None) or {}
                fc_lines,fc_audit=monitoring_forecast(self.gdf.copy(),land)
                # Do not keep a stale "BLOQUEADA" headline after the calibrated
                # experimental panel has returned a numeric result. Carbon
                # presentation and native-stock routines are untouched.
                panel_results = [(crop_name, item) for crop_name, item in fc_audit.get("crops", {}).items()
                                 if isinstance(item, dict) and item.get("forecast_model") == "panel"
                                 and isinstance(item.get("forecast"), dict)
                                 and "production" in item["forecast"]]
                if len(panel_results) == 1:
                    crop_name, panel_entry = panel_results[0]
                    panel = panel_entry["forecast"]
                    p = panel["production"]
                    fields = p.get("fields_kg_ha", {})
                    v = next(iter(fields.values()), None)
                    t = p.get("production_t")
                    if isinstance(v, dict) and isinstance(t, dict):
                        from crop_report_consistency import remove_superseded_yield_placeholders
                        executive = remove_superseded_yield_placeholders(executive)
                        executive += [
                            "Produtividade estimada no momento dessa análise: ESTIMATIVA EXPERIMENTAL regional — "
                            + format_ptbr(v["median"] / 1000, 2) + " t/ha (intervalo 90%: "
                            + format_ptbr(v["p05"] / 1000, 2) + "–"
                            + format_ptbr(v["p95"] / 1000, 2) + " t/ha)"
                            + (("; equivalente a " + format_ptbr(v["median"] / 60, 2)
                                + " sacas/ha (60 kg/saca; intervalo 90%: "
                                + format_ptbr(v["p05"] / 60, 2) + "–"
                                + format_ptbr(v["p95"] / 60, 2) + " sacas/ha)")
                               if str(crop_name).strip().casefold() == "soja" else "")
                            + (("; incerteza relativa (intervalo preditivo 90%, base mediana): -"
                                + format_ptbr(100 * (v["median"] - v["p05"]) / v["median"], 1)
                                + "% / +" + format_ptbr(100 * (v["p95"] - v["median"]) / v["median"], 1) + "%")
                               if str(crop_name).strip().casefold() == "soja" and v["median"] > 0
                               else ("; incerteza relativa: N/D (mediana igual a zero)"
                                     if str(crop_name).strip().casefold() == "soja" else "")),
                            "Produção provável: CENÁRIO EXPERIMENTAL CONDICIONAL sobre área cartográfica MapBiomas 2025 (assumindo área e cultura mantidas na safra projetada) — "
                            + format_ptbr(t["median"], 2) + " t (intervalo 90%: "
                            + format_ptbr(t["p05"], 2) + "–"
                            + format_ptbr(t["p95"], 2) + " t)",
                            "Nota: a área de 2025 é hipótese de cenário, NÃO comprova hectares de soja plantados/colhidos em 2027; "
                            "quantis de produção não abrangem o erro de classificação da máscara agrícola.",
                            "Limite: classe MapBiomas anual, não confirmação de plantio atual; "
                            "incertezas de classificação, manejo e transferência espacial não necessariamente quantificadas."]
                executive+=fc_lines
                audit_text+=["","PREVISÃO DE SAFRA — AUDITORIA",json.dumps(fc_audit,ensure_ascii=False,indent=2,default=str)]
            except Exception as exc:
                executive+=["","Previsão de safra: INDISPONÍVEL — "+type(exc).__name__+": "+str(exc)[:200]]
            def present():
                if query_id!=self._weather_query_generation or analysis_id!=self.project.get("analysis_run_id"):
                    return
                self._set(self.crop_res,"\n".join(executive))
                self._set(self.crop_audit,"\n".join(audit_text))
            self.after(0,present)
        threading.Thread(target=worker,daemon=True).start()

    def _sources(self):
        f=self.tabs[4]; ttk.Label(f,text="Rastreabilidade metodológica",style="H.TLabel").pack(anchor="w")
        ttk.Button(f,text="RESUMIR INVENTÁRIO (DAP + ÁREA BASAL)",command=self.summarize_inventory_ui).pack(anchor="w",pady=(6,2))
        ttk.Button(f,text="AMPLIAR BIBLIOTECA — INSTITUIÇÕES, PNLA E SINAFLO",command=self.harvest_official_inventory_ui).pack(anchor="w",pady=2)
        ttk.Label(f,text="Busca bases abertas institucionais e oficiais, baixa recursos do REDAPE e do Sinaflor e abre o PNLA para localizar estudos públicos por processo. Inventários privados só entram no último nível e com margem de erro publicada.",wraplength=1000).pack(anchor="w",pady=(0,6))
        source_box=ttk.Frame(f); source_box.pack(fill="both",expand=True,pady=8)
        self.src=tk.Text(source_box,height=24,wrap="word",yscrollcommand=lambda *a:source_scroll.set(*a))
        source_scroll=ttk.Scrollbar(source_box,orient="vertical",command=self.src.yview)
        self.src.pack(side="left",fill="both",expand=True); source_scroll.pack(side="right",fill="y")
        self._bind_text_scroll(self.src)
        txt=("REGRAS DO MOTOR\n• MEDIDO: derivado diretamente do inventário/raster fornecido.\n• MODELADO: proxy/equação publicada, identificado com fonte e domínio.\n• NÃO ESTIMADO: quando não existe suporte defensável.\n\n"
             "Raízes vivas: floresta de terras altas usa equação Cairns et al. (1997), BGB=exp(-1,0587+0,8836 ln AGB), quando aplicável; erro residual e transferência não quantificados. Não usar razão fixa global nem aplicar essa equação a savanas/campos/várzeas.\n"
             f"Conversão biomassa→C: 0,47; {SOURCES['protocol']}.\n"
             f"Solo: {SOURCES['soil']}. O produto PronaSolos utilizado tem resolução nativa de 90 m; o programa preserva essa resolução e não faz falso downscaling.\n"
             "Necromassa acima e abaixo do solo: não aplicar alometria. Madeira caída pode mostrar a média direta SFB/IFN por bioma×UF quando disponível, mas a tabela ainda não tem coordenadas nem classe IBGE; fica fora do total da AOI até validação por fitofisionomia. Necromassa subterrânea exige massa seca de raízes mortas por área e profundidade, com parcelas independentes; ORNL DAAC 1116 é evidência limitada a raízes finas (<2 mm), não ao estoque subterrâneo total.\n"
             "Serrapilheira: Tapajós usa referência de massa seca do estoque no piso florestal, independente da AGB/SAR e restrita à fitofisionomia/localidade compatíveis. Fora desse domínio, só estoque gravimétrico ou calibração massa–profundidade local; queda anual e profundidade isolada não são estoque.")
        doc=app_resource("docs/CLASSIFICACAO_SAR_USO_SOLO.md")
        if doc.exists():txt+="\n\n"+doc.read_text(encoding="utf-8")
        # International theses and institutions are valid methodological sources.
        # Bibliography is not a trained SAR classifier and cannot bypass the
        # independent Brazilian per-class validation contract.
        try:
            from agricultural_external_models import CANDIDATES
            txt+="\n\nMODELOS AGRÍCOLAS INTERNACIONAIS E TESES — FONTES CANDIDATAS, NÃO HOMOLOGADAS"
            for candidate in CANDIDATES:
                txt+=("\n• "+candidate["id"]+" | "+candidate["institution"]+" | "
                      +", ".join(candidate["crops"])+" | "+candidate["url"])
            txt+="\nOs métodos internacionais podem ser utilizados com compatibilidade de sensores, domínio e validação brasileira espacial/temporal independente; sem estes requisitos, não declarar cultura específica."
        except Exception as exc:
            txt+="\nCatálogo externo de modelos indisponível: "+str(exc)
        self._set(self.src,txt)

    def harvest_official_inventory_ui(self):
        base=filedialog.askdirectory(title="Escolha a pasta da biblioteca ampliada de inventários")
        if not base:return
        root=Path(base)/"Enform_Verde_Biblioteca_Inventarios"
        self.status.set("Consultando REDAPE e Sinaflor; abrindo pesquisa pública do PNLA…")
        self._set(self.src,"Coleta em andamento. Esta janela continuará responsiva.\n\nPrioridade: parcelas georreferenciadas abertas de instituições reconhecidas; depois inventários institucionais totalizados com erro documentado; dados oficiais do IFN/SFB e Sinaflor no mesmo nível de origem oficial; por último, inventários privados de licenciamento somente com autorização e margem de erro publicada.")
        webbrowser.open(PNLA_PORTAL)
        def collect():
            results={}
            errors={}
            for name,fn,folder in (("REDAPE",harvest_redape,"01_REDAPE_Embrapa"),("SINAFLO",harvest_sinaflor,"02_SINAFLO_IBAMA")):
                try:results[name]=fn(root/folder)
                except Exception as exc:errors[name]=f"{type(exc).__name__}: {exc}"
            def finish():
                lines=["BIBLIOTECA DE INVENTÁRIOS — COLETA DE FONTES OFICIAIS",""]
                for name,manifest in results.items():
                    items=manifest.get("resources",[])
                    downloaded=sum(1 for x in items if x.get("download_status")=="baixado")
                    lines += [f"{name}: {len(items)} recursos catalogados; {downloaded} baixados."]
                    tiers={}
                    for item in items:
                        tier=item.get("evidence_tier","registro_para_triagem")
                        tiers[tier]=tiers.get(tier,0)+1
                    lines += [f"  Triagem: {tiers}"]
                for name,error in errors.items():lines += [f"{name}: falha na coleta — {error}"]
                lines += ["","HIERARQUIA DE USO"]
                lines += [f"{x['rank']}. {x['label']}: {x['description']}" for x in SOURCE_HIERARCHY]
                lines += ["","Nenhum arquivo foi automaticamente promovido a calibração ou cálculo. Confira parcela/unidade amostral, georreferenciamento, data, fitofisionomia, método, licença e incerteza."]
                lines += ["Inventários privados de licenciamento exigem acesso autorizado e margem de erro publicada; sem isso ficam fora dos cálculos."]
                lines += ["","Repositórios institucionais para triagem complementar:"]
                lines += [f"{x['institution']}: {x['url']} — {x['method']}" for x in INSTITUTIONAL_PORTALS]
                lines += ["","Arquivos e manifestos salvos em:",str(root)]
                self._set(self.src,"\n".join(lines))
                self.status.set("Coleta de catálogos concluída.")
                messagebox.showinfo("Biblioteca de inventários",f"Coleta concluída. Consulte os manifestos e arquivos em:\n{root}")
            self.after(0,finish)
        threading.Thread(target=collect,daemon=True).start()

    def summarize_inventory_ui(self):
        src=filedialog.askopenfilename(title="Selecione CSV harmonizado de inventário",filetypes=[("CSV","*.csv"),("Todos","*.*")])
        if not src:return
        try:
            result=summarize_inventory_csv(src)
            dest=filedialog.asksaveasfilename(title="Salvar resumo estrutural",defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")])
            if not dest:return
            wb=Workbook(); ws=wb.active; ws.title="Por inventário"
            summaries=result["inventory_summary"]
            if not summaries:raise ValueError("Nenhuma árvore viva com DAP válido foi encontrada.")
            ws.append(list(summaries[0]))
            for row in summaries:ws.append([row.get(k) for k in summaries[0]])
            wp=wb.create_sheet("Por parcela"); plots=result["plot_summary"]
            if plots:
                wp.append(list(plots[0]))
                for row in plots:wp.append([row.get(k) for k in plots[0]])
            wm=wb.create_sheet("Método e limites")
            wm.append(["Item","Descrição"]); wm.append(["Método",result["method"]])
            for limitation in result["limitations"]:wm.append(["Limite",limitation])
            wb.save(dest)
            messagebox.showinfo("Inventário",f"Resumo salvo. Métricas de campo sem pareamento SAR:\n{dest}")
        except Exception as e:messagebox.showerror("Inventário",str(e))
    def _bind_text_scroll(self,w):
        """Make disabled long-form reports scroll by wheel as well as scrollbar."""
        def wheel(event):
            if getattr(event,"num",None)==4: step=-3
            elif getattr(event,"num",None)==5: step=3
            else:
                delta=int(getattr(event,"delta",0) or 0)
                if not delta:return "break"
                step=-max(1,abs(delta)//120)*(1 if delta>0 else -1)
            w.yview_scroll(step,"units")
            return "break"
        w.bind("<MouseWheel>",wheel)
        w.bind("<Button-4>",wheel); w.bind("<Button-5>",wheel)

    def _set(self,w,t):
        w.config(state="normal"); w.delete("1.0","end"); w.insert("1.0",t); w.config(state="disabled")
        try:w.yview_moveto(0.0)
        except tk.TclError:pass
    def _reset_analysis_state(self,keep_geometry=False):
        """Invalida integralmente qualquer resultado derivado da consulta anterior."""
        self._analysis_generation+=1
        self._weather_query_generation+=1
        self._crop_monitoring_base_report=""
        self._crop_monitoring_audit_base=""
        if hasattr(self,"crop_res"):
            self._set(self.crop_res,"Aguardando nova análise.")
        if hasattr(self,"crop_audit"):
            self._set(self.crop_audit,"A auditoria anterior foi descartada. Aguardando nova análise.")
        self._ibge_generation+=1; self._ibge_pending=False; self._pending_execute=False
        old_vector=self.project.get("vector")
        self.project={"version":APP_VERSION}
        if old_vector and keep_geometry:self.project["vector"]=old_vector
        if not keep_geometry:
            self.gdf=None
            if hasattr(self,"aoi_area_display"):self.aoi_area_display.set("Aguardando perímetro.")
        self._map_generation+=1
        self._satellite_map_visible=False
        if hasattr(self,"map_status"):
            self.map_status.set("Aguardando imagem de referência para a nova AOI.")
        if getattr(self,"_map_refresh_job",None) is not None:
            try:self.after_cancel(self._map_refresh_job)
            except Exception:pass
            self._map_refresh_job=None
        if hasattr(self,"map_canvas"):
            self.map_canvas.delete("all")
            self.map_canvas.create_text(20,20,anchor="nw",text="Carregue CAR, CCIR ou vetor e visualize o satélite com o polígono.",fill="#455")
        self.soil_raster=None
        self.sar_paths=[]
        self.land_use_config=None
        if hasattr(self,"land_use_state"):self.land_use_state.set("Sem modelo SAR validado. Fallback: IBGE → MapBiomas.")
        self.inv=None
        self.active_source=None
        self.active_input_id=None
        self.biome.set(""); self.phys.set("")
        for widget_name in ("remote_text","res","crop_res"):
            w=getattr(self,widget_name,None)
            if w is not None:self._set(w,"")
        if hasattr(self,"spatial_text"):self._set(self.spatial_text,"Nova entrada recebida. Resultados anteriores foram descartados.")
        self.status.set("Estado anterior descartado. Preparando nova consulta.")
        if hasattr(self,"vector_status") and not keep_geometry:self.vector_status.set("Nenhum arquivo vetorial carregado.")
        self.update_idletasks()

    def clear_research(self):
        """Clear the inquiry and ignore any late response from its worker thread."""
        self._reset_analysis_state(keep_geometry=False)
        self.car.set(""); self.ccir.set("")
        self._analysis_running=False
        for name in ("pipeline_btn","global_execute_btn"):
            button=getattr(self,name,None)
            if button is not None:
                try:button.state(["!disabled"])
                except tk.TclError:pass
        if hasattr(self,"spatial_text"):
            self._set(self.spatial_text,"Pesquisa apagada. Carregue um novo perímetro.")
        self.status.set("Pesquisa apagada. Carregue um novo perímetro para iniciar outra análise.")

    def car_lookup(self):
        self._reset_analysis_state()
        try:
            self.status.set("Consultando SICAR..."); self.update_idletasks(); self.gdf=resolve_car(self.car.get()); self.active_source="CAR"; self.active_input_id=self.car.get().strip().upper(); self.ccir.set(""); self._show_geom("SICAR")
        except Exception as e: self.status.set("CAR não resolvido."); messagebox.showwarning("SICAR",str(e))
    def ccir_lookup(self):
        self._reset_analysis_state()
        try:
            self.status.set("Consultando SIGEF pelo código do CCIR..."); self.update_idletasks()
            self.gdf=resolve_ccir_sigef(self.ccir.get()); self.active_source="CCIR"; self.active_input_id=re.sub(r"\D","",self.ccir.get()); self.car.set(""); self._show_geom("CCIR / SIGEF")
        except Exception as e:
            self.status.set("CCIR/SIGEF não resolvido."); messagebox.showwarning("CCIR / SIGEF",str(e))

    def pick_vector(self):
        p=filedialog.askopenfilename(title="Selecionar limite da propriedade",filetypes=[("Vetores","*.kml *.kmz *.geojson *.json *.shp *.gpkg"),("Todos","*.*")])
        if not p:return
        self._reset_analysis_state()
        self.vector_status.set(f"Selecionado: {Path(p).name} — validando arquivo…"); self.status.set("Validando arquivo vetorial..."); self.update_idletasks()
        try:
            self.gdf=read_vector(p); self.project["vector"]=p; self.active_source="VECTOR"; self.active_input_id=str(Path(p).resolve()); self.car.set(""); self.ccir.set("")
            self.vector_status.set(f"Upload concluído ✓  {Path(p).name}  |  {len(self.gdf)} feição(ões) vetorial(is) carregada(s).")
            self.nb.select(self.tabs[1]); self.update_idletasks()
            self._show_geom(Path(p).name); self.vector_status.set(f"Upload concluído ✓  {Path(p).name}  |  {len(self.gdf)} feição(ões) carregada(s).")
        except Exception as e:
            self.gdf=None; self.vector_status.set(f"Upload não concluído — {Path(p).name}: {e}"); self.status.set("Falha ao carregar vetor."); messagebox.showerror("Vetor não carregado",f"O arquivo não foi carregado; nenhuma análise foi iniciada.\n\nArquivo: {Path(p).name}\n\nMotivo: {e}")
    def _schedule_offline_map_fit(self,label):
        """Load Sentinel-2/CBERS-4A imagery; keep only the AOI outline on failure."""
        self._map_extent_factor=1.36
        self._satellite_map_visible=False
        self._draw_aoi_outline(label + " — carregando camada online")
        self._map_provider="ONLINE_PENDING"
        # Network requests run in a worker; the cartographic IBGE raster is not
        # a satellite-background fallback.
        self.show_google_map(refresh=False,prefer_public=False)
        # The AOI outline has already been rendered; do not schedule an undefined callback.

    def _show_geom(self,src):
        m=geom_metrics(self.gdf); self.project["geometry_metrics"]=m
        if hasattr(self,"aoi_area_display"):
            from property_physiognomy_display import equal_area_aoi_ha
            self.aoi_area_display.set(f"{format_ptbr(equal_area_aoi_ha(self.gdf),2)} ha (EPSG:6933; base dos percentuais)")
        if hasattr(self,"ibge_phys_display"):
            self.ibge_phys_display.set("Aguardando mapeamento da vegetação nativa; mapa potencial IBGE não confirma presença atual.")
        self._set(self.spatial_text,f"Perímetro: {src}\nÁrea de referência (EPSG:6933): {format_ptbr(m['area_ha'],2)} ha\nÁrea UTM (apenas diagnóstico): {format_ptbr(m['area_utm_ha'],2)} ha — EPSG:{m['utm_epsg']}\nCentroide: {format_ptbr(m['centroid'][1],6)}; {format_ptbr(m['centroid'][0],6)}\nPercentuais e estoques da AOI utilizam a área equivalente EPSG:6933.\n\nPerímetro válido para recorte espacial.")
        # The basemap is a visualization only. An offline renderer, satellite
        # provider or Tk canvas failure must never prevent the scientific AOI
        # setup from launching the independent IBGE diagnostic worker.
        try:
            self._schedule_offline_map_fit(f"Perímetro carregado: {src} — mapa vetorial offline")
        except Exception as exc:
            self.project["map_preview_error"] = f"{type(exc).__name__}: {exc}"
            try:
                self._draw_aoi_outline("Perímetro carregado — prévia cartográfica indisponível")
            except Exception:
                pass
        self.status.set(f"Perímetro carregado: {src}; diagnóstico IBGE em segundo plano."); self.update_idletasks()
        self._ibge_generation+=1; generation=self._ibge_generation; geometry=self.gdf.copy(); self._ibge_pending=True
        def worker():
            try: self._ibge_queue.put((generation,"ok",diagnose_ibge(geometry)))
            except Exception as e: self._ibge_queue.put((generation,"error",str(e)))
        threading.Thread(target=worker,name="EnformIBGE",daemon=True).start()
        self.after(100,self._poll_ibge)
    def _poll_ibge(self):
        try:generation,kind,value=self._ibge_queue.get_nowait()
        except queue.Empty:
            if self.winfo_exists():self.after(120,self._poll_ibge)
            return
        if generation!=self._ibge_generation:return
        self._ibge_pending=False
        if kind!="ok":
            self.project["ibge_diagnosis_error"]=value
            if hasattr(self,"ibge_phys_display"):
                self.ibge_phys_display.set("Não determinada — falha na consulta ao mapa oficial IBGE: "+str(value)[:160])
            self.status.set("Perímetro carregado; diagnóstico IBGE pendente.")
            self._set(self.spatial_text,self.spatial_text.get("1.0","end").strip()+"\n\nDiagnóstico IBGE pendente: "+str(value))
            if self._pending_execute:self._pending_execute=False; self.after(0,self.execute)
            return
        d=value; self.project["ibge_diagnosis"]=d
        if d.get("biomas"):self.biome.set(d["biomas"][0][0])
        primary=primary_ibge_physiognomy(d)
        if primary:self.phys.set(primary)
        elif d.get("vegetacao_error"):self.phys.set("Não determinada — "+d["vegetacao_error"][:120])
        if hasattr(self,"ibge_biome_display"):
            self.ibge_biome_display.set(self.biome.get() or "Não determinado")
        # IBGE describes potential vegetation, never current cover.
        if hasattr(self,"ibge_phys_display") and not self.project.get("native_carbon"):
            potential="; ".join(
                str(x.get("name") or "não determinada")+" — "+
                format_ptbr(float(x.get("area_ha",0)),2)+" ha"
                for x in d.get("regioes_fitoecologicas",[]) if x.get("name"))
            self.ibge_phys_display.set(
                "Cobertura nativa ATUAL: aguardando confirmação por SAR.\n"+
                ("Fitofisionomia POTENCIAL IBGE (não comprova presença atual): "+
                 potential if potential else "Fitofisionomia potencial IBGE: não determinada."))
        btxt="; ".join(f"{n}: {format_ptbr(ha,2)} ha ({format_ptbr(pct,2)}%)" for n,ha,pct in d.get("biomas",[]))
        code_txt="\n".join(f"  código {x.get('code') or 'N/D'} — {x['name']}: {format_ptbr(x['area_ha'],2)} ha ({format_ptbr(x['percent'],2)}%)" for x in d.get("regioes_fitoecologicas",[]))
        ibge_lines=["Bioma(s) IBGE: "+(btxt or "não determinado")]+ibge_area_summary_lines(d)
        if code_txt:ibge_lines.append("Código(s) das regiões fitoecológicas (IBGE):\n"+code_txt)
        current=self.spatial_text.get("1.0","end").strip()
        self._set(self.spatial_text,current+"\n\n"+"\n".join(ibge_lines))
        self.status.set("Perímetro e diagnóstico IBGE concluídos." if not d.get("vegetacao_error") else "Bioma IBGE concluído; fitofisionomia não classificada — modelos que exigem classe IBGE ficam bloqueados; apenas rotas independentes da classe podem prosseguir.")
        if self._pending_execute:self._pending_execute=False; self.after(0,self.execute)
    def pick_soil(self):
        p=filedialog.askopenfilename(filetypes=[("GeoTIFF","*.tif *.tiff")])
        if p:self.soil_raster=p; self.status.set("Raster de COS selecionado.")
    def auto_soil(self):
        if self.gdf is None:return messagebox.showwarning("Solo","Carregue/resolva o perímetro primeiro.")
        try:self.status.set("Baixando COS Embrapa..."); self.update_idletasks(); self.soil_raster=try_download_embrapa_soc(self.gdf); self.status.set("COS Embrapa obtido.")
        except Exception as e:self.status.set("COS automático indisponível."); messagebox.showwarning("Solo Embrapa",str(e))
    def execute(self,event=None):
        if self._analysis_running:
            self.status.set("Análise já em execução; aguarde.")
            return
        if self._ibge_pending:
            self._pending_execute=True; self.status.set("A AOI está carregada. A análise começará assim que o diagnóstico territorial do IBGE terminar.")
            return
        car=self.car.get().strip().upper(); ccir=re.sub(r"\D","",self.ccir.get())
        if car and ccir:return messagebox.showwarning("Identificação","Informe CAR ou CCIR, não ambos. Para outro perímetro, carregue um arquivo vetorial.")
        if car and (self.active_source!="CAR" or self.active_input_id!=car):
            self._reset_analysis_state(); self.status.set("Consultando automaticamente o CAR no SICAR…"); self.update_idletasks()
            try:
                self.gdf=resolve_car(car); self.active_source="CAR"; self.active_input_id=car; self.ccir.set(""); self._show_geom("SICAR — consulta automática")
            except Exception as e:
                self.status.set("Consulta automática CAR/SICAR não concluída."); return messagebox.showwarning("SICAR",str(e))
        elif ccir and (self.active_source!="CCIR" or self.active_input_id!=ccir):
            self._reset_analysis_state(); self.status.set("Consultando automaticamente CCIR/SNCR e perímetro SIGEF…"); self.update_idletasks()
            try:
                self.gdf=resolve_ccir_sigef(ccir); self.active_source="CCIR"; self.active_input_id=ccir; self.car.set(""); self._show_geom("CCIR/SNCR — SIGEF automático")
            except Exception as e:
                self.status.set("Consulta automática CCIR/SNCR/SIGEF não concluída."); return messagebox.showwarning("CCIR / SIGEF",str(e))
        if self._ibge_pending:
            self._pending_execute=True; self.status.set("Perímetro resolvido. A análise começará após o diagnóstico territorial do IBGE.")
            return
        if self.gdf is None:return messagebox.showwarning("Perímetro necessário","Informe CAR, CCIR ou carregue um arquivo vetorial; depois pressione EXECUTAR ANÁLISE.")
        if self.sar_paths:return self._execute_main(event)
        # Snapshot every Tk variable on the GUI thread before starting the worker.
        land_config=self.land_use_config
        inventory_evidence=(list(self.inventory_evidence_data)
                            if self.inventory_evidence_data is not None else None)
        biodiversity_inventory_records=(list(self.biodiversity_inventory_records)
            if self.biodiversity_inventory_records is not None else None)
        inventory_manifest=(dict(self.inventory_evidence_manifest)
                            if self.inventory_evidence_manifest is not None else None)
        land_ibge=self.ibge_physiognomy_gdf.copy() if self.ibge_physiognomy_gdf is not None else None
        land_field=self.ibge_class_field or "legenda_1"
        gdf=self.gdf.copy(); biome=self.biome.get(); phys=self.phys.get(); token=self.esa_token.get().strip()
        try:
            from analysis_pipeline_contract import geometry_hash
            aoi_hash=geometry_hash(gdf)
        except Exception as exc:
            self.status.set("Falha ao identificar a geometria da AOI.")
            return messagebox.showerror("Análise", "Não foi possível gerar o hash da AOI; análise bloqueada: "+type(exc).__name__)
        edl_token=self.edl_token.get().strip(); edl_user=self.edl_user.get().strip(); edl_password=self.edl_password.get(); cdse_token=self.cdse_token.get().strip()
        cdse_client_id=self.cdse_client_id.get().strip(); cdse_client_secret=self.cdse_client_secret.get().strip()
        self._analysis_generation+=1; run_id=self._analysis_generation
        self._analysis_running=True; self.pipeline_btn.state(["disabled"]); self.global_execute_btn.state(["disabled"])
        self.status.set("Consultando e processando SAR em segundo plano…")
        def worker():
            try:
                reference=land_ibge;reference_field=land_field
                if reference is None:
                    try:reference,reference_field=load_ibge_land_use_reference(gdf)
                    except Exception:pass
                land=run_land_use(gdf,Path.home()/".enform_verde"/"uso_solo"/uuid.uuid4().hex[:12],land_config,ibge=reference,ibge_field=reference_field,sar_paths=getattr(self,'sar_paths',None))
                options={"offline_token":token,"edl_user":edl_user,"edl_password":edl_password,"edl_token":edl_token,
                         "cdse_token":cdse_token,"cdse_client_id":cdse_client_id,"cdse_client_secret":cdse_client_secret,
                         "inventory_evidence":inventory_evidence,
                         "biodiversity_inventory_records":biodiversity_inventory_records,
                         "inventory_evidence_manifest":inventory_manifest}
                native=native_carbon_analysis(gdf,land,biome,options)
                from soil_pedology_embrapa import analyze_embrapa_pedology
                pedology,zones=analyze_embrapa_pedology(gdf,with_zones=True)
                try:
                    from soil_fertility_zonal import analyze_fertility
                    fertility=analyze_fertility(gdf,units=zones)
                except Exception as exc:
                    fertility={"status":"N/D","reason":"Falha controlada: "+type(exc).__name__,
                               "units":{},"layers":[]}
                self._analysis_queue.put((run_id,"ok",{"sar":{},"soil":{},"land_use":land,
                                                      "native_carbon":native,"pedology":pedology,
                                                      "fertility":fertility,"aoi_hash":aoi_hash}))
            except Exception:self._analysis_queue.put((run_id,"error",traceback.format_exc()))
        threading.Thread(target=worker,name="EnformAnalysis",daemon=True).start()
        self.after(120,self._poll_analysis)

    def _poll_analysis(self):
        try:run_id,kind,payload=self._analysis_queue.get_nowait()
        except queue.Empty:
            if self._analysis_running:self.after(120,self._poll_analysis)
            return
        if run_id!=self._analysis_generation:
            if self._analysis_running:self.after(120,self._poll_analysis)
            return
        self._analysis_running=False; self.pipeline_btn.state(["!disabled"]); self.global_execute_btn.state(["!disabled"])
        if kind=="error":
            log=Path.home()/".enform_verde"/"enform_diagnostico.log"; log.parent.mkdir(parents=True,exist_ok=True); log.write_text(payload,encoding="utf-8")
            self.status.set("Falha controlada — programa permanece responsivo.")
            return messagebox.showerror("Análise","Falha controlada. Log gravado em:\n"+str(log))
        self.status.set("SAR consultado; calculando carbono…")
        self.after(1,lambda rid=run_id,p=payload:self._execute_main(precomputed_sar=p.get("sar"),precomputed_soil=p.get("soil"),precomputed_land=p.get("land_use"),precomputed_native=p.get("native_carbon"),precomputed_pedology=p.get("pedology"),precomputed_fertility=p.get("fertility"),expected_aoi_hash=p.get("aoi_hash")) if rid==self._analysis_generation else None)

    def _execute_main(self,event=None,precomputed_sar=None,precomputed_soil=None,precomputed_land=None,precomputed_native=None,precomputed_pedology=None,precomputed_fertility=None,expected_aoi_hash=None):
        # Cada execução substitui, nunca acumula, os resultados derivados da geometria corrente.
        self.project["analysis_run_id"]=uuid.uuid4().hex[:12].upper()
        self.project["analysis_started_utc"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
        for k in ("analysis_aoi_hash","analysis_aoi_crs","pipeline_audit","analysis_rows","area_ha","total_tc_ha","total_tco2_ha","last_result","total_is_partial","partial_carbon_total_tc_ha","partial_independent_carbon_total_tc_ha","partial_soil_analysis","partial_sar_analysis","native_carbon","sar_result","sar_warning","total_uncertainty","mapbiomas_zonal","soil_pedology","soil_fertility","modeled_field_predictions","modeled_field_files"):
            self.project.pop(k,None)
        current_car=self.car.get().strip().upper()
        current_ccir=re.sub(r"\D","",self.ccir.get())
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
        from analysis_pipeline_contract import geometry_hash, validate_result_for_publication
        try:
            run_aoi_hash=geometry_hash(self.gdf)
            if expected_aoi_hash and expected_aoi_hash!=run_aoi_hash:
                raise ValueError("HASH_AOI_DIVERGENTE — o processamento em segundo plano pertence a outra geometria.")
        except Exception as exc:
            self.status.set("Análise bloqueada por identidade inconsistente da AOI.")
            return messagebox.showerror("Análise",str(exc))
        self.project["analysis_aoi_hash"]=run_aoi_hash
        self.project["analysis_aoi_crs"]=str(self.gdf.crs)
        self.project["analysis_app_version"]=APP_VERSION
        try:
            self.status.set("Executando estimativa remota..."); self.update_idletasks()
            area=geom_metrics(self.gdf)["area_ha"]
            self.project.pop("land_use",None)
            reference=self.ibge_physiognomy_gdf;reference_field=self.ibge_class_field or "legenda_1"
            if precomputed_land is None and reference is None:
                try:reference,reference_field=load_ibge_land_use_reference(self.gdf)
                except Exception:pass
            land=precomputed_land if precomputed_land is not None else run_land_use(self.gdf,Path.home()/".enform_verde"/"uso_solo"/uuid.uuid4().hex[:12],self.land_use_config,ibge=reference,ibge_field=reference_field,sar_paths=getattr(self,'sar_paths',None))
            if land.get("error"):raise ValueError(land["error"])
            self.project["land_use"]=land
            native=(precomputed_native if precomputed_native is not None
                    else native_carbon_analysis(
                        self.gdf,land,self.biome.get(),
                        sar_options={
                            "inventory_evidence":self.inventory_evidence_data,
                            "inventory_evidence_manifest":self.inventory_evidence_manifest,
                            "biodiversity_inventory_records":self.biodiversity_inventory_records,
                        },
                        sar_paths=self.sar_paths))
            if precomputed_pedology is not None:
                pedology=precomputed_pedology
                fertility=precomputed_fertility
            else:
                from soil_pedology_embrapa import analyze_embrapa_pedology
                pedology,zones=analyze_embrapa_pedology(self.gdf,with_zones=True)
                try:
                    from soil_fertility_zonal import analyze_fertility
                    fertility=analyze_fertility(self.gdf,units=zones)
                except Exception as exc:
                    fertility={"status":"N/D","reason":"Falha controlada: "+type(exc).__name__,
                               "units":{},"layers":[]}
            self.project["soil_pedology"]=pedology
            self.project["soil_fertility"]=fertility or {"status":"N/D","reason":"sem consulta"}
            # A SAR transport failure is a reportable analysis state, not a
            # reason to discard independent soil/carbon diagnostics or leave
            # the dashboard blank. The failed stage remains explicitly failed
            # and its classes stay N/D; internal exceptions and stale AOIs
            # remain hard blockers.
            validate_result_for_publication(run_aoi_hash,self.gdf,land,
                required_keys=("vector_path",),allow_declared_error_status=True)
            validate_result_for_publication(run_aoi_hash,self.gdf,native,
                required_keys=("area_aoi_ha","strata","components"),
                allow_declared_error_status=True)
            land_status=str(land.get("status") or "N/D").upper()
            recent_sar=land.get("recent_sar_cover") or {}
            land_failed=land_status.startswith(("ERRO","FAILED","FAILURE"))
            native_status=str(native.get("status") or "N/D").upper()
            native_failed=native_status.startswith(("ERRO","FAILED","FAILURE"))
            partial=land_failed or native_failed
            self.project["pipeline_audit"]={
                "analysis_run_id":self.project["analysis_run_id"],
                "aoi_hash":run_aoi_hash,
                "overall_status":"PARCIAL_COM_ERRO_TECNICO" if partial else "CONCLUIDA_COM_ESTADOS_DECLARADOS",
                "stages":{
                    "land_use":{"status":"ERRO_TECNICO" if land_failed else land_status,
                                 "reason":recent_sar.get("reason") or land.get("reason"),
                                 "vector_path":land.get("vector_path")},
                    "native_carbon":{"status":"ERRO_TECNICO" if native_failed else
                                               "CONCLUIDA" if native.get("complete") else "PARCIAL",
                                     "native_area_ha":native.get("native_area_ha"),
                                     "unknown_cover_area_ha":native.get("unknown_cover_area_ha")},
                    "pedology":{"status":(pedology or {}).get("status","N/D")},
                    "fertility":{"status":(fertility or {}).get("status","N/D")},
                },
            }
            self._present_native_carbon(native,land,pedology=pedology,fertility=fertility)
            self._present_cultivated_monitoring(land)
            if partial:
                reason=(recent_sar.get("reason") or land.get("reason") or
                        native.get("reason") or "falha técnica registrada na auditoria da etapa")
                self.status.set("Análise parcial — SAR com erro técnico; classes atuais permanecem N/D. "+str(reason)[:180])
            else:
                self.status.set("Análise concluída com estados e lacunas declarados; consulte a trilha de auditoria.")
            return
        except Exception as e:self.status.set("Falha."); messagebox.showerror("Análise",str(e))

    def _present_native_carbon(self,native,land,pedology=None,fertility=None):
        self.project["native_carbon"]=native
        self.project["area_ha"]=native["area_aoi_ha"]
        if hasattr(self,"aoi_area_display"):
            self.aoi_area_display.set(f"{format_ptbr(native['area_aoi_ha'],2)} ha (EPSG:6933; base dos percentuais)")
        if hasattr(self,"ibge_biome_display"):
            self.ibge_biome_display.set(self.biome.get() or "Não determinado")
        if hasattr(self,"ibge_phys_display"):
            from property_physiognomy_display import format_property_physiognomies
            native_text=format_property_physiognomies(native,format_ptbr)
            if not native.get("native_area_ha",0):
                d=self.project.get("ibge_diagnosis") or {}
                potential="; ".join(
                    str(x.get("name") or "N/D")+" — "+
                    format_ptbr(float(x.get("area_ha",0)),2)+" ha"
                    for x in d.get("regioes_fitoecologicas",[]) if x.get("name"))
                if potential:
                    native_text += ("\nPOTENCIAL IBGE (não confirmado como nativo atual): "+
                                    potential)
            self.ibge_phys_display.set(native_text)
        known=native.get("known_total_tc")
        area=native["native_area_ha"]
        self.project["total_tc_ha"]=(known/area if known is not None and area else None)
        self.project["total_tco2_ha"]=(self.project["total_tc_ha"]*44/12 if self.project["total_tc_ha"] is not None else None)
        self.project["total_tc"]=known
        self.project["total_tco2e"]=(known*44/12 if known is not None else None)
        self.project["total_is_partial"]=not native["complete"]
        rows=[]
        for item in native["components"]:
            density=item["tc_on_all_native_area"]
            rows.append({"parametro":item["parametro"],"tc":density,"tco2":density*44/12 if density is not None else None,
                         "origem":"NATIVA_ESTRATIFICADA","status":"QUANTIFICADO" if density is not None else "PARCIAL / NÃO ESTIMADO",
                         "metodo":"soma (estoque/ha × área da interseção) por fitofisionomia nativa",
                         "fonte":"fontes individuais por estrato no relatório e auditoria",
                         "obs":f"Área nativa quantificada: {format_ptbr(item['quantified_area_ha'],2)} ha; sem dado: {format_ptbr(item['missing_native_area_ha'],2)} ha. Total conhecido: "+(format_ptbr(item['known_total_tc'],2)+" tC" if item['known_total_tc'] is not None else "N/D"),
                         "erro_abs_tc":None,"erro_pct":None,"erro_metrica":"Incertezas individuais por estrato; total não quantificado",
                         "nivel_confianca":"sem IC total; não tratar falta de dado como zero"})
        self.project["analysis_rows"]=rows
        lines=[f"ENFORM VERDE {APP_VERSION} — CARBONO SOMENTE EM FORMAÇÕES NATIVAS",
               "Área do polígono: "+format_ptbr(native["area_aoi_ha"],2)+" ha",
               "Formações nativas MAPEADAS: "+
                   (format_ptbr(area,2)+" ha (área cartográfica, sem confirmação de campo)" if area>0 or native["unknown_cover_area_ha"]<=0
                    else "N/D — não há área nativa atual confirmada"),
               "Outros usos (somente ocorrência, sem carbono): "+
                   (format_ptbr(native["excluded_other_uses_ha"],2)+" ha" if native["excluded_other_uses_ha"]>0 or native["unknown_cover_area_ha"]<=0
                    else "N/D — uso não nativo não confirmado"),
               "Cobertura não confirmada (sem carbono): "+format_ptbr(native["unknown_cover_area_ha"],2)+" ha",
               "Área sem classe cartográfica de referência: "+format_ptbr(native.get("unmapped_aoi_area_ha",0),2)+" ha",
               "Completude do MAPA de cobertura: "+native.get("cover_completeness","NÃO VERIFICADA")+
                   " — não indica completude dos compartimentos de carbono; o estoque segue PARCIAL enquanto houver compartimentos N/D.",
               native["method"],""]
        from executive_carbon_report import executive_carbon_lines
        from soil_pedology_embrapa import pedology_report_lines
        from soil_fertility_zonal import fertility_report_lines
        lines = (executive_carbon_lines(native,format_ptbr) +
                 pedology_report_lines(pedology or {},format_ptbr) +
                 fertility_report_lines(fertility or {},format_ptbr) + lines)
        for scenario in native.get("conditional_inventory_scenarios",[]):
            lines += ["", "CENÁRIO CONDICIONAL DE CARBONO — INVENTÁRIO/REFERÊNCIA REGIONAL (não é cobertura atual confirmada)",
                      "Estado: "+str(scenario.get("status")),
                      "Área-base: "+format_ptbr(scenario.get("area_ha",0),2)+" ha — "+str(scenario.get("area_basis")),
                      "Fitofisionomia: "+str(scenario.get("physiognomy"))+"; domínio geográfico: "+str(scenario.get("geographic_tier")),
                      "Fonte e evidência: "+str(scenario.get("source"))+" — "+str(scenario.get("source_url")),
                      "Unidades/parcelas (quando declaradas pela fonte): n="+str(scenario.get("inventory_n_unique_sampling_units"))+"; AGB "+format_ptbr(scenario.get("agb_mean_mg_ha"),2)+" Mg/ha; faixa da fonte "+json.dumps(scenario.get("agb_range_mg_ha") or scenario.get("agb_observed_range_mg_ha"),ensure_ascii=False),
                      str(scenario.get("estimate_label"))+" — carbono condicional: "+format_ptbr(scenario.get("carbon_mean_tc_ha"),2)+" tC/ha; total cenário "+format_ptbr(scenario.get("carbon_total_tc_scenario"),2)+" tC ("+format_ptbr(scenario.get("carbon_total_tco2e_scenario"),2)+" tCO₂e).",
                      "Incerteza: "+str(scenario.get("uncertainty")),
                      "TRILHA DE CÁLCULO: "+json.dumps(scenario.get("calculation_trace") or {},ensure_ascii=False,sort_keys=True),
                      "Falhas SAR registradas (não equivalem a ausência de cenas): "+json.dumps(scenario.get("sar_technical_failures") or [],ensure_ascii=False),
                      "Confiança: "+str(scenario.get("confidence")),
                      "Limitações: "+"; ".join(scenario.get("limitations",[]))]
        diag=native.get("inventory_scenario_diagnostic")
        if diag:
            lines += ["", "CENÁRIO DE INVENTÁRIO: "+str(diag.get("status"))+" — "+str(diag.get("reason"))]
        for st in native["strata"]:
            lines.append(st["class_name"]+": "+format_ptbr(st["area_ha"],2)+" ha ("+format_ptbr(st["area_pct"],2)+"% da AOI) — "+st["source"])
            lines.append("  FITOFISIONOMIA À QUAL SE APLICA A ESTIMATIVA: "+st["physiognomy"]+" — "+st["physiognomy_resolution"])
            lines.append("  Proveniência SAR/altura: "+json.dumps(st.get("sar_details") or {},ensure_ascii=False,default=str))
            # Display actual raster acquisition separately from catalog discovery.
            sar_details=st.get("sar_details") or {}
            if isinstance(sar_details,dict):
                actual_stats=sar_details.get("stats") or []
                for scene in actual_stats:
                    if not isinstance(scene,dict):
                        continue
                    lines.append("  CENA PROCESSADA: "+str(scene.get("path") or scene.get("scene") or "arquivo não identificado"))
                    from sar_acquisition_time import acquisition_display
                    acquisition=acquisition_display(scene)
                    lines.append("    Horário de aquisição (UTC -3): "+acquisition["brasilia"])
                    lines.append("    Horário de aquisição (UTC): "+acquisition["utc"])
                    if acquisition.get("reference_period"):lines.append("    Período de referência do produto: "+acquisition["reference_period"])
                    if acquisition.get("explanation"):lines.append("    Observação temporal: "+acquisition["explanation"])
            for row in st["components"]:
                from experimental_audit import audit_carbon_component
                calc_trace=audit_carbon_component(row,area_ha=st["area_ha"],formation=st["physiognomy"],analysis_id=self.project.get("analysis_run_id"))
                lines.append("    RASTRO DO CÁLCULO EXPERIMENTAL (não homologado): "+json.dumps(calc_trace,ensure_ascii=False,sort_keys=True,default=str))
                if row["parametro"]=="Necromassa subterrânea":lines.append("  Necromassa subterrânea — raízes mortas")
                value=(format_ptbr(row["tc"],2)+" tC/ha; "+format_ptbr(row["tc"]*44/12,2)+" tCO₂e/ha; "+format_ptbr(row["total_tc"],2)+" tC; "+format_ptbr(row["total_tc"]*44/12,2)+" tCO₂e na interseção") if row["total_tc"] is not None and row.get("tc") is not None else "NÃO ESTIMADO / EXCLUÍDO DO TOTAL"
                lines += ["  "+row["parametro"]+": "+value,"    Fonte: "+str(row.get("fonte")),"    Método: "+str(row.get("metodo")),"    Erro/incerteza e limitação: "+str(row.get("obs")),"    Nível estatístico: conforme fonte por estrato; não há IC do total","    Intervalos/erro informados: "+json.dumps({k:row[k] for k in ("range_tc_ha","range_dry_mg_ha","agb_uncertainty_mg_ha","agb_range_mg_ha","spatial_sd_tc_ha","root_prediction_interval_tc_ha","root_uncertainty_status","root_uncertainty_source") if row.get(k) is not None},ensure_ascii=False)]
            from soil_intersection_report import soil_intersection_lines
            lines += soil_intersection_lines(st.get("soil_profiles"),format_ptbr)
            for depth,profile in (st.get("soil_profiles") or {}).items():
                if depth!="0–100 cm" and isinstance(profile,dict) and profile.get("tc_ha") is not None:
                    lines.append("  Solo "+depth+": "+format_ptbr(profile["tc_ha"],2)+" tC/ha nesta formação; perfil informativo, não somado novamente ao total.")
        lines += ["",("TOTAL" if native["complete"] else "SOMA PARCIAL CONHECIDA")+" NAS INTERSEÇÕES NATIVAS: "+(format_ptbr(known,2)+" tC" if known is not None else "NÃO ESTIMADO"),"ESTOQUE EQUIVALENTE NAS INTERSEÇÕES NATIVAS: "+(format_ptbr(known*44/12,2)+" tCO₂e" if known is not None else "NÃO ESTIMADO"),"Densidades na área nativa: "+(format_ptbr(known/area,2)+" tC/ha; "+format_ptbr((known/area)*44/12,2)+" tCO₂e/ha" if known is not None and area else "NÃO ESTIMADO"),native["uncertainty_note"],""]
        joint=native.get("total_uncertainty")
        if joint:
            # This is only reached with externally supplied complete covariance.
            # Never present a clipped normal interval as empirically calibrated.
            lo,hi=joint["ci95_tC"]
            lo_co2,hi_co2=joint["ci95_tCO2e"]
            lines.extend([
                "IC95% NORMAL APROXIMADO DO TOTAL (NÃO VALIDADO INDEPENDENTEMENTE): "
                    +format_ptbr(lo,2)+"–"+format_ptbr(hi,2)+" tC; "
                    +format_ptbr(lo_co2,2)+"–"+format_ptbr(hi_co2,2)+" tCO₂e.",
                "Erro-padrão condicionado à matriz de covariância fornecida: "
                    +format_ptbr(joint["se_tC"],2)+" tC. Não inclui erros sem modelagem documentada."
            ])
        lines+=land_use_report_lines(land,lambda v:format_ptbr(v,2))
        # Explicit PRE-FIELD outputs: actual estimates, not made-up observations.
        try:
            from modeled_field_validation import (build_pre_field_manifest,
                                                  write_pre_field_evidence)
            try:
                from enform_build_source import SOURCE_SHA
            except ImportError:
                SOURCE_SHA=None
            prefield=build_pre_field_manifest(
                native, analysis_id=self.project["analysis_run_id"], land=land,
                source_sha=SOURCE_SHA or self.project.get("source_code_sha"))
            evidence_dir=Path(land["vector_path"]).parent
            evidence_files=write_pre_field_evidence(evidence_dir,prefield)
            self.project["modeled_field_predictions"]=prefield
            self.project["modeled_field_files"]=evidence_files
            lines.extend(["", "RESULTADOS MODELADOS — TESTES DE CAMPO PENDENTES",
                "Estimativas numéricas modeladas: "+str(prefield["predictions_with_numeric_model"])+
                "; resultados N/D: "+str(prefield["predictions_without_model"])+".",
                "Manifesto pré-campo: "+str(evidence_files["predictions_json"]),
                "Planilha em branco para medições independentes: "+
                str(evidence_files["field_template_csv"]),
                "As faixas dos modelos não são IC95% de campo. Nenhuma medição observada foi criada."])
        except Exception as exc:
            self.project["modeled_field_predictions"]={"status":"N/D",
                "reason":type(exc).__name__+": "+str(exc)[:160]}
            lines.extend(["", "MODELOS PARA VERIFICAÇÃO EM CAMPO: N/D — "+
                          type(exc).__name__+": "+str(exc)[:160]])
        text="\n".join(lines)
        self.project["last_result"]=text
        self._set(self.res,text);self.nb.select(self.tabs[3])
        self.status.set("Carbono por formação nativa concluído; lacunas e outros usos indicados separadamente.")
        # Store serializable class-level results beside spatial provenance.
        audit=Path(land["vector_path"]).parent/"carbono_formacoes_nativas.json"
        audit.write_text(json.dumps(native,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        # Separate pedology from carbon stocks in exported calculation evidence.
        pedo_audit=Path(land["vector_path"]).parent/"pedologia_embrapa_auditoria.json"
        pedo_audit.write_text(json.dumps(pedology or {},ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        fert_audit=Path(land["vector_path"]).parent/"fertilidade_embrapa_auditoria.json"
        fert_audit.write_text(json.dumps(fertility or {},ensure_ascii=False,indent=2,default=str),encoding="utf-8")

    def export_excel(self):
        from analysis_pipeline_contract import geometry_hash
        try:
            expected_hash=self.project.get("analysis_aoi_hash")
            if not expected_hash or geometry_hash(self.gdf)!=expected_hash:
                raise ValueError("HASH_AOI_DIVERGENTE — reexecute a análise para esta geometria antes de exportar.")
        except Exception as exc:
            return messagebox.showerror("Excel",str(exc))
        if not self.project.get("analysis_rows") and not self.project.get("land_use"):
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
                    if isinstance(v,(int,float)) and not isinstance(v,bool):
                        c.number_format='[$-416]#.##0' if float(v).is_integer() else '[$-416]#.##0,00'
                sh.cell(i,2).font=Font(bold=True,color=green)
        area=self.project.get("area_ha"); total=self.project.get("total_tc_ha"); totalco2=self.project.get("total_tco2_ha"); ar=self.project.get("analysis_rows",[]); is_partial=bool(self.project.get("total_is_partial")) or not bool(ar)
        ws=wb.active; ws.title="Resumo Executivo"; setup(ws,"Enform Verde — Resumo Executivo")
        put(ws,[["Entrada","Projeto",None,None,"Informado","cadastro",None,self.name.get()],
                ["Diagnóstico IBGE","Bioma dominante",None,None,"Calculado espacialmente","interseção de polígonos","IBGE — Biomas 2025",self.biome.get()],
                ["Diagnóstico IBGE","Fitofisionomia/região fitoecológica dominante",None,None,"Calculado espacialmente","interseção de polígonos","IBGE — Vegetação 2026",self.phys.get()],
                ["Entrada","Área analisada",None,None,"Calculado","geometria","CAR/vetor",f"{format_ptbr(area,2)} ha"],
                ["Entrada","Sensor/produto selecionado",None,None,"Informado","SAR/multissensor","ESA/fornecedor",self.sensor.get()],
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
        from sentinel1_mpc import sign_asset_href
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
            vals={}
            for pol in ("vv","vh"):
                href=s["assets"][pol]["href"]
                if s.get("provider","MPC")=="MPC":
                    href=sign_asset_href(href)
                with rasterio.Env(**tls_setup.gdal_env()):
                    with rasterio.open(href) as src:
                        g=shape(transform_geom("EPSG:4326",src.crs,mapping(aoi.geometry.iloc[0])))
                        w=from_bounds(*g.bounds,transform=src.transform).round_offsets().round_lengths()
                        a=src.read(1,window=w,masked=True)
                        vals[pol]=int((~a.mask).sum()) if hasattr(a,"mask") else int(a.size)
            return vals
        px=retry(read)
        if min(px.values())<100:raise RuntimeError("menos de 100 pixels SAR válidos: "+str(px))
        out["sentinel1"]={"status":"OK","scene_id":s.get("id"),"acquisition_utc":s.get("acquisition_utc"),
                          "provider":s.get("provider","MPC"),"valid_pixels":px}
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
