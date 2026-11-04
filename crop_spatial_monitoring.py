"""Spatially explicit crop sampling for large municipal AOIs.

Uses the exact disjoint land-use polygons saved by run_land_use. Sampled
Sentinel-1 fields are NOT a validated wall-to-wall vigor map. No whole-municipality
raster pixels are treated as a field; native-cover polygons are excluded.
"""
from __future__ import annotations

from pathlib import Path


def crop_geometry(land, crop, *, canonical_fn):
    import geopandas as gpd
    path = (land or {}).get("vector_path")
    if not path or not Path(path).is_file():
        return None
    frame = gpd.read_file(path)
    if frame.empty or not {"class_name", "source"}.issubset(frame.columns) or frame.crs is None:
        return None
    mask = (frame["class_name"].map(
        lambda name: canonical_fn(str(name)[len("Lavoura de "):])
        if str(name).casefold().startswith("lavoura de ") else None) == crop)
    mask &= frame["source"].isin(("MAPBIOMAS", "SAR_VALIDADO"))
    selected = frame.loc[mask, ["geometry"]].copy()
    selected = selected[selected.geometry.notna() & ~selected.geometry.is_empty]
    return selected if not selected.empty else None


def sample_crop_patches(geometry, *, max_patches=6, min_area_ha=12.0,
                        target_patch_ha=64.0, min_purity=.90):
    """Deterministic representative interior patches, using equal-area metres.

    A crop polygon is never replaced by its municipality bounding rectangle.
    A patch has >=90% mapped crop; its *actual clipped geometry* is passed to S1.
    Sampling is a diagnostic convenience, not representative survey design.
    """
    import geopandas as gpd
    from shapely.geometry import box
    from shapely.geometry import Point
    from math import sqrt

    if geometry is None or geometry.empty or geometry.crs is None:
        return []
    mapped = geometry.to_crs(6933)
    shapes = [geom for geom in mapped.geometry if geom is not None and not geom.is_empty]
    if not shapes:
        return []
    shapes.sort(key=lambda x: -x.area)
    patches = []
    side = sqrt(target_patch_ha * 10000.0)
    for geom in shapes:
        if len(patches) >= max_patches:
            break
        if geom.area < min_area_ha * 10000.0:
            continue
        # Reproducible spatial spread across large agricultural polygons.
        # These are diagnostic patches, NOT a random survey or exhaustive map.
        minx, miny, maxx, maxy = geom.bounds
        candidates = [geom.representative_point()]
        for i in range(1, 8):
            for j in range(1, 8):
                p = Point(minx + (maxx-minx)*i/8, miny + (maxy-miny)*j/8)
                if geom.contains(p):
                    candidates.append(p)
        for p in candidates:
            if len(patches) >= max_patches:
                break
            window = box(p.x-side/2, p.y-side/2, p.x+side/2, p.y+side/2)
            clipped = geom.intersection(window)
            if clipped.is_empty or clipped.area < min_area_ha*10000:
                continue
            if clipped.area/window.area < min_purity:
                continue
            if any(clipped.intersects(old.to_crs(6933).geometry.iloc[0]) for old in patches):
                continue
            patches.append(gpd.GeoDataFrame(geometry=[clipped], crs=6933).to_crs(4326))
    return patches


def sampled_sentinel_vigor(crop_gdf, as_of, code, vigor_fn, *,
                           max_patches=6):
    patches = sample_crop_patches(crop_gdf, max_patches=max_patches)
    if not patches:
        return {"status": "N/D", "reason": "sem parcelas internas suficientemente homogêneas no mapa anual",
                "patches_evaluated": 0, "patches_valid": 0}
    by_class = {"baixo vigor": 0., "vigor adequado": 0., "alto vigor": 0.}
    attempts = []
    accepted = 0
    total_crop_area_ha = float(crop_gdf.to_crs(6933).geometry.area.sum()/10000.0)
    weighted = 0.
    for idx, patch in enumerate(patches):
        ha = float(patch.to_crs(6933).geometry.area.sum()/10000)
        try:
            result = vigor_fn(patch, as_of, code)
        except Exception as exc:
            result = {"status": "N/D", "reason": type(exc).__name__ + ": " + str(exc)[:160]}
        attempts.append({"sample": idx+1, "area_ha": ha,
                         "status": result.get("status"), "reason": result.get("reason"),
                         "scene_id": result.get("scene_id"),
                         "acquisition_utc": result.get("acquisition_utc")})
        p = result.get("probabilities")
        if result.get("status") not in ("experimental", "validated") or not isinstance(p, dict):
            continue
        try:
            weights = {c: float(p[c]) for c in by_class}
        except (KeyError, TypeError, ValueError):
            continue
        if any(v < 0 or v > 1 for v in weights.values()) or abs(sum(weights.values())-1)>1e-4:
            continue
        weighted += ha
        accepted += 1
        for name in by_class:
            by_class[name] += ha*weights[name]
    if not accepted:
        return {"status": "N/D", "reason": "Sentinel-1 ou referências da mesma classe indisponíveis nos polígonos amostrados",
                "patches_evaluated": len(patches), "patches_valid": 0, "sample_audit": attempts,
                "mapped_crop_area_ha": total_crop_area_ha, "sar_sample_coverage_fraction": 0.0}
    prob = {name: val/weighted for name,val in by_class.items()}
    label = max(prob, key=prob.get)
    return {"status": "experimental", "class": label, "probabilities": prob,
            "patches_evaluated": len(patches), "patches_valid": accepted,
            "sample_area_ha": weighted, "mapped_crop_area_ha": total_crop_area_ha,
            "sar_sample_coverage_fraction": weighted/total_crop_area_ha if total_crop_area_ha>0 else 0.,
            "sample_audit": attempts,
            "source": "Sentinel-1 RTC + classes MapBiomas, amostragem espacial dirigida",
            "uncertainty_warning": "Probabilidades descritivas das amostras, NÃO calibradas para todo o município; erro de transferência e seleção não quantificado"}
