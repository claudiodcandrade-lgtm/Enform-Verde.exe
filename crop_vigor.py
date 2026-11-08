"""Crop vigor in three classes — "baixo vigor", "vigor adequado", "alto vigor".

Per field (one crop, one phenological stage, one acquisition window) three
observable factors are measured on Sentinel-1 dual-pol data:

* size  — apparent plant size: median canopy height (m) when an InSAR/height
  product is supplied; otherwise median dual-pol Radar Vegetation Index
  RVI = 4·σ⁰VH / (σ⁰VV + σ⁰VH) (linear units; dual-pol adaptation of Kim &
  van Zyl 2009, used for crops e.g. by Nasirzadehdizaji et al. 2019,
  Appl. Sci. 9:655), a proxy of canopy biomass/cover;
* uniformity — U = 1/(1 + CV) of 3×3-multilooked RVI inside the field;
* roughness — canopy texture by GLCM homogeneity
  Hom = Σ P(i,j)/(1+(i−j)²) of VH (dB, 32 levels on a FIXED −30…−5 dB range,
  4 directions, symmetric). A more homogeneous canopy texture is read as a
  more regular stand. This is radar texture, NOT a physical roughness
  measurement of leaves or soil.

Each factor is standardised against REFERENCE FIELDS of the same crop, stage,
region and date window (robust z = (x − median)/(1.4826·MAD)). The composite
V is the weighted mean of the z-scores (equal weights by default — documented
assumption, to be calibrated with field data). Class limits are the empirical
terciles of the reference composites (leave-one-out), so "adequado" means
"typical of comparable fields", not an absolute agronomic diagnosis.

Uncertainty is quantified: a spatial block bootstrap of the field (5×5-pixel
blocks, speckle/autocorrelation aware) and a bootstrap of the reference
fields yield P(baixo), P(adequado), P(alto). Field truth for vigor classes is
still required before calling this validated: status = experimental.
"""
from __future__ import annotations

import numpy as np

CLASSES = ("baixo vigor", "vigor adequado", "alto vigor")
GLCM_LEVELS = 32
VH_RANGE_DB = (-30.0, -5.0)
OFFSETS = ((0, 1), (1, 0), (1, 1), (1, -1))
DEFAULT_WEIGHTS = {"size": 1.0, "uniformity": 1.0, "texture_homogeneity": 1.0}
MIN_PIXELS = 30
MIN_REFERENCE_FIELDS = 6


def _boxcar3(a):
    """3×3 NaN-aware mean (multilook) to damp speckle before CV."""
    pad = np.pad(a, 1, constant_values=np.nan)
    stack = np.stack([pad[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)])
    valid = np.isfinite(stack)
    with np.errstate(invalid="ignore"):
        out = np.where(valid, stack, 0).sum(0) / valid.sum(0)
    out[~np.isfinite(a)] = np.nan
    return out


def _quantize(vh_db):
    lo, hi = VH_RANGE_DB
    q = np.floor((np.clip(vh_db, lo, hi - 1e-9) - lo) / (hi - lo) * GLCM_LEVELS)
    return np.where(np.isfinite(vh_db), q, -1).astype(int)


def _glcm_counts(q):
    """Symmetric co-occurrence counts over the 4 directions; −1 = outside field."""
    counts = np.zeros((GLCM_LEVELS, GLCM_LEVELS))
    h, w = q.shape
    for dy, dx in OFFSETS:            # dy >= 0 for every offset
        if h - dy <= 0 or w - abs(dx) <= 0:
            continue
        xa = slice(0, w - dx) if dx >= 0 else slice(-dx, w)
        xb = slice(dx, w) if dx >= 0 else slice(0, w + dx)
        a = q[0:h - dy, xa]
        b = q[dy:h, xb]
        ok = (a >= 0) & (b >= 0)
        np.add.at(counts, (a[ok], b[ok]), 1)
        np.add.at(counts, (b[ok], a[ok]), 1)
    return counts


def _homogeneity(counts):
    total = counts.sum()
    if total <= 0:
        return np.nan
    i, j = np.indices(counts.shape)
    return float((counts / total / (1.0 + (i - j) ** 2)).sum())


