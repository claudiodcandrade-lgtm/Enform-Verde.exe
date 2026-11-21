import unittest
import pandas as pd
from crop_yield_modeling import (_add_historical_yield_features, _check_source_provenance,
                                 _cluster_bootstrap_ci, _feature_columns, _finite_quantile)


class CropYieldModelingContracts(unittest.TestCase):
    def _frame(self):
        return pd.DataFrame({
            "sar_crop_probability": [0.9], "sar_vigor_integral": [1.0],
            "sar_stress_anomaly_z": [0.2], "climate_precip_total": [100.0],
            "yield_lag_1_t_ha": [3.0],
        })

    def test_feature_schema_requires_sar_crop_vigor_stress_and_weather(self):
        frame = self._frame()
        cols = _feature_columns(frame)
        self.assertEqual(len(cols), 5)
        missing = self._frame().drop(columns=["sar_stress_anomaly_z"])
        with self.assertRaisesRegex(ValueError, "stress anomaly"):
            _feature_columns(missing)

    def test_height_feature_requires_validation_and_does_not_replace_vigor(self):
        frame=self._frame().assign(sar_height_mean_m=[1.2],sar_height_validated=[False])
        with self.assertRaisesRegex(ValueError,"independently validated"):
            _feature_columns(frame)
        frame["sar_height_validated"]=True
        self.assertIn("sar_height_mean_m",_feature_columns(frame))
        frame=frame.drop(columns=["sar_vigor_integral"],errors="ignore")
        with self.assertRaisesRegex(ValueError,"vigor/phenology"):
            _feature_columns(frame)

    def test_split_conformal_rank_is_conservative(self):
        self.assertEqual(_finite_quantile([1, 2, 3, 4, 5], 0.80), 5.0)

    def test_yield_lags_never_bridge_missing_seasons(self):
        frame = pd.DataFrame({
            "municipality_code": ["A", "A", "A"],
            "season_year": [2019, 2021, 2022],
            "yield_t_ha": [3.0, 4.0, 4.5],
        })
        result = _add_historical_yield_features(frame)
        self.assertTrue(pd.isna(result.loc[1, "yield_lag_1_t_ha"]))
        self.assertEqual(result.loc[2, "yield_lag_1_t_ha"], 4.0)
        self.assertTrue(pd.isna(result.loc[2, "yield_lag_2_t_ha"]))

    def test_cluster_bootstrap_requires_multiple_spatial_blocks(self):
        frame = pd.DataFrame({"spatial_block": ["one", "one"], "value": [0.0, 1.0]})
        with self.assertRaisesRegex(ValueError, "five held-out spatial blocks"):
            _cluster_bootstrap_ci(frame, "value")

    def test_mapbiomas_yield_labels_cannot_validate(self):
        frame = pd.DataFrame({
            "yield_source_url": ["https://mapbiomas.org/map"],
            "yield_license": ["CC-BY"],
            "sar_source_url": ["https://example.org/sar"],
            "weather_source": ["NASA POWER"],
            "weather_source_url": ["https://power.larc.nasa.gov"],
            "sar_crop_validated": [True], "sar_vigor_validated": [True],
            "sar_stress_validated": [True],
        })
        with self.assertRaisesRegex(ValueError, "pseudo-labels"):
            _check_source_provenance(frame)


if __name__ == "__main__":
    unittest.main()
