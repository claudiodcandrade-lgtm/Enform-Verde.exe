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
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold, cross_val_score

from crop_health_yield_quality import evaluate_yield_forecast

_REQUIRED = (
    "crop", "municipality_code", "spatial_block", "season_year", "yield_t_ha",
    "yield_source_url", "yield_license", "sar_crop_validated",
    "sar_vigor_validated", "sar_stress_validated", "sar_source_url",
    "weather_source", "weather_source_url", "forecast_origin_utc", "forecast_phase",
    "sar_latest_acquisition_utc", "weather_period_start_utc", "weather_period_end_utc",
    "weather_available_asof_utc",
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
    truth = {"true", "1", "yes", "sim"}
    valid_sar = frame[["sar_crop_validated", "sar_vigor_validated",
                       "sar_stress_validated"]].apply(
        lambda col: col.map(lambda v: (str(v).strip().casefold() in truth)
                            if isinstance(v, str) else bool(v)))
    if not valid_sar.all().all():
        raise ValueError("independent in-domain SAR crop, vigor and stress validation is required")
    if frame["yield_source_url"].astype(str).str.contains(
            "mapbiomas", case=False, regex=False).any():
        raise ValueError("MapBiomas pseudo-labels cannot be yield-validation truth")
    height_features = [c for c in frame.columns if c.startswith("sar_height_")
                       and c not in {"sar_height_validated", "sar_height_source_url",
                                     "sar_height_model_sha256", "sar_height_validation_status",
                                     "sar_height_validation_reference", "sar_height_crop",
                                     "sar_height_phase"}]
    if height_features:
        required = ("sar_height_validated", "sar_height_source_url", "sar_height_model_sha256",
                    "sar_height_validation_status", "sar_height_validation_reference",
                    "sar_height_crop", "sar_height_phase")
        missing = [c for c in required if c not in frame.columns]
        if missing:
            raise ValueError("SAR height validation provenance missing: " + ", ".join(missing))
        approved = frame["sar_height_validated"].map(
            lambda v: (str(v).strip().casefold() in truth) if isinstance(v, str) else bool(v))
        if not bool(approved.all()):
            raise ValueError("independent in-domain SAR height validation is required")
        if not frame["sar_height_validation_status"].astype(str).str.upper().eq(
                "INDEPENDENT_DOMAIN_VALIDATION_APPROVED").all():
            raise ValueError("SAR height validation status is not approved")
        for col in ("sar_height_source_url", "sar_height_validation_reference"):
            if frame[col].isna().any() or frame[col].astype(str).str.strip().eq("").any():
                raise ValueError("missing height provenance: " + col)
        for digest in frame["sar_height_model_sha256"].astype(str):
            if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                raise ValueError("invalid SHA-256 for SAR height retrieval model")
        if not frame["sar_height_crop"].astype(str).str.casefold().eq(
                frame["crop"].astype(str).str.casefold()).all():
            raise ValueError("SAR height validation crop differs from yield-model crop")
        if not frame["sar_height_phase"].astype(str).str.casefold().eq(
                frame["forecast_phase"].astype(str).str.casefold()).all():
            raise ValueError("SAR height validation phase differs from forecast phase")


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    meta = {"sar_crop_validated", "sar_vigor_validated", "sar_stress_validated",
            "sar_height_validated", "sar_height_source_url", "sar_height_model_sha256",
            "sar_height_validation_status", "sar_height_validation_reference",
            "sar_height_crop", "sar_height_phase", "sar_source_url",
            "weather_source", "weather_source_url"}
    sar = [c for c in frame.columns if c.startswith(
               ("sar_crop_", "sar_vigor_", "sar_phenology_", "sar_stress_", "sar_height_"))
           and c not in meta]
    climate = [c for c in frame.columns if c.startswith(("climate_", "weather_"))
               and c not in meta]
    history = [c for c in frame.columns if c.startswith("yield_lag_")]
    numeric = []
    for col in sar + climate + history:
        converted = pd.to_numeric(frame[col], errors="coerce")
        if converted.notna().any():
            frame[col] = converted
            numeric.append(col)
    # A height feature is usable only when the row carries a reviewed, remote
    # SAR-height product with crop/region/phase-specific independent validation.
    height_columns = [c for c in numeric if c.startswith("sar_height_")]
    if height_columns:
        if "sar_height_validated" not in frame.columns:
            raise ValueError("SAR height predictors require independent in-domain validation metadata")
        truth = {"true", "1", "yes", "sim"}
        ok = frame["sar_height_validated"].map(
            lambda v: (str(v).strip().casefold() in truth) if isinstance(v, str) else bool(v))
        if not bool(ok.all()):
            raise ValueError("SAR height must be independently validated by crop, region and phase")
    groups = {
        "SAR crop identity": any(c.startswith("sar_crop_") for c in numeric),
        "SAR vigor/phenology": any(c.startswith(("sar_vigor_", "sar_phenology_")) for c in numeric),
        "SAR nonspecific stress anomaly": any(c.startswith("sar_stress_") for c in numeric),
        "dynamic climate": any(c.startswith(("climate_", "weather_")) for c in numeric),
    }
    missing = [name for name, present in groups.items() if not present]
    if missing:
        raise ValueError("required predictor groups missing: " + ", ".join(missing))
    return numeric


def _add_historical_yield_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add exact one- and two-season PAM lags, never interpolating a missing year."""
    out = frame.copy()
    lookup = {(str(row.municipality_code), int(row.season_year)): float(row.yield_t_ha)
              for row in out.itertuples()}
    out["yield_lag_1_t_ha"] = [lookup.get((str(code), int(year)-1), np.nan)
                                for code, year in zip(out["municipality_code"], out["season_year"])]
    out["yield_lag_2_t_ha"] = [lookup.get((str(code), int(year)-2), np.nan)
                                for code, year in zip(out["municipality_code"], out["season_year"])]
    return out


def _fit_spatial_cv(candidates, x, y, groups):
    splits = min(5, groups.nunique())
    if splits < 3:
        raise ValueError("at least three spatial groups are needed for model selection")
    cv = GroupKFold(n_splits=splits)
    scores = {name: float(-cross_val_score(
        estimator, x, y, groups=groups, cv=cv,
        scoring="neg_mean_absolute_error", n_jobs=1).mean())
        for name, estimator in candidates.items()}
    selected = min(scores, key=scores.get)
    return candidates[selected].fit(x, y), selected, scores


def _cluster_bootstrap_ci(frame: pd.DataFrame, value_column: str, *,
                          repetitions: int = 2000, seed: int = 271828) -> list[float]:
    """Percentile CI resampling held-out spatial blocks, preserving within-block dependence."""
    blocks = [g[value_column].dropna().to_numpy(dtype=float)
              for _, g in frame.groupby("spatial_block")]
    blocks = [x for x in blocks if len(x)]
    if len(blocks) < 5:
        raise ValueError("cluster uncertainty requires at least five held-out spatial blocks")
    rng = np.random.default_rng(seed)
    estimates = np.empty(repetitions, dtype=float)
    for i in range(repetitions):
        sample = rng.integers(0, len(blocks), size=len(blocks))
        vals = [blocks[j] for j in sample]
        estimates[i] = np.concatenate(vals).mean()
    return [float(np.quantile(estimates, .025)), float(np.quantile(estimates, .975))]


def _block_metrics(frame: pd.DataFrame, nominal_coverage: float) -> dict:
    result = {}
    for block, group in frame.groupby("spatial_block"):
        independent = _independent_rows(group)
        n = len(independent)
        covered = int(independent["_covered"].sum())
        result[str(block)] = {
            "n_independent": n, "n_covered": covered, "coverage": covered/n if n else None,
            "coverage_role": "descriptive_by_block; aggregate uncertainty uses spatial-block bootstrap",
            "interval_acceptable": n >= _MIN_TEST_MUNICIPALITIES,
            "rmse_t_ha": float(np.sqrt(independent["_sq_error"].mean())) if n else None,
            "mae_t_ha": float(independent["_abs_error"].mean()) if n else None,
            "bias_t_ha": float(independent["_bias"].mean()) if n else None,
        }
    return result


def train_crop_yield_model(
    panel: pd.DataFrame,
    *,
    crop: str,
    forecast_phase: str,
    heldout_blocks: list[str],
    artifact_path: str | Path,
    nominal_coverage: float = 0.90,
    min_improvement_over_median: float = 0.0,
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
    data = data.loc[data["forecast_phase"].astype(str).str.casefold() == str(forecast_phase).casefold()].copy()
    if data.empty:
        raise ValueError("no public yield records for requested crop")
    _check_source_provenance(data)
    data["season_year"] = pd.to_numeric(data["season_year"], errors="raise").astype(int)
    data["yield_t_ha"] = pd.to_numeric(data["yield_t_ha"], errors="coerce")
    data = data[np.isfinite(data["yield_t_ha"]) & (data["yield_t_ha"] > 0)].copy()
    _check_historical_asof(data)
    if data.duplicated(["municipality_code", "season_year"]).any():
        raise ValueError("duplicate municipality-season labels; resolve crop season/multiple harvests")
    data = _add_historical_yield_features(data)
    # A one-season historical yield is an operationally available benchmark.
    # Never fill gaps across suppressed or missing PAM years.
    data = data[data["yield_lag_1_t_ha"].notna()].copy()
    if data.empty:
        raise ValueError("no consecutive prior-season PAM yield for persistence benchmark")
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
    model, selected_name, cv_mae = _fit_spatial_cv(candidates, x_train, y_train, groups)

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
    coverage_ci = _cluster_bootstrap_ci(independent.assign(_covered_float=independent["_covered"].astype(float)),
                                        "_covered_float")
    mae = float(independent["_abs_error"].mean())
    rmse = float(np.sqrt(independent["_sq_error"].mean()))
    bias = float(independent["_bias"].mean())
    median_baseline = float(np.median(y_train))
    baseline_mae = float(np.mean(np.abs(independent["yield_t_ha"]-median_baseline)))
    improvement = (baseline_mae-mae)/baseline_mae if baseline_mae else 0.0
    climate_features = [f for f in features if f.startswith(("climate_", "weather_"))]
    history_features = [f for f in features if f.startswith("yield_lag_")]
    baseline_sets = {
        "climate_only": climate_features,
        "historical_yield_only": ["yield_lag_1_t_ha"],
        "historical_yield_plus_climate": history_features + climate_features,
    }
    baseline_candidates = {
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                  max_features=0.8, random_state=42, n_jobs=-1)),
        "hist_gradient_boosting": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            HistGradientBoostingRegressor(max_iter=150, max_leaf_nodes=15,
                                          l2_regularization=2.0, random_state=42)),
    }
    baseline_maes = {}
    baseline_predictions = {}
    baseline_cv = {}
    for baseline_name, cols in baseline_sets.items():
        if not cols:
            raise ValueError("climate and historical yield baselines are mandatory")
        baseline_model, baseline_algorithm, fold_scores = _fit_spatial_cv(
            dict(baseline_candidates), train[cols], y_train, groups)
        pred = np.maximum(0.0, baseline_model.predict(test[cols]))
        baseline_predictions[baseline_name] = pred
        baseline_maes[baseline_name] = float(np.mean(np.abs(test["yield_t_ha"].to_numpy()-pred)))
        baseline_cv[baseline_name] = {"algorithm": baseline_algorithm, "spatial_cv_mae_t_ha": fold_scores}
    height_features = [c for c in features if c.startswith("sar_height_")]
    height_incremental_ci = None
    if height_features:
        without_height = [c for c in features if not c.startswith("sar_height_")]
        height_ablation_model, height_ablation_algorithm, height_ablation_cv = _fit_spatial_cv(
            dict(baseline_candidates), train[without_height], y_train, groups)
        height_ablation_pred = np.maximum(0.0, height_ablation_model.predict(test[without_height]))
        height_ablation_errors = np.abs(test["yield_t_ha"].to_numpy()-height_ablation_pred)
        full_errors = np.abs(test["yield_t_ha"].to_numpy()-test_pred)
        height_score = test.assign(_height_incremental_skill=height_ablation_errors-full_errors)
        height_score = height_score.loc[independent.index]
        height_incremental_ci = _cluster_bootstrap_ci(height_score, "_height_incremental_skill")
        if height_incremental_ci[0] <= 0:
            raise ValueError("validated SAR height did not improve independent spatial-block forecast skill")
    strongest_baseline_name = min(baseline_maes, key=baseline_maes.get)
    strongest_baseline_mae = baseline_maes[strongest_baseline_name]
    sar_skill = ((strongest_baseline_mae-mae)/strongest_baseline_mae
                 if strongest_baseline_mae else 0.0)
    # Align benchmark predictions to the one-per-N9 independent scoring rows.
    scored_index = independent.index
    benchmark_errors = {}
    test_scored = test.assign(_model_abs_error=np.abs(test["yield_t_ha"].to_numpy()-test_pred))
    for name, pred in baseline_predictions.items():
        test_scored[f"_{name}_abs_error"] = np.abs(test["yield_t_ha"].to_numpy()-pred)
        benchmark_errors[name] = _cluster_bootstrap_ci(
            test_scored.loc[scored_index].assign(
                _skill=(test_scored.loc[scored_index, f"_{name}_abs_error"] -
                        test_scored.loc[scored_index, "_model_abs_error"])), "_skill")
    strongest_skill_ci = benchmark_errors[strongest_baseline_name]
    interval_ok = coverage_ci[0] <= nominal_coverage <= coverage_ci[1]
    per_block = _block_metrics(test_cov_frame, nominal_coverage)
    eligible_blocks = [b for b, m in per_block.items() if m["interval_acceptable"]]
    if len(eligible_blocks) < _MIN_SPATIAL_BLOCKS:
        raise ValueError("fewer than five held-out spatial blocks meet per-block coverage and sample criteria")
    if not interval_ok:
        raise ValueError("prediction interval failed independent spatial-temporal coverage criterion")
    if improvement <= min_improvement_over_median:
        raise ValueError("selected model did not beat the training-median baseline sufficiently")
    if sar_skill <= min_improvement_over_median or strongest_skill_ci[0] <= 0:
        raise ValueError("SAR+climate model failed to beat the strongest climate/history baseline with positive block-bootstrap skill")
    if n_independent < _MIN_TEST_MUNICIPALITIES:
        raise ValueError("test set lost independent municipalities after deduplication")

    feature_support = {}
    for col in features:
        values = train[col].dropna().astype(float)
        q01, q25, q75, q99 = values.quantile([.01, .25, .75, .99])
        feature_support[col] = {"q01": float(q01), "q99": float(q99),
                                "iqr": float(q75-q25)}
    manifest = {
        "schema_version": 2, "crop": crop, "forecast_phase": forecast_phase,
        "model_id": f"ev-yield-{crop.casefold()}-{forecast_phase.casefold()}-{test_year}",
        "algorithm": selected_name, "feature_columns": features,
        "nominal_coverage": nominal_coverage, "conformal_radius_t_ha": radius,
        "calibration": {"year": calibration_year, "n_municipalities": cal_units,
                        "method": "split conformal absolute residual; later-year held-out blocks",
                        "assumption": "exchangeability is not guaranteed under spatial or temporal distribution shift; coverage is an empirical test result, not a universal guarantee"},
        "validation": {"independent_test": True, "in_domain": True,
                       "spatial_temporal_holdout": True, "test_year": test_year,
                       "heldout_blocks": sorted(heldout), "n_independent": n_independent,
                       "n_covered": n_covered, "coverage": coverage,
                       "coverage_cluster_bootstrap95": coverage_ci,
                       "coverage_uncertainty_method": "percentile bootstrap of held-out spatial blocks; 2000 draws",
                       "nominal_coverage": nominal_coverage,
                       "rmse_t_ha": rmse, "mae_t_ha": mae, "bias_t_ha": bias,
                       "sample_count": n_independent,
                       "median_baseline_mae_t_ha": baseline_mae,
                       "improvement_over_median": improvement,
                       "benchmarks_mae_t_ha": baseline_maes,
                       "strongest_benchmark": strongest_baseline_name,
                       "sar_skill_vs_strongest_benchmark": sar_skill,
                       "sar_skill_block_bootstrap95_t_ha": strongest_skill_ci,
                       "sar_skill_block_bootstrap95_by_benchmark_t_ha": benchmark_errors,
                       "sar_height_incremental_skill_block_bootstrap95_t_ha": height_incremental_ci,
                       "benchmark_spatial_cv": baseline_cv,
                       "internal_spatial_cv_mae_t_ha": cv_mae,
                       "per_spatial_block": per_block,
                       "eligible_spatial_blocks": sorted(eligible_blocks)},
        "training": {"n_rows": len(train), "n_municipalities": train["municipality_code"].nunique(),
                     "first_year": int(train["season_year"].min()),
                     "last_year": int(train["season_year"].max()),
                     "yield_sources": sorted(data["yield_source_url"].astype(str).unique()),
                     "yield_licenses": sorted(data["yield_license"].astype(str).unique()),
                     "sar_sources": sorted(data["sar_source_url"].astype(str).unique()),
                     "weather_sources": sorted(data["weather_source"].astype(str).unique()),
                     "weather_source_urls": sorted(data["weather_source_url"].astype(str).unique()),
                     "panel_sha256": hashlib.sha256(pd.util.hash_pandas_object(data, index=True).values.tobytes()).hexdigest()},
        "feature_support": feature_support,
        "height_predictors_used": height_features,
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


def _check_historical_asof(frame: pd.DataFrame) -> None:
    for row in frame.itertuples():
        try:
            origin = _as_utc(row.forecast_origin_utc)
            acquisition = _as_utc(row.sar_latest_acquisition_utc)
            weather_end = _as_utc(row.weather_period_end_utc)
            weather_available = _as_utc(row.weather_available_asof_utc)
            weather_start = _as_utc(row.weather_period_start_utc)
            if acquisition > origin or weather_end > origin or weather_available > origin or weather_start > weather_end:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            raise ValueError("training row contains SAR or weather information unavailable at its forecast origin")


def _as_utc(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must carry timezone")
    return parsed.astimezone(timezone.utc)


def forecast_crop_yield(artifact_path: str | Path, features: dict, *,
                        crop: str, forecast_phase: str, region: str,
                        spatial_block: str, season: str,
                        weather_provenance: dict, imagery_provenance: dict,
                        freshness_provenance: dict,
                        reference_date_utc: str | None = None):
    """Predict only within independently evaluated spatial blocks/domains."""
    stored = load(artifact_path)
    model, manifest = stored["model"], stored["manifest"]
    val = manifest["validation"]
    if str(crop).casefold() != str(manifest["crop"]).casefold():
        raise ValueError("crop does not match trained model")
    if str(forecast_phase).casefold() != str(manifest["forecast_phase"]).casefold():
        raise ValueError("forecast phase does not match calibrated model")
    if str(spatial_block) not in val["heldout_blocks"]:
        raise ValueError("requested spatial block has no independent transfer validation")
    cols = manifest["feature_columns"]
    missing = [c for c in cols if c not in features]
    if missing:
        raise ValueError("forecast feature vector missing: "+", ".join(missing))
    x = pd.DataFrame([{c: pd.to_numeric(pd.Series([features[c]]), errors="coerce").iloc[0]
                        for c in cols}], columns=cols)
    if x.isna().any().any():
        raise ValueError("non-numeric or missing SAR/climate forecast feature")
    for col in cols:
        support = manifest["feature_support"][col]
        spread = max(float(support["iqr"]), 1e-9)
        if float(x.iloc[0][col]) < support["q01"]-3*spread or float(x.iloc[0][col]) > support["q99"]+3*spread:
            raise ValueError("forecast outside training feature support: "+col)
    block_val = val.get("per_spatial_block", {}).get(str(spatial_block))
    if not block_val or not block_val.get("interval_acceptable"):
        raise ValueError("spatial block lacks independent calibration/coverage evidence")
    prediction = max(0.0, float(model.predict(x)[0]))
    radius = float(manifest["conformal_radius_t_ha"])
    interval = {"lower": max(0.0, prediction-radius), "upper": prediction+radius,
                "nominal_coverage": manifest["nominal_coverage"],
                "method": "split conformal absolute residual"}
    validation = {
        **block_val, "independent_test": True, "in_domain": True,
        "spatial_temporal_holdout": True, "sample_count": val["n_independent"],
        "rmse_t_ha": val["rmse_t_ha"], "mae_t_ha": val["mae_t_ha"],
        "bias_t_ha": val["bias_t_ha"],
        "prediction_interval_validation": {
            "independent_test": True, "spatial_temporal_holdout": True,
            "method": "later-season independent test with resampling by spatial blocks",
            "nominal_coverage": manifest["nominal_coverage"],
            "n_independent": val["n_independent"],
            "n_covered": val["n_covered"],
            "n_spatial_blocks": len(val["per_spatial_block"]),
            "uncertainty_method": "spatial_block_bootstrap",
            "coverage_cluster_bootstrap95": val["coverage_cluster_bootstrap95"]}}
    result = evaluate_yield_forecast(
        predicted_t_ha=prediction, model_id=manifest["model_id"], crop=crop,
        region=region, season=season, weather_provenance=weather_provenance,
        imagery_provenance=imagery_provenance, validation=validation,
        prediction_interval_t_ha=interval, reference_date_utc=reference_date_utc,
        freshness_provenance=freshness_provenance)
    return result
