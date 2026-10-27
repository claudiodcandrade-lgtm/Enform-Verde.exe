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
SCORE_THRESHOLD = 0.90  # calibrated estimate; local validation still mandatory
MIN_VALIDATION = 50
MIN_PRECISION_LOWER = 0.90
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
        chosen = (predictions == label) & (scores >= SCORE_THRESHOLD)
        n = int(chosen.sum())
        correct = int(((truth == label) & chosen).sum())
        lower = wilson_lower(correct, n)
        upper = 1.0 - wilson_lower(n-correct,n) if n else 1.0
        gates[label] = {'n_independent': n, 'correct': correct, 'precision': correct/n if n else None,
                        'precision_wilson95_lower': lower, 'precision_wilson95_upper': upper,
                        'eligible': n >= MIN_VALIDATION and lower >= MIN_PRECISION_LOWER}
    return {'labels': labels, 'confusion_matrix': confusion_matrix(truth, predictions, labels=labels).tolist(),
            'metrics': metrics, 'gates': gates, 'score_threshold': SCORE_THRESHOLD,
            'min_validation': MIN_VALIDATION, 'min_precision_lower': MIN_PRECISION_LOWER,
            'uncertainty': 'IC95% Wilson da precisão da classe aceita, condicionado à independência/representatividade dos pontos; não é erro de área nem garantia individual por pixel.'}


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
        # Conflicting labels within one source are gaps, not first-row wins.
        conflicts = []
        for pos, row in enumerate(projected.itertuples()):
            for j in projected.sindex.query(row.geometry, predicate='intersects'):
                if j <= pos:
                    continue
                other = projected.iloc[int(j)]
                if row.class_name != other.class_name:
                    overlap = row.geometry.intersection(other.geometry)
                    if overlap.area > 0:
                        conflicts.append(overlap)
        from shapely.ops import unary_union
        conflict = unary_union(conflicts)
        for row in projected.itertuples():
            clipped = remaining.intersection(row.geometry).difference(conflict)
            if clipped.is_empty or clipped.area <= 0:
                continue
            pieces.append({'class_name': row.class_name, 'source': row.source,
                           'taxonomy': row.taxonomy, 'geometry': clipped})
            remaining = remaining.difference(clipped)
    if remaining.area > 1e-6:
        pieces.append({'class_name': 'Não classificado', 'source': 'SEM_COBERTURA',
                       'taxonomy': 'sem classificação', 'geometry': remaining})
    out = gpd.GeoDataFrame(pieces, crs=AREA_CRS)
    out = out.dissolve(by=['class_name', 'source', 'taxonomy'], as_index=False)
    out['area_ha'] = out.geometry.area / 10000
    out['area_pct'] = 100 * out.geometry.area / geom.area
    records = out.drop(columns='geometry').to_dict('records')
    if abs(sum(r['area_ha'] for r in records) - geom.area/10000) > max(1e-6, geom.area/10000*1e-8):
        raise ValueError('Falha no fechamento das áreas de classificação.')
    return out.to_crs('EPSG:4326'), {
        'classes': records, 'area_aoi_ha': geom.area/10000,
        'method': 'interseção exata AOI × polígonos das células; área em EPSG:6933; denominador: AOI inteira',
        'priority': 'SAR com validação elegível > IBGE > MapBiomas > não classificado',
        'area_uncertainty': 'Área cartográfica; sem correção amostral de área e sem IC de área.',
    }


