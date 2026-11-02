"""All numeric fixtures here are SYNTHETIC regression values, not observations."""
import copy
import unittest

from experimental_soil_scenarios import soil_0_100_scenario_envelope

BIOME = "Amazônia"
PHYS = "Floresta Ombrófila Densa"
DEPTHS = (0, 5, 15, 30, 60, 100)


def example_horizons():
    return [{
        "top_cm": a,
        "bottom_cm": b,
        "biome": BIOME,
        "physiognomy": PHYS,
        "bulk_density_basis": "fine_earth_volume",
        "bulk_density_g_cm3": [1.0, 1.2, 1.4],
        "organic_carbon_mass_fraction": [.01, .02, .03],
        "coarse_fragment_volume_fraction": [0.0, .10, .20],
        "licensed_for_use": True,
        "source_url": "https://example.org/synthetic-fixture-not-field-data",
        "source_sha256": "a" * 64,
    } for a, b in zip(DEPTHS[:-1], DEPTHS[1:])]


class ExperimentalSoilScenarioTests(unittest.TestCase):
    def evaluate(self, rows):
        return soil_0_100_scenario_envelope(rows, biome=BIOME, physiognomy=PHYS)

    def test_physical_stock_and_worst_case_box_bounds(self):
        r = self.evaluate(example_horizons())
        self.assertTrue(r["available"])
        self.assertEqual(r["status"], "experimental")
        # 100 cm * 100 * BD * C * (1 - rock)
        self.assertAlmostEqual(r["stock_tc_ha"], 216.0)
        self.assertAlmostEqual(r["scenario_range_tc_ha"][0], 80.0)
        self.assertAlmostEqual(r["scenario_range_tc_ha"][1], 420.0)
        self.assertAlmostEqual(r["stock_tco2e_ha"], 216 * 44 / 12)
        self.assertEqual(r["depth_cm"], [0, 100])
        self.assertEqual(r["source_count"], 1)

    def test_scenario_is_never_homologated_or_a_confidence_interval(self):
        r = self.evaluate(example_horizons())
        self.assertFalse(r["is_target_aoi_ci95"])
        self.assertFalse(r["scientifically_homologated"])
        self.assertFalse(r["target_aoi_coverage_validated"])
        self.assertFalse(r["source_bytes_verified"])
        self.assertIsNone(r["transfer_error_tc_ha"])
        self.assertNotIn("ci95_tc_ha", r)

    def test_missing_horizon_is_nd_not_zero_or_extrapolation(self):
        self.assertEqual(self.evaluate(example_horizons()[:-1])["status"], "not_available")

    def test_missing_deep_interval_is_nd(self):
        rows = example_horizons()
        rows[-1]["bottom_cm"] = 60
        self.assertFalse(self.evaluate(rows)["available"])

    def test_gaps_overlap_and_unsorted_layers_are_nd(self):
        for mutation in ("gap", "overlap", "unsorted"):
            rows = example_horizons()
            if mutation == "gap":
                rows[2]["top_cm"] = 20
            elif mutation == "overlap":
                rows[1]["bottom_cm"] = 20
            else:
                rows[1], rows[2] = rows[2], rows[1]
            with self.subTest(mutation=mutation):
                self.assertEqual(self.evaluate(rows)["status"], "not_available")

    def test_wrong_physiognomy_biome_or_unlicensed_are_nd(self):
        for field, value in (("physiognomy", "Formação Savânica"),
                             ("biome", "Pantanal"), ("licensed_for_use", False)):
            rows = example_horizons()
            rows[3][field] = value
            with self.subTest(field=field):
                self.assertFalse(self.evaluate(rows)["available"])

    def test_digest_and_source_are_not_assumed_verified(self):
        rows = example_horizons()
        rows[0]["source_sha256"] = "not a sha"
        self.assertFalse(self.evaluate(rows)["available"])
        rows = example_horizons()
        rows[0]["source_url"] = "http://unverified.example"
        self.assertFalse(self.evaluate(rows)["available"])

    def test_density_must_be_fine_earth_volume_basis(self):
        rows = example_horizons()
        rows[0]["bulk_density_basis"] = "total_soil_volume"
        self.assertFalse(self.evaluate(rows)["available"])

    def test_physical_bounds_and_nan_rejected(self):
        bad = [
            ("bulk_density_g_cm3", [1.0, .9, 1.4]),
            ("bulk_density_g_cm3", [0.0, .4, 1.0]),
            ("bulk_density_g_cm3", [1.0, float("inf"), 1.5]),
            ("organic_carbon_mass_fraction", [.01, .03, 1.01]),
            ("organic_carbon_mass_fraction", [-.1, .02, .03]),
            ("coarse_fragment_volume_fraction", [0.0, .1, 1.0]),
            ("coarse_fragment_volume_fraction", [0.0, True, .2]),
        ]
        for field, value in bad:
            rows = example_horizons()
            rows[1][field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(self.evaluate(rows)["status"], "not_available")

    def test_incomplete_domain_returns_nd(self):
        self.assertFalse(soil_0_100_scenario_envelope(
            example_horizons(), biome="nonbiome", physiognomy=PHYS)["available"])
        self.assertFalse(soil_0_100_scenario_envelope(
            example_horizons(), biome=BIOME, physiognomy="")["available"])

    def test_nominal_rock_fraction_effect_monotonic(self):
        lowrock = example_horizons()
        for r in lowrock:
            r["coarse_fragment_volume_fraction"] = [0, 0, 0]
        highrock = example_horizons()
        for r in highrock:
            r["coarse_fragment_volume_fraction"] = [.2, .2, .2]
        self.assertGreater(self.evaluate(lowrock)["stock_tc_ha"],
                           self.evaluate(highrock)["stock_tc_ha"])

    def test_nonlinearity_is_bounded_without_independence_assumption(self):
        rows = example_horizons()
        # Extreme parameter combinations across all horizons share common
        # drivers; endpoint arithmetic is valid but provides no probability.
        for r in rows:
            r["organic_carbon_mass_fraction"] = [.01, .01, .01]
        result = self.evaluate(rows)
        self.assertAlmostEqual(result["scenario_range_tc_ha"][0], 80)
        self.assertAlmostEqual(result["scenario_range_tc_ha"][1], 140)

    def test_optional_pipeline_fills_soil_only_without_measured_profile(self):
        from native_carbon import estimate_native_components
        soil = {"experimental_horizons_0_100": example_horizons()}
        result = estimate_native_components(
            None, PHYS, BIOME, lambda *_: {}, lambda _: soil)
        rows = {x["parametro"]: x for x in result["components"]}
        self.assertEqual(rows["Solo 0–100 cm"]["origem"], "EXPERIMENTAL_FISICO")
        self.assertEqual(rows["Solo 0–100 cm"]["tc"], 216)
        self.assertFalse(rows["Solo 0–100 cm"]["scientifically_homologated"])
        self.assertEqual(rows["Solo 0–100 cm"]["range_tc_ha"], [80, 420])

    def test_measured_soil_profile_precedes_experimental(self):
        from native_carbon import estimate_native_components
        soil = {
            "0–100 cm": {"tc_ha": 25},
            "experimental_horizons_0_100": example_horizons()
        }
        result = estimate_native_components(
            None, PHYS, BIOME, lambda *_: {}, lambda _: soil)
        rows = [x for x in result["components"] if x["parametro"] == "Solo 0–100 cm"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tc"], 25)
        self.assertEqual(rows[0]["origem"], "MAPEAMENTO")


if __name__ == "__main__":
    unittest.main()
