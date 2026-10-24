"""Evidence-source routes for crop masks, SAR monitoring and yield validation.

This module separates available data pathways from evidence already acquired.
It never promotes map products or statistical area yields to pixel-level field
truth. Operational forecast release remains guarded by independent validation.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path


REFERENCE_ROUTES = {
    "yieldsat": {
        "role": "field_truth_and_field_yield",
        "priority": 1,
        "geography": "Brazil and other countries",
        "crops_brazil": {"milho": 118, "soja": 293, "trigo": 140},
        "years": "2017-2024",
        "access": "dataset_form",
        "independent_for_sar": True,
        "limitations": ["Inputs imagery documented as Sentinel-2; acquire Sentinel-1 independently and join by field/season.",
                        "Counts do not establish geographical coverage for every region or crop season.",
                        "Dataset license and access terms must be checked before redistribution or commercial use."],
    },
    "cropharvest": {
        "role": "pretraining_and_external_transfer_test",
        "priority": 2,
        "geography": "global, heterogeneous source datasets",
        "classes": "crop/non-crop plus source-dependent multiclass labels",
        "access": "public_download",
        "independent_for_sar": False,
        "limitations": ["Label sources and crop taxonomies vary; audit Brazil subset and source lineage.",
                        "Not a substitute for Brazilian crop-by-crop, season-specific independent validation."],
    },
    "mapbiomas_agriculture": {
        "role": "training_pseudolabels_and_stratification_only",
        "priority": 3,
        "geography": "Brazil",
        "access": "public_download_or_gee",
        "independent_for_sar": False,
        "limitations": ["Map-derived labels cannot validate models trained or selected against those maps.",
                        "Keep crop season, collection version and map year explicit."],
    },
    "ibge_pam_n9": {
        "role": "regional_yield_outcome",
        "priority": 1,
        "geography": "Brazil, historical N9 microregions",
        "years": "2015-2024 materialized in this project",
        "access": "public_sidra",
        "independent_for_sar": True,
        "limitations": ["Yield labels are regional aggregates, never pixel or field truth.",
                        "Boundary vintage, crop season, suppressions and unit conversion must be audited."],
    },
    "field_boundaries": {
        "role": "geometry_and_sampling_frame_only",
        "priority": 4,
        "geography": "dataset dependent",
        "access": "public_or_research_access",
        "independent_for_sar": False,
        "limitations": ["A field polygon without an authoritative crop label does not establish crop identity."],
    },
}


def plan_evidence_routes(*, task: str, crop: str | None = None,
                         available_sources=()) -> dict:
    """Return ordered alternatives and explicit release blockers for a task."""
    task = str(task).strip().casefold()
    available = {str(x).strip().casefold() for x in available_sources}
    if task not in {"crop_mask", "yield_linkage", "phenology", "yield_forecast"}:
        raise ValueError("task must be crop_mask, yield_linkage, phenology or yield_forecast")
    if task == "crop_mask":
        order = ["yieldsat", "cropharvest", "mapbiomas_agriculture", "field_boundaries"]
    elif task == "yield_linkage":
        order = ["ibge_pam_n9", "yieldsat", "cropharvest"]
    elif task == "phenology":
        order = ["yieldsat", "cropharvest", "mapbiomas_agriculture"]
    else:
        order = ["yieldsat", "ibge_pam_n9", "cropharvest"]
    routes = []
    for name in order:
        route = dict(REFERENCE_ROUTES[name])
        route["source_id"] = name
        route["source_available_in_run"] = name in available
        route["eligible_as_independent_validation"] = bool(route["independent_for_sar"] and name in available)
        routes.append(route)
    blockers = []
    if task in {"crop_mask", "phenology", "yield_forecast"} and not any(
            r["source_available_in_run"] and r["independent_for_sar"] for r in routes):
        blockers.append("Rótulo de campo independente ainda não foi fornecido ou baixado")
    if crop:
        supported = {k for k, n in REFERENCE_ROUTES["yieldsat"]["crops_brazil"].items() if n > 0}
        if str(crop).casefold() not in supported:
            blockers.append("YieldSAT não lista referência brasileira para esta cultura; exigir fonte independente específica")
    blockers += ["Descoberta SAR não comprova extração de pixels na área válida da cultura",
                 "Previsão requer validação temporal e espacial externa; alternativas de dados não substituem o teste"]
    return {"task": task, "crop": crop, "ordered_routes": routes,
            "release_ready": False, "blockers": blockers,
            "policy": "A rota pode orientar aquisição e experimento; não concede aprovação científica automaticamente."}


def build_pam_sar_panel(pam_path, sar_path, weather_path=None, output_path=None) -> dict:
    """Join observed PAM N9 yield with crop-masked SAR aggregates.

    SAR CSV requires product_key, territory_code, year, spatial_block,
    mask_validation_status, mask_model_sha256, crop_mask_source,
    latest_acquisition_utc, age_days, scenes_in_window, crop_phase,
    freshness_validation_status, SAR source URL, three independent SAR
    validation flags, and features prefixed ``sar_``. Weather CSV requires the
    PAM join keys, source and source URL, and numeric climate_/weather_ fields.
    This checks the input contract, not the truthfulness of external reports.
    """
    if weather_path is None:
        raise ValueError("independent climate panel required to assemble a model-ready panel")
    required = {"product_key", "territory_code", "year", "spatial_block", "mask_validation_status",
                "mask_model_sha256", "crop_mask_source", "latest_acquisition_utc",
                "age_days", "scenes_in_window", "crop_phase", "freshness_validation_status",
                "sar_source_url", "sar_crop_validated", "sar_vigor_validated",
                "sar_stress_validated"}
    def open_text(path):
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="") if str(path).endswith(".gz") else open(path, encoding="utf-8-sig", newline="")
    with open_text(sar_path) as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("SAR aggregate CSV missing: " + ", ".join(sorted(required-set(reader.fieldnames or []))))
        features = [c for c in reader.fieldnames if c.startswith("sar_")]
        if not features:
            raise ValueError("SAR aggregate CSV needs numeric sar_* feature columns")
        sar_rows = list(reader)
    if not sar_rows:
        raise ValueError("No SAR crop-masked regional aggregates supplied")
    # Require a one-to-one crop × N9 × year key and a genuinely reviewed
    # independent validation marker before building model-ready records.
    keys, eligible_sar = set(), {}
    for row in sar_rows:
        key = (row["product_key"], row["territory_code"], row["year"])
        if key in keys:
            raise ValueError("duplicate crop × N9 × year SAR aggregate: " + repr(key))
        keys.add(key)
        if row["mask_validation_status"] != "INDEPENDENT_VALIDATION_APPROVED":
            continue
        if row["freshness_validation_status"] != "CROP_PHASE_FRESHNESS_CALIBRATED":
            continue
        if not row["mask_model_sha256"] or not row["crop_mask_source"]:
            raise ValueError("approved mask requires model SHA-256 and reference source")
        if not row["spatial_block"].strip() or not row["sar_source_url"].strip():
            raise ValueError("approved SAR aggregate requires spatial block and source URL")
        eligible_sar[key] = row
    pam = {}
    pam_sha = hashlib.sha256(Path(pam_path).read_bytes()).hexdigest()
    with open_text(pam_path) as f:
        for row in csv.DictReader(f):
            if row.get("variable_code") != "112" or not row.get("value_numeric"):
                continue
            key = (row["product_key"], row["territory_code"], row["year"])
            if key in pam:
                raise ValueError("duplicate PAM yield key: " + repr(key))
            pam[key] = row
    weather = {}
    with open_text(weather_path) as f:
        reader = csv.DictReader(f)
        weather_required = {"product_key", "territory_code", "year", "weather_source", "weather_source_url"}
        if not reader.fieldnames or not weather_required.issubset(reader.fieldnames):
            raise ValueError("weather CSV missing: " + ", ".join(sorted(weather_required-set(reader.fieldnames or []))))
        climate_features = [c for c in reader.fieldnames if c.startswith(("climate_", "weather_"))
                            and c not in {"weather_source", "weather_source_url"}]
        if not climate_features:
            raise ValueError("weather CSV needs numeric climate_* or weather_* features")
        for row in reader:
            key = (row["product_key"], row["territory_code"], row["year"])
            if key in weather:
                raise ValueError("duplicate weather key: " + repr(key))
            if not row["weather_source"].strip() or not row["weather_source_url"].strip():
                raise ValueError("weather source and URL are mandatory")
            weather[key] = row
    output = []
    for key, sar in eligible_sar.items():
        label = pam.get(key)
        wx = weather.get(key)
        if not label or not wx:
            continue
        record = {"crop": key[0], "municipality_code": key[1], "territory_code": key[1],
                  "spatial_block": sar["spatial_block"], "season_year": int(key[2]),
                  "yield_t_ha": float(label["value_numeric"]) / 1000.0,
                  "yield_source_url": label.get("source_url") or label.get("source_url", ""),
                  "yield_license": "IBGE PAM; confirm terms before redistribution",
                  "sar_source_url": sar.get("sar_source_url", ""),
                  "sar_mask_sha256": sar["mask_model_sha256"],
                  "sar_mask_reference": sar["crop_mask_source"],
                  "sar_latest_acquisition_utc": sar["latest_acquisition_utc"],
                  "sar_age_days": float(sar["age_days"]),
                  "sar_scenes_in_window": int(sar["scenes_in_window"]),
                  "sar_crop_phase": sar["crop_phase"],
                  "sar_independent_mask_approved": True,
                  "sar_crop_validated": sar["sar_crop_validated"],
                  "sar_vigor_validated": sar["sar_vigor_validated"],
                  "sar_stress_validated": sar["sar_stress_validated"],
                  "weather_source": wx["weather_source"],
                  "weather_source_url": wx["weather_source_url"],
                  "pam_source_sha256": pam_sha}
        for col in features:
            try:
                record[col] = float(sar[col])
            except (TypeError, ValueError):
                record[col] = None
        for col in climate_features:
            try:
                record[col] = float(wx[col])
            except (TypeError, ValueError):
                record[col] = None
        output.append(record)
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(output[0]) if output else [])
            if output:
                writer.writeheader(); writer.writerows(output)
    return {"status": "panel_assembled" if output else "no_eligible_overlap",
            "rows": len(output), "pam_rows": len(pam),
            "sar_rows": len(sar_rows), "approved_mask_rows": len(eligible_sar),
            "pam_sha256": pam_sha,
            "output_path": str(output_path) if output_path else None,
            "warning": "Join em escala N9/safra; não é validação pixel/field. Auditoria independente do arquivo de validação permanece obrigatória."}
