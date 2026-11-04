"""Sentinel-1 texture with ESA BIOMASS direct forest-height evidence.

The direct ESA BIOMASS FP_FH__L2B height product provides metres.
Sentinel-1 C-band only adds quantitative structural features and acquisition
timestamps. A calibrated height residual is optional and requires a certified,
spatially independent field validation contract. No raw backscatter-to-height
formula is invented.
"""
from __future__ import annotations
from math import isfinite,sqrt
from datetime import datetime, timezone


def _num(v):
    try:
        v=float(v)
        return v if isfinite(v) else None
    except (TypeError,ValueError,OverflowError):
        return None


def sentinel1_structure_features(vv_linear, vh_linear, *, mask=None):
    """Sample-descriptive, not trained vegetation labels or tree height."""
    import numpy as np
    vv=np.asarray(vv_linear,dtype=float)
    vh=np.asarray(vh_linear,dtype=float)
    if vv.ndim!=2 or vh.shape!=vv.shape or min(vv.shape)<3:
        raise ValueError("Sentinel-1 VV e VH exigem a mesma grade 2D >=3x3")
    good=np.isfinite(vv)&np.isfinite(vh)&(vv>0)&(vh>0)
    if mask is not None:
        m=np.asarray(mask,dtype=bool)
        if m.shape!=vv.shape:raise ValueError("Máscara SAR incompatível")
        good &= m
    if good.sum()<9:
        return {"status":"N/D","reason":"menos de nove pixels VV/VH válidos","native_presence_confirmed":False}
    db_vv=10*np.log10(vv[good]);db_vh=10*np.log10(vh[good])
    ratio=db_vh-db_vv
    vh_grid=np.where(good,10*np.log10(np.maximum(vh,1e-20)),np.nan)
    pairs=[]
    for axis in (0,1):
        a,b=(vh_grid[:-1,:],vh_grid[1:,:]) if axis==0 else (vh_grid[:,:-1],vh_grid[:,1:])
        valid=np.isfinite(a)&np.isfinite(b)
        if valid.any():pairs.extend((a[valid]-b[valid]).tolist())
    neighbor=np.asarray(pairs,dtype=float)
    # Variance of neighboring radar pixels is a texture proxy, NOT physical
    # roughness in metres and not evidence of irregular boundaries alone.
    return {
        "status":"PIXELS_SAR_ESTRUTURAIS_PROCESSADOS",
        "n_pixels":int(good.sum()),
        "vv_median_db":float(np.median(db_vv)),
        "vh_median_db":float(np.median(db_vh)),
        "vh_vv_median_db":float(np.median(ratio)),
        "vh_spatial_iqr_db":float(np.subtract(*np.percentile(db_vh,[75,25]))),
        "neighbor_dissimilarity_db":float(np.mean(np.abs(neighbor))) if len(neighbor) else None,
        "neighbor_rms_contrast_db":float(np.sqrt(np.mean(neighbor**2))) if len(neighbor) else None,
        "native_presence_confirmed":False,
        "height_measured":False,
        "notes":"Textura/rugosidade radiométrica não são rugosidade geométrica em metros; identidade nativa exige classificação SAR e validação independentes.",
    }


def combine_biomass_sentinel1_height(biomass_fh, sentinel1=None, *, residual_model=None):
    """Prefer direct ESA FH height, append S1 supporting evidence.

    A residual correction, if provided, requires external validated RMSE and
    a matching AOI domain+height definition; otherwise FH remains unchanged.
    """
    out={"status":"N/D","height_mean_m":None,
         "height_source":"ESA BIOMASS FP_FH__L2B",
         "sentinel1_role":"contexto estrutural/temporal, não altura direta",
         "scientific_scope":"mensuração ao nível AOI, nunca altura de cada árvore"}
    h=_num((biomass_fh or {}).get("height_mean_m"))
    n=(biomass_fh or {}).get("height_n_valid_pixels")
    if h is None or h<=0 or str((biomass_fh or {}).get("product"))!="FP_FH__L2B" or not isinstance(n,int) or n<1:
        out["reason"]="FH L2B sem pixels de altura válidos no polígono"
        return out
    out.update(status="ALTURA_BIOMASS_DIRETA",height_mean_m=h,
               height_product="FP_FH__L2B",height_n_valid_pixels=n,
               biomass_source=(biomass_fh or {}).get("source"),
               height_metric=(biomass_fh or {}).get("height_metric"),
               height_product_uncertainty_m=_num((biomass_fh or {}).get("height_standard_error_pixel_zonal_mean_m")))
    if not isinstance(sentinel1,dict) or sentinel1.get("status")!="PIXELS_SAR_ESTRUTURAIS_PROCESSADOS":
        out["sentinel1_status"]="N/D; altura FH direta conservada"
        return out
    out["sentinel1_features"]={k:sentinel1.get(k) for k in
         ("n_pixels","vv_median_db","vh_median_db","vh_vv_median_db",
          "vh_spatial_iqr_db","neighbor_dissimilarity_db","neighbor_rms_contrast_db")}
    out["sentinel1_status"]="OBSERVACAO_ESTRUTURAL_DISPONIVEL"
    # The residual model must be an externally validated fitted object,
    # never inferred from a global citation or the SAR measurements alone.
    if not isinstance(residual_model,dict):
        out["correction_status"]="BLOQUEADA_SEM_MODELO_VALIDADO"
        return out
    if not (residual_model.get("independent_validation") is True
            and residual_model.get("in_domain_validation") is True
            and residual_model.get("compatible_height_metric") == out["height_metric"]
            and residual_model.get("aoi_spatial_match") is True):
        out["correction_status"]="BLOQUEADA_SEM_VALIDACAO_COMPATIVEL"
        return out
    weights=residual_model.get("coefficients")
    rmse=_num(residual_model.get("holdout_rmse_m"))
    if not isinstance(weights,dict) or rmse is None or rmse<=0:
        out["correction_status"]="BLOQUEADA_SEM_COEFICIENTES_E_RMSE"
        return out
    corr=_num(weights.get("intercept_m",0.0))
    if corr is None:
        out["correction_status"]="BLOQUEADA_COEFICIENTES_INVALIDOS";return out
    for feature, coefficient in weights.items():
        if feature=="intercept_m":continue
        if feature not in out["sentinel1_features"]:
            out["correction_status"]="BLOQUEADA_ATRIBUTO_INDISPONIVEL";return out
        v=_num(out["sentinel1_features"][feature]);c=_num(coefficient)
        if v is None or c is None:
            out["correction_status"]="BLOQUEADA_ATRIBUTO_INVALIDO";return out
        corr+=v*c
    adjusted=h+corr
    if not isfinite(adjusted) or adjusted<=0:
        out["correction_status"]="BLOQUEADA_ALTURA_FISICAMENTE_INVALIDA";return out
    out["height_mean_m"]=adjusted
    out["correction_status"]="FUSAO_RESIDUAL_VALIDADA_NO_DOMINIO"
    out["status"]="ALTURA_BIOMASS_S1_FUSAO_VALIDADA"
    out["height_residual_correction_m"]=corr
    out["height_model_holdout_rmse_m"]=rmse
    out["uncertainty_kind"]="RMSE holdout e erro do produto apresentados separadamente; não assumir independência"
    return out
