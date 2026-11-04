"""Scientific contract for stage-dependent PAM × FAO × SAR yield.
All synthetic values below are unit-test fixtures, never field observations."""
import pytest
from crop_yield_phenology_matrix import design_features, integrate_yield_matrix, validate_field_observation
from crop_specific_model_registry import MODEL_REGISTRY


def fixtures(crop="Soja"):
    stages = MODEL_REGISTRY[crop]["critical_stages"]
    measurements = {s: {"eta_etc": .75, "heat_z": .3, "sar_vigor_z": -.25,
                        "sar_scene_ids": ["SCENE-UNIT-TEST"], "sar_acquisition_utc": "2026-11-01T10:00:00Z",
                        "sar_pixels_read": True, "weather_source": "NASA POWER"} for s in stages}
    return measurements, {s: .8 for s in stages}


def test_all_nine_crops_have_stage_specific_matrix_dimensions():
    for crop in MODEL_REGISTRY:
        stages, ky = fixtures(crop)
        names, values = design_features(crop, {"stages": stages}, ky_by_stage=ky)
        assert len(names) == len(values) == 4 * len(stages)
        assert names[0].endswith("water_stress")
        assert values[0] == pytest.approx(.2)
        assert values[3] == pytest.approx(-.05)


def test_sar_conditional_projection_not_allowed_without_field_calibration():
    stages, ky = fixtures()
    r = integrate_yield_matrix("Soja", pam_baseline_kg_ha=3200, stages=stages, ky_by_stage=ky)
    assert r["status"] == "N/D"
    assert r["pam_baseline_kg_ha"] == 3200
    assert "coeficientes SAR" in r["reason"]


def test_field_evidence_gate():
    stages, _ = fixtures()
    valid = {"field_id": "TESTE", "harvest_year": 2026, "observed_yield_source": "fixture",
             "observed_yield_kg_ha": 3000, "stages": stages}
    validate_field_observation("Soja", valid)
    invalid = {**valid, "observed_yield_source": ""}
    with pytest.raises(ValueError, match="independente"):
        validate_field_observation("Soja", invalid)
