"""Offline verification of the 2026 SFB field-evidence acquisition route."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.harvest_ifn_field_data import PANEL_RESOURCES, harvest_sfb_2026_panel


class Reply:
    def __init__(self, *, text="", body=b""):
        self.text = text
        self.content = body

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, license_ok=True, html_csv=False):
        self.license_ok = license_ok
        self.html_csv = html_csv
        self.urls = []

    def get(self, url, timeout=None):
        self.urls.append(url)
        if "dataset/painel-de-biomassa-e-carbono" in url:
            return Reply(text=("Creative Commons Attribution 4.0"
                               if self.license_ok else "no declared license"))
        if self.html_csv:
            return Reply(body=b"<!doctype html><html>access denied</html>")
        return Reply(body=("bioma;ua;necromassa_t_por_ha\n"
                           "Amazônia;UA001;2.3\n").encode("utf-8"))


class SFBPanelHarvestTests(unittest.TestCase):
    def test_cc_by_records_archived_with_hash_and_not_homologated(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            session = Session()
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(session, report)
            self.assertEqual(set(report["datasets"]), set(PANEL_RESOURCES))
            self.assertEqual(report["failures"], [])
            for name in PANEL_RESOURCES:
                item = report["datasets"][name]
                self.assertEqual(item["status"], "harvested_not_validated")
                row = item["resources"][0]
                self.assertEqual(row["unique_ua_by_biome"]["Amazônia"], 1)
                blob = Path(tmp, name, row["filename"]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), row["sha256"])
                self.assertEqual(row["bytes"], len(blob))

    def test_missing_license_stops_download(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            session = Session(license_ok=False)
            harvest_sfb_2026_panel(session, report)
            self.assertEqual(len(session.urls), 1)
            self.assertEqual(report["datasets"], {})
            self.assertTrue(any("license" in error for error in report["failures"]))

    def test_html_failure_never_claims_harvest(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "tools.harvest_ifn_field_data.OUT", Path(tmp)):
            report = {"datasets": {}, "failures": []}
            harvest_sfb_2026_panel(Session(html_csv=True), report)
            self.assertEqual(len(report["failures"]), len(PANEL_RESOURCES))
            self.assertTrue(all(item["status"] == "access_or_schema_error"
                                for item in report["datasets"].values()))


if __name__ == "__main__":
    unittest.main()
