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


def _certified_route_absence(audit):
    """Only a complete, error-free AOI audit proving zero valid pixels is absence."""
    return (isinstance(audit,dict)
        and audit.get("configured") is True
        and audit.get("coverage_absence_confirmed") is True
        and audit.get("catalog_search_complete") is True
        and audit.get("pagination_complete") is True
        and audit.get("pixel_read_complete") is True
        and audit.get("valid_pixel_count") == 0
        and audit.get("technical_error_count") == 0)


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


def fit_experimental_xl_height_model(frame, *, feature_columns, band, physiognomy, biome, region,
                                      reference_url, reference_sha256,
                                      reference_kind, primary_route_status, primary_route_audit=None,
                                      group_column="site_id", target_column="field_height_m"):
    """Fit an auditable X/L fallback height model from independent field pairs.

    This route is allowed only after the priority P-band ESA + recent SAR route
    is unavailable for the AOI. It reports grouped spatial holdout errors and
    never uses arbitrary coefficients or pseudo-labels.
    """
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    band=str(band).upper().strip()
    if band not in ("X","L"):
        raise ValueError("A contingência de altura aceita apenas banda X ou L.")
    status=str(primary_route_status or "").upper().strip()
    if status != "NO_COVERAGE" or not _certified_route_absence(primary_route_audit):
        raise ValueError("X/L só pode ser usado após ausência de cobertura certificada, com busca, paginação e leitura completas e sem erros.")
    if reference_kind != "independent_field_observations":
        raise ValueError("A calibração X/L exige observações de campo independentes; mapas não são rótulos de altura.")
    if not reference_url or not reference_sha256 or not physiognomy:
        raise ValueError("Fonte, SHA-256 e fitofisionomia compatível são obrigatórios.")
    if len(feature_columns)<1 or len(set(feature_columns))!=len(feature_columns):
        raise ValueError("Declare preditores X/L únicos e não vazios.")
    qa_columns={"sar_product_id","field_height_definition","spatial_match_error_m",
                "pixel_size_m","date_field","date_sar","biome","physiognomy","region"}
    required=set(feature_columns)|{group_column,target_column,"plot_id"}|qa_columns
    missing=sorted(required-set(frame.columns))
    if missing:
        raise ValueError("Pares X/L incompletos; faltam controles parcela-pixel: "+", ".join(missing))
    data=frame.copy()
    for col in list(feature_columns)+[target_column,"spatial_match_error_m","pixel_size_m"]:
        data[col]=pd.to_numeric(data[col],errors="coerce")
    data["date_field"]=pd.to_datetime(data["date_field"],errors="coerce",utc=True)
    data["date_sar"]=pd.to_datetime(data["date_sar"],errors="coerce",utc=True)
    data=data.dropna(subset=list(feature_columns)+[target_column,group_column,"plot_id"]+
                     ["sar_product_id","field_height_definition","spatial_match_error_m",
                      "pixel_size_m","date_field","date_sar"])
    numeric=data[list(feature_columns)+[target_column,"spatial_match_error_m","pixel_size_m"]].to_numpy(float)
    data=data.loc[np.isfinite(numeric).all(axis=1)].copy()
    date_delta=(data["date_field"]-data["date_sar"]).abs().dt.total_seconds()/86400.0
    matched=(data["spatial_match_error_m"]>=0)&(data["pixel_size_m"]>0)&(
        data["spatial_match_error_m"]<=0.5*data["pixel_size_m"])&(date_delta<=365)
    data=data.loc[matched].copy()
    if data.empty:
        raise ValueError("Nenhum par passou a QA de co-registro <= meio pixel e diferença temporal <=365 dias.")
    if data["sar_product_id"].astype(str).nunique()!=1:
        raise ValueError("Separe produtos SAR; o modelo não pode misturar resoluções/processamentos.")
    if data["field_height_definition"].astype(str).str.strip().eq("").any() or data["field_height_definition"].astype(str).nunique()!=1:
        raise ValueError("Use uma única definição de altura de campo, explicitamente declarada.")
    for column,expected in (("biome",biome),("physiognomy",physiognomy),("region",region)):
        values=data[column].astype(str).str.strip()
        if not expected or values.eq("").any() or set(values)!={str(expected)}:
            raise ValueError("Pares de campo devem pertencer ao mesmo bioma, fitofisionomia e região declarados.")
    data=data.loc[(data[target_column]>0)&data[group_column].astype(str).str.strip().ne("")&
                  data["plot_id"].astype(str).str.strip().ne("")].copy()
    if data["plot_id"].duplicated().any():
        raise ValueError("Agregue cada footprint de parcela a uma linha; pixels repetidos não são réplicas independentes.")
    groups=data[group_column].astype(str).to_numpy()
    n_sites=len(set(groups))
    if n_sites<5 or len(data)<=len(feature_columns)+1:
        raise ValueError("Exige pelo menos cinco sítios espaciais e pares suficientes para o número de preditores.")
    x=data[list(feature_columns)].to_numpy(float)
    y=data[target_column].to_numpy(float)
    pred=np.full(len(y),np.nan)
    cv=GroupKFold(n_splits=min(5,n_sites))
    for train,test in cv.split(x,y,groups):
        if len(train)<=len(feature_columns):
            raise ValueError("Fold espacial sem observações suficientes para ajustar o modelo.")
        model=LinearRegression().fit(x[train],y[train])
        pred[test]=model.predict(x[test])
    residual=pred-y
    final=LinearRegression().fit(x,y)
    metrics={
        "n_independent_plots":int(len(data)),
        "n_spatial_sites":int(n_sites),
        "RMSE_m":float(np.sqrt(mean_squared_error(y,pred))),
        "MAE_m":float(mean_absolute_error(y,pred)),
        "bias_m":float(np.mean(pred-y)),
        "R2":float(r2_score(y,pred)) if np.var(y)>0 else None,
        "OOF_residual_quantiles_m":[float(v) for v in np.quantile(residual,[0.05,0.95])],
        "validation":"GroupKFold espacial por sítio; previsão out-of-fold",
        "minimum_accuracy_policy":"qualquer precisão mensurável é reportada; não há limiar universal",
    }
    return {
        "status":"MODELO_XL_EXPERIMENTAL_COM_VALIDACAO_ESPACIAL",
        "deployable":False,
        "band":band,
        "sensor_priority":"P ESA + Sentinel-1 recente; X; L",
        "primary_route_status":status,
        "physiognomy":str(physiognomy),
        "biome":str(biome),
        "region":str(region),
        "feature_columns":list(feature_columns),
        "coefficients":{"intercept_m":float(final.intercept_),
                        **{name:float(value) for name,value in zip(feature_columns,final.coef_)}},
        "feature_min":{name:float(data[name].min()) for name in feature_columns},
        "feature_max":{name:float(data[name].max()) for name in feature_columns},
        "metrics":metrics,
        "reference_url":reference_url,
        "reference_sha256":str(reference_sha256),
        "reference_kind":reference_kind,
        "sar_product_id":str(data["sar_product_id"].iloc[0]),
        "field_height_definition":str(data["field_height_definition"].iloc[0]),
        "pairing_qc":{"max_spatial_match_fraction_of_pixel":0.5,
                      "max_date_delta_days":365,
                      "n_pairs_passing_qc":int(len(data))},
        "scope":"somente a banda/produto, fitofisionomia, região e intervalo de preditores representados pelas parcelas",
        "limitation":"Modelo experimental; GroupKFold não substitui holdout externo independente por região.",
    }


