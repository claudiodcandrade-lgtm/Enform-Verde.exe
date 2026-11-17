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
    """Pass only when real optical imagery is visible as a Tk canvas image."""
    provider=str(provider or "").strip().casefold()
    if not visible or not photo_size or min(photo_size)<=0 or canvas_image_count<1:
        return None
    if not isinstance(pixel_quality,dict):
        return None
    if pixel_quality.get("p99_luminance",0)<20 or pixel_quality.get("std_luminance",0)<5 or pixel_quality.get("visible_fraction",0)<0.15:
        return None
    if "cbers-4a/wfi" in provider:
        return "PASS_CBERS"
    if "sentinel-2" in provider:
        return "PASS_SENTINEL2_FALLBACK"
    if "nasa gibs" in provider or "viirs" in provider or "esri_world_imagery" in provider or "cache óptico" in provider:
        return "PASS_OPTICAL_IMAGE_FALLBACK"
    return None


def scale_canvas_bbox(root_x, root_y, width, height, tk_screen_size, screenshot_size):
    """Convert Tk logical screen coordinates to ImageGrab physical pixels."""
    tk_width, tk_height = (max(1, int(value)) for value in tk_screen_size)
    shot_width, shot_height = (max(1, int(value)) for value in screenshot_size)
    sx, sy = shot_width / tk_width, shot_height / tk_height
    left = round(int(root_x) * sx)
    top = round(int(root_y) * sy)
    right = round((int(root_x) + max(1, int(width))) * sx)
    bottom = round((int(root_y) + max(1, int(height))) * sy)
    return left, top, max(left + 1, right), max(top + 1, bottom)


def fit_window_geometry(screen_size, desired_width=1024, desired_height=680, margin=0):
    """Return a desktop-filling Tk geometry without exceeding screen bounds.

    The application itself has a 1024 px minimum width. Keeping the test
    window narrower than that makes Tk silently expand it around the requested
    origin, which can place the canvas outside a 1024 px hosted desktop.
    """
    screen_width, screen_height = (max(1, int(value)) for value in screen_size)
    margin = max(0, int(margin))
    width = min(max(1, int(desired_width)), max(1, screen_width - 2 * margin))
    height = min(max(1, int(desired_height)), max(1, screen_height - 2 * margin))
    left = margin
    top = margin
    return f"{width}x{height}+{left}+{top}"


def capture_bbox_is_visible(bbox, screenshot_size):
    """Require the entire canvas crop to lie inside captured desktop pixels."""
    if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
        return False
    width, height = (max(1, int(value)) for value in screenshot_size)
    left, top, right, bottom = (int(value) for value in bbox)
    return 0 <= left < right <= width and 0 <= top < bottom <= height


def scroll_fraction_for_target(map_root_y, scroll_root_y, current_fraction,
                               scrollregion_height, target_root_y):
    """Return an outer Tk-canvas yview fraction that brings the map to a target."""
    total=max(1,int(scrollregion_height))
    offset=min(total,max(0,round(float(current_fraction)*total)))
    map_content_y=int(map_root_y)-int(scroll_root_y)+offset
    wanted_offset=map_content_y-(int(target_root_y)-int(scroll_root_y))
    return max(0.0,min(1.0,wanted_offset/total))


def canvas_height_fitting_window(window_bottom, screen_bottom, canvas_root_y,
                                 requested=560, margin=24, minimum=180):
    """Fit canvas inside both the app window and captured desktop, or return 0."""
    available=min(int(window_bottom),int(screen_bottom))-int(margin)-int(canvas_root_y)
    return min(max(0,int(requested)),available) if available>=int(minimum) else 0


