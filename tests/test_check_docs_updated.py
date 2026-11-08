"""Documentation rule: code changes require spec (.docx) and continuity prompt updates."""
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_docs_updated as c  # noqa: E402


class DocsRuleTests(unittest.TestCase):
    def test_code_change_without_docs_fails(self):
        _, missing = c.check({"crop_vigor.py"})
        self.assertEqual(set(missing), {c.SPEC, c.PROMPT, c.HISTORICAL_PROMPT, c.SOIL_SPEC})

    def test_code_change_with_both_docs_passes(self):
        self.assertEqual(c.check({"crop_vigor.py", c.SPEC, c.PROMPT, c.HISTORICAL_PROMPT, c.SOIL_SPEC})[1], [])

    def test_docs_only_change_passes(self):
        self.assertEqual(c.check({"docs/x.md"})[1], [])

    def test_versioned_spec_is_valid_docx_with_current_update(self):
        z = zipfile.ZipFile(ROOT / c.SPEC)
        xml = z.read("word/document.xml").decode("utf-8")
        import re
        ver = re.search(r'^APP_VERSION="([^"]+)"', (ROOT / "desktop_app.py").read_text(encoding="utf-8"), re.M).group(1)
        self.assertIn(ver, xml)


if __name__ == "__main__":
    unittest.main()
