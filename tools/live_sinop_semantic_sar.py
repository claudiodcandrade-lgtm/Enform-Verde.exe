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
from sar_landcover_lemplus import classify_aoi, in_validated_domain

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


def run():
    # Fixed AOI only illustrates the API working over REAL SAR observations;
    # it is not a substitute for the owner's complete polygon.
    aoi=gpd.GeoDataFrame(geometry=[box(-55.205498,-11.887667,
                                      -55.175498,-11.857667)],crs="EPSG:4326")
    area_ha=float(aoi.to_crs(6933).geometry.area.sum()/1e4)
    report=build_report_header(area_ha)
    try:
        eligible,reason=in_validated_domain(None,aoi=aoi)
        report["model_domain_status"]=reason
        if not eligible:raise ValueError("MODEL_DOMAIN_NOT_ELIGIBLE")
        result=classify_aoi(aoi,as_of=date(2026,11,10))
        report.update({"status":result["status"],"season":result.get("season"),
            "reason":result.get("reason"),"acquisition_diagnostic":result.get("acquisition_diagnostic"),
            "model_id":result.get("model_id"),"model_sha256":result.get("model_sha256"),
            "scenes_used":result.get("scenes_used"),"observed_months":result.get("observed_months"),
            "pixel_count":result.get("pixels"),"class_accuracy_training":result.get("landcover_overall_accuracy"),
            "class_accuracy_training_ci95":result.get("landcover_overall_accuracy_wilson95"),
            "classes":result.get("classes",[])})
        polys=result.get("polygons_6933")
        if polys is None or polys.empty:
            raise RuntimeError("NO_SEMANTIC_POLYGONS_OBSERVED")
        # Exact intersections in EPSG:6933, instead of pixels times nominal area.
        polys=polys.to_crs(6933).copy()
        polys["area_ha"]=polys.geometry.area/10000.
        polys["validation_status"]="EXPERIMENTAL_NO_LOCAL_FIELD_VALIDATION"
        polys["season"]=result["season"]
        polys.to_file(OUT/"sinop_semantic_polygons.geojson",driver="GeoJSON")
        class_areas={
            str(row.class_name):float(row.area_ha)
            for row in polys.itertuples()}
        report.update(summarize_sample_box(area_ha, class_areas))
        report["ready_for_property_transfer"]=False
        report["status"]="SAR_EXPERIMENTAL_POLYGONS_OBSERVED"
    except Exception as exc:
        report["status"]="FAILED_DIAGNOSTIC"
        report["failure_type"]=type(exc).__name__
        report["failure_reason"]=str(exc).split("?")[0][:300]
    finally:
        report["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
        (OUT/"sinop_experimental_report.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        print(json.dumps(report,ensure_ascii=False,default=str))
    return 0 if report["status"]=="SAR_EXPERIMENTAL_POLYGONS_OBSERVED" else 1


if __name__=="__main__":
    sys.exit(run())
