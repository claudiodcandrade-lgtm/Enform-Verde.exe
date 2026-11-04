"""The approved visual standard must be preserved in every new version.

Compares the live application shell and static visual assets with
validation/ui_visual_baseline.json. A deliberate visual change requires
`python ui_visual_standard.py --update` AND a documented entry in the
technical specification (see docs/PADRAO_VISUAL_ENFORM_VERDE.md).
"""
import json
import unittest

import ui_visual_standard as uvs


class VisualStandardTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads(uvs.BASELINE.read_text(encoding="utf-8"))

    def test_static_assets_and_palettes_unchanged(self):
        cur = json.loads(json.dumps(uvs.static_snapshot(), ensure_ascii=False))
        self.assertEqual(uvs.diff(self.baseline["static"], cur), [])

    def test_application_shell_unchanged(self):
        try:
            snap = uvs.capture()
        except Exception as exc:  # no display available (headless Linux without Xvfb)
            if "display" in str(exc).lower():
                self.skipTest("sem display gráfico: " + str(exc))
            raise
        self.assertEqual(uvs.diff(self.baseline["shell"], snap["shell"]), [])

    def test_header_has_no_text_overlay_and_one_image(self):
        h = self.baseline["shell"]["header"]
        self.assertEqual((h["text_overlays"], h["image_items"]), (0, 1))

    def test_diff_detects_a_change(self):
        changed = json.loads(json.dumps(self.baseline))
        changed["static"]["palette"]["ORANGE"] = "#000000"
        self.assertTrue(uvs.diff(self.baseline, changed))


if __name__ == "__main__":
    unittest.main()