def raster_class_polygons(aoi, raster_path, legend=None):
    """Polygonize only AOI window, retaining edge-cell footprints for clipping."""
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.mask import mask
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
            if geometry_window(src,[mapping(inside)]).width * geometry_window(src,[mapping(inside)]).height > 4_000_000:
                raise ValueError('Janela de classes excede 4 milhões de células; subdivida a AOI.')
            arr, transform = mask(src, [mapping(inside)], crop=True, all_touched=True, filled=False)
            if arr[0].size > 4_000_000:
                raise ValueError('Janela de classes excede 4 milhões de células; subdivida a AOI.')
            valid = ~np.ma.getmaskarray(arr[0]) & np.isfinite(arr[0].data) & (arr[0].data > 0)
            rows = []
            for geometry, code in shapes(arr[0].data.astype('int32'), mask=valid, transform=transform):
                code = int(code)
                name = legend[code] if legend is not None else LEGEND.get(code, (f'Classe MapBiomas {code}', ''))[0]
                rows.append({'class_code': code, 'class_name': name,
                             'source': 'SAR_VALIDADO' if legend is not None else 'MAPBIOMAS',
                             'taxonomy': 'legenda do modelo SAR' if legend is not None else 'MapBiomas',
                             'geometry': shape(geometry)})
            return gpd.GeoDataFrame(rows, columns=['class_code','class_name','source','taxonomy','geometry'], crs=src.crs)


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
            return bool((model.classes_[bp.argmax(axis=1)]==label).all() and (bp.max(axis=1)>=SCORE_THRESHOLD).all())
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
                if native_ok and report['gates'][label]['eligible'] and prob[j].max() >= SCORE_THRESHOLD:
                    output[idx] = codes[label]
                    confidence_grid[idx] = prob[j].max()
                else:
                    parent = parent_names[parent_prob[j].argmax()]
                    if parent!='vegetação natural' and parent_report['gates'][parent]['eligible'] and parent_prob[j].max() >= SCORE_THRESHOLD:
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


def name_native_from_ibge(predicted, reference):
    """IBGE names compatible native structure; no distance in user outputs."""
    import geopandas as gpd
    pieces=[]
    ref=reference.to_crs(AREA_CRS) if reference is not None else None
    for row in predicted.to_crs(AREA_CRS).itertuples():
        formation=native_formation(row.class_name)
        if not formation or ref is None:
            pieces.append(dict(class_name=row.class_name,source=row.source,taxonomy=row.taxonomy,geometry=row.geometry));continue
        compatible=ref[ref.class_name.map(ibge_formation)==formation]
        remaining=row.geometry
        # Keep distinct local IBGE names where the recognized patch intersects them.
        for item in compatible.itertuples():
            clipped=remaining.intersection(item.geometry)
            if clipped.area>0:
                pieces.append(dict(class_name=item.class_name,source='SAR_VALIDADO+IBGE',taxonomy='Formação SAR: '+formation+'; nome: IBGE legenda_1',geometry=clipped))
                remaining=remaining.difference(clipped)
        if remaining.area>0:
            if not compatible.empty:
                distances=compatible.geometry.distance(remaining)
                nearest=compatible.loc[distances.idxmin()]
                name,source=nearest.class_name,'SAR_VALIDADO+IBGE'
                taxonomy='Formação SAR: '+formation+'; nome: IBGE legenda_1'
            else:
                name,source,taxonomy=row.class_name,row.source,'Formação SAR ampla; nome IBGE compatível indisponível'
            pieces.append(dict(class_name=name,source=source,taxonomy=taxonomy,geometry=remaining))
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


