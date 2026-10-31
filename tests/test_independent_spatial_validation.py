import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.independent_spatial_validation import validate_csv

HEADER = "observed,predicted,lower,upper,partition,spatial_unit\n"
VALID = HEADER + "1,1,0,2,train,A\n2,3,1,4,test,B\n4,3,2,5,test,C\n"

class SpatialValidationTests(unittest.TestCase):
    def validate(self, content, sha=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "plots.csv"
            data = content.encode()
            path.write_bytes(data)
            return validate_csv(path, sha or hashlib.sha256(data).hexdigest(), "Mg/ha")

    def test_recompute_metrics_and_coverage(self):
        result = self.validate(VALID)
        self.assertEqual(result["independent_sample_count"], 2)
        self.assertAlmostEqual(result["rmse"], 1)
        self.assertAlmostEqual(result["mae"], 1)
        self.assertAlmostEqual(result["bias"], 0)
        self.assertEqual(result["interval_coverage"], 1)

    def test_repeated_test_rows_count_spatial_units_not_pseudoreplicated_plots(self):
        # A third measured row is in the same physical test cluster B (alias b).
        # It must not increase the number of independent spatial units.
        result = self.validate(VALID + "6,7,5,8,test,b\n")
        self.assertEqual(result["independent_sample_count"], 2)
        self.assertEqual(result["test_observation_count"], 3)
        self.assertEqual(result["test_spatial_units"], 2)
        self.assertEqual(result["interval_n_nominal"], 3)
        self.assertEqual(result["interval_independent_spatial_unit_count"], 2)
        self.assertAlmostEqual(result["rmse"], 1.0)
        self.assertIn("observation", result["metric_weighting"])

    def test_cluster_equal_weight_metrics_match_when_one_row_per_unit(self):
        result = self.validate(VALID)
        self.assertAlmostEqual(result["cluster_equal_weight_rmse"], result["rmse"])
        self.assertAlmostEqual(result["cluster_equal_weight_mae"], result["mae"])
        self.assertAlmostEqual(result["cluster_equal_weight_bias"], result["bias"])
        self.assertAlmostEqual(result["cluster_equal_weight_interval_coverage"], result["interval_coverage"])

    def test_cluster_equal_weight_metrics_do_not_overweight_repeated_plots(self):
        # B contributes two rows, C one; B/b must remain one physical unit.
        result = self.validate(VALID + "6,10,9,11,test,b\n")
        self.assertEqual(result["independent_sample_count"], 2)
        self.assertEqual(result["test_observation_count"], 3)
        self.assertAlmostEqual(result["rmse"], (6.0) ** 0.5)
        self.assertAlmostEqual(result["cluster_equal_weight_rmse"], (4.75) ** 0.5)
        self.assertAlmostEqual(result["cluster_equal_weight_mae"], 1.75)
        self.assertAlmostEqual(result["cluster_equal_weight_bias"], 0.75)
        self.assertAlmostEqual(result["interval_coverage"], 2.0 / 3.0)
        self.assertAlmostEqual(result["cluster_equal_weight_interval_coverage"], 0.75)
        self.assertIn("no cluster-robust CI", result["cluster_metric_weighting"])

    def test_disallow_spatial_leakage(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            self.validate(VALID.replace("test,B", "test,A"))

    def test_disallow_case_alias_leakage(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            self.validate(VALID.replace("test,B", "test,a"))

    def test_disallow_unicode_width_alias_leakage(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            self.validate(VALID.replace("test,B", "test,Ａ"))

    def test_disallow_case_alias_pseudoreplication(self):
        with self.assertRaisesRegex(ValueError, "distinct test spatial units"):
            self.validate(VALID.replace("test,C", "test,b"))

    def test_disallow_pseudoreplication_in_one_test_spatial_unit(self):
        with self.assertRaisesRegex(ValueError, "distinct test spatial units"):
            self.validate(VALID.replace("test,C", "test,B"))

    def test_duplicate_csv_header_is_rejected(self):
        malformed = VALID.replace("partition,spatial_unit\n", "partition,spatial_unit,spatial_unit\n")
        with self.assertRaisesRegex(ValueError, "duplicate or blank CSV headers"):
            self.validate(malformed)

    def test_unexpected_extra_csv_columns_are_rejected(self):
        malformed = VALID.replace("test,B\n", "test,B,unexpected\n")
        with self.assertRaisesRegex(ValueError, "unexpected extra CSV columns"):
            self.validate(malformed)

    def test_disallow_tampered_raw_data(self):
        with self.assertRaisesRegex(ValueError, "sha256 mismatch"):
            self.validate(VALID, sha="0" * 64)

    def test_reject_invalid_intervals(self):
        with self.assertRaisesRegex(ValueError, "invalid prediction interval"):
            self.validate(VALID.replace("2,3,1,4", "2,3,4,1"))

    def test_missing_test_rows(self):
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.validate(VALID.replace("test,B", "train,B").replace("test,C", "train,C"))

    def test_nonfinite_measurements(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.validate(VALID.replace("2,3,1,4", "2,nan,1,4"))

if __name__ == "__main__":
    unittest.main()
