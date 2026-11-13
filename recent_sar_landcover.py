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

SAR_CANDIDATE_CLASSES = {
    1: "Assinatura SAR estável — uso/cobertura N/D",
    2: "Área cultivada — candidato SAR experimental; cultura N/D",
    3: "Assinatura SAR ambígua — uso/cobertura N/D",
}

def candidate_class_name(code):
    """Human-readable pilot label; class 2 is a candidate, not a confirmed crop."""
    return SAR_CANDIDATE_CLASSES.get(int(code), "Assinatura SAR — uso/cobertura N/D")

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

def _rolling_history(data, inside, aoi_area_ha, *, max_window_days=150,
                     min_scenes=3, min_span_days=35):
    """Experimental rolling SAR candidate areas, never field-validated land use.

    Each point is reclassified using only same-orbit VV/VH scenes acquired on
    or before that date and within the preceding ``max_window_days``. The
    class-2 area is therefore a temporal-signature candidate, not a confirmed
    crop area. Pixel areas are normalized to the exact AOI area to account for
    the partial boundary cells selected by the rasterized AOI mask.
    """
    chronological=sorted(data,key=lambda row:row[0])
    history=[]
    inside_count=int(np.asarray(inside,dtype=bool).sum())
    if inside_count<=0 or not chronological:return history
    cell_area=float(aoi_area_ha)/inside_count
    for end_index,(end_dt,_,_) in enumerate(chronological):
        start_dt=end_dt-timedelta(days=max_window_days)
        window=[row for row in chronological[:end_index+1]
                if start_dt<=row[0]<=end_dt]
        span=(window[-1][0]-window[0][0]).total_seconds()/86400 if window else 0
        base={"as_of_utc":end_dt.isoformat(),
              "window_start_utc":window[0][0].isoformat() if window else None,
              "window_days":max_window_days,"scene_count":len(window),
              "span_days":round(span,2),"status":"N/D_SERIE_INSUFICIENTE"}
        if len(window)<min_scenes or span<min_span_days:
            base["reason"]="exige ao menos 3 cenas e 35 dias de intervalo"
            history.append(base);continue
        try:
            codes,qa=classify_temporal(
                np.stack([row[2][0] for row in window]),
                np.stack([row[2][1] for row in window]),inside)
        except ValueError as exc:
            base.update({"status":"N/D_SEPARABILIDADE_SAR",
                         "reason":str(exc)[:180],"qa":None})
            history.append(base);continue
        areas={}
        for code,name in SAR_CANDIDATE_CLASSES.items():
            areas[name]=round(float(np.count_nonzero(codes==code))*cell_area,2)
        mapped=int(np.count_nonzero(codes))
        base.update({"status":"CANDIDATOS_EXPERIMENTAIS",
                     "areas_ha":areas,
                     "cultivated_candidate_area_ha":areas[SAR_CANDIDATE_CLASSES[2]],
                     "mapped_candidate_area_ha":round(mapped*cell_area,2),
                     "valid_pixels":qa["valid_pixels"],
                     "valid_fraction":qa["valid_fraction"],
                     "uncertainty":"não quantificada; heurística temporal sem validação local nem IC95%",
                     "qa":qa})
        history.append(base)
    return history

