"""Fail-closed gate for regional height-chart fallback."""
import math


def build_height_absence_certificate(esa_search_audit, esa_height_result, gtdx_result):
    """Build an AOI-scoped absence proof only from complete live route audits."""
    esa_queries=(esa_search_audit or {}).get("queries") or []
    fh_queries=[q for q in esa_queries if q.get("product_type") in {"FP_FH__L2A","FP_FH__L2B"}]
    esa_search_ok=(len(fh_queries)==4 and all(
        q.get("catalog_search_complete") is True and q.get("pagination_complete") is True
        and q.get("technical_error_count")==0 for q in fh_queries))
    esa_empty=bool(esa_search_ok and all(q.get("matching_product_count")==0 for q in fh_queries))
    height_result=esa_height_result or {}
    height_errors=height_result.get("technical_error_count")
    if height_errors is None:
        height_errors=len(height_result.get("errors") or [])
    completed_zero_pixel_read=bool(height_result.get("pixel_read_complete") is True
        and int(height_errors or 0)==0
        and isinstance(height_result.get("valid_pixel_count"),int)
        and height_result.get("valid_pixel_count")==0)
    esa_read_ok=(esa_empty or bool(height_result.get("pixel_read_complete") is True
        and int(height_errors or 0)==0
        and isinstance(height_result.get("valid_pixel_count"),int)
        and height_result.get("valid_pixel_count") >= 0))
    # A product may intersect the catalog AOI bbox while its actual FH raster
    # has no valid cells inside the precise requested geometry. A completed
    # zonal read of every downloaded candidate with zero valid cells is an
    # AOI-scoped absence observation; a catalog hit alone is not.
    esa_coverage_absent=bool(esa_search_ok and (esa_empty or completed_zero_pixel_read)
        and int(height_errors or 0)==0)
    esa_route={"route":"ESA_BIOMASS_FH","configured":True,
        "catalog_search_complete":esa_search_ok,"pagination_complete":esa_search_ok,
        "pixel_read_complete":esa_read_ok,
        "coverage_absence_confirmed":esa_coverage_absent,
        "valid_pixel_count":0 if esa_coverage_absent else height_result.get("valid_pixel_count"),
        "technical_error_count":sum(int(q.get("technical_error_count") or 0) for q in fh_queries)
            +int(height_errors or 0)}
    gtdx=gtdx_result or {}
    gtdx_empty=(gtdx.get("catalog_search_complete") is True
        and gtdx.get("pagination_complete") is True
        and gtdx.get("pixel_read_complete") is True
        and gtdx.get("valid_pixel_count")==0
        and gtdx.get("technical_error_count")==0)
    gtdx_route={"route":"GTDX_GEDI_TANDEM_X","configured":True,
        "catalog_search_complete":gtdx.get("catalog_search_complete") is True,
        "pagination_complete":gtdx.get("pagination_complete") is True,
        "pixel_read_complete":gtdx.get("pixel_read_complete") is True,
        "coverage_absence_confirmed":gtdx_empty,
        "valid_pixel_count":gtdx.get("valid_pixel_count"),
        "technical_error_count":int(gtdx.get("technical_error_count") or 0)}
    routes=[esa_route,gtdx_route]
    confirmed=all(r["coverage_absence_confirmed"] for r in routes)
    return {"status":"SAR_AUSENCIA_COBERTURA_CONFIRMADA" if confirmed else "AUSENCIA_SAR_NAO_COMPROVADA",
        "scope":"AOI consultada; rotas de altura ESA BIOMASS FH e GTDX",
        "global_search_complete":all(r["catalog_search_complete"] for r in routes),
        "pagination_complete":all(r["pagination_complete"] for r in routes),
        "pixel_read_complete":all(r["pixel_read_complete"] for r in routes),
        "routes":routes}


def regional_height_fallback_decision(certificate):
    """Allow inventory height references only after certified SAR absence.

    A technical error, incomplete catalog/pagination/pixel read, or any valid
    SAR height pixel blocks this chart fallback.
    """
    if not isinstance(certificate, dict):
        return False, "CERTIFICADO_DE_AUSENCIA_SAR_NAO_DISPONIVEL"
    if certificate.get("status") != "SAR_AUSENCIA_COBERTURA_CONFIRMADA":
        return False, "AUSENCIA_SAR_NAO_CONFIRMADA"
    for key in ("global_search_complete", "pagination_complete", "pixel_read_complete"):
        if certificate.get(key) is not True:
            return False, f"BUSCA_SAR_INCOMPLETA:{key}"
    routes=certificate.get("routes")
    if not isinstance(routes,list) or not routes:
        return False, "AUDITORIA_DE_ROTAS_SAR_AUSENTE"
    for route in routes:
        if not isinstance(route,dict) or route.get("configured") is not True:
            return False, "ROTA_SAR_NAO_CONFIGURADA_OU_AUDITORIA_INVALIDA"
        if route.get("coverage_absence_confirmed") is not True:
            return False, "AUSENCIA_DE_COBERTURA_NAO_CONFIRMADA_EM_TODAS_AS_ROTAS"
        if route.get("catalog_search_complete") is not True or route.get("pagination_complete") is not True:
            return False, "CATALOGO_OU_PAGINACAO_INCOMPLETOS"
        if route.get("pixel_read_complete") is not True:
            return False, "LEITURA_DE_PIXELS_INCOMPLETA"
        if route.get("valid_pixel_count") != 0:
            return False, "PIXELS_SAR_DE_ALTURA_EXISTENTES_OU_CONTAGEM_NAO_ZERO"
        if route.get("technical_error_count") != 0:
            return False, "ERRO_TECNICO_SAR_BLOQUEIA_FALLBACK"
    return True, "AUSENCIA_SAR_CONFIRMADA_EM_TODAS_AS_ROTAS_AUDITADAS"


