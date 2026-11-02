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

    def test_dashboard_uses_exact_pr_head_sha_not_synthetic_merge(self):
        src = (ROOT / ".github/workflows/dashboard-dual-tests.yml").read_text(encoding="utf-8")
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", src)
        self.assertIn("persist-credentials: false", src)
        self.assertIn("if ($sourceSha -ne $expectedSha)", src)
        self.assertIn("Dashboard checkout SHA mismatch", src)
        self.assertIn("Verify dashboard tests use exact branch source SHA", src)

    def test_ifn_harvest_imports_shared_identity_as_module(self):
        src = (ROOT / ".github/workflows/harvest-ifn-field-data.yml").read_text(encoding="utf-8")
        self.assertIn("python -m tools.harvest_ifn_field_data", src)
        self.assertIn('sys.executable, "-m", "tools.prepare_ifn_agb_candidates"', src)
        self.assertIn("tools/ifn_state_identity.py", src)
        self.assertNotIn("python tools/harvest_ifn_field_data.py", src)

    def test_release_gate_is_strict(self):
        src = (ROOT / ".github/workflows/scientific-release-gate.yml").read_text(encoding="utf-8")
        self.assertIn("tools/scientific_release_gate.py", src)
        self.assertIn("validation/release_evidence.json", src)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", src)
        self.assertIn("if: always()", src)

if __name__ == "__main__":
    unittest.main()


class IFNIBGEWorkflowScopeTests(unittest.TestCase):
    def test_spatial_workflow_acquires_only_required_official_panels(self):
        src = (ROOT / ".github/workflows/ifn-ibge-spatial-sensitivity.yml").read_text(encoding="utf-8")
        self.assertIn('required = {"ifn_painel_biomassa_2026", "ifn_painel_arvores_mortas_2026"}', src)
        self.assertIn("--registry ifn_panel_sources.json", src)
        self.assertIn('if {row["id"] for row in selected} != required:', src)
        self.assertIn("IFN panels with integrity audit", src)
