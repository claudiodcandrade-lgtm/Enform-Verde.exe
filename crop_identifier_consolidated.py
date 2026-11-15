"""Crop names are accepted only from current, independently validated SAR maps.

PAM is a yield baseline; MapBiomas is never an input to this module.
"""
from __future__ import annotations

import csv
import gzip
from collections import defaultdict

from crop_yield_scenario import PAM_PATH, PRODUCT_KEY, _resource

CROPS=("Milho","Soja","Sorgo","Café","Cana-de-açúcar","Arroz","Feijão","Citros")
TEMPORARY_UNSEPARATED=("Milho","Sorgo","Feijão")
REGISTRY={crop:{
    "route":"SAR_VALIDADO",
    "tier":1,
    "product":"classificador orbital SAR atual com validação independente por classe/domínio",
    "model_status":"N/D até existir manifesto executável, pixels atuais e validação compatível"}
    for crop in CROPS}


def consolidated_table():
    """No crop label is enabled by a historical annual land-cover product."""
    return [{"crop":crop,**row,"label_allowed":False,
             "uncertainty":"N/D até execução SAR atual e auditoria independente",
             "sar_model_installed":False}
            for crop,row in REGISTRY.items()]


def pam_area_shares(micro_code,crops=TEMPORARY_UNSEPARATED,years=None,path=PAM_PATH):
    """Mean harvested-area share from PAM; prior/benchmark only, never identification."""
    keys={PRODUCT_KEY[c]:c for c in crops}
    area=defaultdict(lambda:defaultdict(float))
    with gzip.open(_resource(path),"rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if (r["territory_code"]==str(micro_code) and r["variable_code"]=="216"
                    and r["product_key"] in keys and r["observation_status"]=="numeric"):
                y=int(r["year"])
                if years is None or y in years:
                    area[y][keys[r["product_key"]]]+=float(r["value_numeric"])
    shares=defaultdict(list)
    for _,by in area.items():
        total=sum(by.values())
        if total>0:
            for c in crops:shares[c].append(by.get(c,0.0)/total)
    if not shares:return None
    return {c:sum(v)/len(v) for c,v in shares.items()}


def attribute_unseparated(micro_code,area_ha,crops=TEMPORARY_UNSEPARATED):
    """Return PAM priors only; caller must never present these as mapped crops."""
    shares=pam_area_shares(micro_code,crops)
    if not shares:return {"status":"N/D","reason":"PAM sem área colhida destas culturas na microrregião"}
    ranked=sorted(shares.items(),key=lambda kv:-kv[1])
    return {"status":"PAM_PRIOR_ONLY","area_ha":area_ha,"probabilities":dict(ranked),
            "most_likely":ranked[0][0],
            "note":"participação histórica da PAM; não identifica cultura nem área do talhão"}
