"""Experimental yield forecast: vigor × climate on the microregional PAM history.

Production of the AOI follows the user's general form

    P_AOI = Σ_s A_s · y_s(x_s, θ_s)

where s is a field (talhão) of one crop, A_s its area and y_s the forecast
yield. x_s = (vigor class probabilities, climate class probabilities,
microregional history) and θ_s = (trend, quantile matrix, error terms).

Yield model for one field:
1. Microregional history y_t (IBGE PAM, SIDRA 5457, N9, kg/ha) — suppressed
   years are skipped, never zero.
2. Technology trend by Theil–Sen; detrended values projected to the target
   year:  ỹ_t = y_t − (a + b·t) + (a + b·T).
3. Vigor class v ∈ {baixo, adequado, alto} and climate class c ∈
   {desfavorável, neutro, favorável} select a quantile level q(v, c) of ỹ:

                 desfavorável  neutro  favorável
     baixo           0.00       0.15     0.30      (0.00 = microregional floor)
     adequado        0.35       0.50     0.60      (0.60 = a little above typical)
     alto            0.70       0.85     1.00      (1.00 = microregional ceiling)

   ŷ = Q_ỹ(q(v,c)). The matrix is monotone in both factors and encodes the
   rule given by the user; it is a documented assumption to be recalibrated
   with observed field yields.

Uncertainty (Monte Carlo, all sources simultaneously, with dependencies):
* vigor class drawn from its bootstrap probabilities (independent per field);
* climate class drawn from its analog-ensemble probabilities (SHARED by all
  fields of the same microregion and crop);
* trend/baseline: bootstrap of the PAM years, refit each draw (SHARED);
* model error: empirical leave-one-year-out hindcast errors of the
  climate+history part (SHARED per microregion-crop, systematic);
* transfer error: N(0, σ_transfer) only if measured; otherwise reported as
  NOT quantified (the vigor component has no field validation yet);
* area error: N(A, σ_A) if the classification area error is known.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PAM_PATH = ROOT / "data" / "pam_microregion_yield_2015_2024.csv.gz"
MICRO_PATH = ROOT / "data" / "ibge_microrregioes_2021_simplificada.geojson.gz"
PRODUCT_KEY = {"Soja": "soja_grao", "Milho": "milho_grao", "Sorgo": "sorgo_grao",
               "Café": "cafe_total", "Cana-de-açúcar": "cana_acucar", "Arroz": "arroz_grao",
               "Feijão": "feijao_grao", "Citros": "laranja"}
VIGOR = ("baixo vigor", "vigor adequado", "alto vigor")
CLIMATE = ("desfavorável", "neutro", "favorável")
QUANTILE_MATRIX = np.array([[0.00, 0.15, 0.30],
                            [0.35, 0.50, 0.60],
                            [0.70, 0.85, 1.00]])
MIN_YEARS = 6


def _resource(path):
    import sys
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    p = base / "data" / Path(path).name
    return p if p.is_file() else Path(path)


def load_microregion_yields(crop, micro_code, path=PAM_PATH):
    key = PRODUCT_KEY[crop]
    out = {}
    with gzip.open(_resource(path), "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if (r["product_key"] == key and r["territory_code"] == str(micro_code)
                    and r["variable_code"] == "112" and r["observation_status"] == "numeric"):
                out[int(r["year"])] = float(r["value_numeric"])
    return out


def microregion_of(gdf, path=MICRO_PATH):
    """Dominant N9 microregion (by area) and all intersected ones with shares."""
    import geopandas as gpd
    with gzip.open(_resource(path), "rb") as fh:
        micro = gpd.GeoDataFrame.from_features(json.load(fh)["features"], crs=4326)
    aoi = gdf.to_crs(4326)
    hit = micro[micro.intersects(aoi.geometry.union_all())]
    if hit.empty:
        raise ValueError("AOI fora da malha de microrregiões IBGE")
    geom = aoi.to_crs(6933).geometry.union_all()
    shares = []
    for _, row in hit.to_crs(6933).iterrows():
        a = row.geometry.intersection(geom).area
        if a > 0:
            shares.append({"code": str(row.CD_MICRO), "name": row.NM_MICRO, "uf": row.SIGLA,
                           "share": a / geom.area})
    shares.sort(key=lambda d: -d["share"])
    return {"dominant": shares[0], "all": shares}


def theil_sen(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]; ok = dx != 0
    if not ok.any():
        return 0.0, float(np.median(y))
    b = float(np.median((y[j] - y[i])[ok] / dx[ok]))
    return b, float(np.median(y - b * x))


def detrended(yields, target_year):
    yrs = np.array(sorted(yields)); val = np.array([yields[y] for y in yrs])
    b, a = theil_sen(yrs, val)
    return val - (a + b * yrs) + (a + b * target_year), {"slope_kg_ha_yr": b, "baseline_kg_ha": a + b * target_year}


def scenario_table(yields, target_year):
    vals, trend = detrended(yields, target_year)
    tab = {v: {c: float(np.quantile(vals, QUANTILE_MATRIX[i, j])) for j, c in enumerate(CLIMATE)}
           for i, v in enumerate(VIGOR)}
    return {"table_kg_ha": tab, "floor": float(vals.min()), "mean": float(vals.mean()),
            "ceiling": float(vals.max()), **trend}


def hindcast_errors(yields, climate_F_by_year):
    """Leave-one-year-out test of the climate + history part (vigor = adequado).

    climate_F_by_year: composite F for each historical season year (same
    crop, same microregion). Returns observed − predicted errors (kg/ha).
    """
    years = sorted(set(yields) & set(climate_F_by_year))
    errs = []; naive = []
    for t in years:
        train = {y: yields[y] for y in years if y != t}
        if len(train) < MIN_YEARS - 1:
            continue
        F = np.array([climate_F_by_year[y] for y in train])
        t1, t2 = np.quantile(F, [1 / 3, 2 / 3])
        f = climate_F_by_year[t]; c = 0 if f < t1 else (2 if f > t2 else 1)
        vals, _ = detrended(train, t)
        errs.append(yields[t] - float(np.quantile(vals, QUANTILE_MATRIX[1, c])))
        naive.append(yields[t] - float(np.quantile(vals, 0.5)))   # trend only, no climate
    e = np.array(errs); nv = np.array(naive)
    if not len(e):
        return {"n": 0, "errors_kg_ha": []}
    return {"n": int(len(e)), "errors_kg_ha": e.tolist(), "bias_kg_ha": float(e.mean()),
            "mae_kg_ha": float(np.abs(e).mean()), "rmse_kg_ha": float(np.sqrt((e ** 2).mean())),
            "naive_trend_only_mae_kg_ha": float(np.abs(nv).mean()),
            "climate_skill_vs_trend": float(1 - np.abs(e).mean() / np.abs(nv).mean()) if np.abs(nv).mean() > 0 else None,
            "note": "Hindcast só do componente clima+histórico (vigor histórico indisponível = adequado)."}


def _probs(p, labels):
    v = np.array([float((p or {}).get(k, 0.0)) for k in labels])
    if v.sum() <= 0 or np.any(v < 0):
        raise ValueError("probabilidades de classe inválidas")
    return v / v.sum()


def forecast_production(fields, target_year, *, n_mc=5000, seed=20261103):
    """Monte Carlo of P_AOI = Σ A_s ŷ_s with shared terms per microregion-crop.

    Each field: {id, crop, micro_code, area_ha, area_sd_ha?, yields{year:kg/ha},
    vigor_probs{class:p}, climate_probs{class:p}, hindcast{errors_kg_ha:[...]}?,
    transfer_sd_kg_ha?}.
    """
    rng = np.random.default_rng(seed)
    groups = {}
    for f in fields:
        if len(f["yields"]) < MIN_YEARS:
            raise ValueError(f"talhão {f['id']}: menos de {MIN_YEARS} anos PAM numéricos")
        groups.setdefault((f["micro_code"], f["crop"]), []).append(f)
    per_field = {f["id"]: np.empty(n_mc) for f in fields}
    total_t = np.zeros(n_mc)
    quantified = {"vigor": True, "climate": True, "baseline": True, "model_error": True,
                  "transfer": True, "area": True}
    for (micro, crop), members in groups.items():
        ref = members[0]
        yrs = np.array(sorted(ref["yields"])); vals = np.array([ref["yields"][y] for y in yrs])
        pc = _probs(ref["climate_probs"], CLIMATE)
        errs = np.asarray((ref.get("hindcast") or {}).get("errors_kg_ha") or [], float)
        tsd = ref.get("transfer_sd_kg_ha")
        quantified["model_error"] &= len(errs) > 0
        quantified["transfer"] &= tsd is not None
        for m in range(n_mc):
            idx = rng.integers(0, len(yrs), len(yrs))
            while len(set(yrs[idx])) < 2:
                idx = rng.integers(0, len(yrs), len(yrs))
            b, a = theil_sen(yrs[idx], vals[idx])
            det = vals[idx] - (a + b * yrs[idx]) + (a + b * target_year)
            c = rng.choice(3, p=pc)
            shared = (rng.choice(errs) if len(errs) else 0.0) + (rng.normal(0, tsd) if tsd else 0.0)
            for f in members:
                v = rng.choice(3, p=_probs(f["vigor_probs"], VIGOR))
                y = max(0.0, float(np.quantile(det, QUANTILE_MATRIX[v, c])) + shared)
                sd = f.get("area_sd_ha")
                area = max(0.0, rng.normal(f["area_ha"], sd)) if sd else f["area_ha"]
                per_field[f["id"]][m] = y
                total_t[m] += area * y / 1000.0
        quantified["area"] &= all(f.get("area_sd_ha") is not None for f in members)

    def summary(x):
        return {"mean": float(x.mean()), "median": float(np.median(x)),
                "p05": float(np.quantile(x, .05)), "p10": float(np.quantile(x, .10)),
                "p90": float(np.quantile(x, .90)), "p95": float(np.quantile(x, .95))}
    missing = [k for k, ok in quantified.items() if not ok]
    return {"status": "experimental", "target_year": target_year,
            "fields_kg_ha": {k: summary(v) for k, v in per_field.items()},
            "production_t": summary(total_t), "n_mc": n_mc,
            "uncertainty_sources_included": [k for k, ok in quantified.items() if ok],
            "uncertainty_sources_NOT_quantified": missing,
            "interval_note": ("Intervalo 90% (p05–p95) de Monte Carlo com dependências; "
                              + ("NÃO inclui: " + ", ".join(missing) + ". " if missing else "")
                              + "Não é IC calibrado até haver colheitas observadas.")}
