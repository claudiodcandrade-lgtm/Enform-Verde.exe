"""Spatial-temporal crop-yield model training with conformal intervals.

The module fits crop-specific transfer models only from supplied, traceable
municipality-season records. It requires observed SAR crop/vigor/stress features
and climate covariates in both training and validation data. Synthetic samples,
map pseudo-label validation, and random pixel splits are not accepted.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import GroupKFold, cross_val_score

from crop_health_yield_quality import evaluate_yield_forecast

_REQUIRED = (
    "crop", "municipality_code", "spatial_block", "season_year", "yield_t_ha",
    "yield_source_url", "yield_license", "sar_crop_validated",
    "sar_vigor_validated", "sar_stress_validated", "sar_source_url",
    "weather_source", "weather_source_url",
)
_MIN_TRAIN = 200
_MIN_CALIBRATION_MUNICIPALITIES = 50
_MIN_TEST_MUNICIPALITIES = 50
_MIN_SPATIAL_BLOCKS = 5


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total <= 0:
        return [0.0, 1.0]
    p = successes / total
    den = 1 + z*z/total
    center = (p + z*z/(2*total))/den
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/den
    return [max(0.0, center-half), min(1.0, center+half)]


def _finite_quantile(values, coverage: float) -> float:
    vals = np.sort(np.asarray(values, dtype=float))
    if not len(vals) or not np.isfinite(vals).all():
        raise ValueError("calibration residuals are empty or non-finite")
    # Split-conformal finite-sample rank; conservative upper order statistic.
    rank = min(len(vals), int(math.ceil((len(vals)+1)*coverage)))
    return float(vals[rank-1])


def _independent_rows(frame: pd.DataFrame) -> pd.DataFrame:
    # One held-out outcome per municipality is needed for the binomial coverage CI.
    return frame.sort_values("season_year").drop_duplicates("municipality_code", keep="last")


def _check_source_provenance(frame: pd.DataFrame) -> None:
    for col in ("yield_source_url", "yield_license", "sar_source_url",
                "weather_source", "weather_source_url"):
        if frame[col].isna().any() or frame[col].astype(str).str.strip().eq("").any():
            raise ValueError("missing provenance: " + col)
    if not frame[["sar_crop_validated", "sar_vigor_validated",
                  "sar_stress_validated"]].apply(
                      lambda col: col.map(lambda v: v is True or v == 1)).all().all():
        raise ValueError("independent in-domain SAR crop, vigor and stress validation is required")
    if frame["yield_source_url"].astype(str).str.contains(
            "mapbiomas", case=False, regex=False).any():
        raise ValueError("MapBiomas pseudo-labels cannot be yield-validation truth")


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    sar = [c for c in frame.columns if c.startswith("sar_") and
           c not in {"sar_crop_validated", "sar_vigor_validated",
                     "sar_stress_validated", "sar_source_url"}]
    climate = [c for c in frame.columns if c.startswith(("climate_", "weather_"))
               and c not in {"weather_source", "weather_source_url"}]
    groups = {
        "SAR crop identity": any(c.startswith("sar_crop_") for c in sar),
        "SAR vigor/phenology": any(c.startswith(("sar_vigor_", "sar_phenology_")) for c in sar),
        "SAR nonspecific stress anomaly": any(c.startswith("sar_stress_") for c in sar),
        "dynamic climate": bool(climate),
    }
    missing = [name for name, present in groups.items() if not present]
    if missing:
        raise ValueError("required predictor groups missing: " + ", ".join(missing))
    cols = sar + climate
    for col in cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if not frame[cols].notna().any(axis=0).all():
        raise ValueError("a required predictor is entirely missing")
    return cols


def train_crop_yield_model(
    panel: pd.DataFrame,
    *,
    crop: str,
    heldout_blocks: list[str],
    artifact_path: str | Path,
    nominal_coverage: float = 0.90,
    min_improvement_over_median: float = 0.02,
) -> dict:
    """Train one crop model and validate on later years and unseen spatial blocks.

    The last season in the supplied panel is the independent test season and the
    preceding season calibrates conformal residuals. All held-out blocks are
    excluded from model fitting. Returns a non-operational failure status rather
    than a model when sample, provenance, transfer, or interval tests fail.
    """
    if not 0.80 <= float(nominal_coverage) <= 0.99:
        raise ValueError("nominal coverage must be between 0.80 and 0.99")
    data = panel.copy()
    missing = [c for c in _REQUIRED if c not in data.columns]
    if missing:
        raise ValueError("training panel missing columns: " + ", ".join(missing))
    data = data.loc[data["crop"].astype(str).str.casefold() == str(crop).casefold()].copy()
    if data.empty:
        raise ValueError("no public yield records for requested crop")
    _check_source_provenance(data)
    data["season_year"] = pd.to_numeric(data["season_year"], errors="raise").astype(int)
    data["yield_t_ha"] = pd.to_numeric(data["yield_t_ha"], errors="coerce")
    data = data[np.isfinite(data["yield_t_ha"]) & (data["yield_t_ha"] > 0)].copy()
    if data.duplicated(["municipality_code", "season_year"]).any():
        raise ValueError("duplicate municipality-season labels; resolve crop season/multiple harvests")
    blocks = set(data["spatial_block"].astype(str))
    heldout = {str(x) for x in heldout_blocks}
    if not heldout or not heldout.issubset(blocks) or len(blocks-heldout) < 5:
        raise ValueError("need declared held-out blocks and at least five training spatial blocks")
    years = sorted(data["season_year"].unique())
    if len(years) < 5:
        raise ValueError("at least five crop seasons are required for temporal holdout")
    test_year, calibration_year = years[-1], years[-2]
    train = data[(~data["spatial_block"].astype(str).isin(heldout)) &
                 (data["season_year"] <= years[-3])].copy()
    calibration = data[data["spatial_block"].astype(str).isin(heldout) &
                       (data["season_year"] == calibration_year)].copy()
    test = data[data["spatial_block"].astype(str).isin(heldout) &
                 (data["season_year"] == test_year)].copy()
    cal_units = calibration["municipality_code"].nunique()
    test_units = test["municipality_code"].nunique()
    test_blocks = test["spatial_block"].nunique()
    if len(train) < _MIN_TRAIN:
        raise ValueError(f"training sample below {_MIN_TRAIN}: {len(train)}")
    if cal_units < _MIN_CALIBRATION_MUNICIPALITIES:
        raise ValueError(f"conformal calibration requires {_MIN_CALIBRATION_MUNICIPALITIES} independent municipalities; got {cal_units}")
    if test_units < _MIN_TEST_MUNICIPALITIES or test_blocks < _MIN_SPATIAL_BLOCKS:
        raise ValueError("independent test requires >=50 municipalities and >=5 spatial blocks")
    _check_source_provenance(train)
    _check_source_provenance(calibration)
    _check_source_provenance(test)

    features = _feature_columns(data)
    x_train, y_train = train[features], train["yield_t_ha"]
    groups = train["spatial_block"].astype(str)
    splits = min(5, groups.nunique())
    if splits < 3:
        raise ValueError("at least three spatial groups are needed for model selection")
    candidates = {
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            RandomForestRegressor(n_estimators=300, min_samples_leaf=5,
                                  max_features=0.8, random_state=42, n_jobs=-1)),
        "hist_gradient_boosting": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            HistGradientBoostingRegressor(max_iter=180, max_leaf_nodes=15,
                                          l2_regularization=2.0,
                                          random_state=42)),
    }
    cv = GroupKFold(n_splits=splits)
    cv_mae = {}
    for name, estimator in candidates.items():
        scores = cross_val_score(estimator, x_train, y_train, groups=groups,
                                 cv=cv, scoring="neg_mean_absolute_error", n_jobs=1)
        cv_mae[name] = float(-scores.mean())
    selected_name = min(cv_mae, key=cv_mae.get)
    model = candidates[selected_name].fit(x_train, y_train)

    cal_pred = np.maximum(0.0, model.predict(calibration[features]))
    cal_resid = np.abs(calibration["yield_t_ha"].to_numpy()-cal_pred)
    radius = _finite_quantile(cal_resid, nominal_coverage)
    test_pred = np.maximum(0.0, model.predict(test[features]))
    y_test = test["yield_t_ha"].to_numpy()
    lower = np.maximum(0.0, test_pred-radius)
    upper = test_pred+radius
    test_cov_frame = test.assign(_covered=(y_test >= lower) & (y_test <= upper),
                                 _abs_error=np.abs(y_test-test_pred),
                                 _sq_error=(y_test-test_pred)**2,
                                 _bias=test_pred-y_test)
    independent = _independent_rows(test_cov_frame)
    n_independent = len(independent)
    n_covered = int(independent["_covered"].sum())
    coverage = n_covered/n_independent
    coverage_ci = _wilson(n_covered, n_independent)
    mae = float(independent["_abs_error"].mean())
    rmse = float(np.sqrt(independent["_sq_error"].mean()))
    bias = float(independent["_bias"].mean())
    median_baseline = float(np.median(y_train))
    baseline_mae = float(np.mean(np.abs(independent["yield_t_ha"]-median_baseline)))
    improvement = (baseline_mae-mae)/baseline_mae if baseline_mae else 0.0
    interval_ok = coverage_ci[0] <= nominal_coverage <= coverage_ci[1]
    if not interval_ok:
        raise ValueError("prediction interval failed independent spatial-temporal coverage criterion")
    if improvement < min_improvement_over_median:
        raise ValueError("selected model did not beat the training-median baseline sufficiently")
    if n_independent < _MIN_TEST_MUNICIPALITIES:
        raise ValueError("test set lost independent municipalities after deduplication")

    manifest = {
        "schema_version": 1, "crop": crop, "model_id": f"ev-yield-{crop.casefold()}-{test_year}",
        "algorithm": selected_name, "feature_columns": features,
        "nominal_coverage": nominal_coverage, "conformal_radius_t_ha": radius,
        "calibration": {"year": calibration_year, "n_municipalities": cal_units,
                        "method": "split conformal absolute residual; later-year held-out blocks"},
        "validation": {"independent_test": True, "in_domain": True,
                       "spatial_temporal_holdout": True, "test_year": test_year,
                       "heldout_blocks": sorted(heldout), "n_independent": n_independent,
                       "n_covered": n_covered, "coverage": coverage,
                       "coverage_wilson95": coverage_ci, "nominal_coverage": nominal_coverage,
                       "rmse_t_ha": rmse, "mae_t_ha": mae, "bias_t_ha": bias,\n                       "sample_count": n_independent,
                       "median_baseline_mae_t_ha": baseline_mae,
                       "improvement_over_median": improvement,
                       "internal_spatial_cv_mae_t_ha": cv_mae},
        "training": {"n_rows": len(train), "n_municipalities": train["municipality_code"].nunique(),
                     "first_year": int(train["season_year"].min()),
                     "last_year": int(train["season_year"].max()),
                     "yield_sources": sorted(data["yield_source_url"].astype(str).unique()),
                     "yield_licenses": sorted(data["yield_license"].astype(str).unique()),
                     "sar_sources": sorted(data["sar_source_url"].astype(str).unique()),
                     "weather_sources": sorted(data["weather_source"].astype(str).unique()),
                     "weather_source_urls": sorted(data["weather_source_url"].astype(str).unique()),\n                     "panel_sha256": hashlib.sha256(pd.util.hash_pandas_object(data, index=True).values.tobytes()).hexdigest()},\n        "feature_support": {c: {"q01": float(data.loc[train.index, c].quantile(.01)),\n                                "q99": float(data.loc[train.index, c].quantile(.99)),\n                                "iqr": float(data.loc[train.index, c].quantile(.75)-data.loc[train.index, c].quantile(.25))}\n                           for c in features},
        "limitations": ["Admin-level labels predict municipal/regional yield, not field yield.",
                        "Transferability applies only to tested held-out blocks and observed feature support.",
                        "SAR stress features indicate nonspecific anomalies; they do not diagnose disease or pests.",
                        "Weather reanalysis and forecast products are not station measurements."],
    }
    artifact = Path(artifact_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    dump({"model": model, "manifest": manifest}, artifact)
    manifest["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_suffix(artifact.suffix+".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "modelo_transferencia_validado", "artifact": str(artifact),
            "manifest": manifest}


def forecast_crop_yield(artifact_path: str | Path, features: dict, *,
                        crop: str, region: str, spatial_block: str, season: str,
                        weather_provenance: dict, imagery_provenance: dict,
                        reference_date_utc: str | None = None):
    """Predict only within independently evaluated spatial blocks/domains."""
    stored = load(artifact_path)
    model, manifest = stored["model"], stored["manifest"]
    val = manifest["validation"]
    if str(crop).casefold() != str(manifest["crop"]).casefold():
        raise ValueError("crop does not match trained model")
    if str(spatial_block) not in val["heldout_blocks"]:
        raise ValueError("requested spatial block has no independent transfer validation")
    cols = manifest["feature_columns"]
    missing = [c for c in cols if c not in features]
    if missing:
        raise ValueError("forecast feature vector missing: "+", ".join(missing))
    x = pd.DataFrame([{c: features[c] for c in cols}], columns=cols)
    prediction = max(0.0, float(model.predict(x)[0]))
    radius = float(manifest["conformal_radius_t_ha"])
    interval = {"lower": max(0.0, prediction-radius), "upper": prediction+radius,
                "nominal_coverage": manifest["nominal_coverage"],
                "method": "split conformal absolute residual"}
    validation = dict(val, prediction_interval_validation={
        "independent_test": True, "spatial_temporal_holdout": True,
        "method": "later-season held-out spatial blocks",
        "nominal_coverage": manifest["nominal_coverage"],
        "n_independent": val["n_independent"], "n_covered": val["n_covered"]})
    result = evaluate_yield_forecast(
        predicted_t_ha=prediction, model_id=manifest["model_id"], crop=crop,
        region=region, season=season, weather_provenance=weather_provenance,
        imagery_provenance=imagery_provenance, validation=validation,
        prediction_interval_t_ha=interval, reference_date_utc=reference_date_utc)
    return result
