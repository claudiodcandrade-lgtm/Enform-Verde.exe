"""Scientific gates for crop health indicators and yield forecasts.

This module evaluates external, validated outputs. It does NOT diagnose pests,
diseases, or generate yield from SAR without trained models.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

@dataclass(frozen=True)
class CropAssessment:
    status: str
    value: float | None
    unit: str
    uncertainty: float | None
    provenance: dict
    limitations: tuple[str, ...]

def assess_crop_stress(*, indicators, baseline, observations_utc, sensor_sources,
                       model_validated=False, reference_region=None):
    """Flag descriptive anomalies, not diseases or pest identity."""
    notes = []
    if not observations_utc or not sensor_sources:
        notes.append("Sem observações datadas e fontes verificáveis")
    if not model_validated:
        notes.append("Modelo fitossanitário não validado para esta cultura e região")
    deviations = {}
    for key, value in indicators.items():
        ref = baseline.get(key)
        if not ref or len(ref) != 2 or ref[1] <= 0:
            continue
        if all(isfinite(float(x)) for x in (value, *ref)):
            deviations[key] = round((float(value) - float(ref[0])) / float(ref[1]), 3)
    if not deviations:
        notes.append("Sem linha de base sazonal comparável")
    return {"status": "indicadores_exploratorios" if deviations else "dados_insuficientes",
            "standardized_anomalies": deviations,
            "phytosanitary_diagnosis": "não determinado",
            "sources": list(sensor_sources), "observations_utc": list(observations_utc),
            "region": reference_region, "limitations": notes + [
                "Anomalia SAR/óptica não identifica etiologia de doença ou praga"]}

def _wilson_interval(successes, total, z=1.959963984540054):
    """Wilson score interval for empirical prediction-interval coverage."""
    if total <= 0:
        return None
    p = successes / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total)) / denom
    half = z * ((p*(1-p)/total + z*z/(4*total*total)) ** 0.5) / denom
    return [max(0.0, center-half), min(1.0, center+half)]


def evaluate_yield_forecast(*, predicted_t_ha, model_id, crop, region, season,
                            weather_provenance, imagery_provenance, validation,
                            prediction_interval_t_ha=None, uncertainty_t_ha=None,
                            reference_date_utc=None):
    """Release a forecast only with independently calibrated predictive uncertainty.

    prediction_interval_t_ha must be a central, calibrated prediction interval
    from the fitted model. Validation coverage is checked on independent
    out-of-sample forecasts; a standard error or RMSE alone is not a predictive
    interval and cannot satisfy this gate.
    """
    errors = []
    validation = validation if isinstance(validation, dict) else {}
    if not model_id or not crop or not region or not season:
        errors.append("Modelo, cultura, região e safra obrigatórios")
    if not weather_provenance or not imagery_provenance:
        errors.append("Fontes meteorológicas e orbitais não verificadas")
    if not validation.get("independent_test") or not validation.get("in_domain"):
        errors.append("Validação independente e domínio de aplicação não comprovados")
    for metric in ("rmse_t_ha", "mae_t_ha", "bias_t_ha", "sample_count"):
        if metric not in validation:
            errors.append("Métrica de validação ausente: " + metric)
    interval = prediction_interval_t_ha
    if not isinstance(interval, dict):
        errors.append("Intervalo preditivo calibrado obrigatório; estimativa pontual bloqueada")
    else:
        try:
            lower, upper = float(interval["lower"]), float(interval["upper"])
            nominal = float(interval["nominal_coverage"])
            method = str(interval["method"]).strip()
            if not all(isfinite(v) for v in (lower, upper, nominal)) or lower < 0 or upper < lower or not 0 < nominal < 1 or not method:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            errors.append("Intervalo preditivo inválido: limites, nível e método são obrigatórios")
            interval = None
    iv = validation.get("prediction_interval_validation")
    if not isinstance(iv, dict):
        errors.append("Validação independente da cobertura do intervalo preditivo ausente")
    else:
        try:
            n = int(iv["n_independent"])
            covered = int(iv["n_covered"])
            val_nominal = float(iv["nominal_coverage"])
            if (n < 50 or covered < 0 or covered > n or not isfinite(val_nominal)
                    or not iv.get("independent_test") or not iv.get("spatial_temporal_holdout")
                    or not iv.get("method")):
                raise ValueError()
            coverage_interval = _wilson_interval(covered, n)
            if interval is None or abs(val_nominal - float(interval["nominal_coverage"])) > 1e-9:
                errors.append("Nível nominal da validação não corresponde ao intervalo publicado")
            elif not coverage_interval[0] <= val_nominal <= coverage_interval[1]:
                errors.append("Cobertura empírica do intervalo incompatível com o nível nominal no IC95% Wilson")
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append("Calibração exige ≥50 previsões independentes com holdout espacial e temporal e cobertura documentada")
    try:
        value = float(predicted_t_ha)
        if not isfinite(value) or value < 0:
            errors.append("Produtividade inválida")
    except (TypeError, ValueError):
        value = None
        errors.append("Produtividade indisponível")
    if interval is not None and value is not None:
        if not float(interval["lower"]) <= value <= float(interval["upper"]):
            errors.append("Estimativa pontual fora do intervalo preditivo declarado")
    if uncertainty_t_ha is not None:
        try:
            if not isfinite(float(uncertainty_t_ha)) or float(uncertainty_t_ha) < 0:
                errors.append("Incerteza inválida")
        except (TypeError, ValueError):
            errors.append("Incerteza inválida")
    if reference_date_utc:
        try:
            dt = datetime.fromisoformat(reference_date_utc.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                errors.append("Data sem fuso")
        except ValueError:
            errors.append("Data inválida")
    interval_out = None if interval is None else {
        "lower_t_ha": float(interval["lower"]), "upper_t_ha": float(interval["upper"]),
        "nominal_coverage": float(interval["nominal_coverage"]), "method": interval["method"],
        "validated_coverage": (int(iv["n_covered"]) / int(iv["n_independent"])) if isinstance(iv, dict) and iv.get("n_independent") else None,
        "coverage_wilson95": _wilson_interval(int(iv["n_covered"]), int(iv["n_independent"])) if isinstance(iv, dict) and iv.get("n_independent") else None
    }
    half_width = max(value - interval_out["lower_t_ha"], interval_out["upper_t_ha"] - value) if interval_out and value is not None else None
    return CropAssessment(
        status="previsao_validada" if not errors else "previsao_nao_habilitada",
        value=value if not errors else None, unit="t/ha",
        uncertainty=half_width if not errors else None,
        provenance={"model": model_id, "crop": crop, "region": region, "season": season,
                    "weather": weather_provenance, "imagery": imagery_provenance,
                    "validation": validation, "prediction_interval": interval_out,
                    "reference_date_utc": reference_date_utc},
        limitations=tuple(errors))
