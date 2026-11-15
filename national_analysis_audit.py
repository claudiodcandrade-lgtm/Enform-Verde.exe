"""National AOI audit contract for Brazil. Evidence is not invented.

All locations in Brazil are eligible for attempted source acquisition. Spatial
coverage, confidence, source chronology and experimental status are distinct:
an annual cartographic class is never proof of current SAR land use.
"""
from __future__ import annotations

from datetime import datetime,timezone
from hashlib import sha256
from math import isfinite

BIOMES=("Amazônia","Cerrado","Caatinga","Mata Atlântica","Pantanal","Pampa")
AREA_CRS="EPSG:6933"

def _f(value):
    try:
        v=float(value)
        return v if isfinite(v) else None
    except (TypeError,ValueError,OverflowError):
        return None

def audit_national_coverage(aoi,land,*,biome=None,at_utc=None):
    """Auditable area partition and source-specific uncertainty, fail-closed."""
    if aoi is None or getattr(aoi,"crs",None) is None:
        raise ValueError("AOI deve ter CRS informado para auditoria nacional")
    geo=aoi.to_crs("EPSG:4326").geometry.union_all()
    metric=aoi.to_crs(AREA_CRS).geometry.union_all()
    if geo.is_empty or metric.is_empty or not geo.is_valid:
        raise ValueError("Geometria da AOI vazia/inválida")
    total=float(metric.area)/10000.0
    if not isfinite(total) or total<=0:
        raise ValueError("Área da AOI inválida")
    bounds=geo.bounds
    # WGS84 geographic envelope is a plausibility flag, never a Brazil biome
    # classifier or a pretext to invent land-cover pixels.
    # Includes Fernando de Noronha, Trindade/Martim Vaz, São Pedro e São
    # Paulo and the Brazilian continental extent. This is a plausibility
    # envelope, not a substitute for official territorial intersection.
    within_brazil_bbox=(bounds[0]>=-75.0 and bounds[2]<=-27.0
                        and bounds[1]>=-35.0 and bounds[3]<=7.0)
    strata=[]
    area_by_group={"nativa_mapeada_ha":0.0,"outros_usos_mapeados_ha":0.0,
                   "nao_classificada_ha":0.0}
    for r in land.get("classes") or []:
        ha=_f(r.get("area_ha"))
        if ha is None or ha<0:raise ValueError("Área inválida na classe cartográfica")
        if ha==0:continue
        flag=r.get("native_status")
        group=("nativa_mapeada_ha" if flag is True else
               "outros_usos_mapeados_ha" if flag is False else "nao_classificada_ha")
        area_by_group[group]+=ha
        origin=str(r.get("source") or "SEM_FONTE")
        cartographic=("MAPBIOMAS" in origin or origin=="IBGE")
        eligible_sar=origin.startswith("SAR_VALIDADO")
        strata.append({"class_name":str(r.get("class_name") or "Não identificada"),
            "area_ha":round(ha,6),"source":origin,"cartographic_only":cartographic,
            "current_sar_classification":eligible_sar,
            "local_classification_uncertainty_ha":None,
            "local_classification_accuracy":None,
            "uncertainty_note":("Fonte anual ou referência potencial: não expressa"
              " erro de classificação atual nesta AOI" if cartographic else
              "Exigir matriz de confusão independente por classe/região e "
              "área corrigida por erro para quantificar incerteza espacial")})
    reported=sum(area_by_group.values())
    closure=abs(reported-total)
    closure_tolerance=max(.05,total*.001)
    if closure>closure_tolerance:
        raise ValueError(f"Fechamento cartográfico inconsistente: {closure:.4f} ha")
    source=land.get("recent_sar_cover") or {}
    orbital_status=source.get("status") or "N/D"
    measured=orbital_status=="SAR_REAL_EXPERIMENTAL_CANDIDATES"
    mapped=any(x["current_sar_classification"] for x in strata)
    audit={
        "schema":"enform-national-coverage-audit-v1",
        "processed_utc":(at_utc or datetime.now(timezone.utc)).isoformat(),
        "aoi_sha256_wgs84":sha256(geo.wkb).hexdigest(),
        "analysis_area_crs":AREA_CRS,"aoi_area_ha":round(total,6),
        "brazil_bbox_plausible":within_brazil_bbox,
        "biome_label":biome if biome in BIOMES else "N/D — consulta IBGE necessária",
        "geography_policy":("Aplicação nacional: tentar dados compatíveis em qualquer"
          " bioma brasileiro; indisponibilidade nunca autoriza fabricação de classe, "
          "SAR, carbono ou incerteza"),
        "coverage_groups_ha":{k:round(v,6) for k,v in area_by_group.items()},
        "coverage_groups_pct":{k:round(100*v/total,4) for k,v in area_by_group.items()},
        "area_closure_error_ha":round(closure,6),
        "area_closure_tolerance_ha":round(closure_tolerance,6),
        "strata_provenance":strata,
        "current_sar_observation":"PIXELS_REAIS" if measured else "N/D",
        "current_sar_observation_reason":None if measured else str(source.get("reason") or "não verificada"),
        "latest_sar_acquisition_utc":source.get("latest_acquisition_utc") if measured else None,
        "sar_scene_ids":source.get("scene_ids") if measured else [],
        "sar_candidate_area_ha":source.get("areas_ha") if measured else None,
        "current_sar_classification":"SAR_VALIDADO_CLASSE_ESPECIFICA" if mapped else "N/D — SEM_CLASSIFICADOR_ATUAL_VALIDADO",
        "sar_candidate_uncertainty_ha":None,
        "cartographic_classification_uncertainty_ha":None,
        "uncertainty_policy":("Sem amostras independentes compatíveis: erro de máscara"
          " e acurácia de classes = N/D; percentuais mapeados NÃO têm IC95%."
          " Séries SAR heurísticas são candidatas, não classes validadas."),
        "mathematics":{"area":"Área = area(intersecção projetada em EPSG:6933)/10000",
                       "percent":"100 * area_classe_ha / area_AOI_ha",
                       "area_closure":"sum(areas_exclusivas_ha)-area_AOI_ha",
                       "uncertainty":"N/D onde não há estimador validado; não converter dispersão temporal em IC95%"},
        "audit_reproducibility":{"pixel_source":source.get("method") if measured else None,
             "raster_path":source.get("raster_path") if measured else None,
             "vector_path":source.get("vector_path") if measured else None,
             "source_dates":"see scene IDs and acquisition timestamps; keep original sources"},
        "warnings":[("Limite territorial fora do envelope aproximado do Brasil; "
                     "conferir CRS/coordenadas" if not within_brazil_bbox else
                     "Cobertura nacional potencial: disponibilidade real varia por AOI e sensor")]}
    return audit
