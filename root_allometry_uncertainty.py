"""Conditional uncertainty propagation for the Cairns (1997) live-root equation.

This does not provide default coefficients' uncertainty, a validated geographic
domain, or a national root-stock CI. It only propagates uncertainties that were
independently documented and explicitly supplied by an applicable source.
"""
import math
import random

COEFFICIENTS = (-1.0587, 0.8836)
CARBON_FRACTION = 0.47


def _finite_positive(value, label, allow_zero=False):
    if isinstance(value, bool):
        raise ValueError(label + " must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(label + " must be numeric") from exc
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(label + " must be finite and positive")
    return number


def cairns_root_prediction(agb_mg_ha, *, calibration=None, draws=12000, seed=42):
    """Return predicted live roots (tC/ha) and conditional uncertainty if supported.

    AGB is live aboveground dry biomass (Mg/ha), NOT carbon. Full uncertainty
    requires the *mean AGB* standard deviation/SE (correct scale for AOI),
    coefficient covariance and residual error from a valid forest-domain source.

    Intervals are predictive for a stock density conditional on the inputs, NOT
    an independently calibrated 95% coverage statement for a new AOI.
    """
    agb = _finite_positive(agb_mg_ha, "AGB")
    b0, b1 = COEFFICIENTS
    point_dry = math.exp(b0 + b1 * math.log(agb))
    output = {
        "mean_model_tc_ha": point_dry * CARBON_FRACTION,
        "median_model_dry_mg_ha": point_dry,
        "conditional_prediction_interval_tc_ha": None,
        "uncertainty_status": "not_quantified",
        "coverage_validated": False,
        "limitations": "No coefficient covariance, residual error and AGB error verified together",
    }
    if calibration is None:
        return output
    if not isinstance(calibration, dict):
        raise ValueError("calibration must be a mapping")
    required = ("source", "applicable_physiognomy", "agb_sd_mg_ha",
                "coefficient_covariance", "residual_sd_log", "independent_validation")
    if any(calibration.get(k) is None for k in required):
        raise ValueError("incomplete root calibration evidence")
    if not str(calibration["source"]).strip() or not str(calibration["applicable_physiognomy"]).strip():
        raise ValueError("root calibration provenance/domain missing")
    if calibration["independent_validation"] is not True:
        raise ValueError("independent root calibration validation required")
    sd_agb = _finite_positive(calibration["agb_sd_mg_ha"], "AGB SD", True)
    residual_sd = _finite_positive(calibration["residual_sd_log"], "residual log SD", True)
    cov = calibration["coefficient_covariance"]
    try:
        a, c = float(cov[0][0]), float(cov[0][1])
        e, d = float(cov[1][0]), float(cov[1][1])
        if len(cov) != 2 or any(len(row) != 2 for row in cov):
            raise ValueError()
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError("invalid coefficient covariance matrix") from exc
    if any(not math.isfinite(x) for x in (a, c, e, d)) or min(a, d) < 0 or abs(c-e) > 1e-10 or c*c > a*d + 1e-12:
        raise ValueError("coefficient covariance must be positive semidefinite")
    if not isinstance(draws, int) or not 1000 <= draws <= 50000:
        raise ValueError("draws must be between 1000 and 50000")
    # Lognormal AGB distribution is parameterized by the declared AGB mean+SD.
    variance_log = math.log1p((sd_agb / agb)**2)
    mu_log = math.log(agb) - variance_log / 2.0
    sqrt_var = math.sqrt(variance_log)
    rng = random.Random(seed)
    # Exact 2x2 PSD factorization; handles a zero-variance intercept.
    l11 = math.sqrt(a)
    if l11 > 0:
        l21 = c / l11
        l22 = math.sqrt(max(0.0, d - l21*l21))
    else:
        if abs(c) > 1e-12:
            raise ValueError("covariance with zero-variance intercept")
        l21, l22 = 0.0, math.sqrt(d)
    sims = []
    for _ in range(draws):
        z0, z1 = rng.gauss(0, 1), rng.gauss(0, 1)
        intercept = b0 + l11*z0
        slope = b1 + l21*z0 + l22*z1
        sample_log_agb = mu_log + sqrt_var*rng.gauss(0, 1)
        log_bgb = intercept + slope*sample_log_agb + residual_sd*rng.gauss(0, 1)
        if not -700 < log_bgb < 700:
            raise ValueError("unstable root calibration / simulation")
        sims.append(math.exp(log_bgb) * CARBON_FRACTION)
    sims.sort()
    # Empirical central 95% predictive range, not an AOI-level CI.
    lo = sims[int(math.floor(0.025*(draws-1)))]
    hi = sims[int(math.ceil(0.975*(draws-1)))]
    output.update({
        "conditional_prediction_interval_tc_ha": [lo, hi],
        "uncertainty_status": "conditional_monte_carlo_95_not_validated_for_AOI",
        "source": str(calibration["source"]),
        "applicable_physiognomy": str(calibration["applicable_physiognomy"]),
        "simulations": draws,
        "limitations": "95% conditional predictive range; does not establish empirical AOI coverage or spatial transfer error",
    })
    return output
