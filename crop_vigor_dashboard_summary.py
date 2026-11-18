"""Compact, auditable crop-vigor summary for the executive dashboard."""
from __future__ import annotations


def crop_vigor_dashboard_lines(crop_audit, format_number):
    """Return concise lines that distinguish observed vigor from model use.

    The model's own audit flag is authoritative. A displayed vigor class alone
    never implies that the forecast distribution used it.
    """
    lines = []
    crops = (crop_audit or {}).get("crops") or {}
    for crop_name, entry in crops.items():
        if not isinstance(entry, dict):
            continue
        inputs = entry.get("forecast_inputs") or {}
        model_audit = (entry.get("vigor_model_audit") or
                       inputs.get("vigor_model_audit") or {})
        used = model_audit.get("used_in_yield_distribution") is True
        observation = (entry.get("crop_specific_vigor") or
                       entry.get("vigor_observation") or
                       entry.get("vigor") or {})
        probabilities = (model_audit.get("probabilities_used") or
                         observation.get("probabilities") or {})
        probability_text = ", ".join(
            str(label) + ": " + format_number(value * 100, 0) + "%"
            for label, value in probabilities.items()
            if isinstance(value, (int, float)))
        line = (
            str(crop_name) + ": vigor " +
            str(observation.get("class") or observation.get("status") or "N/D") +
            "; participação na distribuição PAM×clima: " +
            ("SIM, condicional" if used else "NÃO confirmada")
        )
        if probability_text:
            line += "; probabilidades: " + probability_text
        area = observation.get("sample_area_ha")
        coverage = observation.get("sar_sample_coverage_fraction")
        if isinstance(area, (int, float)):
            line += "; amostra: " + format_number(area, 2) + " ha"
        if isinstance(coverage, (int, float)):
            line += " (" + format_number(coverage * 100, 2) + "% da máscara)"
        scenes = observation.get("accepted_scenes") or []
        samples = observation.get("sample_audit") or []
        scene = scenes[0] if scenes else (samples[0] if samples else {})
        scene_date = scene.get("acquisition_utc") or "data N/D"
        mask_season = str(inputs.get("crop_mask_season") or "safra N/D")
        line += "; cena: " + str(scene_date) + "; máscara: " + mask_season
        lines.append(line)
    if not lines:
        candidate = (crop_audit or {}).get("current_sar_candidate_vigor") or {}
        lines.append(
            "Vigor SAR: " +
            str(candidate.get("class") or candidate.get("reason") or
                candidate.get("status") or "N/D") +
            "; uso na previsão por cultura: não confirmado."
        )
    return lines
