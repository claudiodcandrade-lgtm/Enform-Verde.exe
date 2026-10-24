"""Quality gates for the Enform Verde agricultural diagnosis.

These checks do not substitute field validation or run crop classifiers.
"""
from datetime import datetime, timezone

CROPS = ("soja", "milho", "sorgo", "café", "cana-de-açúcar", "arroz", "feijão", "citros")

def assess_diagnostic(*, acquisition_utc, processing_ok, source_verified,
                      model_validation, probabilities, native_mask_confirmed,
                      now=None, max_age_days=12, min_precision=0.85,
                      min_recall=0.80, min_probability=0.90, min_margin=0.15):
    """Abstain unless temporal, processing, source and per-class validation pass.

    model_validation maps label to independently measured precision/recall and
    applicability domain. Values must come from real held-out validation.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware current time required")
    result = {"status": "não_classificado", "label": "uso não determinado",
              "native_carbon_eligible": False, "reasons": [], "acquisition_utc": acquisition_utc}
    if not acquisition_utc:
        result["reasons"].append("Sem data de aquisição")
        return result
    try:
        acquired = datetime.fromisoformat(acquisition_utc.replace("Z", "+00:00"))
        if acquired.tzinfo is None:
            raise ValueError()
        age = (now - acquired).total_seconds() / 86400
    except (ValueError, TypeError):
        result["reasons"].append("Data de aquisição inválida")
        return result
    result["age_days"] = round(age, 2)
    if age < 0 or age > max_age_days:
        result["reasons"].append("Aquisição fora da janela de atualidade")
    if not processing_ok:
        result["reasons"].append("Pré-processamento não verificado")
    if not source_verified:
        result["reasons"].append("Proveniência não verificada")
    if not probabilities:
        result["reasons"].append("Sem probabilidades do classificador")
        return result
    try:
        scores = sorted(((k, float(v)) for k, v in probabilities.items()
                         if 0 <= float(v) <= 1), key=lambda kv: kv[1], reverse=True)
    except (TypeError, ValueError):
        result["reasons"].append("Probabilidades inválidas")
        return result
    if not scores:
        result["reasons"].append("Sem probabilidades válidas")
        return result
    label, probability = scores[0]
    margin = probability - (scores[1][1] if len(scores) > 1 else 0)
    validation = model_validation.get(label, {})
    if not validation.get("independent_test") or not validation.get("in_domain"):
        result["reasons"].append("Validação independente/domínio não comprovados")
    if validation.get("precision", -1) < min_precision or validation.get("recall", -1) < min_recall:
        result["reasons"].append("Acurácia da classe abaixo do limiar")
    if probability < min_probability or margin < min_margin:
        result["reasons"].append("Confiança/margem insuficiente")
    if label == "vegetação nativa" and not native_mask_confirmed:
        result["reasons"].append("Máscara nativa sem confirmação independente")
    if result["reasons"]:
        return result
    result["status"] = "classificação_com_evidências"
    result["label"] = label
    result["confidence"] = probability
    result["native_carbon_eligible"] = label == "vegetação nativa" and native_mask_confirmed
    return result
