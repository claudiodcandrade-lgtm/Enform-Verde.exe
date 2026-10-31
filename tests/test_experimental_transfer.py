"""Offline regression for quantitative but non-homologated secondary estimates.

Synthetic test values prove numerical contracts; they are never field evidence.
"""
import math
import unittest

from experimental_transfer import measured_transfer_error
from evidence_hierarchy import select_stock_evidence
from secondary_carbon_adapter import secondary_native_components
from native_carbon import estimate_native_components

BIOME = "Cerrado"
PHYS = "Formação Savânica"
DIGEST = "1" * 64


def record(pool, estimate, **extra):
    base = {
        "biome": BIOME, "physiognomy": PHYS, "pool": pool,
        "unit": "Mg/ha" if pool == "agb" else "tC/ha",
        "source": "Licensed study", "source_url": "https://example.org/study",
        "institution": "University", "licensed_for_use": True,
        "geographic_tier": "microrregional",
        "evidence_level": "primary_plots_open",
        "independent_units": 25, "estimate": estimate,
        "published_sd": 2.0, "pool_measurement": "direct_inventory",
    }
    if pool == "soil_0_100":
        base["depth_cm"] = [0, 100]
    base.update(extra)
    return base


def heldouts(n=20, pool="agb"):
    return [
        {"biome": BIOME, "physiognomy": PHYS, "pool": pool,
         "unit": "Mg/ha" if pool == "agb" else "tC/ha",
         "evidence_type": "independent_real_data",
         "training_overlap": False, "heldout_from_model_selection": True,
         "licensed_for_use": True,
         "source_url": "https://example.org/field",
         "dataset_sha256": DIGEST,
         "spatial_group": "site-" + str(i),
         "observation_id": "plot-" + str(i),
         "observed": 100.0, "predicted": 100.0 + i / 10.0}
        for i in range(n)
    ]


class ExperimentalTransferTests(unittest.TestCase):
    def test_five_groups_only_descriptive(self):
        value = measured_transfer_error(heldouts(5), biome=BIOME, physiognomy=PHYS,
                                        pool="agb", units="Mg/ha")
        self.assertTrue(value["available"])
        self.assertEqual(value["n_independent_groups"], 5)
        self.assertAlmostEqual(value["uncertainty_bound"], 0.4)
        self.assertIsNone(value["conformal_nominal_level"])
        self.assertFalse(value["target_aoi_coverage_validated"])

    def test_twenty_groups_candidate_quantile_not_homologated(self):
        value = measured_transfer_error(heldouts(20), biome=BIOME, physiognomy=PHYS,
                                        pool="agb", units="Mg/ha")
        self.assertEqual(value["n_independent_groups"], 20)
        self.assertAlmostEqual(value["uncertainty_bound"], 1.9)
        self.assertAlmostEqual(value["conformal_nominal_level"], 0.95)
        self.assertFalse(value["is_target_aoi_ci95"])

    def test_spatial_leakage_and_wrong_physiognomy_fail(self):
        bad = heldouts(20)
        bad[0]["training_overlap"] = True
        self.assertFalse(measured_transfer_error(bad, biome=BIOME, physiognomy=PHYS,
                                                pool="agb", units="Mg/ha")["available"])
        wrong = heldouts(20)
        wrong[0]["physiognomy"] = "Floresta Ombrófila Densa"
        self.assertFalse(measured_transfer_error(wrong, biome=BIOME, physiognomy=PHYS,
                                                pool="agb", units="Mg/ha")["available"])

    def test_duplicate_or_unlicensed_field_fails(self):
        bad = heldouts(20)
        bad.append(dict(bad[0]))
        self.assertFalse(measured_transfer_error(bad, biome=BIOME, physiognomy=PHYS,
                                                pool="agb", units="Mg/ha")["available"])
        unlicensed = heldouts(20)
        unlicensed[0]["licensed_for_use"] = False
        self.assertFalse(measured_transfer_error(unlicensed, biome=BIOME, physiognomy=PHYS,
                                                pool="agb", units="Mg/ha")["available"])

    def test_transfer_validation_takes_precedence_to_unverified_percent(self):
        item = record("agb", 100, geographic_tier="regional",
                      published_sd=10, transfer_uncertainty=999,
                      transfer_validation=heldouts(20))
        result = select_stock_evidence([item], biome=BIOME, physiognomy=PHYS,
                                       pool="agb", unit="Mg/ha")
        self.assertTrue(result["available"])
        self.assertAlmostEqual(result["transfer_uncertainty"], 1.9)
        self.assertEqual(result["range"], [88.1, 111.9])
        self.assertFalse(result["is_target_aoi_ci95"])

    def test_invalid_validation_cannot_be_bypassed_by_manual_percent(self):
        item = record("agb", 100, geographic_tier="estadual",
                      transfer_validation=heldouts(4), transfer_uncertainty=500)
        result = select_stock_evidence([item], biome=BIOME, physiognomy=PHYS,
                                       pool="agb", unit="Mg/ha")
        self.assertFalse(result["available"])
        self.assertEqual(result["rejections"][0]["reason"],
                         "invalid_independent_transfer_validation")


