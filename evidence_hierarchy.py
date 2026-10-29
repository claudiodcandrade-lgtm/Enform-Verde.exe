"""Conservative hierarchy for published carbon/biomass observations.

Evidence is selected, not manufactured. A descriptive spread or a source CI is
never re-labelled a validated 95% interval for an unobserved target AOI.
Location and fitophysiognomy must be explicitly compatible. Inventory/state
fallback never silently overrides a valid microrregional observation.
"""
from __future__ import annotations

import math
import unicodedata

GEOGRAPHIC_TIERS = ("microrregional", "regional", "estadual", "nacional")
EVIDENCE_LEVELS = ("primary_plots_open", "primary_aggregated", "official_inventory",
                   "peer_reviewed_aggregate")
POOLS = ("agb", "roots", "standing_deadwood", "downed_deadwood", "litter", "soil_0_100")


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return " ".join("".join(x for x in value if not unicodedata.combining(x)).split())


def _number(value, positive=False):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n) or n < 0 or (positive and n == 0):
        return None
    return n


def select_stock_evidence(candidates, *, biome, physiognomy, pool,
                          unit="Mg/ha"):
    """Select one fully traceable applicable estimate.

    Candidate records must declare biome, original fitophysiognomy, pool,
    unit, source/source_url, institution, geographic_tier, evidence_level,
    estimate, uncertainty as a published CI, SD or observed range.
    Non-local candidates additionally require a positive explicit transfer
    uncertainty (same unit), *not* an invented percentage.

    Results include the selected published value and a conservative published
    uncertainty envelope; this is NOT a target-AOI 95% CI, nor scientific
    homologation. No evidence yields an explicit no-estimate decision.
    """
    if pool not in POOLS:
        raise ValueError("unknown carbon/biomass compartment")
    if not _norm(physiognomy) or not _norm(biome):
        return {"available": False, "reason": "bioma/fitofisionomia não informados",
                "rejections": []}
    if not isinstance(candidates, (list, tuple)):
        raise ValueError("candidates must be a sequence")
    options = []
    rejected = []
    for index, row in enumerate(candidates):
        reason = None
        if not isinstance(row, dict):
            reason = "record_not_mapping"
        elif _norm(row.get("biome")) != _norm(biome):
            reason = "different_biome"
        elif _norm(row.get("physiognomy")) != _norm(physiognomy):
            # Never reuse values from the nearest but biologically distinct class.
            reason = "incompatible_physiognomy"
        elif row.get("pool") != pool or row.get("unit") != unit:
            reason = "pool_or_unit_mismatch"
        elif row.get("geographic_tier") not in GEOGRAPHIC_TIERS:
            reason = "unknown_geographic_tier"
        elif row.get("evidence_level") not in EVIDENCE_LEVELS:
            reason = "unverifiable_evidence_level"
        elif not all(str(row.get(f) or "").strip()
                     for f in ("source", "source_url", "institution")):
            reason = "missing_provenance"
        elif row.get("source_url", "").startswith(("https://", "http://")) is False:
            reason = "unresolvable_source_url"
        elif row.get("licensed_for_use") is not True:
            reason = "license_not_verified"
        elif _number(row.get("estimate"), positive=True) is None:
            reason = "missing_stock"
        elif pool == "soil_0_100" and row.get("depth_cm") != [0, 100]:
            reason = "wrong_soil_depth"
        elif pool in ("standing_deadwood", "downed_deadwood") and row.get(
                "pool_measurement") not in ("direct_inventory", "gravimetric"):
            reason = "deadwood_requires_direct_inventory"
        elif pool == "roots" and row.get("pool_measurement") not in (
                "direct_inventory", "validated_allometry"):
            reason = "roots_require_compatible_evidence"
        else:
            center = _number(row["estimate"], positive=True)
            interval = row.get("published_ci95")
            spread = _number(row.get("published_sd"))
            observed_range = row.get("published_range")
            kind = None
            if (isinstance(interval, (list, tuple)) and len(interval) == 2
                    and _number(interval[0]) is not None
                    and _number(interval[1]) is not None
                    and float(interval[0]) <= center <= float(interval[1])):
                lo, hi = map(float, interval)
                kind = "source_published_ci95_not_target_AOI_ci95"
            elif spread is not None and spread > 0:
                lo, hi = max(0.0, center - spread), center + spread
                kind = "source_published_sd_descriptive_only"
            elif (isinstance(observed_range, (list, tuple))
                  and len(observed_range) == 2
                  and _number(observed_range[0]) is not None
                  and _number(observed_range[1]) is not None
                  and float(observed_range[0]) <= center <= float(observed_range[1])):
                lo, hi = map(float, observed_range)
                kind = "source_observed_range_descriptive_only"
            else:
                reason = "no_publishable_uncertainty"
            if reason is None:
                tier = row["geographic_tier"]
                transfer = _number(row.get("transfer_uncertainty"))
                if tier != "microrregional" and (transfer is None or transfer <= 0):
                    reason = "missing_nonlocal_transfer_uncertainty"
                else:
                    # Widen source envelope conservatively without assuming independence.
                    transfer = transfer or 0.0
                    lo, hi = max(0.0, lo - transfer), hi + transfer
                    options.append((GEOGRAPHIC_TIERS.index(tier),
                                    EVIDENCE_LEVELS.index(row["evidence_level"]),
                                    -max(0, int(_number(row.get("independent_units")) or 0)),
                                    index, row, lo, hi, kind, transfer))
        if reason:
            rejected.append({"index": index, "reason": reason,
                             "source": row.get("source") if isinstance(row, dict) else None})
    if not options:
        return {"available": False, "reason": "sem evidência compatível com incerteza publicada e transferência defensável",
                "rejections": rejected}
    _, _, _, index, item, low, high, kind, transfer = sorted(
        options, key=lambda x: x[:4])[0]
    return {
        "available": True, "stock": float(item["estimate"]), "range": [low, high],
        "uncertainty_kind": kind + (
            "; explicit_nonlocal_transfer_envelope" if transfer else ""),
        "is_target_aoi_ci95": False,
        "scientifically_homologated": False,
        "geographic_tier": item["geographic_tier"],
        "evidence_level": item["evidence_level"],
        "source": item["source"], "source_url": item["source_url"],
        "institution": item["institution"], "pool": pool,
        "unit": unit, "biome": biome, "physiognomy": physiognomy,
        "transfer_uncertainty": transfer, "selected_index": index,
        "rejections": rejected,
        "note": "estimativa secundária compatível; intervalo não garante cobertura 95% na AOI",
    }
