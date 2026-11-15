#!/usr/bin/env python3
"""Validate the Embrapa/PronaSolos 0–100 cm SOC stock map against soil profiles.

Observed stock per profile (no extrapolation, no pedotransfer by default):

    S_obs = Σ_l  C_l[g/kg] · BD_l[g/cm³] · (1 − CF_l) · t_l[cm] · 0.1   (Mg C/ha)

with layers clipped to 0–100 cm; the profile is accepted only if measured
layers cover 0–100 cm without gaps. Predicted stock S_map = sum of the five
Embrapa horizons at the profile's pixel (and the 3×3 mean, reported as a
positional-error sensitivity).

Independence and design (what the modular gate requires):
* profiles are grouped in 1°×1° spatial blocks (the independent unit);
* blocks are split deterministically into CALIBRATION and TEST halves;
* a split-conformal interval on the log ratio log(S_obs/S_map) is fitted on
  calibration blocks and its coverage measured on test blocks;
* bias/MAE/RMSE are computed on test-block means (n = number of test blocks),
  profile-level metrics are reported separately;
* a profile is "independent of the map" only if its dataset is declared NOT
  used in the Embrapa 2021 training AND the declaration has a source. Without
  that, the report is diagnostic: status "experimental", never "validated".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

REQUIRED = ("profile_id", "dataset_id", "lon", "lat", "upper_cm", "lower_cm",
            "soc_g_kg", "bd_g_cm3")


def profile_stock_0_100(layers):
    """layers: iterable of dicts with upper_cm, lower_cm, soc_g_kg, bd_g_cm3, cf_frac?"""
    ls = sorted(layers, key=lambda r: float(r["upper_cm"]))
    top, stock = 0.0, 0.0
    for r in ls:
        u, l = float(r["upper_cm"]), float(r["lower_cm"])
        if l <= top:
            continue
        if u > top + 1e-6:
            return None                      # gap → not accepted, no interpolation
        c, bd = float(r["soc_g_kg"]), float(r["bd_g_cm3"])
        cf = float(r.get("cf_frac") or 0.0)
        if not (c >= 0 and 0.1 <= bd <= 2.6 and 0 <= cf < 1):
            return None
        t = min(l, 100.0) - top
        stock += c * bd * (1 - cf) * t * 0.1
        top = min(l, 100.0)
        if top >= 100.0:
            return stock
    return None


def block_id(lon, lat):
    return f"{math.floor(lat)}_{math.floor(lon)}"


def split_blocks(blocks, seed="enform-soil-2026"):
    """Deterministic, content-independent 50/50 split by hashed block id."""
    cal, test = [], []
    for b in sorted(set(blocks)):
        h = int(hashlib.sha256((seed + b).encode()).hexdigest(), 16)
        (cal if h % 2 == 0 else test).append(b)
    return cal, test


def metrics(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    e = pred - obs
    ss = ((obs - obs.mean()) ** 2).sum()
    return {"n": int(len(obs)), "bias": float(e.mean()), "mae": float(np.abs(e).mean()),
            "rmse": float(np.sqrt((e ** 2).mean())),
            "r2": float(1 - (e ** 2).sum() / ss) if ss > 0 else None}


def validate(pairs, *, alpha=0.10, independence=None):
    """pairs: [{profile_id, dataset_id, lon, lat, obs, pred, pred3x3?}]."""
    pairs = [p for p in pairs if p["obs"] > 0 and p["pred"] > 0]
    if len(pairs) < 10:
        return {"status": "insufficient", "n_profiles": len(pairs),
                "reason": "menos de 10 perfis pareados válidos"}
    for p in pairs:
        p["block"] = block_id(p["lon"], p["lat"])
    cal_b, test_b = split_blocks([p["block"] for p in pairs])
    cal = [p for p in pairs if p["block"] in cal_b]
    test = [p for p in pairs if p["block"] in test_b]
    if len(cal_b) < 2 or len(test_b) < 2:
        return {"status": "insufficient", "n_profiles": len(pairs),
                "reason": "menos de 2 blocos de calibração ou de teste"}
    r = np.abs(np.log([p["obs"] / p["pred"] for p in cal]))
    k = math.ceil((len(r) + 1) * (1 - alpha))
    q = float(np.sort(r)[min(k, len(r)) - 1])
    inside = [p["pred"] * math.exp(-q) <= p["obs"] <= p["pred"] * math.exp(q) for p in test]
    by_block = {}
    for p in test:
        by_block.setdefault(p["block"], []).append(p)
    bo = [np.mean([p["obs"] for p in v]) for v in by_block.values()]
    bp = [np.mean([p["pred"] for p in v]) for v in by_block.values()]
    block_m = metrics(bo, bp)
    ind = independence or {}
    datasets = sorted({p["dataset_id"] for p in pairs})
    independent = bool(datasets) and all(
        ind.get(d, {}).get("used_in_map_training") is False and ind.get(d, {}).get("source")
        for d in datasets)
    return {
        "status": "independent_validation" if independent else "diagnostic_not_independent",
        "unit": "Mg C/ha (0–100 cm)",
        "validation_design": "split-conformal por blocos espaciais 1°×1°; métricas nos blocos de teste",
        "train_partition": "calibration_blocks", "test_partition": "test_blocks",
        "train_spatial_units": len(cal_b), "test_spatial_units": len(by_block),
        "train_spatial_unit_ids": cal_b, "test_spatial_unit_ids": sorted(by_block),
        "independent_sample_count": len(by_block),
        "bias": block_m["bias"], "mae": block_m["mae"], "rmse": block_m["rmse"], "r2": block_m["r2"],
        "interval_nominal": 1 - alpha, "interval_log_halfwidth": q,
        "interval_coverage": float(np.mean(inside)),
        "profile_level_test_metrics": metrics([p["obs"] for p in test], [p["pred"] for p in test]),
        "n_profiles": len(pairs), "datasets": datasets,
        "independence_declarations": {d: ind.get(d) for d in datasets},
        "positional_sensitivity_3x3": (metrics([p["obs"] for p in test], [p["pred3x3"] for p in test])
                                       if all(p.get("pred3x3") for p in test) else None),
    }


def wosis_screen(profiles, orgc, bdfiod, cfvo=None, *, max_position_error=("Circa 100 m",)):
    """Screen WoSIS-format tables (pandas) for profiles usable above."""
    import pandas as pd
    m = orgc.merge(bdfiod[["profile_id", "upper_depth", "lower_depth", "value_avg"]],
                   on=["profile_id", "upper_depth", "lower_depth"], suffixes=("_oc", "_bd"))
    if cfvo is not None and len(cfvo):
        m = m.merge(cfvo[["profile_id", "upper_depth", "lower_depth", "value_avg"]].rename(
            columns={"value_avg": "cf_pct"}), on=["profile_id", "upper_depth", "lower_depth"], how="left")
    out, reasons = [], {"sem_cobertura_0_100_com_BD_medida": 0, "erro_posicional_grande": 0}
    pos = profiles.set_index("profile_id")
    for pid, g in m.groupby("profile_id"):
        layers = [{"upper_cm": r.upper_depth, "lower_cm": r.lower_depth, "soc_g_kg": r.value_avg_oc,
                   "bd_g_cm3": r.value_avg_bd,
                   "cf_frac": (r.cf_pct / 100.0 if "cf_pct" in g and pd.notna(r.cf_pct) else 0.0)}
                  for r in g.itertuples()]
        s = profile_stock_0_100(layers)
        if s is None:
            reasons["sem_cobertura_0_100_com_BD_medida"] += 1; continue
        p = pos.loc[pid]
        if p.positional_uncertainty not in max_position_error:
            reasons["erro_posicional_grande"] += 1; continue
        out.append({"profile_id": str(pid), "dataset_id": p.dataset_code, "lon": float(p.longitude),
                    "lat": float(p.latitude), "obs": s, "year": p.year})
    return out, reasons


def pair_with_map(candidates, cache_dir=None):
    """Attach Embrapa 0–100 cm map values (pixel and 3×3 mean) via the official WCS."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import rasterio
    from shapely.geometry import box
    from pronasolos_wcs import PIXEL_DEG, fetch_horizons
    out = []
    for c in candidates:
        g = box(c["lon"] - 2 * PIXEL_DEG, c["lat"] - 2 * PIXEL_DEG, c["lon"] + 2 * PIXEL_DEG, c["lat"] + 2 * PIXEL_DEG)
        try:
            got = fetch_horizons(g, cache_dir=cache_dir)
        except Exception as exc:
            out.append(dict(c, pred=None, pair_error=type(exc).__name__)); continue
        total = None
        for lid in sorted(got["paths"]):
            with rasterio.open(got["paths"][lid]) as src:
                a = src.read(1).astype(float); a[a < 0] = np.nan
                r, k = src.index(c["lon"], c["lat"])
                total = a if total is None else total + a
        win = total[max(0, r - 1):r + 2, max(0, k - 1):k + 2]
        out.append(dict(c, pred=float(total[r, k]) if np.isfinite(total[r, k]) else None,
                        pred3x3=float(np.nanmean(win)) if np.isfinite(win).any() else None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wosis-dir", required=True, help="profiles.zip, orgc.zip, bdfiod.zip, cfvo.zip")
    ap.add_argument("--report", default="soil_0_100_validation_report.json")
    a = ap.parse_args()
    import io, zipfile
    import pandas as pd
    root = Path(a.wosis_dir); tables, digests = {}, {}
    for t in ("profiles", "orgc", "bdfiod", "cfvo"):
        raw = (root / f"{t}.zip").read_bytes(); digests[t] = hashlib.sha256(raw).hexdigest()
        z = zipfile.ZipFile(io.BytesIO(raw)); n = [x for x in z.namelist() if x.endswith(".csv")][0]
        d = pd.read_csv(io.BytesIO(z.read(n)), low_memory=False)
        tables[t] = d[d.country_name == "Brazil"]
    cand, reasons = wosis_screen(tables["profiles"], tables["orgc"], tables["bdfiod"], tables["cfvo"])
    report = {"source": "ISRIC WoSIS latest (WFS)", "inputs_sha256": digests,
              "brazil_profiles": int(len(tables["profiles"])),
              "eligible_profiles": len(cand),
              "rejections": dict(reasons, sem_densidade_medida_em_camada_com_carbono=int(
                  len(tables["profiles"]) - len(cand) - sum(reasons.values()))),
              "eligible_datasets": sorted({c["dataset_id"] for c in cand})}
    paired = pair_with_map(cand) if cand else []
    report["paired_profiles"] = sum(1 for p in paired if p.get("pred"))
    report["validation"] = (validate([p for p in paired if p.get("pred")]) if len(cand) >= 10 else
                            {"status": "insufficient", "reason": "menos de 10 perfis elegíveis"})
    Path(a.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