class SecondaryCarbonTests(unittest.TestCase):
    def test_six_sources_are_separate_and_deadwood_sum_not_double_counted(self):
        items = [record("agb", 100), record("roots", 18),
                 record("standing_deadwood", 3), record("downed_deadwood", 5),
                 record("litter", 2), record("soil_0_100", 43)]
        result = secondary_native_components(items, biome=BIOME, physiognomy=PHYS)
        rows = {x["parametro"]: x for x in result["components"]}
        self.assertEqual(len(rows), 5)
        self.assertAlmostEqual(rows["Biomassa aérea"]["tc"], 47.0)
        self.assertEqual(rows["Necromassa aérea"]["tc"], 8)
        self.assertEqual(rows["Solo 0–100 cm"]["tc"], 43)
        self.assertFalse(rows["Necromassa aérea"]["scientifically_homologated"])

    def test_partial_deadwood_is_never_total(self):
        value = secondary_native_components(
            [record("downed_deadwood", 6)], biome=BIOME, physiognomy=PHYS)
        self.assertEqual(value["components"], [])
        self.assertIn("deadwood_partial", value["audit"])

    def test_class_incompatible_records_never_transfer(self):
        value = secondary_native_components(
            [record("litter", 5, physiognomy="Floresta Ombrófila Densa")],
            biome=BIOME, physiognomy=PHYS)
        self.assertEqual(value["components"], [])

    def test_explicit_fallback_populates_missing_pool_and_preserves_sar(self):
        data = [record("agb", 100), record("litter", 2)]
        no_sar = estimate_native_components(None, PHYS, BIOME,
                    lambda *_: {}, lambda _: {}, inventory_evidence=data)
        by_pool = {v["parametro"]: v for v in no_sar["components"]}
        self.assertEqual(by_pool["Serapilheira"]["tc"], 2)
        self.assertAlmostEqual(by_pool["Biomassa aérea"]["tc"], 47.0)
        self.assertTrue(no_sar["secondary_evidence_audit"]["agb"]["available"])
        sar = estimate_native_components(None, PHYS, BIOME,
                    lambda *_: {"agb_mg_ha": 30, "data_origin": "SAR_PIXELS",
                                "source": "Validated radar processing"},
                    lambda _: {}, inventory_evidence=data)
        by_pool = {v["parametro"]: v for v in sar["components"]}
        self.assertAlmostEqual(by_pool["Biomassa aérea"]["tc"], 14.1)
        self.assertEqual(by_pool["Biomassa aérea"]["origem"], "SAR_PIXELS")
        self.assertEqual(by_pool["Serapilheira"]["tc"], 2)

    def test_existing_pipeline_unchanged_without_inventory_evidence(self):
        result = estimate_native_components(None, PHYS, BIOME,
                    lambda *_: {}, lambda _: {})
        self.assertIsNone(result["secondary_evidence_audit"])


if __name__ == "__main__":
    unittest.main()
