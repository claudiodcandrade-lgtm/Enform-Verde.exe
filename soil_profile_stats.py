"""Paired PronaSolos soil-layer stock summaries.

Only the same spatial query point may contribute to a depth profile. Layer
wise averages from different locations MUST NOT be added as though observed
together. Source raster estimates remain map estimates, not prediction CIs.
"""
from math import isfinite
from statistics import mean, stdev

LAYERS = ((2, "0–5"), (3, "5–15"), (4, "15–30"),
          (5, "30–60"), (6, "60–100"), (7, "100–200"))
TARGETS = {"0–30 cm": 3, "0–60 cm": 4,
           "0–100 cm": 5, "0–200 cm": 6}

def summarize_paired_soil_profiles(observations):
    """Return cumulative stocks only for jointly complete sets of horizons.

    observations: sequence of mappings layer_id -> carbon stock (tC/ha) for
    each geolocated sample point. Missing layer entries are distinct from zero.
    No extrapolation is performed. Depths overlap: never sum returned profiles.
    The reported SD represents descriptive spatial variation of mapped stocks,
    not a calibration or predictive uncertainty or a confidence interval.
    """
    if not isinstance(observations, (list, tuple)):
        raise ValueError("observations must be a sequence")
    for sample in observations:
        if not isinstance(sample, dict):
            raise ValueError("each sample must be a layer mapping")
        for value in sample.values():
            if isinstance(value, bool):
                raise ValueError("invalid soil stock")
            try:
                x = float(value)
            except (ValueError, TypeError) as e:
                raise ValueError("invalid soil stock") from e
            if not isfinite(x) or x < 0:
                raise ValueError("invalid soil stock")
    out = {}
    for label, count in TARGETS.items():
        need = [lid for lid, _ in LAYERS[:count]]
        paired = [sample for sample in observations if all(k in sample for k in need)]
        if not paired:
            continue
        sums = [sum(float(sample[k]) for k in need) for sample in paired]
        m = float(mean(sums))
        sd = float(stdev(sums)) if len(sums) > 1 else None
        out[label] = {
            "tc_ha": m,
            "spatial_sd_tc_ha": sd,
            "n_samples": len(paired),
            "layers": [name for _, name in LAYERS[:count]],
            "layer_means_tc_ha": {
                name: float(mean(float(sample[lid]) for sample in paired))
                for lid, name in LAYERS[:count]
            },
            "source": "PronaSolos/Embrapa Solos — estoque de carbono orgânico 90 m",
            "uncertainty_kind": (
                "DP espacial amostral dos totais por ponto com horizontes pareados; "
                "NÃO é IC95% nem erro de predição; correlação espacial, "
                "erro do mapa e viés de transferência não quantificados"
            ),
            "profile_pairing": "horizontes coincidentes por ponto de consulta",
            "predictive_uncertainty_quantified": False
        }
    return out
