"""Guarded plot-level SAR calibration using spatially independent folds.

Inputs must already be genuine contemporaneous field-plot/SAR pairs. This
module intentionally refuses inventory-only or pixel-only data.
"""
from __future__ import annotations
import numpy as np

BASE_PREDICTORS=("basal_area_m2_ha","mean_dbh_cm","stems_ha")
SAR_PREDICTORS=("height_sar_m",)

def calibrate_height_structure_agb(frame, agb_col="agb_ref_mg_ha", group_col="site_id"):
    """Compare structure-only and height-SAR augmented log-linear models.

    Reports spatial out-of-fold metrics; the returned fit is exploratory and
    not marked deployable. Independent external-site validation remains a
    release gate. AGB labels must be documented as measured or allometric.
    """
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
    required=[agb_col,group_col,*BASE_PREDICTORS,*SAR_PREDICTORS]
    missing=[c for c in required if c not in frame.columns]
    if missing: raise ValueError("Contrato parcela–SAR incompleto; colunas ausentes: "+", ".join(missing))
    d=frame[required].copy()
    original_index=d.index.copy()
    numeric_cols=[agb_col,*BASE_PREDICTORS,*SAR_PREDICTORS]
    for c in numeric_cols: d[c]=pd.to_numeric(d[c],errors="coerce")
    d[group_col]=d[group_col].astype("string").str.strip()
    numeric=d[numeric_cols].to_numpy(dtype=float,na_value=np.nan)
    good=np.isfinite(numeric).all(axis=1)&(numeric>0).all(axis=1)&(d[agb_col].to_numpy(float)>0)
    good &= d[group_col].notna().to_numpy()&(d[group_col].astype(str).to_numpy()!="")
    valid_source_index=original_index[good]
    provenance=(sorted(set(str(x) for x in frame.loc[valid_source_index,"agb_label_provenance"].dropna()))
                if "agb_label_provenance" in frame.columns else [])
    d=d.loc[good].reset_index(drop=True)
    y=np.log(d[agb_col].to_numpy(float)); groups=d[group_col].astype(str).to_numpy()
    if len(d)<30: raise ValueError(f"Calibração bloqueada: requer ≥30 pares completos exploratórios; há {len(d)}.")
    n_groups=len(np.unique(groups))
    if n_groups<5: raise ValueError(f"Calibração bloqueada: requer ≥5 sítios independentes para CV espacial; há {n_groups}.")
    feature_sets={"estrutura_sem_SAR":list(BASE_PREDICTORS),
                  "estrutura_mais_altura_SAR":list(BASE_PREDICTORS+SAR_PREDICTORS)}
    cv=GroupKFold(n_splits=min(5,n_groups)); result={}
    for name,cols in feature_sets.items():
        X=np.log(d[cols].to_numpy(float))
        pred=np.full(len(y),np.nan)
        for tr,te in cv.split(X,y,groups):
            model=LinearRegression().fit(X[tr],y[tr]); pred[te]=model.predict(X[te])
        pred_agb=np.exp(pred); observed=d[agb_col].to_numpy(float)
        result[name]={"RMSE_Mg_ha":float(np.sqrt(mean_squared_error(observed,pred_agb))),
            "MAE_Mg_ha":float(mean_absolute_error(observed,pred_agb)),
            "bias_Mg_ha":float(np.mean(pred_agb-observed)),
            "R2_log":float(r2_score(y,pred)),"n_pairs":len(d),"independent_sites":n_groups,
            "validation":"GroupKFold por sítio; predições out-of-fold", "predictors":cols}
    fit=LinearRegression().fit(np.log(d[feature_sets["estrutura_mais_altura_SAR"]].to_numpy(float)),y)
    # transform back to a documented power law. exp(intercept) is not a
    # Duan-corrected prediction; output coefficients only, never point AGB.
    return {"status":"EXPLORATORY_SPATIAL_CV_ONLY","deployable":False,
        "n_pairs":len(d),"independent_sites":n_groups,"agb_label_col":agb_col,
        "agb_label_provenance":provenance,
        "comparison":result,"sar_height_added_rmse_delta_Mg_ha":result["estrutura_mais_altura_SAR"]["RMSE_Mg_ha"]-result["estrutura_sem_SAR"]["RMSE_Mg_ha"],
        "log_model_coefficients":{"intercept":float(fit.intercept_),**{k:float(v) for k,v in zip(feature_sets["estrutura_mais_altura_SAR"],fit.coef_)}},
        "release_gate":"validar em sítio externo independente, auditar AGB/alometria e erro de altura SAR, testar resíduos e cobertura do intervalo; não publicar como calibrado antes disso"}
