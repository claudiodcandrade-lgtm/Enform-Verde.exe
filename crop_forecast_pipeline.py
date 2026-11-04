"""End-to-end experimental yield forecast for identified crop fields.

Order enforced: (1) crop identified by a usable identifier (crop_model_priority);
(2) vigor class with probabilities (crop_vigor); (3) dynamic climate
favourability (crop_climate_favorability); (4) microregional PAM history and
leave-one-year-out hindcast; (5) Monte Carlo production (crop_yield_scenario).
Any missing step returns N/D with its reason — never a default yield.
"""
from __future__ import annotations

from datetime import date, timedelta

from crop_climate_favorability import DEFAULT_SEASON, favourability, fetch_power_daily
from crop_yield_scenario import (MIN_YEARS, forecast_production, hindcast_errors,
                                 load_microregion_yields, microregion_of, scenario_table)


def _season_start_year(crop, as_of, season):
    start_mmdd = (season or DEFAULT_SEASON[crop])[0]
    s = date.fromisoformat(f"{as_of.year}-{start_mmdd}")
    return as_of.year if as_of >= s else as_of.year - 1


def _panel_season_year(crop, lat, as_of):
    """Agricultural year whose crop is running or next to be sown at ``as_of``."""
    from crop_water_balance_yield import CROP, sowing_dates
    for sy in (as_of.year - 2, as_of.year - 1, as_of.year):
        end = max(sowing_dates(crop, lat, sy)) + timedelta(days=sum(CROP[crop]["len"]))
        if end >= as_of:
            return sy
    return as_of.year


def forecast_fields(fields, *, as_of=None, season=None, weather_fetcher=fetch_power_daily,
                    first_reference_year=2000, n_mc=5000, model="auto", artifact=None, awc_fetcher=None):
    """fields: [{id, gdf, crop, identification{label_allowed,...}, vigor{status,probabilities},
    area_ha, area_sd_ha?}] — all of the same crop calendar.

    model="auto": calibrated panel model (crop_panel_yield_model) whenever the
    crop has a calibrated artifact; otherwise the uncalibrated scenario matrix.
    """
    as_of = as_of or (date.today() - timedelta(days=3))
    if model in ("auto", "panel"):
        from crop_panel_yield_model import load_artifact
        art = artifact if artifact is not None else load_artifact()
        crops = {f["crop"] for f in fields}
        if art and all(c in art.get("crops", {}) for c in crops):
            return _forecast_panel(fields, art, as_of, weather_fetcher, first_reference_year, n_mc, awc_fetcher)
        if model == "panel":
            raise ValueError("modelo calibrado indisponível para " + ", ".join(sorted(crops)))
    ready, report = [], {"fields": {}, "status": "ok"}
    for f in fields:
        rid = f["id"]; crop = f["crop"]
        ident = f.get("identification") or {}
        if not ident.get("label_allowed"):
            report["fields"][rid] = {"status": "N/D", "reason": "cultura não identificada por identificador utilizável"}
            continue
        vig = f.get("vigor") or {}
        if vig.get("status") not in ("experimental", "validated"):
            report["fields"][rid] = {"status": "N/D", "reason": "vigor N/D: " + str(vig.get("reason", ""))}
            continue
        micro = microregion_of(f["gdf"])["dominant"]
        yields = load_microregion_yields(crop, micro["code"])
        if len(yields) < MIN_YEARS:
            report["fields"][rid] = {"status": "N/D", "reason": f"PAM com menos de {MIN_YEARS} anos numéricos"}
            continue
        c = f["gdf"].to_crs(4326).geometry.union_all().centroid
        sy = _season_start_year(crop, as_of, season)
        wx = weather_fetcher(c.y, c.x, date(first_reference_year, 1, 1), as_of)
        fav = favourability(wx["daily"], crop, c.y, sy, range(first_reference_year, sy),
                            season=season, as_of=as_of)
        if fav["status"] != "ok":
            report["fields"][rid] = {"status": "N/D", "reason": fav["reason"]}
            continue
        harvest_year = sy + 1 if fav["season_window"][1][:4] != str(sy) else sy
        offset = harvest_year - sy
        hc = hindcast_errors(yields, {y + offset: v for y, v in fav["reference_F_by_year"].items()})
        ready.append({"id": rid, "crop": crop, "micro_code": micro["code"], "area_ha": f["area_ha"],
                      "area_sd_ha": f.get("area_sd_ha"), "yields": yields,
                      "vigor_probs": vig["probabilities"], "climate_probs": fav["probabilities"],
                      "hindcast": hc, "transfer_sd_kg_ha": f.get("transfer_sd_kg_ha")})
        report["fields"][rid] = {"status": "experimental", "microregion": micro, "pam_years": sorted(yields),
                                 "vigor": vig, "climate": fav, "hindcast": hc,
                                 "scenarios": scenario_table(yields, harvest_year),
                                 "harvest_year": harvest_year, "weather_source": wx.get("source_url")}
    if not ready:
        report["status"] = "N/D"
        return report
    years = {report["fields"][f["id"]]["harvest_year"] for f in ready}
    if len(years) != 1:
        raise ValueError("talhões com anos-safra diferentes não podem ser somados")
    report["production"] = forecast_production(ready, years.pop(), n_mc=n_mc)
    return report


