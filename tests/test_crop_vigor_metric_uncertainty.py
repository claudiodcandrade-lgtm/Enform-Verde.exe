"""Unit tests for SAR vigor metric uncertainty; synthetic arrays are TEST FIXTURES,
never real Sentinel-1 observations or scientific validation."""
import numpy as np
from crop_vigor import classify_vigor, field_metrics


def test_metric_components_and_bootstrap_ranges():
    rng = np.random.default_rng(12)
    shape = (24, 24)
    vh = rng.normal(-17, 2, shape)
    vv = rng.normal(-10, 1.5, shape)
    refs = []
    for k in range(8):
        refs.append(field_metrics(rng.normal(-17 + k * .5, 2, shape),
                                  rng.normal(-10 - k * .2, 1.5, shape)))
    out = classify_vigor(vh, vv, refs, n_boot=80, seed=12)
    assert out["status"] == "experimental"
    assert set(out["metrics"]) >= {"size", "uniformity", "texture_homogeneity"}
    assert set(out["metric_boot_p05_p95"]) == {"size", "uniformity", "texture_homogeneity"}
    for lo, hi in out["metric_boot_p05_p95"].values():
        assert np.isfinite([lo, hi]).all() and lo <= hi
    assert out["n_bootstrap"] > 0
    assert abs(sum(out["probabilities"].values()) - 1.) < 1e-8
    assert "NÃO acurácia" in out["uncertainty_scope"]
    assert "radar_interpretation" in out


def test_no_reference_fields_is_nd_not_false_accuracy():
    out = classify_vigor(np.full((25, 25), -16.), np.full((25, 25), -10.), [], n_boot=20)
    assert out["status"] == "N/D"
