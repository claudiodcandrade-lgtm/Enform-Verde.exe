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

def _finite_coeff(v):
    try:
        value=float(v)
        return value if isfinite(value) else None
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
    if (not isinstance(coefficients,dict) or any(k not in coefficients or _finite_coeff(coefficients[k]) is None
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


DBH_DISTRIBUTION_SCHEME = "dbh_5_10_20_30_40_60plus_v2_total_ba_plus_class_shares"
DBH_DISTRIBUTION_BINS = ("dbh_5_10_cm", "dbh_10_20_cm", "dbh_20_30_cm",
                         "dbh_30_40_cm", "dbh_40_60_cm", "dbh_60_plus_cm")
DBH_DISTRIBUTION_SHAPE = DBH_DISTRIBUTION_BINS[1:]


def agb_sar_height_diameter_distribution(height, inventory, model, *, biome, physiognomy):
    """Integrate SAR canopy height with an inventory diameter-class distribution.

    Deployment form:
      log(AGB) = beta0 + betaH*log(H_SAR) + betaG*log(G_total)
                 + sum_k beta_k*share(G_k), k = classes 10 cm and above
      AGB = smearing_factor * exp(log(AGB))

    G_total is mean inventory basal area per hectare; G_k/G_total are class
    shares, with 5–10 cm as the compositional reference to avoid redundancy.
    This
    estimator is intentionally unavailable until independent, domain-matched
    calibration and validation supply every coefficient and the retransformation
    factor. Tests validate the calculation contract, not scientific accuracy.
    """
    from math import exp, log
    result={"status":"AGB_DISTRIBUICAO_DIAMETRICA_N/D","agb_mg_ha":None,
            "height_sar_m":None,"inventory_dbh_distribution":None,
            "uncertainty_mg_ha":None,"missing":[],
            "formula":"AGB = smearing_factor × exp(β0 + βH·ln(H_SAR) + βG·ln(G_total) + Σβk·share(Gk), k≥10 cm; 5–10 cm é a classe de referência)"}
    height=height if isinstance(height,dict) else {}
    inventory=inventory if isinstance(inventory,dict) else {}
    model=model if isinstance(model,dict) else {}
    h=_positive(height.get("height_mean_m"))
    if (h is None or _positive(height.get("height_n_valid_pixels")) is None
            or height.get("sensor_family")!="SAR"
            or not height.get("source") or not height.get("height_metric")):
        result["missing"].append("altura de dossel obtida de pixels SAR reais na AOI")
    else:
        result["height_sar_m"]=h
    basal_area_total=_positive(inventory.get("community_mean_basal_area_m2_ha"))
    if (inventory.get("biome")!=biome or inventory.get("physiognomy")!=physiognomy
            or inventory.get("tier") not in ("microrregional","regional")
            or not inventory.get("microregion") or not inventory.get("source_url")
            or _positive(inventory.get("n_independent_plots")) is None
            or inventory.get("dbh_distribution_scheme_id")!=DBH_DISTRIBUTION_SCHEME):
        result["missing"].append("distribuição diamétrica de inventário compatível e georreferenciada")
    bins=inventory.get("dbh_distribution_by_plot_mean") or []
    by_id={str(row.get("bin_id")):row for row in bins if isinstance(row,dict)}
    if len(by_id)!=len(DBH_DISTRIBUTION_BINS) or any(
            bin_id not in by_id or _nonnegative(by_id[bin_id].get("mean_basal_area_m2_ha")) is None
            for bin_id in DBH_DISTRIBUTION_BINS):
        result["missing"].append("área basal por hectare em todas as classes diamétricas requeridas")
    elif basal_area_total is None:
        result["missing"].append("área basal média total do inventário")
    else:
        bin_total=sum(float(by_id[k]["mean_basal_area_m2_ha"]) for k in DBH_DISTRIBUTION_BINS)
        if not isfinite(bin_total) or abs(bin_total-basal_area_total)>max(0.05,0.02*basal_area_total):
            result["missing"].append("reconciliação entre área basal comunitária e soma dos bins DAP")
    coefficients=model.get("distribution_coefficients")
    model_coefficients=(isinstance(coefficients,dict)
        and all(_finite_coeff(coefficients.get("share_"+k)) is not None for k in DBH_DISTRIBUTION_SHAPE)
        and _finite_coeff(coefficients.get("intercept")) is not None
        and _finite_coeff(coefficients.get("height")) is not None
        and _finite_coeff(coefficients.get("basal_area_total")) is not None)
    if (not model_coefficients or model.get("dbh_distribution_scheme_id")!=DBH_DISTRIBUTION_SCHEME
            or _positive(model.get("smearing_factor")) is None
            or _positive(model.get("independent_rmse_mg_ha")) is None
            or model.get("independent_validation") is not True
            or int(model.get("independent_validation_n",0) or 0)<30
            or int(model.get("independent_validation_sites",0) or 0)<5
            or model.get("biome")!=biome or model.get("physiognomy")!=physiognomy
            or not model.get("model_id") or not model.get("source_url")):
        result["missing"].append("modelo H_SAR + distribuição DAP validado independentemente no domínio")
    if result["missing"]:
        return result
    try:
        eta=(float(coefficients["intercept"])+float(coefficients["height"])*log(h)
             +float(coefficients["basal_area_total"])*log(basal_area_total))
        for bin_id in DBH_DISTRIBUTION_SHAPE:
            share=float(by_id[bin_id]["mean_basal_area_m2_ha"])/basal_area_total
            eta+=float(coefficients["share_"+bin_id])*share
        agb=float(model["smearing_factor"])*exp(eta)
        rmse=float(model["independent_rmse_mg_ha"])
        if not isfinite(agb) or agb<=0 or not isfinite(rmse) or rmse<=0:
            raise ValueError("predição ou RMSE inválido")
    except (TypeError,ValueError,OverflowError):
        result["missing"].append("predição matemática ou erro de validação inválido")
        return result
    result.update(status="AGB_SAR_ALTURA_DISTRIBUICAO_DIAMETRICA_VALIDADA_NO_DOMINIO",
        agb_mg_ha=agb,uncertainty_mg_ha=rmse,
        uncertainty_kind="RMSE em sítios independentes; transferência espacial adicional não quantificada",
        model_id=model["model_id"],model_source=model["source_url"],
        inventory_source=inventory["source_url"],inventory_tier=inventory["tier"],
        inventory_microregion=inventory["microregion"],inventory_n_independent_plots=int(inventory["n_independent_plots"]),
        dbh_distribution_scheme_id=DBH_DISTRIBUTION_SCHEME,
        inventory_dbh_distribution=[{"bin_id":k,"basal_area_m2_ha":float(by_id[k]["mean_basal_area_m2_ha"])}
                                    for k in DBH_DISTRIBUTION_BINS],
        height_product=height.get("product"),height_source=height["source"],
        formula_trace={"linear_predictor":eta,"smearing_factor":float(model["smearing_factor"]),
            "height_metric":height["height_metric"],"basal_area_total_m2_ha":basal_area_total,
            "dbh_class_shares_reference_bin":DBH_DISTRIBUTION_BINS[0],"beta":coefficients},
        limitations=["inventário representa a microrregião/região, não medição da propriedade",
            "altura da propriedade vem exclusivamente de SAR",
            "erro de transferência regional não está incluído no RMSE independente"])
    return result