def _forecast_panel(fields, art, as_of, weather_fetcher, first_ref, n_mc, awc_fetcher):
    from crop_panel_yield_model import field_params, season_ry_ensemble, simulate
    from crop_water_balance_yield import awc_at, harvest_year
    awc_fetcher = awc_fetcher or awc_at
    report = {"fields": {}, "status": "ok", "model": "panel",
              "model_label": "Modelo de painel calibrado no histórico PAM (balanço hídrico FAO-56/FAO-33)"}
    ready = []
    for f in fields:
        rid, crop = f["id"], f["crop"]
        if not (f.get("identification") or {}).get("label_allowed"):
            report["fields"][rid] = {"status": "N/D", "reason": "cultura não identificada por identificador utilizável"}
            continue
        vig = f.get("vigor") or {}
        vig_ok = vig.get("status") in ("experimental", "validated")
        micro_all = microregion_of(f["gdf"]); micro = micro_all["dominant"]
        yields = load_microregion_yields(crop, micro["code"])
        c = f["gdf"].to_crs(4326).geometry.union_all().centroid
        sy = _panel_season_year(crop, c.y, as_of)
        wx = weather_fetcher(c.y, c.x, date(first_ref, 9, 1), as_of)
        aw = awc_fetcher(c.y, c.x)
        ens = season_ry_ensemble(wx["daily"], crop, c.y, sy, aw["awc_mm_cm"], as_of, range(first_ref, sy))
        hy = harvest_year(crop, c.y, sy)
        params = field_params(art, crop, micro["code"], micro["uf"], yields, ens, hy,
                              vig.get("probabilities") if vig_ok else None)
        if params["status"] != "ok":
            report["fields"][rid] = {"status": "N/D", "reason": params["reason"]}
            continue
        ready.append({"id": rid, "area_ha": f["area_ha"], "area_sd_ha": f.get("area_sd_ha"),
                      "group": (micro["code"], crop), "params": params})
        report["fields"][rid] = {"status": "experimental_validated_out_of_sample", "microregion": micro,
                                 "harvest_year": hy, "awc": aw, "ry_median": float(sorted(ens)[len(ens) // 2]),
                                 "ry_p10_p90": [float(x) for x in __import__("numpy").quantile(ens, [.1, .9])],
                                 "n_analogs": len(ens), "region_group": params["region_group"],
                                 "beta": params["beta"], "trend_source": params["trend_source"],
                                 "loyo": params["loyo"], "vigor": vig if vig_ok else None,
                                 "weather_source": wx.get("source_url")}
    if not ready:
        report["status"] = "N/D"; return report
    if len({report["fields"][x["id"]]["harvest_year"] for x in ready}) != 1:
        raise ValueError("talhões com anos-safra diferentes não podem ser somados")
    report["production"] = simulate(ready, n=n_mc)
    return report


def productivity_display(crop, summary, fmt=lambda x, nd=0: f"{x:,.{nd}f}".replace(",", ".")):
    """Display calibrated/scenario forecast in t/ha; soybean also in 60-kg bags/ha.

    Input forecast quantiles are kg/ha, not independent bag estimates. The
    conversion is exact: t/ha = kg/ha / 1000; 60-kg bags/ha = kg/ha / 60.
    """
    p = summary
    out = (f"    Produtividade prevista: {fmt(p['median']/1000, 2)} t/ha "
           f"(intervalo 90%: {fmt(p['p05']/1000, 2)}–{fmt(p['p95']/1000, 2)} t/ha)")
    if str(crop).strip().casefold() == "soja":
        out += (f"; equivalente a {fmt(p['median']/60, 2)} sacas/ha (60 kg/saca; "
                f"intervalo 90%: {fmt(p['p05']/60, 2)}–{fmt(p['p95']/60, 2)} sacas/ha)")
        if p["median"] > 0:
            low_pct = 100 * (p["median"] - p["p05"]) / p["median"]
            high_pct = 100 * (p["p95"] - p["median"]) / p["median"]
            out += (f"; incerteza relativa (intervalo preditivo 90%, base mediana): "
                    f"-{fmt(low_pct, 1)}% / +{fmt(high_pct, 1)}%")
        else:
            out += "; incerteza relativa: N/D (mediana igual a zero)"
    return out


def forecast_lines(report, fmt=lambda x, nd=0: f"{x:,.{nd}f}".replace(",", ".")):
    if report.get("model") == "panel":
        return _panel_lines(report, fmt)
    out = ["PREVISÃO DE SAFRA — CENÁRIO NÃO CALIBRADO (matriz vigor × clima; sem modelo calibrado para a cultura)"]
    for rid, r in report["fields"].items():
        if r["status"] == "N/D":
            out.append(f"  {rid}: N/D — {r['reason']}")
            continue
        p = report["production"]["fields_kg_ha"][rid]
        v, cl, sc, hc = r["vigor"], r["climate"], r["scenarios"], r["hindcast"]
        out += [f"  {rid} — microrregião {r['microregion']['name']}/{r['microregion']['uf']} "
                f"(PAM {r['pam_years'][0]}–{r['pam_years'][-1]}), safra {r['harvest_year']}",
                f"    Vigor: {v['class']} (P: " + ", ".join(f"{k} {100*x:.0f}%" for k, x in v["probabilities"].items()) + ")",
                f"    Clima: {cl['class']} (P: " + ", ".join(f"{k} {100*x:.0f}%" for k, x in cl["probabilities"].items())
                + f"; {100*cl['observed_fraction_of_season']:.0f}% da safra observada)",
                f"    Microrregião (tendência projetada): piso {fmt(sc['floor'])}, média {fmt(sc['mean'])}, teto {fmt(sc['ceiling'])} kg/ha",
                productivity_display(rid, p, fmt),
                f"    Hindcast clima+histórico (n={hc.get('n')}): MAE {fmt(hc.get('mae_kg_ha', 0))} kg/ha; "
                f"só tendência {fmt(hc.get('naive_trend_only_mae_kg_ha', 0))} kg/ha"]
    if "production" in report:
        t = report["production"]["production_t"]
        out += [f"  PRODUÇÃO TOTAL: {fmt(t['median'])} t (intervalo 90%: {fmt(t['p05'])}–{fmt(t['p95'])} t)",
                "  " + report["production"]["interval_note"]]
    return out


def _panel_lines(report, fmt):
    out = ["PREVISÃO DE SAFRA — " + report["model_label"],
           "  Experimental: validada fora da amostra (deixando um ano-safra de fora); não homologada."]
    for rid, r in report["fields"].items():
        if r["status"] == "N/D":
            out.append(f"  {rid}: N/D — {r['reason']}"); continue
        p = report["production"]["fields_kg_ha"][rid]; l = r["loyo"]
        out += [f"  {rid} — {r['microregion']['name']}/{r['microregion']['uf']}, safra {r['harvest_year']} "
                f"(grupo {r['region_group']}; {r['trend_source']})",
                f"    Água disponível do solo: {r['awc']['awc_mm_cm']:.2f} mm/cm ({r['awc']['source']})".replace(".", ","),
                (f"    Rendimento relativo hídrico (RY): mediana {r['ry_median']:.2f} "
                 f"(p10–p90 {r['ry_p10_p90'][0]:.2f}–{r['ry_p10_p90'][1]:.2f}; {r['n_analogs']} anos análogos)").replace(".", ","),
                ("    Vigor: " + r["vigor"]["class"] + " (posiciona o resultado no terço correspondente dos erros históricos)")
                if r["vigor"] else "    Vigor: N/D — intervalo cobre todos os erros históricos",
                productivity_display(rid, p, fmt),
                f"    Validação do modelo no grupo: MAE {fmt(l['mae_kg_ha'])} kg/ha vs. {fmt(l['trend_only_mae_kg_ha'])} só tendência "
                f"(ganho {100*l['skill_vs_trend']:.0f}%; {l['units_improved']}/{l['units']} microrregiões melhoram)"]
    if "production" in report:
        t = report["production"]["production_t"]
        out.append(f"  PRODUÇÃO TOTAL: {fmt(t['median'])} t (intervalo 90%: {fmt(t['p05'])}–{fmt(t['p95'])} t)")
    return out
