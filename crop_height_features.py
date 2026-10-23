"""Optional crop-height/phenology contract: fail closed unless height is measured and validated.

A SAR backscatter feature is not itself a measured crop height; height must come
from a documented retrieval model with independent error and matching dates.
"""
from __future__ import annotations
import math

CROP_NAMES = ("Milho", "Soja", "Sorgo", "Café", "Cana-de-açúcar", "Arroz", "Feijão", "Citros")
HEIGHT_FEATURES = ("height_m", "height_uncertainty_m", "observation_date", "phenological_stage")


def check_crop_height_observation(observation, contract):
    """Audit one height observation before passing it to an agricultural classifier.

    Does NOT identify a crop and deliberately has no universal crop-specific
    height thresholds. An interval-validated product is needed for inference.
    """
    reasons = []
    if not isinstance(contract, dict):
        return {"eligible": False, "reasons": ["contrato de altura ausente"]}
    for key in ("height_source", "retrieval_model", "validation_reference",
                "sensor", "processing", "date", "uncertainty_method",
                "rmse_m", "domain"):
        if not contract.get(key) and contract.get(key) != 0:
            reasons.append("metadado obrigatório ausente: " + key)
    if contract.get("height_source") not in ("SAR_height_product", "field_height"):
        reasons.append("altura não é produto SAR validado ou medição de campo")
    if not isinstance(observation,dict):
        observation = {}
    for key in HEIGHT_FEATURES:
        if observation.get(key) is None:
            reasons.append("atributo obrigatório ausente: " + key)
    if observation.get("observation_date") != contract.get("date"):
        reasons.append("datas da altura e da cena não coincidem")
    for key in ("height_m", "height_uncertainty_m"):
        try:
            value = float(observation[key])
            if not math.isfinite(value) or value < 0:
                reasons.append("altura/incerteza inválida: " + key)
        except (KeyError,ValueError,TypeError):
            reasons.append("altura/incerteza não numérica: " + key)
    try:
        rmse = float(contract["rmse_m"])
        if not math.isfinite(rmse) or rmse < 0:
            reasons.append("RMSE de altura inválido")
    except (KeyError,ValueError,TypeError):
        reasons.append("RMSE de altura ausente ou inválido")
    if contract.get("independent_validation") is not True:
        reasons.append("erro de altura não validado independentemente")
    if contract.get("uncertainty_method") not in ("prediction_interval_half_width", "standard_uncertainty"):
        reasons.append("natureza da incerteza de altura desconhecida")
    return {"eligible": not reasons, "reasons": reasons,
            "height_m": observation.get("height_m"),
            "height_uncertainty_m": observation.get("height_uncertainty_m"),
            "warning": "Altura não identifica cultura isoladamente; usar séries SAR multitemporais, fenologia e validação independente por cultura."}


def height_interval_features(observation, contract):
    """Return bounded height features only for audited observations."""
    audit = check_crop_height_observation(observation, contract)
    if not audit["eligible"]:
        return None, audit
    h = float(observation["height_m"])
    u = float(observation["height_uncertainty_m"])
    return {"height_m": h, "height_lower_m": max(0.0, h-u),
            "height_upper_m": h+u, "phenological_stage": observation["phenological_stage"]}, audit
