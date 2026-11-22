"""Contract checks: geographical specificity and defensible published uncertainty."""
import unittest
from evidence_hierarchy import select_stock_evidence


def row(**changes):
    base = dict(biome="Amazônia", physiognomy="Floresta Ombrófila Densa",
                pool="agb", unit="Mg/ha", source="Licensed IFN plots",
                source_url="https://dados.florestal.gov.br/", institution="SFB",
                licensed_for_use=True, geographic_tier="microrregional",
                evidence_level="primary_plots_open", estimate=300.0,
                published_sd=50.0, independent_units=20)
    return dict(base, **changes)


class EvidenceHierarchyTests(unittest.TestCase):
    def select(self, rows, pool="agb", phys="Floresta Ombrófila Densa", unit="Mg/ha"):
        return select_stock_evidence(rows, biome="Amazônia", physiognomy=phys,
                                     pool=pool, unit=unit)

    def test_microrregional_beats_more_precise_nonlocal(self):
        regional = row(source="State IFN", geographic_tier="estadual",
                       evidence_level="official_inventory", estimate=400.0,
                       published_sd=1.0, transfer_uncertainty=75.0)
        found = self.select([regional, row()])
        self.assertTrue(found["available"])
        self.assertEqual(found["source"], "Licensed IFN plots")
        self.assertEqual(found["range"], [250.0, 350.0])
        self.assertFalse(found["is_target_aoi_ci95"])

    def test_nonlocal_requires_quantified_transfer(self):
        result = self.select([row(geographic_tier="estadual",
                                  transfer_uncertainty=None)])
        self.assertFalse(result["available"])
        self.assertEqual(result["rejections"][0]["reason"],
                         "missing_nonlocal_transfer_uncertainty")

    def test_incompatible_physiognomy_never_substituted(self):
        result = self.select([row(physiognomy="Formação Campestre")])
        self.assertFalse(result["available"])
        self.assertEqual(result["rejections"][0]["reason"],
                         "incompatible_physiognomy")

    def test_source_interval_is_not_aoi_ci(self):
        result = self.select([row(published_ci95=["250", "360"], published_sd=None)])
        self.assertTrue(result["available"])
        self.assertEqual(result["range"], [250.0, 360.0])
        self.assertFalse(result["scientifically_homologated"])

    def test_roots_and_deadwood_require_compatible_measurement(self):
        roots = row(pool="roots", unit="tC/ha", published_sd=3)
        self.assertFalse(self.select([roots], pool="roots", unit="tC/ha")["available"])
        valid = row(pool="roots", unit="tC/ha", published_sd=3,
                    pool_measurement="validated_allometry", estimate=20)
        self.assertTrue(self.select([valid], pool="roots", unit="tC/ha")["available"])
        dead = row(pool="standing_deadwood", unit="tC/ha", estimate=7,
                   published_sd=1, pool_measurement="validated_allometry")
        self.assertFalse(self.select([dead], pool="standing_deadwood", unit="tC/ha")["available"])

    def test_soil_wrong_depth_or_unlicensed_rejected(self):
        incomplete = row(pool="soil_0_100", unit="tC/ha", depth_cm=[0, 30])
        unlicensed = row(licensed_for_use=False)
        self.assertFalse(self.select([incomplete], pool="soil_0_100", unit="tC/ha")["available"])
        self.assertFalse(self.select([unlicensed])["available"])

    def test_aggregated_reference_interval_is_descriptive(self):
        report = self.select([row(evidence_level="peer_reviewed_aggregate",
                                  geographic_tier="regional",
                                  transfer_uncertainty=20, published_sd=50)])
        self.assertEqual(report["range"], [230.0, 370.0])
        self.assertEqual(report["uncertainty_kind"],
                         "source_published_sd_descriptive_only; explicit_nonlocal_transfer_envelope")


if __name__ == "__main__":
    unittest.main()
