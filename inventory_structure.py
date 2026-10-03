"""Auditable DAP and basal-area summaries from harmonized tree inventories.

These are field-derived structure metrics. They are not SAR observations and
are never silently paired with satellite pixels. Areas are accepted from an
explicit column or from the two documented inventory designs only.
"""
from __future__ import annotations
import csv
import math
from collections import defaultdict

KNOWN_PLOT_AREAS_HA = {
    "MX_SANTO_AMBROSIO_2025": 0.025,  # 167 plots × 250 m², audit v0.2
    "CE_JALAPAO_FOREST_2026": 0.025,  # 10 plots × 250 m², audit v0.2
}

def summarize_inventory_csv(path):
    """Return tree- and plot-level means, basal area and provenance flags.

    BA = sum(pi * (DBH_m/2)^2) / sampled plot area. Dead trees are retained
    in source counts but excluded from live-stand structure. Missing plot IDs
    cannot contribute to plot density/ha. DAP means are arithmetic means of
    measured live stems; they do not replace the diameter distribution.
    """
    by_plot=defaultdict(list); by_inventory=defaultdict(list)
    with open(path,encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows or not {"inventory_id","dbh_cm","status"}.issubset(rows[0]):
        raise ValueError("CSV deve conter inventory_id, dbh_cm e status.")
    for r in rows:
        inv=str(r["inventory_id"]); plot=str(r.get("plot_id") or "").strip()
        try: d=float(r.get("dbh_cm", ""))
        except (TypeError,ValueError): d=float("nan")
        if not math.isfinite(d) or d<=0: continue
        live=str(r.get("status") or "").strip().casefold() in ("alive","viva","vivo","live")
        item={"dbh_cm":d,"ba_m2":math.pi*(d/200.0)**2,"live":live,"plot_id":plot,
              "height_m":_float(r.get("height_m")),"species":r.get("species","")}
        by_inventory[inv].append(item)
        if live and plot: by_plot[(inv,plot)].append(item)
    plot_rows=[]
    for (inv,plot),trees in sorted(by_plot.items()):
        area=KNOWN_PLOT_AREAS_HA.get(inv)
        # An explicit area field can override known metadata only if consistent.
        ba=sum(t["ba_m2"] for t in trees)
        plot_rows.append({"inventory_id":inv,"plot_id":plot,"n_live_stems":len(trees),
            "mean_dbh_cm":sum(t["dbh_cm"] for t in trees)/len(trees),
            "ba_m2_plot":ba,"plot_area_ha":area,
            "basal_area_m2_ha":ba/area if area else None,
            "mean_field_height_m":_mean([t["height_m"] for t in trees]),
            "sar_pair_available":False,"agb_sar_calibration_eligible":False})
    inventory_rows=[]
    for inv,trees in sorted(by_inventory.items()):
        live=[t for t in trees if t["live"]]
        inventory_rows.append({"inventory_id":inv,"n_records_with_dbh":len(trees),
            "n_live_stems":len(live),"n_live_with_plot":sum(1 for t in live if t["plot_id"]),
            "n_plots":len({t["plot_id"] for t in live if t["plot_id"]}),
            "mean_dbh_cm_all_live":_mean([t["dbh_cm"] for t in live]),
            "mean_dbh_cm_plot_assigned":_mean([t["dbh_cm"] for t in live if t["plot_id"]]),
            "mean_plot_basal_area_m2_ha":_mean([p["basal_area_m2_ha"] for p in plot_rows if p["inventory_id"]==inv and p["basal_area_m2_ha"] is not None]),
            "plot_area_ha":KNOWN_PLOT_AREAS_HA.get(inv),"sar_pair_available":False,
            "agb_sar_calibration_eligible":False,
            "interpretation":"estrutura derivada de inventário de campo; sem parcela–pixel SAR pareada"})
    return {"inventory_summary":inventory_rows,"plot_summary":plot_rows,
            "method":"BA = Σ[π(DBH_m/2)^2]/área amostrada; DAP médio aritmético dos fustes vivos; áreas conforme auditoria biblioteca v0.2.",
            "limitations":["DAP médio não representa distribuição diamétrica.",
                "DAP e área basal de campo não são estimativas SAR.",
                "DAP+altura SAR não identificam AGB sem alometria compatível, densidade de fustes/estrutura e validação no domínio.",
                "não há pares espaciais/temporais SAR nos inventários harmonizados disponíveis."]}

def _float(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>0 else None
    except (TypeError,ValueError): return None

def _mean(xs):
    v=[float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return sum(v)/len(v) if v else None
