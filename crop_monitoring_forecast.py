"""Crop monitoring add-on for the desktop: consolidated identification,
automatic vigor (Sentinel-1) and calibrated yield forecast for the AOI.

Pure function (no tkinter) so it is testable and runs in a worker thread.
"""
from __future__ import annotations

from datetime import date, timedelta

from crop_identifier_consolidated import MAPBIOMAS_C11, REGISTRY, attribute_unseparated

NAME_TO_CODE = {v: k for k, v in MAPBIOMAS_C11.items()}


def crops_in_land_result(land):
    """MapBiomas crop classes reported by land_use_sar → {crop: area_ha}."""
    out = {}
    for item in (land or {}).get("classes", []) or []:
        name = str(item.get("class_name", ""))
        if name.startswith("Lavoura de ") and item.get("source") in ("MAPBIOMAS", "SAR_VALIDADO"):
            crop = name.replace("Lavoura de ", "").strip()
            crop = {"Citrus": "Citros", "Cana": "Cana-de-açúcar"}.get(crop, crop)
            out[crop] = out.get(crop, 0.0) + float(item.get("area_ha") or 0)
        elif name in ("Outras Lavouras Temporárias", "Lavoura Temporária"):
            out["__temporarias__"] = out.get("__temporarias__", 0.0) + float(item.get("area_ha") or 0)
    return out


def monitoring_forecast(gdf, land, *, as_of=None, vigor_fn=None, forecast_fn=None, micro_fn=None):
    from crop_forecast_pipeline import forecast_fields, forecast_lines
    from crop_panel_yield_model import load_artifact
    from crop_vigor_auto import automatic_vigor
    from crop_yield_scenario import microregion_of
    as_of = as_of or (date.today() - timedelta(days=3))
    vigor_fn = vigor_fn or automatic_vigor
    forecast_fn = forecast_fn or forecast_fields
    micro_fn = micro_fn or microregion_of
    crops = crops_in_land_result(land)
    lines = ["", "IDENTIFICAÇÃO CONSOLIDADA DE CULTURAS E PREVISÃO DE SAFRA (experimental)"]
    audit = {"as_of": as_of.isoformat(), "crops": {}}
    if not crops:
        lines.append("• Nenhuma lavoura identificada pela rota consolidada (mapa brasileiro anual ou modelo SAR validado).")
        return lines, audit
    art = load_artifact() or {"crops": {}}
    micro = micro_fn(gdf)["dominant"]
    for crop, area in sorted(crops.items(), key=lambda kv: -kv[1]):
        if crop == "__temporarias__":
            att = attribute_unseparated(micro["code"], area)
            audit["crops"]["outras_temporarias"] = att
            if att["status"] == "N/D":
                lines.append("• Outras lavouras temporárias: cultura não identificada (" + att["reason"] + ")")
            else:
                probs = ", ".join(f"{c} {100*p:.0f}%" for c, p in att["probabilities"].items())
                lines.append(f"• Outras lavouras temporárias ({area:.1f} ha): cultura NÃO identificada; "
                             f"probabilidade a priori na microrregião {micro['name']} (PAM): {probs}")
            continue
        reg = REGISTRY.get(crop, {})
        lines.append(f"• {crop} ({area:.1f} ha) — {reg.get('product', 'rota não registrada')}; "
                     "mapa do ano anterior, sem validação desta propriedade")
        entry = {"area_ha": area, "identification": reg}
        if crop in art.get("crops", {}):
            code = NAME_TO_CODE.get(crop)
            try:
                vig = vigor_fn(gdf, as_of, code) if code else {"status": "N/D", "reason": "sem classe de referência"}
            except Exception as exc:
                vig = {"status": "N/D", "reason": type(exc).__name__ + ": " + str(exc)[:160]}
            entry["vigor"] = {k: v for k, v in vig.items() if k not in ("metrics", "z_scores")}
            if vig.get("status") == "N/D":
                lines.append("  Vigor automático: N/D — " + str(vig.get("reason")))
            else:
                p = ", ".join(f"{k} {100*v:.0f}%" for k, v in vig["probabilities"].items())
                lines.append(f"  Vigor automático (Sentinel-1 {str(vig.get('acquisition_utc', ''))[:10]}): {vig['class']} ({p})")
            try:
                rep = forecast_fn([{"id": crop, "gdf": gdf, "crop": crop,
                                    "identification": {"label_allowed": True}, "vigor": vig, "area_ha": area}],
                                  as_of=as_of)
                lines += ["  " + l for l in forecast_lines(rep)]
                entry["forecast_status"] = rep.get("status")
            except Exception as exc:
                lines.append("  Previsão de safra: N/D — " + type(exc).__name__ + ": " + str(exc)[:160])
        else:
            lines.append("  Previsão de safra: sem modelo calibrado para esta cultura (apenas soja e milho calibrados).")
        audit["crops"][crop] = entry
    return lines, audit
