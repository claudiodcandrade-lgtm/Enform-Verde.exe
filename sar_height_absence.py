"""Fail-closed gate for regional height-chart fallback."""


def build_height_absence_certificate(esa_search_audit, esa_height_result, gtdx_result):
    """Build an AOI-scoped absence proof only from complete live route audits."""
    esa_queries=(esa_search_audit or {}).get("queries") or []
    fh_queries=[q for q in esa_queries if q.get("product_type") in {"FP_FH__L2A","FP_FH__L2B"}]
    esa_search_ok=(len(fh_queries)==4 and all(
        q.get("catalog_search_complete") is True and q.get("pagination_complete") is True
        and q.get("technical_error_count")==0 for q in fh_queries))
    esa_empty=bool(esa_search_ok and all(q.get("matching_product_count")==0 for q in fh_queries))
    esa_read_ok=(esa_empty or bool((esa_height_result or {}).get("pixel_read_complete") is True
        and (esa_height_result or {}).get("technical_error_count")==0
        and (esa_height_result or {}).get("valid_pixel_count")==0))
    esa_route={"route":"ESA_BIOMASS_FH","configured":True,
        "catalog_search_complete":esa_search_ok,"pagination_complete":esa_search_ok,
        "pixel_read_complete":esa_read_ok,
        "coverage_absence_confirmed":esa_empty and esa_read_ok,
        "valid_pixel_count":0 if esa_empty and esa_read_ok else (esa_height_result or {}).get("valid_pixel_count"),
        "technical_error_count":sum(int(q.get("technical_error_count") or 0) for q in fh_queries)
            +int((esa_height_result or {}).get("technical_error_count") or 0)}
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
