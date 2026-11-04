"""Strict AGB structural-fusion contract.

Canopy height must be a real SAR height product; crown projected area must be
measured from actual SAR pixels with validated segmentation (not a GLCM proxy).
Mean DBH and stand basal area must come from physiognomy-matched field plots.
A numeric AGB only comes from locally validated coefficients on matched
height, crown, DBH, G inputs. No empirical coefficients are fabricated.
"""
from __future__ import annotations
from math import isfinite,sqrt
from datetime import datetime

def _positive(v):
    try:
        v=float(v)
        return v if isfinite(v) and v>0 else None
    except (TypeError,ValueError,OverflowError):
        return None

def _nonnegative(v):
    try:
        v=float(v)
        return v if isfinite(v) and v>=0 else None
    except (TypeError,ValueError,OverflowError):
        return None

def agb_sar_crown_inventory_contract(height, crown, inventory, model, *,
                                     biome, physiognomy):
    """A data/validation gate; output a computed AGB only with all actual inputs.

    Required validated functional form is per-hectare:
    AGB = beta0 + beta_h*H + beta_c*C + beta_d*D + beta_g*G
    where H in metres, C projected canopy cover in m²/ha, D mean DBH in cm
    and G basal area in m²/ha. This is NOT a physically universal equation;
    coefficients must be fitted and independently validated for the domain.
    """
    result={"status":"AGB_ESTRUTURAL_N/D","agb_mg_ha":None,
            "height_sar_m":None,"crown_area_sar_m2_ha":None,
            "dbh_inventory_cm":None,"basal_area_inventory_m2_ha":None,
            "uncertainty_mg_ha":None,"missing":[],"model_id":None,
            "limitation":"Não converter textura S1 em área de copa ou altura sem segmentação/calibração verificadas."}
    if not isinstance(height,dict):height={}
    if not isinstance(crown,dict):crown={}
    if not isinstance(inventory,dict):inventory={}
    if not isinstance(model,dict):model={}
    h=_positive(height.get("height_mean_m"))
    if (h is None or _positive(height.get("height_n_valid_pixels")) is None
        or height.get("product") not in ("FP_FH__L2B","Pantropical Forest Height and Biomass from GEDI and TanDEM-X Data Fusion")
        or not height.get("source")):
        result["missing"].append("altura SAR real com produto e pixels válidos")
    else:result["height_sar_m"]=h
    c=_positive(crown.get("projected_crown_area_m2_ha"))
    if (c is None or c>10000 or not crown.get("sar_scene_id")
        or crown.get("derived_from_sar_pixels") is not True
        or crown.get("validated_segmentation") is not True
        or _positive(crown.get("independent_validation_n")) is None
        or not crown.get("method_url")):
        result["missing"].append("área de projeção de copas SAR validada na AOI")
    else:result["crown_area_sar_m2_ha"]=c
    d=_positive(inventory.get("dbh_mean_cm"))
    g=_positive(inventory.get("basal_area_m2_ha"))
    if (d is None or g is None or not inventory.get("source_url")
        or inventory.get("biome")!=biome
        or inventory.get("physiognomy")!=physiognomy
        or inventory.get("tier") not in ("microrregional","regional")
        or _positive(inventory.get("n_independent_plots")) is None):
        result["missing"].append("inventário de DAP e G compatível por fitofisionomia e região")
    else:
        result["dbh_inventory_cm"]=d
        result["basal_area_inventory_m2_ha"]=g
        result["inventory_source"]=inventory.get("source_url")
        result["inventory_tier"]=inventory["tier"]
    coefficients=model.get("coefficients")
    needed=("intercept","height","crown_area","dbh","basal_area")
    if (not isinstance(coefficients,dict) or any(k not in coefficients or
        _nonnegative(coefficients[k]) is None and k!="intercept"
        for k in needed)
        or _positive(model.get("independent_rmse_mg_ha")) is None
        or model.get("independent_validation") is not True
        or model.get("biome")!=biome or model.get("physiognomy")!=physiognomy
        or not model.get("model_id") or not model.get("source_url")
        or model.get("height_metric")!=height.get("height_metric")):
        result["missing"].append("modelo AGB H+C+D+G com coeficientes e RMSE independentes no domínio")
    if result["missing"]:
        return result
    try:
        betas={k:float(coefficients[k]) for k in needed}
        if not all(isfinite(x) for x in betas.values()):
            raise ValueError("coeficientes inválidos")
        agb=(betas["intercept"]+betas["height"]*h+
             betas["crown_area"]*c+betas["dbh"]*d+betas["basal_area"]*g)
    except (TypeError,ValueError,OverflowError):
        result["missing"].append("coeficientes numéricos inválidos")
        return result
    if not isfinite(agb) or agb<=0:
        result["missing"].append("biomassa calculada não física")
        return result
    result.update(status="AGB_SAR_ESTRUTURAL_EXPERIMENTAL_VALIDADO_NO_DOMINIO",
                  agb_mg_ha=agb,uncertainty_mg_ha=float(model["independent_rmse_mg_ha"]),
                  uncertainty_kind="RMSE independente do modelo; não abrange automaticamente erro de extrapolação",
                  model_id=model["model_id"],model_source=model["source_url"],
                  source="Altura SAR + área copa SAR + DAP/área basal de inventário regional")
    return result
