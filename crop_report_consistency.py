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
