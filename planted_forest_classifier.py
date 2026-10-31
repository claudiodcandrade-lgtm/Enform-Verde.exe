"""Planted-forest target taxonomy and conservative SAR decision support.

MapBiomas C11 class 9 means SILVICULTURA and does not reveal tree genus.
The genus Eucalyptus / Pinus requires independent, compatible observations.
"""
from __future__ import annotations

MAPBIOMAS_C11_SILVICULTURE_CODE = 9
PLANTED_FOREST = "Floresta plantada"
GENERA = ("Eucalipto", "Pinus")

def planted_forest_map_label(collection, code):
    """Interpret verified MapBiomas legend; never infer genus from class 9."""
    if collection != "mapbiomas_c11_coverage":
        return None
    try:
        return PLANTED_FOREST if int(code) == MAPBIOMAS_C11_SILVICULTURE_CODE else None
    except (ValueError,TypeError):
        return None

def planted_forest_decision(sar_class, genus_scores=None, genus_gates=None, *, mapped_silviculture=False):
    """Only promote genus from independently accepted classifier output.

    No map label, height alone or generic 'forest' class can prove silviculture;
    map-sourced silviculture is explicitly cartographic, not SAR validated.
    """
    from crop_model_registry import SCORE_THRESHOLD, MIN_INDEPENDENT, MIN_PRECISION_LOWER
    base_confirmed = sar_class in (PLANTED_FOREST, *GENERA)
    source="SAR_VALIDADO" if base_confirmed else "MAPBIOMAS" if mapped_silviculture else "SEM_COBERTURA"
    if not (base_confirmed or mapped_silviculture):
        return {"class_name":None,"source":source,"reason":"floresta plantada não comprovada"}
    result={"class_name":PLANTED_FOREST,"source":source,
            "reason":"gênero não verificado; classe silvicultura mantida"}
    if not base_confirmed:
        return result
    if not isinstance(genus_scores,dict) or not isinstance(genus_gates,dict):
        return result
    scores={g:genus_scores.get(g) for g in GENERA}
    for g in GENERA:
        v=scores[g]
        if not isinstance(v,(int,float)) or not 0 <= v <= 1:
            return result
    if abs(sum(scores.values())-1)>1e-4:
        return result
    winner=max(GENERA,key=lambda g:scores[g])
    gate=genus_gates.get(winner) or {}
    if (scores[winner]>=SCORE_THRESHOLD
        and gate.get("eligible") is True
        and gate.get("n_independent",0)>=MIN_INDEPENDENT
        and gate.get("precision_wilson95_lower",0)>=MIN_PRECISION_LOWER):
        return {"class_name":winner,"source":"SAR_VALIDADO",
                "reason":"gênero SAR sujeito a validação independente específica"}
    return result
