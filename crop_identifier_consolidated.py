"""Consolidated crop identification for the eight listed crops (rule of 2026-11-03).

Order of evidence follows crop_model_priority (Brazil → African savannas/CIRAD
→ international). For each crop the best AVAILABLE route is fixed here, with
its uncertainty stated, so the program never improvises a crop name.

Route types
* "mapa_brasileiro_anual" — MapBiomas Brasil Coleção 11 (consórcio brasileiro;
  Souza et al. 2020, Remote Sensing 12:2735), classes trained against
  Brazilian reference maps (soja: Song et al.; cana: TerraClass; arroz
  irrigado: ANA/CONAB; café: CONAB). Producer accuracy assessment: ≈85 000
  LAPIG/UFG points, mean global accuracy 88,78 % (1985–2024); per-class C11
  table not yet published → class uncertainty reported as the global figure.
  Temporal transfer: the map is for the previous calendar year, not the
  current season — stated in every output.
* "atribuicao_probabilistica" — the crop is NOT separated by any available
  map/model (milho, sorgo, feijão inside "Outras Lavouras Temporárias" or as a
  second crop). The share of each candidate crop in the microregion's
  harvested area (IBGE PAM, same years) is reported as a prior probability,
  never as an identification.
* "modelo_sar_validado" — reserved for a trained SAR classifier that passes
  crop_model_registry (none installed).
"""
from __future__ import annotations

import csv
import gzip
from collections import defaultdict

from crop_yield_scenario import PAM_PATH, PRODUCT_KEY, _resource

MAPBIOMAS_C11 = {39: "Soja", 20: "Cana-de-açúcar", 40: "Arroz", 46: "Café", 47: "Citros"}
MAPBIOMAS_ACCURACY = {"global_accuracy_mean_1985_2024": 0.8878, "n_reference_points_approx": 85000,
                      "per_class_c11": "não publicada até 03/11/2026",
                      "source": "https://brasil.mapbiomas.org/analise-de-acuracia/"}
TEMPORARY_UNSEPARATED = ("Milho", "Sorgo", "Feijão")

REGISTRY = {
    "Soja": {"route": "mapa_brasileiro_anual", "tier": 1, "product": "MapBiomas C11 classe 39",
             "reference_map": "Song et al. (2021) — expansão da soja na América do Sul"},
    "Cana-de-açúcar": {"route": "mapa_brasileiro_anual", "tier": 1, "product": "MapBiomas C11 classe 20",
                       "reference_map": "TerraClass 2020"},
    "Arroz": {"route": "mapa_brasileiro_anual", "tier": 1, "product": "MapBiomas C11 classe 40 (só arroz irrigado RS/SC/TO/PR litoral)",
              "reference_map": "ANA & CONAB — arroz irrigado 2017–2020"},
    "Café": {"route": "mapa_brasileiro_anual", "tier": 1, "product": "MapBiomas C11 classe 46",
             "reference_map": "CONAB — mapeamento do café 2015–2019"},
    "Citros": {"route": "mapa_brasileiro_anual", "tier": 1, "product": "MapBiomas C11 classe 47",
               "reference_map": "MapBiomas (legenda Citrus)"},
    "Milho": {"route": "atribuicao_probabilistica", "tier": 1, "product": "IBGE PAM área colhida por microrregião"},
    "Sorgo": {"route": "atribuicao_probabilistica", "tier": 1, "product": "IBGE PAM área colhida por microrregião"},
    "Feijão": {"route": "atribuicao_probabilistica", "tier": 1, "product": "IBGE PAM área colhida por microrregião"},
}


def consolidated_table():
    rows = []
    for crop, r in REGISTRY.items():
        unc = (f"acurácia global MapBiomas {100*MAPBIOMAS_ACCURACY['global_accuracy_mean_1985_2024']:.2f}% "
               f"(~{MAPBIOMAS_ACCURACY['n_reference_points_approx']} pontos); por classe C11: "
               f"{MAPBIOMAS_ACCURACY['per_class_c11']}; mapa do ano anterior (transferência temporal)"
               if r["route"] == "mapa_brasileiro_anual" else
               "probabilidade a priori pela participação na área colhida (PAM); não é identificação")
        rows.append({"crop": crop, **r, "uncertainty": unc,
                     "label_allowed": r["route"] == "mapa_brasileiro_anual",
                     "sar_model_installed": False})
    return rows


def pam_area_shares(micro_code, crops=TEMPORARY_UNSEPARATED, years=None, path=PAM_PATH):
    """Mean share of harvested area among ``crops`` in the microregion (IBGE PAM)."""
    keys = {PRODUCT_KEY[c]: c for c in crops}
    area = defaultdict(lambda: defaultdict(float))
    with gzip.open(_resource(path), "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if (r["territory_code"] == str(micro_code) and r["variable_code"] == "216"
                    and r["product_key"] in keys and r["observation_status"] == "numeric"):
                y = int(r["year"])
                if years is None or y in years:
                    area[y][keys[r["product_key"]]] += float(r["value_numeric"])
    shares = defaultdict(list)
    for y, by in area.items():
        tot = sum(by.values())
        if tot > 0:
            for c in crops:
                shares[c].append(by.get(c, 0.0) / tot)
    if not shares:
        return None
    return {c: sum(v) / len(v) for c, v in shares.items()}


def attribute_unseparated(micro_code, area_ha, crops=TEMPORARY_UNSEPARATED):
    s = pam_area_shares(micro_code, crops)
    if not s:
        return {"status": "N/D", "reason": "PAM sem área colhida destas culturas na microrregião"}
    ranked = sorted(s.items(), key=lambda kv: -kv[1])
    return {"status": "atribuicao_probabilistica", "area_ha": area_ha,
            "probabilities": dict(ranked), "most_likely": ranked[0][0],
            "note": ("Probabilidade a priori pela área colhida da microrregião (IBGE PAM 2015–2024). "
                     "Não identifica a cultura do talhão.")}
