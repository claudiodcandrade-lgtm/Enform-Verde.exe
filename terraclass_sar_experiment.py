"""Experimental SAR training from official TerraClass map labels.

This module deliberately produces *map-agreement experiments*, not field
validation. It is kept separate from the validated classifier registry and
from land_use_sar's accepted area totals. TerraClass currently supplies the
supported reference domain (Amazonia/Cerrado); predictions outside that domain
must remain N/D until a separate compatible reference/model is available.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path


TERRACLASS_2024_URL = "https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/terraclass-divulga-dados-atualizados-sobre-cobertura-e-uso-da-terra-no-bioma-amazonia"
PRODES_REFERENCE_URL = "https://data.inpe.br/biomasbr/prodes-monitoramento-anual-da-supressao-de-vegetacao-nativa/"
TERRACLASS_SUPPORTED_YEARS = {2024}
TERRACLASS_DOMAINS = {"amazonia", "cerrado"}

# Broad categories only. TerraClass does not provide species-level labels for
# soybean versus maize; never expand these classes into crop identities.
CLASS_ALIASES = {
    "vegetacao natural florestal primaria": "Vegetação nativa",
    "vegetacao natural florestal secundaria": "Vegetação nativa",
    "vegetacao natural primaria": "Vegetação nativa",
    "vegetacao natural secundaria": "Vegetação nativa",
    "nao floresta": "Vegetação nativa",
    "natural nao florestal": "Vegetação nativa",
    "pastagem arbustiva arborea": "Pastagem",
    "pastagem herbacea": "Pastagem",
    "pastagem": "Pastagem",
    "cultura agricola perene": "Agricultura",
    "cultura agricola semiperene": "Agricultura",
    "cultura agricola temporaria de 1 ciclo": "Agricultura",
    "cultura agricola temporaria de mais de 1 ciclo": "Agricultura",
    "cultura agricola temporaria": "Agricultura",
    "silvicultura": "Silvicultura",
    "mineracao": "Outros usos",
    "urbanizada": "Outros usos",
    "outras areas edificadas": "Outros usos",
    "outros usos": "Outros usos",
    "corpo d agua": "Outros usos",
    "nao observado": None,
    "desflorestamento no ano": None,
}


def _normalize_class(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    return value


def terraclass_category(value):
    """Map an official TerraClass legend string to a broad safe category."""
    return CLASS_ALIASES.get(_normalize_class(value))


def _safe_output_path(path):
    target = Path(path).resolve()
    if target.suffix.lower() not in {".joblib", ".json"}:
        raise ValueError("Formato de saída experimental inválido.")
    return target


def _source_digest(path):
    """Hash a single-file vector or all same-stem Shapefile components."""
    source = Path(path)
    files = (sorted(source.parent.glob(source.stem + ".*"))
             if source.suffix.casefold() == ".shp" else [source])
    if not files or any(not p.is_file() for p in files):
        raise ValueError("Arquivo de referência ou componentes espaciais ausentes.")
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.name.encode("utf-8"))
        digest.update(b"\0")
        with item.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _block_bootstrap_intervals(targets, prediction, groups, labels, *, seed=42, iterations=2000):
    """Cluster-bootstrap precision/recall intervals over held-out map blocks."""
    import numpy as np
    unique = np.unique(groups)
    rng = np.random.default_rng(seed)
    report = {}
    for label in labels:
        counts = []
        for group in unique:
            mask = groups == group
            truth = targets[mask]
            pred = prediction[mask]
            tp = int(((truth == label) & (pred == label)).sum())
            fp = int(((truth != label) & (pred == label)).sum())
            fn = int(((truth == label) & (pred != label)).sum())
            counts.append((tp, fp, fn))
        counts = np.asarray(counts, dtype="int64")
        sampled = rng.integers(0, len(unique), size=(iterations, len(unique)))
        sums = counts[sampled].sum(axis=1)
        p_den = sums[:, 0] + sums[:, 1]
        r_den = sums[:, 0] + sums[:, 2]
        precision = np.divide(sums[:, 0], p_den, out=np.full(iterations, np.nan), where=p_den > 0)
        recall = np.divide(sums[:, 0], r_den, out=np.full(iterations, np.nan), where=r_den > 0)
        def bounds(values):
            valid = values[np.isfinite(values)]
            return [float(x) for x in np.quantile(valid, [0.025, 0.975])] if len(valid) else None
        report[str(label)] = {"precision_ci95_block_bootstrap": bounds(precision),
                              "recall_ci95_block_bootstrap": bounds(recall),
                              "bootstrap_blocks": int(len(unique)),
                              "bootstrap_iterations": int(iterations)}
    return report


def train_spatial_map_agreement(
    feature_raster,
    reference_vector,
    output_model,
    output_report,
    *,
    label_field,
    domain,
    reference_year,
    feature_year,
    block_size_m=5000,
    random_state=42,
):
    """Train a broad-class SAR model and report spatially held-out map agreement.

    Inputs are cropped, co-registered SAR feature bands and TerraClass polygons.
    The report's held-out target is the same map product used to create labels;
    it can never be represented as independent field accuracy. This function
    does not alter application inference or release eligibility.
    """
    domain_key = _normalize_class(domain)
    if domain_key not in TERRACLASS_DOMAINS:
        raise ValueError("TerraClass 2024: domínio aceito somente Amazônia ou Cerrado.")
    if reference_year not in TERRACLASS_SUPPORTED_YEARS or feature_year != reference_year:
        raise ValueError("Ano da referência e da série SAR devem coincidir com TerraClass 2024.")
    if not 1000 <= float(block_size_m) <= 50000:
        raise ValueError("Bloco espacial fora da faixa (1–50 km).")

    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.features import rasterize
    from rasterio.transform import xy
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    from sklearn.model_selection import GroupKFold, cross_val_predict
    import joblib

    with rasterio.open(feature_raster) as raster:
        if not raster.crs or raster.count < 2:
            raise ValueError("Raster de atributos requer CRS e pelo menos duas bandas SAR.")
        if not raster.crs.is_projected:
            raise ValueError("Grade SAR deve estar em CRS projetado métrico para blocos espaciais.")
        if raster.width * raster.height * raster.count > 40_000_000:
            raise ValueError("Recorte SAR excede o limite; processe AOIs/tiles menores.")
        raster_metadata = {"crs": raster.crs.to_string(), "width": int(raster.width),
                           "height": int(raster.height), "band_count": int(raster.count),
                           "transform": [float(v) for v in raster.transform]}
        features = raster.read(masked=True)
        values = np.asarray(features.data, dtype=np.float32)
        valid = (~np.ma.getmaskarray(features).any(axis=0)
                 & np.isfinite(values).all(axis=0))
        ref = gpd.read_file(reference_vector)
        if label_field not in ref.columns:
            raise ValueError("Campo de legenda TerraClass ausente.")
        if ref.crs is None:
            raise ValueError("Referência TerraClass sem CRS.")
        ref = ref.to_crs(raster.crs)
        geometries = []
        label_codes = {}
        for row in ref[[label_field, "geometry"]].itertuples(index=False, name=None):
            label = terraclass_category(row[0])
            geom = row[1]
            if label is None or geom is None or geom.is_empty:
                continue
            code = label_codes.setdefault(label, len(label_codes) + 1)
            geometries.append((geom, code))
        if len(label_codes) < 2:
            raise ValueError("TerraClass não contém duas classes elegíveis no recorte.")
        labels = rasterize(geometries, out_shape=(raster.height, raster.width),
                           transform=raster.transform, fill=0, all_touched=False,
                           dtype="uint8")
        rows, cols = np.where(valid & (labels > 0))
        if len(rows) < 100:
            raise ValueError("Menos de 100 pixels SAR co-registrados com rótulos elegíveis.")
        samples = values[:, rows, cols].T
        targets = labels[rows, cols]
        xs, ys = xy(raster.transform, rows, cols, offset="center")
        # Anchor blocks to a fixed projected-coordinate lattice so different
        # AOI tiles cannot shift the split grid and leak neighboring pixels.
        groups = (np.floor(np.asarray(xs) / block_size_m).astype("int64")
                  .astype(str) + ":" +
                  np.floor(np.asarray(ys) / block_size_m).astype("int64").astype(str))

    unique_groups = np.unique(groups)
    if len(unique_groups) < 5:
        raise ValueError("Validação cartográfica requer pelo menos 5 blocos espaciais.")
    model = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                   n_jobs=-1, random_state=random_state,
                                   min_samples_leaf=2)
    folds = min(5, len(unique_groups))
    prediction = cross_val_predict(model, samples, targets,
                                   groups=groups, cv=GroupKFold(n_splits=folds),
                                   n_jobs=1, method="predict")
    model.fit(samples, targets)
    target_names = {value: key for key, value in label_codes.items()}
    labels_ordered = sorted(target_names)
    cm = confusion_matrix(targets, prediction, labels=labels_ordered)
    precision, recall, f1, support = precision_recall_fscore_support(
        targets, prediction, labels=labels_ordered, zero_division=0)
    cluster_intervals = _block_bootstrap_intervals(
        targets, prediction, groups, labels_ordered, seed=random_state)
    report = {
        "status": "EXPERIMENTAL_MAP_AGREEMENT_ONLY",
        "model_role": "training-only experimental SAR classifier; not field validated",
        "priority_policy": "Use only as explicit fallback when no applicable tested/homologated model exists; never supersede one.",
        "domain": domain_key,
        "reference": {"name": "TerraClass", "year": reference_year,
                      "url": TERRACLASS_2024_URL,
                      "local_dataset_sha256": _source_digest(reference_vector),
                      "prodes_context_url": PRODES_REFERENCE_URL,
                      "prodes_used_as_label": False},
        "sar_feature_raster_sha256": _source_digest(feature_raster),
        "sar_feature_grid": raster_metadata,
        "feature_year": feature_year,
        "class_names": [target_names[x] for x in labels_ordered],
        "confusion_matrix_map_reference": cm.tolist(),
        "per_class_map_agreement": {
            target_names[label]: {"precision": float(p), "recall": float(r),
                                  "f1": float(f), "n_pixels": int(n),
                                  **cluster_intervals[str(label)]}
            for label, p, r, f, n in zip(labels_ordered, precision, recall, f1, support)
        },
        "n_pixels": int(len(targets)),
        "n_spatial_blocks": int(len(unique_groups)),
        "cv_folds": int(folds),
        "class_code_map": {str(value): name for name, value in label_codes.items()},
        "field_validation": False,
        "release_eligible": False,
        "limitations": [
            "Métrica mede concordância com TerraClass em blocos retidos, não acurácia de campo.",
            "TerraClass não distingue soja de milho; a classe Agricultura é agregada.",
            "Não extrapolar Amazônia/Cerrado para os demais biomas.",
            "PRODES é contexto/mascara de supressão, não rótulo de cultura ou floresta atual.",
            "Co-registro e contemporaneidade da série SAR exigem verificação da fonte de entrada.",
        ],
    }
    model_path = _safe_output_path(output_model)
    report_path = _safe_output_path(output_report)
    if model_path.suffix.lower() != ".joblib" or report_path.suffix.lower() != ".json":
        raise ValueError("Modelo deve terminar em .joblib e relatório em .json.")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "class_code_map": report["class_code_map"],
                 "domain": domain_key, "year": reference_year,
                 "experimental": True, "field_validated": False}, model_path)
    report["model_sha256"] = hashlib.sha256(model_path.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
