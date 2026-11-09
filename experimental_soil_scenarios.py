"""Experimental SOC 0-100 cm stock from *fully documented* physical input bounds.

Finite interval arithmetic gives an outer envelope for declared input ranges.
It does NOT estimate an observed prediction error, independent AOI coverage or
a 95% confidence interval. Incomplete domains, licensing or horizons => N/D.

Reference physical definition: FAO GSP MRV SOC protocol, Annex 4, A4.1.
For each horizon:
    C (tC/ha) = thickness_cm * BD_fine_g_cm3 * fraction_C * 100
                * (1 - coarse_fragment_volume_fraction).
BD_fine is dry fine-earth mass per *fine-earth* volume. Do not apply the
coarse-fragment correction again when input BD already uses total soil volume.
"""
from __future__ import annotations

import math
import re
from urllib.parse import urlparse

from evidence_hierarchy import _norm

DEPTH_BREAKS_CM = (0, 5, 15, 30, 60, 100)
VALID_BIOMES = {"amazonia", "cerrado", "caatinga", "mata atlantica", "pantanal"}
SOIL_SOURCE_PUBLISHERS = {"embrapa solos/pronasolos", "embrapa solos", "pronasolos"}
SOIL_SOURCE_HOSTS = ("embrapa.br", "sgb.gov.br")


def _official_brazilian_soil_source(row):
    """Accept only explicitly identified Brazilian Embrapa/PronaSolos inputs."""
    publisher = _norm(row.get("publisher") or row.get("source_program"))
    product = str(row.get("source_product") or "").strip()
    raw_url = row.get("source_url")
    if publisher not in SOIL_SOURCE_PUBLISHERS or not product:
        return False
    try:
        parsed = urlparse(raw_url if isinstance(raw_url, str) else "")
        host = (parsed.hostname or "").lower().rstrip(".")
        return (parsed.scheme == "https" and not parsed.username and not parsed.password
                and parsed.port in (None, 443)
                and any(host == domain or host.endswith("." + domain)
                        for domain in SOIL_SOURCE_HOSTS))
    except ValueError:
        return False


def _triple(value, field, *, minimum=0.0, maximum=None, exclude_max=False):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{field}: expected [minimum, nominal, maximum]")
    if any(type(v) not in (int, float) for v in value):
        raise ValueError(f"{field}: all bounds must be numeric")
    a, b, c = (float(v) for v in value)
    if not all(math.isfinite(v) for v in (a, b, c)) or not minimum <= a <= b <= c:
        raise ValueError(f"{field}: invalid ordered physical bounds")
    if maximum is not None and (c >= maximum if exclude_max else c > maximum):
        raise ValueError(f"{field}: above physical limit")
    return a, b, c


