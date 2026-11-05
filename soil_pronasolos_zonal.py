"""Raw PronaSolos SOC maps: actual polygon/pixel intersections, not bbox points.

This is a LOCAL, full 90m raster route. It does not download rendered map images,
invent pixels, or interpret colour-stretched MapServer TIFFs as carbon stock.
Five raw, aligned Embrapa stock layers with verified file hashes are required.
"""
from __future__ import annotations

import hashlib
import json
import math
from urllib.parse import urlparse
from pathlib import Path

DEPTHS = ((2, "0-5"), (3, "5-15"), (4, "15-30"),
          (5, "30-60"), (6, "60-100"))


def verified_local_horizons(root=None):
    """Find an explicitly documented five-layer LOCAL raster cache.

    Manifest is mandatory: without per-raster hashes, a local TIFF could be
    a renderer or an unrelated product. The operator must verify the license
    terms; a manifest assertion is not independent license verification.
    """
    root = Path(root or Path.home()/".enform_verde"/"pronasolos_90m").resolve()
    manifest = root/"manifest.json"
    if not manifest.is_file():
        return None
    try:
        meta = json.loads(manifest.read_text(encoding="utf-8"))
        if (meta.get("publisher") != "Embrapa Solos/PronaSolos"
                or meta.get("unit") != "Mg C/ha"
                or meta.get("raw_raster") is not True
                or meta.get("license_reviewed") is not True
                or not str(meta.get("source_url", "")).startswith("https://")):
            return None
        # A declared HTTPS URL and a SHA-256 hash do not authenticate a publisher.
        # Reject example/test hosts and unrelated domains in the operational path.
        # Even an accepted host is only a necessary provenance check, not proof
        # of license, scientific accuracy or authenticity of the raster contents.
        source = urlparse(str(meta["source_url"]))
        host = (source.hostname or "").lower().rstrip(".")
        allowed = ("embrapa.br", "sgb.gov.br")
        if (source.scheme != "https" or source.username or source.password
                or source.port not in (None, 443)
                or not any(host == d or host.endswith("." + d) for d in allowed)):
            return None
        layers = meta["layers"]
        if set(layers) != {str(i) for i,_ in DEPTHS}:
            return None
        paths = {}
        for i,_ in DEPTHS:
            item = layers[str(i)]
            name, digest = item["file"], item["sha256"]
            if (not isinstance(name, str) or not isinstance(digest, str)
                    or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest)):
                return None
            path = (root/name).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                return None
            hasher=hashlib.sha256()
            with path.open("rb") as stream:
                while True:
                    block=stream.read(1024*1024)
                    if not block:break
                    hasher.update(block)
            if hasher.hexdigest() != digest.lower():
                return None
            paths[i] = path
        return paths
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return None


