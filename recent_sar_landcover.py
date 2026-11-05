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
        if not candidates or (ref-candidates[0][0]).days>30:
            raise ValueError("No current dual-polarization Sentinel-1 scenes")
        orbit=(candidates[0][1].get("orbit_state"),candidates[0][1].get("relative_orbit"))
        candidates=[v for v in candidates if (v[1].get("orbit_state"),v[1].get("relative_orbit"))==orbit]
        selected=[]
        for dt,scene in candidates:
            if all(abs((dt-d).total_seconds())>5*86400 for d,_ in selected):
                selected.append((dt,scene))
            if len(selected)>=7:break
        if len(selected)<3 or (selected[0][0]-selected[-1][0]).days<35:
            raise ValueError("Insufficient same-orbit acquisitions spanning 35 days")
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
                            arr=np.full(size,np.nan,dtype=np.float32)
                            reproject(source=rasterio.band(src,1),destination=arr,
                                      src_nodata=src.nodata,dst_nodata=np.nan,
                                      dst_crs=crs,dst_transform=tr,resampling=Resampling.nearest)
                            pair.append(arr)
                data.append((dt,str(scene.get("id","")),pair))
            except (UnicodeError,OSError,RuntimeError,ValueError) as exc:
                errors.append({"scene_id":str(scene.get("id","")),"error_type":type(exc).__name__})
        result["failed_scene_reads"]=errors
        if len(data)<3 or (data[0][0]-data[-1][0]).days<35:
            raise ValueError("Not enough actual VV/VH raster pixels were accessible")
        crs,tr,size,local=grid
        inside=geometry_mask([mapping(local)],out_shape=size,transform=tr,invert=True)
        codes,qa=classify_temporal(np.stack([r[2][0] for r in data]),
                                   np.stack([r[2][1] for r in data]),inside)
        codes=sieve(codes,size=12,mask=codes>0).astype(np.uint8)
        codes[(codes==0)&inside]=3
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
        result["reason"]=type(exc).__name__+": "+str(exc)[:200]
    return result
