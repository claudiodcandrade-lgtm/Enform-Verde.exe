#!/usr/bin/env python3
"""Build data/models/yield_panel_v1.json from PAM (N9) + NASA POWER + PronaSolos AWC.

Reproducible: top-N producing microregions per crop (PAM 2015–2024), five
points per microregion, three sowing dates, FAO-56/FAO-33 relative yield,
pooled β per region group, leave-one-year-out validation.
"""
import argparse, collections, csv, gzip, json, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from crop_climate_favorability import fetch_power_daily  # noqa: E402
from crop_panel_yield_model import ARTIFACT, calibrate, file_sha  # noqa: E402
from crop_water_balance_yield import SOURCES, awc_at, harvest_year, season_ry  # noqa: E402
from crop_yield_scenario import MICRO_PATH, PAM_PATH, PRODUCT_KEY, load_microregion_yields  # noqa: E402


def points(geom):
    minx, miny, maxx, maxy = geom.bounds
    out = [geom.representative_point()]
    for fx, fy in ((.3, .3), (.7, .3), (.3, .7), (.7, .7)):
        p = Point(minx + fx * (maxx - minx), miny + fy * (maxy - miny))
        if geom.contains(p):
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", default="Soja,Milho"); ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--first-season", type=int, default=2013); ap.add_argument("--last-season", type=int, default=2024)
    a = ap.parse_args()
    micro = {f["properties"]["CD_MICRO"]: f for f in json.load(gzip.open(MICRO_PATH))["features"]}
    panels, awc_log = {}, {}
    for crop in a.crops.split(","):
        prod = collections.defaultdict(float)
        with gzip.open(PAM_PATH, "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["product_key"] == PRODUCT_KEY[crop] and r["variable_code"] == "214" and r["observation_status"] == "numeric":
                    prod[r["territory_code"]] += float(r["value_numeric"])
        codes = [c for c, _ in sorted(prod.items(), key=lambda x: -x[1])[:a.top] if c in micro]

        def unit(code):
            y = load_microregion_yields(crop, code)
            if len(y) < 8:
                return None
            rys = collections.defaultdict(list)
            for p in points(shape(micro[code]["geometry"])):
                wx = fetch_power_daily(p.y, p.x, date(a.first_season, 9, 1), date(a.last_season + 1, 8, 31))["daily"]
                aw = awc_at(p.y, p.x); awc_log[f"{crop}:{code}:{p.y:.3f},{p.x:.3f}"] = aw
                for sy in range(a.first_season, a.last_season + 1):
                    r = season_ry(wx, crop, p.y, sy, aw["awc_mm_cm"])
                    if r:
                        rys[harvest_year(crop, p.y, sy)].append(r["ry"])
            return code, {"uf": micro[code]["properties"]["SIGLA"], "name": micro[code]["properties"]["NM_MICRO"],
                          "yields": y, "ry": {k: float(np.mean(v)) for k, v in rys.items()}}
        with ThreadPoolExecutor(6) as ex:
            panels[crop] = dict(u for u in ex.map(unit, codes) if u)
    prov = {"built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pam_file_sha256": file_sha(PAM_PATH), "microregions_file_sha256": file_sha(MICRO_PATH),
            "weather": "NASA POWER daily (T2M_MAX, T2M_MIN, PRECTOTCORR), 5 pontos/microrregião",
            "awc": "Embrapa/PronaSolos Água Disponível (mm/cm); fallback 1,0 mm/cm registrado",
            "awc_fallback_points": sum(1 for v in awc_log.values() if v["source"].startswith("fallback")),
            "awc_points": len(awc_log), "methods": SOURCES,
            "seasons": [a.first_season, a.last_season], "top_microregions": a.top}
    art = calibrate(panels, prov)
    art["panel_units"] = {crop: {c: {k: u[k] for k in ("uf", "name")} for c, u in p.items()} for crop, p in panels.items()}
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    for crop, groups in art["crops"].items():
        for g, m in groups.items():
            l = m["loyo"]
            print(crop, g, "units", l["units"], "beta", round(m["beta_kg_ha_per_RY"]), "MAE", round(l["mae_kg_ha"]),
                  "trend-only", round(l["trend_only_mae_kg_ha"]), "skill", round(l["skill_vs_trend"], 3),
                  "improved", f'{l["units_improved"]}/{l["units"]}')


if __name__ == "__main__":
    main()
