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

def evaluate_yield_forecast(*, predicted_t_ha, model_id, crop, region, season,
                            weather_provenance, imagery_provenance, validation,
                            uncertainty_t_ha=None, reference_date_utc=None):
    """Reject unsupported production forecasts; preserve validation evidence."""
    errors = []
    if not model_id or not crop or not region or not season:
        errors.append("Modelo, cultura, região e safra obrigatórios")
    if not weather_provenance or not imagery_provenance:
        errors.append("Fontes meteorológicas e orbitais não verificadas")
    if not validation.get("independent_test") or not validation.get("in_domain"):
        errors.append("Validação independente e domínio de aplicação não comprovados")
    for metric in ("rmse_t_ha", "bias_t_ha", "sample_count"):
        if metric not in validation:
            errors.append("Métrica de validação ausente: " + metric)
    try:
        value = float(predicted_t_ha)
        if not isfinite(value) or value < 0:
            errors.append("Produtividade inválida")
    except (TypeError, ValueError):
        value = None
        errors.append("Produtividade indisponível")
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
    return CropAssessment(
        status="previsao_validada" if not errors else "previsao_nao_habilitada",
        value=value if not errors else None, unit="t/ha",
        uncertainty=float(uncertainty_t_ha) if uncertainty_t_ha is not None and not errors else None,
        provenance={"model": model_id, "crop": crop, "region": region, "season": season,
                    "weather": weather_provenance, "imagery": imagery_provenance,
                    "validation": validation, "reference_date_utc": reference_date_utc},
        limitations=tuple(errors))
