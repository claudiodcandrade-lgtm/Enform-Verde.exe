"""Panel yield model calibrated on historical data (experimental, validated out-of-sample).

For microregion u and harvest year t (IBGE PAM, SIDRA 5457, N9):

    y_ut = a_u + b_u·t + β_g · RY_ut + ε_ut

* RY_ut: Doorenbos–Kassam relative yield from the FAO-56 water balance
  (crop_water_balance_yield), averaged over 5 points of the microregion and
  3 sowing dates, Embrapa/PronaSolos available water, NASA POWER weather.
* a_u + b_u·t: microregion-specific technology trend (fixed effects).
* β_g: ONE coefficient pooled over all microregions of region group g
  (Sul = PR/SC/RS; Centro-Norte = others), estimated by Frisch–Waugh
  (trend partialled out of y and RY jointly) — the standard panel
  crop-weather regression design (e.g. Lobell et al. 2011, Science 333:616;
  Schlenker & Roberts 2009, PNAS 106:15594).
* Validation: leave-one-YEAR-out across all microregions (a whole season is
  withheld), skill = 1 − MAE_model / MAE_trend-only.

Vigor (three classes, experimental) conditions the residual: baixo → lower
third of the out-of-sample errors, adequado → middle third, alto → upper
third, weighted by the vigor probabilities. Low vigor + low RY therefore
lands near the microregional floor, as required, but now through a model
whose climate part is calibrated on history.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "data" / "models" / "yield_panel_v1.json"
SOUTH = {"PR", "SC", "RS"}
VIGOR = ("baixo vigor", "vigor adequado", "alto vigor")


def region_group(uf):
    return "Sul" if uf in SOUTH else "Centro-Norte"


def _detrend(t, v):
    X = np.column_stack([np.ones(len(t)), t])
    c, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ c, c


def fit_beta(units):
    """units: [(code, years array, y array, ry array)] → pooled β (Frisch–Waugh)."""
    R, Y = [], []
    for _, t, y, r in units:
        R.append(_detrend(t, r)[0]); Y.append(_detrend(t, y)[0])
    R = np.concatenate(R); Y = np.concatenate(Y)
    return float((R * Y).sum() / (R * R).sum())


def unit_trend(t, y, r, beta):
    X = np.column_stack([np.ones(len(t)), t])
    c, *_ = np.linalg.lstsq(X, y - beta * r, rcond=None)
    return float(c[0]), float(c[1])


def _arrays(y, ry, drop=None):
    ks = np.array(sorted(k for k in y if k in ry and k != drop), float)
    return ks, np.array([y[int(k)] for k in ks]), np.array([ry[int(k)] for k in ks])


def loyo(panel):
    """panel: {code: {"uf", "yields":{yr:kg/ha}, "ry":{yr:RY}}} of ONE region group."""
    years = sorted({y for u in panel.values() for y in u["yields"]})
    errs, naive, per_unit = [], [], {}
    for t in years:
        units = []
        for code, u in panel.items():
            ks, y, r = _arrays(u["yields"], u["ry"], drop=t)
            if len(ks) >= 6 and t in u["yields"] and t in u["ry"]:
                units.append((code, ks, y, r))
        if len(units) < 3:
            continue
        beta = fit_beta(units)
        for code, ks, y, r in units:
            a, b = unit_trend(ks, y, r, beta)
            obs = panel[code]["yields"][t]
            e = obs - (a + b * t + beta * panel[code]["ry"][t])
            c0 = np.polyfit(ks, y, 1); n = obs - np.polyval(c0, t)
            errs.append(e); naive.append(n)
            per_unit.setdefault(code, []).append((e, n))
    e, n = np.array(errs), np.array(naive)
    improved = sum(np.mean([abs(a) for a, _ in v]) < np.mean([abs(b) for _, b in v]) for v in per_unit.values())
    return {"n": int(len(e)), "units": len(per_unit), "units_improved": int(improved),
            "mae_kg_ha": float(np.abs(e).mean()), "rmse_kg_ha": float(np.sqrt((e ** 2).mean())),
            "bias_kg_ha": float(e.mean()), "trend_only_mae_kg_ha": float(np.abs(n).mean()),
            "skill_vs_trend": float(1 - np.abs(e).mean() / np.abs(n).mean()),
            "errors_kg_ha": e.round(1).tolist()}


def calibrate(panels_by_crop, provenance):
    """panels_by_crop: {crop: {code: unit}} → artifact dict (β, trends, LOYO metrics)."""
    art = {"model": "panel y = a_u + b_u t + beta_g RY", "version": 1, "provenance": provenance, "crops": {}}
    for crop, panel in panels_by_crop.items():
        art["crops"][crop] = {}
        for g in ("Sul", "Centro-Norte"):
            sub = {c: u for c, u in panel.items() if region_group(u["uf"]) == g}
            if len(sub) < 3:
                continue
            units = [(c,) + _arrays(u["yields"], u["ry"]) for c, u in sub.items()]
            beta = fit_beta(units)
            trends = {c: unit_trend(ks, y, r, beta) for c, ks, y, r in units}
            art["crops"][crop][g] = {"beta_kg_ha_per_RY": beta, "unit_trends": trends,
                                     "unit_mean_ry": {c: float(np.mean(r)) for c, _, _, r in units},
                                     "loyo": loyo(sub)}
    return art


def load_artifact(path=ARTIFACT):
    import sys
    p = Path(getattr(sys, "_MEIPASS", ROOT)) / "data" / "models" / Path(path).name
    p = p if p.is_file() else Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def season_ry_ensemble(daily, crop, lat, season_year, awc_mm_cm, as_of, reference_years):
    """RY for the running season: observed days + each reference year's remaining days."""
    from crop_climate_favorability import _by_date
    from crop_water_balance_yield import CROP, simulate, sowing_dates
    series = _by_date(daily)
    out = []
    for ry_year in reference_years:
        shift = date(ry_year, 1, 1) - date(season_year, 1, 1)
        merged = dict(series)
        for s in sowing_dates(crop, lat, season_year):
            for k in range(sum(CROP[crop]["len"])):
                d = s + timedelta(days=k)
                if d > as_of:
                    merged[d] = series.get(d + shift) or merged.get(d)
        sims = [simulate(merged, crop, s, lat, awc_mm_cm) for s in sowing_dates(crop, lat, season_year)]
        sims = [x["ry"] for x in sims if x]
        if sims:
            out.append(float(np.mean(sims)))
    return out


