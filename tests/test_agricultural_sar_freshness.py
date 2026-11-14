import unittest
from datetime import datetime, timedelta, timezone

from agricultural_sar_freshness import freshness_report, land_use_diagnostic_status


class AgriculturalSarFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
        self.manifests = [{"scenes": [
            {"id": "new", "acquisition_utc": (self.now-timedelta(days=4)).isoformat(), "relative_orbit": 3},
            {"id": "old", "acquisition_utc": (self.now-timedelta(days=15)).isoformat(), "relative_orbit": 3},
        ]}]

    def test_missing_crop_phase_thresholds_fail_closed(self):
        result = freshness_report(self.manifests, now=self.now)
        self.assertEqual(result["status"], "criterios_temporais_nao_definidos")
        self.assertFalse(result["freshness_criteria"]["defined"])
        self.assertEqual(result["age_days"], 4.0)

    def test_explicit_crop_phase_criteria_assess_actual_acquisition_age(self):
        result = freshness_report(
            self.manifests, crop="soja", region="MT", phenological_phase="enchimento",
            now=self.now, max_age_days=8, series_window_days=35, min_scenes=2,
            threshold_source="calendário local validado + distribuição de revisita S1",
        )
        self.assertEqual(result["status"], "cenas_recentes_identificadas")
        self.assertEqual(result["scenes_in_series_window"], 2)
        self.assertEqual(result["freshness_criteria"]["source"], "calendário local validado + distribuição de revisita S1")

    def test_stale_acquisition_never_claims_current_diagnostic(self):
        result = freshness_report(
            self.manifests, crop="soja", region="MT", phenological_phase="enchimento",
            now=self.now, max_age_days=2, series_window_days=35, min_scenes=2,
            threshold_source="validated phase threshold",
        )
        self.assertEqual(result["status"], "desatualizado")
        status = land_use_diagnostic_status(
            freshness=result, classifier_validated=True, imagery_processed=True,
            native_mask_verified=True,
        )
        self.assertEqual(status, "diagnostico_com_restricao_temporal")


if __name__ == "__main__":
    unittest.main()