def main(timeout=180):
    import desktop_app as app
    import geopandas as gpd
    from shapely.geometry import box
    test_aoi=gpd.GeoDataFrame(
        geometry=[box(-55.205,-11.888,-55.175,-11.858)],crs="EPSG:4326")
    window=app.App()
    status="NOT_STARTED"
    result={"scope":"Sinop centroid vicinity, NOT original KML",
            "mode":"real optical source through provider retrieval, UI queue and visible Tk canvas",
            "accepted_sources":["CBERS-4A/WFI","Sentinel-2","NASA GIBS VIIRS","Esri World Imagery","optical cache"],
            "optical_retrieval_is_not_landcover_classification":True}
    screen=None
    capture_bbox=None
    try:
        # Hosted Windows runners can leave the Tk root behind another desktop
        # window; ImageGrab then measures the obscuring window instead of the
        # canvas. Make the live test surfaceable before capturing its pixels.
        window.deiconify()
        window.lift()
        try:window.attributes("-topmost",True)
        except Exception:pass
        screen_size=(window.winfo_screenwidth(),window.winfo_screenheight())
        # App.__init__ applies a desktop-oriented minimum size. The CI runner
        # can be exactly 1024x768, so let the live smoke use all available
        # desktop pixels and allow its map canvas to contract with the window.
        window.minsize(800,600)
        window.geometry(fit_window_geometry(screen_size))
        window.update_idletasks()
        window.update()
        window.gdf=test_aoi
        window._map_extent_factor=1.36
        # The map canvas lives on notebook tab 1; Tk reports its canvas as
        # non-viewable until that page is selected. A successful worker result
        # on a hidden tab is not a visible GUI result.
        window.nb.select(window.tabs[1])
        window.update_idletasks()
        window.update()
        # The Spatial page is intentionally vertically scrollable: its IBGE
        # summary and controls precede the map. Move that outer page to the
        # map area before measuring the canvas; merely selecting the tab can
        # leave a real, viewable canvas below the fold of a 768 px desktop.
        spatial_scroll=next((child for child in window.tabs[1].winfo_children()
                             if isinstance(child,app.tk.Canvas)),None)
        def place_map_in_scroll_view():
            if spatial_scroll is None:
                return
            region=spatial_scroll.bbox("all")
            if not region:
                return
            total=max(1,int(region[3])-int(region[1]))
            yview=spatial_scroll.yview()
            outer_y=int(spatial_scroll.winfo_rooty())
            target_y=outer_y+12
            fraction=scroll_fraction_for_target(
                window.map_canvas.winfo_rooty(),outer_y,yview[0],total,target_y)
            spatial_scroll.yview_moveto(fraction)
            window.update_idletasks()
            window.update()
        place_map_in_scroll_view()
        # The canvas has a 560 px design request. Fit it within both the
        # visible desktop and the actual top-level window, then reposition it
        # once more because shrinking the canvas changes the outer scrollrange.
        window_bottom=int(window.winfo_rooty())+int(window.winfo_height())
        available_canvas_height=canvas_height_fitting_window(
            window_bottom,int(screen_size[1]),int(window.map_canvas.winfo_rooty()))
        available_canvas_width=(int(screen_size[0])-int(window.map_canvas.winfo_rootx())-12)
        if available_canvas_width>=220:
            window.map_canvas.configure(width=min(900,available_canvas_width))
        if available_canvas_height>=180:
            window.map_canvas.configure(height=available_canvas_height)
            window.update_idletasks()
            window.update()
            place_map_in_scroll_view()
        window.show_google_map(refresh=False,prefer_public=True)
        deadline=time.monotonic()+timeout
        last_observation={}
        while time.monotonic()<deadline:
            window.update()
            provider=str(getattr(window,"_map_provider","") or "")
            map_status=str(window.map_status.get())
            pending=(map_status.startswith("Carregando CBERS-4A/WFI") or
                     "enquanto atualiza CBERS-4A" in map_status or
                     map_status.startswith("Imagem óptica em carregamento"))
            canvas_viewable=bool(window.map_canvas.winfo_viewable())
            visible=canvas_viewable and bool(getattr(window,"_satellite_map_visible",False))
            canvas_items=window.map_canvas.find_all()
            photo=getattr(window,"google_map_photo",None)
            photo_size=(photo.width(),photo.height()) if photo is not None else None
            image_count=sum(window.map_canvas.type(item)=="image" for item in canvas_items)
            from PIL import ImageGrab
            x0,y0=window.map_canvas.winfo_rootx(),window.map_canvas.winfo_rooty()
            screen=ImageGrab.grab()
            capture_bbox=scale_canvas_bbox(
                x0,y0,window.map_canvas.winfo_width(),window.map_canvas.winfo_height(),
                (window.winfo_screenwidth(),window.winfo_screenheight()),screen.size)
            capture_bbox_visible=capture_bbox_is_visible(capture_bbox,screen.size)
            pixels=np.asarray(screen.crop(capture_bbox).convert("RGB"),dtype=np.uint8)
            luminance=pixels.astype("float32").mean(axis=2)
            pixel_quality={"p99_luminance":float(np.percentile(luminance,99)),"std_luminance":float(luminance.std()),"visible_fraction":float((luminance>8).mean())}
            last_observation={
                "provider":provider,"map_status":map_status[:220],
                "window_state":str(window.state()),
                "window_origin":[int(window.winfo_rootx()),int(window.winfo_rooty())],
                "window_size":[int(window.winfo_width()),int(window.winfo_height())],
                "canvas_origin":[int(window.map_canvas.winfo_rootx()),int(window.map_canvas.winfo_rooty())],
                "spatial_yview":list(spatial_scroll.yview()) if spatial_scroll is not None else None,
                "spatial_scrollregion":str(spatial_scroll.cget("scrollregion")) if spatial_scroll is not None else None,
                "window_bottom":int(window.winfo_rooty())+int(window.winfo_height()),
                "window_viewable":bool(window.winfo_viewable()),
                "canvas_viewable":bool(window.map_canvas.winfo_viewable()),
                "canvas_size":[int(window.map_canvas.winfo_width()),int(window.map_canvas.winfo_height())],
                "photo_size":list(photo_size) if photo_size else None,
                "tk_screen_size":[int(window.winfo_screenwidth()),int(window.winfo_screenheight())],
                "captured_screen_size":list(screen.size),"capture_bbox":list(capture_bbox),
                "capture_bbox_fully_visible":capture_bbox_visible,
                "canvas_bg":str(window.map_canvas.cget("bg")),
                "canvas_items":len(canvas_items),"canvas_image_items":image_count,
                "pixel_quality":pixel_quality,
            }
            passed=rendered_optical_status(provider,visible and capture_bbox_visible,photo_size,image_count,pixel_quality,len(canvas_items))
            if passed:
                result.update(status=passed,provider=provider,canvas_items=len(canvas_items),
                              canvas_image_items=image_count,image_width=photo_size[0] if photo_size else None,
                              image_height=photo_size[1] if photo_size else None,
                              canvas_pixel_quality=pixel_quality,
                              optical_attempt_status=map_status[:220],
                              worker_terminal_state_observed=not pending)
                break
            if pending:
                time.sleep(0.12)
                continue
            if provider == "NO_OPTICAL_IMAGE" or "FALHA AO ABRIR IMAGEM ÓPTICA" in map_status:
                result["status"] = "NO_OPTICAL_IMAGE"
                result["last_canvas_observation"] = last_observation
                diagnostic=Path.home()/".enform_verde"/"ultimo_diagnostico_imagem_otica.json"
                if diagnostic.is_file():
                    try:result["provider_diagnostic"]=json.loads(diagnostic.read_text(encoding="utf-8"))
                    except (OSError,ValueError):pass
                break
            time.sleep(0.12)
        else:
            result["status"]="TIMEOUT"
            result["last_canvas_observation"]=last_observation
            diagnostic=Path.home()/".enform_verde"/"ultimo_diagnostico_imagem_otica.json"
            if diagnostic.is_file():
                try:result["provider_diagnostic"]=json.loads(diagnostic.read_text(encoding="utf-8"))
                except (OSError,ValueError):pass
        result["last_ui_status"]=str(window.status.get())[:350]
    except Exception as exc:
        result.update(status="ERROR",error_type=type(exc).__name__,
                      message=str(exc)[:300])
    finally:
        if result.get("status") not in ("PASS_CBERS","PASS_SENTINEL2_FALLBACK","PASS_OPTICAL_IMAGE_FALLBACK") and screen is not None:
            try:screen.crop(capture_bbox).save(ROOT/"optical_gui_sinop_canvas_debug.png")
            except Exception:pass
        try:window.destroy()
        except Exception:pass
    output=ROOT/"optical_gui_sinop_live.json"
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result["status"] in ("PASS_CBERS","PASS_SENTINEL2_FALLBACK","PASS_OPTICAL_IMAGE_FALLBACK") else 1


if __name__=="__main__":
    raise SystemExit(main())