def _blocks(vh_db, vv_db, height, block=5):
    rvi = None
    with np.errstate(invalid="ignore", divide="ignore"):
        vh = 10 ** (vh_db / 10.0); vv = 10 ** (vv_db / 10.0)
        rvi = 4 * vh / (vv + vh)
    rvi_ml = _boxcar3(rvi)
    q = _quantize(vh_db)
    out = []
    H, W = vh_db.shape
    for r in range(0, H, block):
        for c in range(0, W, block):
            sl = (slice(r, r + block), slice(c, c + block))
            vals = rvi_ml[sl][np.isfinite(rvi_ml[sl])]
            if not len(vals):
                continue
            # GLCM inside the block plus one-pixel halo so adjacency is kept
            qs = q[max(0, r - 1):r + block, max(0, c - 1):c + block]
            hts = None
            if height is not None:
                hh = height[sl]; hts = hh[np.isfinite(hh)]
            out.append({"rvi": vals, "glcm": _glcm_counts(qs), "height": hts})
    return out


def _metrics_from_blocks(blocks):
    rvi = np.concatenate([b["rvi"] for b in blocks])
    glcm = sum(b["glcm"] for b in blocks)
    heights = [b["height"] for b in blocks if b["height"] is not None and len(b["height"])]
    size = float(np.median(np.concatenate(heights))) if heights else float(np.median(rvi))
    mean = float(np.mean(rvi))
    cv = float(np.std(rvi, ddof=1) / mean) if mean > 0 and len(rvi) > 1 else np.nan
    return {"size": size, "size_kind": "altura_mediana_m" if heights else "RVI_mediano",
            "uniformity": 1.0 / (1.0 + cv) if np.isfinite(cv) else np.nan,
            "texture_homogeneity": _homogeneity(glcm), "n_pixels": int(len(rvi))}


def field_metrics(vh_db, vv_db, height_m=None):
    """Field-level vigor factors. Arrays share one grid; NaN = outside field."""
    vh_db = np.asarray(vh_db, float); vv_db = np.asarray(vv_db, float)
    if vh_db.shape != vv_db.shape:
        raise ValueError("VH e VV com grades diferentes")
    h = None if height_m is None else np.asarray(height_m, float)
    blocks = _blocks(vh_db, vv_db, h)
    if not blocks:
        raise ValueError("talhão sem pixels válidos")
    return _metrics_from_blocks(blocks)


def _robust(values):
    v = np.asarray(values, float)
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) * 1.4826
    if mad <= 0:
        sd = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
        mad = sd if sd > 0 else np.nan
    return med, mad


def _composite(metrics, ref_stats, weights):
    num = den = 0.0; z = {}
    for k, w in weights.items():
        x = metrics.get(k); med, scale = ref_stats[k]
        if x is None or not np.isfinite(x) or not np.isfinite(scale):
            continue
        z[k] = (x - med) / scale
        num += w * z[k]; den += w
    return (num / den if den else np.nan), z


def _reference_terciles(reference, weights):
    comps = []
    for i in range(len(reference)):
        others = reference[:i] + reference[i + 1:]
        stats = {k: _robust([r[k] for r in others]) for k in weights}
        comps.append(_composite(reference[i], stats, weights)[0])
    comps = np.asarray([c for c in comps if np.isfinite(c)])
    return np.quantile(comps, [1 / 3, 2 / 3])


def _klass(v, t):
    return 0 if v < t[0] else (2 if v > t[1] else 1)


