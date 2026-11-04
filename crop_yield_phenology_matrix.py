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


def experimental_prior_projection(crop, *, pam_baseline_kg_ha, stages, ky_by_stage,
                                  published_prior, n_mc=4000, seed=20261104):
    """Enable explicitly EXPERIMENTAL SAR×phenology yield from a PUBLISHED parameter prior.

    Unlike integrate_yield_matrix (which requires independently observed field
    calibration), this exploratory route propagates uncertainty in published
    crop/stage matched regression coefficients and documented historical error.
    A crop name alone is NOT a justification for transferring coefficients.
    Missing scientific evidence yields N/D, never synthetic coefficients.

    Required prior: {source_url, crop, stage_names, feature_names, coeff_mean,
    coeff_sd, historical_residuals_kg_ha, transfer_sd_kg_ha,
    coefficient_domain, baseline_uncertainty_kg_ha}. The source must be
    independently audited for appropriateness before use.
    """
    names, features = design_features(crop, {"stages": stages}, ky_by_stage=ky_by_stage)
    baseline = float(pam_baseline_kg_ha)
    result = {"status": "N/D", "crop": crop, "model": "PAM × FAO × SAR — coeficientes publicados",
              "pam_baseline_kg_ha": baseline, "stage_feature_names": names,
              "stage_feature_values": features}
    if not isinstance(published_prior, Mapping):
        result["reason"] = "sem publicação com coeficientes e dispersões por cultura e fase"
        return result
    if (published_prior.get("crop") != crop
            or published_prior.get("feature_names") != names
            or not str(published_prior.get("source_url", "")).startswith("https://")
            or not published_prior.get("coefficient_domain")
            or not published_prior.get("reviewed_crop_stage_transfer")):
        result["reason"] = "domínio científico da publicação ou compatibilidade de estádios não documentados"
        return result
    means = published_prior.get("coeff_mean", [])
    sds = published_prior.get("coeff_sd", [])
    residuals = published_prior.get("historical_residuals_kg_ha", [])
    sigma_base = published_prior.get("baseline_uncertainty_kg_ha")
    sigma_transfer = published_prior.get("transfer_sd_kg_ha")
    try:
        import numpy as np
        mu = np.asarray(means, dtype=float)
        sig = np.asarray(sds, dtype=float)
        e = np.asarray(residuals, dtype=float)
        base_sd = float(sigma_base)
        trans_sd = float(sigma_transfer)
        if (len(mu) != len(names) or len(sig) != len(names) or len(e) < 6
                or not np.isfinite(mu).all() or not np.isfinite(sig).all()
                or not np.isfinite(e).all() or (sig < 0).any()
                or not math.isfinite(baseline) or baseline < 0 or
                not math.isfinite(base_sd) or base_sd < 0 or
                not math.isfinite(trans_sd) or trans_sd < 0 or
                not isinstance(n_mc, int) or not 500 <= n_mc <= 50000):
            raise ValueError("parâmetros incompletos ou não finitos")
    except (TypeError, ValueError, KeyError) as exc:
        result["reason"] = "prior ou erros históricos inválidos: " + str(exc)
        return result
    rng = np.random.default_rng(seed)
    c = rng.normal(mu, sig, size=(n_mc, len(mu)))
    x = np.asarray(features, dtype=float)
    samples = np.maximum(0.0, baseline + rng.normal(0, base_sd, n_mc)
                         + c @ x + rng.choice(e, n_mc, replace=True)
                         + rng.normal(0, trans_sd, n_mc))
    median, lo, hi = (float(np.quantile(samples, q)) for q in (.5, .05, .95))
    result.update({"status": "experimental_literature_prior_not_field_validated",
                   "median_kg_ha": median, "p05_kg_ha": lo, "p95_kg_ha": hi,
                   "median_t_ha": median / 1000, "interval_90_t_ha": [lo / 1000, hi / 1000],
                   "source_url": published_prior["source_url"],
                   "coefficient_domain": published_prior["coefficient_domain"],
                   "n_mc": n_mc, "seed": seed,
                   "uncertainty_scope": ("Propagação Monte Carlo do prior publicado, variabilidade PAM "
                                         "e transferência informada. NÃO é validação em propriedade; "
                                         "cobertura do intervalo preditivo não demonstrada."),
                   "warning": "EXPERIMENTAL; verificação de campo e validação espacial pendentes"})
    if crop == "Soja":
        result.update({"median_sacks_60kg_ha": median / 60,
                       "interval_90_sacks_60kg_ha": [lo / 60, hi / 60],
                       "interval_90_relative_percent": ([100*(lo-median)/median, 100*(hi-median)/median]
                                                       if median else None)})
    return result