def _select_orbit_series(candidates,ref):
    """Select most recent COMPLETE same-orbit time series, not merely latest item."""
    groups={}
    for dt,scene in candidates:
        orbit=(scene.get("orbit_state"),scene.get("relative_orbit"))
        provider=scene.get("provider","MPC")
        if orbit[0] is not None and orbit[1] is not None:
            groups.setdefault((provider,orbit[0],orbit[1]),[]).append((dt,scene))
    eligible=[]
    for provider,orbit_state,relative_orbit in groups:
        orbit=(provider,orbit_state,relative_orbit)
        rows=groups[orbit]
        picked=[]
        for dt,scene in sorted(rows,key=lambda item:item[0],reverse=True):
            if all(abs((dt-other).total_seconds())>5*86400 for other,_ in picked):
                picked.append((dt,scene))
            if len(picked)>=12:break
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
        from sentinel1_sources import search_sentinel1_sources
        from sentinel1_mpc import (get_runtime_sas_token, asset_href_for_read_attempt)
        ref=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        geom=aoi.to_crs(4326).geometry.union_all()
        if geom.is_empty:raise ValueError("AOI empty")
        found=(search or search_sentinel1_sources)(mapping(geom),start_utc=ref-timedelta(days=150),end_utc=ref)
        candidates=[]
        for scene in found.get("scenes",[]):
            try:
                dt=datetime.fromisoformat(str(scene["acquisition_utc"]).replace("Z","+00:00"))
                if dt.tzinfo and dt<=ref and {"vv","vh"}<=set(scene.get("assets") or {}):
                    candidates.append((dt.astimezone(timezone.utc),scene))
            except (KeyError,ValueError,TypeError):pass
        candidates.sort(key=lambda v:v[0],reverse=True)
        if not candidates and not found.get("pagination_complete", True):
            result.update({"status":"ERRO_TECNICO","reason":"CATALOG_SEARCH_INCOMPLETE",
                           "provider_diagnostics":found.get("providers",[])})
            return result
        if not candidates:
            result.update({"status":"N/D_DADOS", "reason":"CATALOGUES_COMPLETED_NO_COMPATIBLE_VV_VH_SERIES",
                           "provider_diagnostics":found.get("providers",[]),
                           "catalog_scene_count":int(found.get("scene_count",0)), "selected_scene_count":0,
                           "readable_scene_count":0})
            return result
        grid=None
        data=[]
        errors=[]
        selected=[]
        orbit=None
        provider_used=None
        providers=["MPC","INPE"]
        if search is not None:
            providers=sorted({row[1].get("provider","MPC") for row in candidates})
        provider_diagnostics=found.get("providers",[])
        selection_diagnostics=[]
        for provider in providers:
            provider_rows=[row for row in candidates if row[1].get("provider","MPC")==provider]
            provider_selected,provider_orbit=_select_orbit_series(provider_rows,ref)
            provider_diag={"provider":provider,"candidate_scene_count":len(provider_rows),
                           "eligible_series_found":bool(provider_selected),
                           "selected_scene_count":len(provider_selected),
                           "pixel_read_attempt_count":0,"readable_scene_count":0,
                           "failed_scene_count":0,"token_error_count":0}
            selection_diagnostics.append(provider_diag)
            if not provider_selected:
                continue
            provider_grid=None
            provider_data=[]
            provider_errors=[]
            provider_token=""
            if provider=="MPC":
                try:
                    provider_token=(token_fn or get_runtime_sas_token)()
                except Exception as exc:
                    # An unavailable collection SAS must not skip all discovered scenes.
                    # Try the official per-asset signing endpoint during the read loop.
                    errors.append({"provider":provider,"error_type":"TOKEN_"+type(exc).__name__,
                                   "error":_safe_reason(exc),"recovered":False,
                                   "fallback":"SIGN_INDIVIDUAL_ASSET"})
                    provider_diag["token_error_count"]+=1
            for dt,scene in provider_selected:
                scene_ok=False
                for attempt in range(4):
                    provider_diag["pixel_read_attempt_count"]+=1
                    read_stage="asset_authorization"
                    try:
                        # A failed attempt must never poison the output grid for
                        # the next scene or provider. Commit only after both
                        # polarizations were actually read and reprojected.
                        scene_grid=provider_grid
                        pair=[]
                        for pol in ("vv","vh"):
                            from tls_setup import gdal_env
                            # Rotate actual HTTP transports after failures:
                            # default multiplexing, serial ranges, single GET,
                            # and serial ranges without HTTP/2 multiplexing.
                            gdal_opts={"GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR",
                                       "GDAL_HTTP_TIMEOUT":"45","GDAL_HTTP_MAX_RETRY":"3",
                                       "GDAL_HTTP_RETRY_DELAY":"1",**gdal_env()}
                            if attempt>=1:
                                gdal_opts.update({"CPL_VSIL_CURL_USE_HEAD":"NO",
                                                  "GDAL_HTTP_MULTIRANGE":("SERIAL" if attempt in (1,3) else "SINGLE_GET"),
                                                  "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES":"NO",
                                                  "GDAL_HTTP_VERSION":"1.1"})
                            if attempt==3:gdal_opts["GDAL_HTTP_MULTIPLEX"]="NO"
                            with rasterio.Env(**gdal_opts):
                                asset_href=scene["assets"][pol]["href"]
                                read_href=(asset_href_for_read_attempt(
                                    asset_href,attempt=attempt,token=provider_token,
                                    token_fn=token_fn or get_runtime_sas_token)
                                    if provider=="MPC" else asset_href)
                                read_stage="open_cog"
                                with rasterio.open(read_href) as src:
                                    read_stage="read_cog_window"
                                    if not src.crs:raise ValueError("Missing georeferencing in SAR source")
                                    if scene_grid is None:
                                        aoig=shape(transform_geom("EPSG:4326",src.crs,mapping(geom)))
                                        win=from_bounds(*aoig.bounds,transform=src.transform).round_offsets().round_lengths()
                                        win=win.intersection(Window(0,0,src.width,src.height))
                                        if win.width*win.height>1800000 or min(win.width,win.height)<=0:
                                            raise ValueError("SAR AOI exceeds memory-bounded raster window")
                                        scene_grid=(src.crs,src.window_transform(win),
                                                    (int(win.height),int(win.width)),aoig)
                                    crs,tr,size,_=scene_grid
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
                                        src_values=np.ma.filled(window_values.astype(np.float32),np.nan)
                                    arr=np.full(size,np.nan,dtype=np.float32)
                                    read_stage="reproject_cog_window"
                                    reproject(source=src_values,destination=arr,
                                              src_transform=src.window_transform(window),src_crs=src.crs,
                                              src_nodata=np.nan,dst_nodata=np.nan,dst_crs=crs,
                                              dst_transform=tr,resampling=Resampling.nearest)
                                    if not (np.isfinite(arr) & (arr > 0)).any():
                                        raise ValueError("SAR_SCENE_NO_VALID_PIXELS_IN_AOI")
                                    pair.append(arr)
                        if len(pair)!=2:
                            raise ValueError("SAR_SCENE_INCOMPLETE_VV_VH_PAIR")
                        provider_grid=scene_grid
                        provider_data.append((dt,str(scene.get("id","")),pair))
                        provider_diag["readable_scene_count"]+=1
                        scene_ok=True
                        break
                    except (UnicodeError,OSError,RuntimeError,ValueError) as exc:
                        row={"provider":provider,"scene_id":str(scene.get("id","")),
                             "error_type":type(exc).__name__,
                             "error_class":("GDAL_NATIVE_ERROR_NON_UTF8" if isinstance(exc,UnicodeError) else "COG_READ_ERROR"),
                             "stage":read_stage,
                             "read_strategy":("MULTIRANGE_DEFAULT" if attempt==0 else
                               "SERIAL_RANGE_HTTP11" if attempt==1 else
                               "SINGLE_GET_HTTP11" if attempt==2 else "SERIAL_NO_MULTIPLEX_HTTP11"),
                             "error":_safe_reason(exc),
                             "attempt":attempt+1,"recovered":False}
                        provider_errors.append(row)
                        provider_diag["failed_scene_count"]+=1
                        if attempt==0 and provider=="MPC":
                            try:
                                provider_token=(token_fn or get_runtime_sas_token)()
                            except Exception as token_exc:
                                provider_errors.append({"provider":provider,"scene_id":str(scene.get("id","")),
                                    "error_type":"TOKEN_REFRESH_"+type(token_exc).__name__,
                                    "error":_safe_reason(token_exc),"attempt":attempt+1,"recovered":False})
                if scene_ok and provider_errors and provider_errors[-1].get("scene_id")==str(scene.get("id","")):
                    provider_errors[-1]["recovered"]=True
            errors.extend(provider_errors)
            if len(provider_data)>=3 and (provider_data[0][0]-provider_data[-1][0]).days>=35:
                data=provider_data
                selected=provider_selected
                orbit=provider_orbit
                grid=provider_grid
                provider_used=provider
                break
            if provider_data:
                errors.append({"provider":provider,"error_type":"INSUFFICIENT_READABLE_SERIES",
                               "readable_scene_count":len(provider_data),"recovered":False})
        result["catalog_provider_diagnostics"]=provider_diagnostics
        result["provider_processing_diagnostics"]=selection_diagnostics
        result["failed_scene_reads"]=errors
        result["selected_scene_count"]=sum(x["selected_scene_count"] for x in selection_diagnostics)
        result["pixel_read_attempt_count"]=sum(x["pixel_read_attempt_count"] for x in selection_diagnostics)
        result["readable_scene_count"]=sum(x["readable_scene_count"] for x in selection_diagnostics)
        eligible_count=sum(x["eligible_series_found"] for x in selection_diagnostics)
        if eligible_count==0:
            result.update({"status":"N/D_DADOS","reason":"NO_ELIGIBLE_TEMPORAL_SERIES",
                           "diagnostic":"Cenas candidatas foram catalogadas, mas nenhuma série cumpriu órbita, recência e duração; nenhuma leitura de pixel foi tentada"})
            return result
        if len(data)<3 or (data[0][0]-data[-1][0]).days<35:
            all_selected_reads=sum(x["readable_scene_count"] for x in selection_diagnostics)
            any_read_attempt=sum(x["pixel_read_attempt_count"] for x in selection_diagnostics)
            token_errors=sum(x["token_error_count"] for x in selection_diagnostics)
            if token_errors and any_read_attempt==0:
                status,reason="ERRO_TECNICO","PROVIDER_AUTHENTICATION_FAILED"
            elif any_read_attempt and all_selected_reads==0:
                status,reason="ERRO_TECNICO","SELECTED_SCENES_PIXEL_READ_FAILED"
            else:
                status,reason="N/D_DADOS","INSUFFICIENT_READABLE_TEMPORAL_SERIES"
            result.update({"status":status,"reason":reason,
                           "diagnostic":"Consultar provider_processing_diagnostics e failed_scene_reads; contadores distinguem seleção, tentativa e leitura"})
            return result
        crs,tr,size,local=grid
        result["committed_grid_shape"]=[int(size[0]),int(size[1])]
        result["committed_grid_crs"]=str(crs)
        result["source_scene_count"]=len(data)
        inside=geometry_mask([mapping(local)],out_shape=size,transform=tr,invert=True)
        try:
            codes,qa=classify_temporal(np.stack([r[2][0] for r in data]),
                                       np.stack([r[2][1] for r in data]),inside)
        except ValueError as exc:
            # Readable SAR is not necessarily discriminative enough for a map.
            # This is a model/data eligibility abstention, not an HTTP/IO error.
            reason=str(exc)
            if "spatially/temporally separate" in reason or "SAR signal" in reason:
                result.update({"status":"N/D_VALIDACAO",
                               "reason":"SAR_SIGNATURE_SEPARABILITY_INSUFFICIENT",
                               "diagnostic":"Cenas VV/VH foram lidas, mas a dispersao espacial/temporal nao sustenta classes experimentais; sem area ou cultura inferida",
                               "native_confirmed":False,"crop_confirmed":False})
                return result
            raise
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
                            class_1="stable backscatter signature; semantic use unknown",
                            class_2="cultivated-area candidate only; crop N/D; not calibrated",
                            class_3="ambiguous backscatter signature; semantic use unknown")
        # V87.36: experimental radar-signature units carry NO crop/vegetation name.
        names={code:candidate_class_name(code) for code in (1,2,3)}
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
        aoi_area_ha=float(aoi.to_crs(6933).geometry.area.sum())/10000
        history=_rolling_history(data,inside,aoi_area_ha)
        result.update({"status":"SAR_REAL_EXPERIMENTAL_CANDIDATES",
             "raster_path":str(raster),"vector_path":str(vec) if len(features)<4000 else None,
             "provider_diagnostics":found.get("providers",[]),
             "providers_used":[provider_used] if provider_used else [],
             "scene_ids":[r[1] for r in data],"scene_count":len(data),
             "acquisitions_utc":[r[0].isoformat() for r in data],
             "latest_acquisition_utc":data[0][0].isoformat(),
             "orbit_state":orbit[1],"relative_orbit":orbit[2],
             "areas_ha":{names[k]:round(areas[k],2) for k in names},
             "history_window_days":150,"history_by_date":history,
             "qa":qa,"method":"unsupervised Sentinel-1 temporal signature screen; class 2 is only a cultivated-area candidate; no crop/native confirmation or calibrated accuracy"})
    except (UnicodeError,OSError,RuntimeError,ValueError,ImportError) as exc:
        result["status"]="ERRO_TECNICO"
        result["reason"]=type(exc).__name__+": "+_safe_reason(exc)
    return result
