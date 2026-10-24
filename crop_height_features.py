"""Optional crop-height/phenology contract: fail closed unless height is measured and validated.

A SAR backscatter feature is not itself a measured crop height; height must come
from a documented retrieval model with independent error and matching dates.
"""
from __future__ import annotations
import math

CROP_NAMES = ("Milho", "Soja", "Sorgo", "Café", "Cana-de-açúcar", "Arroz", "Feijão", "Citros")
HEIGHT_FEATURES = ("height_m", "height_uncertainty_m", "observation_date", "phenological_stage")

# Literature establishes technical potential for these Sentinel-1 crop-height
# retrievals outside the Enform Verde Brazilian validation domain. They are
# candidates only: training/release still requires independent in-domain
# height validation for crop × region × phase × sensor/processing.
SAR_HEIGHT_CANDIDATES = {
    "milho": {"sensor": "Sentinel-1 C-band", "reference": "https://doi.org/10.3390/agriculture12060800",
              "status": "literature_candidate_requires_Brazil_domain_validation"},
    "soja": {"sensor": "Sentinel-1 plus optical fusion", "reference": "https://www.sciencedirect.com/science/article/pii/S0034425725002299",
             "status": "literature_candidate_requires_Brazil_domain_validation"},
    "arroz": {"sensor": "Sentinel-1 C-band time series", "reference": "https://doi.org/10.3390/rs10091394",
              "status": "literature_candidate_requires_Brazil_domain_validation"},
    "cana_acucar": {"sensor": "Sentinel-1A time series", "reference": "https://doi.org/10.1080/10095020.2024.2381607",
                    "status": "literature_candidate_requires_Brazil_domain_validation"},
}


def crop_height_route(crop):
    """Return evidence route for a crop without implying local validation."""
    key = str(crop).casefold().replace("-", "_").replace(" ", "_")
    aliases = {"maize": "milho", "corn": "milho", "milho_grao": "milho",
               "soybean": "soja", "soy": "soja", "soja_grao": "soja",
               "rice": "arroz", "arroz_grao": "arroz",
               "sugarcane": "cana_acucar", "cana": "cana_acucar", "cana_de_acucar": "cana_acucar"}
    key = aliases.get(key, key)
    return dict(SAR_HEIGHT_CANDIDATES[key]) if key in SAR_HEIGHT_CANDIDATES else {
        "status": "no_crop_specific_SAR_height_retrieval_established_for_operational_use"}


def check_crop_height_observation(observation, contract):
    """Audit one height observation before passing it to an agricultural classifier.

    Does NOT identify a crop and deliberately has no universal crop-specific
    height thresholds. An interval-validated product is needed for inference.
    """
    reasons = []
    if not isinstance(contract, dict):
        return {"eligible": False, "reasons": ["contrato de altura ausente"]}
    for key in ("height_source", "retrieval_model", "height_source_url", "model_sha256",
                "validation_reference", "sensor", "processing", "date", "uncertainty_method",
                "rmse_m", "bias_m", "domain", "crop", "region", "phase",
                "n_independent", "n_spatial_blocks", "coverage_95"):
        if not contract.get(key) and contract.get(key) != 0:
            reasons.append("metadado obrigatório ausente: " + key)
    if contract.get("height_source") != "SAR_height_product":
        reasons.append("altura não é um produto SAR")
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
    if contract.get("in_domain_validation") is not True:
        reasons.append("altura sem validação independente no domínio cultura/região/fase")
    try:
        if int(contract["n_independent"]) < 50 or int(contract["n_spatial_blocks"]) < 5:
            reasons.append("validação de altura exige ≥50 unidades e ≥5 blocos espaciais")
        if not math.isfinite(float(contract["bias_m"])):
            reasons.append("viés de altura inválido")
        coverage = float(contract["coverage_95"])
        if not 0 < coverage < 1:
            reasons.append("cobertura do intervalo de altura inválida")
    except (KeyError, ValueError, TypeError, OverflowError):
        reasons.append("estatísticas independentes de altura ausentes ou inválidas")
    digest = str(contract.get("model_sha256", ""))
    if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        reasons.append("hash SHA-256 do modelo de altura inválido")
    if contract.get("uncertainty_method") not in ("prediction_interval_half_width", "standard_uncertainty"):
        reasons.append("natureza da incerteza de altura desconhecida")
    return {"eligible": not reasons, "reasons": reasons,
            "height_m": observation.get("height_m"),
            "height_uncertainty_m": observation.get("height_uncertainty_m"),
            "warning": "Altura é preditor estrutural, não medida isolada de idade, vigor ou saúde. Usar trajetória fenológica e validação independente por cultura, região e fase."}


def height_interval_features(observation, contract):
    """Return bounded height features only for audited observations."""
    audit = check_crop_height_observation(observation, contract)
    if not audit["eligible"]:
        return None, audit
    h = float(observation["height_m"])
    u = float(observation["height_uncertainty_m"])
    return {"height_m": h, "height_lower_m": max(0.0, h-u),
            "height_upper_m": h+u, "phenological_stage": observation["phenological_stage"]}, audit
