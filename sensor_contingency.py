"""Explicit sensor priority and contingency policy for Enform Verde.

Alternative sensors may replace a Sentinel-1-derived measurement only after an
independent model validation for that sensor, target, resolution and domain.
Otherwise they are contextual evidence and the requested SAR result abstains.
"""
from __future__ import annotations

POLICY_VERSION = "1.0"
SENSOR_ROUTES = (
    {
        "priority": 1, "sensor": "Sentinel-1",
        "purpose": "SAR time series, VV/VH, current radar change and structure",
        "primary_route": "Microsoft Planetary Computer STAC sentinel-1-rtc + fresh in-memory SAS + HTTPS COG window reads",
        "alternate_routes": [
            "Copernicus Data Space Sentinel-1 GRD/SLC via OAuth; requires configured credentials and RTC/GRD preprocessing",
            "Alaska Satellite Facility DAAC Sentinel-1 via Earthdata; requires configured credentials and RTC preprocessing",
        ],
        "substitutable": False,
        "gate": "actual VV/VH pixels, acquisition IDs/dates, orbit/polarization consistency, valid AOI coverage and read QA",
    },
    {
        "priority": 2, "sensor": "Sentinel-2",
        "purpose": "optical reflectance, cloud-screened vegetation indices, visual preview",
        "primary_route": "Planetary Computer STAC and EarthSearch STAC; retry multiple L2A scenes and validate RGB/band reads",
        "alternate_routes": ["NASA GIBS or Esri imagery for display only"],
        "substitutable": False,
        "gate": "surface reflectance, cloud/shadow mask, acquisition date, valid pixel fraction and sensor-specific validated model",
    },
    {
        "priority": 3, "sensor": "Landsat 8/9",
        "purpose": "optical temporal continuity when Sentinel-2 gaps/clouds prevent analysis",
        "primary_route": "USGS Landsat Collection 2 Level-2 via public STAC/COG provider",
        "alternate_routes": [],
        "substitutable": False,
        "gate": "surface reflectance scaling, QA_PIXEL cloud/shadow/snow mask, harmonization and independent Landsat validation",
    },
    {
        "priority": 4, "sensor": "GEDI / ESA Biomass",
        "purpose": "height/biomass references and calibration or independent checks",
        "primary_route": "official mission products and documented distribution endpoints",
        "alternate_routes": [],
        "substitutable": False,
        "gate": "footprint/product support, acquisition date, quality flags and compatible independent plots",
    },
    {
        "priority": 5, "sensor": "MODIS / VIIRS / GPM",
        "purpose": "regional phenology or climate context at coarse resolution",
        "primary_route": "official NASA data services",
        "alternate_routes": ["NASA POWER or CPTEC/INPE for their defined climate products"],
        "substitutable": False,
        "gate": "never infer field-scale crop identity, vigor or yield from coarse pixels",
    },
)


def fallback_plan(*, target="crop_monitoring"):
    """Return auditable order and non-substitution rules for a requested analysis."""
    return {
        "policy_version": POLICY_VERSION,
        "target": target,
        "priority_sensor": "Sentinel-1",
        "routes": [dict(row) for row in SENSOR_ROUTES],
        "status_vocabulary": {
            "N/D_DADOS": "catalogue has no suitable scenes or valid coverage after complete search",
            "ERRO_TECNICO": "catalogue/credentials/network/COG/decoder/reprojection/analysis failed; retry or repair, never report as data absence",
            "N/D_VALIDACAO": "pixels exist, but no compatible independently validated classifier/model supports the requested result",
            "PROCESSADO_EXPERIMENTAL": "measurements were computed, but are not a validated class or field-level estimate",
        },
        "rules": [
            "Sentinel-1 remains the first acquisition and analysis route.",
            "When Sentinel-1 is unavailable, try the stated optical/context routes only for their supported measurements.",
            "Do not relabel an optical or coarse-resolution result as SAR.",
            "Do not calculate property crop area, vigor, phytosanitary state or yield from a substitute sensor without an independent sensor-specific validation gate.",
            "Distinguish N/D_DADOS, ERRO_TECNICO and N/D_VALIDACAO in reports and audit JSON.",
            "Record provider, collection, scene IDs, UTC dates, pixel coverage, masks, failures, model version and validation domain.",
        ],
    }
