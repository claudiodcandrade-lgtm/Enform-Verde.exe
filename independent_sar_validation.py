"""Independent external SAR classifier validation from field-labelled CSV.

Input is a table of HELD-OUT predictions from the actual deployed SAR model.
Never use training pseudo-labels or the same geography/units for both training
and validation. This function performs statistics, not model prediction.
"""
from __future__ import annotations
import csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path
from crop_model_registry import CLASSIFIER_TARGETS, SCORE_THRESHOLD, MIN_INDEPENDENT, MIN_PRECISION_LOWER, _wilson_lower

def validate_independent_predictions(csv_path, *, model_sha256, reference_url,
                                     training_unit_ids=(), output_json=None):
    """Compute acceptance gates; refuse validation with unverifiable provenance."""
    path=Path(csv_path)
    fields={"unit_id","truth","prediction","calibrated_probability","reference_source",
            "reference_date","observation_date","independent_field_reference",
            "source_record_id","biome","state"}
    if not path.is_file() or not model_sha256 or not reference_url:
        raise ValueError("Arquivo, SHA-256 dos pesos e URL de referência obrigatórios.")
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not fields.issubset(reader.fieldnames):
            raise ValueError("Colunas obrigatórias de validação ausentes.")
        rows=list(reader)
    used=set(training_unit_ids); seen=set(); errors=[]; accepted=defaultdict(lambda:{"n":0,"correct":0})
    labels=tuple(CLASSIFIER_TARGETS)
    matrix={t:{p:0 for p in labels} for t in labels}
    for line,r in enumerate(rows,2):
        uid=r["unit_id"].strip()
        if not uid or uid in seen or uid in used:
            errors.append(f"linha {line}: unidade duplicada ou usada em treinamento")
            continue
        seen.add(uid)
        if r["truth"] not in labels or r["prediction"] not in labels:
            errors.append(f"linha {line}: classe ausente do catálogo")
            continue
        try:score=float(r["calibrated_probability"])
        except ValueError:score=float("nan")
        if not math.isfinite(score) or score<0 or score>1:
            errors.append(f"linha {line}: probabilidade inválida")
            continue
        if r["independent_field_reference"].strip().lower() != "true":
            errors.append(f"linha {line}: referência de campo independente não demonstrada")
            continue
        if not all(r[k].strip() for k in ("reference_source","source_record_id","reference_date",
                                          "observation_date","biome","state")):
            errors.append(f"linha {line}: proveniência de referência incompleta")
            continue
        t,p=r["truth"],r["prediction"]
        matrix[t][p]+=1
        if score>=SCORE_THRESHOLD:
            accepted[p]["n"]+=1
            accepted[p]["correct"]+=int(t==p)
    gates={}
    for label in labels:
        n=accepted[label]["n"]; correct=accepted[label]["correct"]
        lower=_wilson_lower(correct,n)
        gates[label]={"n_independent_accepted":n,"correct":correct,
                      "precision":correct/n if n else None,"precision_wilson95_lower":lower,
                      "eligible":not errors and n>=MIN_INDEPENDENT and lower>=MIN_PRECISION_LOWER}
    report={"status":"REPROVADO_AUDITORIA" if errors else "ESTATISTICAS_CALCULADAS",
            "all_targets_validated":bool(rows) and not errors and all(g["eligible"] for g in gates.values()),
            "model_sha256":model_sha256,"reference_url":reference_url,
            "validation_file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "total_rows":len(rows),"audit_errors":errors,
            "confusion_matrix":matrix,"gates":gates,
            "limitations":["A declaração de independência e a autenticidade dos registros exigem auditoria externa.",
                           "Verificar separação espacial/temporal contra treinos e compatibilidade de domínio.",
                           "Não basta fornecer um CSV: previsões devem vir do modelo SAR executado."]}
    if output_json:
        Path(output_json).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report
