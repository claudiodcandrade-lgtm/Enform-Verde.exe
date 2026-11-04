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


def mapped_soil_0_100_on_polygon(gdf, horizon_paths, *, max_cells=1500000):
    """Area-weighted raw raster 0-100 cm on EXACT clipped polygon intersection.

    Input gdf is the actual native fitophysiognomy intersection passed by the
    carbon engine, not the AOI bbox or the entire property. Every raster cell
    receives an equal-area (EPSG:6933) intersection weight. Only cells with
    all five independent depth layers can contribute; no 0-30 extrapolation.
    Incomplete mapped coverage is reported N/D rather than scaled to whole AOI.
    """
    import numpy as np
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds, transform as window_transform
    from shapely.geometry import box, mapping
    from shapely.ops import transform as transform_geom
    from pyproj import Transformer
    from soil_profile_stats import summarize_paired_soil_profiles

    def nd(reason, **extra):
        return {"_diagnostic": {"target_depth_cm": 100,
                "target_status": "INCOMPLETO_NAO_EXTRAPOLAR",
                "method": "area_weighted_raw_raster_polygon_intersection",
                "reason": reason, **extra}}
    if set(horizon_paths) != {i for i,_ in DEPTHS}:
        return nd("cinco rasters brutos de 0–100 cm obrigatórios")
    with rasterio.Env():
        from contextlib import ExitStack
        with ExitStack() as stack:
            srcs = [stack.enter_context(rasterio.open(horizon_paths[i])) for i,_ in DEPTHS]
            first = srcs[0]
            if not first.crs or first.count != 1 or not first.crs.is_projected:
                return nd("raster base não é camada contínua projetada de banda única")
            if abs(first.transform.b)>1e-10 or abs(first.transform.d)>1e-10:
                return nd("rasters rotacionados requerem processamento específico")
            # Reject RGB/rendered imagery and integer-coded display pixels.
            # This is a necessary structural check, not proof of official origin.
            for src in srcs:
                if src.count != 1 or src.dtypes[0] not in ("float32", "float64"):
                    return nd("camada não é raster científico contínuo float de banda única")
                if src.colorinterp and any(str(ci).lower().endswith(
                        ("red", "green", "blue", "palette")) for ci in src.colorinterp):
                    return nd("raster de visualização RGB/paleta não é estoque bruto")
            for src in srcs[1:]:
                if (src.count != 1 or src.crs != first.crs
                        or src.transform != first.transform
                        or src.width != first.width or src.height != first.height):
                    return nd("rasters não alinhados (CRS, pixel ou extensão distintos)")
            geom = gdf.to_crs(first.crs).geometry.union_all()
            if geom.is_empty or not geom.is_valid:
                return nd("interseção poligonal nativa inválida")
            bounds = geom.bounds
            left, bottom, right, top = first.bounds
            if bounds[2] <= left or bounds[0] >= right or bounds[3] <= bottom or bounds[1] >= top:
                return nd("polígono fora da cobertura do mapa oficial")
            window = from_bounds(max(bounds[0],left), max(bounds[1],bottom),
                                 min(bounds[2],right), min(bounds[3],top),
                                 transform=first.transform)
            # Expand to enclosing integer pixels; rounding to nearest can omit edge cells.
            from rasterio.windows import Window
            col0 = math.floor(window.col_off)
            row0 = math.floor(window.row_off)
            col1 = math.ceil(window.col_off + window.width)
            row1 = math.ceil(window.row_off + window.height)
            window = Window(col0,row0,col1-col0,row1-row0).intersection(
                Window(0,0,first.width,first.height))
            width, height = int(window.width), int(window.height)
            if width<1 or height<1 or width*height>max_cells:
                return nd("recorte excede capacidade para cálculo de interseções exatas",
                          raster_window_cells=width*height, maximum_cells=max_cells)
            transform = window_transform(window, first.transform)
            mask = geometry_mask([mapping(geom)], out_shape=(height,width),
                                 transform=transform, invert=True, all_touched=True)
            arrays = [src.read(1,window=window,masked=True) for src in srcs]
            valid = mask.copy()
            for data in arrays:
                valid &= ~np.ma.getmaskarray(data) & np.isfinite(data.data) & (data.data >= 0)
            valid_indices = np.argwhere(valid)
            to_eq = Transformer.from_crs(first.crs, "EPSG:6933", always_xy=True).transform
            geom_eq = transform_geom(to_eq,geom)
            requested_area = geom_eq.area
            if requested_area<=0:
                return nd("área da interseção não positiva")
            weights=[]; samples=[]; covered=0.0
            for row,col in valid_indices:
                x0,y0 = transform*(int(col),int(row))
                x1,y1 = transform*(int(col)+1,int(row)+1)
                pix = transform_geom(to_eq,box(min(x0,x1),min(y0,y1),
                                                 max(x0,x1),max(y0,y1)))
                overlap = pix.intersection(geom_eq).area
                if overlap<=0:continue
                weights.append(overlap)
                samples.append(float(sum(float(a.data[row,col]) for a in arrays)))
                covered+=overlap
            coverage=min(1.0,covered/requested_area)
            diagnostic={"coverage_fraction":coverage,
                        "covered_area_ha":covered/10000,
                        "intersected_area_ha":requested_area/10000,
                        "valid_complete_pixels":len(samples),
                        "source":"raw_aligned_pronasolos_geotiff",
                        "method":"area_weighted_raw_raster_polygon_intersection",
                        "target_depth_cm":100,
                        "uncertainty":"Spatial SD is descriptive only; no AOI CI95 or transfer error"}
            if not samples or coverage<0.995:
                return nd("mapa 0–100 cm sem cobertura completa na interseção",
                          **{k:v for k,v in diagnostic.items() if k!="method" and k!="target_depth_cm"})
            weights=np.array(weights,dtype="float64")
            samples=np.array(samples,dtype="float64")
            mean=float(np.average(samples,weights=weights))
            sd=float(np.sqrt(np.average((samples-mean)**2,weights=weights))) if len(samples)>1 else None
            return {"0–100 cm":{
                        "tc_ha":mean, "spatial_sd_tc_ha":sd,
                        "n_samples":len(samples),
                        "area_covered_ha":covered/10000,
                        "coverage_fraction":coverage,
                        "source":"Embrapa Solos/PronaSolos (5 mapas brutos, 90m)",
                        "uncertainty_kind":"desvio espacial de pixels, sem IC95% da AOI",
                        "profile_pairing":"mesmo pixel e cinco horizontes, interseção geométrica exata",
                        "predictive_uncertainty_quantified":False},
                    "_diagnostic":dict(diagnostic,
                         target_status="COMPLETO_POR_INTERSECAO_RASTER",
                         full_raster_0_100=True)}
