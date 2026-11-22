"""Measured error of ecological/geographic transfer from independent field holdouts.

Not a substitute for the independent scientific release gate. This computes
measurable transfer diagnostics for compatible native formations and pools,
without claiming an unvalidated confidence interval for a new AOI.

Spatial groups represent independent field sites/locations (not pixels or
pseudo-plots). Each observation must be from an independently held-out
measurement with traceable source and usable rights.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict


def _valid_stock(value):
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value)) and float(value) >= 0.0
    except (ValueError, TypeError):
        return False


def measured_transfer_error(observations, *, biome, physiognomy, pool,
                            units, alpha=0.05):
    """Assess independently observed model-transfer errors by spatial group.

    Assumes the point estimator has been frozen BEFORE these validation
    observations were collected/selected. All records must have matching
    biome, fitophysiognomy, pool and units and must be independent of training.

    For >= 5 groups report a measured descriptive envelope (maximum absolute
    group-held-out error). For >= ceil(1/alpha)-1 groups, also report the
    split-conformal order-statistic threshold, CONDITIONAL on independent,
    exchangeable geographic groups; this is not a guaranteed target-AOI CI
    under geographic shift. No uncertain input is converted to zero.
    """
    if not isinstance(observations, (list, tuple)) or not observations:
        return {"available": False, "reason": "no independent field residuals"}
    if not (isinstance(alpha, (int, float)) and not isinstance(alpha, bool)
            and math.isfinite(alpha) and 0 < alpha < 1):
        raise ValueError("alpha must be strictly between zero and one")
    from evidence_hierarchy import _norm
    seen = set()
    grouped = defaultdict(list)
    sources = set()
    for i, row in enumerate(observations):
        if not isinstance(row, dict):
            return {"available": False, "reason": f"invalid record {i}"}
        if (_norm(row.get("biome")) != _norm(biome)
                or _norm(row.get("physiognomy")) != _norm(physiognomy)
                or row.get("pool") != pool or row.get("unit") != units):
            return {"available": False, "reason": f"incompatible field evidence {i}"}
        if (row.get("evidence_type") != "independent_real_data"
                or row.get("training_overlap") is not False
                or row.get("heldout_from_model_selection") is not True):
            return {"available": False, "reason": f"independence not established {i}"}
        source = row.get("source_url")
        digest = row.get("dataset_sha256")
        if (not isinstance(source, str) or not source.startswith("https://")
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)
                or row.get("licensed_for_use") is not True):
            return {"available": False, "reason": f"source/license/hash not established {i}"}
        group = row.get("spatial_group")
        unit = row.get("observation_id")
        if not isinstance(group, str) or not group.strip() or not isinstance(unit, str) or not unit.strip():
            return {"available": False, "reason": f"missing field/group ID {i}"}
        key = (group, unit)
        if key in seen:
            return {"available": False, "reason": f"duplicate held-out observation {i}"}
        seen.add(key)
        observed, predicted = row.get("observed"), row.get("predicted")
        if not _valid_stock(observed) or not _valid_stock(predicted):
            return {"available": False, "reason": f"invalid independent measurements {i}"}
        grouped[group].append(float(predicted) - float(observed))
        sources.add((source, digest))
    n = len(grouped)
    if n < 5:
        return {"available": False, "reason": "fewer than five independent spatial groups",
                "n_groups": n}
    # A whole validation site is one unit: preserve its worst absolute error.
    scores = sorted(max(abs(err) for err in values) for values in grouped.values())
    residuals = [v for rows in grouped.values() for v in rows]
    bias = sum(residuals) / len(residuals)
    rmse = math.sqrt(sum(v*v for v in residuals) / len(residuals))
    mae = sum(abs(v) for v in residuals) / len(residuals)
    rank = math.ceil((n + 1) * (1 - alpha))
    finite_conformal = rank <= n
    bound = scores[rank - 1] if finite_conformal else scores[-1]
    return {
        "available": True, "n_independent_groups": n,
        "n_observations": len(residuals), "n_sources": len(sources),
        "mae": mae, "rmse": rmse, "bias": bias,
        "observed_max_group_absolute_error": scores[-1],
        "uncertainty_bound": bound,
        "uncertainty_kind": (
            "split_conformal_spatial_group_candidate_exchangeability_unverified"
            if finite_conformal else
            "heldout_group_max_absolute_residual_descriptive_only"),
        "conformal_nominal_level": (1.0 - alpha if finite_conformal else None),
        "target_aoi_coverage_validated": False,
        "is_target_aoi_ci95": False,
        "spatial_exchangeability_assumed_not_demonstrated": True,
        "calibration_independent_groups": sorted(grouped),
        "limitations": (
            "Requires frozen model, fully separate field groups, representative "
            "geography/fitofisionomia and external coverage evaluation. A nominal "
            "conformal level applies only under group exchangeability; neither "
            "group leave-out diagnostics nor observed error range proves spatial "
            "transfer coverage on the target AOI."
        ),
    }