def soil_0_100_scenario_envelope(horizons, *, biome, physiognomy):
    """Calculate a conservative *scenario* range if all five layers exist.

    Input horizon metadata requires a licensed traceable document URL and
    SHA256 *claim*; the function cannot verify the source bytes and explicitly
    advertises this limitation. Only a separate independent-evidence gate may
    verify sources or promote any model to a scientifically validated status.

    Every horizon must use the same, precisely compatible biome and IBGE
    physiognomy. The bound vector [low, nominal, high] is *not* interpreted as
    statistical quantiles. Inputs must be Brazilian Embrapa Solos/PronaSolos
    data with explicit product provenance; foreign/global soil datasets are rejected.
    """
    def nd(reason):
        return {"available": False, "status": "not_available", "reason": reason,
                "scientifically_homologated": False}
    if _norm(biome) not in VALID_BIOMES or not _norm(physiognomy):
        return nd("biome or IBGE physiognomy not established")
    if not isinstance(horizons, (list, tuple)) or len(horizons) != 5:
        return nd("exactly five complete, non-overlapping 0-100 cm horizons required")
    pieces = []
    sources = set()
    for i, (start, finish) in enumerate(zip(DEPTH_BREAKS_CM[:-1], DEPTH_BREAKS_CM[1:])):
        row = horizons[i]
        if not isinstance(row, dict):
            return nd(f"invalid horizon {i}")
        if (type(row.get("top_cm")) is not int or type(row.get("bottom_cm")) is not int
                or (row["top_cm"], row["bottom_cm"]) != (start, finish)):
            return nd(f"gap, overlap or incompatible depth at horizon {i}")
        if _norm(row.get("biome")) != _norm(biome) or _norm(row.get("physiognomy")) != _norm(physiognomy):
            return nd(f"biome/IBGE physiognomy incompatible at horizon {i}")
        url, digest = row.get("source_url"), row.get("source_sha256")
        if (row.get("licensed_for_use") is not True
                or not _official_brazilian_soil_source(row)
                or not isinstance(digest, str) or not re.fullmatch("[0-9a-fA-F]{64}", digest)):
            return nd(f"source is not an identified Brazilian Embrapa/PronaSolos product, or is unlicensed/untraceable at horizon {i}")
        if row.get("bulk_density_basis") != "fine_earth_volume":
            return nd(f"bulk density basis not demonstrated at horizon {i}")
        try:
            bd = _triple(row.get("bulk_density_g_cm3"), "bulk density", minimum=0.0)
            c = _triple(row.get("organic_carbon_mass_fraction"), "organic carbon fraction",
                        minimum=0.0, maximum=1.0)
            rock = _triple(row.get("coarse_fragment_volume_fraction"), "coarse fragment fraction",
                           minimum=0.0, maximum=1.0, exclude_max=True)
        except ValueError as exc:
            return nd(f"horizon {i}: {exc}")
        if bd[0] <= 0:
            return nd(f"zero/negative bulk density at horizon {i}")
        thickness = finish - start
        low = 100.0 * thickness * bd[0] * c[0] * (1.0 - rock[2])
        point = 100.0 * thickness * bd[1] * c[1] * (1.0 - rock[1])
        high = 100.0 * thickness * bd[2] * c[2] * (1.0 - rock[0])
        if not all(math.isfinite(v) and v >= 0 for v in (low, point, high)):
            return nd(f"non-finite stock at horizon {i}")
        pieces.append((low, point, high))
        sources.add((url, digest.lower()))
    low, point, high = (sum(x[j] for x in pieces) for j in (0, 1, 2))
    if not all(math.isfinite(v) and v >= 0 for v in (low, point, high)):
        return nd("non-finite profile carbon stock")
    if not low <= point <= high:
        return nd("scenario envelope inconsistent")
    return {
        "available": True, "status": "experimental",
        "stock_tc_ha": point,
        "scenario_range_tc_ha": [low, high],
        "stock_tco2e_ha": point * 44.0 / 12.0,
        "scenario_range_tco2e_ha": [low * 44.0 / 12.0, high * 44.0 / 12.0],
        "depth_cm": [0, 100],
        "biome": biome, "physiognomy": physiognomy,
        "source_count": len(sources),
        "source_references": [{"url": u, "sha256_claim": h}
                              for u, h in sorted(sources)],
        "source_bytes_verified": False,
        "uncertainty_kind": "deterministic_physical_input_scenario_envelope_no_coverage",
        "uncertainty_quantified": False,
        "scenario_bounds_quantified": True,
        "is_target_aoi_ci95": False,
        "target_aoi_coverage_validated": False,
        "transfer_error_tc_ha": None,
        "scientifically_homologated": False,
        "method": ("FAO GSP MRV A4.1: sum of five paired horizons 0-100 cm; "
                   "fine-earth BD * carbon mass fraction * fine-earth volume fraction"),
        "limitations": (
            "The declared input bounds are hypotheses/conditional ranges, NOT observed "
            "error or calibrated probability quantiles. Their joint endpoint envelope "
            "is not a CI95 or a 90% prediction interval. Source SHA256 and license "
            "claims require independent byte/license verification; no geographic "
            "transfer, temporal validity or AOI spatial representativeness is proven."
        ),
    }


DEPTH_BREAKS_0_30_CM = (0, 5, 15, 30)

