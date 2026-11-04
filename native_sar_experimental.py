"""Experimental SAR-only screening index for native-vegetation field checks.

This is a transparent, unsupervised ranking index, not a calibrated probability
or validated native-cover classifier. It uses Sentinel-1 VV/VH spatial texture,
multiscale morphology and local directional anisotropy. Threshold-area spread
is a sensitivity range, not a confidence interval.
"""
from __future__ import annotations

from pathlib import Path
import math
import re


def native_structure_index(vv, vh, *, mask=None):
    """Return 0..1 relative screening scores and component feature arrays."""
    import numpy as np
    from scipy.ndimage import uniform_filter, grey_opening, grey_closing

    vv = np.asarray(vv, dtype=float)
    vh = np.asarray(vh, dtype=float)
    if vv.ndim != 2 or vh.shape != vv.shape or min(vv.shape) < 7:
        raise ValueError("VV/VH devem ser grades 2D coincidentes, com pelo menos 7×7 pixels")
    valid = np.isfinite(vv) & np.isfinite(vh)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != vv.shape:
            raise ValueError("Máscara AOI incompatível com VV/VH")
        valid &= mask
    if valid.sum() < 49:
        return {"status": "N/D", "reason": "menos de 49 pixels SAR válidos", "score": None}

    # GRD/COG backscatter may be stored as linear power or dB. The conversion
    # is inferred conservatively from the VV/VH median sign and recorded.
    median = float(np.nanmedian(np.concatenate([vv[valid], vh[valid]])))
    if median > 0:
        if np.any(vv[valid] <= 0) or np.any(vh[valid] <= 0):
            raise ValueError("Backscatter linear contém valores não positivos")
        vv_db = np.full(vv.shape, np.nan)
        vh_db = np.full(vh.shape, np.nan)
        vv_db[valid] = 10.0 * np.log10(vv[valid])
        vh_db[valid] = 10.0 * np.log10(vh[valid])
        unit_handling = "potência linear convertida para dB"
    else:
        vv_db, vh_db = vv.copy(), vh.copy()
        unit_handling = "dB preservado"

    fill = float(np.nanmedian(vh_db[valid]))
    x = np.where(valid, vh_db, fill)
    # Spatial variability at two scales; local standard deviation is a
    # radiometric texture/rugosity proxy, not physical surface roughness.
    mean3 = uniform_filter(x, size=3, mode="nearest")
    sq3 = uniform_filter(x*x, size=3, mode="nearest")
    std3 = np.sqrt(np.maximum(0.0, sq3-mean3*mean3))
    mean7 = uniform_filter(x, size=7, mode="nearest")
    sq7 = uniform_filter(x*x, size=7, mode="nearest")
    std7 = np.sqrt(np.maximum(0.0, sq7-mean7*mean7))
    texture = 0.5*(std3+std7)

    # Morphological profile: response across structuring-element sizes
    # approximates characteristic spatial scale ("granulometry" of image
    # texture); it is not soil particle-size granulometry.
    morph = np.zeros(vv.shape, dtype=float)
    for size in (3, 5, 7):
        footprint = np.ones((size, size), dtype=bool)
        opened = grey_opening(x, footprint=footprint, mode="nearest")
        closed = grey_closing(x, footprint=footprint, mode="nearest")
        morph += np.abs(closed-opened)
    morph /= 3.0

    # Local directional anisotropy: aligned, repeated edges are a geometry
    # cue; it does not detect cadastral boundaries with certainty.
    dx = np.zeros_like(x); dy = np.zeros_like(x)
    dx[:, 1:] = np.abs(x[:, 1:]-x[:, :-1])
    dy[1:, :] = np.abs(x[1:, :]-x[:-1, :])
    gx = uniform_filter(dx, size=7, mode="nearest")
    gy = uniform_filter(dy, size=7, mode="nearest")
    anisotropy = np.abs(gx-gy)/(gx+gy+1e-6)

    def rank01(values):
        sample = values[valid & np.isfinite(values)]
        qs = np.nanquantile(sample, np.linspace(0, 1, 101))
        ranks = np.linspace(0, 1, len(qs))
        result = np.interp(values, qs, ranks)
        return np.clip(result, 0, 1)

    texture_rank = rank01(texture)
    morph_rank = rank01(morph)
    geometry_irregularity = 1.0-rank01(anisotropy)
    score = np.where(valid,
                     0.40*texture_rank + 0.35*morph_rank + 0.25*geometry_irregularity,
                     np.nan)
    return {
        "status": "SAR_EXPERIMENTAL_INDEX",
        "score": score,
        "features": {
            "texture_multiscale_db": texture,
            "morphological_scale_response_db": morph,
            "directional_anisotropy": anisotropy,
        },
        "n_valid_pixels": int(valid.sum()),
        "unit_handling": unit_handling,
        "score_definition": "0.40 quantil-textura + 0.35 quantil-perfil-morfológico + 0.25 (1-quantil-anisotropia)",
        "feature_semantics": {
            "texture_multiscale_db": "proxy de heterogeneidade/ rugosidade radiométrica VV/VH",
            "morphological_scale_response_db": "granulometria da textura da imagem em escalas 3/5/7 pixels; não granulometria do solo",
            "directional_anisotropy": "proxy de alinhamento geométrico local",
        },
        "status_scientifico": "EXPERIMENTAL_NAO_CALIBRADO",
        "probability": None,
        "accuracy": None,
    }


