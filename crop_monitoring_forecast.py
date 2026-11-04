"""Crop monitoring add-on for the desktop: consolidated identification,
automatic vigor (Sentinel-1) and calibrated yield forecast for the AOI.

Pure function (no tkinter) so it is testable and runs in a worker thread.
"""
from __future__ import annotations

from datetime import date, timedelta

from crop_identifier_consolidated import MAPBIOMAS_C11, REGISTRY, attribute_unseparated

NAME_TO_CODE = {v: k for k, v in MAPBIOMAS_C11.items()}
CANONICAL_CROPS = {name.casefold(): name for name in REGISTRY}
CANONICAL_CROPS.update({"citrus": "Citros", "cana": "Cana-de-açúcar", "cana de açúcar": "Cana-de-açúcar"})


def canonical_crop(label):
    """Case-insensitive bridge between MapBiomas display labels and PAM/model keys."""
    return CANONICAL_CROPS.get(str(label).strip().casefold(), str(label).strip())



def crops_in_land_result(land):
    """MapBiomas crop classes reported by land_use_sar → {crop: area_ha}."""
    out = {}
    for item in (land or {}).get("classes", []) or []:
        name = str(item.get("class_name", ""))
        if name.startswith("Lavoura de ") and item.get("source") in ("MAPBIOMAS", "SAR_VALIDADO"):
            crop = name.replace("Lavoura de ", "").strip()
            crop = canonical_crop(crop)
            out[crop] = out.get(crop, 0.0) + float(item.get("area_ha") or 0)
        elif name in ("Outras Lavouras Temporárias", "Lavoura Temporária"):
            out["__temporarias__"] = out.get("__temporarias__", 0.0) + float(item.get("area_ha") or 0)
    return out


