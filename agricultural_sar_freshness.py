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

def freshness_report(manifests, *, now=None, max_age_days=12, min_scenes=3):
    """Assess actual acquisition dates and temporal sampling, not processing dates."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if max_age_days <= 0 or min_scenes < 1:
        raise ValueError("Invalid monitoring thresholds")
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
    recent = [s for s in scenes if (now - s["acquisition_utc"]).total_seconds() <= 90 * 86400]
    status = ("sem_aquisicoes" if not scenes else
              "desatualizado" if age > max_age_days else
              "serie_insuficiente" if len(recent) < min_scenes else "cenas_recentes_identificadas")
    return {"status": status, "latest_acquisition_utc": latest.isoformat() if latest else None,
            "age_days": round(age, 2) if age is not None else None,
            "scenes_last_90_days": len(recent), "total_discovered": len(scenes),
            "scene_ids": [s["id"] for s in scenes],
            "warning": "Descoberta de cenas não comprova classificação fenológica nem diagnóstico atualizado"}

def land_use_diagnostic_status(*, freshness, classifier_validated=False,
                               imagery_processed=False, native_mask_verified=False):
    """Never call land use current unless imagery and validated model actually ran."""
    if not imagery_processed:
        return "aguardando_processamento"
    if not classifier_validated:
        return "sem_classificador_validado"
    if not native_mask_verified:
        return "mascara_nativa_nao_verificada"
    if freshness.get("status") != "cenas_recentes_identificadas":
        return "diagnostico_com_restricao_temporal"
    return "diagnostico_atual_com_evidencias"
