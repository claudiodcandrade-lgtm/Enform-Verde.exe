#!/usr/bin/env python3
"""Live INPE Sentinel-1 RTC catalog-to-pixel acceptance probe (no credentials)."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import gettempdir

import geopandas as gpd
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from desktop_app import read_vector
from sar_pipeline import inpe_sentinel1_rtc, planetary_sentinel1_cog


def main() -> int:
    tapajos=read_vector("acceptance/Teste_SAR_Biomassa_Tapajos.kmz")
    def sample(lon,lat):
        # About 4.4 km on a side: enough pixels to test COG clipping without
        # depending on a private property or one particular municipality.
        return gpd.GeoDataFrame(geometry=[box(lon-.02,lat-.02,lon+.02,lat+.02)],crs="EPSG:4326")
    national_samples={
        "Amazonia_Manaus":sample(-60.02,-3.10),
        "Amazonia_Sinop":sample(-55.19,-11.87),
        "Cerrado_Brasilia":sample(-47.93,-15.78),
        "Caatinga_Petrolina":sample(-40.50,-9.39),
        "MataAtlantica_SaoPaulo":sample(-46.63,-23.55),
        "Pantanal_Corumba":sample(-57.65,-19.00),
        "Pampa_Bage":sample(-54.10,-31.33),
        "Amazonia_Tapajos_AOI":tapajos,
    }
    cache_root=Path(gettempdir())/"enform_sentinel1_national_probe"
    cache_root.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"eight representative AOIs across six Brazilian biomes; not wall-to-wall coverage",
            "required_pair":"same-acquisition VV and VH, each with at least 100 valid pixels, acquisition <=30 days",
            "sites":{},"status":"IN_PROGRESS"}
    report_path=Path("inpe_sentinel1_rtc_live.json")
    def safe_diagnostics(provider_results):
        def redact(value):
            if isinstance(value, str):
                return re.sub(r"https?://\S+", "<asset-url-redacted>", value)[:300]
            if isinstance(value, list):
                return [redact(x) for x in value[:8]]
            if isinstance(value, dict):
                return {str(k): redact(v) for k, v in value.items()
                        if str(k).casefold() not in {"href", "url", "signed_url"}}
            return value
        safe={}
        for provider,result in provider_results.items():
            row={k:v for k,v in result.items() if k not in {"stats","paths","partial_paths"}}
            safe[provider]=redact(row)
        return safe
    def save_report():
        report["status"]=("PASS_DISTRIBUTED_SAMPLE" if report["sites"] and all(
            x.get("status")=="REAL_VV_VH_PIXELS_READ" for x in report["sites"].values()) else "NOT_PASSED")
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for label,aoi in national_samples.items():
        provider_results={}
        # Check both public routes. INPE is not required to have a current
        # acquisition at every sample if MPC supplies readable current pixels.
        for provider,reader in (
            ("MPC",lambda:planetary_sentinel1_cog(aoi,Path(cache_root)/label,limit=1)),
            ("INPE",lambda:inpe_sentinel1_rtc(aoi,days=30,limit=6)),
        ):
            try:
                provider_results[provider]=reader()
            except Exception as exc:
                provider_results[provider]={"pixel_state":"ERRO_TECNICO",
                    "error_type":type(exc).__name__,"error":str(exc)[:240],"stats":[]}
        usable=[]
        for provider,result in provider_results.items():
            by_scene={}
            for row in result.get("stats",[]):
                scene_id=row.get("scene")
                if scene_id:
                    by_scene.setdefault(scene_id,{})[row["polarization"]]=row
            usable.extend((provider,scene,pair) for scene,pair in by_scene.items()
                          if {"VV","VH"}<=set(pair) and
                          min(pair["VV"].get("n",0),pair["VH"].get("n",0))>=100)
        if not usable:
            report["sites"][label]={"status":"NO_RECENT_SAME_SCENE_VV_VH_PIXELS",
                "provider_diagnostics":safe_diagnostics(provider_results)}
            save_report()
            print("SENTINEL1_SAMPLE_NOT_PASSED "+json.dumps({"site":label,
                  "provider_diagnostics":report["sites"][label]["provider_diagnostics"]},ensure_ascii=False))
            continue
        provider,scene,pair=max(usable,key=lambda item:item[2]["VV"].get("acquisition_utc","") or "")
        try:
            acquired=datetime.fromisoformat(pair["VV"]["acquisition_utc"].replace("Z","+00:00"))
            age_days=(datetime.now(timezone.utc)-acquired.astimezone(timezone.utc)).total_seconds()/86400
        except (AttributeError, TypeError, ValueError) as exc:
            report["sites"][label]={"status":"ERRO_TECNICO_INVALID_ACQUISITION_TIME",
                "scene_id":scene,"provider":provider,"error":str(exc)[:240],
                "provider_diagnostics":safe_diagnostics(provider_results)}
            save_report()
            print("SENTINEL1_SAMPLE_NOT_PASSED "+json.dumps({"site":label,
                  "status":report["sites"][label]["status"]},ensure_ascii=False))
            continue
        if not 0<=age_days<=30:
            report["sites"][label]={"status":"NO_RECENT_SAME_SCENE_VV_VH_PIXELS",
                "scene_id":scene,"provider":provider,"acquisition_utc":acquired.isoformat(),
                "age_days":round(age_days,2),"provider_diagnostics":safe_diagnostics(provider_results)}
            save_report()
            print("SENTINEL1_SAMPLE_NOT_PASSED "+json.dumps({"site":label,
                  "status":report["sites"][label]["status"],"age_days":round(age_days,2)},ensure_ascii=False))
            continue
        report["sites"][label]={"status":"REAL_VV_VH_PIXELS_READ","scene_id":scene,
            "provider":provider,
            "acquisition_utc":pair["VV"]["acquisition_utc"],
            "age_days":round(age_days,2),
            "provider_diagnostics":safe_diagnostics(provider_results),
            "vv_valid_pixels":pair["VV"]["n"],"vh_valid_pixels":pair["VH"]["n"],
            "crs":pair["VV"].get("crs"),
            "temporal_age_note":"Pixels were read from an acquisition no more than 30 days old; this distributed sample is not an exhaustive wall-to-wall guarantee."}
        save_report()
        print("SENTINEL1_SAMPLE_OK "+json.dumps({"site":label,**report["sites"][label]},ensure_ascii=False))
    save_report()
    print("INPE_SENTINEL1_RTC_LIVE_REPORT "+json.dumps(report,ensure_ascii=False))
    return 0 if report["status"]=="PASS_DISTRIBUTED_SAMPLE" else 1


if __name__=="__main__":
    raise SystemExit(main())
