"""Conservative land-use decision and native-only carbon eligibility.

This module does not itself infer crop probabilities. It consumes externally
validated classifier outputs with provenance and calibration metadata.
"""
from dataclasses import dataclass
from typing import Mapping, Optional
import unicodedata

CROPS = frozenset({"soja", "milho", "sorgo", "café", "cana-de-açúcar", "arroz", "feijão", "citros", "algodão"})
NATIVE = frozenset({"vegetação nativa"})
NON_NATIVE = frozenset({"pastagem", "áreas cultivadas", "área urbana", "corpo d'água"})
MIN_CONFIDENCE = 0.90
MIN_MARGIN = 0.15

def has_cultivated_area(class_records) -> bool:
    """True only for mapped crop/agriculture classes; pasture alone is not a crop."""
    crop_keys = {unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().casefold()
                 for x in CROPS}
    crop_keys.update({"areas cultivadas", "agricultura", "lavoura temporaria", "lavoura perene",
                      "cana", "citrus", "algodao", "cotton"})
    for item in class_records or ():
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("class_name", ""))
        key = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()
        if key.startswith("lavoura de "):
            key = key[len("lavoura de "):].strip()
        try:
            area = float(item.get("area_ha", 0) or 0)
        except (TypeError, ValueError):
            continue
        if key in crop_keys and area > 0:
            return True
    return False

@dataclass(frozen=True)
class LandUseDecision:
    label: str
    confidence: Optional[float]
    source: str
    native_carbon_eligible: bool
    reason: str

def classify_land_use(probabilities: Mapping[str, float], *,
                      source: str, validated: bool,
                      native_reference_confirmed: bool = False,
                      confidence_threshold: float = MIN_CONFIDENCE,
                      margin_threshold: float = MIN_MARGIN) -> LandUseDecision:
    """Require a validated, sourced model; avoid forced crop/pasture labels.

    Native eligibility additionally requires independent native-vegetation
    confirmation. A model's crop scores alone cannot establish native cover.
    """
    if not source or not validated:
        return LandUseDecision("não classificada", None, source or "não informada", False,
                               "Classificador sem validação ou fonte documentada")
    valid = {k: float(v) for k, v in probabilities.items()
             if k in CROPS | NATIVE | NON_NATIVE and 0 <= float(v) <= 1}
    if not valid:
        return LandUseDecision("não classificada", None, source, False, "Sem probabilidades válidas")
    ranked = sorted(valid.items(), key=lambda item: item[1], reverse=True)
    label, score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    if score < confidence_threshold or score - runner_up < margin_threshold:
        if any(k in valid for k in CROPS | {"pastagem", "áreas cultivadas"}):
            return LandUseDecision("áreas cultivadas", score, source, False,
                                   "Cultura/pastagem não diferenciada com confiança")
        return LandUseDecision("não classificada", score, source, False,
                               "Classe sem confiança suficiente")
    if label == "vegetação nativa":
        eligible = native_reference_confirmed
        return LandUseDecision(label, score, source, eligible,
                               "Vegetação nativa confirmada" if eligible else
                               "Aguardando confirmação independente de vegetação nativa")
    if label in CROPS or label == "pastagem":
        return LandUseDecision(label, score, source, False, "Uso antrópico; carbono excluído")
    return LandUseDecision(label, score, source, False, "Fora da máscara de vegetação nativa")

def native_only_stock(values, native_mask):
    """Return native-only total; fail closed for unknown masks or invalid stocks."""
    if len(values) != len(native_mask):
        raise ValueError("Valores e máscara precisam ter o mesmo comprimento")
    total = 0.0
    for value, native in zip(values, native_mask):
        if native is not True:
            continue
        if value is None:
            continue
        value = float(value)
        if not __import__("math").isfinite(value) or value < 0:
            raise ValueError("Estoque nativo inválido")
        total += value
    return total
