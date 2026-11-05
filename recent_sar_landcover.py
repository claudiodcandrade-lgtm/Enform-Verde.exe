"""AOI-wide real Sentinel-1 RTC radar screening; candidate land cover only.

Annual maps do not train or label the current radar layer. This is an
unsupervised within-AOI exploratory screening, NOT a calibrated forest/crop
classifier. Sensitivity to thresholds is not a statistical confidence interval.
"""
from __future__ import annotations
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np

def classify_temporal(vv,vh,inside):
    vv=np.asarray(vv,dtype=float);vh=np.asarray(vh,dtype=float)
    inside=np.asarray(inside,dtype=bool)
    if vv.ndim!=3 or vv.shape!=vh.shape or vv.shape[1:]!=inside.shape or vv.shape[0]<3:
        raise ValueError("Need at least three aligned VV/VH scenes")
    good=inside & ((np.isfinite(vv)&np.isfinite(vh)&(vv>0)&(vh>0)).sum(axis=0)>=3)
    if good.sum()<49: raise ValueError("Need at least 49 AOI pixels with three valid scenes")
    with np.errstate(all="ignore"):
        level_db=np.where((vh>0)&np.isfinite(vh),10*np.log10(np.maximum(vh,1e-12)),np.nan)
        level=np.nanmedian(level_db,axis=0)
        amplitude=np.nanpercentile(level_db,90,axis=0)-np.nanpercentile(level_db,10,axis=0)
    if (np.nanpercentile(amplitude[good],90)-np.nanpercentile(amplitude[good],10)<.35 or
        np.nanpercentile(level[good],90)-np.nanpercentile(level[good],10)<.75):
        raise ValueError("SAR signal does not spatially/temporally separate candidate signatures")
    stable=good & (level>=np.nanquantile(level[good],.65)) & (amplitude<=np.nanquantile(amplitude[good],.35))
    variable=good & (amplitude>=np.nanquantile(amplitude[good],.70)) & (level<np.nanquantile(level[good],.75))
    classes=np.zeros(inside.shape,dtype=np.uint8)
    classes[good]=3;classes[stable]=1;classes[variable&~stable]=2
    return classes,{"valid_pixels":int(good.sum()),"aoi_pixels":int(inside.sum()),
                    "valid_fraction":float(good.sum()/max(1,int(inside.sum()))),
                    "uncertainty":"Threshold heuristic only; no calibrated error, no IC95%, no classification accuracy"}

def _select_orbit_series(candidates,ref):
    """Select most recent COMPLETE same-orbit time series, not merely latest item."""
    groups={}
    for dt,scene in candidates:
        orbit=(scene.get("orbit_state"),scene.get("relative_orbit"))
        if orbit[0] is not None and orbit[1] is not None:
            groups.setdefault(orbit,[]).append((dt,scene))
    eligible=[]
    for orbit,rows in groups.items():
        picked=[]
        for dt,scene in sorted(rows,key=lambda item:item[0],reverse=True):
            if all(abs((dt-other).total_seconds())>5*86400 for other,_ in picked):
                picked.append((dt,scene))
            if len(picked)>=7:break
        if (len(picked)>=3 and 0<=(ref-picked[0][0]).total_seconds()<=30*86400
                and (picked[0][0]-picked[-1][0]).total_seconds()>=35*86400):
            eligible.append((picked[0][0],len(picked),orbit,picked))
    if not eligible:return [],None
    eligible.sort(key=lambda item:(item[0],item[1]),reverse=True)
    return eligible[0][3],eligible[0][2]


def _safe_reason(error):
    """Redact signed remote COG URLs, SAS parameters and credentials."""
    import re
    result=str(error)
    result=re.sub(r"https?://[^\s]+","[URL_REDACTED]",result)
    result=re.sub(r"(?i)(sig|se|sv|sp|st)=[^&\s]+",r"\1=[REDACTED]",result)
    return result[:200]


