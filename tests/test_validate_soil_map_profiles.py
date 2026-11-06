"""Soil 0–100 cm map validation tool — synthetic profiles only (not evidence)."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import validate_soil_map_profiles as v  # noqa: E402
import modular_scientific_gate as gate  # noqa: E402


def lay(u, l, c, bd, cf=0.0):
    return {"upper_cm": u, "lower_cm": l, "soc_g_kg": c, "bd_g_cm3": bd, "cf_frac": cf}


class StockTests(unittest.TestCase):
    def test_stock_formula_and_clipping(self):
        # 10 g/kg × 1.2 g/cm³ × 100 cm × 0.1 = 120 Mg C/ha; layer beyond 100 cm clipped
        self.assertAlmostEqual(v.profile_stock_0_100([lay(0, 40, 10, 1.2), lay(40, 130, 10, 1.2)]), 120.0)
        self.assertAlmostEqual(v.profile_stock_0_100([lay(0, 100, 10, 1.0, cf=.5)]), 50.0)

    def test_gap_shallow_or_invalid_bd_is_rejected(self):
        self.assertIsNone(v.profile_stock_0_100([lay(0, 30, 10, 1.2), lay(40, 100, 10, 1.2)]))
        self.assertIsNone(v.profile_stock_0_100([lay(0, 60, 10, 1.2)]))
        self.assertIsNone(v.profile_stock_0_100([lay(0, 100, 10, 9.0)]))


def pairs(noise=0.0, n_blocks=12, per=3):
    out = []
    for b in range(n_blocks):
        for k in range(per):
            obs = 60 + 5 * b + k
            out.append({"profile_id": f"p{b}_{k}", "dataset_id": "D1", "lon": -60 + 2 * b + .1 * k,
                        "lat": -10 + .1 * k, "obs": obs, "pred": obs * (1 + noise * ((-1) ** k))})
    return out


class ValidationTests(unittest.TestCase):
    def test_perfect_map(self):
        r = v.validate(pairs())
        self.assertAlmostEqual(r["rmse"], 0.0); self.assertEqual(r["interval_coverage"], 1.0)
        self.assertEqual(r["independent_sample_count"], r["test_spatial_units"])
        self.assertFalse(set(r["train_spatial_unit_ids"]) & set(r["test_spatial_unit_ids"]))
        self.assertEqual(r["status"], "diagnostic_not_independent")

    def test_independence_requires_sourced_declaration(self):
        r = v.validate(pairs(.1), independence={"D1": {"used_in_map_training": False}})
        self.assertEqual(r["status"], "diagnostic_not_independent")
        r = v.validate(pairs(.1), independence={"D1": {"used_in_map_training": False, "source": "carta Embrapa"}})
        self.assertEqual(r["status"], "independent_validation")
        self.assertGreater(r["rmse"], 0)

    def test_too_few_profiles(self):
        self.assertEqual(v.validate(pairs()[:5])["status"], "insufficient")

    def test_report_satisfies_modular_gate_only_when_independent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "data.csv").write_text("x\n1\n")
            ds = hashlib.sha256((root / "data.csv").read_bytes()).hexdigest()
            rep = v.validate(pairs(.1), independence={"D1": {"used_in_map_training": False, "source": "x"}})
            rep["dataset_sha256"] = ds
            (root / "rep.json").write_text(json.dumps(rep))
            rs = hashlib.sha256((root / "rep.json").read_bytes()).hexdigest()
            row = {"biome": "Cerrado", "pool": "soil_0_100", "fitofisionomia": "Savana", "status": "validated",
                   "evidence_type": "independent_real_data", "source_url": "https://x", "dataset_sha256": ds,
                   "dataset_file": "data.csv", "validation_report": "rep.json", "validation_report_sha256": rs,
                   "uncertainty_kind": "split-conformal", "domain": "Cerrado", "transfer_error_method": "blocos",
                   "depth_cm": [0, 100]}
            res = gate.assess({"source_sha": "a" * 40, "capabilities": [row]}, "a" * 40, root)
            self.assertTrue(res["passed"], res["errors"])


if __name__ == "__main__":
    unittest.main()