def classify_vigor(vh_db, vv_db, reference_fields, *, height_m=None, weights=None,
                   n_boot=300, seed=20261103):
    """Return class, probabilities and the full audit for one field."""
    weights = dict(weights or DEFAULT_WEIGHTS)
    ref = [dict(r) for r in reference_fields or []]
    if len(ref) < MIN_REFERENCE_FIELDS:
        return {"status": "N/D", "reason": f"menos de {MIN_REFERENCE_FIELDS} talhões de referência "
                "da mesma cultura/fase/região — vigor relativo não definível"}
    if any(r.get("size_kind") not in (None, "altura_mediana_m", "RVI_mediano") for r in ref):
        raise ValueError("referência com tipo de tamanho desconhecido")
    vh_db = np.asarray(vh_db, float); vv_db = np.asarray(vv_db, float)
    h = None if height_m is None else np.asarray(height_m, float)
    blocks = _blocks(vh_db, vv_db, h)
    m = _metrics_from_blocks(blocks) if blocks else None
    if m is None or m["n_pixels"] < MIN_PIXELS:
        return {"status": "N/D", "reason": f"talhão com menos de {MIN_PIXELS} pixels válidos"}
    if m.get("size_kind") != "altura_mediana_m":
        return {"status":"N/D",
                "reason":"altura de plantas em metros sem modelo SAR validado para cultura/região/fase; RVI é proxy de cobertura e não substitui altura",
                "partial_metrics":m,
                "uncertainty":"classe de vigor composta não calculada"}
    if any(r.get("size_kind", m["size_kind"]) != m["size_kind"] for r in ref):
        return {"status": "N/D", "reason": "referência e talhão usam medidas de tamanho diferentes"}
    stats = {k: _robust([r[k] for r in ref]) for k in weights}
    V, z = _composite(m, stats, weights)
    t = _reference_terciles(ref, weights)
    rng = np.random.default_rng(seed)
    counts = np.zeros(3); boot = []
    metric_boot = {k: [] for k in ("size", "uniformity", "texture_homogeneity")}
    for _ in range(n_boot):
        bb = [blocks[i] for i in rng.integers(0, len(blocks), len(blocks))]
        rr = [ref[i] for i in rng.integers(0, len(ref), len(ref))]
        try:
            st = {k: _robust([r[k] for r in rr]) for k in weights}
            tb = _reference_terciles(rr, weights)
            bm = _metrics_from_blocks(bb)
            vb = _composite(bm, st, weights)[0]
        except (ValueError, IndexError):
            continue
        if np.isfinite(vb) and np.all(np.isfinite(tb)):
            counts[_klass(vb, tb)] += 1; boot.append(vb)
            for key in metric_boot:
                if np.isfinite(bm.get(key, np.nan)):
                    metric_boot[key].append(float(bm[key]))
    if counts.sum() == 0 or not np.isfinite(V) or not np.all(np.isfinite(t)):
        return {"status": "N/D", "reason": "bootstrap espacial ou referências inválidos para a estimativa de incerteza"}
    probs = counts / counts.sum()
    metric_intervals = {key: [float(np.quantile(values, .05)), float(np.quantile(values, .95))]
                        for key, values in metric_boot.items() if len(values) >= 10}
    return {"status": "experimental", "class": CLASSES[_klass(V, t)],
            "probabilities": dict(zip(CLASSES, map(float, probs))),
            "composite": float(V), "composite_boot_p05_p95": (
                [float(np.quantile(boot, .05)), float(np.quantile(boot, .95))] if boot else None),
            "reference_terciles": [float(x) for x in t], "z_scores": z, "metrics": m,
            "weights": weights, "n_reference_fields": len(ref), "n_bootstrap": int(counts.sum()),
            "metric_boot_p05_p95": metric_intervals,
            "uncertainty_scope": ("Intervalo percentílico 90% dos indicadores por bootstrap espacial em blocos; "
                                  "probabilidades são estabilidade interna da classificação, NÃO acurácia "
                                  "observada em campo nem IC de produtividade."),
            "radar_interpretation": {"size": "RVI mediano, proxy da cobertura vegetal; altura só com produto independente",
                                     "uniformity": "1/(1+CV) do RVI multilook 3×3",
                                     "texture_homogeneity": "homogeneidade GLCM do VH dB; proxy de textura/rugosidade do radar"},
            "method": "z robusto vs. talhões de referência; tercis da referência; bootstrap espacial em blocos 5×5",
            "limitations": ("Pesos iguais não calibrados; textura SAR não é rugosidade física; "
                            "classes relativas à referência regional; validar com vigor observado em campo.")}
