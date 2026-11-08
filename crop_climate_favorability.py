"""Seasonal climate favourability for a crop: "desfavorável", "neutro", "favorável".

Indices over the crop season window (daily NASA POWER grid data, or any
series with T2M_MAX, T2M_MIN, PRECTOTCORR):

* water deficit  D = Σ max(0, Kc·ET0 − P)  [mm]
  ET0 by Hargreaves–Samani (FAO-56 eq. 52) with extraterrestrial radiation
  Ra from FAO-56 eq. 21; Kc = mid-season value of FAO-56 Table 12.
* heat stress    H = number of days with Tmax above a crop threshold.

Both are standardised against the SAME calendar window in the reference
years (z = (x − mean)/sd). Composite F = −(z_D + z_H)/√2 (higher = more
favourable; independence assumed and stated). Classes are the empirical
terciles of F over the reference years.

Season still running: the unobserved days are filled with each reference
year's own data (analog ensemble), giving one F per analog year; the share
of analogs in each class is the class probability. This is how the climate
uncertainty of the rest of the season enters the yield model.
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

CLASSES = ("desfavorável", "neutro", "favorável")
KC_MID = {  # FAO-56 (Allen et al., 1998) Table 12, mid-season Kc
    "Soja": 1.15, "Milho": 1.20, "Sorgo": 1.05, "Feijão": 1.15, "Arroz": 1.20,
    "Café": 0.95, "Cana-de-açúcar": 1.25, "Citros": 0.65}
HEAT_TMAX_C = {  # ASSUMED stress thresholds — configurable, cite when calibrated
    "Soja": 35.0, "Milho": 35.0, "Sorgo": 38.0, "Feijão": 32.0, "Arroz": 35.0,
    "Café": 34.0, "Cana-de-açúcar": 38.0, "Citros": 38.0}
DEFAULT_SEASON = {  # generic Brazilian windows (MM-DD); replace by CONAB calendar of the UF
    "Soja": ("10-01", "02-28"), "Milho": ("10-01", "03-31"), "Sorgo": ("02-01", "06-30"),
    "Feijão": ("10-15", "01-31"), "Arroz": ("10-01", "03-15"), "Café": ("09-01", "04-30"),
    "Cana-de-açúcar": ("10-01", "09-30"), "Citros": ("08-01", "05-31")}
POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"


def extraterrestrial_radiation(lat_deg, doy):
    """FAO-56 eq. 21 (MJ m⁻² d⁻¹)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return 24 * 60 / math.pi * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))


def et0_hargreaves(tmax, tmin, lat_deg, doy):
    """FAO-56 eq. 52, Ra converted to mm/day by 0.408."""
    tmean = (tmax + tmin) / 2
    return 0.0023 * 0.408 * extraterrestrial_radiation(lat_deg, doy) * (tmean + 17.8) * math.sqrt(max(0.0, tmax - tmin))


def _season_dates(season_year, start_mmdd, end_mmdd):
    """season_year = calendar year in which the season STARTS."""
    s = date.fromisoformat(f"{season_year}-{start_mmdd}")
    e = date.fromisoformat(f"{season_year}-{end_mmdd}")
    if e < s:
        e = date.fromisoformat(f"{season_year + 1}-{end_mmdd}")
    return s, e


def season_indices(daily, crop, lat_deg):
    """daily: list of dicts {date: 'YYYYMMDD' or date, T2M_MAX, T2M_MIN, PRECTOTCORR}."""
    kc, thr = KC_MID[crop], HEAT_TMAX_C[crop]
    deficit = 0.0; heat = 0; n = 0
    for r in daily:
        tx, tn, p = r.get("T2M_MAX"), r.get("T2M_MIN"), r.get("PRECTOTCORR")
        if tx is None or tn is None or p is None:
            continue
        d = _rdate(r)
        deficit += max(0.0, kc * et0_hargreaves(tx, tn, lat_deg, d.timetuple().tm_yday) - p)
        heat += tx > thr; n += 1
    return {"water_deficit_mm": deficit, "heat_days": int(heat), "valid_days": n}


def _rdate(r):
    d = r["date"]
    return d if isinstance(d, date) else date(int(str(d)[:4]), int(str(d)[4:6]), int(str(d)[6:8]))


def _by_date(daily):
    return {_rdate(r): r for r in daily}


