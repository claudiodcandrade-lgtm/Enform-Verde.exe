#!/usr/bin/env python3
"""Experimental real-SAR semantic polygons for a fixed test box near Sinop.

This is explicitly NOT the Fazenda Maria Eduarda KML and does not prove
contemporaneous 2026/27 conditions. Uses the last complete Oct-Sep season.
"""
import json
import sys
import traceback
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import geopandas as gpd
from shapely.geometry import box

OUT=Path("sinop_sar_semantic_experimental")
OUT.mkdir(exist_ok=True)


def build_report_header(sample_box_area_ha, started_at=None):
    """Name the fixed sample scope so its areas cannot be read as farm totals."""
    return {
        "status": "STARTED",
        "scope": "fixed 0.03-degree test box near Sinop centroid; NOT original KML",
        "sample_box_area_ha": float(sample_box_area_ha),
        "reference_farm_area_ha_not_processed": 1459.91,
        "data_origin": "Sentinel-1 RTC VV/VH observed SAR pixels",
        "claim": "experimental model inference from last complete agricultural year",
        "field_validated": False,
        "current_sowing_season_2026_27_verified": False,
        "mapbiomas_or_ibge_used_as_current_labels": False,
        "started_at_utc": started_at or datetime.now(timezone.utc).isoformat(),
    }


def summarize_sample_box(sample_box_area_ha, class_areas_ha):
    """Summarize only the fixed test box; never label it as farm-area totals."""
    class_areas = {str(name): float(area) for name, area in class_areas_ha.items()}
    classified = float(sum(class_areas.values()))
    return {
        "sample_box_polygon_area_by_class_ha": class_areas,
        "sample_box_polygon_area_ha": classified,
        "sample_box_unclassified_area_ha": max(
            0.0, float(sample_box_area_ha) - classified),
    }


def _load_aoi(path, label):
    if path is None:
        if label != "Sinop":
            raise ValueError("AOI_PATH_REQUIRED_FOR_" + label.upper())
        return gpd.GeoDataFrame(geometry=[box(-55.205498,-11.887667,
                                               -55.175498,-11.857667)],crs="EPSG:4326")
    path=Path(path)
    if path.suffix.casefold()==".kmz":
        import zipfile
        with zipfile.ZipFile(path) as archive:
            member=next((n for n in archive.namelist() if n.casefold().endswith(".kml")),None)
            if member is None:raise ValueError("KMZ_SEM_KML")
            local=OUT/(label.lower()+"_input.kml")
            local.write_bytes(archive.read(member))
            path=local
    frame=gpd.read_file(path)
    if frame.empty or frame.crs is None:
        raise ValueError("AOI_VAZIA_OU_CRS_AUSENTE_"+label.upper())
    return frame


