"""Prevent GitHub PR merge SHA from silently masquerading as a release build SHA."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkflowProvenanceTests(unittest.TestCase):
    def test_windows_build_checks_out_exact_head(self):
        src = (ROOT / ".github/workflows/build-windows.yml").read_text(encoding="utf-8")
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", src)
        self.assertIn("if ($sourceSha -ne $expectedSha)", src)
        self.assertIn("Expected source SHA from branch/PR: $expectedSha", src)
        self.assertIn("Clean-folder EXE UI smoke", src)
        self.assertNotIn("$env:GITHUB_EVENT_NAME -ne 'pull_request'", src)

    def test_release_gate_is_strict(self):
        src = (ROOT / ".github/workflows/scientific-release-gate.yml").read_text(encoding="utf-8")
        self.assertIn("tools/scientific_release_gate.py", src)
        self.assertIn("validation/release_evidence.json", src)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", src)
        self.assertIn("if: always()", src)

if __name__ == "__main__":
    unittest.main()