def monitoring_forecast(gdf, land, *, as_of=None, vigor_fn=None, forecast_fn=None, micro_fn=None):
    from crop_forecast_pipeline import forecast_fields, forecast_lines
    from crop_panel_yield_model import load_artifact
    from crop_vigor_auto import automatic_vigor
    from crop_yield_scenario import microregion_of
    from crop_spatial_monitoring import crop_geometry, sampled_sentinel_vigor
    from crop_specific_model_registry import model_contract
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
    # A municipal AOI is not a crop mask. Never derive field-scale vigor or
    # phytosanitary status from a mixed-cover municipality polygon.
    aoi_ha = float(gdf.to_crs(6933).geometry.area.sum()) / 10000.0
    municipal_scale = aoi_ha > 5000.0
    audit["geometry_scope"] = {"aoi_ha": aoi_ha, "municipal_scale": municipal_scale,
                               "crop_geometry_available": bool(land.get("vector_path")),
                               "note": "monitoramento SAR somente em polígonos mapeados de cultura; amostragem não equivale a validação de área"}

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
        spec = model_contract(crop)
        audit.setdefault("species_model_contracts", {})[crop] = spec
        if spec["status"] != "N/D":
            lines.append("  Modelo fisiológico prioritário (PESQUISA; não executado): " + spec["recommended_model"])
            lines.append("  Estádios sensíveis: " + "; ".join(spec["phenological_stages"]))
            lines.append("  Variáveis climáticas específicas: " + "; ".join(spec["climate_features"]))
            lines.append("  Indicadores SAR a calibrar: " + "; ".join(spec["sar_features"]))
        reg = REGISTRY.get(crop, {})
        lines.append(f"• {crop} ({area:.1f} ha) — {reg.get('product', 'rota não registrada')}; "
                     "mapa do ano anterior, sem validação desta propriedade")
        entry = {"area_ha": area, "identification": reg}
        crop_gdf = crop_geometry(land, crop, canonical_fn=canonical_crop)
        entry["crop_polygon_available"] = crop_gdf is not None
        if crop in art.get("crops", {}):
            code = NAME_TO_CODE.get(crop)
            # Reuse the exact MapBiomas raster that succeeded in the land-use
            # stage, including a user-supplied local Windows TIFF.
            selected_map = (land or {}).get("mapbiomas_source")
            def scene_vigor(patch, day, class_code):
                if vigor_fn is automatic_vigor and selected_map:
                    return automatic_vigor(patch, day, class_code, mapbiomas_url=selected_map)
                return vigor_fn(patch, day, class_code)
            try:
                if crop_gdf is not None and municipal_scale and code is not None:
                    vig = sampled_sentinel_vigor(crop_gdf, as_of, code, scene_vigor, require_scene_evidence=(vigor_fn is automatic_vigor))
                elif municipal_scale:
                    vig = {"status": "N/D", "reason": "sem polígono de cultura disponível; proibido usar AOI municipal multiclasse para vigor"}
                else:
                    vig = scene_vigor(crop_gdf if crop_gdf is not None else gdf, as_of, code) if code else {"status": "N/D", "reason": "sem classe de referência"}
            except Exception as exc:
                vig = {"status": "N/D", "reason": type(exc).__name__ + ": " + str(exc)[:160]}
            entry["vigor"] = dict(vig)  # preserve numerical metrics, uncertainty and traceability
            if vig.get("status") == "N/D":
                lines.append("  Vigor automático: N/D — " + str(vig.get("reason")))
            else:
                p = ", ".join(f"{k} {100*v:.0f}%" for k, v in vig["probabilities"].items())
                stamp = str(vig.get("acquisition_utc") or "")[:10]
                if vig.get("patches_evaluated"):
                    lines.append(f"  Vigor Sentinel-1 amostral ({vig['patches_valid']}/{vig['patches_evaluated']} parcelas): {vig['class']} ({p}); NÃO extrapolado como mapa municipal validado")
                    dates = vig.get("acquisition_period_utc")
                    if dates:
                        lines.append(f"  AQUISIÇÃO SENTINEL-1 REAL (UTC): {dates[0]} até {dates[1]}")
                        from datetime import datetime, timezone, timedelta
                        utc_minus_3 = timezone(timedelta(hours=-3))
                        def _date_br(iso):
                            return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(utc_minus_3).isoformat()
                        lines.append(f"  Aquisição Sentinel-1 (UTC−3): {_date_br(dates[0])} até {_date_br(dates[1])}")
                        lines.append(f"  Janela operacional: até 24 dias, limite máximo 30 dias; data de referência {as_of.isoformat()}")
                        scene_ids = sorted({v["scene_id"] for v in vig.get("accepted_scenes", []) if v.get("scene_id")})
                        lines.append("  Cenas auditáveis: " + ", ".join(scene_ids))
                    else:
                        lines.append("  Aquisição Sentinel-1: NÃO COMPROVADA por cena e data; resultado ainda não deve ser descrito como monitoramento orbital efetivo.")
                    lines.append(f"  Cobertura SAR válida da área cartográfica de {crop}: {100*vig.get('sar_sample_coverage_fraction',0):.3f}%")
                else:
                    lines.append(f"  Vigor automático (Sentinel-1 {stamp}): {vig['class']} ({p})")
            if vig.get("status") in ("experimental", "validated"):
                metric_cases = vig.get("sample_audit") or [vig]
                for sample in metric_cases:
                    metrics = sample.get("metrics") or {}
                    intervals = sample.get("metric_boot_p05_p95") or {}
                    if not metrics:
                        continue
                    sample_ref = f"recorte {sample['sample']}" if sample.get("sample") else "talhão"
                    labels = (("size", "Porte aparente do dossel (RVI/altura)"),
                              ("uniformity", "Uniformidade do dossel"),
                              ("texture_homogeneity", "Textura/rugosidade SAR VH (homogeneidade GLCM)"))
                    for code, label in labels:
                        value = metrics.get(code)
                        if value is None:
                            continue
                        ci = intervals.get(code)
                        note = (f"; bootstrap 90%: {ci[0]:.3f}–{ci[1]:.3f}"
                                if ci is not None else "; incerteza N/D")
                        lines.append(f"  {sample_ref} — {label}: {value:.3f}" + note)
                lines.append("  Incerteza de vigor: bootstrap espacial interno; NÃO equivale à acurácia de campo nem mede rugosidade física.")
            try:
                if municipal_scale:
                    lines.append("  Escala: previsão regional agregada à área cartográfica da cultura; vigor de subamostras SAR, quando disponível, não representa validação municipal.")
                # Diagnostic patches do not constitute an area-representative
                # vigor sample. Use unconditioned historical residuals for the
                # municipality-wide yield distribution until a spatially
                # exhaustive or probability-calibrated vigor product exists.
                forecast_vigor = ({"status": "N/D",
                                   "reason": "vigor SAR amostral não extrapolável ao município"}
                                  if municipal_scale and vig.get("patches_evaluated") else vig)
                entry["vigor_usable_for_municipal_yield"] = forecast_vigor is vig
                rep = forecast_fn([{"id": crop, "gdf": crop_gdf if crop_gdf is not None else gdf, "crop": crop,
                                    "identification": {"label_allowed": True}, "vigor": forecast_vigor, "area_ha": area}],
                                  as_of=as_of)
                lines += ["  " + l for l in forecast_lines(rep)]
                entry["forecast_status"] = rep.get("status")
                entry["forecast_model"] = rep.get("model")
                entry["forecast"] = {k: v for k, v in rep.items() if k in ("production", "fields", "model_label", "status") }
            except Exception as exc:
                lines.append("  Previsão de safra: N/D — " + type(exc).__name__ + ": " + str(exc)[:160])
        else:
            lines.append("  Previsão de safra: sem modelo calibrado para esta cultura (apenas soja e milho calibrados).")
        audit["crops"][crop] = entry
    return lines, audit
