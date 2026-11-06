"""Recent Sentinel-1 SAR pixel observation over a crop-map sampling point.

The primary classification priority is SAR.  This module is NOT a classifier:
it proves which recent radar pixels were read, and provides dated VV/VH
measurements for future fit-for-purpose crop classifiers.  MapBiomas historical
classes only choose a reference sampling location, not the output label.

Fail closed on failed network or image reads, without inventing a current
crop, a confidence score or wall-to-wall current field area.  SAS tokens are
never persisted in the result.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite


def probe_recent_sar_crop_pixels(aoi, crop_polygons, *, now=None, search=None,
                                 extract=None, token_fn=None, max_age_days=30,
                                 lookback_days=90, max_scenes=2):
    from shapely.geometry import mapping
    from carbon_compartments import aoi_to_wgs84
    from sentinel1_mpc import (search_sentinel1_rtc, extract_cog_point,
                               get_runtime_sas_token)

    stamp = now or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        raise ValueError("Referência temporal SAR deve conter fuso")
    if not (1 <= max_age_days <= lookback_days <= 180 and 1 <= max_scenes <= 4):
        raise ValueError("Janela/cota SAR inválida")
    out = {
        "status": "SAR_NAO_VERIFICADO", "priority": "SAR_RECENTE",
        "crop_identified": False, "crop_classification": "N/D",
        "sampling": "um ponto interior de máscara cartográfica histórica",
        "max_age_days": max_age_days, "lookback_days": lookback_days,
        "caveat": ("Observações Sentinel-1 VV/VH em um ponto não identificam "
                   "a cultura, não são classificação por talhão nem provam "
                   "área plantada na safra atual."),
    }
    try:
        field = aoi_to_wgs84(crop_polygons)
        if field.empty or not field.geometry.notna().any():
            out["reason"] = "sem interseção agrícola cartográfica para amostragem"
            return out
        p = field.geometry.union_all().representative_point()
        lon, lat = float(p.x), float(p.y)
        if not (isfinite(lon) and isfinite(lat)):
            raise ValueError("coordenadas não finitas")
        bounds = aoi_to_wgs84(aoi).geometry.union_all()
        if not bounds.covers(p):
            out["reason"] = "ponto de amostragem fora da AOI"
            return out
        out["sample_wgs84"] = [round(lon, 7), round(lat, 7)]
        search = search or search_sentinel1_rtc
        found = search(mapping(bounds),
                       start_utc=stamp - timedelta(days=lookback_days),
                       end_utc=stamp)
        scenes = []
        for scene in found.get("scenes", []):
            try:
                acquisition = datetime.fromisoformat(
                    str(scene["acquisition_utc"]).replace("Z", "+00:00"))
                if acquisition.tzinfo is None:
                    continue
                acquisition = acquisition.astimezone(timezone.utc)
                assets = scene.get("assets") or {}
                polarizations = {str(x).upper() for x in
                                 (scene.get("polarizations") or [])}
                if (acquisition <= stamp and
                        (stamp - acquisition).total_seconds() <= max_age_days * 86400
                        and "vv" in assets and "vh" in assets
                        and (not polarizations or {"VV", "VH"} <= polarizations)):
                    scenes.append((acquisition, scene))
            except (KeyError, TypeError, ValueError):
                continue
        scenes.sort(key=lambda item: item[0], reverse=True)
        if not scenes:
            out["reason"] = "nenhuma cena Sentinel-1 VV/VH recente compatível"
            return out
        extractor = extract or extract_cog_point
        token_getter = token_fn or get_runtime_sas_token
        token = token_getter()
        samples = []
        for acquisition, scene in scenes[:max_scenes]:
            readings = {}
            try:
                for band in ("vv", "vh"):
                    raw = extractor(
                        scene["assets"][band]["href"], lon=lon, lat=lat,
                        polarization=band, token=token, window_size=3)
                    value = float(raw["median_native"])
                    if raw.get("status") != "pixels_read" or not isfinite(value) or value < 0:
                        raise ValueError("pixel RTC inválido: " + band)
                    readings[band.upper()] = {
                        "median_rtc_native": value,
                        "valid_pixels": raw.get("valid_pixels"),
                        "unit": raw.get("unit")}
            except (UnicodeError, OSError, ValueError, RuntimeError, KeyError,
                    TypeError) as exc:
                samples.append({
                    "scene_id": str(scene.get("id", "")),
                    "status": "PIXELS_INDISPONIVEIS",
                    "reason": type(exc).__name__ + ": " + str(exc)[:160],
                })
                continue
            samples.append({
                "scene_id": str(scene.get("id", "")),
                "status": "PIXELS_LIDOS", "acquisition_utc": acquisition.isoformat(),
                "orbit_state": scene.get("orbit_state"),
                "relative_orbit": scene.get("relative_orbit"),
                "measurements": readings,
            })
        out["scenes"] = samples
        valid = [item for item in samples if item["status"] == "PIXELS_LIDOS"]
        if valid:
            out["status"] = "SAR_PIXELS_RECENTES_PROCESSADOS"
            out["latest_acquisition_utc"] = valid[0]["acquisition_utc"]
            out["source"] = "Sentinel-1 RTC / Microsoft Planetary Computer"
        else:
            out["reason"] = "cenas catalogadas, mas VV/VH não puderam ser lidos"
        return out
    except (UnicodeError, OSError, ValueError, RuntimeError, KeyError,
            TypeError) as exc:
        out["reason"] = type(exc).__name__ + ": " + str(exc)[:190]
        return out
