"""Auditable non-Sentinel SAR fallback for the recent land-cover screen.

This module reads pixels from ASF NISAR L2 GCOV or georeferenced ALOS L-band
products when no usable recent Sentinel-1 series exists. It reports sensor
measurements only; it never labels them as Sentinel-1 VV/VH or land-cover
classes. Other missions remain explicitly unconfigured until their official
catalogue, license and pixel reader are integrated.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

RECENT_ALTERNATIVE_DAYS = 30
ASF_ENABLED_LBAND = ("NISAR L2 GCOV", "ALOS PALSAR")
UNCONFIGURED_ROUTES = (
    "NISAR S-band Bhoonidhi/ISRO",
    "SAOCOM-1A/1B CONAE",
    "RCM/EODMS",
    "NovaSAR-1/Bhoonidhi",
    "EOS-04/Bhoonidhi",
    "ALOS-4/JAXA",
    "RADARSAT-2",
    "TerraSAR-X/TanDEM-X/PAZ",
    "COSMO-SkyMed",
    "ICEYE",
    "Capella",
    "Umbra",
    "Synspective StriX",
)

def _safe_error(exc):
    text = str(exc)
    text = re.sub(r"https?://\S+", "[URL_REDACTED]", text)
    text = re.sub(r"(?i)(token|password|authorization|sig|se|sv|sp|st)=[^&\s]+",
                  r"\1=[REDACTED]", text)
    return (type(exc).__name__ + ": " + text)[:240]

def _acquired(item):
    try:
        from sar_acquisition_time import acquisition_utc
        return acquisition_utc(item)
    except Exception:
        return None

def _default_discover(aoi):
    from sar_pipeline import discover_asf
    return discover_asf(aoi, limit=100)

def _default_session():
    from sar_pipeline import _earthaccess_requests_session
    return _earthaccess_requests_session()

def _safe_filename(url, scene_id):
    name = Path(urlsplit(str(url)).path).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(scene_id)).strip("._")
    return name or "sar_scene"

def _download(session, url, target):
    import requests
    target = Path(target)
    if target.is_file() and target.stat().st_size > 0:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.unlink(missing_ok=True)
    with session.get(url, stream=True, timeout=(20, 600), allow_redirects=True) as response:
        response.raise_for_status()
        with partial.open("wb") as output:
            for chunk in response.iter_content(8 * 1024 * 1024):
                if chunk:
                    output.write(chunk)
    if not partial.is_file() or partial.stat().st_size == 0:
        partial.unlink(missing_ok=True)
        raise OSError("Download completed without bytes")
    os.replace(partial, target)
    return target

def _process_pixels(aoi, item, local_path, work_dir):
    """Use existing, sensor-specific pixel readers; return statistics and paths."""
    scene_text = (str(item.get("id", "")) + " " +
                  str(item.get("properties", {}))).upper()
    if "NISAR" in scene_text:
        from sar_pipeline import process_nisar_gcov
        summary = process_nisar_gcov(aoi, local_path)
        return {
            "sensor": "NISAR",
            "band": "L",
            "product": summary.get("product", "NISAR L2 GCOV"),
            "polarimetric_terms": summary.get("terms", {}),
            "features": summary.get("features", {}),
            "paths": [str(local_path)],
            "pixel_reader": "sar_pipeline.process_nisar_gcov",
        }
    from lband_preprocess import preprocess_lband
    from sar_pipeline import _zonal
    prepared = preprocess_lband(local_path, work_dir / ("alos_" + Path(local_path).stem))
    rasters = [Path(x) for x in prepared.get("rasters", [])]
    if not rasters:
        raise ValueError("ALOS product not ready for pixel reading: " +
                         str(prepared.get("status", "unknown")))
    stats = []
    clipped_paths = []
    for index, raster in enumerate(rasters):
        row = _zonal(aoi, str(raster))
        stats.append({"path": str(raster), **row})
        clipped_paths.append(str(raster))
    return {
        "sensor": "ALOS PALSAR",
        "band": "L",
        "product": prepared.get("kind", prepared.get("status", "ALOS georeferenced product")),
        "rasters": stats,
        "paths": clipped_paths,
        "pixel_reader": "sar_pipeline._zonal",
        "preprocessing": prepared.get("steps", []),
    }

def run_alternative_radar_screen(
    aoi,
    output_dir,
    *,
    now=None,
    max_age_days=RECENT_ALTERNATIVE_DAYS,
    discover=None,
    session_factory=None,
    downloader=None,
    pixel_processor=None,
):
    """Search and read a recent NISAR/ALOS pixel product after Sentinel-1 fails.

    ASF catalogue access is independent of Earthdata file-download credentials.
    A missing candidate from these two routes is not called national data absence:
    the other listed mission routes are not yet configured in this adapter.
    """
    ref = now or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    ref = ref.astimezone(timezone.utc)
    root = Path(output_dir).expanduser().resolve() / "alternative_sar"
    cache = root / "cache"
    root.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "ERRO_TECNICO",
        "native_confirmed": False,
        "crop_confirmed": False,
        "scientific_status": "N/D_VALIDACAO",
        "classification_status": "N/D_VALIDACAO",
        "sensor_search_scope": list(ASF_ENABLED_LBAND),
        "routes_not_configured": list(UNCONFIGURED_ROUTES),
        "global_search_complete": False,
        "max_age_days": int(max_age_days),
        "queried_at_utc": ref.isoformat(),
    }
    try:
        groups = (discover or _default_discover)(aoi)
    except Exception as exc:
        result.update({"status": "ERRO_TECNICO", "reason": "ASF_DISCOVERY_FAILED",
                       "error": _safe_error(exc)})
        return result

    candidates = []
    group_errors = []
    for group in groups or []:
        label = str(group.get("dataset", ""))
        if label not in ASF_ENABLED_LBAND:
            continue
        if group.get("error"):
            group_errors.append({"dataset": label, "error": _safe_error(
                RuntimeError(group.get("error")))})
        for item in group.get("items", []) or []:
            acquired = _acquired(item)
            url = item.get("download_url")
            if acquired is None or not url:
                continue
            acquired = acquired.astimezone(timezone.utc)
            age = (ref - acquired).total_seconds()
            if 0 <= age <= float(max_age_days) * 86400:
                priority = ASF_ENABLED_LBAND.index(label)
                candidates.append((priority, acquired, label, item))
    candidates.sort(key=lambda row: (row[0], -row[1].timestamp()))
    result["catalog_candidates_recent"] = len(candidates)
    result["provider_diagnostics"] = group_errors

    if not candidates:
        result.update({
            "status": "ERRO_TECNICO",
            "reason": "ALT_RADAR_SEARCH_INCOMPLETE",
            "detail": "NISAR L/ALOS ASF has no usable recent candidate and other global radar routes are not configured; do not report N/D_DADOS.",
        })
        _write_manifest(root, result)
        return result

    try:
        session, auth = (session_factory or _default_session)()
    except Exception as exc:
        session, auth = None, {"available": False, "reason": _safe_error(exc)}
    result["earthdata_auth"] = {
        "available": bool(session is not None),
        "reason": str((auth or {}).get("reason", ""))[:160],
    }
    if session is None:
        result.update({"status": "ACESSO_RESTRITO",
                       "reason": "EARTHDATA_LOGIN_REQUIRED_FOR_PIXEL_DOWNLOAD"})
        _write_manifest(root, result)
        return result

    download_fn = downloader or _download
    processor = pixel_processor or _process_pixels
    errors = []
    for _, acquired, label, item in candidates[:8]:
        scene_id = str(item.get("id") or "unknown")
        url = item.get("download_url")
        target = cache / _safe_filename(url, scene_id)
        try:
            local_path = download_fn(session, url, target)
            pixel_result = processor(aoi, item, local_path, root)
            if not pixel_result:
                raise ValueError("Pixel processor returned no result")
            result.update({
                "status": "ALTERNATIVE_RADAR_PIXELS_PROCESSED",
                "reason": None,
                "sensor": pixel_result.get("sensor", label),
                "band": pixel_result.get("band", "L"),
                "product": pixel_result.get("product", label),
                "scene_id": scene_id,
                "acquisition_utc": acquired.isoformat(),
                "pixel_result": pixel_result,
                "failed_candidates": errors,
                "manifest_path": str(root / "radar_alternative_manifest.json"),
                "message": "Real alternative-sensor pixels were read. They are not Sentinel-1 VV/VH; current native/crop classes remain unvalidated.",
            })
            _write_manifest(root, result)
            return result
        except Exception as exc:
            errors.append({"scene_id": scene_id, "dataset": label,
                           "acquisition_utc": acquired.isoformat(),
                           "error": _safe_error(exc)})
    result.update({"status": "ERRO_TECNICO",
                   "reason": "ALL_RECENT_ALT_RADAR_PIXEL_READS_FAILED",
                   "failed_candidates": errors})
    _write_manifest(root, result)
    return result

def _write_manifest(root, result):
    path = Path(root) / "radar_alternative_manifest.json"
    safe = dict(result)
    safe.pop("manifest_path", None)
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
