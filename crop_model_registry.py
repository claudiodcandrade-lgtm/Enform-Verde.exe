"""Fail-closed registry for international crop classifiers.

A registry entry is NOT a fitted model, downloaded weights, or Brazilian validation.
This module has no heavy dependencies and is safe to import in the Windows GUI.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

CROPS = ("Milho", "Soja", "Sorgo", "Café", "Cana-de-açúcar", "Arroz", "Feijão", "Citros")
SCORE_THRESHOLD = 0.90
MIN_INDEPENDENT = 50
MIN_PRECISION_LOWER = 0.90
ALLOWED_MODALITIES = ("SAR-only", "SAR+óptico")


def _wilson_lower(correct: int, n: int) -> float:
    if n <= 0:
        return 0.0
    import math
    z = 1.959963984540054
    p = correct / n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1+z*z/n)


def evaluate_crop_model(entry: dict, *, base_dir: str | Path = ".") -> dict:
    """Check model provenance and independently validated acceptance.

    The caller must verify authenticity of the independent validation evidence:
    JSON fields alone cannot authenticate field observations or prove independence.
    Refuses to produce any classification if essential evidence is missing.
    """
    name = entry.get("crop")
    audit = {"crop": name, "eligible": False, "reasons": [], "source": entry.get("repository_url"),
             "model_id": entry.get("model_id"), "modality": entry.get("modality")}
    reasons = audit["reasons"]
    if name not in CROPS:
        reasons.append("cultura não contemplada")
    for field in ("model_id", "model_version", "repository_url", "license", "sensor",
                  "processing", "period", "domain", "feature_schema", "modality",
                  "validation"):
        if not entry.get(field):
            reasons.append("campo obrigatório ausente: " + field)
    if entry.get("modality") not in ALLOWED_MODALITIES:
        reasons.append("modalidade inválida ou não declarada")
    if entry.get("modality") == "SAR-only" and not entry.get("sar_features"):
        reasons.append("SAR-only sem atributos SAR comprovados")
    if entry.get("modality") == "SAR+óptico" and not (entry.get("sar_features") and entry.get("optical_features")):
        reasons.append("modelo multimodal sem ambas as fontes declaradas")
    weights = entry.get("weights")
    if not isinstance(weights, dict) or not weights.get("path") or not weights.get("sha256"):
        reasons.append("pesos locais e hash obrigatórios; URL ou artigo não são modelo executável")
    else:
        p = (Path(base_dir) / weights["path"]).resolve()
        base = Path(base_dir).resolve()
        if not p.is_relative_to(base):
            reasons.append("caminho dos pesos fora do diretório autorizado")
        elif not p.is_file():
            reasons.append("arquivo de pesos indisponível")
        else:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest.lower() != str(weights["sha256"]).lower():
                reasons.append("hash dos pesos não corresponde")
    v = entry.get("validation")
    if not isinstance(v, dict):
        reasons.append("validação independente ausente")
    else:
        for key in ("reference_url", "reference_sha256", "split_protocol", "geographic_domain",
                    "temporal_domain", "confusion_matrix", "calibration_method"):
            if not v.get(key):
                reasons.append("evidência de validação ausente: " + key)
        if v.get("independent") is not True:
            reasons.append("independência de validação não demonstrada")
        if v.get("representative") is not True:
            reasons.append("representatividade de validação não documentada")
        try:
            accepted = int(v["n_accepted"])
            correct = int(v["n_correct"])
            threshold = float(v["calibrated_probability_threshold"])
            if accepted < 0 or correct < 0 or correct > accepted:
                raise ValueError()
            audit["precision_wilson95_lower"] = _wilson_lower(correct, accepted)
            audit["n_independent"] = accepted
            if accepted < MIN_INDEPENDENT:
                reasons.append("menos de 50 unidades independentes aceitas")
            if threshold < SCORE_THRESHOLD:
                reasons.append("limiar calibrado inferior a 0,90")
            if audit["precision_wilson95_lower"] < MIN_PRECISION_LOWER:
                reasons.append("limite inferior Wilson abaixo de 0,90")
        except (ValueError, TypeError, KeyError):
            reasons.append("contagens/limiar de validação inválidos")
    audit["eligible"] = not reasons
    audit["note"] = ("Elegibilidade documental; exige revisão humana de procedência, unidades "
                     "independentes, domínio e validação em campo. Não implica desempenho nacional.")
    return audit


def audit_registry(manifest_path: str | Path, *, requested_crop: str | None = None) -> dict:
    """Inspect a local manifest; never downloads or performs unsupported inference."""
    path = Path(manifest_path)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    models = cfg.get("models")
    if not isinstance(models, list):
        raise ValueError("Manifesto requer lista models.")
    results = [evaluate_crop_model(m, base_dir=path.parent) for m in models
               if requested_crop is None or m.get("crop") == requested_crop]
    return {"registry": str(path), "requested_crop": requested_crop,
            "models": results, "eligible_models": sum(bool(r["eligible"]) for r in results),
            "inference_status": "NÃO EXECUTADA — adaptador específico ainda necessário"}


def model_accepts_scene(entry: dict, scene: dict) -> bool:
    """Strict contract guard before any optional inference backend."""
    keys = ("sensor", "processing", "period", "modality", "feature_schema")
    return all(entry.get(k) == scene.get(k) for k in keys) and bool(entry.get("domain") == scene.get("domain"))
