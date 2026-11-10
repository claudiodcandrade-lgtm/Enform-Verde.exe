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
    """Read bounded real Sentinel-1 RTC VV/VH windows with monthly means.

    Monthly feature vectors are only eligible if ALL 12 months contain paired
    valid VV/VH pixels. A failed polarization never counts as an observed pair.
    The function does not read a full satellite image through rasterio.band.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject, transform_geom
    from rasterio.windows import from_bounds, Window
    from rasterio.transform import from_origin
    from shapely.geometry import mapping, shape
    from datetime import datetime, timezone
    from sentinel1_mpc import (_signed_href, get_runtime_sas_token,
                               search_sentinel1_rtc, sign_asset_href)
    import tls_setup
    tls_setup.configure()
    geom = aoi_4326.geometry.union_all()
    eq = aoi_4326.to_crs(6933)
    minx, miny, maxx, maxy = eq.total_bounds
    W = max(1,int(np.ceil((maxx - minx) / PIXEL_M)))
    H = max(1,int(np.ceil((maxy - miny) / PIXEL_M)))
    if W * H > 4_000_000:
        raise ValueError("AOI grande demais para a classificação SAR em 80 m")
    dst_tr = from_origin(minx, maxy, PIXEL_M, PIXEL_M)
    start = f"{months[0][0]}-{months[0][1]:02d}-01"
    ey, em = months[-1]
    import calendar
    end = f"{ey}-{em:02d}-{calendar.monthrange(ey,em)[1]:02d}"
    if search_fn is None:
        found = search_sentinel1_rtc(mapping(geom),
            start_utc=datetime.fromisoformat(start+"T00:00:00+00:00"),
            end_utc=datetime.fromisoformat(end+"T23:59:59+00:00"),
            max_pages=30, page_limit=100)
        feats = found["scenes"]
        pagination_complete = found["pagination_complete"]
    else:
        feats = search_fn(geom.bounds, start, end)
        pagination_complete = True
    if not pagination_complete:
        return None, {"reason":"PAGINACAO_STAC_INCOMPLETA",
                      "scenes_discovered":len(feats)}
    feats = [f for f in feats if {"vv", "vh"} <= set(f.get("assets") or {})]
    if not feats:
        return None, {"reason":"NENHUMA_CENA_RTC_VV_VH",
                      "scenes_discovered":0}
    def ym_of(f):
        p=f.get("properties") or {}
        value=p.get("datetime") or f.get("acquisition_utc") or p.get("start_datetime") or ""
        try:return tuple(int(x) for x in str(value)[:7].split("-"))
        except Exception:return None
    def orb_of(f):
        p=f.get("properties") or {}
        return (p.get("sat:relative_orbit") or f.get("relative_orbit"),
                p.get("sat:orbit_state") or f.get("orbit_state"))
    month_set=set(months)
    feats=[f for f in feats if ym_of(f) in month_set]
    orbits=defaultdict(set)
    for feat in feats:orbits[orb_of(feat)].add(ym_of(feat))
    if not orbits:
        return None, {"reason":"CENAS_FORA_DA_JANELA_AGRICOLA"}
    orbit=max(orbits,key=lambda k:(len(orbits[k]),sum(orb_of(f)==k for f in feats)))
    grouped=defaultdict(list)
    for feat in feats:
        if orb_of(feat)==orbit:grouped[ym_of(feat)].append(feat)
    # Newest first, with fallback on read errors from individual assets.
    for group in grouped.values():
        group.sort(key=lambda f:str((f.get("properties") or {}).get("datetime")
                                    or f.get("acquisition_utc") or ""),reverse=True)
    try:
        token=(token_fn or get_runtime_sas_token)()
    except Exception:
        # Independent per-asset signing can still recover actual RTC pixels.
        token=""
    S={};C={};used=[];failed=[];observed_months=[];monthly_pair_counts={}
    for ym in months:
        pairs=[]
        for feat in grouped.get(ym,[])[:5]:
            # Atomic scene: commit both polarizations or neither.
            pair={}
            for attempt in range(3):
                try:
                    for pol in ("vv","vh"):
                        gdal_opts={"GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR",
                                   "GDAL_HTTP_TIMEOUT":"45","GDAL_HTTP_MAX_RETRY":"3",
                                   "GDAL_HTTP_RETRY_DELAY":"1",**tls_setup.gdal_env()}
                        if attempt==2:
                            gdal_opts.update({"CPL_VSIL_CURL_USE_HEAD":"NO",
                                              "GDAL_HTTP_MULTIRANGE":"NO",
                                              "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES":"NO",
                                              "GDAL_HTTP_VERSION":"1.1"})
                        with rasterio.Env(**gdal_opts):
                            with rasterio.open((sign_asset_href(feat["assets"][pol]["href"])
                                                if (attempt > 0 or not token)
                                                else _signed_href(feat["assets"][pol]["href"],token))) as src:
                                if src.crs is None:raise ValueError("SAR_COG_MISSING_CRS")
                                local=shape(transform_geom("EPSG:4326",src.crs,mapping(geom)))
                                window=from_bounds(*local.bounds,transform=src.transform)
                                from math import floor,ceil
                                x0,y0=floor(window.col_off),floor(window.row_off)
                                x1,y1=ceil(window.col_off+window.width),ceil(window.row_off+window.height)
                                window=Window(x0,y0,max(1,x1-x0),max(1,y1-y0)).intersection(
                                    Window(0,0,src.width,src.height))
                                if window.width<1 or window.height<1:
                                    raise ValueError("SAR_COG_OUTSIDE_AOI")
                                if window.width*window.height>4_000_000:
                                    raise ValueError("SAR_WINDOW_EXCEEDS_PIXEL_BUDGET")
                                raw=np.ma.filled(src.read(1,window=window,masked=True)
                                                 .astype(np.float32),np.nan)
                                out=np.full((H,W),np.nan,dtype=np.float32)
                                reproject(source=raw,destination=out,
                                    src_transform=src.window_transform(window),
                                    src_crs=src.crs,src_nodata=np.nan,
                                    dst_transform=dst_tr,dst_crs="EPSG:6933",
                                    dst_nodata=np.nan,resampling=Resampling.average)
                                out[~np.isfinite(out)|(out<=0)]=np.nan
                                if not np.isfinite(out).any():
                                    raise ValueError("SAR_NO_POSITIVE_AOI_PIXELS")
                                pair[pol]=out
                    break
                except (OSError,RuntimeError,ValueError,UnicodeError) as exc:
                    failed.append({"scene":str(feat.get("id",""))[:65],
                                   "type":type(exc).__name__,"attempt":attempt+1,
                                   "read_strategy":("HTTP_1_1_NO_MULTIRANGE" if attempt==2 else "DEFAULT_GDAL")})
                    pair={}
                    if attempt==0 and token_fn is None:
                        try:token=get_runtime_sas_token()
                        except Exception:pass
            if len(pair)!=2:continue
            good=np.isfinite(pair["vv"]) & np.isfinite(pair["vh"])
            if not good.any():continue
            pairs.append({pol:np.where(good,pair[pol],np.nan) for pol in ("vv","vh")})
            used.append(str(feat.get("id","")))
            if len(pairs)>=3:break
        if not pairs:continue
        monthly_pair_counts[f"{ym[0]}-{ym[1]:02d}"]=len(pairs)
        for pol in ("vv","vh"):
            # Average up to 3 independent paired acquisitions in linear units,
            # matching the RF's monthly-mean training feature semantics.
            valid_stack=np.stack([p[pol] for p in pairs])
            numerator=np.nansum(valid_stack,axis=0)
            count=np.isfinite(valid_stack).sum(axis=0)
            S[(ym,pol)]=np.divide(numerator,count,out=np.full((H,W),np.nan),
                                  where=count>0)
            C[(ym,pol)]=count>0
        observed_months.append(f"{ym[0]}-{ym[1]:02d}")
    missing=[f"{ym[0]}-{ym[1]:02d}" for ym in months if ym not in
             {tuple(map(int,x.split("-"))) for x in observed_months}]
    if missing:
        return None, {"reason":"MESES_RTC_SEM_PARES_VV_VH",
            "observed_months":observed_months,"missing_months":missing,
            "scenes_used":len(used),"monthly_pair_counts":monthly_pair_counts,
            "pixel_read_errors":failed[:12]}
    bands=[]
    for ym in months:
        vv,vh=S[(ym,"vv")],S[(ym,"vh")]
        with np.errstate(divide="ignore",invalid="ignore"):
            vvd,vhd=10*np.log10(vv),10*np.log10(vh)
        bands += [vvd,vhd,vhd-vvd]
    return (np.stack(bands,-1),dst_tr,(H,W)),{
        "orbit":orbit,"scenes_used":len(used),
        "observed_months":observed_months,
        "monthly_pair_counts":monthly_pair_counts,
        "pixel_read_errors":failed[:12],
        "first_scene":used[0],"last_scene":used[-1]}

def in_validated_domain(ibge=None, ibge_field="legenda_1", aoi=None):
    """Validated domain (v2): savanna/Cerrado phytoregions, and Amazonian forest
    phytoregions inside the MT/RO/west-BA training envelope (labels: LEM+ BA,
    INPE MT field samples, INPE Rondônia 2022)."""
    if ibge is None or len(ibge) == 0 or ibge_field not in ibge:
        # IBGE is descriptive context, not the source of today's land cover.
        # A missing external IBGE service must not prevent experimental SAR
        # inference inside the documented training region. Mark transfer as
        # provisional; field accuracy is NOT established by this check.
        if aoi is not None:
            centroid=aoi.to_crs(4326).geometry.union_all().centroid
            w,s,e,n=DOMAIN_ENVELOPE
            if w <= centroid.x <= e and s <= centroid.y <= n:
                return True, ("DOMINIO_GEOGRAFICO_PROVISORIO; fita IBGE indisponível; "
                              "classificação SAR EXPERIMENTAL sem validação local de fitofisionomia")
        if aoi is not None:
            return True, ("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL; fora do dominio "
                          "regional conhecido; inferencia para afericao em campo, "
                          "acuracia e incerteza de transferencia N/D")
        return False, "AOI nao fornecida; nao e possivel determinar extrapolacao"
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
    return True, ("EXTRAPOLACAO_NACIONAL_EXPERIMENTAL; fora do domínio "
                  "de treino (fitorregião dominante: " + dominant +
                  "); inferencia SAR para afericao em campo, sem acuracia local")


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
        return {"status": "N/D_SEM_PIXELS_SAR", "reason": info["reason"],
                "season": season, "acquisition_diagnostic": info}
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
                                "source": "SAR_EXPERIMENTAL_MODELO", "validation_status": "experimental_medido",
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
                        "source": "SAR_EXPERIMENTAL_MODELO", "validation_status": "experimental_medido",
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
