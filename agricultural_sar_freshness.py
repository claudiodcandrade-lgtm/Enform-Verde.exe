"""Conservative acquisition freshness assessment for agricultural monitoring.

This module evaluates supplied catalog manifests; it does not pretend a
catalog response proves scene download, processing or classification.
"""
from datetime import datetime, timezone

def parse_utc(value):
    if not value:
        return None
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except ValueError:
        return None

def freshness_report(manifests, *, crop=None, region=None, phenological_phase=None,
                     now=None, max_age_days=None, series_window_days=None,
                     min_scenes=None, threshold_source=None):
    """Assess acquisition freshness under explicit crop/phase-specific criteria.

    No global age or scene-count defaults are scientifically defensible for all
    crops and orbital schedules. Missing criteria therefore fail closed.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    criteria_defined = all((crop, region, phenological_phase, threshold_source)) and all(
        value is not None for value in (max_age_days, series_window_days, min_scenes))
    if criteria_defined and (max_age_days <= 0 or series_window_days <= 0 or min_scenes < 1):
        raise ValueError("Invalid crop/phase-specific freshness criteria")
    records = {}
    for manifest in manifests:
        for scene in manifest.get("scenes", []):
            acquired = parse_utc(scene.get("acquisition_utc"))
            ident = scene.get("id")
            if ident and acquired and acquired <= now:
                records[ident] = {"id": ident, "acquisition_utc": acquired,
                                  "source": scene.get("source"),
                                  "polarizations": scene.get("polarizations"),
                                  "relative_orbit": scene.get("relative_orbit")}
    scenes = sorted(records.values(), key=lambda s: s["acquisition_utc"], reverse=True)
    latest = scenes[0]["acquisition_utc"] if scenes else None
    age = (now - latest).total_seconds() / 86400 if latest else None
    recent = ([s for s in scenes if (now - s["acquisition_utc"]).total_seconds()
               <= series_window_days * 86400] if criteria_defined else [])
    status = ("sem_aquisicoes" if not scenes else
              "criterios_temporais_nao_definidos" if not criteria_defined else
              "desatualizado" if age > max_age_days else
              "serie_insuficiente" if len(recent) < min_scenes else "cenas_recentes_identificadas")
    return {"status": status, "latest_acquisition_utc": latest.isoformat() if latest else None,
            "age_days": round(age, 2) if age is not None else None,
            "scenes_in_series_window": len(recent), "total_discovered": len(scenes),
            "crop": crop, "region": region, "phenological_phase": phenological_phase,
            "freshness_criteria": {"defined": criteria_defined,
                                   "max_age_days": max_age_days,
                                   "series_window_days": series_window_days,
                                   "minimum_scenes": min_scenes,
                                   "source": threshold_source},
            "scene_ids": [s["id"] for s in scenes],
            "warning": "Timestamp recente não comprova pixels válidos, cultura classificada ou vigor fenológico validado"}

def land_use_diagnostic_status(*, freshness, classifier_validated=False,
                               imagery_processed=False, native_mask_verified=False):
    """Never call land use current unless imagery and validated model actually ran."""
    if not imagery_processed:
        return "aguardando_processamento"
    if not classifier_validated:
        return "sem_classificador_validado"
    if not native_mask_verified:
        return "mascara_nativa_nao_verificada"
    if (freshness.get("status") != "cenas_recentes_identificadas" or
            not freshness.get("freshness_criteria", {}).get("defined")):
        return "diagnostico_com_restricao_temporal"
    return "diagnostico_atual_com_evidencias"