def secondary_cci_agb_decision(height_certificate, *, valid_height_pixels=False, cci_calibration=None):
    """Allow direct CCI L4 after an error-free attempt at the preferred FH route.

    A usable FH value has already been offered to the FH × inventory model by
    the caller before this gate. If that model cannot estimate AGB, the owner
    has selected CCI plus inventory references as the second route. If FH is
    absent, both height routes still need a complete, error-free absence proof.
    CCI remains a satellite product, not a locally calibrated FH model.
    """
    if not isinstance(height_certificate, dict):
        return {"eligible":False,"reason":"CERTIFICADO_DA_ROTA_PRIORITARIA_AUSENTE",
                "evidence":"PRIORITY_ROUTE_AUDIT_MISSING"}
    routes=height_certificate.get("routes")
    if not isinstance(routes,list) or not routes:
        return {"eligible":False,"reason":"AUDITORIA_DAS_ROTAS_PRIORITARIAS_AUSENTE",
                "evidence":"PRIORITY_ROUTE_AUDIT_MISSING"}
    esa=next((r for r in routes if isinstance(r,dict) and
              r.get("route")=="ESA_BIOMASS_FH"),None)
    if not isinstance(esa,dict) or esa.get("configured") is not True:
        return {"eligible":False,"reason":"ROTA_ESA_BIOMASS_FH_SEM_AUDITORIA_VALIDA",
                "evidence":"PRIORITY_ROUTE_AUDIT_INVALID"}
    for route in ([esa] if valid_height_pixels else routes):
        if route.get("catalog_search_complete") is not True or route.get("pagination_complete") is not True:
            return {"eligible":False,"reason":"BUSCA_PRIORITARIA_INCOMPLETA:"+str(route.get("route")),
                    "evidence":"PRIORITY_ROUTE_INCOMPLETE"}
        if route.get("pixel_read_complete") is not True:
            return {"eligible":False,"reason":"LEITURA_PRIORITARIA_INCOMPLETA:"+str(route.get("route")),
                    "evidence":"PRIORITY_ROUTE_INCOMPLETE"}
        if int(route.get("technical_error_count") or 0)>0:
            return {"eligible":False,"reason":"ERRO_TECNICO_NA_ROTA_PRIORITARIA:"+str(route.get("route")),
                    "evidence":"PRIORITY_ROUTE_TECHNICAL_ERROR"}
    fh_found=bool(valid_height_pixels or any(
        isinstance(route.get("valid_pixel_count"),int) and route.get("valid_pixel_count",0)>0
        for route in routes))
    if not fh_found and not (height_certificate.get("status")=="SAR_AUSENCIA_COBERTURA_CONFIRMADA" and all(
            route.get("coverage_absence_confirmed") is True and route.get("valid_pixel_count")==0
            for route in routes)):
        return {"eligible":False,"reason":"SEM_PIXELS_FH_VALIDOS_E_AUSENCIA_NAO_CONFIRMADA",
                "evidence":"PRIORITY_ROUTE_ABSENCE_UNPROVEN"}
    return {"eligible":True,
            "reason":("FH FOI PROCESSADO, MAS O MODELO FH×INVENTARIO NÃO GEROU AGB; ESA CCI L4 É A SEGUNDA ROTA, COM REFERÊNCIAS DE INVENTÁRIOS COMPATÍVEIS." if fh_found else
                      "AUSÊNCIA DE FH CONFIRMADA SEM ERROS; ESA CCI L4 É A SEGUNDA ROTA, COM REFERÊNCIAS DE INVENTÁRIOS COMPATÍVEIS."),
            "evidence":"FH_MODEL_ATTEMPTED_CCI_DIRECT_PRODUCT_SECONDARY" if fh_found else
                      "FH_ABSENCE_CONFIRMED_CCI_DIRECT_PRODUCT_SECONDARY",
            "cci_calibration_required":False,
            "inventory_comparison_required_in_report":True,
            "note":"CCI permanece produto anual AGB L4 com incerteza própria; referências de inventário são apresentadas separadamente e não são somadas nem usadas como calibração implícita."}
