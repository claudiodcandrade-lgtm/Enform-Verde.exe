"""Create strictly training-only SAR samples from mapped agricultural references.

Map-derived labels are pseudo-labels: never use them to certify independent accuracy,
even when spatially held out. This module does not change the validated classifier gate.
"""
from __future__ import annotations
import json
from pathlib import Path

# Verified MapBiomas Brazil Collection 11 agricultural legend (first-season coverage).
MAPBIOMAS_C11_CROPS = {39: "Soja", 20: "Cana-de-açúcar", 40: "Arroz",
                       46: "Café", 47: "Citros"}
# Second season is a different map and MUST NOT be silently used as first season.
SUPPORTED_MAPS = {"mapbiomas_c11_first_season": MAPBIOMAS_C11_CROPS}


def extract_pseudolabel_training_samples(
    feature_raster, reference_raster, output_geojson, *,
    reference_kind="mapbiomas_c11_first_season", year=None,
    reference_url=None, feature_year=None, max_per_class=500,
    edge_buffer_pixels=1, random_seed=42,
):
    """Pair existing SAR feature cells with strictly same-season agricultural map labels.

    Requires identical pixel grids/CRS: rejects implicit reprojection, mismatched
    years, invalid/masked cells. Erodes homogeneous reference patches to avoid
    boundaries; spatial correlation and systematic map label errors still remain.
    Returns GeoJSON of training candidates ONLY, never a validated model.
    """
    import numpy as np
    import rasterio
    from scipy.ndimage import binary_erosion
    from rasterio.transform import xy
    if reference_kind not in SUPPORTED_MAPS:
        raise ValueError("Produto/legenda agrícola não suportado; não misturar primeira e segunda safra.")
    if not isinstance(year,int) or year < 1985 or not reference_url:
        raise ValueError("Referência requer ano inteiro e URL institucional verificável.")
    if feature_year != year:
        raise ValueError("Safra dos atributos SAR não corresponde ao ano cartográfico.")
    if max_per_class < 1 or max_per_class > 50000 or not 1 <= edge_buffer_pixels <= 10:
        raise ValueError("Parâmetros amostrais fora dos limites permitidos.")
    with rasterio.open(feature_raster) as features, rasterio.open(reference_raster) as refs:
        if (features.crs is None or refs.crs is None or features.crs != refs.crs
            or features.transform != refs.transform or features.width != refs.width
            or features.height != refs.height):
            raise ValueError("Rasters SAR e referência precisam estar na mesma grade e CRS.")
        if features.count < 1 or refs.count != 1:
            raise ValueError("Atributos SAR ou mapa agrícola com bandas inválidas.")
        if features.width*features.height*features.count > 40_000_000:
            raise ValueError("Raster excede limite; recortar AOI antes da extração.")
        a = features.read(masked=True)
        b = refs.read(1,masked=True)
        values = a.data.astype("float64")
        valid = (~np.ma.getmaskarray(a).any(axis=0)
                 & np.isfinite(values).all(axis=0)
                 & ~np.ma.getmaskarray(b))
        rng = np.random.default_rng(random_seed)
        records = []
        counts = {}
        for code, name in SUPPORTED_MAPS[reference_kind].items():
            patch = (b.data == code) & valid
            safe = binary_erosion(patch, iterations=edge_buffer_pixels, border_value=0)
            positions = np.argwhere(safe)
            if len(positions) > max_per_class:
                positions = positions[rng.choice(len(positions), size=max_per_class, replace=False)]
            counts[name] = len(positions)
            for row, col in positions:
                lon, lat = xy(features.transform,int(row),int(col))
                records.append({"type":"Feature",
                                "geometry":{"type":"Point","coordinates":[float(lon),float(lat)]},
                                "properties":{"label":name,"source":"MAP_DERIVED_PSEUDOLABEL",
                                              "reference_kind":reference_kind,
                                              "reference_url":reference_url,"reference_year":year,
                                              "split":"train","unit_id":f"{reference_kind}-{year}-{int(row)}-{int(col)}",
                                              "training_only":True,
                                              "sar_features":[float(v) for v in values[:,row,col]]}})
        output_path = Path(output_geojson)
        output_path.parent.mkdir(parents=True,exist_ok=True)
        output_path.write_text(json.dumps({
            "type":"FeatureCollection",
            "name":"SAR_TRAINING_PSEUDOLABELS_NOT_VALIDATION",
            "crs":{"type":"name","properties":{"name":features.crs.to_string()}},
            "features":records},ensure_ascii=False),encoding="utf-8")
        return {"path":str(output_path),"counts":counts,"total":len(records),
                "class_source":reference_url,"year":year,"reference_kind":reference_kind,
                "validation_eligible":False,
                "restriction":"Pseudorrótulos cartográficos somente treino. Validação independente real obrigatória; split espacial do mesmo mapa não é validação independente."}
