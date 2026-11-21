"""Quality gates for the Enform Verde agricultural diagnosis.

These checks do not substitute field validation or run crop classifiers.
"""
from datetime import datetime, timezone

CROPS = ("soja", "milho", "sorgo", "café", "cana-de-açúcar", "arroz", "feijão", "citros")

def assess_diagnostic(*, acquisition_utc, processing_ok, source_verified,
                      model_validation, probabilities, native_mask_confirmed,
                      now=None, max_age_days=12, min_precision=None,
                      min_recall=None, min_probability=None, min_margin=None):
    """Require a measured, traceable performance metric; no accuracy cutoff.

    Published foreign-domain results may support a *provisional* crop signal
    from an actually executed model, distinctly labeled as unverified locally.
    No published percentage is represented as the accuracy of this AOI.
    Legacy min_* arguments are ignored: they are not scientific release gates.
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
    from math import isfinite
    validation = (model_validation or {}).get(label, {})
    local = validation.get("independent_test") is True and validation.get("in_domain") is True
    # A recognized publication is valid research evidence even with weak
    # accuracy. Published-only labels are explicitly provisional, never a
    # locally validated model or proof of native carbon eligibility.
    published = (validation.get("published_validation") is True
                 and bool(validation.get("institution"))
                 and bool(validation.get("publication_url"))
                 and bool(validation.get("metric")))
    metric_value=validation.get("precision") if local else validation.get("published_accuracy")
    if metric_value is None:
        result["reasons"].append("Desempenho quantitativo não informado")
    else:
        try:
            measure=float(metric_value)
            if not isfinite(measure) or not 0<=measure<=1:
                raise ValueError()
        except (TypeError,ValueError):
            result["reasons"].append("Acurácia publicada inválida")
            measure=None
    if not local and not published:
        result["reasons"].append("Validação independente ou publicação científica rastreável ausente")
    if local and validation.get("recall") is not None:
        try:
            recall=float(validation["recall"])
            if not isfinite(recall) or not 0<=recall<=1:
                raise ValueError()
        except (TypeError,ValueError):
            result["reasons"].append("Recall inválido")
    if validation.get("n_independent") is not None:
        try:
            if int(validation["n_independent"])<=0:
                raise ValueError()
        except (TypeError,ValueError):
            result["reasons"].append("Amostra independente inválida")
    result["validation_scope"]="local_independent" if local else ("published_original_domain_only" if published else "unverified")
    result["measured_accuracy"]=measure if metric_value is not None else None
    result["accuracy_metric"]=validation.get("metric") or ("precision" if local else None)
    result["validation_source"]=validation.get("publication_url") or validation.get("source")
    result["sample_count"]=validation.get("n_independent")
    result["uncertainty_note"]=("Desempenho publicado no domínio de origem; não é acurácia validada nesta AOI."
                                if not local else "Validação local declarada; incerteza depende do desenho e da amostragem.")
    if label == "vegetação nativa" and not native_mask_confirmed:
        result["reasons"].append("Máscara nativa sem confirmação independente")
    if result["reasons"]:
        return result
    result["status"] = ("classificação_com_evidências" if local
                        else "classificação_provisória_com_acurácia_publicada")
    result["label"] = label
    result["confidence"] = probability
    result["native_carbon_eligible"] = bool(local and label == "vegetação nativa" and native_mask_confirmed)
    return result