def _run_full_handoff(label, aoi):
    import hashlib
    import uuid
    from analysis_pipeline_contract import geometry_hash
    from desktop_app import native_carbon_analysis, _native_carbon_failure_result, _sar_dashboard_payload
    from land_use_sar import run_land_use, report_lines
    area_ha=float(aoi.to_crs(6933).geometry.area.sum()/1e4)
    run_id=uuid.uuid4().hex[:12].upper()
    aoi_hash=geometry_hash(aoi)
    out=OUT/label.lower()
    out.mkdir(parents=True,exist_ok=True)
    report={"label":label,"area_aoi_ha":area_ha,"analysis_run_id":run_id,
            "aoi_hash_sha256":aoi_hash,"field_validated":False,
            "data_origin":"Sentinel-1 RTC VV/VH pixels and ENFORM_SAR_BRASIL_RF_V2",
            "scope":"AOI de teste integral fornecida ao runner; resultados experimentais, sem validação local"}
    land=run_land_use(aoi,out/"land_use",ibge=None)
    land["analysis_run_id"]=run_id
    land["aoi_hash_sha256"]=aoi_hash
    report["land_use"]={k:land.get(k) for k in
        ("status","current_sar_crop_identification","sar_model_config","sar_selection",
         "area_aoi_ha","classes","warnings","sar_classifier_lemplus")}
    lemplus_audit=land.get("sar_classifier_lemplus") or {}
    annual_applied=bool(lemplus_audit.get("result_applied_to_annual_map"))
    current_applied=bool(lemplus_audit.get("result_applied_to_current_aoi"))
    if not (annual_applied or current_applied):
        raise RuntimeError(label+": CLASSIFICADOR_SAR_NAO_PRODUZIU_MAPA_ANUAL_NEM_ATUAL: "+
                           str(lemplus_audit.get("reason")))
    report["sar_temporal_handoff"]={
        "annual_map_applied":annual_applied,
        "annual_season":lemplus_audit.get("season"),
        "annual_scope":lemplus_audit.get("temporal_scope"),
        "current_semantic_result_applied":current_applied,
        "current_semantic_status":land.get("current_semantic_classification_status"),
        "alternative_radar_status":(land.get("alternative_radar_screen") or {}).get("status"),
        "alternative_radar_trigger":(land.get("alternative_radar_screen") or {}).get("trigger_reason")}
    classes=land.get("classes") or []
    semantic=[r for r in classes if str(r.get("source") or "").startswith(
        ("SAR_VALIDADO","SAR_EXPERIMENTAL_MODELO"))]
    if not semantic:
        raise RuntimeError(label+": MASCARA_SEMANTICA_NAO_CHEGOU_AO_RESUMO_DE_USO_DO_SOLO")
    class_area=sum(float(r.get("area_ha") or 0.0) for r in classes)
    if abs(class_area-area_ha)>max(0.02,area_ha*1e-6):
        raise RuntimeError(label+": FECHAMENTO_DE_AREA_DIVERGENTE")
    native_semantic=[r for r in semantic if r.get("native_status") is True]
    if not native_semantic:
        raise RuntimeError(label+": MASCARA_NATIVA_SAR_NAO_CHEGOU_AO_PONTO_DE_ENTRADA_DO_CARBONO")
    try:
        native=native_carbon_analysis(aoi,land,"Amazônia")
    except Exception as exc:
        native=_native_carbon_failure_result(aoi,exc)
        report["carbon_stage_exception"]=type(exc).__name__+": "+str(exc)[:300]
    native["analysis_run_id"]=run_id
    native["aoi_hash_sha256"]=aoi_hash
    strata=native.get("strata") or []
    native_names={str(r.get("class_name")) for r in native_semantic}
    received={str(r.get("class_name")) for r in strata}
    if not received.intersection(native_names):
        raise RuntimeError(label+": ESTRATOS_NATIVOS_SAR_NAO_CHEGARAM_AO_MODULO_DE_CARBONO")
    dashboard=_sar_dashboard_payload(native,land)
    semantic_payload=dashboard.get("semantic_land_use") or {}
    if not semantic_payload.get("classes"):
        raise RuntimeError(label+": MASCARAS_SEMANTICAS_AUSENTES_NO_PAYLOAD_DO_DASHBOARD")
    if dashboard.get("analysis_run_id")!=run_id or dashboard.get("aoi_hash_sha256")!=aoi_hash:
        raise RuntimeError(label+": IDENTIDADE_DA_AOI_OU_EXECUCAO_PERDIDA_NO_DASHBOARD")
    dashboard_classes=semantic_payload["classes"]
    if {(r.get("class_name"),r.get("source")) for r in dashboard_classes} != {
        (r.get("class_name"),r.get("source")) for r in semantic}:
        raise RuntimeError(label+": CLASSES_SAR_DIVERGEM_ENTRE_CORE_E_DASHBOARD")
    report["carbon"]={
        "status":native.get("status"),"native_area_ha":native.get("native_area_ha"),
        "known_total_tc":native.get("known_total_tc"),
        "known_total_tco2":native.get("known_total_tco2"),
        "complete":native.get("complete"),"strata_count":len(strata),
        "strata_class_names":sorted(received),
        "component_statuses":[{"class_name":st.get("class_name"),
            "components":[{"parametro":c.get("parametro"),"tc":c.get("tc"),
                "origem":c.get("origem"),"fonte":c.get("fonte"),
                "uncertainty":c.get("uncertainty"),"obs":c.get("obs")}
                for c in st.get("components",[])]} for st in strata],
        "uncertainty_note":native.get("uncertainty_note"),
        "exception":report.get("carbon_stage_exception")}
    report["dashboard"]={
        "status":dashboard.get("status"),
        "semantic_status":semantic_payload.get("status"),
        "class_count":semantic_payload.get("class_count"),
        "class_area_ha":semantic_payload.get("area_ha"),
        "analysis_run_id":dashboard.get("analysis_run_id"),
        "aoi_hash_sha256":dashboard.get("aoi_hash_sha256")}
    report["execution_status"]="SAR_TO_LAND_USE_TO_CARBON_TO_DASHBOARD_HANDOFF_PASSED"
    (out/"land_use_report.txt").write_text("\n".join(report_lines(land)),encoding="utf-8")
    (out/"carbon_handoff.json").write_text(json.dumps(report["carbon"],ensure_ascii=False,
        indent=2,default=str),encoding="utf-8")
    (out/"dashboard_payload.json").write_text(json.dumps(dashboard,ensure_ascii=False,
        indent=2,default=str),encoding="utf-8")
    (out/"end_to_end_report.json").write_text(json.dumps(report,ensure_ascii=False,
        indent=2,default=str),encoding="utf-8")
    return report


def run():
    reports=[]
    try:
        sinop=_load_aoi(None,"Sinop")
        reports.append(_run_full_handoff("Sinop_amostra_003graus",sinop))
        tapajos_path=next((p for p in sys.argv[1:] if p.lower().endswith((".kml",".kmz"))),None)
        if not tapajos_path:
            raise ValueError("TAPAJOS_ACCEPTANCE_KML_OR_KMZ_REQUIRED")
        tapajos=_load_aoi(tapajos_path,"Tapajos")
        reports.append(_run_full_handoff("Tapajos",tapajos))
        aggregate={"status":"BOTH_AOIS_END_TO_END_HANDOFF_PASSED","aois":reports,
                   "farm_kml_included":False,
                   "limitations":["Sinop uses fixed public sample box, not Fazenda Maria Eduarda KML.",
                                  "Both semantic masks remain experimental until local field validation."]}
        (OUT/"end_to_end_acceptance.json").write_text(
            json.dumps(aggregate,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        print(json.dumps(aggregate,ensure_ascii=False,default=str))
        return 0
    except Exception as exc:
        failure={"status":"END_TO_END_HANDOFF_FAILED","failure_type":type(exc).__name__,
                 "failure_reason":str(exc).split("?")[0][:500],"completed_aois":reports}
        (OUT/"end_to_end_acceptance.json").write_text(
            json.dumps(failure,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        print(json.dumps(failure,ensure_ascii=False,default=str))
        return 1


if __name__=="__main__":
    sys.exit(run())
