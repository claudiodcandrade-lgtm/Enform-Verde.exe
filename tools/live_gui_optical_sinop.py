#!/usr/bin/env python3
"""Live end-to-end optical GUI regression on a Sinop sample, not a farm proof.

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

def rendered_optical_status(provider, visible, photo_size, canvas_image_count):
    """Return PASS only for a CBERS/Sentinel-2 photo actually drawn on canvas."""
    provider=str(provider or "").strip().casefold()
    if not visible or not photo_size or min(photo_size)<=0 or canvas_image_count<1:
        return None
    if "cbers-4a/wfi" in provider:
        return "PASS_CBERS"
    if "sentinel-2" in provider:
        return "PASS_SENTINEL2_FALLBACK"
    # Other backdrops (VIIRS, web mosaics, cartography) are not the two
    # specified medium-resolution optical sources and cannot satisfy this gate.
    return None


def main(timeout=180):
    import desktop_app as app
    import geopandas as gpd
    from shapely.geometry import box
    test_aoi=gpd.GeoDataFrame(
        geometry=[box(-55.205,-11.888,-55.175,-11.858)],crs="EPSG:4326")
    window=app.App()
    status="NOT_STARTED"
    result={"scope":"Sinop centroid vicinity, NOT original KML",
            "mode":"real CBERS-4A or Sentinel-2 via Tk worker queue and canvas",
            "accepted_sources":["CBERS-4A/WFI","Sentinel-2"],
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
            photo=getattr(window,"google_map_photo",None)
            photo_size=(photo.width(),photo.height()) if photo is not None else None
            image_count=sum(window.map_canvas.type(item)=="image" for item in canvas_items)
            passed=rendered_optical_status(provider,visible,photo_size,image_count)
            if passed:
                result.update(status=passed,provider=provider,
                              canvas_items=len(canvas_items),canvas_image_items=image_count,
                              image_width=photo_size[0],image_height=photo_size[1])
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
    return 0 if result["status"] in ("PASS_CBERS","PASS_SENTINEL2_FALLBACK") else 1


if __name__=="__main__":
    raise SystemExit(main())
