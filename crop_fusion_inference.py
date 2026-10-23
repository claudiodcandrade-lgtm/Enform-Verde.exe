"""Fail-closed late fusion for externally fitted, independently validated crop models.

Uses existing model probabilities and independently audited regional height/phenology.
Does not fit or silently rescale scores. Unsupported evidence can abstain, never
promote a weak class into a seemingly validated prediction.
"""
from __future__ import annotations
import math
from crop_regional_phenology import regional_stage_evidence
from crop_model_registry import SCORE_THRESHOLD, MIN_INDEPENDENT, MIN_PRECISION_LOWER

def decide_crop_with_phenology(probabilities, observation, height_contract,
                              regional_records, validation_gates, *, model_source):
    """Return accepted crop only when the full independent validation contract holds.

    The caller MUST have calibrated probabilities from a model trained with SAR,
    separately validated on real reference observations. The calendar is a
    compatibility veto, not new probability evidence.
    """
    audit={"status":"ABSTENCAO", "crop":None, "source":model_source,
           "reasons":[], "candidates":[], "method":"SAR calibrado + veto regional altura/fenologia"}
    if not model_source:
        audit["reasons"].append("fonte/modelo não declarado")
    if not isinstance(probabilities,dict) or not probabilities:
        audit["reasons"].append("probabilidades ausentes")
        return audit
    try:
        values={k:float(v) for k,v in probabilities.items()}
        if any(not math.isfinite(v) or v<0 or v>1 for v in values.values()) or abs(sum(values.values())-1)>1e-4:
            raise ValueError()
    except (TypeError,ValueError):
        audit["reasons"].append("probabilidades calibradas inválidas")
        return audit
    ranking=sorted(values, key=values.get,reverse=True)
    best=ranking[0]
    if values[best]<SCORE_THRESHOLD:
        audit["reasons"].append("probabilidade abaixo de 0,90")
        return audit
    gate=(validation_gates or {}).get(best,{})
    if not (gate.get("eligible") is True and int(gate.get("n_independent",0))>=MIN_INDEPENDENT
            and float(gate.get("precision_wilson95_lower",0))>=MIN_PRECISION_LOWER):
        audit["reasons"].append("validação independente insuficiente para classe")
        return audit
    if len(ranking)>1 and values[best]==values[ranking[1]]:
        audit["reasons"].append("empate entre classes")
        return audit
    rec=(regional_records or {}).get(best)
    evidence=regional_stage_evidence(best,observation,height_contract,rec)
    audit["candidates"].append({"crop":best,"sar_probability":values[best],
                                "regional_support":evidence})
    if not evidence["eligible_as_supporting_feature"]:
        audit["reasons"].append("incompatibilidade/ausência de evidência fenológica e altura")
        return audit
    audit.update({"status":"ACEITO_COM_EVIDENCIA_REGIONAL","crop":best,
                  "score_calibrated_sar":values[best],
                  "warning":"Confiança regional não foi recalibrada pela altura; evidências apenas vetam. Exige validação prospectiva da política de fusão."})
    return audit
