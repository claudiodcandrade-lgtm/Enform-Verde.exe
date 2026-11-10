"""Pure executive-report presentation helpers.

The initial cartographic stage may say that yield is unavailable while a
separately run PAM/FAO panel is pending. If the later panel succeeds, remove
only the obsolete placeholders from the FINAL executive report, including
those embedded in an earlier multi-line report chunk. Never hide blocked
status when the newer forecast itself is not available.
"""
from __future__ import annotations


def remove_superseded_yield_placeholders(chunks):
    """Return a copy of text chunks without contradictory provisional lines."""
    out = []
    for chunk in chunks:
        text = str(chunk)
        kept = []
        for line in text.splitlines(keepends=True):
            clean = line.strip()
            is_productivity = clean.startswith("Produtividade provável:")
            is_production = clean.startswith("Produção provável:")
            provisional = (
                ("BLOQUEADA" in clean or "INDISPONÍVEL" in clean)
                and (is_productivity or is_production)
            )
            if not provisional:
                kept.append(line)
        out.append("".join(kept))
    return out


def current_crop_area_by_semantic_sar(land):
    """Return current crop areas only when this AOI has an executable SAR classification.

    An unavailable classifier must not turn the empty class list into a measured
    zero-hectare result.
    """
    if not isinstance(land, dict) or land.get("status") != "SAR_ELEGIVEL":
        return None, None
    classes=land.get("classes") or []
    crop=sum(float(x.get("area_ha") or 0) for x in classes
             if str(x.get("class_name") or "").startswith("Lavoura de "))
    generic=sum(float(x.get("area_ha") or 0) for x in classes
                if str(x.get("class_name") or "") in
                ("Áreas cultivadas","Lavoura Temporária","Outras Lavouras Temporárias"))
    return crop,generic


def experimental_seasonal_sar_classes(land):
    """Summarize real-pixel seasonal model output without calling it current/validated.

    The LEM+ RF result is eligible only when its runtime audit identifies the
    experimental classifier and the final area rows retain that SAR source.
    Areas are exact polygon/pixel intersections, not statistically corrected
    estimates; uncertainty for the AOI is therefore explicitly unmeasured.
    """
    if not isinstance(land, dict):
        return None
    meta = land.get("sar_classifier_lemplus")
    if not isinstance(meta, dict) or meta.get("status") != "SAR_CLASSIFICADOR_EXPERIMENTAL":
        return None
    rows = []
    for item in land.get("classes") or []:
        if not isinstance(item, dict) or not str(item.get("source") or "").startswith("SAR_EXPERIMENTAL_MODELO"):
            continue
        try:
            area = float(item.get("area_ha"))
        except (TypeError, ValueError):
            continue
        if area > 0:
            rows.append({"class_name": str(item.get("class_name") or "Classe SAR não identificada"),
                         "area_ha": area})
    if not rows:
        return None
    return {
        "season": meta.get("season"), "model_id": meta.get("model_id"),
        "model_sha256": meta.get("model_sha256"), "pixels": meta.get("pixels"),
        "scenes_used": meta.get("scenes_used"), "observed_months": meta.get("observed_months"),
        "landcover_overall_accuracy": meta.get("landcover_overall_accuracy"),
        "landcover_overall_accuracy_wilson95": meta.get("landcover_overall_accuracy_wilson95"),
        "crop_overall_accuracy": meta.get("crop_overall_accuracy"),
        "in_training_domain": meta.get("in_training_domain"),
        "domain": meta.get("domain"), "classes": rows,
        "area_uncertainty": "Estimativa com incerteza não mensurada",
    }
