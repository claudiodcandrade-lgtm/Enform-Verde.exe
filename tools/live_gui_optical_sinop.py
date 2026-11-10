#!/usr/bin/env python3
"""Live end-to-end CBERS-4A GUI regression on a Sinop sample, not a farm proof.

This test exercises the real worker -> queue -> Tk canvas path, not only
satellite catalog or COG reads. The source AOI is a public small bounding box
around the supplied centroid, not a reconstruction of the private KML.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

import geopandas as gpd
from shapely.geometry import box


def main(timeout=180):
    import desktop_app as app
    test_aoi=gpd.GeoDataFrame(
        geometry=[box(-55.205,-11.888,-55.175,-11.858)],crs="EPSG:4326")
    window=app.App()
    status="NOT_STARTED"
    result={"scope":"Sinop centroid vicinity, NOT original KML",
            "mode":"real CBERS-4A via Tk worker queue and canvas",
            "optical_retrieval_is_not_landcover_classification":True}
    try:
        window.update()
        window.gdf=test_aoi
        window._map_extent_factor=1.36
        window.show_google_map(refresh=False,prefer_public=True)
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            window.update()
            provider=str(getattr(window,"_map_provider","") or "")
            visible=bool(getattr(window,"_satellite_map_visible",False))
            canvas_items=window.map_canvas.find_all()
            has_photo=getattr(window,"google_map_photo",None) is not None
            if visible and provider.startswith("CBERS-4A/WFI") and has_photo and canvas_items:
                result.update(status="PASS",provider=provider,
                              canvas_items=len(canvas_items),
                              image_width=window.google_map_photo.width(),
                              image_height=window.google_map_photo.height())
                break
            if visible and provider.startswith(("Sentinel-2","NASA GIBS","CACHE","MAPA CARTOGRÁFICO")):
                # Capture CBERS failure; alternatives are not proof of priority.
                result.update(status="FALLBACK_ONLY",provider=provider)
                break
            time.sleep(0.12)
        else:
            result["status"]="TIMEOUT"
        result["last_ui_status"]=str(window.status.get())[:350]
    except Exception as exc:
        result.update(status="ERROR",error_type=type(exc).__name__,
                      message=str(exc)[:300])
    finally:
        try:window.destroy()
        except Exception:pass
    output=ROOT/"optical_gui_sinop_live.json"
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
