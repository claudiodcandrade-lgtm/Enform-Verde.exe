"""Crop monitoring add-on for the desktop: consolidated identification,
automatic vigor (Sentinel-1) and calibrated yield forecast for the AOI.

Pure function (no tkinter) so it is testable and runs in a worker thread.
"""
from __future__ import annotations

from datetime import date, timedelta

from crop_identifier_consolidated import CROPS, REGISTRY, attribute_unseparated
CANONICAL_CROPS = {name.casefold(): name for name in CROPS}
CANONICAL_CROPS.update({"citrus": "Citros", "cana": "Cana-de-açúcar", "cana de açúcar": "Cana-de-açúcar"})


def canonical_crop(label):
    """Normalize SAR classifier labels to model/PAM crop names; no map-code lookup."""
    return CANONICAL_CROPS.get(str(label).strip().casefold(), str(label).strip())



def mapbiomas_historical_reference(land):
    """Return MapBiomas crop areas as an explicitly historical reference only."""
    out = {}
    for item in (land or {}).get("classes", []) or []:
        if item.get("source") != "MAPBIOMAS_HISTORICO":
            continue
        name = str(item.get("class_name", ""))
        if name.startswith("Lavoura de "):
            crop = canonical_crop(name.replace("Lavoura de ", "").strip())
            out[crop] = out.get(crop, 0.0) + float(item.get("area_ha") or 0.0)
        elif name in ("Outras Lavouras Temporárias", "Lavoura Temporária"):
            out["__temporarias__"] = out.get("__temporarias__", 0.0) + float(item.get("area_ha") or 0.0)
    return out


def _crops_from_sar_source(land, prefix):
    out = {}
    for item in (land or {}).get("classes", []) or []:
        if not str(item.get("source") or "").startswith(prefix):
            continue
        name = str(item.get("class_name", ""))
        if name.startswith("Lavoura de "):
            crop = canonical_crop(name.replace("Lavoura de ", "").strip())
            out[crop] = out.get(crop, 0.0) + float(item.get("area_ha") or 0.0)
        elif name in ("Outras Lavouras Temporárias", "Lavoura Temporária"):
            out["__temporarias__"] = out.get("__temporarias__", 0.0) + float(item.get("area_ha") or 0.0)
    return out


def crops_in_land_result(land):
    """Only locally accepted current SAR labels count as current identity."""
    return _crops_from_sar_source(land, "SAR_VALIDADO")


