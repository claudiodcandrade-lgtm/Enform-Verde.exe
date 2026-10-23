"""Batch entrypoint for audited crop probabilities, height and regional phenology.

An actual SAR model must produce the externally supplied calibrated posteriors;
this module never substitutes map labels or arbitrary scores for predictions.
"""
from __future__ import annotations
import json
from pathlib import Path
from crop_fusion_inference import decide_crop_with_phenology


def classify_crop_batch(records, *, height_contract, regional_records,
                        validation_gates, model_source, output_path=None):
    """Perform fail-closed fusion for multiple independent observations.

    Each record needs observation and probabilities. This does not generate
    scores or field-validated crop models; the upstream classifier is mandatory.
    """
    if not isinstance(records, list):
        raise ValueError("records precisa ser uma lista.")
    if not isinstance(regional_records, dict) or not isinstance(validation_gates, dict):
        raise ValueError("Contratos regionais e de validação precisam ser dicionários.")
    results=[]
    for n, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("Registro inválido: "+str(n))
        decision=decide_crop_with_phenology(
            record.get("probabilities"), record.get("observation"),
            height_contract, regional_records, validation_gates,
            model_source=model_source)
        results.append({"observation_id":record.get("observation_id",n),
                        "status":decision["status"],"class_name":decision["crop"],
                        "source":"SAR_VALIDADO" if decision["crop"] is not None else "SEM_CLASSIFICACAO_SAR",
                        "decision":decision})
    report={"status":"BATCH_FUSION_EVALUATED", "model_source":model_source,
            "accepted":sum(r["class_name"] is not None for r in results),
            "abstained":sum(r["class_name"] is None for r in results),
            "results":results,
            "caveat":"Resultados condicionais: não garante que os scores fornecidos sejam oriundos de modelo SAR validado. Ainda não integrado à GUI nem à aquisição automática."}
    if output_path is not None:
        path=Path(output_path)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report
