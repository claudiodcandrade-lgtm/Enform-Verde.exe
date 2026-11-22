"""Regional gravimetric calibration for IFN litter-depth observations.

Depth-only IFN records cannot be converted to carbon with a national constant.
This module requires open IFN target depths and independent, same-region and
same-physiognomy depth/dry-mass calibration samples. It returns an explicitly
experimental estimate and a full calculation trace; it never labels the
clustered bootstrap interval as a farm-level confidence interval.
"""
from __future__ import annotations

import math
import unicodedata
from collections import defaultdict

import numpy as np


MIN_CALIBRATION_POINTS = 30
MIN_CALIBRATION_UNITS = 5
MIN_TARGET_UNITS = 5
MAX_IFN_DISTANCE_KM = 250.0


def _norm(value):
    text=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(ch for ch in text if ch.isalnum() and not unicodedata.combining(ch))


def _float(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (TypeError,ValueError,OverflowError):
        return None


def _distance_km(lon1,lat1,lon2,lat2):
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371.0088*2*math.asin(min(1.0,math.sqrt(h)))


def _validated_record(row, biome, physiognomy, region):
    return (_norm(row.get("biome"))==_norm(biome)
            and _norm(row.get("physiognomy"))==_norm(physiognomy)
            and _norm(row.get("region"))==_norm(region))


def estimate_litter_carbon_from_depth(records, *, biome, physiognomy, region,
                                      aoi_lon, aoi_lat, seed=20261113,
                                      bootstrap_replicates=2000):
    """Estimate standing-litter C from nearby open IFN depth plus paired gravimetry.

    Record contract:
      * calibration: ``record_type='gravimetric_calibration'`` with depth_cm,
        dry_mass_g, sample_area_m2, unit_id, same biome/physiognomy/region,
        source/source_url/institution and measured carbon_fraction.
      * IFN target: ``record_type='ifn_depth'`` with depth_cm, unit_id, lon,
        lat, source/source_url/institution, ``open_data=True`` and the same
        biome/physiognomy/region.

    Calibration is grouped by independent unit. Target IFN units are sorted by
    geodesic distance and only the five closest within 250 km are used. The
    response is dry mass per area (g/m2); the model is ``m = beta0 + beta1*d``.
    Carbon is computed from a measured calibration carbon fraction when
    present. Without one, mass is returned but carbon is N/D: a carbon fraction
    must not be silently inferred from dry mass or a generic constant.
    """
    result={"status":"N/D_CONVERSAO_PROFUNDIDADE_SEM_PARES_GRAVIMETRICOS",
            "mean_tc_ha":None,"uncertainty":None,"source":None,
            "calculation_trace":None,"limitations":[]}
    if not isinstance(records,(list,tuple)):
        result["reason"]="EVIDENCIAS_IFN_INVALIDAS"; return result
    calibr=[];targets=[]
    for r in records:
        if not isinstance(r,dict) or not _validated_record(r,biome,physiognomy,region):
            continue
        if r.get("record_type")=="gravimetric_calibration":
            d=_float(r.get("depth_cm")); m=_float(r.get("dry_mass_g")); a=_float(r.get("sample_area_m2"))
            if (d is not None and d>0 and m is not None and m>=0 and a is not None and a>0
                    and r.get("unit_id") and r.get("source") and r.get("source_url")
                    and r.get("institution")):
                calibr.append((r,d,m/a)) # g/m2
        elif r.get("record_type")=="ifn_depth" and r.get("open_data") is True:
            d=_float(r.get("depth_cm")); lon=_float(r.get("lon")); lat=_float(r.get("lat"))
            if (d is not None and d>=0 and lon is not None and lat is not None
                    and r.get("unit_id") and r.get("source") and r.get("source_url")
                    and r.get("institution") and "ifn" in _norm(r.get("institution"))):
                targets.append((r,d,_distance_km(aoi_lon,aoi_lat,lon,lat)))
    cal_units={str(row[0].get("unit_id")) for row in calibr}
    if len(calibr)<MIN_CALIBRATION_POINTS or len(cal_units)<MIN_CALIBRATION_UNITS:
        result.update(reason="CALIBRACAO_EXIGE_30_AMOSTRAS_E_5_UNIDADES_INDEPENDENTES",
                      calibration_point_count=len(calibr),calibration_unit_count=len(cal_units))
        return result
    targets=[r for r in targets if r[2]<=MAX_IFN_DISTANCE_KM]
    by_target=defaultdict(list)
    for r in targets:by_target[str(r[0]["unit_id"])].append(r)
    units=[]
    for uid,rows in by_target.items():
        units.append((min(r[2] for r in rows),uid,rows))
    units.sort(key=lambda r:(r[0],r[1]))
    units=units[:MIN_TARGET_UNITS]
    if len(units)<MIN_TARGET_UNITS:
        result.update(reason="MENOS_DE_5_UNIDADES_IFN_ABERTAS_COMPATIVEIS_DENTRO_DE_250_KM",
                      nearby_target_unit_count=len(units))
        return result
    x=np.asarray([r[1] for r in calibr],dtype=float)
    y=np.asarray([r[2] for r in calibr],dtype=float)
    design=np.column_stack([np.ones(len(x)),x])
    # Give each independent calibration unit equal total weight so that a
    # densely sampled plot cannot masquerade as many independent plots.
    cal_by_unit=defaultdict(list)
    for i,row in enumerate(calibr):cal_by_unit[str(row[0]["unit_id"])].append(i)
    weights=np.asarray([1.0/len(cal_by_unit[str(row[0]["unit_id"])]) for row in calibr])
    beta=np.linalg.lstsq(design*np.sqrt(weights[:,None]),y*np.sqrt(weights),rcond=None)[0]
    if beta[1]<0 or not np.all(np.isfinite(beta)):
        result["reason"]="RELACAO_PROFUNDIDADE_MASSA_NAO_FISICAMENTE_PLAUSIVEL";return result
    predicted=[];observed=[]
    for uid,idx in cal_by_unit.items():
        train=np.asarray([i for key,values in cal_by_unit.items() if key!=uid for i in values],dtype=int)
        if len(train)<2:continue
        wd=np.asarray([1.0/len([j for j in train if str(calibr[j][0]["unit_id"])==str(calibr[i][0]["unit_id"])]) for i in train])
        xd=np.column_stack([np.ones(len(train)),x[train]])
        b=np.linalg.lstsq(xd*np.sqrt(wd[:,None]),y[train]*np.sqrt(wd),rcond=None)[0]
        predicted.extend((b[0]+b[1]*x[idx]).tolist());observed.extend(y[idx].tolist())
    residual=np.asarray(observed)-np.asarray(predicted)
    loo_rmse=float(np.sqrt(np.mean(residual**2))) if len(residual) else None
    loo_bias=float(np.mean(residual)) if len(residual) else None
    if loo_rmse is None or not math.isfinite(loo_rmse):
        result["reason"]="VALIDACAO_AGRUPADA_POR_UNIDADE_INDISPONIVEL";return result
    target_depths=np.asarray([r[1] for _,_,rows in units for r in rows],dtype=float)
    if (np.min(target_depths)<np.min(x) or np.max(target_depths)>np.max(x)):
        result.update(reason="PROFUNDIDADE_IFN_FORA_DA_FAIXA_CALIBRADA_SEM_EXTRAPOLACAO",
                      calibration_depth_range_cm=[float(np.min(x)),float(np.max(x))],
                      target_depth_range_cm=[float(np.min(target_depths)),float(np.max(target_depths))])
        return result
    yhat=np.maximum(0.0,beta[0]+beta[1]*target_depths) # g/m2
    dry_mg_ha=float(np.mean(yhat)*0.01)
    cf=[_float(r[0].get("carbon_fraction")) for r in calibr]
    cf=[x for x in cf if x is not None and 0<x<1]
    if not cf:
        result.update(status="MASSA_SECA_ESTIMADA_CARBONO_ND",
                      dry_litter_mg_ha=dry_mg_ha,
                      reason="FRAÇÃO_DE_CARBONO_NÃO_MEDIDA_NAS_AMOSTRAS",
                      source="IFN/SFB aberto + calibração gravimétrica pareada compatível",
                      limitations=["massa seca estimada; carbono não calculado sem análise de C da mesma fonte"])
        return result
    carbon_fraction=float(np.mean(cf))
    stock_tc_ha=dry_mg_ha*carbon_fraction
    rng=np.random.default_rng(seed)
    cal_u=list(cal_by_unit)
    target_u=[r[1] for r in units]
    draws=[]
    # Cluster bootstrap resamples whole calibration UAs and whole target UAs.
    # It quantifies observed sampling/model variability only, not transfer to AOI.
    for _ in range(max(200,int(bootstrap_replicates))):
        pick=rng.choice(cal_u,size=len(cal_u),replace=True)
        ix=[i for uid in pick for i in cal_by_unit[str(uid)]]
        if len(ix)<3:continue
        boot_units=defaultdict(list)
        for i in ix:boot_units[str(calibr[i][0]["unit_id"])].append(i)
        bw=np.asarray([1.0/len(boot_units[str(calibr[i][0]["unit_id"])]) for i in ix])
        bd=np.column_stack([np.ones(len(ix)),x[ix]])
        b=np.linalg.lstsq(bd*np.sqrt(bw[:,None]),y[ix]*np.sqrt(bw),rcond=None)[0]
        if b[1]<0 or not np.all(np.isfinite(b)):continue
        t_units=rng.choice(len(units),size=len(units),replace=True)
        td=np.asarray([r[1] for ui in t_units for r in units[int(ui)][2]],dtype=float)
        pred=np.maximum(0.0,b[0]+b[1]*td)
        draws.append(float(np.mean(pred)*0.01*carbon_fraction))
    interval=(np.quantile(draws,[0.025,0.975]).tolist() if len(draws)>=100 else None)
    first=calibr[0][0]
    result.update({"status":"ESTIMATIVA_EXPERIMENTAL_IFN_GRAVIMETRICA",
        "mean_tc_ha":stock_tc_ha,"dry_litter_mg_ha":dry_mg_ha,
        "carbon_fraction":carbon_fraction,
        "carbon_fraction_basis":"média de frações medidas nas amostras",
        "bootstrap_interval_tc_ha":interval,
        "uncertainty":{"calibration_leave_one_unit_out_rmse_dry_mg_ha":loo_rmse*0.01,
                        "calibration_leave_one_unit_out_bias_dry_mg_ha":loo_bias*0.01,
                        "bootstrap_95pct_conditional_tc_ha":interval,
                        "meaning":"intervalo bootstrap condicional à calibração/IFN selecionados; não inclui erro de transferência para a propriedade e não é IC95% da fazenda"},
        "source":"SFB/IFN aberto (profundidade nas cinco UA mais próximas) + amostras gravimétricas pareadas da mesma fitofisionomia e região",
        "sources":{"ifn_depth_units":[{"unit_id":uid,"distance_km":dist,
                     "source":rows[0][0].get("source"),"source_url":rows[0][0].get("source_url")} for dist,uid,rows in units],
                   "gravimetric_calibration":sorted({(r[0].get("source"),r[0].get("source_url")) for r in calibr})},
        "calibration_point_count":len(calibr),"calibration_unit_count":len(cal_units),
        "ifn_target_unit_count":len(units),"nearest_ifn_distance_km":units[0][0],
        "calibration_region":region,"physiognomy":physiognomy,
        "calculation_trace":{"model":"dry_mass_g_m2 = beta0 + beta1 * depth_cm",
            "beta0_g_m2":float(beta[0]),"beta1_g_m2_per_cm":float(beta[1]),
            "target_depth_mean_cm":float(np.mean(target_depths)),
            "target_depth_n":int(len(target_depths)),"mean_dry_mass_g_m2":float(np.mean(yhat)),
            "dry_litter_Mg_ha_formula":"mean_dry_mass_g_m2 * 0.01",
            "carbon_stock_tC_ha_formula":"dry_litter_Mg_ha * carbon_fraction",
            "calibration_validation":"regressão ponderada por unidade independente; leave-one-unit-out; não extrapolar fora da amplitude de profundidade calibrada",
            "bootstrap_resamples":len(draws)},
        "limitations":["somente unidades IFN de mesma região e fitofisionomia",
            "apenas as cinco unidades abertas mais próximas até 250 km foram usadas",
            "não é medição dentro da fazenda; erro de transferência espacial não está quantificado",
            "não usar sem amostras gravimétricas pareadas e proveniência verificável"]})
    return result
