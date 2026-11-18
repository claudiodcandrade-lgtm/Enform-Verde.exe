"""Automatic three-class vigor for a field from the latest Sentinel-1 RTC scene.

1. Latest Sentinel-1 RTC (MPC or INPE fallback) within
   ``window_days`` that covers the field; VV/VH γ⁰ read only in a window of
   field + ``ring_km`` (COG range reads), converted to dB.
2. Reference fields are separate polygons of the same crop emitted by the
   accepted current SAR classifier, outside the target field, read in the same
   Sentinel-1 scene. MapBiomas does not select references or pixels.
3. crop_vigor.classify_vigor (robust z, terciles, spatial bootstrap).
Status remains experimental (no field truth of vigor).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

MIN_REFERENCE_BLOCKS = 6


def _scene(field_4326, as_of, window_days, search):
    from shapely.geometry import mapping
    end = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=timezone.utc)
    end = min(end, datetime.now(timezone.utc))
    found = search(mapping(field_4326), start_utc=end - timedelta(days=window_days), end_utc=end)
    for s in found["scenes"]:
        if {"vv", "vh"} <= set(s["assets"]) and "VH" in (s.get("polarizations") or ["VH"]):
            return s, found
    return None, found


def automatic_vigor(field_gdf, as_of, crop_name, *, reference_gdf=None, ring_km=8.0,
                    window_days=30, search=None, token_fn=None, height_provider=None,
                    max_px=2500, reference_mode="validated_crop_fields"):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import geometry_mask
    from rasterio.warp import reproject, transform_geom
    from rasterio.windows import from_bounds
    from shapely.geometry import mapping, shape

    from crop_vigor import classify_vigor, field_metrics
    from sentinel1_mpc import _signed_href, get_runtime_sas_token
    from sentinel1_sources import search_sentinel1_sources

    search = search or search_sentinel1_sources
    token_fn = token_fn or get_runtime_sas_token
    g = field_gdf.to_crs(4326).geometry.union_all()
    # Catalogue search with the field's bounding box: pixel-shaped classifier
    # polygons have thousands of vertices and made the STAC request fail
    # (bug found in the 09/11/2026 Sinop test). Pixels still use the true field.
    from shapely.geometry import box as _box
    scene, scene_search_audit = _scene(_box(*g.bounds), as_of, window_days, search)
    if scene is None:
        providers=scene_search_audit.get("providers") or []
        search_audit={key:scene_search_audit.get(key) for key in
            ("providers","scene_count","pagination_complete","queried_at_utc")}
        incomplete=(not providers or
                    scene_search_audit.get("pagination_complete") is not True or
                    any(row.get("status") != "OK" for row in providers))
        if incomplete:
            return {"status":"ERRO_TECNICO",
                    "reason":"catálogo Sentinel-1 incompleto ou com falha em uma rota; ausência não comprovada",
                    "search_window_days":window_days,"as_of":as_of.isoformat(),
                    "scene_search_audit":search_audit}
        return {"status": "N/D", "reason": f"sem cena Sentinel-1 RTC VV/VH nos últimos {window_days} dias",
                "search_window_days": window_days, "as_of": as_of.isoformat(),
                "scene_search_audit":search_audit}
    # Catalog entries alone are not evidence of current, acquired SAR pixels.
    # Reject stale/future scene dates even if a custom STAC backend returns them.
    acquired = datetime.fromisoformat(str(scene.get("acquisition_utc", "")).replace("Z", "+00:00"))
    reference = datetime.combine(as_of, datetime.max.time()).replace(tzinfo=timezone.utc)
    if acquired.tzinfo is None:
        return {"status": "N/D", "reason": "cena sem timezone de aquisição", "scene_id": scene["id"]}
    age_days = (reference - acquired.astimezone(timezone.utc)).total_seconds() / 86400.0
    if age_days < 0 or age_days > window_days:
        return {"status": "N/D", "reason": f"cena fora da janela de atualidade de {window_days} dias",
                "scene_id": scene["id"], "acquisition_utc": scene["acquisition_utc"],
                "scene_age_days": age_days}
    provider=scene.get("provider","MPC")
    token = (token_fn or get_runtime_sas_token)() if provider=="MPC" else ""
    import tls_setup
    env={"GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR","GDAL_HTTP_MAX_RETRY":"3",
         "GDAL_HTTP_TIMEOUT":"35",**tls_setup.gdal_env()}
    def scene_href(pol):
        href=scene["assets"][pol]["href"]
        return _signed_href(href,token) if provider=="MPC" else href
    with rasterio.Env(**env):
        with rasterio.open(scene_href("vh")) as vh_src, \
             rasterio.open(scene_href("vv")) as vv_src:
            crs = vh_src.crs
            if not crs or not vv_src.crs:
                return {"status":"N/D","reason":"cenas SAR sem CRS válido"}
            gf = shape(transform_geom("EPSG:4326", crs, mapping(g)))
            ring = gf.buffer(ring_km * 1000.0)
            win = from_bounds(*ring.bounds, transform=vh_src.transform).round_offsets().round_lengths()
            win = win.intersection(rasterio.windows.Window(0, 0, vh_src.width, vh_src.height))
            if win.width<1 or win.height<1 or win.width>max_px or win.height>max_px:
                return {"status": "N/D", "reason": "janela SAR vazia ou excede o limite; reduzir ring_km"}
            tr = vh_src.window_transform(win)
            vh = np.ma.filled(vh_src.read(1,window=win,masked=True).astype(np.float32),np.nan)
            # VV may have a different transform/extent from VH. Read only its
            # cropped COG window, then align to the VH grid before ratios.
            vv_ring=shape(transform_geom("EPSG:4326",vv_src.crs,mapping(g))).buffer(ring_km*1000)
            vwin=from_bounds(*vv_ring.bounds,transform=vv_src.transform).round_offsets().round_lengths()
            vwin=vwin.intersection(rasterio.windows.Window(0,0,vv_src.width,vv_src.height))
            if vwin.width<1 or vwin.height<1 or vwin.width>max_px or vwin.height>max_px:
                return {"status":"N/D","reason":"janela VV não intercepta o campo ou excede o limite"}
            vv_source=np.ma.filled(vv_src.read(1,window=vwin,masked=True).astype(np.float32),np.nan)
            vv=np.full(vh.shape,np.nan,dtype=np.float32)
            reproject(vv_source,vv,src_transform=vv_src.window_transform(vwin),
                      src_crs=vv_src.crs,src_nodata=np.nan,
                      dst_transform=tr,dst_crs=crs,dst_nodata=np.nan,
                      resampling=Resampling.nearest)
    for a in (vh, vv):
        a[(a <= 0) | ~np.isfinite(a)] = np.nan
    vh_db, vv_db = 10 * np.log10(vh), 10 * np.log10(vv)
    shp = vh.shape
    field_mask = geometry_mask([mapping(gf)], out_shape=shp, transform=tr, invert=True)
    in_field = field_mask & np.isfinite(vh_db) & np.isfinite(vv_db)
    if in_field.sum() < 30:
        return {"status": "N/D", "reason": "talhão com menos de 30 pixels SAR válidos"}
    fvh=np.where(field_mask,vh_db,np.nan); fvv=np.where(field_mask,vv_db,np.nan)
    refs=[]; used=0; peer_labels=[]
    if reference_gdf is not None and not reference_gdf.empty and reference_gdf.crs:
        peers=reference_gdf.to_crs(crs)
        for row in peers.itertuples():
            geom=row.geometry
            if geom is None or geom.is_empty or geom.intersects(gf):
                continue
            if not ring.intersects(geom):
                continue
            peer_mask=geometry_mask([mapping(geom)],out_shape=shp,transform=tr,invert=True)
            peer_mask &= ~field_mask & np.isfinite(vh_db) & np.isfinite(vv_db)
            if int(peer_mask.sum())<30:
                continue
            peer_height=None
            if height_provider is not None:
                try:
                    peer_product=height_provider(reference_gdf,scene,crs,tr,shp,peer_mask)
                    from crop_height_features import check_crop_height_observation
                    peer_height_audit=check_crop_height_observation(
                        peer_product.get("observation"),peer_product.get("contract"))
                    candidate_height=np.asarray(peer_product.get("height_m"),dtype=float)
                    if peer_height_audit.get("eligible") and candidate_height.shape==shp:
                        peer_height=candidate_height
                except Exception:
                    peer_height=None
            try:
                metric=field_metrics(np.where(peer_mask,vh_db,np.nan),
                                     np.where(peer_mask,vv_db,np.nan),height_m=peer_height)
                refs.append(metric); used+=1
                peer_labels.append(str(getattr(row,"class_name",crop_name)))
            except ValueError:
                continue
    candidate_blocks = reference_mode == "sar_candidate_blocks"
    annual_mask_blocks = reference_mode == "annual_experimental_crop_mask"
    if used < MIN_REFERENCE_BLOCKS:
        reference_label = ("blocos espaciais SAR candidatos" if candidate_blocks else
                           "blocos espaciais da máscara anual experimental" if annual_mask_blocks else
                           "talhões SAR independentes")
        return {"status":"N/D",
                "reason":f"só {used} {reference_label} no raio de {ring_km} km; vigor relativo requer {MIN_REFERENCE_BLOCKS}",
                "scene_id":scene["id"],"acquisition_utc":scene["acquisition_utc"],
                "reference_fields":None if (candidate_blocks or annual_mask_blocks) else used,
                "reference_blocks":used if (candidate_blocks or annual_mask_blocks) else None,
                "reference_source":("blocos não sobrepostos da máscara SAR atual experimental" if candidate_blocks else
                    "blocos não sobrepostos da máscara anual SAR experimental; classe atual não confirmada" if annual_mask_blocks else
                    "classes atuais do classificador SAR validado")}
    height_array=None; height_audit={"eligible":False,"reasons":["modelo de altura não configurado"]}
    if height_provider is not None:
        try:
            product=height_provider(field_gdf,scene,crs,tr,shp,field_mask)
            from crop_height_features import check_crop_height_observation
            height_audit=check_crop_height_observation(product.get("observation"),product.get("contract"))
            if height_audit.get("eligible"):
                height_array=np.asarray(product.get("height_m"),dtype=float)
                if height_array.shape!=shp:
                    height_audit={"eligible":False,"reasons":["grade de altura difere da grade SAR"]}
                    height_array=None
        except Exception as exc:
            height_audit={"eligible":False,"reasons":[type(exc).__name__+": "+str(exc)[:160]]}
    partial_metrics=field_metrics(fvh,fvv,height_m=height_array)
    out=classify_vigor(fvh,fvv,refs,height_m=height_array,n_boot=200)
    reference_definition = (
        "blocos espaciais não sobrepostos da máscara de candidatos cultivados SAR da mesma AOI e aquisição; cultura não identificada"
        if candidate_blocks else
        "blocos espaciais não sobrepostos derivados da máscara anual SAR experimental da cultura; Sentinel-1 é atual, mas a permanência da cultura no local não está confirmada"
        if annual_mask_blocks else
        "talhões de cultura em geometrias independentes classificadas pelo mesmo modelo SAR aceito; pixels fora do talhão-alvo, mesma cena e janela")
    out.update({"scene_id":scene["id"],"acquisition_utc":scene["acquisition_utc"],
                "scene_age_days":round(age_days,2),"search_window_days":window_days,
                "reference_fields":None if (candidate_blocks or annual_mask_blocks) else used,
                "reference_blocks":used if (candidate_blocks or annual_mask_blocks) else None,
                "reference_definition":reference_definition,
                "reference_labels":peer_labels,
                "height_audit":height_audit,
                "partial_metrics":partial_metrics,
                "crop":crop_name,
                "source":("Sentinel-1 RTC VV/VH atual + máscara de candidatos SAR experimental; não confirma cultura"
                          if candidate_blocks else
                          "Sentinel-1 RTC VV/VH atual sobre máscara anual SAR experimental; permanência da cultura não confirmada"
                          if annual_mask_blocks else
                          "Sentinel-1 RTC VV/VH atual + máscara SAR validada; MapBiomas não utilizado"),
                "conditional_scope":"SAFRA_ANTERIOR_MASK_X_SAR_ATUAL" if annual_mask_blocks else
                                   "CANDIDATO_CULTIVADO" if candidate_blocks else "MASCARA_CULTURA_ACEITA"})
    return out
