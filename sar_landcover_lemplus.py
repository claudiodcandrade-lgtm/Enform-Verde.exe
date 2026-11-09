"""Always-available SAR classifier (owner decision 8A) — v2 adds Amazonian forest labels (INPE Rondônia 2022, MT): Sentinel-1 RTC monthly
signatures → land cover (native vegetation / crops / pasture / forestry) and
crop type (soybean, maize, cotton, coffee), trained on LEM+ field labels
(INPE et al., CC BY 4.0, west Bahia, 2019/20) — never MapBiomas.

Validation (spatial 0,1° blocks, GroupKFold 5, out-of-sample): land cover
OA 0,952 (IC95% 0,940–0,961), native vegetation precision 0,89 (0,83–0,93);
crop OA 0,958 (0,947–0,967). Per owner decision 2B any measured accuracy is
accepted as EXPERIMENTAL; outside the training domain the transfer error is
NOT quantified and is declared in every output.

Runtime: the last COMPLETE agricultural year (Oct→Sep) before ``as_of``; for
each month the mean linear γ⁰ (VV, VH) over all scenes of the most frequent
relative orbit, on an 80 m grid; per-pixel probabilities; areas in EPSG:6933.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "data" / "models" / "sar_brasil_rf_v2.joblib"
MANIFEST = ROOT / "data" / "models" / "sar_brasil_rf_v2.manifest.json"
PIXEL_M = 80.0
NATIVE_LABEL = "Vegetação nativa (Cerrado)"
FOREST_LABEL = "Floresta nativa"
DOMAIN_ENVELOPE = (-66.7, -17.5, -45.4, -7.7)
CROP_MAJORITY = 0.5
UNIDENTIFIED_CROP = "Área cultivada — cultura não identificada"
CROP_NAMES = {UNIDENTIFIED_CROP: UNIDENTIFIED_CROP, "Soja": "Lavoura de Soja", "Milho": "Lavoura de Milho", "Algodão": "Lavoura de Algodão",
              "Café": "Lavoura de Café"}


def _resource(p):
    import sys
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    q = base / "data" / "models" / Path(p).name
    return q if q.is_file() else Path(p)


def agricultural_year(as_of):
    """Last complete Oct→Sep window strictly before ``as_of``."""
    end_year = as_of.year if as_of.month >= 10 else as_of.year - 1
    months = [(end_year - 1, m) for m in range(10, 13)] + [(end_year, m) for m in range(1, 10)]
    return months, f"{end_year - 1}/{end_year}"


def load():
    import hashlib
    import joblib
    man = json.loads(_resource(MANIFEST).read_text(encoding="utf-8"))
    path = _resource(MODEL)
    if hashlib.sha256(path.read_bytes()).hexdigest() != man["sha256"]:
        raise RuntimeError("SHA-256 do modelo SAR não confere com o manifesto")
    return joblib.load(path), man


def _monthly_features(aoi_4326, months, search_fn=None, token_fn=None):
    import rasterio
    import requests
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from rasterio.transform import from_origin
    from sentinel1_mpc import _signed_href, get_runtime_sas_token
    import tls_setup
    tls_setup.configure()
    geom = aoi_4326.geometry.union_all()
    eq = aoi_4326.to_crs(6933)
    minx, miny, maxx, maxy = eq.total_bounds
    W = int(np.ceil((maxx - minx) / PIXEL_M)); H = int(np.ceil((maxy - miny) / PIXEL_M))
    if W * H > 4_000_000:
        raise ValueError("AOI grande demais para a classificação SAR em 80 m")
    dst_tr = from_origin(minx, maxy, PIXEL_M, PIXEL_M)
    start = f"{months[0][0]}-{months[0][1]:02d}-01"
    ey, em = months[-1]
    end = f"{ey}-{em:02d}-30"
    if search_fn is None:
        r = requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search",
                          json={"collections": ["sentinel-1-rtc"], "bbox": list(geom.bounds),
                                "datetime": f"{start}/{end}", "limit": 250}, timeout=90).json()
        feats = r.get("features", [])
    else:
        feats = search_fn(geom.bounds, start, end)
    feats = [f for f in feats if {"vv", "vh"} <= set(f.get("assets", {}))]
    if not feats:
        return None, {"reason": "nenhuma cena Sentinel-1 RTC VV/VH no ano agrícola"}
    orbit = Counter(f["properties"].get("sat:relative_orbit") for f in feats).most_common(1)[0][0]
    feats = [f for f in feats if f["properties"].get("sat:relative_orbit") == orbit]
    token = (token_fn or get_runtime_sas_token)()
    S = defaultdict(lambda: np.zeros((H, W))); C = defaultdict(lambda: np.zeros((H, W)))
    used = []
    for f in feats:
        ym = tuple(int(x) for x in f["properties"]["datetime"][:7].split("-"))
        if ym not in months:
            continue
        try:
            for pol in ("vv", "vh"):
                with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4",
                                  **tls_setup.gdal_env()):
                    with rasterio.open(_signed_href(f["assets"][pol]["href"], token)) as src:
                        out = np.full((H, W), np.nan)
                        reproject(rasterio.band(src, 1), out, dst_transform=dst_tr, dst_crs="EPSG:6933",
                                  resampling=Resampling.average, dst_nodata=np.nan)
                ok = np.isfinite(out) & (out > 0)
                S[(ym, pol)][ok] += out[ok]; C[(ym, pol)][ok] += 1
            used.append(f["id"])
        except Exception:
            continue
    bands = []
    for ym in months:
        vv = S[(ym, "vv")] / np.where(C[(ym, "vv")] > 0, C[(ym, "vv")], np.nan)
        vh = S[(ym, "vh")] / np.where(C[(ym, "vh")] > 0, C[(ym, "vh")], np.nan)
        vvd, vhd = 10 * np.log10(vv), 10 * np.log10(vh)
        bands += [vvd, vhd, vhd - vvd]
    return (np.stack(bands, -1), dst_tr, (H, W)), {"orbit": orbit, "scenes_used": len(used),
                                                    "first_scene": used[0] if used else None,
                                                    "last_scene": used[-1] if used else None}


def in_validated_domain(ibge=None, ibge_field="legenda_1", aoi=None):
    """Validated domain (v2): savanna/Cerrado phytoregions, and Amazonian forest
    phytoregions inside the MT/RO/west-BA training envelope (labels: LEM+ BA,
    INPE MT field samples, INPE Rondônia 2022)."""
    if ibge is None or len(ibge) == 0 or ibge_field not in ibge:
        return False, "fitorregião IBGE indisponível para verificar o domínio"
    eq = ibge.to_crs(6933)
    names = eq[ibge_field].astype(str).str.casefold()
    share = eq.geometry.area.groupby(names).sum()
    dominant = share.idxmax() if len(share) else ""
    if any(k in dominant for k in ("savana", "cerrado")):
        return True, "dentro do domínio de treino (savana/Cerrado)"
    if "floresta" in dominant:
        ref = (aoi if aoi is not None else ibge).to_crs(4326).geometry.union_all().centroid
        w, s_, e, n = DOMAIN_ENVELOPE
        if w <= ref.x <= e and s_ <= ref.y <= n:
            return True, "dentro do domínio de treino (floresta amazônica, envelope MT/RO)"
    return False, "fora do domínio de treino (fitorregião dominante: " + dominant + ")"


def classify_aoi(aoi, *, as_of=None, search_fn=None, token_fn=None):
    """Return {status, classes:[{class_name, area_ha, native_status, source, mean_probability}], ...}."""
    import geopandas as gpd
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping
    as_of = as_of or date.today()
    months, season = agricultural_year(as_of)
    models, man = load()
    aoi4326 = aoi.to_crs(4326)
    data, info = _monthly_features(aoi4326, months, search_fn, token_fn)
    if data is None:
        return {"status": "N/D_SEM_PIXELS_SAR", "reason": info["reason"], "season": season}
    X, tr, (H, W) = data
    inside = geometry_mask([mapping(g) for g in aoi.to_crs(6933).geometry], out_shape=(H, W),
                           transform=tr, invert=True)
    ok = inside & np.isfinite(X).all(-1)
    if ok.sum() == 0:
        return {"status": "N/D_SEM_PIXELS_SAR", "reason": "pixels SAR insuficientes no ano agrícola", "season": season}
    Xv = X[ok]
    lc = models["landcover"]; pl = lc.predict_proba(Xv); lab = lc.classes_[pl.argmax(1)]
    pix_ha = PIXEL_M * PIXEL_M / 1e4
    classes = []
    # pixel label raster (crop names inside cultivated pixels) → polygons
    names = np.full((H, W), "", dtype=object)
    names[ok] = lab
    crop_mask = lab == "Cultivo agrícola"
    pc = None
    if crop_mask.any():
        cm = models["crop"]; pc = cm.predict_proba(Xv[crop_mask]); clab = cm.classes_[pc.argmax(1)].astype(object)
        # Owner priority (09/11/2026): when the crop is not identified, show
        # "Área cultivada". A pixel is left unnamed when no listed crop wins a
        # majority of the forest votes (max probability < 0.5); this is a
        # decision rule, not an accuracy.
        clab[pc.max(1) < CROP_MAJORITY] = UNIDENTIFIED_CROP
        tmp = names[ok]; tmp[crop_mask] = np.array([CROP_NAMES.get(c, "Lavoura de " + c) for c in clab], dtype=object)
        names[ok] = tmp
    val = man["validation"]
    for name in lc.classes_:
        sel = lab == name
        if not sel.any():
            continue
        if name == "Cultivo agrícola" and pc is not None:
            for crop in np.unique(clab):
                s2 = clab == crop
                classes.append({"class_name": CROP_NAMES.get(crop, "Lavoura de " + crop),
                                "area_ha": float(s2.sum() * pix_ha), "native_status": False,
                                "source": "SAR_VALIDADO", "validation_status": "experimental_medido",
                                "mean_probability": float(pc[s2].max(1).mean()),
                                "class_precision_wilson95": val["crop"]["per_class"].get(crop, {}).get("precision_wilson95"),
                                "season": season})
            continue
        classes.append({"class_name": ("Vegetação nativa (assinatura SAR)" if name == NATIVE_LABEL else
                                       "Floresta nativa (assinatura SAR)" if name == FOREST_LABEL else
                                       "Área antrópica recente (corte raso/solo exposto)" if name == "Corte raso recente" else name),
                        "area_ha": float(sel.sum() * pix_ha),
                        "native_status": (True if name in (NATIVE_LABEL, FOREST_LABEL) else
                                          None if name == "Área úmida" else False),
                        "source": "SAR_VALIDADO", "validation_status": "experimental_medido",
                        "mean_probability": float(pl[sel].max(1).mean()),
                        "class_precision_wilson95": val["landcover"]["per_class"].get(name, {}).get("precision_wilson95"),
                        "season": season})
    from rasterio.features import shapes
    from shapely.geometry import shape as _shape
    codes = {n: i + 1 for i, n in enumerate(sorted({x for x in names[ok]}))}
    code_arr = np.zeros((H, W), dtype="int32")
    for n_, i_ in codes.items():
        code_arr[names == n_] = i_
    inv = {v: k for k, v in codes.items()}
    polys = [{"class_name": ("Vegetação nativa (assinatura SAR)" if inv[int(v)] == NATIVE_LABEL else
                            "Floresta nativa (assinatura SAR)" if inv[int(v)] == FOREST_LABEL else
                            "Área antrópica recente (corte raso/solo exposto)" if inv[int(v)] == "Corte raso recente" else inv[int(v)]),
              "geometry": _shape(gm)} for gm, v in shapes(code_arr, mask=code_arr > 0, transform=tr)]
    poly_gdf = (gpd.GeoDataFrame(polys, crs=6933).dissolve("class_name").reset_index()
                .clip(aoi.to_crs(6933)) if polys else None)
    cent = aoi4326.geometry.union_all().centroid
    w, s, e, n = DOMAIN_ENVELOPE
    in_domain = w <= cent.x <= e and s <= cent.y <= n
    return {"status": "SAR_CLASSIFICADOR_EXPERIMENTAL", "model_id": man["model_id"], "model_sha256": man["sha256"],
            "season": season, "classes": classes, "pixels": int(ok.sum()), "pixel_m": PIXEL_M,
            "landcover_overall_accuracy": val["landcover"]["overall_accuracy"],
            "landcover_overall_accuracy_wilson95": val["landcover"]["overall_accuracy_wilson95"],
            "crop_overall_accuracy": val["crop"]["overall_accuracy"], "in_training_domain": in_domain,
            "domain_warning": (None if in_domain else man["domain"]["transfer_note"]), **info,
            "labels_source": "; ".join(t["dataset"] for t in man["training_labels"]), "polygons_6933": poly_gdf}
