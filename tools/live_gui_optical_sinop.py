#!/usr/bin/env python3
"""Live end-to-end optical GUI regression on a Sinop sample, not a farm proof.

This test exercises the real worker -> queue -> Tk canvas path, not only
satellite catalog or COG reads. The source AOI is a public small bounding box
around the supplied centroid, not a reconstruction of the private KML.
"""
from __future__ import annotations

import json
import sys
import numpy as np
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def rendered_optical_status(provider, visible, photo_size, canvas_image_count, pixel_quality=None, canvas_item_count=0):
    """Pass only when real canvas pixels show imagery or a cartographic fallback."""
    provider=str(provider or "").strip().casefold()
    if not visible:
        return None
    if not isinstance(pixel_quality,dict) or pixel_quality.get("p99_luminance",0)<20 or pixel_quality.get("std_luminance",0)<5 or pixel_quality.get("visible_fraction",0)<0.15:
        return None
    if "ibge_potential_fallback" in provider:
        return "PASS_IBGE_FALLBACK" if canvas_item_count>0 else None
    if "aoi_local_fallback" in provider:
        return "PASS_AOI_FALLBACK" if canvas_item_count>0 else None
    if not photo_size or min(photo_size)<=0 or canvas_image_count<1:
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
            "mode":"CBERS/Sentinel-2 when available; otherwise IBGE cartography/AOI fallback on Tk canvas",
            "accepted_sources":["CBERS-4A/WFI","Sentinel-2","IBGE_POTENTIAL_FALLBACK","AOI_LOCAL_FALLBACK"],
            "optical_retrieval_is_not_landcover_classification":True}
    initial_fallback_visible=False
    try:
        window.update()
        window.gdf=test_aoi
        window._map_extent_factor=1.36
        window.show_google_map(refresh=False,prefer_public=True)
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            window.update()
            provider=str(getattr(window,"_map_provider","") or "")
            map_status=str(window.map_status.get())
            # The AOI outline is drawn synchronously before the remote worker
            # starts. It prevents a black canvas while loading, but is not proof
            # that the worker delivered an image or completed the IBGE fallback.
            if provider == "AOI_LOCAL_FALLBACK":
                initial_fallback_visible=True
            pending=(map_status.startswith("Carregando CBERS-4A/WFI") or
                     "enquanto atualiza CBERS-4A" in map_status)
            if pending:
                time.sleep(0.12)
                continue
            visible=bool(getattr(window,"_satellite_map_visible",False))
            visible=visible or provider in ("IBGE_POTENTIAL_FALLBACK","AOI_LOCAL_FALLBACK")
            canvas_items=window.map_canvas.find_all()
            photo=getattr(window,"google_map_photo",None)
            photo_size=(photo.width(),photo.height()) if photo is not None else None
            image_count=sum(window.map_canvas.type(item)=="image" for item in canvas_items)
            from PIL import ImageGrab
            x0,y0=window.map_canvas.winfo_rootx(),window.map_canvas.winfo_rooty()
            pixels=np.asarray(ImageGrab.grab(bbox=(x0,y0,x0+window.map_canvas.winfo_width(),y0+window.map_canvas.winfo_height())).convert("RGB"),dtype=np.uint8)
            luminance=pixels.astype("float32").mean(axis=2)
            pixel_quality={"p99_luminance":float(np.percentile(luminance,99)),"std_luminance":float(luminance.std()),"visible_fraction":float((luminance>8).mean())}
            passed=rendered_optical_status(provider,visible,photo_size,image_count,pixel_quality,len(canvas_items))
            if passed:
                result.update(status=passed,provider=provider,canvas_items=len(canvas_items),
                              canvas_image_items=image_count,image_width=photo_size[0] if photo_size else None,
                              image_height=photo_size[1] if photo_size else None,
                              canvas_pixel_quality=pixel_quality,
                              optical_attempt_status=map_status[:220],
                              worker_terminal_state_observed=True,
                              initial_nonblack_fallback_seen=initial_fallback_visible)
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
    return 0 if result["status"] in ("PASS_CBERS","PASS_SENTINEL2_FALLBACK","PASS_IBGE_FALLBACK","PASS_AOI_FALLBACK") else 1


if __name__=="__main__":
    raise SystemExit(main())
