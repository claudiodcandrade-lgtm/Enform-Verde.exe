"""Historical cultivated-area contingency, gated behind exhausted SAR routes.

MapBiomas is used only to report its named annual reference classes, never as
current SAR cover. PAM is historical regional context; no class is presented
as a current crop observation or validated field yield.
"""
from __future__ import annotations

import math
import statistics


MAPBIOMAS_CROPS = {
    18: ("Agricultura — cultura não identificada", None),
    19: ("Lavoura temporária — cultura não identificada", None),
    20: ("Cana-de-açúcar", "Cana-de-açúcar"),
    39: ("Soja", "Soja"),
    40: ("Arroz", "Arroz"),
    41: ("Outras lavouras temporárias — cultura não identificada", None),
    46: ("Café", "Café"),
    47: ("Citros", "Citros"),
    48: ("Outras lavouras perenes — cultura não identificada", None),
    62: ("Algodão", None),
}
PIXEL_STATUSES = {"SAR_REAL_EXPERIMENTAL_CANDIDATES", "SAR_CLASSIFICADOR_EXPERIMENTAL",
                  "ALTERNATIVE_RADAR_PIXELS_PROCESSED", "SAR_ELEGIVEL", "SAR_MODELO_EXPERIMENTAL",
                  "SAR_UNIDADES_EXPERIMENTAIS"}
CONFIRMED_ABSENCE_STATUS = "SAR_AUSENCIA_COBERTURA_CONFIRMADA"


def sar_routes_exhausted(land):
    """Allow a historical contingency only after audited, complete SAR absence.

    Errors, inaccessible assets, incomplete pagination, unconfigured missions,
    and missing route audits are not evidence of absent SAR coverage. The
    explicit absence certificate is intentionally stricter than a generic N/D
    status so a reader/transport defect can never open the fallback gate.
    """
    if not isinstance(land, dict) or land.get("status") in PIXEL_STATUSES:
        return {"eligible": False, "reason": "SAR_PROCESSADO_OU_RESULTADO_SAR_PRESENTE"}
    app_status = str(land.get("status") or "").upper()
    if any(token in app_status for token in ("ERRO", "ERROR", "INCOMPLETE", "INCOMPLETO", "FAILED")):
        return {"eligible": False, "reason": "ERRO_TECNICO_SAR_NAO_EVIDENCIA_AUSENCIA"}
    classes = land.get("classes") or []
    if any(str(row.get("source") or "").startswith(("SAR_VALIDADO", "SAR_EXPERIMENTAL_MODELO",
                                                       "SAR_CURRENT_EXPERIMENTAL")) for row in classes):
        return {"eligible": False, "reason": "MASCARA_OU_UNIDADES_SAR_PRESENTES"}
    recent = land.get("recent_sar_cover")
    seasonal = land.get("sar_classifier_lemplus")
    alternative = land.get("alternative_radar_screen")
    native = land.get("native_sar_experimental")
    routes = {"sentinel1_recente": recent, "lemplus_sazonal": seasonal,
              "radar_alternativo": alternative, "triagem_nativa": native}
    missing = [name for name, row in routes.items() if not isinstance(row, dict)]
    if missing:
        return {"eligible": False, "reason": "AUDITORIA_DE_ROTAS_SAR_INCOMPLETA",
                "missing_routes": missing}
    if land.get("all_sar_missions_checked") is not True:
        return {"eligible": False, "reason": "BUSCA_GLOBAL_SAR_NAO_CONFIRMADA"}
    if land.get("unconfigured_sar_routes"):
        return {"eligible": False, "reason": "ROTAS_SAR_NAO_CONFIGURADAS",
                "unconfigured_routes": list(land.get("unconfigured_sar_routes") or [])}
    for name, row in routes.items():
        status = str(row.get("status") or "").upper()
        if status != CONFIRMED_ABSENCE_STATUS:
            return {"eligible": False, "reason": "AUSENCIA_SAR_NAO_COMPROVADA_OU_ROTA_COM_ERRO",
                    "route": name, "route_status": status or "STATUS_AUSENTE"}
        if (row.get("coverage_absence_confirmed") is not True
                or row.get("catalog_search_complete") is not True
                or row.get("pagination_complete") is not True
                or row.get("pixel_read_complete") is not True
                or int(row.get("valid_pixel_count") or 0) != 0
                or int(row.get("technical_error_count") or 0) != 0):
            return {"eligible": False, "reason": "CERTIFICADO_DE_AUSENCIA_SAR_INCOMPLETO",
                    "route": name}
        pixels = row.get("pixels")
        if status in PIXEL_STATUSES or (isinstance(pixels, (int, float)) and pixels > 0):
            return {"eligible": False, "reason": "PIXELS_SAR_PROCESSADOS", "route": name,
                    "route_status": status}
    return {"eligible": True, "reason": "ROTAS_SAR_CONFIGURADAS_ESGOTADAS_SEM_PIXELS_UTILIZAVEIS",
            "routes": {name: {"status": row.get("status"),
                              "reason": row.get("reason") or row.get("diagnostic")}
                       for name, row in routes.items()},
            "unconfigured_global_routes": list((alternative or {}).get("routes_not_configured") or [])}


