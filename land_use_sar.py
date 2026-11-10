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
# Owner decision 08/11/2026 (question 2 = B): any MEASURED accuracy is accepted as
# experimental, provided its uncertainty is estimated (n independent + Wilson CI95).
MIN_VALIDATION = 1
MIN_PRECISION_LOWER = 0.0
SMALL_SAMPLE_WARNING = 30
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
                        'eligible': n >= MIN_VALIDATION and lower >= MIN_PRECISION_LOWER, 'sample_size_warning': n < SMALL_SAMPLE_WARNING,
                        'acceptance_status': ('experimental_measured' if n >= MIN_VALIDATION else 'not_measured'),
                        'accuracy_policy': 'any_measured_accuracy_with_explicit_sample_and_interval'}
    return {'labels': labels, 'confusion_matrix': confusion_matrix(truth, predictions, labels=labels).tolist(),
            'metrics': metrics, 'gates': gates, 'score_threshold': SCORE_THRESHOLD,
            'min_validation': MIN_VALIDATION, 'min_precision_lower': MIN_PRECISION_LOWER,
            'minimum_accuracy_required': None,
            'acceptance_policy': 'qualquer acurácia MEDIDA é aceita como experimental com n independente e IC95% Wilson obrigatórios (decisão do proprietário, 08/11/2026)',
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
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def classify_config(aoi, config_path, output_dir):
    """Fit RF on actual institutional reference points; validate before precedence.

    Feature GeoTIFF bands must be fully described in config and in band names.
    Samples are GeoJSON/GPKG points with label, split, unit_id; one point per
    independent unit. No training on MapBiomas/IBGE pseudo-labels is accepted.
    """
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.mask import mask
    from shapely.geometry import shape, mapping
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neighbors import NearestNeighbors
    from carbon_compartments import aoi_to_wgs84
    cfg_path = Path(config_path)
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    base = cfg_path.parent
    for field in ('reference_url','institution','reference_kind','publication_url','sensor',
                  'processing','period','features','classes','domain','samples','feature_raster'):
        if not cfg.get(field):
            raise ValueError('Configuração SAR incompleta: ' + field)
    if cfg['reference_kind'] != 'independent_observations':
        raise ValueError('Referência exige observações independentes; mapas IBGE/MapBiomas não validam prioridade sobre si mesmos.')
    domain = shape(cfg['domain'])
    aoigeom = aoi_to_wgs84(aoi).geometry.union_all()
    if not domain.is_valid or not domain.covers(aoigeom):
        raise ValueError('AOI fora do domínio geográfico documentado do modelo.')
    if not any(f.get('source') == 'SAR' for f in cfg['features']):
        raise ValueError('O modelo precisa conter atributos SAR reais.')
    if any(not f.get('name') or not f.get('unit') or not f.get('source') for f in cfg['features']):
        raise ValueError('Cada atributo exige nome, unidade e origem.')
    samples_path, raster_path = base/cfg['samples'], base/cfg['feature_raster']
    points = gpd.read_file(samples_path)
    if not points.crs or not set(('label','split','unit_id')).issubset(points.columns):
        raise ValueError('Amostras exigem CRS e campos label, split, unit_id.')
    if points.empty or points[['label','split','unit_id']].isna().any().any() or not points.geom_type.eq('Point').all():
        raise ValueError('Amostras devem ser pontos válidos, com rótulo e unidade independente.')
    if points.unit_id.duplicated().any() or not points.split.isin(['train','calibration','validation']).all():
        raise ValueError('Uma observação por unidade independente; split deve ser train, calibration ou validation.')
    if not points.to_crs(4326).geometry.map(domain.covers).all():
        raise ValueError('Referências fora do domínio documentado.')
    train = np.asarray(points.split == 'train')
    calibration = np.asarray(points.split == 'calibration')
    test = np.asarray(points.split == 'validation')
    if train.sum() < 10 or calibration.sum() < 10 or test.sum() < 2:
        raise ValueError('Treino/validação independentes insuficientes.')
    labels = points.label.astype(str).to_numpy()
    if len(set(labels[train])) < 2 or set(labels[test]) != set(labels[train]) or set(labels[calibration]) != set(labels[train]):
        raise ValueError('Treino e validação precisam representar as mesmas classes, no mínimo duas.')
    if not set(labels).issubset(cfg['classes']):
        raise ValueError('Classe sem legenda explícita.')
    # Distances use a local azimuthal equidistant CRS (not a global area CRS).
    center = domain.centroid
    metric = points.to_crs(f'+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84 +units=m')
    xy = np.column_stack((metric.geometry.x, metric.geometry.y))
    def nearest_distance(query, reference):
        return float(NearestNeighbors(n_neighbors=1).fit(reference).kneighbors(query)[0].min())
    if min(nearest_distance(xy[test],xy[train|calibration]), nearest_distance(xy[calibration],xy[train])) < MIN_DISTANCE_M:
        raise ValueError('Treino/calibração/validação a menos de 1 km; risco de vazamento espacial.')
    distances = NearestNeighbors(n_neighbors=2).fit(xy[test]).kneighbors(xy[test])[0]
    if distances[:,1].min() < MIN_DISTANCE_M:
        raise ValueError('Pontos de validação a menos de 1 km; independência não demonstrada.')
    names = [f['name'] for f in cfg['features']]
    with rasterio.open(raster_path) as src:
        if not src.crs or list(src.descriptions) != names:
            raise ValueError('Nomes/ordem das bandas e CRS devem coincidir com o contrato de atributos.')
        if any(str(src.tags().get(k,'')) != str(cfg[k]) for k in ('sensor','processing','period')):
            raise ValueError('Sensor/processamento/período do GeoTIFF diferem do contrato.')
        sample_points = points.to_crs(src.crs)
        x = np.ma.vstack(list(src.sample(zip(sample_points.geometry.x, sample_points.geometry.y), masked=True)))
        if np.ma.getmaskarray(x).any() or not np.isfinite(x.data).all():
            raise ValueError('Amostras fora do raster ou em nodata.')
        x = np.asarray(x)
        model = RandomForestClassifier(n_estimators=300, max_features='sqrt', min_samples_leaf=2,
                                       class_weight='balanced_subsample', random_state=42, n_jobs=1)
        model.fit(x[train], labels[train])
        # Multiclass logistic calibration on a separate spatial split.
        from sklearn.linear_model import LogisticRegression
        calibrator = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        calibrator.fit(np.log(np.clip(model.predict_proba(x[calibration]),1e-8,1)), labels[calibration])
        def probabilities(values):
            return calibrator.predict_proba(np.log(np.clip(model.predict_proba(values),1e-8,1)))
        if list(calibrator.classes_) != list(model.classes_):
            raise ValueError('Ordem das classes de calibração incompatível.')
        probs = probabilities(x[test])
        pred = model.classes_[probs.argmax(axis=1)]
        scores = probs.max(axis=1)
        validation_in_range = ((x[test] >= x[train].min(axis=0)) & (x[test] <= x[train].max(axis=0))).all(axis=1)
        scores = np.where(validation_in_range, scores, 0.0)
        parents = {label: cfg['classes'][label]['parent'] for label in model.classes_}
        def native_safe(values,label):
            if parents[label]!='vegetação natural':return True
            contract=native_height_contract(cfg)
            if not native_formation(label) or contract is None:return False
            hi,ui=contract
            uncertainty=values[ui]
            if not math.isfinite(uncertainty) or uncertainty<0 or values[hi]-uncertainty<0:return False
            bounds=np.tile(values,(2,1));bounds[:,hi]=[values[hi]-uncertainty,values[hi]+uncertainty]
            if not ((bounds>=x[train].min(axis=0)) & (bounds<=x[train].max(axis=0))).all():return False
            bp=probabilities(bounds)
            return bool((model.classes_[bp.argmax(axis=1)]==label).all())
        # Validation uses exactly the same native abstention as operational pixels.
        scores=np.where([native_safe(v,l) for v,l in zip(x[test],pred)],scores,0.0)
        report = validation_report(labels[test], pred, scores)
        reliability=[]
        for low in np.arange(0,1,0.1):
            selected=(probs.max(axis=1)>=low)&((probs.max(axis=1)<low+0.1) if low<0.9 else (probs.max(axis=1)<=1))
            if selected.any():reliability.append({'lower':float(low),'n':int(selected.sum()),'mean_probability':float(probs.max(axis=1)[selected].mean()),'observed_accuracy':float((pred[selected]==labels[test][selected]).mean())})
        report['reliability_bins']=reliability
        report['expected_calibration_error']=sum(r['n']*abs(r['mean_probability']-r['observed_accuracy']) for r in reliability)/int(test.sum())
        parents = {label: cfg['classes'][label]['parent'] for label in model.classes_}
        parent_names = sorted(set(parents.values()))
        if any(v not in ('área cultivada', 'uso agropecuário', 'silvicultura', 'vegetação natural', 'água', 'outro') for v in parent_names):
            raise ValueError('Grupo pai não reconhecido.')
        pp = np.column_stack([probs[:,[parents[c] == p for c in model.classes_]].sum(axis=1) for p in parent_names])
        parent_pred = np.asarray(parent_names)[pp.argmax(axis=1)]
        parent_report = validation_report([parents[l] for l in labels[test]], parent_pred, np.where(validation_in_range,pp.max(axis=1),0.0))
        geom_src = gpd.GeoSeries([aoigeom], crs=4326).to_crs(src.crs).iloc[0]
        from rasterio.features import geometry_window
        win = geometry_window(src,[mapping(geom_src)])
        if win.width * win.height * src.count > 40_000_000:
            raise ValueError('Janela de atributos excede limite de memória; subdivida a AOI.')
        data, transform = mask(src, [mapping(geom_src)], crop=True, all_touched=True, filled=False)
        if data[0].size > 4_000_000:
            raise ValueError('Janela de atributos excede 4 milhões de células; subdivida a AOI.')
        flat = data.data.reshape(src.count,-1).T
        good = ~np.ma.getmaskarray(data).any(axis=0).ravel() & np.isfinite(flat).all(axis=1)
        # Reject covariate extrapolation; eligibility requires an in-domain feature vector.
        good &= ((flat >= x[train].min(axis=0)) & (flat <= x[train].max(axis=0))).all(axis=1)
        labels_out = list(model.classes_) + [('Áreas cultivadas' if p=='área cultivada' else 'Grupo: '+p) for p in parent_names]
        codes = {label:i+1 for i,label in enumerate(labels_out)}
        output = np.zeros(len(flat), dtype='uint16')
        confidence_grid = np.full(len(flat), -9999.0, dtype='float32')
        positions = np.flatnonzero(good)
        for start in range(0,len(positions),65536):
            indices = positions[start:start+65536]
            prob = probabilities(flat[indices])
            detail = model.classes_[prob.argmax(axis=1)]
            parent_prob = np.column_stack([prob[:,[parents[c] == p for c in model.classes_]].sum(axis=1) for p in parent_names])
            for j, idx in enumerate(indices):
                label = detail[j]
                native_ok=native_safe(flat[idx],label)
                if native_ok and report['gates'][label]['eligible']:
                    output[idx] = codes[label]
                    confidence_grid[idx] = prob[j].max()
                else:
                    parent = parent_names[parent_prob[j].argmax()]
                    if parent!='vegetação natural' and parent_report['gates'][parent]['eligible']:
                        output[idx] = codes['Áreas cultivadas' if parent=='área cultivada' else 'Grupo: '+parent]
                        confidence_grid[idx] = parent_prob[j].max()
        outdir = Path(output_dir); outdir.mkdir(parents=True,exist_ok=True)
        output_path = outdir/'sar_uso_validado.tif'
        profile = src.profile.copy()
        profile.update(driver='GTiff',count=1,dtype='uint16',nodata=0,width=data.shape[2],height=data.shape[1],transform=transform)
        with rasterio.open(output_path,'w',**profile) as dst:
            dst.write(output.reshape(data.shape[1:]),1)
            dst.update_tags(class_legend=json.dumps({v:k for k,v in codes.items()},ensure_ascii=False),
                            source='RF SAR com calibração logística e validação espacial independente')
    confidence_path = outdir/'sar_confianca_calibrada.tif'
    profile.update(dtype='float32',nodata=-9999.0)
    with rasterio.open(confidence_path,'w',**profile) as dst:
        dst.write(confidence_grid.reshape(data.shape[1:]),1)
        dst.update_tags(meaning='Probabilidade calibrada da classe aceita; IC da precisão por classe em validacao_sar.json; não é garantia por pixel')
    report.update({'class_metadata':cfg['classes'], 'native_structure':cfg.get('native_structure'), 'native_policy':'Somente floresta/savana/campo; altura SAR e intervalo; estabilidade nos limites não é IC de classificação; IBGE apenas nomeia', 'confidence_raster':str(confidence_path), 'parent_validation':parent_report, 'source_config':str(cfg_path),
                   'reference_url':cfg['reference_url'],'institution':cfg['institution'],
                   'publication_url':cfg['publication_url'],'sensor':cfg['sensor'], 'processing':cfg['processing'],
                   'period':cfg['period'], 'features':cfg['features'], 'n_train':int(train.sum()),
                   'n_validation':int(test.sum()),'validation_in_covariate_range':int(validation_in_range.sum()), 'n_calibration':int(calibration.sum()), 'min_distance_m':MIN_DISTANCE_M,
                   'calibration':'logística multiclasse sobre log-probabilidades RF; split espacial separado',
                   'validation_multiclass_brier':float(np.mean(np.sum((probs-(labels[test][:,None] == model.classes_[None,:]).astype(float))**2,axis=1))),
                   'feature_sha256':_sha(raster_path),'reference_sha256':_sha(samples_path),
                   'implementation':'RF novo; não é reprodução dos pesos de artigo; validação por execução',
                   'raster':str(output_path),'eligible_pixels':int((output>0).sum())})
    (outdir/'validacao_sar.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    polygons = raster_class_polygons(aoi,output_path,{v:k for k,v in codes.items()})
    # Detailed crop names are exposed only for classes that passed the
    # independent class-level gate above. Parent classes remain generic.
    for pos,row in polygons.iterrows():
        if row.get('source')=='SAR_VALIDADO' and row.get('class_name') in cfg['classes']:
            meta=cfg['classes'][row['class_name']]
            if meta.get('parent')=='área cultivada':
                label=_executive_crop_label(row['class_name'])
                if label: polygons.at[pos,'class_name']=label
    return polygons, report


def native_formation(name):
    """Only broad structure; detailed native names belong to IBGE."""
    from native_carbon import normalize
    text=normalize(name).strip()
    if text in ('floresta','formacao florestal'):return 'floresta'
    if text in ('savana','formacao savanica'):return 'savana'
    if text in ('campo','formacao campestre'):return 'campo'
    return None


def ibge_formation(name):
    from native_carbon import normalize
    text=normalize(name)
    # Transition/contact legends do not unambiguously name a single formation.
    if any(x in text for x in ('contato','tensao ecologica','transicao')):return None
    if 'savana' in text or 'estepe' in text:return 'savana'
    if 'camp' in text:return 'campo'
    if 'florest' in text or text.startswith(('fod','foa','fes','fed')):return 'floresta'
    return None


def name_native_from_ibge(predicted, reference, *, max_proximity_m=0):
    """Name SAR-validated native patches from compatible IBGE physiognomies.

    First intersect exact polygons. Remaining native geometry may inherit
    ONLY the name (not a cover-classification) of the nearest compatible IBGE
    polygon when an explicit bounded metric proximity is authorized. The
    result keeps the SAR-validated native geometry and records distance.
    """
    import geopandas as gpd
    from math import isfinite
    if not isinstance(max_proximity_m,(int,float)) or not isfinite(max_proximity_m) or not 0 <= max_proximity_m <= 10000:
        raise ValueError("max_proximity_m deve estar entre 0 e 10000")
    pieces=[]
    ref=reference.to_crs(AREA_CRS) if reference is not None else None
    for row in predicted.to_crs(AREA_CRS).itertuples():
        formation=native_formation(row.class_name)
        if not formation or ref is None:
            pieces.append(dict(class_name=row.class_name,source=row.source,taxonomy=row.taxonomy,geometry=row.geometry))
            continue
        compatible=ref[ref.class_name.map(ibge_formation)==formation]
        remaining=row.geometry
        for item in compatible.itertuples():
            if remaining.is_empty:
                break
            clipped=remaining.intersection(item.geometry)
            if clipped.area>0:
                pieces.append(dict(class_name=item.class_name,source="SAR_VALIDADO+IBGE",
                                   taxonomy="Formação SAR: "+formation+"; nome: IBGE legenda_1 por interseção",
                                   geometry=clipped))
                remaining=remaining.difference(clipped)
        if not remaining.is_empty and remaining.area>0:
            if max_proximity_m>0 and not compatible.empty:
                # Distance refers to equal-area projection metres; approximate
                # proximity, not a survey/legal ecological boundary.
                nearest=min(compatible.itertuples(),
                            key=lambda item:remaining.distance(item.geometry))
                distance_m=float(remaining.distance(nearest.geometry))
                if distance_m <= max_proximity_m:
                    pieces.append(dict(class_name=nearest.class_name,
                                       source="SAR_VALIDADO+IBGE_PROXIMIDADE",
                                       taxonomy=("Presença de vegetação: classe SAR validada "+formation+
                                                 "; nome fitofisionômico INFERIDO por proximidade IBGE legenda_1; "+
                                                 "distância cartográfica aproximada "+f"{distance_m:.1f} m"+
                                                 "; limite "+f"{max_proximity_m:.0f} m"+
                                                 "; NÃO comprova extensão da classe IBGE"),
                                       geometry=remaining))
                    continue
            pieces.append(dict(class_name=row.class_name,source=row.source,
                               taxonomy="Formação SAR ampla; sem interseção IBGE compatível ou proximidade autorizada",
                               geometry=remaining))
    return gpd.GeoDataFrame(pieces,crs=AREA_CRS).to_crs(predicted.crs) if pieces else predicted


def native_height_contract(cfg):
    """No universal height thresholds or implied validation from a citation."""
    contract=cfg.get('native_structure',{})
    features=cfg['features']
    names=[f['name'] for f in features]
    h,u=contract.get('height_feature'),contract.get('uncertainty_feature')
    if not contract.get('validation_reference') or h not in names or u not in names:return None
    hi,ui=names.index(h),names.index(u)
    if hi==ui or any(features[i].get('source')!='SAR' or features[i].get('unit')!='m' for i in (hi,ui)):return None
    if contract.get('uncertainty_kind')!='interval_half_width':return None
    return hi,ui


def _download_official_mapbiomas(url, destination):
    """HTTPS fallback for GDAL builds without working /vsicurl/ support.

    An atomic, bounded download avoids leaving corrupt rasters in the cache.
    Never pretend that a partial file confirms native cover.
    """
    import os
    import shutil
    import urllib.request
    import rasterio
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.part')
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'EnformVerde/3.25 MapBiomas official GeoTIFF'})
        with urllib.request.urlopen(request,timeout=60) as response:
            content_type=response.headers.get('Content-Type','').lower()
            reported=response.headers.get('Content-Length')
            if 'text/html' in content_type or 'application/json' in content_type:
                raise ValueError('Resposta não é GeoTIFF: '+content_type)
            if reported and int(reported)>5_000_000_000:
                raise ValueError('GeoTIFF supera limite de download de 5 GB')
            with open(temporary,'wb') as out:
                copied=0
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    copied+=len(chunk)
                    if copied>5_000_000_000:
                        raise ValueError('Download excedeu limite de 5 GB')
                    out.write(chunk)
        if temporary.stat().st_size==0:
            raise ValueError('Arquivo MapBiomas vazio')
        if reported and copied != int(reported):
            raise ValueError(f'Download MapBiomas truncado: {copied} de {reported} bytes')
        with rasterio.open(temporary) as check:
            if not (check.crs and check.count>=1 and check.width>0 and check.height>0):
                raise ValueError('GeoTIFF MapBiomas sem metadados válidos')
        os.replace(temporary,destination)
        return destination
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _annotate_second_crop(primary, secondary):
    """Attach complementary second-season labels without double-counting AOI area."""
    import geopandas as gpd
    from mapbiomas_zonal import YEAR
    from shapely.ops import unary_union
    if primary is None or primary.empty or secondary is None or secondary.empty:
        return primary
    secondary = secondary.to_crs(primary.crs)
    crop_codes = {1: "milho", 62: "algodão", 41: "outras culturas"}
    agricultural_primary = {18, 19, 20, 21, 39, 40, 41, 46, 47, 48, 62}
    output = []
    for row in primary.itertuples(index=False):
        item = row._asdict()
        code = item.get("class_code")
        try:
            code = int(code)
        except (TypeError, ValueError):
            code = -1
        geom = item["geometry"]
        matches = secondary[secondary.geometry.intersects(geom)]
        if code not in agricultural_primary or matches.empty:
            output.append(item)
            continue
        overlaps = []
        for second in matches.itertuples(index=False):
            second_item = second._asdict()
            second_code = int(second_item.get("class_code", -1))
            label = crop_codes.get(second_code)
            if not label:
                continue
            intersection = _robust_polygon_overlay(geom, second_item["geometry"], "intersection")
            if not intersection.is_empty and intersection.area > 0:
                overlaps.append((intersection, label))
        if not overlaps:
            output.append(item)
            continue
        union = unary_union([g for g, _ in overlaps])
        remainder = _robust_polygon_overlay(geom, union, "difference")
        if not remainder.is_empty and remainder.area > 0:
            base = dict(item); base["geometry"] = remainder
            output.append(base)
        for intersection, label in overlaps:
            annotated = dict(item)
            annotated["geometry"] = intersection
            annotated["secondary_crop"] = label
            annotated["taxonomy"] = str(annotated.get("taxonomy", "")) + "; MapBiomas C11 2ª safra beta: " + label + " (classe complementar, ano " + str(YEAR) + ")"
            # A seasonal class refines only a generic cultivated-map label.
            # It never overwrites a named first-season crop.
            if annotated.get("class_name") == "Áreas cultivadas" and label in ("milho", "algodão"):
                annotated["class_name"] = "Lavoura de " + label
            output.append(annotated)
    return gpd.GeoDataFrame(output, geometry="geometry", crs=primary.crs)