def soil_0_30_scenario_envelope(horizons, *, biome, physiognomy):
    """Calculate a conservative *scenario* range if all three layers exist.

    Input horizon metadata requires a licensed traceable document URL and
    SHA256 *claim*; the function cannot verify the source bytes and explicitly
    advertises this limitation. Only a separate independent-evidence gate may
    verify sources or promote any model to a scientifically validated status.

    Every horizon must use the same, precisely compatible biome and IBGE
    physiognomy. The bound vector [low, nominal, high] is *not* interpreted as
    statistical quantiles. For SoilGrids Q05/Q95 the result is a sensitivity
    envelope, NEVER a 90% or 95% joint predictive interval.
    """
    def nd(reason):
        return {"available": False, "status": "not_available", "reason": reason,
                "scientifically_homologated": False}
    if _norm(biome) not in VALID_BIOMES or not _norm(physiognomy):
        return nd("biome or IBGE physiognomy not established")
    if not isinstance(horizons, (list, tuple)) or len(horizons) != 3:
        return nd("exactly three complete, non-overlapping 0-30 cm horizons required")
    pieces = []
    sources = set()
    for i, (start, finish) in enumerate(zip(DEPTH_BREAKS_0_30_CM[:-1], DEPTH_BREAKS_0_30_CM[1:])):
        row = horizons[i]
        if not isinstance(row, dict):
            return nd(f"invalid horizon {i}")
        if (type(row.get("top_cm")) is not int or type(row.get("bottom_cm")) is not int
                or (row["top_cm"], row["bottom_cm"]) != (start, finish)):
            return nd(f"gap, overlap or incompatible depth at horizon {i}")
        if _norm(row.get("biome")) != _norm(biome) or _norm(row.get("physiognomy")) != _norm(physiognomy):
            return nd(f"biome/IBGE physiognomy incompatible at horizon {i}")
        url, digest = row.get("source_url"), row.get("source_sha256")
        if (row.get("licensed_for_use") is not True
                or not isinstance(url, str) or not url.startswith("https://")
                or not isinstance(digest, str) or not re.fullmatch("[0-9a-fA-F]{64}", digest)):
            return nd(f"unlicensed or untraceable source at horizon {i}")
        if row.get("bulk_density_basis") != "fine_earth_volume":
            return nd(f"bulk density basis not demonstrated at horizon {i}")
        try:
            bd = _triple(row.get("bulk_density_g_cm3"), "bulk density", minimum=0.0)
            c = _triple(row.get("organic_carbon_mass_fraction"), "organic carbon fraction",
                        minimum=0.0, maximum=1.0)
            rock = _triple(row.get("coarse_fragment_volume_fraction"), "coarse fragment fraction",
                           minimum=0.0, maximum=1.0, exclude_max=True)
        except ValueError as exc:
            return nd(f"horizon {i}: {exc}")
        if bd[0] <= 0:
            return nd(f"zero/negative bulk density at horizon {i}")
        thickness = finish - start
        low = 100.0 * thickness * bd[0] * c[0] * (1.0 - rock[2])
        point = 100.0 * thickness * bd[1] * c[1] * (1.0 - rock[1])
        high = 100.0 * thickness * bd[2] * c[2] * (1.0 - rock[0])
        if not all(math.isfinite(v) and v >= 0 for v in (low, point, high)):
            return nd(f"non-finite stock at horizon {i}")
        pieces.append((low, point, high))
        sources.add((url, digest.lower()))
    low, point, high = (sum(x[j] for x in pieces) for j in (0, 1, 2))
    if not all(math.isfinite(v) and v >= 0 for v in (low, point, high)):
        return nd("non-finite profile carbon stock")
    if not low <= point <= high:
        return nd("scenario envelope inconsistent")
    return {
        "available": True, "status": "experimental",
        "stock_tc_ha": point,
        "scenario_range_tc_ha": [low, high],
        "stock_tco2e_ha": point * 44.0 / 12.0,
        "scenario_range_tco2e_ha": [low * 44.0 / 12.0, high * 44.0 / 12.0],
        "depth_cm": [0, 30],
        "biome": biome, "physiognomy": physiognomy,
        "source_count": len(sources),
        "source_references": [{"url": u, "sha256_claim": h}
                              for u, h in sorted(sources)],
        "source_bytes_verified": False,
        "uncertainty_kind": "deterministic_physical_input_scenario_envelope_no_coverage",
        "uncertainty_quantified": False,
        "scenario_bounds_quantified": True,
        "is_target_aoi_ci95": False,
        "target_aoi_coverage_validated": False,
        "transfer_error_tc_ha": None,
        "scientifically_homologated": False,
        "method": ("FAO GSP MRV A4.1: sum of three paired horizons 0-30 cm; "
                   "fine-earth BD * carbon mass fraction * fine-earth volume fraction"),
        "limitations": (
            "The declared input bounds are hypotheses/conditional ranges, NOT observed "
            "error or calibrated probability quantiles. Their joint endpoint envelope "
            "is not a CI95 or a 90% prediction interval. Source SHA256 and license "
            "claims require independent byte/license verification; no geographic "
            "transfer, temporal validity or AOI spatial representativeness is proven."
        ),
    }