def run_sentinel1_native_screen(aoi, sar_paths, output_dir, *, ibge=None, ibge_field="legenda_1",
                                candidate_threshold=0.65, max_pixels=8_000_000,
                                max_ibge_proximity_m=3000):
    """Create score raster, threshold-sensitivity areas and candidate GeoJSON."""
    import numpy as np
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask as raster_mask
    from rasterio.warp import reproject, Resampling
    from rasterio.features import geometry_mask, shapes

    paths=[Path(p) for p in (sar_paths or [])]
    if not paths:
        return {"status":"N/D","reason":"nenhum GeoTIFF SAR fornecido"}
    norm=lambda p:re.sub(r"[^a-z0-9]","",p.name.casefold())
    vv_path=next((p for p in paths if re.search(r"(^|s1a|s1b|s1c|sentinel1|sentinel)(.*)(vv|sigma0vv)",norm(p))),None)
    vh_path=next((p for p in paths if re.search(r"(^|s1a|s1b|s1c|sentinel1|sentinel)(.*)(vh|sigma0vh)",norm(p))),None)
    if vv_path is None or vh_path is None:
        return {"status":"N/D","reason":"exige GeoTIFFs Sentinel-1 VV e VH identificáveis pelo nome; nenhuma cena de outros sensores é tratada como Sentinel-1"}
    outdir=Path(output_dir); outdir.mkdir(parents=True,exist_ok=True)

    with rasterio.open(vv_path) as vsrc, rasterio.open(vh_path) as hsrc:
        if vsrc.crs is None or hsrc.crs is None:
            return {"status":"N/D","reason":"CRS ausente nos rasters VV/VH"}
        target_crs=vsrc.crs
        geom=aoi.to_crs(target_crs).geometry
        vv_clip, transform=raster_mask(vsrc,[g.__geo_interface__ for g in geom],crop=True,filled=False)
        vv=np.asarray(vv_clip[0].filled(np.nan),dtype=float)
        vh_full=np.full(vv.shape,np.nan,dtype=np.float32)
        reproject(source=rasterio.band(hsrc,1),destination=vh_full,
                  src_transform=hsrc.transform,src_crs=hsrc.crs,
                  dst_transform=transform,dst_crs=target_crs,
                  resampling=Resampling.bilinear,nodata=hsrc.nodata,
                  dst_nodata=np.nan)
        valid_geom=~geometry_mask([g.__geo_interface__ for g in geom],out_shape=vv.shape,
                                  transform=transform,invert=False)
        valid=valid_geom & np.isfinite(vv) & np.isfinite(vh_full)
        if int(valid.sum())>max_pixels:
            return {"status":"N/D","reason":f"{int(valid.sum())} pixels excedem o limite de processamento {max_pixels}; dividir AOI"}
        result=native_structure_index(vv,vh_full,mask=valid)
        if result.get("score") is None:
            return {k:v for k,v in result.items() if k!="score"}
        score=result.pop("score")
        resx,resy=vsrc.res
        score_path=outdir/"indice_estrutura_nativa_sar_experimental.tif"
        profile=vsrc.profile.copy()
        profile.update(driver="GTiff",height=score.shape[0],width=score.shape[1],count=1,
                       dtype="float32",transform=transform,nodata=-9999,compress="deflate")
        with rasterio.open(score_path,"w",**profile) as dst:
            dst.write(np.where(np.isfinite(score),score,-9999).astype("float32"),1)
            dst.update_tags(model="experimental_native_sar_screen_v1",
                            score_definition=result["score_definition"],
                            probability="none",accuracy="none",
                            inputs=f"{vv_path.name};{vh_path.name}")

        thresholds=[0.55,0.65,0.75,0.85]
        areas={}
        pixel_geoms={}
        for threshold in thresholds:
            binary=np.isfinite(score)&(score>=threshold)&valid
            features=list(shapes(binary.astype("uint8"),mask=binary,transform=transform))
            geoms=[gpd.GeoSeries.from_wkb([__import__("shapely").geometry.shape(g).wkb],crs=target_crs).iloc[0]
                   for g,val in features if val==1]
            # Use exact equal-area geometry, avoiding degree-squared area.
            area=gpd.GeoSeries(geoms,crs=target_crs).to_crs("EPSG:6933").area.sum()/10000 if geoms else 0.0
            areas[f"{threshold:.2f}"]={"area_ha":float(area),"patch_count":len(geoms)}
            pixel_geoms[threshold]=geoms
        if candidate_threshold not in pixel_geoms:
            raise ValueError("candidate_threshold deve ser um dos limiares de sensibilidade")
        selected=pixel_geoms[candidate_threshold]
        rows=[]
        ibge_projected=None
        if ibge is not None and not ibge.empty:
            ibge_projected=ibge.to_crs("EPSG:6933")
        for geom in selected:
            row={"class_name":"Vegetação nativa candidata SAR (experimental)",
                 "source":"SENTINEL1_EXPERIMENTAL_STRUCTURE_INDEX",
                 "taxonomy":("Índice de triagem SAR sem probabilidade/acurácia calibrada; "+
                             "limiar "+f"{candidate_threshold:.2f}")}
            if ibge_projected is not None:
                centroid=gpd.GeoSeries([geom],crs=target_crs).to_crs("EPSG:6933").iloc[0].centroid
                distances=ibge_projected.geometry.distance(centroid)
                idx=int(distances.idxmin())
                nearest=ibge_projected.loc[idx]
                distance=float(distances.loc[idx])
                row["ibge_nearest_label"]=str(nearest.get(ibge_field,"")) if distance<=max_ibge_proximity_m else None
                row["ibge_nearest_distance_m"]=distance
                row["taxonomy"] += ("; nome IBGE por proximidade="+str(row["ibge_nearest_label"])+
                                   f" ({distance:.1f} m)" if row["ibge_nearest_label"] else
                                   "; nenhuma classe IBGE dentro do limite de proximidade")
            row["geometry"]=geom
            rows.append(row)
        vector_path=outdir/"vegetacao_nativa_candidata_sar_experimental.geojson"
        if rows:
            gpd.GeoDataFrame(rows,geometry="geometry",crs=target_crs).to_file(vector_path,driver="GeoJSON")
        else:
            gpd.GeoDataFrame(columns=["class_name","source","taxonomy","geometry"],
                             geometry="geometry",crs=target_crs).to_file(vector_path,driver="GeoJSON")
    return {
        "status":"SAR_EXPERIMENTAL_CANDIDATE_SCREEN",
        "native_presence_confirmed":False,
        "model":"Índice de triagem SAR não supervisionado v1",
        "sensors":["Sentinel-1 C VV","Sentinel-1 C VH"],
        "inputs":[str(vv_path),str(vh_path)],
        "score_range":[0.0,1.0],
        "candidate_threshold":candidate_threshold,
        "threshold_sensitivity_area_ha":areas,
        "sensitivity_range_ha":[areas["0.85"]["area_ha"],areas["0.55"]["area_ha"]],
        "sensitivity_is":"faixa de sensibilidade a limiares, não intervalo de confiança nem acurácia",
        "n_valid_pixels":result["n_valid_pixels"],
        "unit_handling":result["unit_handling"],
        "score_definition":result["score_definition"],
        "feature_semantics":result["feature_semantics"],
        "status_scientifico":result["status_scientifico"],
        "probability":None,"accuracy":None,
        "score_raster_path":str(score_path),
        "candidate_vector_path":str(vector_path),
        "ibge_naming":"classe mais próxima por distância até 3 km; serve apenas para nomeação cartográfica",
        "limits":[
            "a camada mostra candidatos de estrutura compatível, não comprova cobertura nativa",
            "não há treinamento supervisionado nem validação independente",
            "a faixa de área representa sensibilidade a limiares, não erro de classificação",
            "não substitui inspeção de campo nem classes SAR validadas"
        ]
    }
