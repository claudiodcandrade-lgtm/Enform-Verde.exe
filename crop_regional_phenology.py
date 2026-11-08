"""Regional crop phenology + height evidence fusion. No universal calendar or height thresholds.

Source records are supplied by audited ZARC/CONAB or equivalent institutions.
Recommended sowing windows are a prior, never proof of an actual sowing date.
"""
from __future__ import annotations
from datetime import date, datetime
from math import isfinite
from crop_height_features import height_interval_features


def _date(value):
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def regional_stage_evidence(crop, observation, height_contract, regional_record):
    """Assess crop candidate against local season, phenology and measured height.

    Does not return a crop decision or increase classifier confidence. Requires
    matched geographic unit, season, source and independently supported stage
    duration ranges. Stage is possible if ANY permissible planting date and
    development duration yield compatible day-after-sowing interval.
    """
    issues=[]
    if not isinstance(regional_record,dict):regional_record={}
    if not isinstance(observation,dict):observation={}
    if crop != regional_record.get("crop"):
        issues.append("cultura difere do registro regional")
    for key in ("source_url","source_institution","state","municipality_code",
                "season","valid_year","planting_windows","stage_intervals_days",
                "stage_reference_url"):
        if not regional_record.get(key) and regional_record.get(key)!=0:
            issues.append("metadado regional ausente: "+key)
    if observation.get("municipality_code") != regional_record.get("municipality_code"):
        issues.append("município do pixel não corresponde ao registro")
    if observation.get("state") != regional_record.get("state"):
        issues.append("UF do pixel não corresponde ao registro")
    if observation.get("season") != regional_record.get("season"):
        issues.append("safra do pixel não corresponde ao registro")
    try:
        when=_date(observation["observation_date"])
        if int(regional_record["valid_year"]) != when.year:
            issues.append("ano de validade regional difere do ano da observação")
    except (KeyError,ValueError,TypeError):
        issues.append("data/ano regional inválido")
        when=None
    features,audit=height_interval_features(observation,height_contract)
    if not audit["eligible"]:
        issues.extend(audit["reasons"])
    supported=[]
    if when is not None:
        try:
            stage_intervals=regional_record["stage_intervals_days"]
            windows=regional_record["planting_windows"]
            for w in windows:
                start,end=_date(w["start"]),_date(w["end"])
                if end<start or (end-start).days>366:
                    raise ValueError("janela regional inválida")
                if not end<when:
                    end=min(end,when)
                if start> end:continue
                min_days,max_days=(when-end).days,(when-start).days
                for stage,span in stage_intervals.items():
                    lo,hi=map(int,span)
                    if lo<0 or hi<lo:
                        raise ValueError("intervalo fenológico inválido")
                    if max(min_days,lo)<=min(max_days,hi):
                        supported.append(stage)
        except (KeyError,TypeError,ValueError):
            issues.append("janelas e durações fenológicas inválidas")
    stage=observation.get("phenological_stage")
    if stage not in supported:
        issues.append("estágio declarado não sustentado pelo calendário regional")
    return {"crop":crop,"possible_stages":sorted(set(supported)),
            "height_features":features if audit["eligible"] else None,
            "eligible_as_supporting_feature":not issues,"reasons":issues,
            "regional_source":regional_record.get("source_url"),
            "stage_source":regional_record.get("stage_reference_url"),
            "warning":"Calendário ZARC/CONAB indica plausibilidade regional, não plantio observado. Não identifica nem valida uma cultura; altura deve ser calibrada por cultura, estágio e domínio."}