def _window(series, s, e):
    return [series[s + timedelta(days=k)] for k in range((e - s).days + 1) if s + timedelta(days=k) in series]


def favourability(daily_all, crop, lat_deg, target_season_year, reference_years, *,
                  season=None, as_of=None, min_coverage=0.9):
    """Class probabilities for the target season.

    daily_all: daily records covering the reference seasons and the target
    season up to ``as_of`` (inclusive). Reference years are season-start years.
    """
    if crop not in KC_MID:
        raise ValueError("cultura sem Kc/limiar configurado: " + str(crop))
    start_mmdd, end_mmdd = season or DEFAULT_SEASON[crop]
    series = _by_date(daily_all)
    ref = {}
    for y in reference_years:
        if y == target_season_year:
            continue
        s, e = _season_dates(y, start_mmdd, end_mmdd)
        w = _window(series, s, e)
        if len(w) >= min_coverage * ((e - s).days + 1):
            ref[y] = (s, w, season_indices(w, crop, lat_deg))
    if len(ref) < 8:
        return {"status": "N/D", "reason": "menos de 8 safras de referência com dados diários completos"}
    D = np.array([v[2]["water_deficit_mm"] for v in ref.values()])
    Hh = np.array([v[2]["heat_days"] for v in ref.values()], float)
    mD, sD = D.mean(), D.std(ddof=1) or 1.0
    mH, sH = Hh.mean(), Hh.std(ddof=1) or 1.0
    F = lambda d, h: -(((d - mD) / sD) + ((h - mH) / sH)) / math.sqrt(2)
    Fref = np.array([F(d, h) for d, h in zip(D, Hh)])
    t1, t2 = np.quantile(Fref, [1 / 3, 2 / 3])
    klass = lambda f: 0 if f < t1 else (2 if f > t2 else 1)

    s_t, e_t = _season_dates(target_season_year, start_mmdd, end_mmdd)
    as_of = min(as_of or e_t, e_t)
    observed = _window(series, s_t, as_of) if as_of >= s_t else []
    remaining_from = max(s_t, as_of + timedelta(days=1))
    analogs = []
    for y, (s_ref, w_ref, _) in ref.items():
        shift = s_ref - s_t
        fill = [r for r in w_ref if _rdate(r) - shift >= remaining_from]
        idx = season_indices(observed + fill, crop, lat_deg)
        analogs.append((y, F(idx["water_deficit_mm"], idx["heat_days"])))
    counts = np.bincount([klass(f) for _, f in analogs], minlength=3)
    probs = counts / counts.sum()
    obs_frac = len(observed) / ((e_t - s_t).days + 1)
    return {"status": "ok", "class": CLASSES[int(np.argmax(probs))],
            "probabilities": dict(zip(CLASSES, map(float, probs))),
            "season_window": [s_t.isoformat(), e_t.isoformat()], "as_of": as_of.isoformat(),
            "observed_fraction_of_season": obs_frac,
            "reference_years": sorted(ref), "reference_terciles_F": [float(t1), float(t2)],
            "reference_F_by_year": {int(y): float(f) for y, f in zip(ref, Fref)},
            "analog_F": {int(y): float(f) for y, f in analogs},
            "kc_mid": KC_MID[crop], "heat_threshold_c": HEAT_TMAX_C[crop],
            "method": ("F = −(z_déficit + z_calor)/√2 vs. mesma janela nas safras de referência; "
                       "tercis; dias não observados preenchidos por anos análogos"),
            "limitations": ("Grade NASA POWER no centroide (não estação); Hargreaves e Kc médio são "
                            "simplificações; limiares de calor assumidos; sem previsão sazonal CPTEC.")}


def fetch_power_daily(lat, lon, start, end, opener=urlopen):
    url = POWER_API + "?" + urlencode({"parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR", "community": "AG",
                                       "longitude": lon, "latitude": lat, "start": start.strftime("%Y%m%d"),
                                       "end": end.strftime("%Y%m%d"), "format": "JSON"})
    with opener(Request(url, headers={"User-Agent": "EnformVerde"}), timeout=120) as r:
        data = json.load(r)
    par = data["properties"]["parameter"]
    ok = lambda v: None if v is None or v <= -999 else float(v)
    days = sorted(par["PRECTOTCORR"])
    return {"source_url": url, "daily": [{"date": d, **{k: ok(par[k].get(d)) for k in par}} for d in days]}
