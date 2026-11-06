"""Cross-provider Sentinel-1 RTC discovery in explicit priority order."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from sentinel1_inpe import search_sentinel1_inpe_rtc
from sentinel1_mpc import search_sentinel1_rtc


def search_sentinel1_sources(aoi_geojson, *, start_utc, end_utc):
    """Search MPC first and INPE RTC second; retain per-provider diagnostics.

    A provider error never erases usable scenes returned by another provider.
    An empty result can mean true absence only if every configured public RTC
    catalogue completed pagination successfully.
    """
    results=[]
    all_scenes=[]
    for name,search in (("MPC",search_sentinel1_rtc),("INPE",search_sentinel1_inpe_rtc)):
        try:
            row=search(aoi_geojson,start_utc=start_utc,end_utc=end_utc)
            provider_scenes=row.get("scenes",[])
            for scene in provider_scenes:
                scene.setdefault("provider",name)
            results.append({"provider":name,"status":"OK" if row.get("pagination_complete",True) else "INCOMPLETE",
                            "scene_count":len(provider_scenes),
                            "pagination_complete":bool(row.get("pagination_complete",True))})
            all_scenes.extend(provider_scenes)
        except Exception as exc:
            results.append({"provider":name,"status":"ERRO_TECNICO",
                            "error_type":type(exc).__name__,"pagination_complete":False})
    all_scenes.sort(key=lambda s:str(s.get("acquisition_utc","")),reverse=True)
    return {"status":"discovery_only","providers":results,"scenes":all_scenes,
            "scene_count":len(all_scenes),
            "pagination_complete":all(r.get("pagination_complete") for r in results),
            "queried_at_utc":datetime.now(timezone.utc).isoformat(),
            "warning":"MPC Sentinel-1 RTC is primary; INPE RTC is automatic fallback. Catalog scene counts are not pixel-read evidence."}
