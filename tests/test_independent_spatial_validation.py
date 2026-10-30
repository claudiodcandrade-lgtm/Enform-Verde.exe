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

    def test_disallow_spatial_leakage(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            self.validate(VALID.replace("test,B", "test,A"))

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