def field_params(artifact, crop, micro_code, uf, yields, ry_ensemble, harvest_year, vigor_probs=None):
    g = region_group(uf)
    m = (artifact or {}).get("crops", {}).get(crop, {}).get(g)
    if not m:
        return {"status": "N/D", "reason": f"sem modelo calibrado para {crop}/{g}"}
    beta = m["beta_kg_ha_per_RY"]
    if micro_code in m["unit_trends"]:
        a, b = m["unit_trends"][micro_code]; trend_src = "calibrado no painel"
    else:
        if len(yields) < 6:
            return {"status": "N/D", "reason": "histórico PAM insuficiente"}
        ks = np.array(sorted(yields), float); y = np.array([yields[int(k)] for k in ks])
        b, a = (float(v) for v in np.polyfit(ks, y, 1))
        trend_src = "tendência própria + β do grupo (transferência não validada)"
    if not ry_ensemble:
        return {"status": "N/D", "reason": "balanço hídrico sem dados meteorológicos suficientes"}
    pv = np.array([float((vigor_probs or {}).get(k, 0)) for k in VIGOR])
    return {"status": "ok", "region_group": g, "a": a, "b": b, "beta": beta, "trend_source": trend_src,
            "harvest_year": harvest_year, "ry": np.asarray(ry_ensemble, float),
            "errors": np.sort(np.asarray(m["loyo"]["errors_kg_ha"], float)),
            "vigor": (pv / pv.sum()) if pv.sum() > 0 else None,
            "loyo": {k: v for k, v in m["loyo"].items() if k != "errors_kg_ha"}}


def simulate(fields, n=4000, seed=20261103):
    """fields: [{id, area_ha, area_sd_ha?, group, params}] → per-field and total samples.

    Shared per group (microregion × crop): the RY analog draw and the
    position u in the historical error distribution (comonotonic); per field:
    the vigor class (selects the third of the errors) and the area error.
    """
    rng = np.random.default_rng(seed)
    per = {f["id"]: np.empty(n) for f in fields}
    total = np.zeros(n)
    groups = {}
    for f in fields:
        groups.setdefault(f["group"], []).append(f)
    for i in range(n):
        for members in groups.values():
            p0 = members[0]["params"]
            ry = p0["ry"][rng.integers(len(p0["ry"]))]
            u = rng.random()
            for f in members:
                p = f["params"]
                errs = p["errors"]
                if p["vigor"] is not None:
                    part = np.array_split(errs, 3)[rng.choice(3, p=p["vigor"])]
                else:
                    part = errs
                e = part[min(len(part) - 1, int(u * len(part)))]
                y = max(0.0, p["a"] + p["b"] * p["harvest_year"] + p["beta"] * ry + e)
                sd = f.get("area_sd_ha")
                area = max(0.0, rng.normal(f["area_ha"], sd)) if sd else f["area_ha"]
                per[f["id"]][i] = y
                total[i] += area * y / 1000.0
    s = lambda x: {"median": float(np.median(x)), "p05": float(np.quantile(x, .05)),
                   "p95": float(np.quantile(x, .95)), "mean": float(x.mean())}
    return {"fields_kg_ha": {k: s(v) for k, v in per.items()}, "production_t": s(total), "n": n}


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
