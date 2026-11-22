"""Approved visual standard of Enform Verde — snapshot and comparison.

Protected (must not change without an explicit, documented decision):
* palette constants, Excel palette, map AOI colours, icon recipe;
* approved header image (enform_header.png, exact SHA-256), header canvas
  colour/height, no text overlay on the header;
* action bar (title style, button labels and order), left navigation
  (width, colours, labels, order, selected/unselected look), notebook tab
  names and order, footer (version label + subtitle), ttk styles and fonts.

Content INSIDE each tab may evolve with new features; the shell may not.
Regenerate the baseline only for a deliberate visual change:
    python ui_visual_standard.py --update      (then document it in the spec)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "validation" / "ui_visual_baseline.json"


def packaged_baseline():
    """Baseline inside the compiled EXE (sys._MEIPASS) or the source tree."""
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    p = base / "validation" / "ui_visual_baseline.json"
    return p if p.is_file() else BASELINE


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def static_snapshot():
    src = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
    palette = dict(re.findall(r'\b(ORANGE|FOREST|GREEN|PALE|TEXT)="(#[0-9A-Fa-f]{6})"', src))
    excel = re.search(r'orange="([0-9A-F]{6})"; green="([0-9A-F]{6})"; white="([0-9A-F]{6})"; '
                      r'pale="([0-9A-F]{6})"; line="([0-9A-F]{6})"', src)
    wf = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
    icon = re.search(r"im=Image\.new\('RGBA',\(256,256\),(\([^)]*\))\).*?d\.text\(\(72,88\),'(\w+)'", wf, re.S)
    return {
        "palette": palette,
        "excel_palette": list(excel.groups()) if excel else None,
        "map_aoi_colours": sorted(set(re.findall(r'outline="(#FF8A00|#E87500)"', src))
                                  | set(re.findall(r'fill="(#F8B44C)"', src))),
        "header_png_sha256": _sha(ROOT / "enform_header.png"),
        "icon": {"background": icon.group(1), "monogram": icon.group(2)} if icon else None,
        "window_title": re.search(r'self\.title\("([^"]+)"\)', src).group(1),
    }


def _cfg(w, *keys):
    out = {}
    for k in keys:
        try:
            v = w.cget(k)
        except Exception:
            continue
        out[k] = str(v)
    return out


def shell_snapshot(app):
    """Introspect the live shell (call after App() is built)."""
    from tkinter import ttk
    app.update_idletasks()
    root = app.winfo_children()[0]
    header, action, body, footer = None, None, None, None
    for w in root.winfo_children():
        cls = w.winfo_class()
        if cls == "Canvas" and header is None:
            header = w
        elif cls == "TFrame" and action is None and any(
                c.winfo_class() == "TButton" for c in w.winfo_children()):
            action = w
        elif cls == "TFrame" and body is None and any(
                c.winfo_class() == "Frame" for c in w.winfo_children()):
            body = w
        elif cls == "TFrame":
            footer = w
    nav = next(c for c in body.winfo_children() if c.winfo_class() == "Frame")
    style = ttk.Style(app)
    def norm(k, v):
        # Tk returns padding as tuple/Tcl_Obj/str depending on platform
        return " ".join(re.findall(r"-?\d+", str(v))) if k == "padding" else str(v)
    # only the keys Enform configures explicitly (theme-independent)
    keys = {".": ("font", "foreground"), "Title.TLabel": ("font", "foreground"),
            "H.TLabel": ("font", "foreground"), "Run.TButton": ("font", "padding"), "TButton": ("padding",)}
    styles = {s: {k: norm(k, style.lookup(s, k)) for k in ks} for s, ks in keys.items()}
    first_nav = app.nav_buttons[0][0]
    selected = next(b for b, i in app.nav_buttons if i == app.nb.index(app.nb.select()))
    unselected = next(b for b, i in app.nav_buttons if i != app.nb.index(app.nb.select()))
    return {
        "header": dict(_cfg(header, "bg", "height", "highlightthickness"),
                       text_overlays=sum(1 for i in header.find_all() if header.type(i) == "text"),
                       image_items=sum(1 for i in header.find_all() if header.type(i) == "image")),
        "action_bar": [(c.winfo_class(), _cfg(c, "text", "style")) for c in action.winfo_children()],
        "nav": dict(_cfg(nav, "width", "bg", "highlightbackground", "highlightthickness"),
                    labels=[b.cget("text") for b, _ in app.nav_buttons],
                    targets=[i for _, i in app.nav_buttons],
                    button=_cfg(first_nav, "relief", "anchor", "padx", "pady", "activebackground"),
                    selected=_cfg(selected, "bg", "fg", "font"),
                    unselected=_cfg(unselected, "bg", "fg", "font")),
        "tabs": [app.nb.tab(t, "text") for t in app.nb.tabs()],
        "footer": [_cfg(c, "text") for c in footer.winfo_children() if not str(c.cget("textvariable"))],
        "styles": styles,
    }


def full_snapshot(app):
    return {"static": static_snapshot(), "shell": shell_snapshot(app)}


def _normalise(snap):
    """Remove the version string so a version bump is not a visual change."""
    s = json.loads(json.dumps(snap, ensure_ascii=False))
    for item in s["shell"]["footer"]:
        if item.get("text", "").startswith("v"):
            item["text"] = "v<APP_VERSION>"
    return s


def diff(baseline, current, path=""):
    out = []
    if isinstance(baseline, dict) and isinstance(current, dict):
        for k in sorted(set(baseline) | set(current)):
            out += diff(baseline.get(k), current.get(k), f"{path}/{k}")
    elif isinstance(baseline, list) and isinstance(current, list) and len(baseline) == len(current):
        for i, (a, b) in enumerate(zip(baseline, current)):
            out += diff(a, b, f"{path}[{i}]")
    elif baseline != current:
        out.append(f"{path}: aprovado={baseline!r} atual={current!r}")
    return out


def capture():
    from desktop_app import App
    app = App()
    try:
        return _normalise(full_snapshot(app))
    finally:
        app.destroy()


if __name__ == "__main__":
    snap = capture()
    if "--update" in sys.argv:
        BASELINE.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("baseline atualizado:", BASELINE)
    else:
        d = diff(json.loads(BASELINE.read_text(encoding="utf-8")), snap)
        print("\n".join(d) or "PADRAO_VISUAL_OK")
        sys.exit(1 if d else 0)