def experimental_crops_in_land_result(land):
    """Annual SAR RF models generate RETROSPECTIVE conditional crop scenarios."""
    return _crops_from_sar_source(land, "SAR_EXPERIMENTAL_MODELO")

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
    current_crops = crops_in_land_result(land)
    conditional_crops = experimental_crops_in_land_result(land)
    crops = current_crops or conditional_crops
    historical = mapbiomas_historical_reference(land)
    annual_experimental = bool(conditional_crops and not current_crops)
    model_season=((land or {}).get("validation") or {}).get("observed_season")
    lines = ["", "CLASSIFICAÇÃO SAR EXPERIMENTAL, VIGOR ATUAL E PREVISÃO CONDICIONAL DE SAFRA"]
    if annual_experimental:
        lines.append("• COBERTURA EXPERIMENTAL RETROSPECTIVA: máscaras de uso do solo obtidas no ano agrícola "+
                     str(model_season or "sem período identificado")+
                     "; NÃO comprovam cobertura atual da safra em curso, mesmo com SAR recente para vigor.")
    from sensor_contingency import fallback_plan
    audit = {"as_of": as_of.isoformat(), "crops": {},
             "current_crop_identification": ("SAR_EXPERIMENTAL_ANUAL_NAO_ATUAL" if annual_experimental
                                              else "SAR_VALIDADO" if crops else "N/D"),
             "crop_landcover_season":model_season,
             "field_validation_status":"PENDENTE" if annual_experimental else "indefinido",
             "mapbiomas_historical_reference_only": historical,
             "sensor_contingency": fallback_plan(target="agricultura_area_vigor_safra")}
    if not crops:
        lines.append("• Cultura atual: N/D — nenhum identificador SAR validado produziu máscara contemporânea nesta AOI.")
        if historical:
            area = sum(historical.values())
            labels = ", ".join(sorted(k for k in historical if k != "__temporarias__"))
            lines.append("• MapBiomas anual: referência histórica de "+format(area, ".2f")+" ha"+
                         ((" ("+labels+")") if labels else "")+
                         "; não usada para identificar cultura atual, vigor ou safra.")
        lines.append("• Vigor: N/D — sem máscara atual de cultura derivada de SAR.")
        lines.append("• Produtividade e produção da propriedade: N/D — exigem identificador SAR atual e vigor com cenas datadas.")
        audit["forecast_block_reason"] = "sem classe de cultura SAR validada"
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
    # At most ONE real SAR first-look per analysis: user-facing current
    # measurements are not a calibrated or class-specific SAR classifier.
    # Keeping a bounded query avoids repeated network calls for every crop.
    sar_probe_done = False

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
        crop_source=("SAR_EXPERIMENTAL_ANUAL" if annual_experimental else "SAR_VALIDADO")
        lines.append(f"• {crop} ({area:.1f} ha) — área de máscara SAR "+
                     ("EXPERIMENTAL do ano agrícola; NÃO atual" if annual_experimental
                      else "com evidência orbital de classificação")+
                     "; ver data, domínio e incerteza no relatório de auditoria")
        entry = {"area_ha": area, "identification": reg, "identification_source": crop_source,
                 "experimental":annual_experimental,
                 "coverage_age_status":"HISTORICO_SAFRA_COMPLETA" if annual_experimental else "a verificar"}
        crop_gdf = crop_geometry(land, crop, canonical_fn=canonical_crop)
        entry["crop_polygon_available"] = crop_gdf is not None
        if crop_gdf is not None and not sar_probe_done:
            sar_probe_done = True
            try:
                from sar_crop_live_probe import probe_recent_sar_crop_pixels
                live_probe = probe_recent_sar_crop_pixels(gdf, crop_gdf)
                audit["live_sar_probe"] = live_probe
                if live_probe.get("status") == "SAR_PIXELS_RECENTES_PROCESSADOS":
                    lines.append(
                        "  SAR ATUAL — VV/VH realmente lidos: "+
                        str(live_probe.get("latest_acquisition_utc"))+
                        "; a classe de cultura vem apenas do classificador SAR aceito.")
                else:
                    prefix = "  SAR ATUAL: ERRO TÉCNICO — " if live_probe.get("status") == "ERRO_TECNICO" else "  SAR ATUAL: N/D — "
                    lines.append(prefix + str(live_probe.get("reason") or "consulta indisponível")[:180])
            except Exception as exc:
                audit["live_sar_probe"] = {
                    "status": "ERRO_TECNICO",
                    "reason": type(exc).__name__ + ": " + str(exc)[:180]}
                lines.append("  SAR ATUAL: ERRO TÉCNICO — "+
                             audit["live_sar_probe"]["reason"])
        if crop in art.get("crops", {}):
            # Both target and peer masks must be current, accepted SAR crop labels.
            # No annual map-code or cartographic class selects the peer fields.
            def scene_vigor(patch, day, _crop_label):
                if vigor_fn is automatic_vigor:
                    return vigor_fn(patch, day, crop, reference_gdf=crop_gdf)
                return vigor_fn(patch, day, crop)
            try:
                if crop_gdf is not None and municipal_scale:
                    vig = sampled_sentinel_vigor(crop_gdf, as_of, crop, scene_vigor, require_scene_evidence=(vigor_fn is automatic_vigor))
                elif municipal_scale:
                    vig = {"status": "N/D", "reason": "sem polígono de cultura disponível; proibido usar AOI municipal multiclasse para vigor"}
                elif crop_gdf is None:
                    # A 500–2.000 ha user-supplied AOI can still mix native,
                    # pasture and agriculture. Never treat its outer boundary
                    # as a homogeneous soybean/corn field for radar vigor.
                    vig = {"status": "N/D", "reason": "sem máscara vetorial da cultura: polígono analisado não comprova talhão agrícola homogêneo"}
                else:
                    vig = scene_vigor(crop_gdf, as_of, crop)
            except Exception as exc:
                vig = {"status": "ERRO_TECNICO", "reason": type(exc).__name__ + ": " + str(exc)[:160]}
            entry["vigor"] = dict(vig)  # preserve numerical metrics, uncertainty and traceability
            if vig.get("status") == "ERRO_TECNICO":
                lines.append("  Vigor automático: ERRO TÉCNICO — " + str(vig.get("reason")))
            elif vig.get("status") == "N/D":
                lines.append("  Vigor automático: N/D — " + str(vig.get("reason")) )
            else:
                p = ", ".join(f"{k} {100*v:.0f}%" for k, v in vig["probabilities"].items())
                stamp = str(vig.get("acquisition_utc") or "")[:10]
                if vig.get("patches_evaluated"):
                    lines.append(f"  Vigor Sentinel-1 amostral ({vig['patches_valid']}/{vig['patches_evaluated']} parcelas): {vig['class']} ({p}); NÃO extrapolado como mapa municipal validado")
                    dates = vig.get("acquisition_period_utc")
                    if dates:
                        lines.append(f"  AQUISIÇÃO SENTINEL-1 REAL (UTC): {dates[0]} até {dates[1]}")
                        from datetime import datetime, timezone
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
            scene_evidence = (bool(vig.get("scene_id") and vig.get("acquisition_utc")) or
                             bool(vig.get("accepted_scenes")))
            vigor_usable = (vig.get("status") in ("experimental", "validated") and
                            isinstance(vig.get("probabilities"), dict) and scene_evidence and
                            crop_gdf is not None)
            if not vigor_usable:
                # Owner decision 08/11/2026 (5 = B): forecast continues WITHOUT
                # vigor (climate + PAM history), clearly labelled; only a SAR
                # crop mask (crop_gdf) is still mandatory for the field area.
                reason = str(vig.get("reason") or "sem vigor SAR atual com cena datada sobre máscara SAR validada")
                if crop_gdf is None:
                    entry["forecast_status"] = "N/D"
                    entry["forecast"] = {"status": "N/D", "reason": "sem máscara SAR da cultura; " + reason}
                    lines.append("  Produtividade e produção da propriedade: N/D — sem máscara SAR da cultura.")
                    audit["crops"][crop] = entry
                    continue
                lines.append("  Vigor N/D (" + reason + "): previsão SEM VIGOR, só clima + histórico PAM, intervalo mais largo.")
                vig = {"status": "N/D", "reason": reason}
            try:
                if municipal_scale:
                    lines.append("  Escala: vigor amostral SAR; previsão permanece condicional ao domínio e às validações do modelo.")
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
                if annual_experimental:
                    lines.append("  PREVISÃO CONDICIONAL: área e cultura da safra anterior; transferência para "
                                 "a safra corrente NÃO quantificada; usar para aferição experimental, "
                                 "não como produção confirmada da propriedade.")
                entry["forecast_status"] = rep.get("status")
                entry["transfer_uncertainty"]="NAO_QUANTIFICADA" if annual_experimental else None
                entry["forecast_model"] = rep.get("model")
                entry["forecast"] = {k: v for k, v in rep.items() if k in ("production", "fields", "model_label", "status") }
            except Exception as exc:
                lines.append("  Previsão de safra: N/D — " + type(exc).__name__ + ": " + str(exc)[:160])
        else:
            lines.append("  Previsão de safra: sem modelo calibrado para esta cultura (apenas soja e milho calibrados).")
        audit["crops"][crop] = entry
    return lines, audit
