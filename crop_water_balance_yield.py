"""Data-calibrated crop water-balance yield model (scientifically established methods).

Model chain, all from recognised references:
1. Daily soil-water balance, FAO-56 single crop coefficient (Allen et al., 1998):
   ETc = Kc(t)·ET0, Ks = (TAW − Dr)/((1 − p)·TAW) when Dr > RAW, ETa = Ks·ETc;
   ET0 Hargreaves (eq. 52), Kc curve and stage lengths (Tables 11–12),
   rooting depth Zr and depletion fraction p (Table 22).
2. Available water capacity of the soil: Embrapa/PronaSolos "Água disponível"
   (mm per cm of soil) at the field, TAW = AD·Zr. Fallback 1.0 mm/cm, flagged.
3. Relative yield by stage, Doorenbos & Kassam (1979, FAO Irrigation and
   Drainage Paper 33), multiplicative form:
       Ya/Ym = Π_i [1 − Ky_i (1 − ETa_i/ETm_i)]
   and the ISNA/WRSI = ΣETa/ΣETm (Frère & Popov 1979; the water-satisfaction
   index used by Embrapa/MAPA in ZARC).
4. Sowing date unknown → ensemble of sowing dates inside the regional window.
5. CALIBRATION ON HISTORY (data-driven): detrended microregional PAM yield
   is regressed on the modelled relative yield,
       y_t = trend(t) + β·(RY_t − mean RY) + ε_t,
   with β and the error distribution estimated by leave-one-year-out, so the
   reported skill is out-of-sample.
Coefficients marked "FAO" are literature values to be re-checked against the
original tables and refined by the calibration above.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np

from crop_climate_favorability import _by_date, et0_hargreaves

# Kc (ini, mid, end); stage lengths days (ini, dev, mid, late); Ky (veg, flowering,
# yield formation, ripening); Zr (m, lower bound of FAO-56 Table 22); p.
CROP = {
    "Soja":   {"kc": (0.40, 1.15, 0.50), "len": (20, 30, 60, 25), "ky": (0.2, 0.8, 1.0, 0.2), "zr": 0.6, "p": 0.50},
    "Milho":  {"kc": (0.30, 1.20, 0.60), "len": (30, 40, 50, 30), "ky": (0.4, 1.5, 0.5, 0.2), "zr": 1.0, "p": 0.55},
    "Sorgo":  {"kc": (0.30, 1.05, 0.55), "len": (20, 35, 40, 30), "ky": (0.2, 0.55, 0.45, 0.2), "zr": 1.0, "p": 0.55},
    "Feijão": {"kc": (0.40, 1.15, 0.35), "len": (20, 30, 40, 20), "ky": (0.2, 1.1, 0.75, 0.2), "zr": 0.6, "p": 0.45},
}
SOURCES = ("Allen et al. (1998) FAO-56, Tabelas 11, 12 e 22; Doorenbos & Kassam (1979) FAO-33 (Ky); "
           "Frère & Popov (1979) e ZARC Embrapa/MAPA (ISNA); Embrapa/PronaSolos Água Disponível (mm/cm).")
AWC_SERVICE = "https://geoportal.sgb.gov.br/server/rest/services/pronasolos/agua_disponivel/MapServer/0/query"
DEFAULT_AWC_MM_CM = 1.0


def sowing_dates(crop, lat, season_year):
    """Ensemble of sowing dates; season_year = calendar year in which the
    agricultural year starts (Sep). ASSUMED regional windows — replace by the
    ZARC portaria of the municipality when available."""
    south = lat < -25.0
    windows = {  # (month, day, year offset)
        "Soja": (11, 1, 0) if south else (10, 1, 0),
        "Milho": (9, 20, 0) if south else (2, 1, 1),     # outside the South: 2nd crop (safrinha)
        "Feijão": (10, 15, 0) if south else (11, 1, 0),
        "Sorgo": (2, 1, 1),
    }
    m, d, off = windows[crop]
    d0 = date(season_year + off, m, d)
    return [d0 + timedelta(days=k) for k in (0, 15, 30)]


def awc_at(lat, lon, session=None):
    import requests
    s = session or requests.Session()
    try:
        r = s.get(AWC_SERVICE, params={"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
                                       "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                                       "outFields": "total_ad,legad,textura", "returnGeometry": "false",
                                       "f": "json"}, timeout=(5, 20))
        feats = r.json().get("features") or []
        v = float(feats[0]["attributes"]["total_ad"]) if feats else 0.0
        if v > 0:
            return {"awc_mm_cm": v, "source": "Embrapa/PronaSolos Água Disponível", "legend": feats[0]["attributes"].get("legad")}
    except Exception as exc:  # network/service error → explicit fallback
        return {"awc_mm_cm": DEFAULT_AWC_MM_CM, "source": "fallback (serviço indisponível: " + type(exc).__name__ + ")"}
    return {"awc_mm_cm": DEFAULT_AWC_MM_CM, "source": "fallback (sem polígono de solo no ponto)"}


def _kc(crop, day):
    kc_ini, kc_mid, kc_end = CROP[crop]["kc"]
    l1, l2, l3, l4 = CROP[crop]["len"]
    if day < l1:
        return kc_ini
    if day < l1 + l2:
        return kc_ini + (kc_mid - kc_ini) * (day - l1) / l2
    if day < l1 + l2 + l3:
        return kc_mid
    return kc_mid + (kc_end - kc_mid) * (day - l1 - l2 - l3) / l4


def _stage(crop, day):
    l1, l2, l3, l4 = CROP[crop]["len"]
    # FAO-33 stages: vegetative = ini+dev; flowering = first third of mid;
    # yield formation = rest of mid; ripening = late
    if day < l1 + l2:
        return 0
    if day < l1 + l2 + l3 / 3:
        return 1
    if day < l1 + l2 + l3:
        return 2
    return 3


def simulate(series, crop, sow, lat, awc_mm_cm, *, initial_fraction=1.0,
             infiltration_fraction=1.0):
    """series: {date: record}. Returns RY (Doorenbos–Kassam) and ISNA, or None if data missing."""
    c = CROP[crop]
    total = sum(c["len"])
    taw = awc_mm_cm * c["zr"] * 100.0           # mm/cm × cm
    raw = c["p"] * taw
    if not (0 <= initial_fraction <= 1 and 0 <= infiltration_fraction <= 1):
        raise ValueError("initial water and infiltration fractions must be within [0,1]")
    dr = taw * (1 - initial_fraction)             # FAO-56 root-zone depletion at planting
    eta = np.zeros(4); etm = np.zeros(4)
    for k in range(total):
        d = sow + timedelta(days=k)
        r = series.get(d)
        if r is None or r.get("T2M_MAX") is None or r.get("T2M_MIN") is None or r.get("PRECTOTCORR") is None:
            return None
        et0 = et0_hargreaves(r["T2M_MAX"], r["T2M_MIN"], lat, d.timetuple().tm_yday)
        etc = _kc(crop, k) * et0
        ks = 1.0 if dr <= raw else max(0.0, (taw - dr) / ((1 - c["p"]) * taw))
        a = ks * etc
        st = _stage(crop, k)
        eta[st] += a; etm[st] += etc
        dr = min(taw, max(0.0, dr - infiltration_fraction * r["PRECTOTCORR"] + a))
        # The infiltrated fraction is a sensitivity assumption, not measured runoff.
    ratio = np.where(etm > 0, eta / etm, 1.0)
    ry = float(np.prod([max(0.0, 1 - ky * (1 - x)) for ky, x in zip(c["ky"], ratio)]))
    return {"ry": ry, "isna": float(eta.sum() / etm.sum()), "eta_etm_by_stage": ratio.round(3).tolist()}


def season_ry(daily, crop, lat, season_year, awc_mm_cm):
    series = _by_date(daily)
    sims = [simulate(series, crop, s, lat, awc_mm_cm) for s in sowing_dates(crop, lat, season_year)]
    sims = [s for s in sims if s]
    if not sims:
        return None
    return {"ry": float(np.mean([s["ry"] for s in sims])), "isna": float(np.mean([s["isna"] for s in sims])),
            "n_sowings": len(sims)}


def harvest_year(crop, lat, season_year):
    last = max(sowing_dates(crop, lat, season_year))
    return (last + timedelta(days=sum(CROP[crop]["len"]))).year


def _theil(x, y):
    from crop_yield_scenario import theil_sen
    return theil_sen(x, y)


def calibrate_hindcast(yields, ry_by_harvest_year):
    """Leave-one-year-out: out-of-sample skill vs trend-only (same detrending)."""
    years = sorted(set(yields) & set(ry_by_harvest_year))
    errs, naive, betas = [], [], []
    for t in years:
        tr = [y for y in years if y != t]
        if len(tr) < 5:
            continue
        b, a = _theil(tr, [yields[y] for y in tr])
        res = np.array([yields[y] - (a + b * y) for y in tr])
        ry = np.array([ry_by_harvest_year[y] for y in tr]); m = ry.mean()
        den = ((ry - m) ** 2).sum()
        beta = float(((ry - m) * res).sum() / den) if den > 0 else 0.0
        betas.append(beta)
        pred = a + b * t + beta * (ry_by_harvest_year[t] - m)
        errs.append(yields[t] - pred); naive.append(yields[t] - (a + b * t))
    if not errs:
        return {"n": 0}
    e, nv = np.array(errs), np.array(naive)
    return {"n": int(len(e)), "mae_kg_ha": float(np.abs(e).mean()), "rmse_kg_ha": float(np.sqrt((e ** 2).mean())),
            "bias_kg_ha": float(e.mean()), "trend_only_mae_kg_ha": float(np.abs(nv).mean()),
            "skill_vs_trend": float(1 - np.abs(e).mean() / np.abs(nv).mean()) if np.abs(nv).mean() else None,
            "beta_kg_ha_per_unit_ry": {"median": float(np.median(betas)), "min": float(min(betas)), "max": float(max(betas))},
            "errors_kg_ha": e.tolist()}


def forecast(yields, ry_hist, ry_target_ensemble, target_year, *, quantiles=(.05, .5, .95)):
    """Full-history fit; predictive samples = fit(RY analog) + LOYO errors."""
    years = sorted(set(yields) & set(ry_hist))
    b, a = _theil(years, [yields[y] for y in years])
    res = np.array([yields[y] - (a + b * y) for y in years])
    ry = np.array([ry_hist[y] for y in years]); m = ry.mean()
    beta = float(((ry - m) * res).sum() / ((ry - m) ** 2).sum())
    hc = calibrate_hindcast(yields, ry_hist)
    errs = np.asarray(hc.get("errors_kg_ha") or [0.0])
    samples = np.array([a + b * target_year + beta * (r - m) + e for r in ry_target_ensemble for e in errs])
    samples = np.clip(samples, 0, None)
    return {"quantiles_kg_ha": {f"p{int(q*100):02d}": float(np.quantile(samples, q)) for q in quantiles},
            "mean_kg_ha": float(samples.mean()), "beta": beta, "trend_kg_ha_yr": b, "hindcast": hc,
            "n_samples": int(len(samples)), "status": "experimental_calibrated_on_history",
            "sources": SOURCES}
