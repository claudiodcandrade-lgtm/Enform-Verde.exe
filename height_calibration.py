"""Independent agreement checks for SAR forest-height products.

SAR-derived canopy height is the primary height estimate in this project.
Field-measured heights are empirical observations with measurement error and
are used only for external agreement checks, never as the quantity to which
the operational SAR height is forced to conform. This module never creates
field/SAR pairs or outputs a corrected operational height. Direct SAR height
products may be summarized without calibration; agreement metrics are emitted
only from contemporaneous, support-matched Brazilian inventory pairs and
spatially grouped out-of-fold validation.
"""
from __future__ import annotations

import numpy as np


PAIR_COLUMNS = (
    "site_id", "plot_id", "field_height_m", "sar_height_m", "sar_product_id",
    "field_height_definition", "sar_height_definition", "metric_compatibility",
    "spatial_match_error_m", "pixel_size_m", "date_field", "date_sar",
)


def validate_sar_height_pairs(frame, *, min_pairs=30, min_sites=5,
                              max_date_delta_days=365, max_match_fraction=0.5):
    """Assess SAR-vs-field agreement after strict pair QA; do not replace SAR height.

    `metric_compatibility` must be `direct` (same declared height statistic) or
    `crosswalk` with a nonempty `compatibility_reference` documenting the
    published/validated conversion. SAR footprints must overlap the field plot
    within half a pixel and acquisition dates must be within one year by default.
    The output is exploratory and never marked deployable.
    """
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    missing=[c for c in PAIR_COLUMNS if c not in frame.columns]
    if missing:
        return _blocked("missing_columns", "Contrato parcela–SAR incompleto: "+", ".join(missing), 0, 0)
    d=frame.copy()
    for c in ("field_height_m", "sar_height_m", "spatial_match_error_m", "pixel_size_m"):
        d[c]=pd.to_numeric(d[c],errors="coerce")
    d["date_field"]=pd.to_datetime(d["date_field"],errors="coerce",utc=True)
    d["date_sar"]=pd.to_datetime(d["date_sar"],errors="coerce",utc=True)
    for c in ("site_id", "plot_id", "sar_product_id", "field_height_definition", "sar_height_definition", "metric_compatibility"):
        d[c]=d[c].astype("string").str.strip()
    d["date_delta_days"]=(d["date_sar"]-d["date_field"]).abs().dt.total_seconds()/86400.0
    compatible=(d["metric_compatibility"].eq("direct") &
                d["field_height_definition"].eq(d["sar_height_definition"]))
    crosswalk=(d["metric_compatibility"].eq("crosswalk") &
               d.get("compatibility_reference",pd.Series(index=d.index,dtype="string")).astype("string").str.strip().ne(""))
    valid=(np.isfinite(d[["field_height_m","sar_height_m","spatial_match_error_m","pixel_size_m"]].to_numpy(float)).all(axis=1)
           & (d["field_height_m"]>0) & (d["sar_height_m"]>0)
           & (d["pixel_size_m"]>0)
           & (d["spatial_match_error_m"] <= max_match_fraction*d["pixel_size_m"])
           & (d["date_delta_days"] <= max_date_delta_days)
           & (compatible|crosswalk)
           & d["site_id"].notna() & d["site_id"].ne("")
           & d["plot_id"].notna() & d["plot_id"].ne("")
           & d["sar_product_id"].notna() & d["sar_product_id"].ne(""))
    d=d.loc[valid].copy()
    n=len(d); sites=d["site_id"].nunique()
    if n < min_pairs or sites < min_sites:
        return _blocked("insufficient_independent_pairs",
            f"Exige ≥{min_pairs} pares QA e ≥{min_sites} sítios independentes; restaram {n} pares QA em {sites} sítios.",n,sites)
    if d["sar_product_id"].nunique()!=1:
        return _blocked("mixed_products", "Ajuste de altura separado por sensor/produto e definição de métrica.",n,sites)
    if d["sar_height_definition"].nunique()!=1 or d["field_height_definition"].nunique()!=1:
        return _blocked("mixed_height_definitions", "Definições de altura misturadas; estratifique antes do ajuste.",n,sites)
    if d["plot_id"].duplicated().any():
        # Multiple pixels/rows from the same field plot must first be reduced to
        # one support-matched observation to avoid pseudoreplication.
        return _blocked("duplicate_plot_pairs", "Há mais de uma linha por parcela; agregue pixels ao footprint da parcela.",n,sites)
    x=d["sar_height_m"].to_numpy(float).reshape(-1,1)
    y=d["field_height_m"].to_numpy(float)
    groups=d["site_id"].astype(str).to_numpy()
    pred=np.full(n,np.nan)
    cv=GroupKFold(n_splits=min(5,sites))
    for train,test in cv.split(x,y,groups):
        model=LinearRegression().fit(x[train],y[train])
        pred[test]=model.predict(x[test])
    residual=pred-y
    fitted=LinearRegression().fit(x,y)
    metrics={"n_pairs":n,"independent_sites":int(sites),
        "RMSE_m":float(np.sqrt(mean_squared_error(y,pred))),
        "MAE_m":float(mean_absolute_error(y,pred)),
        "bias_m":float(np.mean(pred-y)),"R2":float(r2_score(y,pred)),
        "OOF_residual_quantiles_m":[float(v) for v in np.quantile(residual,[0.025,0.975])],
        "validation":"GroupKFold por sítio; predição out-of-fold"}
    return {"status":"EXPLORATORY_SPATIAL_CV_ONLY","deployable":False,
        "sar_product_id":str(d["sar_product_id"].iloc[0]),
        "field_height_definition":str(d["field_height_definition"].iloc[0]),
        "sar_height_definition":str(d["sar_height_definition"].iloc[0]),
        "metric_compatibility":str(d["metric_compatibility"].iloc[0]),
        "coefficients":{"intercept_m":float(fitted.intercept_),"slope":float(fitted.coef_[0])},
        "metrics":metrics,
        "scope":"somente produto, definições de altura, períodos, fitofisionomias e regiões representados nos sítios pareados",
        "limitations":["não transfere para sensor/produto ou classe IBGE não representados",
            "erro observado é erro de validação cruzada espacial no conjunto fornecido, não nacional",
            "requer holdout externo por região antes de uso operacional"]}


def _blocked(code, reason, n, sites):
    return {"status":"SAR_HEIGHT_CALIBRATION_BLOCKED","deployable":False,
        "reason_code":code,"reason":reason,"n_qa_pairs":int(n),"independent_sites":int(sites),
        "height_estimate_source":"produto SAR direto, quando disponível",
        "calibrated_height_m":None,"local_validation_error_m":None}
