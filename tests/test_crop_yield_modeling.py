import unittest
import pandas as pd
from crop_yield_modeling import _check_source_provenance, _feature_columns, _finite_quantile


class CropYieldModelingContracts(unittest.TestCase):
    def _frame(self):
        return pd.DataFrame({
            "sar_crop_probability": [0.9], "sar_vigor_integral": [1.0],
            "sar_stress_anomaly_z": [0.2], "climate_precip_total": [100.0],
        })

    def test_feature_schema_requires_sar_crop_vigor_stress_and_weather(self):
        frame = self._frame()
        cols = _feature_columns(frame)
        self.assertEqual(len(cols), 4)
        missing = self._frame().drop(columns=["sar_stress_anomaly_z"])
        with self.assertRaisesRegex(ValueError, "stress anomaly"):
            _feature_columns(missing)

    def test_split_conformal_rank_is_conservative(self):
        self.assertEqual(_finite_quantile([1, 2, 3, 4, 5], 0.80), 5.0)

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