def run_recent_sar_screen(aoi,output_dir,*,now=None,search=None,token_fn=None):
    """Acquire at least three same-orbit actual VV/VH RTC scenes and map candidates."""
    result={"status":"N/D","native_confirmed":False,"crop_confirmed":False,
            "scientific_status":"EXPERIMENTAL_NAO_CALIBRADO"}
    try:
        import rasterio
        import geopandas as gpd
        from shapely.geometry import mapping,shape
        from rasterio.features import geometry_mask,shapes,sieve
        from rasterio.windows import from_bounds,Window
        from rasterio.warp import reproject,Resampling,transform_geom
        from sentinel1_mpc import search_sentinel1_rtc,get_runtime_sas_token,_signed_href
        ref=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        geom=aoi.to_crs(4326).geometry.union_all()
        if geom.is_empty:raise ValueError("AOI empty")
        found=(search or search_sentinel1_rtc)(mapping(geom),start_utc=ref-timedelta(days=150),end_utc=ref)
        candidates=[]
        for scene in found.get("scenes",[]):
            try:
                dt=datetime.fromisoformat(str(scene["acquisition_utc"]).replace("Z","+00:00"))
                if dt.tzinfo and dt<=ref and {"vv","vh"}<=set(scene.get("assets") or {}):
                    candidates.append((dt.astimezone(timezone.utc),scene))
            except (KeyError,ValueError,TypeError):pass
        candidates.sort(key=lambda v:v[0],reverse=True)
        selected,orbit=_select_orbit_series(candidates,ref)
        if not selected:
            raise ValueError("No complete recent same-orbit SAR series spanning 35 days")
        token=(token_fn or get_runtime_sas_token)()
        grid=None;data=[];errors=[]
        for dt,scene in selected:
            try:
                pair=[]
                for pol in ("vv","vh"):
                    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                                      GDAL_HTTP_TIMEOUT="35",GDAL_HTTP_MAX_RETRY="2",
                                      GDAL_HTTP_UNSAFESSL="NO"):
                        with rasterio.open(_signed_href(scene["assets"][pol]["href"],token)) as src:
                            if not src.crs:raise ValueError("Missing georeferencing in SAR source")
                            if grid is None:
                                aoig=shape(transform_geom("EPSG:4326",src.crs,mapping(geom)))
                                win=from_bounds(*aoig.bounds,transform=src.transform).round_offsets().round_lengths()
                                win=win.intersection(Window(0,0,src.width,src.height))
                                if win.width*win.height>1800000 or min(win.width,win.height)<=0:
                                    raise ValueError("SAR AOI exceeds memory-bounded raster window")
                                grid=(src.crs,src.window_transform(win),(int(win.height),int(win.width)),aoig)
                            crs,tr,size,_=grid
                            # Read only the source raster window intersecting
                            # the AOI. Reprojecting rasterio.band(src,1) may
                            # trigger huge remote reads of a national COG
                            # despite a small destination grid on Windows.
                            local_aoi=shape(transform_geom("EPSG:4326",src.crs,mapping(geom)))
                            window=from_bounds(*local_aoi.bounds,transform=src.transform)
                            from math import floor,ceil
                            c0,r0=floor(window.col_off),floor(window.row_off)
                            c1,r1=ceil(window.col_off+window.width),ceil(window.row_off+window.height)
                            window=Window(c0,r0,max(0,c1-c0),max(0,r1-r0)).intersection(
                                Window(0,0,src.width,src.height))
                            if window.width<1 or window.height<1:
                                raise ValueError("SAR asset does not intersect AOI")
                            if window.width*window.height>1800000:
                                raise ValueError("SAR source window exceeds bounded pixel limit")
                            with np.errstate(all="ignore"):
                                window_values=src.read(1,window=window,masked=True)
                                src_values=np.ma.filled(
                                    window_values.astype(np.float32),np.nan)
                            arr=np.full(size,np.nan,dtype=np.float32)
                            reproject(source=src_values,destination=arr,
                                      src_transform=src.window_transform(window),
                                      src_crs=src.crs,
                                      src_nodata=np.nan,dst_nodata=np.nan,
                                      dst_crs=crs,dst_transform=tr,resampling=Resampling.nearest)
                            pair.append(arr)
                data.append((dt,str(scene.get("id","")),pair))
            except (UnicodeError,OSError,RuntimeError,ValueError) as exc:
                errors.append({"scene_id":str(scene.get("id","")),"error_type":type(exc).__name__})
        result["failed_scene_reads"]=errors
        result["selected_scene_count"]=len(selected)
        result["readable_scene_count"]=len(data)
        if len(data)<3 or (data[0][0]-data[-1][0]).days<35:
            raise ValueError("Cenas SAR catalogadas, mas menos de 3 pares VV/VH reais legíveis no mesmo órbita; consultar failed_scene_reads no JSON (falhas do acesso COG/SAS).")
        crs,tr,size,local=grid
        inside=geometry_mask([mapping(local)],out_shape=size,transform=tr,invert=True)
        codes,qa=classify_temporal(np.stack([r[2][0] for r in data]),
                                   np.stack([r[2][1] for r in data]),inside)
        valid_observation=(codes>0)
        codes=sieve(codes,size=12,mask=valid_observation).astype(np.uint8)
        codes[(codes==0)&valid_observation]=3
        # Pixels without SAR observations must remain nodata=0, not unknown class 3.
        dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=True)
        raster=dest/"sar_cobertura_atual_candidatos_experimental.tif"
        with rasterio.open(raster,"w",driver="GTiff",height=size[0],width=size[1],
                           count=1,crs=crs,transform=tr,nodata=0,dtype="uint8",compress="deflate") as out:
            out.write(codes,1)
            out.update_tags(source="Sentinel-1 RTC VV/VH actual pixels",status="EXPERIMENTAL_NAO_CALIBRADO",
                            class_1="persistent structure candidate",class_2="seasonal change candidate",
                            class_3="ambiguous")
        names={1:"Estrutura persistente — candidata a vegetação lenhosa",
               2:"Mudança SAR sazonal — candidata a cultivo ou outra mudança",3:"Indeterminada"}
        areas={n:0.0 for n in names};features=[]
        for f,v in shapes(codes,mask=codes>0,transform=tr):
            k=int(v)
            if k not in names:continue
            p=shape(f).intersection(local)
            if p.is_empty:continue
            g=gpd.GeoSeries([p],crs=crs)
            ha=float(g.to_crs(6933).area.iloc[0])/10000
            areas[k]+=ha
            if len(features)<4000:
                features.append({"type":"Feature","properties":{"class_name":names[k],
                    "class_code":k,"area_ha":ha,"source":"SAR_CURRENT_EXPERIMENTAL"},
                    "geometry":mapping(g.to_crs(4326).iloc[0])})
        vec=dest/"sar_cobertura_atual_candidatos_experimental.geojson"
        if len(features)<4000:
            vec.write_text(json.dumps({"type":"FeatureCollection","features":features},
                                      ensure_ascii=False),encoding="utf-8")
        result.update({"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES",
             "raster_path":str(raster),"vector_path":str(vec) if len(features)<4000 else None,
             "scene_ids":[r[1] for r in data],"scene_count":len(data),
             "acquisitions_utc":[r[0].isoformat() for r in data],
             "latest_acquisition_utc":data[0][0].isoformat(),
             "orbit_state":orbit[0],"relative_orbit":orbit[1],
             "areas_ha":{names[k]:round(areas[k],2) for k in names},
             "qa":qa,"method":"unsupervised VH temporal stability/variation; not a current native/crop classifier"})
    except (UnicodeError,OSError,RuntimeError,ValueError,ImportError) as exc:
        result["reason"]=type(exc).__name__+": "+_safe_reason(exc)
    return result
