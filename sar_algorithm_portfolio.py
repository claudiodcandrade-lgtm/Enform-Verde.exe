"""Trainable Brazilian SAR model portfolio: Random Forest, RBF SVM and KNN.

Research/experimental adaptation, not pretrained weights or national validation.
Reference labels MUST be real independently collected observations. Uses
spatial GroupKFold to avoid near-neighbor leakage. Models are NOT auto-promoted
to production because spatial cross-validation is NOT field-independent proof.
Sources: Embrapa Agricultura Digital Sentinel-1/2 studies, Brazilian Sentinel-1
KNN/RF/SVM dissertations; sklearn implementations are original adaptations.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

FEATURE_SCHEMA=("vv_db_median","vh_db_median","vh_db_p10","vh_db_p90",
                "vh_db_amplitude","vv_vh_db_ratio","vh_temporal_cv",
                "vh_glcm_contrast","vh_glcm_homogeneity")
ALGORITHMS=("RandomForest","SVM_RBF","KNN")
MIN_SPATIAL_FOLDS=3


def _models():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    return {
        "RandomForest":RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
            random_state=20261110, n_jobs=1),
        "SVM_RBF":make_pipeline(StandardScaler(),SVC(
            C=2.0,kernel="rbf",gamma="scale",class_weight="balanced",
            probability=True,random_state=20261110)),
        "KNN":make_pipeline(StandardScaler(),KNeighborsClassifier(n_neighbors=5,
                                    weights="distance"))
    }


def train_spatial_sar_portfolio(features, labels, spatial_groups, *, provenance,
                               output_dir=None, feature_names=FEATURE_SCHEMA):
    """Benchmark three executable estimators using ONLY supplied labeled pixels.

    provenance documents origin and observation dates; NEVER accept MapBiomas,
    IBGE potential vegetation or SAR predictions as pseudo-ground-truth.
    No claim of independent measured accuracy: CV is internal model selection.
    """
    import numpy as np
    from sklearn.base import clone
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import balanced_accuracy_score, f1_score, confusion_matrix
    X=np.asarray(features,dtype=np.float64)
    y=np.asarray(labels)
    groups=np.asarray(spatial_groups)
    names=tuple(feature_names)
    if X.ndim!=2 or X.shape[1]!=len(names) or y.ndim!=1 or groups.ndim!=1:
        raise ValueError("FEATURE_SCHEMA_OR_ARRAY_SHAPE_INCOMPATIBLE")
    if len(X)!=len(y) or len(X)!=len(groups) or len(X)<30:
        raise ValueError("INSUFFICIENT_PAIRED_REFERENCE_SAMPLES")
    if not np.isfinite(X).all():
        raise ValueError("NONFINITE_SAR_FEATURES")
    if len(set(names))!=len(names):
        raise ValueError("DUPLICATE_FEATURE_NAMES")
    if len(set(map(str,y)))<2:
        raise ValueError("AT_LEAST_TWO_REFERENCE_CLASSES_REQUIRED")
    unique_groups=np.unique(groups)
    if len(unique_groups)<MIN_SPATIAL_FOLDS:
        raise ValueError("AT_LEAST_THREE_SPATIALLY_DISTINCT_GROUPS_REQUIRED")
    if not isinstance(provenance,dict) or not provenance.get("reference_dataset") or not provenance.get("observation_period"):
        raise ValueError("REFERENCE_PROVENANCE_REQUIRED")
    if provenance.get("reference_origin") in ("IBGE","MAPBIOMAS","SAR_MODEL_PREDICTIONS"):
        raise ValueError("HISTORICAL_OR_SELF_LABELS_NOT_INDEPENDENT_REFERENCE")
    classes=sorted({str(v) for v in y})
    # Fixed group folds are the same for all candidates.
    fold_list=list(GroupKFold(n_splits=min(5,len(unique_groups))).split(X,y,groups))
    scored={}
    for name,model in _models().items():
        preds=np.empty(y.shape,dtype=object)
        valid=np.zeros(len(y),dtype=bool)
        for tr,te in fold_list:
            if len(set(y[tr]))<2:continue
            if name=="KNN" and len(tr)<5:continue
            fitted=clone(model).fit(X[tr],y[tr])
            preds[te]=fitted.predict(X[te])
            valid[te]=True
        if not valid.all():
            scored[name]={"eligible":False,"reason":"SPATIAL_FOLD_WITHOUT_BOTH_CLASSES",
                          "validated_rows":int(valid.sum())}
            continue
        truth=np.asarray([str(v) for v in y])
        prediction=np.asarray([str(v) for v in preds])
        mat=confusion_matrix(truth,prediction,labels=classes)
        scored[name]={"eligible":True,"balanced_accuracy_cv":float(balanced_accuracy_score(truth,prediction)),
                      "macro_f1_cv":float(f1_score(truth,prediction,average="macro",zero_division=0)),
                      "confusion_matrix_cv":mat.tolist(),"classes":classes,
                      "spatial_groups":int(len(unique_groups)),"n":int(len(y)),
                      "validation_scope":"internal spatial cross-validation, NOT independent field validation"}
    admissible=[(v["balanced_accuracy_cv"],v["macro_f1_cv"],n) for n,v in scored.items() if v.get("eligible")]
    best=max(admissible,key=lambda z:(z[0],z[1],z[2]))[-1] if admissible else None
    result={"status":"TRAINABLE_PORTFOLIO_EXPERIMENTAL" if best else "NOT_TRAINABLE",
            "selected_algorithm":best,"evaluation":scored,"feature_names":names,
            "reference_provenance":provenance,"spatial_cv_folds":len(fold_list),
            "independent_validation":"NOT_PROVIDED",
            "local_calibration":"NOT_ESTABLISHED",
            "deployment_eligible":False,
            "training_reference_sha256":hashlib.sha256(
                X.tobytes()+str(tuple(map(str,y))).encode("utf-8")+
                str(tuple(map(str,groups))).encode("utf-8")).hexdigest(),
            "note":"Scientific experimental ranking only; does not prove a current SAR mask in the AOI."}
    if output_dir is not None:
        out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
        (out/"sar_algorithm_comparison.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        if best:
            import joblib
            selected=_models()[best]
            selected.fit(X,y)
            # Explicit experimental prefix; never discover as a validated SAR
            # model until independent reference and regional deployment gate.
            joblib.dump({"estimator":selected,"feature_names":names,
                         "labels":classes,"audit":result},
                        out/"sar_portfolio_experimental.joblib")
    return result


def predict_experimental_sar_portfolio(model_file, features, *, feature_names=FEATURE_SCHEMA):
    """Run trained experimental model on real SAR features with strict schema."""
    import joblib
    import numpy as np
    package=joblib.load(model_file)  # ONLY files trusted and generated locally.
    X=np.asarray(features,dtype=np.float64)
    if tuple(package["feature_names"])!=tuple(feature_names) or X.ndim!=2 or X.shape[1]!=len(feature_names):
        raise ValueError("INCOMPATIBLE_SAR_FEATURE_SCHEMA")
    if not np.isfinite(X).all():raise ValueError("NONFINITE_SAR_FEATURES")
    estimator=package["estimator"]
    labels=estimator.predict(X).tolist()
    prob=estimator.predict_proba(X)
    return {"status":"EXPERIMENTAL_INFERENCE_NOT_FIELD_VALIDATED",
            "labels":labels,"max_probability_uncalibrated":prob.max(axis=1).tolist(),
            "calibrated_probability":False,
            "model":package["audit"]["selected_algorithm"],
            "note":"Model likelihood is NOT estimated scientific confidence or IC95%."}
