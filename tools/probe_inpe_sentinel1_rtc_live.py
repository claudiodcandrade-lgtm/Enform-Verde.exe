#!/usr/bin/env python3
"""Live INPE Sentinel-1 RTC catalog-to-pixel acceptance probe (no credentials)."""
from __future__ import annotations

import json
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
    results={}
    for label,aoi in national_samples.items():
        provider_results={}
        # Check both public routes. INPE is not required to have a current
        # acquisition at every sample if MPC supplies readable current pixels.
        for provider,reader in (
            ("MPC",lambda:planetary_sentinel1_cog(aoi,Path(cache_root)/label,limit=6)),
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
            diagnostic={provider:{k:v for k,v in r.items() if k!="stats"}
                        for provider,r in provider_results.items()}
            raise AssertionError(f"{label}: MPC e INPE não entregaram par VV/VH recente com >=100 pixels reais: {diagnostic}")
        provider,scene,pair=max(usable,key=lambda item:item[2]["VV"].get("acquisition_utc","") or "")
        acquired=datetime.fromisoformat(pair["VV"]["acquisition_utc"].replace("Z","+00:00"))
        age_days=(datetime.now(timezone.utc)-acquired.astimezone(timezone.utc)).total_seconds()/86400
        if not 0<=age_days<=30:
            raise AssertionError(f"{label}: aquisição fora da janela atual de 30 dias: {acquired.isoformat()}")
        results[label]={"status":"REAL_VV_VH_PIXELS_READ","scene_id":scene,
            "provider":provider,
            "acquisition_utc":pair["VV"]["acquisition_utc"],
            "age_days":round(age_days,2),
            "provider_diagnostics":{name:{k:v for k,v in r.items() if k!="stats"}
                                     for name,r in provider_results.items()},
            "vv_valid_pixels":pair["VV"]["n"],"vh_valid_pixels":pair["VH"]["n"],
            "crs":pair["VV"].get("crs"),
            "temporal_age_note":"Pixels were read from an acquisition no more than 30 days old; this distributed sample is not an exhaustive wall-to-wall guarantee."}
    Path("inpe_sentinel1_rtc_live.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INPE_SENTINEL1_RTC_LIVE_PIXEL_READ_OK "+json.dumps(results,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