def predict_experimental_xl_height(features, model, *, band, physiognomy, biome, region,
                                    primary_route_status, primary_route_audit=None,
                                    x_route_status="NO_COVERAGE", x_route_audit=None):
    """Predict height only through the authorized X-then-L fallback chain."""
    import numpy as np
    band=str(band).upper().strip()
    status=str(primary_route_status or "").upper().strip()
    if status != "NO_COVERAGE" or not _certified_route_absence(primary_route_audit):
        return {"status":"N/D","height_mean_m":None,
                "reason":"Ausência da rota prioritária não foi certificada; erro técnico ou auditoria incompleta não autoriza fallback."}
    if band=="L" and (str(x_route_status or "").upper().strip() != "NO_COVERAGE"
                       or not _certified_route_absence(x_route_audit)):
        return {"status":"N/D","height_mean_m":None,
                "reason":"L-band só é acionada quando a rota X-band também está indisponível."}
    if (not isinstance(model,dict) or model.get("band")!=band
        or model.get("physiognomy")!=str(physiognomy)
        or model.get("biome")!=str(biome) or model.get("region")!=str(region)):
        return {"status":"N/D","height_mean_m":None,
                "reason":"Modelo X/L ausente ou incompatível com banda/fitofisionomia."}
    names=model.get("feature_columns") or []
    co=model.get("coefficients") or {}
    if not names or any(name not in features for name in names):
        return {"status":"N/D","height_mean_m":None,"reason":"Preditores do modelo X/L ausentes."}
    values=[]
    for name in names:
        try:value=float(features[name])
        except (TypeError,ValueError,OverflowError):
            return {"status":"N/D","height_mean_m":None,"reason":"Preditor X/L inválido: "+name}
        if not isfinite(value):
            return {"status":"N/D","height_mean_m":None,"reason":"Preditor X/L não finito: "+name}
        if value<float(model["feature_min"][name]) or value>float(model["feature_max"][name]):
            return {"status":"N/D","height_mean_m":None,
                    "reason":"Preditor fora do domínio de calibração: "+name}
        values.append(value)
    estimate=_num(co.get("intercept_m"))
    if estimate is None:return {"status":"N/D","height_mean_m":None,"reason":"Intercepto inválido."}
    for name,value in zip(names,values):
        coefficient=_num(co.get(name))
        if coefficient is None:return {"status":"N/D","height_mean_m":None,"reason":"Coeficiente inválido: "+name}
        estimate+=coefficient*value
    metrics=model.get("metrics") or {}
    if estimate<=0:return {"status":"N/D","height_mean_m":None,"reason":"Altura prevista não física."}
    residual=metrics.get("OOF_residual_quantiles_m")
    rmse=_num(metrics.get("RMSE_m"))
    if not isinstance(residual,list) or len(residual)!=2 or rmse is None or rmse<=0:
        return {"status":"N/D","height_mean_m":None,"reason":"Incerteza espacial OOF ausente."}
    lo=max(0.0,estimate+float(residual[0]));hi=max(lo,estimate+float(residual[1]))
    return {
        "status":"ALTURA_XL_EXPERIMENTAL",
        "height_mean_m":estimate,
        "height_interval_oof_m":[lo,hi],
        "height_rmse_spatial_oof_m":rmse,
        "height_mae_spatial_oof_m":metrics.get("MAE_m"),
        "height_bias_spatial_oof_m":metrics.get("bias_m"),
        "n_independent_plots":metrics.get("n_independent_plots"),
        "n_spatial_sites":metrics.get("n_spatial_sites"),
        "band":band,
        "physiognomy":str(physiognomy),
        "biome":str(biome),
        "region":str(region),
        "reference_url":model.get("reference_url"),
        "reference_sha256":model.get("reference_sha256"),
        "model_coefficients":dict(co),
        "input_features":dict(zip(names,values)),
        "uncertainty_kind":"quantis 5–95% dos resíduos out-of-fold por grupo espacial; RMSE reportado separadamente",
        "deployment_scope":model.get("scope"),
        "scientific_status":"EXPERIMENTAL; não homologado nacionalmente",
    }