def run_land_use(aoi, output_dir, config_path=None, mapbiomas_path=None, ibge=None, ibge_field='legenda_1'):
    import geopandas as gpd
    from mapbiomas_zonal import RASTER_URL, YEAR
    layers, warnings = [], []
    validation = None
    if config_path:
        try:
            predicted, validation = classify_config(aoi,config_path,output_dir)
            # Native detailed labels never override the maps directly.
            metadata=validation.get('class_metadata',{})
            keep=predicted.class_name.map(lambda n: metadata.get(n,{}).get('parent')!='vegetação natural' or native_formation(n) is not None)
            predicted=predicted[keep & ~predicted.class_name.eq('Grupo: vegetação natural')]
            layers.append(predicted)
        except Exception as exc:
            warnings.append('SAR sem prioridade: '+str(exc))
    else:
        warnings.append('Sem modelo treinado/validado e atributos compatíveis; nenhum peso nacional vem embutido.')
    from native_carbon import native_class
    raw_layers=list(layers)
    mb=None
    mapbiomas_failure=None
    mapbiomas_access_attempts=[]
    # Avoid treating transient GDAL HTTP failures as missing vegetation.
    # Retry the official current-year source with conservative HTTP options.
    import time
    import rasterio
    source_path=mapbiomas_path or RASTER_URL.format(year=YEAR)
    # Keep the validated remote pathway, and permit an authenticated local
    # GeoTIFF for Windows installations where GDAL /vsicurl/ is unavailable.
    import os
    local_candidate=os.environ.get('ENFORM_MAPBIOMAS_LOCAL_TIF','').strip()
    if not mapbiomas_path and local_candidate:
        if Path(local_candidate).is_file():
            source_path=local_candidate
        else:
            warnings.append('MapBiomas local configurado, mas arquivo inexistente: '+local_candidate)
    # Automatically recover a previously downloaded official MapBiomas GeoTIFF.
    # Never infer native vegetation from the IBGE potential-vegetation map alone.
    if not mapbiomas_path and source_path.startswith('https://'):
        user_root=Path.home()/'.enform_verde'
        known_names=[
            f'brazil_coverage-col11_{YEAR}.tif',
            f'mapbiomas_brazil_collection11_coverage_{YEAR}.tif',
        ]
        search_dirs=[user_root/'mapbiomas',user_root/'cache'/'mapbiomas',
                     user_root/'uso_solo',user_root/'dados'/'mapbiomas']
        for directory in search_dirs:
            for name in known_names:
                candidate=directory/name
                if candidate.is_file() and candidate.stat().st_size>1024:
                    try:
                        with rasterio.open(candidate) as check:
                            if check.count>=1 and check.crs and check.width>0 and check.height>0:
                                source_path=str(candidate)
                                warnings.append('MapBiomas oficial: raster local previamente armazenado selecionado automaticamente: '+str(candidate))
                                break
                    except Exception as exc:
                        warnings.append('Cache MapBiomas inválido ignorado: '+str(candidate)+' ('+str(exc)+')')
            if source_path!=RASTER_URL.format(year=YEAR):
                break
    for attempt in range(3):
        try:
            with rasterio.Env(GDAL_HTTP_MAX_RETRY='2',
                              GDAL_HTTP_RETRY_DELAY='1',
                              GDAL_HTTP_TIMEOUT='45',
                              GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
                              CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
                mb=raster_class_polygons(aoi,source_path)
            mapbiomas_failure=None
            break
        except Exception as exc:
            mapbiomas_failure=f'{type(exc).__name__}: {exc}'
            mapbiomas_access_attempts.append({'attempt':attempt+1,'error':mapbiomas_failure})
            if attempt<2:time.sleep(1+attempt)
    try:
        if mb is None:
            raise RuntimeError('MapBiomas C11 inacessível após tentativas: '+str(mapbiomas_failure))
        raw_layers.append(mb.copy())
        from mapbiomas_zonal import LEGEND
        crop_names={LEGEND[c][0] for c in (18,19,20,39,40,41,46,47,48,62)}
        # Keep explicit crop-type pixels from the official annual map visible in
        # the executive result, but identify them as MapBiomas map classes—not
        # as independently validated, current-season SAR classifications.
        # Broad/ambiguous crop classes stay at the safe parent label.
        specific={20:'Lavoura de cana-de-açúcar',39:'Lavoura de soja',40:'Lavoura de arroz',
                  46:'Lavoura de café',47:'Lavoura de citros',62:'Lavoura de algodão'}
        if 'class_code' in mb.columns:
            mb['class_code']=mb['class_code'].map(lambda x: int(x) if str(x).strip().lstrip('-').isdigit() else -1)
            for code,label in specific.items():
                mb.loc[mb.class_code.eq(code),'class_name']=label
                mb.loc[mb.class_code.eq(code),'taxonomy']=f"MapBiomas C11, classe {code}; classe cartográfica anual"
            broad=mb.class_code.isin([18,19,41,48])
            mb.loc[broad,'class_name']='Áreas cultivadas'
        else:
            # Compatibility path for externally supplied/mock class polygons
            # without their original class code: preserve the former safe rollup.
            mb.loc[mb.class_name.isin(crop_names),'class_name']='Áreas cultivadas'
    except Exception as exc:
        mapbiomas_failure=str(exc)
        warnings.append('MapBiomas indisponível: '+mapbiomas_failure)
        warnings.append('Cobertura atual não verificada por falha das fontes; IBGE indica fitofisionomia potencial, não confirma cobertura presente.')
    reference=None
    if ibge is not None and not ibge.empty:
        if ibge_field not in ibge.columns:raise ValueError('Campo IBGE ausente.')
        reference=ibge[[ibge_field,'geometry']].dropna(subset=[ibge_field]).rename(columns={ibge_field:'class_name'}).copy()
        reference['source'],reference['taxonomy']='IBGE','IBGE legenda_1'
        raw_layers.append(reference)
    else:warnings.append('IBGE sem polígonos disponíveis; não há detalhamento fitofisionômico oficial.')
    if layers:
        layers[0]=name_native_from_ibge(layers[0],reference)
    # IBGE legenda_1 describes phytoregions, not proof of current native cover.
    # Below accepted SAR, MapBiomas masks current anthropic/native cover, and
    # IBGE supplies the detailed physiognomy within its native intersections.
    if mb is not None and not mb.empty:
        native=mb.class_name.map(lambda name:native_class(name,'MAPBIOMAS') is True)
        layers.append(mb[~native])
        if reference is not None and native.any():
            mask=mb[native].to_crs(reference.crs).geometry.union_all()
            detail=reference.copy()
            detail['geometry']=detail.geometry.make_valid().intersection(mask)
            detail=detail[~detail.geometry.is_empty]
            detail['source']='IBGE+MAPBIOMAS'
            detail['taxonomy']='IBGE legenda_1 em cobertura nativa MapBiomas'
            layers.append(detail)
        layers.append(mb[native])
    if reference is not None:layers.append(reference)
    source_distributions=[]
    for layer in raw_layers:
        if layer is not None and not layer.empty:
            _,source_audit=partition_land_use(aoi,[layer])
            source_distributions.append(source_audit)
    polygons, summary = partition_land_use(aoi,layers)
    summary['original_source_distributions']=source_distributions
    summary['mapbiomas_failure']=mapbiomas_failure
    summary['mapbiomas_access_attempts']=mapbiomas_access_attempts
    summary['cover_verification']='COBERTURA_ATUAL_PARCIAL_OU_INDISPONIVEL' if mapbiomas_failure else 'FONTES_PROCESSADAS'
    summary['unknown_cover_ha']=sum(float(r['area_ha']) for r in summary['classes'] if r.get('native_status') is None) if all('native_status' in r for r in summary['classes']) else None
    summary['priority']='SAR com confiança demonstrada; nas lacunas, IBGE para fitofisionomia e MapBiomas para uso/cobertura atual'
    metadata=(validation or {}).get('class_metadata',{})
    polygons['native_status']=[native_class(r.class_name,r.source,metadata) for r in polygons.itertuples()]
    for row in summary['classes']:row['native_status']=native_class(row['class_name'],row['source'],metadata)
    summary['unknown_cover_ha']=sum(float(r['area_ha']) for r in summary['classes'] if r['native_status'] is None)
    outdir=Path(output_dir);outdir.mkdir(parents=True,exist_ok=True)
    vector_path=outdir/'uso_solo_intersecao.geojson'
    polygons.to_file(vector_path,driver='GeoJSON')
    summary.update({'warnings':warnings,'validation':validation,'vector_path':str(vector_path),
                    'mapbiomas_source':str(source_path),
                    'status':'SAR_ELEGIVEL' if any(r['source'].startswith('SAR_VALIDADO') for r in summary['classes']) else 'FALLBACK_CARTOGRAFICO'})
    (outdir/'uso_solo_auditoria.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def report_lines(summary, fmt=lambda v:f'{v:.2f}'):
    lines=['USO E COBERTURA — CLASSIFICAÇÃO SAR E INTERSEÇÃO ESPACIAL', summary['priority'], summary['method']]
    for row in summary['classes']:
        lines.append(f"  {row['class_name']}: {fmt(row['area_ha'])} ha ({fmt(row['area_pct'])}%) — {row['source']} / {row['taxonomy']}")
    validation=summary.get('validation') or {}
    for level,report in [('classe',validation),('grupo',validation.get('parent_validation',{}))]:
        for label,gate in report.get('gates',{}).items():
            precision=gate['precision']
            text=(fmt(100*precision)+'%' if precision is not None else 'não estimável')
            lines.append(f"  Validação {level} {label}: precisão {text}; IC95% [{fmt(100*gate['precision_wilson95_lower'])}%, {fmt(100*gate['precision_wilson95_upper'])}%]; n independente={gate['n_independent']}; elegível={gate['eligible']}")
    if validation:
        lines.append('Confiança: probabilidade calibrada + IC da precisão da classe; independência e representatividade condicionam o IC. Não é garantia individual por pixel.')
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
