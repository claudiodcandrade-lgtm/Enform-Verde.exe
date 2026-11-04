"""Crop-specific research registry is explicit about integration and calibration."""
from crop_specific_model_registry import MODEL_REGISTRY, CURRENT_CALIBRATED_PANEL, model_contract


def test_all_nine_crops_have_specific_model_and_stage_features():
    assert set(MODEL_REGISTRY) == {"Soja", "Milho", "Sorgo", "Feijão", "Arroz",
                                   "Cana-de-açúcar", "Algodão", "Café", "Citros"}
    for crop in MODEL_REGISTRY:
        spec = model_contract(crop)
        assert spec["status"] == "research_backed_not_integrated"
        assert spec["recommended_model"] and spec["source"].startswith("https://")
        assert len(spec["phenological_stages"]) >= 3
        assert len(spec["climate_features"]) >= 3
        assert len(spec["sar_features"]) >= 2
        assert "não integrado" in spec["warning"]


def test_research_model_is_not_misrepresented_as_calibrated():
    assert CURRENT_CALIBRATED_PANEL == {"Soja", "Milho"}
    assert model_contract("Soja")["existing_panel_available"]
    assert not model_contract("Café")["existing_panel_available"]
    assert model_contract("Algodão")["yield_basis"].startswith("algodão em caroço")
    assert model_contract("Citros")["status"] == "research_backed_not_integrated"
    assert model_contract("Não reconhecida")["status"] == "N/D"
