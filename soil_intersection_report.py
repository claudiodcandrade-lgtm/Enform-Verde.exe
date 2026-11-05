"""Human-readable audit of Solo 0–100 cm from the polygon × Embrapa map intersection.

Kept free of tkinter so the presentation contract can be regression-tested.
Never prints zero for missing data and never hides partial map coverage.
"""
from __future__ import annotations


def _fmt(value, nd=2, fmt=None):
    if value is None:
        return "N/D"
    if fmt:
        return fmt(value, nd)
    return f"{value:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


METHOD_LABELS = {
    "area_weighted_raw_raster_polygon_intersection":
        "interseção geométrica exata polígono × pixels 90 m do mapa Embrapa/PronaSolos",
    "identify_point_sampling_fallback":
        "amostragem por pontos do serviço SGB (contingência; NÃO é interseção exata)",
}


def soil_intersection_summary(soil_profiles):
    """Return a flat dict used by TXT/Excel/painel. ``soil_profiles`` is the
    estimator output stored in each stratum (keys '0–30 cm', '0–100 cm', '_diagnostic')."""
    soil_profiles = soil_profiles or {}
    diag = soil_profiles.get("_diagnostic") or {}
    top = soil_profiles.get("0–100 cm") or {}
    method = diag.get("method") or ("identify_point_sampling_fallback" if top else None)
    prov = diag.get("wcs_provenance") or {}
    status = diag.get("target_status") or ("N/D" if not top else "COMPLETO")
    return {
        "method_code": method,
        "method": METHOD_LABELS.get(method, method or "não executado"),
        "status": status,
        "tc_ha": top.get("tc_ha"),
        "spatial_sd_tc_ha": top.get("spatial_sd_tc_ha"),
        "intersected_area_ha": diag.get("intersected_area_ha"),
        "mapped_area_ha": diag.get("covered_area_ha", top.get("area_covered_ha")),
        "unmapped_area_ha": diag.get("unmapped_area_ha"),
        "coverage_pct": (100.0 * diag["coverage_fraction"]
                         if diag.get("coverage_fraction") is not None else None),
        "pixels": diag.get("valid_complete_pixels"),
        "partial": bool(top.get("partial_coverage")),
        "retrieved_at_utc": prov.get("retrieved_at_utc"),
        "license": prov.get("license"),
        "source_title": prov.get("title"),
        "reason": diag.get("reason"),
        "official_uncertainty": top.get("official_uncertainty") or diag.get("official_uncertainty") or {},
    }


def soil_intersection_lines(soil_profiles, fmt=None):
    s = soil_intersection_summary(soil_profiles)
    if s["tc_ha"] is None:
        out = ["    Solo 0–100 cm — interseção com o mapa: N/D (" + str(s["status"]) + ")"]
        if s["reason"]:
            out.append("      Motivo: " + str(s["reason"])[:300])
        return out
    lines = ["    Solo 0–100 cm — método: " + s["method"]]
    if s["method_code"] == "area_weighted_raw_raster_polygon_intersection":
        lines.append("      Área da interseção: " + _fmt(s["intersected_area_ha"], 2, fmt)
                     + " ha; área com os cinco horizontes mapeados: " + _fmt(s["mapped_area_ha"], 2, fmt)
                     + " ha (" + _fmt(s["coverage_pct"], 2, fmt) + "%); pixels: "
                     + (str(s["pixels"]) if s["pixels"] is not None else "N/D"))
        if s["partial"]:
            lines.append("      COBERTURA PARCIAL: " + _fmt(s["unmapped_area_ha"], 2, fmt)
                         + " ha sem valor no mapa (água, área urbana, afloramento ou lacuna)."
                         " O estoque em tC usa somente a área mapeada; nada foi extrapolado.")
        lines.append("      Densidade = média dos pixels ponderada pela área exata de cada pixel dentro do polígono "
                     "(EPSG:6933); DP espacial " + _fmt(s["spatial_sd_tc_ha"], 2, fmt)
                     + " tC/ha é descritivo, não IC95%.")
        if s["retrieved_at_utc"]:
            lines.append("      Fonte: " + str(s["source_title"]) + " — obtida via WCS em "
                         + s["retrieved_at_utc"] + " UTC; licença " + str(s["license"]) + ".")
    official=s["official_uncertainty"]
    interval=official.get("sum_bounds_envelope_tc_ha")
    if official.get("status")=="ENVELOPE_MARGINAL_OFICIAL" and interval:
        lines.append("      LIMITES OFICIAIS MARGINAIS — envelope somado 0–100 cm: "
                     + _fmt(interval[0],2,fmt)+" a "+_fmt(interval[1],2,fmt)+" tC/ha.")
        stock=official.get("sum_bounds_envelope_stock_tC")
        if stock:
            lines.append("      Estoque na ÁREA MAPEADA — envelope: "
                         + _fmt(stock[0],2,fmt)+" a "+_fmt(stock[1],2,fmt)+" tC.")
        for depth,bounds in (official.get("marginal_horizon_bounds") or {}).items():
            lines.append("      "+depth+" cm — limites marginais oficiais: "
                         +_fmt(bounds["lower_tc_ha"],2,fmt)+" a "
                         +_fmt(bounds["upper_tc_ha"],2,fmt)+" tC/ha.")
        lines.append("      ATENÇÃO: soma de limites marginais NÃO é IC95% conjunto calibrado do estoque.")
    else:
        lines.append("      Incerteza preditiva oficial do estoque 0–100 cm: N/D — "
                     +str(official.get("reason") or "produto oficial não acessível")[:180])
    return lines
