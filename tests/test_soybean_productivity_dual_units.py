"""Unit test: soybean productivity has simultaneous t/ha and 60-kg bags/ha."""
from crop_forecast_pipeline import productivity_display


def test_soybean_dual_unit_display():
    p = {"median": 3600.0, "p05": 3000.0, "p95": 4200.0}
    text = productivity_display("Soja", p, fmt=lambda x, nd=0: f"{x:.{nd}f}")
    assert "3.60 t/ha" in text
    assert "3.00–4.20 t/ha" in text
    assert "60.00 sacas/ha" in text
    assert "50.00–70.00 sacas/ha" in text
    assert "60 kg/saca" in text
    assert "-16.7% / +16.7%" in text
    assert p == {"median": 3600.0, "p05": 3000.0, "p95": 4200.0}


def test_other_crops_remain_tonnes_per_hectare():
    p = {"median": 6000.0, "p05": 4000.0, "p95": 8000.0}
    text = productivity_display("Milho", p, fmt=lambda x, nd=0: f"{x:.{nd}f}")
    assert "6.00 t/ha" in text
    assert "sacas/ha" not in text


def test_asymmetric_uncertainty_percent_and_zero_median():
    fmt = lambda x, nd=0: f"{x:.{nd}f}"
    text = productivity_display("Soja", {"median": 3000, "p05": 2100, "p95": 3900}, fmt=fmt)
    assert "-30.0% / +30.0%" in text
    zero = productivity_display("Soja", {"median": 0, "p05": 0, "p95": 200}, fmt=fmt)
    assert "incerteza relativa: N/D" in zero
