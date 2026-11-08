"""SAR land-use classification with independent validation and spatial precedence.

RF here is a new implementation of a published method family, not the fitted
weights of any cited paper. No nationally validated weights are bundled.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

AREA_CRS = 'EPSG:6933'  # equal-area; EPSG:5880 is polyconic, not equal-area
# The prediction is its calibrated argmax. There is NO universal minimum
# accuracy/probability or sample count to qualify an independently measurable
# model. The actual accuracy, uncertainty and sample size must always be shown.
# Scientific provenance and independent validation remain mandatory.
SCORE_THRESHOLD = 0.0
# Operational class acceptance: 30 independent spatial holdout units and
# a conservative Wilson 95% precision lower bound of at least 0.70.
MIN_VALIDATION = 30
MIN_PRECISION_LOWER = 0.70
MIN_DISTANCE_M = 1000.0

def _executive_crop_label(name):
    """Map a validated crop class to the plain-language label shown in reports."""
    import unicodedata
    key=''.join(c for c in unicodedata.normalize('NFD',str(name or '').casefold())
                if unicodedata.category(c)!='Mn').strip()
    aliases={'soja':'Lavoura de soja','milho':'Lavoura de milho','sorgo':'Lavoura de sorgo',
             'cafe':'Lavoura de café','cana':'Lavoura de cana-de-açúcar',
             'cana-de-acucar':'Lavoura de cana-de-açúcar','cana de acucar':'Lavoura de cana-de-açúcar',
             'arroz':'Lavoura de arroz','feijao':'Lavoura de feijão','citros':'Lavoura de citros',
             'citrus':'Lavoura de citros','algodao':'Lavoura de algodão','cotton':'Lavoura de algodão',
             'rice':'Lavoura de arroz','maize':'Lavoura de milho','soybean':'Lavoura de soja',
             'sorghum':'Lavoura de sorgo','coffee':'Lavoura de café','beans':'Lavoura de feijão'}
    return aliases.get(key)


def wilson_lower(correct, total):
    if not total:
        return 0.0
    p = correct / total
    z = 1.959963984540054
    return (p + z*z/(2*total) - z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))) / (1+z*z/total)


def validation_report(truth, predictions, scores):
    """Each observation must be an independently separated reference point."""
    import numpy as np
    from sklearn.metrics import confusion_matrix, classification_report
    truth, predictions, scores = np.asarray(truth), np.asarray(predictions), np.asarray(scores)
    labels = sorted(set(truth) | set(predictions))
    metrics = classification_report(truth, predictions, labels=labels, output_dict=True, zero_division=0)
    gates = {}
    for label in labels:
        # Zero is the internal abstention sentinel for invalid SAR height or
        # out-of-domain predictors, not a minimum published-accuracy rule.
        chosen = (predictions == label) & np.isfinite(scores) & (scores > 0) & (scores <= 1)
        n = int(chosen.sum())
        correct = int(((truth == label) & chosen).sum())
        lower = wilson_lower(correct, n)
        upper = 1.0 - wilson_lower(n-correct,n) if n else 1.0
        gates[label] = {'n_independent': n, 'correct': correct, 'precision': correct/n if n else None,
                        'precision_wilson95_lower': lower, 'precision_wilson95_upper': upper,
                        'eligible': n >= MIN_VALIDATION and lower >= MIN_PRECISION_LOWER, 'sample_size_warning': n < MIN_VALIDATION,
                        'accuracy_policy': 'any_measured_accuracy_with_explicit_sample_and_interval'}
    return {'labels': labels, 'confusion_matrix': confusion_matrix(truth, predictions, labels=labels).tolist(),
            'metrics': metrics, 'gates': gates, 'score_threshold': SCORE_THRESHOLD,
            'min_validation': MIN_VALIDATION, 'min_precision_lower': MIN_PRECISION_LOWER,
            'minimum_accuracy_required': '30 holdouts independentes e limite inferior Wilson IC95% >= 0,70 por classe',
            'validation_scope': 'measured on the supplied independent reference observations',
            'uncertainty': 'IC95% Wilson da precisão da classe aceita, condicionado à independência/representatividade dos pontos; não é erro de área nem garantia individual por pixel.'}


def _robust_polygon_overlay(left, right, operation):
    """Precision-safe polygon overlay; never silently drop missing area."""
    import shapely
    from shapely.errors import GEOSException
    from shapely.geometry import GeometryCollection
    if operation not in ('intersection', 'difference'):
        raise ValueError('Unsupported overlay operation')
    def polygonal(g):
        if g.is_empty:
            return GeometryCollection()
        if g.geom_type in ('Polygon', 'MultiPolygon'):
            return g
        from shapely.ops import unary_union
        polygons = [p for p in getattr(g, 'geoms', ()) if p.geom_type in ('Polygon', 'MultiPolygon') and not p.is_empty]
        return unary_union(polygons) if polygons else GeometryCollection()
    left, right = polygonal(shapely.make_valid(left)), polygonal(shapely.make_valid(right))
    if left.is_empty or (operation == 'intersection' and right.is_empty):
        return GeometryCollection()
    if operation == 'difference' and right.is_empty:
        return left
    fn = getattr(shapely, operation)
    try:
        return polygonal(shapely.make_valid(fn(left, right)))
    except GEOSException as first:
        # Fixed-precision overlay is the documented GEOS robustness fallback.
        # Grid is 1 mm in EPSG:6933 (metres), far below 30-m map resolution.
        try:
            a = shapely.set_precision(left, 0.001, mode='valid_output')
            b = shapely.set_precision(right, 0.001, mode='valid_output')
            return polygonal(shapely.make_valid(fn(a, b, grid_size=0.001)))
        except GEOSException as second:
            raise ValueError(
                f'Falha geométrica GEOS em {operation}; nenhuma área foi '
                f'aceita sem verificação. Original: {first}; precisão: {second}'
            ) from second


def partition_land_use(aoi, layers):
    """Ordered layers: accepted SAR, IBGE, MapBiomas. Disjoint exact intersections.

    Rows need geometry, class_name, source, taxonomy. Never substitute AOI-wide
    percentages for spatial intersections. Coverage gaps remain explicit.
    """
    import geopandas as gpd
    from shapely.geometry import mapping
    from carbon_compartments import aoi_to_wgs84
    frame = aoi_to_wgs84(aoi).to_crs(AREA_CRS)
    geom = frame.geometry.union_all()
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        raise ValueError('AOI sem polígono válido.')
    remaining, pieces = geom, []
    for layer in layers:
        if layer is None or layer.empty:
            continue
        if layer.crs is None:
            raise ValueError('Camada de classificação sem CRS.')
        projected = layer.to_crs(AREA_CRS).copy()
        projected['geometry'] = projected.geometry.make_valid()
        projected = projected[projected.geometry.notna() & ~projected.geometry.is_empty]
        # Dissolve tile fragments by label before geometry operations. The prior
        # per-pixel loop was quadratic for large AOIs (e.g. Marary), despite
        # raster reads already being tiled. Preserve contradictory overlaps as
        # gaps that may be filled by the next source.
        if 'secondary_crop' not in projected.columns:
            projected['secondary_crop'] = ''
        projected['secondary_crop'] = projected['secondary_crop'].fillna('')
        projected = projected.dissolve(
            by=['class_name', 'source', 'taxonomy', 'secondary_crop'], as_index=False)
        from shapely.ops import unary_union
        conflicts = []
        for pos, row in enumerate(projected.itertuples()):
            for j in projected.sindex.query(row.geometry, predicate='intersects'):
                if int(j) <= pos:
                    continue
                other = projected.iloc[int(j)]
                if row.class_name != other.class_name:
                    overlap = _robust_polygon_overlay(row.geometry, other.geometry, 'intersection')
                    if not overlap.is_empty and overlap.area > 0:
                        conflicts.append(overlap)
        conflict = unary_union(conflicts)
        for row in projected.itertuples():
            clipped = _robust_polygon_overlay(remaining, row.geometry, 'intersection')
            if not conflict.is_empty:
                clipped = _robust_polygon_overlay(clipped, conflict, 'difference')
            if clipped.is_empty or clipped.area <= 0:
                continue
            pieces.append({'class_name': row.class_name, 'source': row.source,
                           'taxonomy': row.taxonomy, 'secondary_crop': getattr(row, 'secondary_crop', '') or '', 'geometry': clipped})
            remaining = _robust_polygon_overlay(remaining, clipped, 'difference')
    if remaining.area > 1e-6:
        pieces.append({'class_name': 'Não classificado', 'source': 'SEM_COBERTURA',
                       'taxonomy': 'sem classificação', 'geometry': remaining})
    out = gpd.GeoDataFrame(pieces, crs=AREA_CRS)
    if 'secondary_crop' not in out.columns:
        out['secondary_crop'] = ''
    out['secondary_crop'] = out['secondary_crop'].fillna('')
    out = out.dissolve(by=['class_name', 'source', 'taxonomy', 'secondary_crop'], as_index=False)
    out['area_ha'] = out.geometry.area / 10000
    out['area_pct'] = 100 * out.geometry.area / geom.area
    records = out.drop(columns='geometry').to_dict('records')
    if abs(sum(r['area_ha'] for r in records) - geom.area/10000) > max(1e-6, geom.area/10000*1e-8):
        raise ValueError('Falha no fechamento das áreas de classificação.')
    return out.to_crs('EPSG:4326'), {
        'classes': records, 'area_aoi_ha': geom.area/10000,
        'method': 'interseção exata AOI × polígonos das células; área em EPSG:6933; denominador: AOI inteira',
        'priority': 'camadas de cobertura atual elegíveis na ordem fornecida; IBGE legenda_1 não confirma uso atual',
        'area_uncertainty': 'Área cartográfica; sem correção amostral de área e sem IC de área.',
    }


def raster_class_polygons(aoi, raster_path, legend=None):
    """Polygonize only AOI window, retaining edge-cell footprints for clipping."""
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.features import shapes, geometry_window
    from shapely.geometry import shape, mapping
    from carbon_compartments import aoi_to_wgs84
    from mapbiomas_zonal import LEGEND
    geom = aoi_to_wgs84(aoi).geometry.union_all()
    path = str(raster_path)
    if path.startswith('https://'):
        path = '/vsicurl/' + path
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_TIMEOUT='25'):
        with rasterio.open(path) as src:
            if not src.crs:
                raise ValueError('Raster de classes sem CRS.')
            inside = gpd.GeoSeries([geom], crs=4326).to_crs(src.crs).iloc[0]
            # Read bounded tiles; never reject a valid AOI for exceeding 4M pixels.
            # Polygonize each tile independently, then let the downstream AOI
            # intersection clip footprints and reconcile class areas.
            from rasterio.windows import Window, transform as window_transform
            from rasterio.features import geometry_mask
            from shapely.geometry import box
            from shapely.prepared import prep
            import math
            from rasterio.errors import WindowError
            try:
                bounds_window = geometry_window(src, [mapping(inside)])
            except WindowError:
                return gpd.GeoDataFrame(columns=['class_code','class_name','source','taxonomy','geometry'], geometry='geometry', crs=src.crs)
            x0 = max(0, int(bounds_window.col_off))
            y0 = max(0, int(bounds_window.row_off))
            x1 = min(src.width, int(math.ceil(bounds_window.col_off + bounds_window.width)))
            y1 = min(src.height, int(math.ceil(bounds_window.row_off + bounds_window.height)))
            rows = []
            prepared = prep(inside)
            tile_size = 512
            for y in range(y0, y1, tile_size):
                for x in range(x0, x1, tile_size):
                    window = Window(x, y, min(tile_size, x1-x), min(tile_size, y1-y))
                    tile_bounds = rasterio.windows.bounds(window, src.transform)
                    if not prepared.intersects(box(*tile_bounds)):
                        continue
                    data = src.read(1, window=window, masked=True)
                    transform = window_transform(window, src.transform)
                    inside_mask = geometry_mask([mapping(inside)], out_shape=data.shape,
                                                transform=transform, invert=True,
                                                all_touched=True)
                    valid = inside_mask & ~np.ma.getmaskarray(data) & np.isfinite(data.data) & (data.data > 0)
                    if not valid.any():
                        continue
                    for geometry, code in shapes(data.data.astype('int32'), mask=valid, transform=transform):
                        code = int(code)
                        name = legend[code] if legend is not None else LEGEND.get(code, (f'Classe MapBiomas {code}', ''))[0]
                        rows.append({'class_code': code, 'class_name': name,
                                     'source': 'SAR_VALIDADO' if legend is not None else 'MAPBIOMAS',
                                     'taxonomy': 'legenda do modelo SAR' if legend is not None else 'MapBiomas',
                                     'geometry': shape(geometry)})
            return gpd.GeoDataFrame(rows, columns=['class_code','class_name','source','taxonomy','geometry'], geometry='geometry', crs=src.crs)


def _sha(path):
    digest = hashlib.sha256()
  