"""Every shipped and live-tested SAR classifier must use its serialized runtime."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModelRuntimePinningTests(unittest.TestCase):
    def test_all_runtime_installers_match_model_manifest(self):
        expected = 'scikit-learn==1.8.0'
        requirements = (ROOT / 'requirements_desktop.txt').read_text(encoding='utf-8')
        self.assertIn(expected, requirements)
        for rel in (
            '.github/workflows/dashboard-dual-tests.yml',
            '.github/workflows/sinop-sar-experimental-live.yml',
        ):
            with self.subTest(workflow=rel):
                self.assertIn(expected, (ROOT / rel).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