def mapped_soil_0_100_on_polygon(gdf, horizon_paths, *, max_cells=12_000_000,
                                 full_coverage=0.995, block_rows=256, source_label=None,
                                  official_bound_paths=None, official_provenance=None):
    """Area-weighted raw raster 0-100 cm on the EXACT polygon intersection.

    ``gdf`` is the native fitophysiognomy intersection passed by the carbon
    engine (never the AOI bbox). Every touched raster cell is weighted by the
    true area of (cell ∩ polygon) in EPSG:6933 (equal area). Only cells with
    all five horizons valid contribute; no 0-30 extrapolation.

    Pixels without value (water, urban, rock, map gaps) are NOT filled: the
    density refers to the mapped part and ``area_covered_ha`` is returned so the
    stock is multiplied by the covered area only. Coverage below
    ``full_coverage`` is labelled PARCIAL; zero coverage is N/D.

    Geographic rasters (EPSG:4326, as published by Embrapa) are supported:
    a lat/lon cell maps to an exact rectangle in EPSG:6933.
    """
    import numpy as np
    import rasterio
    import shapely
    from rasterio.features import geometry_mask
    from rasterio.windows import Window, from_bounds, transform as window_transform
    from shapely.geometry import mapping
    from pyproj import Transformer

    def nd(reason, **extra):
        return {"_diagnostic": {"target_depth_cm": 100,
                "target_status": "INCOMPLETO_NAO_EXTRAPOLAR",
                "target_0_100_available": False,
                "method": "area_weighted_raw_raster_polygon_intersection",
                "reason": reason, **extra}}
    if set(horizon_paths) != {i for i,_ in DEPTHS}:
        return nd("cinco rasters brutos de 0–100 cm obrigatórios")
    from contextlib import ExitStack
    with rasterio.Env(), ExitStack() as stack:
        srcs = [stack.enter_context(rasterio.open(horizon_paths[i])) for i,_ in DEPTHS]
        first = srcs[0]
        # Validate raw floating-point SOC values: reject byte-coded render images.
        if any(src.count != 1 or src.dtypes[0] not in ("float32", "float64") for src in srcs):
            return nd("as cinco camadas devem ser rasters contínuos brutos float32/float64")
        if not first.crs or first.count != 1:
            return nd("raster base sem CRS ou com mais de uma banda")
        if abs(first.transform.b)>1e-10 or abs(first.transform.d)>1e-10:
            return nd("rasters rotacionados requerem processamento específico")
        for src in srcs[1:]:
            if (src.count != 1 or src.crs != first.crs
                    or src.transform != first.transform
                    or src.width != first.width or src.height != first.height):
                return nd("rasters não alinhados (CRS, pixel ou extensão distintos)")
        geom = gdf.to_crs(first.crs).geometry.union_all()
        if geom.is_empty:
            return nd("interseção poligonal nativa vazia")
        if not geom.is_valid:
            from shapely.validation import make_valid
            geom = make_valid(geom)
        bounds = geom.bounds
        left, bottom, right, top = first.bounds
        if bounds[2] <= left or bounds[0] >= right or bounds[3] <= bottom or bounds[1] >= top:
            return nd("polígono fora da cobertura do mapa oficial")
        window = from_bounds(max(bounds[0],left), max(bounds[1],bottom),
                             min(bounds[2],right), min(bounds[3],top),
                             transform=first.transform)
        # Enclosing integer pixels (floor/ceil): rounding can drop edge cells.
        col0 = math.floor(window.col_off); row0 = math.floor(window.row_off)
        col1 = math.ceil(window.col_off + window.width)
        row1 = math.ceil(window.row_off + window.height)
        window = Window(col0,row0,col1-col0,row1-row0).intersection(
            Window(0,0,first.width,first.height))
        width, height = int(window.width), int(window.height)
        if width<1 or height<1 or width*height>max_cells:
            return nd("recorte excede capacidade para cálculo de interseções exatas",
                      raster_window_cells=width*height, maximum_cells=max_cells)
        transform = window_transform(window, first.transform)
        touched = geometry_mask([mapping(geom)], out_shape=(height,width),
                                transform=transform, invert=True, all_touched=True)
        arrays = [src.read(1,window=window,masked=True) for src in srcs]
        valid = touched.copy()
        for data in arrays:
            valid &= ~np.ma.getmaskarray(data) & np.isfinite(data.data) & (data.data >= 0)
        layers = np.stack([np.asarray(a.data, dtype="float64") for a in arrays])
        to_eq = Transformer.from_crs(first.crs, "EPSG:6933", always_xy=True)
        def eq(geoms):
            return shapely.transform(geoms, lambda xy: np.column_stack(
                to_eq.transform(xy[:,0], xy[:,1])))
        requested_area = float(shapely.area(eq(shapely.segmentize(
            geom, (abs(transform.a) / 4.0)))))
        if requested_area<=0:
            return nd("área da interseção não positiva")
        shapely.prepare(geom)
        w_all=[]; idx_all=[]
        for r0 in range(0, height, block_rows):
            r1 = min(height, r0+block_rows)
            rows, cols = np.nonzero(valid[r0:r1]); rows = rows + r0
            if not len(rows):
                continue
            x0 = transform.c + cols*transform.a; x1 = x0 + transform.a
            y0 = transform.f + rows*transform.e; y1 = y0 + transform.e
            boxes = shapely.box(np.minimum(x0,x1), np.minimum(y0,y1),
                                np.maximum(x0,x1), np.maximum(y0,y1))
            inside = shapely.contains_properly(geom, boxes)
            weight = np.zeros(len(boxes))
            if inside.any():
                weight[inside] = shapely.area(eq(boxes[inside]))
            edge = ~inside
            if edge.any():
                parts = shapely.intersection(boxes[edge], geom)
                weight[edge] = shapely.area(eq(parts))
            keep = weight > 0
            w_all.append(weight[keep]); idx_all.append((rows[keep], cols[keep]))
        if not w_all:
            return nd("nenhum pixel com os cinco horizontes válidos na interseção",
                      intersected_area_ha=requested_area/10000, coverage_fraction=0.0)
        weights = np.concatenate(w_all)
        rr = np.concatenate([a for a,_ in idx_all]); cc = np.concatenate([b for _,b in idx_all])
        per_layer = layers[:, rr, cc]                       # (5, n)
        covered = float(weights.sum())
        coverage = min(1.0, covered/requested_area)
        names = [name for _,name in DEPTHS]

        def wstats(values):
            m = float(np.average(values, weights=weights))
            sd = float(np.sqrt(np.average((values-m)**2, weights=weights))) if len(values)>1 else None
            return m, sd
        label = source_label or "Embrapa Solos/PronaSolos (5 mapas brutos, 90 m)"
        partial = coverage < full_coverage
        out = {}
        for depth_label, count in (("0–30 cm",3),("0–60 cm",4),("0–100 cm",5)):
            m, sd = wstats(per_layer[:count].sum(axis=0))
            out[depth_label] = {
                "tc_ha": m, "spatial_sd_tc_ha": sd, "n_samples": int(len(weights)),
                "area_covered_ha": covered/10000, "coverage_fraction": coverage,
                "layers": names[:count],
                "layer_means_tc_ha": {names[i]: float(np.average(per_layer[i], weights=weights))
                                      for i in range(count)},
                "source": label,
                "uncertainty_kind": ("DP espacial ponderado por área dos pixels; descritivo, "
                                     "NÃO é IC95% nem erro de predição do mapa"),
                "profile_pairing": ("interseção geométrica exata polígono × pixel 90 m; "
                                    "cinco horizontes do mesmo pixel; média ponderada por área"),
                "predictive_uncertainty_quantified": False,
                "partial_coverage": partial,
            }
            if count < 5:
                out[depth_label]["diagnostic_only"] = True
        out["_diagnostic"] = {
            "coverage_fraction": coverage, "covered_area_ha": covered/10000,
            "intersected_area_ha": requested_area/10000,
            "unmapped_area_ha": max(0.0, requested_area-covered)/10000,
            "valid_complete_pixels": int(len(weights)),
            "source": "raw_aligned_pronasolos_geotiff",
            "method": "area_weighted_raw_raster_polygon_intersection",
            "raster_crs": str(first.crs), "pixel_size": [abs(first.transform.a), abs(first.transform.e)],
            "target_depth_cm": 100, "target_0_100_available": not partial,
            "target_status": ("PARCIAL_SEM_EXTRAPOLACAO" if partial
                              else "COMPLETO_POR_INTERSECAO_RASTER"),
            "full_raster_0_100": not partial,
            "uncertainty": "Spatial SD is descriptive only; no AOI CI95 or transfer error",
        }
        # Published per-horizon marginal bounds do not provide a calibrated
        # joint 95% confidence interval for the 0–100 cm property stock.
        official = {"status": "N/D", "reason": "limites oficiais não recuperados",
                    "predictive_uncertainty_quantified": False}
        if official_bound_paths is not None:
            try:
                if any(set(official_bound_paths.get(side, {})) != {2, 3, 4, 5, 6}
                       for side in ("lower", "upper")):
                    raise ValueError("dez limites oficiais por horizonte obrigatórios")
                raw_bounds = {}
                for side in ("lower", "upper"):
                    raw_bounds[side] = []
                    for layer_id in range(2, 7):
                        ds = stack.enter_context(rasterio.open(official_bound_paths[side][layer_id]))
                        if (ds.count != 1 or ds.dtypes[0] not in ("float32", "float64")
                                or ds.crs != first.crs or ds.transform != first.transform
                                or ds.width != first.width or ds.height != first.height):
                            raise ValueError("raster de limite oficial incompatível com grade de estoque")
                        arr = ds.read(1, window=window, masked=True)[rr, cc]
                        if np.ma.getmaskarray(arr).any():
                            raise ValueError("pixels oficiais de limites faltantes sobre o estoque")
                        vals = np.asarray(np.ma.filled(arr, np.nan), dtype="float64")
                        if not np.isfinite(vals).all() or (vals < 0).any():
                            raise ValueError("limites oficiais inválidos")
                        raw_bounds[side].append(vals)
                lower, upper = np.stack(raw_bounds["lower"]), np.stack(raw_bounds["upper"])
                if not (np.all(lower <= upper) and
                        np.all(lower <= per_layer + 1e-7) and np.all(per_layer <= upper + 1e-7)):
                    raise ValueError("limites oficiais não abrangem previsão original por horizonte")
                lo = float(np.average(np.sum(lower, axis=0), weights=weights))
                hi = float(np.average(np.sum(upper, axis=0), weights=weights))
                per_horizon = {names[i]: {
                    "lower_tc_ha": float(np.average(lower[i], weights=weights)),
                    "upper_tc_ha": float(np.average(upper[i], weights=weights))}
                    for i in range(5)}
                official = {"status": "ENVELOPE_MARGINAL_OFICIAL",
                    "provenance": official_provenance or {},
                    "marginal_horizon_bounds": per_horizon,
                    "sum_bounds_envelope_tc_ha": [lo, hi],
                    "sum_bounds_envelope_stock_tC": [lo*covered/10000, hi*covered/10000],
                    "mapped_stock_area_ha": covered/10000,
                    "predictive_uncertainty_quantified": False,
                    "marginal_envelope_available": True,
                    "interpretation": ("Soma dos limites marginais publicados por horizonte. "
                       "NÃO é IC95% conjunto validado para 0–100 cm ou para o estoque da propriedade.")}
            except Exception as exc:
                official = {"status": "N/D",
                            "reason": type(exc).__name__ + ": " + str(exc)[:180],
                            "predictive_uncertainty_quantified": False}
        out["0–100 cm"]["official_uncertainty"] = official
        out["0–100 cm"]["predictive_uncertainty_quantified"] = (
            official["predictive_uncertainty_quantified"])
        out["_diagnostic"]["official_uncertainty"] = official
        return out