def build_mapbiomas_pam_contingency(aoi, land, *, map_reader=None,
                                    micro_fn=None, yields_fn=None):
    """Build a historical reference only after every configured SAR route fails."""
    gate = sar_routes_exhausted(land)
    if not gate.get("eligible"):
        return {"status": "BLOQUEADO_ATE_ESGOTAR_SAR", "sar_gate": gate}
    try:
        if map_reader is None:
            from mapbiomas_zonal import mapbiomas_class_percentages
            map_reader = mapbiomas_class_percentages
        mapped = map_reader(aoi)
        if not isinstance(mapped, dict) or not mapped.get("classes"):
            return {"status": "N/D", "stage": "mapbiomas_result_validation",
                    "reason": "MAPBIOMAS_SEM_PIXELS_VALIDOS", "sar_gate": gate}
    except Exception as exc:
        return {"status": "ERRO_TECNICO_MAPBIOMAS", "stage":"mapbiomas_pixel_read",
                "reason": type(exc).__name__, "detail":_safe_exception_detail(exc), "sar_gate": gate}
    try:
        if micro_fn is None:
            from crop_yield_scenario import microregion_of
            micro_fn = microregion_of
        if yields_fn is None:
            from crop_yield_scenario import load_microregion_yields
            yields_fn = load_microregion_yields
        micro = micro_fn(aoi)["dominant"]
    except Exception as exc:
        return {"status": "ERRO_TECNICO_PAM", "stage":"microregion_lookup",
                "reason": type(exc).__name__, "detail":_safe_exception_detail(exc),
                "mapbiomas": {"year": mapped.get("year"), "mapped_area_ha": mapped.get("mapped_area_ha")},
                "sar_gate": gate}

    rows = []
    for item in mapped.get("classes") or []:
        code = int(item.get("class_code", -1))
        if code not in MAPBIOMAS_CROPS:
            continue
        area = float(item.get("area_ha") or 0.0)
        if not math.isfinite(area) or area <= 0:
            continue
        label, pam_crop = MAPBIOMAS_CROPS[code]
        row = {"class_code": code, "label": label, "area_ha": area,
               "source": "MAPBIOMAS_ANUAL_HISTORICO", "pam_crop": pam_crop}
        if pam_crop:
            try:
                yields = yields_fn(pam_crop, micro["code"])
                values = [float(yields[y]) for y in sorted(yields)
                          if 2015 <= int(y) <= 2024 and math.isfinite(float(yields[y])) and float(yields[y]) >= 0]
                if len(values) >= 6:
                    median = statistics.median(values)
                    low = float(__import__("numpy").quantile(values, .05))
                    high = float(__import__("numpy").quantile(values, .95))
                    row.update({"pam_year_count": len(values), "pam_year_range": [2015, 2024],
                                "pam_median_kg_ha": median, "pam_p05_p95_kg_ha": [low, high],
                                "conditional_reference_production_t": area * median / 1000.0,
                                "conditional_reference_production_p05_p95_t": [area * low / 1000.0,
                                                                                 area * high / 1000.0],
                                "uncertainty": "estimativa com incerteza não mensurada; envelope P05–P95 é dispersão histórica PAM, não IC95% nem erro da área MapBiomas"})
                else:
                    row["pam_status"] = "N/D_HISTORICO_COM_MENOS_DE_6_ANOS"
            except Exception as exc:
                row["pam_status"] = "ERRO_TECNICO_PAM_" + type(exc).__name__
                row["pam_error_detail"] = _safe_exception_detail(exc)
        else:
            row["pam_status"] = "CULTURA_NAO_IDENTIFICADA_NA_LEGENDA_MAPBIOMAS"
        rows.append(row)
    return {"status": "FALLBACK_HISTORICO_MAPBIOMAS_PAM" if rows else "N/D_SEM_CLASSES_AGRICOLAS_MAPBIOMAS",
            "current_crop_cover_confirmed": False,
            "classification_role": "contingência histórica após exaustão das rotas SAR configuradas; nunca classificação atual SAR",
            "mapbiomas_collection": mapped.get("collection"), "mapbiomas_year": mapped.get("year"),
            "mapped_area_ha": mapped.get("mapped_area_ha"), "mapbiomas_source": mapped.get("source_url"),
            "pam_microregion": micro, "classes": rows, "sar_gate": gate,
            "uncertainty": "estimativa com incerteza não mensurada para área local; PAM informa dispersão temporal regional, que não é incerteza de transferência nem IC95% da propriedade",
            "calculation_trace": {"area": "interseção dos pixels anuais MapBiomas dentro da AOI",
                                  "yield": "estatísticas descritivas dos anos PAM 2015–2024 na microrregião IBGE dominante",
                                  "production": "área MapBiomas histórica × mediana PAM regional (kg/ha) ÷ 1000",
                                  "prohibited_inference": "não chamar de área atual, cultura observada por SAR, previsão de safra ou validação de campo"}}


def _safe_exception_detail(exc):
    """Keep useful diagnostics even when a native exception contains bad bytes."""
    try:
        detail = str(exc)
    except Exception:
        detail = "mensagem da exceção não decodificável"
    # Signed COG URLs and query credentials must never enter an audit report.
    import re
    detail = re.sub(r"https?://[^\s'\"]+", "[URL_REMOVIDA]", detail)
    return detail.encode("utf-8", "replace").decode("utf-8")[:240]
