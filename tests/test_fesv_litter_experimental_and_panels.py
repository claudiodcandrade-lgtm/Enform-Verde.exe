"""Synthetic regression fixtures for north Mato Grosso FESV experimental litter.
No synthetic observation is a scientific validation of transferred stocks."""
import unittest
from shapely.geometry import box
from carbon_compartments import northern_mato_grosso_fesv_litter_component
from native_carbon import estimate_native_components
from executive_carbon_report import executive_carbon_lines


class NorthMatoGrossoLitterTest(unittest.TestCase):
    def setUp(self):
        self.aoi = box(-55.75, -11.92, -55.74, -11.91)

    def test_litter_source_without_defined_dispersion_is_reference_only(self):
        x = northern_mato_grosso_fesv_litter_component(
            "Amazônia", "Floresta Estacional Sempre-Verde Submontana", self.aoi)
        self.assertIsNotNone(x)
        self.assertIsNone(x["mean_tc_ha"])
        self.assertIsNone(x["range_tc_ha"])
        self.assertEqual(x["published_sample_plots"], 24)
        self.assertEqual(x["origin"], "NAO_ESTIMADO")
        self.assertFalse(x["include_in_total"])
        self.assertIn("natureza de ± não publicada", x["uncertainty_kind"])

    def test_wrong_formation_biome_and_region_not_transferred(self):
        self.assertIsNone(northern_mato_grosso_fesv_litter_component(
            "Amazônia", "Floresta Ombrófila Densa", self.aoi))
        self.assertIsNone(northern_mato_grosso_fesv_litter_component(
            "Cerrado", "Floresta Estacional Sempre-Verde Submontana", self.aoi))
        self.assertIsNone(northern_mato_grosso_fesv_litter_component(
            "Amazônia", "Floresta Estacional Sempre-Verde Submontana",
            box(-45, -8, -44.9, -7.9)))

    def test_litter_without_variance_is_not_reported_as_numeric_stock(self):
        def sar(*args):
            return {"agb_mg_ha": 50.0, "data_origin": "SAR_DERIVED_CCI",
                    "source": "fixture", "regional_components": {}}
        def soil(*args):
            return {}
        result = estimate_native_components(
            self.aoi,"Floresta Estacional Sempre-Verde Submontana",
            "Amazônia",sar,soil)
        rows = {r["parametro"]:r for r in result["components"]}
        x = rows["Serapilheira"]
        self.assertIsNone(x["tc"])
        self.assertEqual(x["origem"], "NAO_ESTIMADO")
        self.assertFalse(x["include_in_total"])
        self.assertIsNone(x["range_tc_ha"])

    def test_executive_land_use_is_not_entirely_forest(self):
        x = executive_carbon_lines({
            "area_aoi_ha": 1500.33, "native_area_ha": 72.92,
            "excluded_other_uses_ha": 1427.41, "unknown_cover_area_ha": 0,
            "cover_completeness":"COMPLETE", "known_total_tc": 11010.48,
            "complete":False, "strata":[]}, lambda v, nd=2: f"{v:,.{nd}f}")
        text = "\n".join(x)
        self.assertIn("72.92", text)
        self.assertIn("1,427.41", text)
        self.assertIn("não", text.lower())


if __name__=="__main__":
    unittest.main()