def run_land_use(aoi, output_dir, config_path=None, mapbiomas_path=None, ibge=None, ibge_field='legenda_1', second_crop_path=None, sar_paths=None):
    import geopandas as gpd
    layers, warnings = [], []
    validation = None
    active_sar_config = None
    candidates = [str(config_path)] if config_path else []
    if not config_path:
        # Previously the desktop only attempted SAR when the operator chose a
        # JSON contract manually. Installed model identifiers now take priority
        # automatically, but only after running the same class-level holdout.
        from sar_model_discovery import discover_installed_sar_configs
        candidates, discovery = discover_installed_sar_configs(aoi)
        warnings.extend(discovery)
    for candidate in candidates:
        try:
            predicted, candidate_validation = classify_config(aoi,candidate,output_dir)
            # A literature citation, invalid SAR structure or a class without
            # measurable reference accuracy cannot override the coverage map.
            metadata=candidate_validation.get('class_metadata',{})
            keep=predicted.class_name.map(
                lambda n: metadata.get(n,{}).get('parent')!='vegetação natural'
                or native_formation(n) is not None)
            predicted=predicted[keep & ~predicted.class_name.eq('Grupo: vegetação natural')]
            if predicted.empty:
                warnings.append('Identificador SAR sem classes elegíveis nesta AOI: '+str(candidate))
                continue
            validation=candidate_validation
            active_sar_config=str(candidate)
            layers.append(predicted)
            warnings.append('Identificador SAR REAL executado e validado com referências independentes: '
                            +str(candidate)+'; consultar validacao_sar.json para métricas e limites.')
            break
        except Exception as exc:
            warnings.append('Identificador SAR recusado ['+str(candidate)+']: '
                            +type(exc).__name__+': '+str(exc)[:250])
    if not layers:
        from international_crop_model_sources import installation_diagnostic
        international = installation_diagnostic()
        warnings.append('Nenhum identificador SAR operacional nesta AOI. '
                        'MapBiomas é referência ANUAL HISTÓRICA; NÃO comprova uso atual. '
                        'IBGE somente denomina fitofisionomias; sem inferência SAR '
                        'validada, a cultura atual permanece N/D.')
        warnings.append('Rota global prioritária: ESA WorldCereal (S1+S2; '
                        'openEO/CDSE, modelos por cultura/estação). '
                        'Base treinável: WorldCereal RDM e Radiant MLHub. '
                        'Instalação/modelo/calibração brasileiros ainda NÃO comprovados. '
                        'Ver international_crop_model_sources.py; head WorldCereal local: '+
                        ('presente' if international['worldcereal_custom_head_file_present'] else 'ausente')+'.')
    from native_carbon import native_class
    raw_layers=list(layers)
    # MapBiomas is deliberately not queried in the current-classification path.
    # It cannot define current crop/native masks, areas, training labels, or vigor.
    mb=None
    mapbiomas_source=None
    mapbiomas_failure='DESATIVADO: MapBiomas não participa da classificação atual'
    mapbiomas_access_attempts=[]
    mapbiomas_reference=[]
    second_crop=None
    second_crop_status='disabled_mapbiomas_not_used'
    second_crop_source=None
    second_crop_detection=[]
    reference=None
    if ibge is not None and not ibge.empty:
        if ibge_field not in ibge.columns:
            raise ValueError('Campo IBGE ausente.')
        reference=ibge[[ibge_field,'geometry']].dropna(subset=[ibge_field]).rename(
            columns={ibge_field:'class_name'}).copy()
        reference['source'],reference['taxonomy']='IBGE','IBGE legenda_1'
        # Keep IBGE out of current-cover area layers; it names compatible
        # SAR-confirmed native polygons only.
        raw_layers.append(reference)
    else:
        warnings.append('IBGE sem polígonos disponíveis; não há detalhamento fitofisionômico oficial.')
    lemplus_audit=None
    if not layers:
        # Owner decision 8A: always attempt a SAR semantic classifier. The
        # LEM+ model (INPE field labels, CC BY 4.0) is used ONLY inside its
        # validated domain (savanna/Cerrado phytoregion); elsewhere its output
        # stays a diagnostic and the AOI keeps radar units / N/D.
        try:
            from sar_landcover_lemplus import classify_aoi, in_validated_domain
            domain_ok,domain_msg=in_validated_domain(ibge,ibge_field,aoi)
            res=classify_aoi(aoi)
            lemplus_audit={k:v for k,v in res.items() if k!='polygons_6933'}
            lemplus_audit['domain']=domain_msg
            polys=res.get('polygons_6933')
            if domain_ok and res.get('status')=='SAR_CLASSIFICADOR_EXPERIMENTAL' and polys is not None and not polys.empty:
                lay=polys.copy()
                rename={'Vegetação nativa (assinatura SAR)':'Formação savânica',
                        'Floresta nativa (assinatura SAR)':'Formação florestal'}
                lay['class_name']=lay['class_name'].replace(rename)
                # The model was spatially evaluated in its training geography.
                # It is NOT independently field-verified on this property.
                # Explicitly distinguish it from locally validated SAR.
                provisional=any(x in domain_msg for x in
                    ('DOMINIO_GEOGRAFICO_PROVISORIO','EXTRAPOLACAO_NACIONAL_EXPERIMENTAL'))
                model_source='SAR_EXPERIMENTAL_MODELO' if provisional else 'SAR_VALIDADO'
                lay['source']=model_source
                lay['taxonomy']='SAR RF experimental, ano agrícola '+str(res.get('season'))
                layers.append(lay[['class_name','source','taxonomy','geometry']])
                class_metadata={
                    'Formação savânica':{'parent':'vegetação natural'},
                    'Formação florestal':{'parent':'vegetação natural'}}
                for item in res.get('classes') or []:
                    cls=rename.get(item['class_name'],item['class_name'])
                    native=item.get('native_status')
                    parent=('vegetação natural' if native is True else
                            'uso não nativo' if native is False else None)
                    class_metadata[cls]={'parent':parent,
                         'mean_probability':item.get('mean_probability'),
                         'precision_wilson95_training':item.get('class_precision_wilson95'),
                         'source':'modelo SAR treinado fora da AOI; validação local pendente'}
                validation={'class_metadata':class_metadata,'gates':{},
                    'model_id':res.get('model_id'),
                    'validation_scope':'blocos espaciais 0,1°: treino LEM+ BA, INPE MT e RO',
                    'local_validation_status':'NAO_REALIZADA',
                    'experimental':True,
                    'observed_season':res.get('season'),
                    'scene_count':res.get('scenes_used'),
                    'observed_months':res.get('observed_months'),
                    'model_sha256':res.get('model_sha256'),
                    'geographic_domain_status':domain_msg}
                active_sar_config='sar_landcover_lemplus:'+str(res.get('model_id'))
                warnings.append('Máscaras e áreas de modelo SAR EXPERIMENTAL para safra '+
                    str(res.get('season'))+'; NÃO representam confirmação de campo nem cobertura do mês atual. '+
                    domain_msg)
            else:
                warnings.append('Classificador SAR LEM+ não aplicado: '+domain_msg+'; status '+str(res.get('status')))
        except Exception as exc:
            lemplus_audit={'status':'ERRO_TECNICO','reason':type(exc).__name__+': '+str(exc)[:200]}
            warnings.append('Classificador SAR LEM+ indisponível: '+lemplus_audit['reason'])
    if layers:
        # Use IBGE only to NAME SAR-confirmed native polygons.
        # Proximity is explicit and bounded to 3 km in a metric projection.
        layers[0]=name_native_from_ibge(layers[0],reference,max_proximity_m=3000)
    # IBGE legend is not evidence of current native cover and never fills gaps.
    # A gap remains explicitly unclassified unless a current SAR product covers it.
    source_distributions=[]
    for layer in raw_layers:
        if layer is not None and not layer.empty:
            _,source_audit=partition_land_use(aoi,[layer])
            source_audit['diagnostic_only']=True
            source_audit['diagnostic_role']='Distribuição bruta da fonte; não integra nem substitui as classes finais de cobertura atual.'
            source_distributions.append(source_audit)
    outdir=Path(output_dir);outdir.mkdir(parents=True,exist_ok=True)
    # Current orbital SAR pixels are the only fallback mapping units. If no
    # validated semantic classifier exists, retain the SAR signatures as
    # explicitly unclassified experimental units; never assign them to crops
    # or native vegetation from thresholds or an annual map.
    recent_sar_cover=None
    try:
        from recent_sar_landcover import run_recent_sar_screen
        recent_sar_cover=run_recent_sar_screen(aoi,outdir)
    except Exception as exc:
        recent_sar_cover={'status':'ERRO_TECNICO',
                          'reason':type(exc).__name__+': '+str(exc)[:200]}
    if not any(str(row.get('source','')).startswith('SAR_VALIDADO') for layer in layers
               for _,row in layer.iterrows()):
        vector_path=(recent_sar_cover or {}).get('vector_path')
        if vector_path and Path(vector_path).is_file():
            try:
                radar_units=gpd.read_file(vector_path)
                if not radar_units.empty and radar_units.crs and 'class_code' in radar_units:
                    from recent_sar_landcover import candidate_class_name
                    radar_units['class_name']=radar_units['class_code'].map(candidate_class_name)
                    radar_units['source']='SAR_CURRENT_EXPERIMENTAL'
                    radar_units['taxonomy']=radar_units['class_code'].map(
                        {1:'retroespalhamento estável; interpretação semântica N/D',
                         2:'variação sazonal VV/VH; candidato a área cultivada, cultura N/D; não calibrado',
                         3:'assinatura ambígua; interpretação semântica N/D'}).fillna(
                             'assinatura SAR; interpretação semântica N/D')
                    units=radar_units[['class_name','source','taxonomy','geometry']]
                    layers.append(units)
                    raw_layers.append(units.copy())
            except Exception as exc:
                warnings.append('Pixels SAR lidos, mas unidades experimentais não puderam ser vetorizadas: '+
                                type(exc).__name__+': '+str(exc)[:180])
    alternative_radar_screen={'status':'NOT_NEEDED_SENTINEL1_PIXELS_AVAILABLE',
                              'classification_status':'N/D_VALIDACAO'}
    if recent_sar_cover.get('status')!='SAR_REAL_EXPERIMENTAL_CANDIDATES':
        try:
            from radar_contingency import run_alternative_radar_screen
            alternative_radar_screen=run_alternative_radar_screen(aoi,outdir)
        except Exception as exc:
            alternative_radar_screen={'status':'ERRO_TECNICO',
                                      'reason':type(exc).__name__+': '+str(exc)[:200],
                                      'classification_status':'N/D_VALIDACAO'}
    polygons, summary = partition_land_use(aoi,layers)
    summary['original_source_distributions']=source_distributions
    summary['mapbiomas_failure']=mapbiomas_failure
    summary['mapbiomas_historical_reference']=mapbiomas_reference
    summary['sar_classifier_lemplus']=lemplus_audit
    summary['second_crop_detection']=second_crop_detection
    summary['second_crop_source']=second_crop_source
    summary['second_crop_status']=second_crop_status
    summary['mapbiomas_access_attempts']=mapbiomas_access_attempts
    summary['cover_verification']='COBERTURA_ATUAL_PARCIAL_OU_INDISPONIVEL' if mapbiomas_failure else 'FONTES_PROCESSADAS'
    summary['unknown_cover_ha']=sum(float(r['area_ha']) for r in summary['classes'] if r.get('native_status') is None) if all('native_status' in r for r in summary['classes']) else None
    summary['priority']=('Classificador semântico SAR validado é prioritário; na ausência, unidades de assinatura SAR atual ficam sem classe semântica N/D. '
                         'MapBiomas desativado na classificação atual; IBGE legenda_1 apenas nomeia fitofisionomia após presença nativa SAR confirmada.')
    def _layer_sources(layer):
        if isinstance(layer, dict):
            return [str(layer.get("source") or "")]
        if hasattr(layer, "columns") and "source" in layer.columns:
            return [str(v) for v in layer["source"].dropna().unique()]
        return []
    has_validated_sar = any(source.startswith("SAR_VALIDADO")
                            for layer in layers for source in _layer_sources(layer))
    has_experimental_sar = any(source.startswith("SAR_EXPERIMENTAL_MODELO")
                            for layer in layers for source in _layer_sources(layer))
    summary['current_sar_crop_identification'] = (
        'CLASSIFICACAO_SAR_VALIDADA' if has_validated_sar else
        'CLASSIFICACAO_SAR_EXPERIMENTAL_SEM_VALIDACAO_LOCAL' if has_experimental_sar else
        'N/D_SEM_MODELO_EXECUTAVEL_VALIDADO')
    summary['worldwide_candidate_sources'] = (
        ['ESA WorldCereal/Presto', 'agroimpacts LSTM/CNN',
         'WorldCereal RDM', 'Radiant MLHub', 'EuroCropsML optico']
        if not (has_validated_sar or has_experimental_sar) else [])
    metadata=(validation or {}).get('class_metadata',{})
    polygons['native_status']=[native_class(r.class_name,r.source,metadata) for r in polygons.itertuples()]
    for row in summary['classes']:
        row['native_status']=native_class(row['class_name'],row['source'],metadata)
        row['land_use_group']=("Vegetação nativa" if row['native_status'] is True else
                               "Uso agropecuário/cultivado" if row['native_status'] is False else
                               "Não classificado")
    polygons['land_use_group'] = polygons['native_status'].map(
        lambda value: "Vegetação nativa" if value is True else
                      "Uso agropecuário/cultivado" if value is False else "Não classificado")
    native_rows=[row for row in summary['classes'] if row['native_status'] is True]
    native_area=sum(float(row['area_ha']) for row in native_rows)
    sar_native_rows=[row for row in native_rows
                     if str(row.get('source') or '').startswith(('SAR_VALIDADO','SAR_EXPERIMENTAL_MODELO'))]
    sar_native_area=sum(float(row['area_ha']) for row in sar_native_rows)
    summary['native_occurrence']={
        "status":("model_experimental_not_field_validated" if has_experimental_sar else "detected_by_validated_SAR") if sar_native_area>0 else "N/D_NOT_VERIFIABLE_WITHOUT_VALIDATED_SAR",
        "label":"Vegetação nativa — máscara SAR experimental, não validada em campo" if has_experimental_sar else "Vegetação nativa — máscara SAR do classificador",
        "area_ha":sar_native_area if sar_native_area>0 else None,
        "area_pct_aoi":(100.0*sar_native_area/summary['area_aoi_ha'] if sar_native_area>0 and summary['area_aoi_ha'] else None),
        "source":"modelo SAR experimental com avaliação fora da AOI" if has_experimental_sar else "classificador SAR com validação independente" if sar_native_area>0 else "N/D — MapBiomas é somente referência anual e IBGE somente nomeia fitofisionomia por proximidade",
        "field_confirmed":False,
        "native_class_breakdown":[{"class_name":row["class_name"],"area_ha":row["area_ha"],"source":row["source"]} for row in sar_native_rows],
        "diversified_property_with_native_and_other_use":bool(sar_native_area>0 and any(row['native_status'] is False for row in summary['classes']))
    }
    summary['unknown_cover_ha']=sum(float(r['area_ha']) for r in summary['classes'] if r['native_status'] is None)
    outdir=Path(output_dir);outdir.mkdir(parents=True,exist_ok=True)
    # Experimental overlay is separate from categorical cover totals: it ranks
    # current S1 structure candidates for field inspection and never relabels
    # MapBiomas/IBGE classes as confirmed native cover.
    try:
        from native_sar_experimental import run_sentinel1_native_screen
        summary['native_sar_experimental']=run_sentinel1_native_screen(
            aoi,sar_paths,outdir,ibge=ibge,ibge_field=ibge_field)
    except Exception as exc:
        summary['native_sar_experimental']={
            'status':'ERROR','reason':type(exc).__name__+': '+str(exc)[:400],
            'native_presence_confirmed':False,'probability':None,'accuracy':None}
    # Current Sentinel-1 time-series candidates are produced separately from
    # accepted land-cover totals and from annual MapBiomas reference polygons.
    summary['recent_sar_cover']=recent_sar_cover or {'status':'N/D','reason':'triagem SAR não executada'}
    summary['alternative_radar_screen']=alternative_radar_screen
    # National audit: reconcile area, provenance and unknown uncertainty.
    from national_analysis_audit import audit_national_coverage
    summary['national_audit']=audit_national_coverage(aoi,summary)
    vector_path=outdir/'uso_solo_intersecao.geojson'
    polygons.to_file(vector_path,driver='GeoJSON')
    summary.update({'warnings':warnings,'validation':validation,'vector_path':str(vector_path),
                    'mapbiomas_source':None,
                    'sar_model_config':active_sar_config,
                    'sar_selection':'EXPLICIT_OPERATOR' if active_sar_config and config_path else
                                    ('INSTALLED_AUTO_DISCOVERED' if active_sar_config else 'NO_EXECUTABLE_SAR_CLASSIFIER'),
                    'status':('SAR_ELEGIVEL' if any(str(r.get('source','')).startswith('SAR_VALIDADO') for r in summary['classes']) else
                              'SAR_MODELO_EXPERIMENTAL' if has_experimental_sar else
                              'SAR_UNIDADES_EXPERIMENTAIS' if any(r.get('source')=='SAR_CURRENT_EXPERIMENTAL' for r in summary['classes']) else
                              'N/D_SEM_COBERTURA_SAR')})
    (outdir/'uso_solo_auditoria.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def report_lines(summary, fmt=lambda v:f'{v:.2f}'):
    lines=['USO E COBERTURA — CLASSIFICAÇÃO SAR E INTERSEÇÃO ESPACIAL', summary['priority'], summary['method']]
    for row in summary['classes']:
        lines.append(f"  {row['class_name']}: {fmt(row['area_ha'])} ha ({fmt(row['area_pct'])}%) — {row['source']} / {row['taxonomy']}")
    lines.append('Identificador SAR utilizado: '+str(summary.get('sar_model_config') or 'NENHUM; classes semânticas atuais N/D.'))
    lines.append('Seleção SAR: '+str(summary.get('sar_selection') or 'não especificada'))
    exp=summary.get('native_sar_experimental') or {}
    if exp.get('status')=='SAR_EXPERIMENTAL_CANDIDATE_SCREEN':
        sensitivity=exp.get('threshold_sensitivity_area_ha') or {}
        lines.append('TRIAGEM EXPERIMENTAL SAR DE VEGETAÇÃO NATIVA — candidatos para vistoria, não confirmação nem probabilidade.')
        for threshold,row in sensitivity.items():
            lines.append(f"  Limiar de índice {threshold}: {fmt(row.get('area_ha'))} ha; n de manchas={row.get('patch_count')}.")
        lines.append('  Sensibilidade a limiares: '+str(exp.get('sensitivity_is')))
        lines.append('  Raster de pontuação: '+str(exp.get('score_raster_path')))
        lines.append('  Polígonos candidatos: '+str(exp.get('candidate_vector_path')))
        lines.append('  Nomes IBGE: '+str(exp.get('ibge_naming')))
    elif exp.get('status') not in (None,'N/D'):
        lines.append('Triagem SAR experimental indisponível: '+str(exp.get('reason') or exp.get('status')))
    elif exp.get('status')=='N/D':
        lines.append('Triagem SAR experimental indisponível: '+str(exp.get('reason')))
    national=summary.get('national_audit') or {}
    if national:
        lines.append('AUDITORIA NACIONAL — AOI '+fmt(national['aoi_area_ha'])+
                     ' ha, EPSG:6933; SHA256 geom. '+national['aoi_sha256_wgs84'])
        lines.append('  Fechamento: '+fmt(national['area_closure_error_ha'])+
                     ' ha; incerteza de classificação local: N/D sem validação.')
        lines.append('  '+national['uncertainty_policy'])
    orbital=summary.get('recent_sar_cover') or {}
    lines.append('SAR ATUAL ORBITAL (MapBiomas não participa da classificação): '+str(orbital.get('status','N/D')))
    if orbital.get('status')=='SAR_REAL_EXPERIMENTAL_CANDIDATES':
        lines.append('  Cenas reais VV/VH: '+str(orbital.get('scene_count'))+'; mais recente UTC: '+str(orbital.get('latest_acquisition_utc')))
        for n,a in (orbital.get('areas_ha') or {}).items():
            lines.append('  '+n+': '+fmt(a)+' ha — candidato não validado')
        lines.append('  GeoTIFF SAR: '+str(orbital.get('raster_path')))
        lines.append('  GeoJSON SAR: '+str(orbital.get('vector_path')))
        lines.append('  NÃO confirmar vegetação nativa nem lavouras a partir de limiares heurísticos.')
    else:
        lines.append('  Não houve pixels orbitais suficientes: '+str(orbital.get('reason','N/D')))
    # Operators need actionable evidence in the plain-text report: a generic
    # SELECTED_SCENES_PIXEL_READ_FAILED hid provider-specific causes at Sinop.
    for provider in (orbital.get('provider_processing_diagnostics') or []):
        lines.append('  DIAGNÓSTICO VV/VH '+str(provider.get('provider','N/D'))+
                     ': candidatas='+str(provider.get('candidate_scene_count',0))+
                     '; série elegível='+str(bool(provider.get('eligible_series_found',False)))+
                     '; selecionadas='+str(provider.get('selected_scene_count',0))+
                     '; leituras tentadas='+str(provider.get('pixel_read_attempt_count',0))+
                     '; cenas legíveis='+str(provider.get('readable_scene_count',0))+
                     '; falhas='+str(provider.get('failed_scene_count',0)))
    for error in (orbital.get('failed_scene_reads') or [])[:6]:
        lines.append('  FALHA SAR '+str(error.get('provider','N/D'))+
                     ' / '+str(error.get('scene_id','N/D'))[:65]+
                     ': '+str(error.get('error_type','N/D'))+
                     ' — '+str(error.get('error','N/D'))[:150])
    if orbital.get('committed_grid_shape'):
        lines.append('  Grade SAR efetivamente lida (linhas, colunas): '+
                     str(orbital['committed_grid_shape'])+
                     '; CRS: '+str(orbital.get('committed_grid_crs','N/D')))
    alt=summary.get('alternative_radar_screen') or {}
    lines.append('CONTINGÊNCIA RADAR L/X/NISAR — '+str(alt.get('status','N/D'))+'; identificação semântica permanece N/D até validação específica.')
    if alt.get('reason'):lines.append('  '+str(alt.get('reason'))[:220])
    validation=summary.get('validation') or {}
    for level,report in [('classe',validation),('grupo',validation.get('parent_validation',{}))]:
        for label,gate in report.get('gates',{}).items():
            precision=gate['precision']
            text=(fmt(100*precision)+'%' if precision is not None else 'não estimável')
            lines.append(f"  Validação {level} {label}: precisão {text}; IC95% [{fmt(100*gate['precision_wilson95_lower'])}%, {fmt(100*gate['precision_wilson95_upper'])}%]; n independente={gate['n_independent']}; mensurável={gate['eligible']}; amostra pequena={gate.get('sample_size_warning',False)}")
    if validation:
        lines.append('Sem acurácia mínima: qualquer desempenho mensurável é informado com n, precisão por classe e IC95% Wilson; priorizar modelos de melhor desempenho compatível, sem ocultar modelos de baixa acurácia. Probabilidade calibrada não é garantia individual por pixel.')
    lines.extend(summary.get('warnings',[]))
    lines += [summary['area_uncertainty'], 'Polígonos: '+summary['vector_path']]
    return lines


if __name__ == '__main__':
    import argparse
    import geopandas as gpd
    parser=argparse.ArgumentParser()
    parser.add_argument('--aoi',required=True);parser.add_argument('--config');parser.add_argument('--mapbiomas')
    parser.add_argument('--ibge');parser.add_argument('--ibge-field',default='legenda_1');parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=run_land_use(gpd.read_file(args.aoi),args.output,args.config,args.mapbiomas,
                        gpd.read_file(args.ibge) if args.ibge else None,args.ibge_field)
    print('\n'.join(report_lines(result)))
