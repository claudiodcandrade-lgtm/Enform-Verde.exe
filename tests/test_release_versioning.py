"""Every new version must produce a Windows EXE package named from APP_VERSION."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "build-windows.yml"


def app_version():
    m = re.search(r'^APP_VERSION="([^"]+)"', (ROOT / "desktop_app.py").read_text(encoding="utf-8"), re.M)
    return m.group(1)


class ReleaseVersioningTests(unittest.TestCase):
    def test_version_format_and_release_notes_exist(self):
        ver = app_version()
        self.assertRegex(ver, r"^\d+\.\d+\.\d+(-[A-Z0-9-]+)?$")
        self.assertTrue((ROOT / f"APP_RELEASE_NOTES_v{ver.split('-')[0]}.md").is_file())

    def test_artifact_and_release_derive_from_app_version(self):
        text = WF.read_text(encoding="utf-8")
        # parse without PyYAML (not a runtime dependency)
        self.assertEqual(text.count("path: dist/Enform Verde/"), 1)
        block = text[text.index("path: dist/Enform Verde/") - 200:text.index("path: dist/Enform Verde/")]
        self.assertIn("name: Enform-Verde-Windows-v${{ env.APP_VERSION }}", block)
        self.assertIn("\n  publish-release:\n", text)
        self.assertIn("contents: write", text[text.index("publish-release:"):])
        self.assertIn("--module-check", text)
        self.assertIn("--visual-check", text)
        self.assertIn('validation/ui_visual_baseline.json;validation', text)
        self.assertNotRegex(text, r"VERSÃO \d+\.\d+\.\d+")          # no hard-coded version in LEIA-ME
        for mod in ("pronasolos_wcs", "crop_forecast_pipeline", "crop_vigor"):
            self.assertIn("--hidden-import " + mod, text)


if __name__ == "__main__":
    unittest.main()
