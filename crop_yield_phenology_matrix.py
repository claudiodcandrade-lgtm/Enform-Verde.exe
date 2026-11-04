"""Phenology-explicit PAM × observed SAR vigor × water/climate yield matrix.

Scientific components:
- FAO-56: daily ETc = Kc(stage) * ET0 and actual ETa = Ks * ETc.
- FAO-33: stress per stage D_s = 1 - ETa_s/ETc_s, with sensitivity Ky_s.
- Historical PAM provides baseline and climate response, not plot-level SAR
  calibration. Radar vigor/phenology influences yield ONLY when fitted against
  independent observed yields from real fields in the same crop/region/stages.

Stage-dependent statistical model (crop-specific fit):
    y_{u,t} = a_u + b_u t + sum_s [
        beta_s * Ky_s * D_s + gamma_s * V_s +
        delta_s * D_s * V_s + eta_s * H_s] + epsilon_{u,t}
The interaction D_s * V_s captures distinct vigor sensitivity under water
stress. H_s must be a reference-standardized phenological temperature/radiation
stress metric (not raw Celsius). All coefficients are fitted, never invented.
Training and validation block entire years; inter-field spatial transfer
requires an independent spatial block validation, not only yearly hindcasts.

No external crop simulator is implied to be installed or executable.
"""
from __future__ import annotations
from collections.abc import Mapping
import math

from crop_specific_model_registry import MODEL_REGISTRY

FEATURE_KINDS = ("water_stress", "heat_stress", "sar_vigor", "water_x_vigor")
STAGE_UNITS = ("ETa_ETc", "heat_reference_z", "sar_vigor_reference_z")


def validate_field_observation(crop, obs):
    """Validate one independently observed crop yield + stage feature record."""
    if crop not in MODEL_REGISTRY:
        raise ValueError("cultura sem modelo de estádios")
    if not isinstance(obs, Mapping) or not obs.get("field_id") or not obs.get("harvest_year"):
        raise ValueError("identificador de talhão e ano-safra obrigatórios")
    if not obs.get("observed_yield_source"):
        raise ValueError("produtividade REAL independente da PAM obrigatória para ajustar SAR")
    y = float(obs.get("observed_yield_kg_ha"))
    if not math.isfinite(y) or y < 0:
        raise ValueError("produtividade observada inválida")
    stages = MODEL_REGISTRY[crop]["critical_stages"]
    measures = obs.get("stages")
    if not isinstance(measures, Mapping) or set(measures) != set(stages):
        raise ValueError("exigir registros das fases fenológicas específicas da cultura")
    for stage in stages:
        m = measures[stage]
        if not isinstance(m, Mapping):
            raise ValueError("medição por estágio inválida")
        for k in ("eta_etc", "heat_z", "sar_vigor_z"):
            v = float(m[k])
            if not math.isfinite(v):
                raise ValueError("variável por estágio não finita")
        if not 0 <= float(m["eta_etc"]) <= 1:
            raise ValueError("ETa/ETc deve estar entre zero e um")
        if not m.get("sar_scene_ids") or not m.get("sar_acquisition_utc"):
            raise ValueError("vigor precisa ter cenas Sentinel-1 reais e datas")
        if not m.get("sar_pixels_read"):
            raise ValueError("exigir leitura SAR VV/VH comprovada")
        if not m.get("weather_source"):
            raise ValueError("exigir fonte meteorológica rastreável")


def design_features(crop, observation, *, ky_by_stage):
    """Build strictly ordered climate × vigor stage matrix (no fitted coefficients)."""
    stages = MODEL_REGISTRY[crop]["critical_stages"]
    if set(ky_by_stage) != set(stages):
        raise ValueError("sensibilidades Ky calibradas para TODAS as fases exigidas")
    x, names = [], []
    for stage in stages:
        m = observation["stages"][stage]
        ky = float(ky_by_stage[stage])
        if not math.isfinite(ky) or ky < 0:
            raise ValueError("Ky de estádio inválido")
        deficit = ky * (1.0 - float(m["eta_etc"]))
        vigor = float(m["sar_vigor_z"])
        heat = float(m["heat_z"])
        # Ky*deficit supplies physiologically scaled exposure; all four
        # coefficients remain empirical, even when FAO-33 supplies Ky.
        x.extend((deficit, heat, vigor, deficit * vigor))
        names.extend(f"{stage}:{name}" for name in FEATURE_KINDS)
    return names, x


def integrate_yield_matrix(crop, *, pam_baseline_kg_ha, stages, ky_by_stage,
                           calibration=None, prior_validation=None):
    """Compute a yield only with independent field-fit calibration for the same crop.

    A PAM-only artifact cannot identify SAR vigor coefficients. In that case
    return N/D for the integrated SAR-conditional yield, while retaining the
    historical baseline separately and explicit scientific reasons.
    """
    names, x = design_features(crop, {"stages": stages}, ky_by_stage=ky_by_stage)
    baseline = float(pam_baseline_kg_ha)
    if not math.isfinite(baseline) or baseline < 0:
        raise ValueError("PAM baseline must be a nonnegative kg/ha")
    audit = {"status": "N/D", "crop": crop, "pam_baseline_kg_ha": baseline,
             "feature_names": names, "feature_values": x,
             "formula": "Y = PAM_base + Σ_s(β_s Ky_s(1−ETa/ETc)_s + η_s H_s + γ_s V_s + δ_s Ky_s(1−ETa/ETc)_s V_s)",
             "source_type": "PAM histórico + FAO-56/FAO-33 + SAR real"}
    if calibration is None or prior_validation is None:
        audit["reason"] = ("coeficientes SAR × fase e validação independente não disponíveis; "
                           "não atribuir à PAM calibração de vigor")
        return audit
    if (calibration.get("crop") != crop or calibration.get("feature_names") != names
            or not calibration.get("field_yield_observation_provenance")
            or not prior_validation.get("leave_year_out_pass")
            or not prior_validation.get("spatial_holdout_pass")):
        audit["reason"] = "calibração incompatível ou validação temporal/espacial ausente"
        return audit
    betas = calibration.get("coefficients")
    if not isinstance(betas, (tuple, list)) or len(betas) != len(x):
        audit["reason"] = "dimensão dos coeficientes da matriz incompatível"
        return audit
    if any(not math.isfinite(float(v)) for v in betas):
        audit["reason"] = "coeficientes inválidos"
        return audit
    # Predictive interval must come from held-out empirical residuals and
    # include documented transfer/spatial/measurement effects, not a guessed %.
    residuals = prior_validation.get("predictive_residuals_kg_ha")
    if not isinstance(residuals, list) or len(residuals) < 10:
        audit["reason"] = "menos de dez erros preditivos independentes para intervalo de previsão"
        return audit
    import numpy as np
    errors = np.asarray(residuals, dtype=float)
    if not np.isfinite(errors).all():
        audit["reason"] = "erros preditivos inválidos"
        return audit
    pred = max(0.0, baseline + sum(float(c) * v for c, v in zip(betas, x)))
    samples = np.maximum(0., pred + errors)
    audit.update({"status": "experimental_calibrated_independently",
                  "predicted_kg_ha": pred,
                  "predictive_interval_90_kg_ha": [float(np.quantile(samples, .05)),
                                                  float(np.quantile(samples, .95))],
                  "interval_scope": ("erro validado nos resíduos informados; "
                                     "não inclui fatores sem evidência quantitativa"),
                  "calibration_sources": calibration["field_yield_observation_provenance"]})
    return audit
