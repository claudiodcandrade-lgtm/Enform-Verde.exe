import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import desktop_app


class _GeoFrame(list):
    @property
    def empty(self):
        return not self


class AcceptanceProgressDiagnosticsTests(unittest.TestCase):
    def test_acceptance_records_stage_progress_and_summary(self):
        fixture = _GeoFrame([object()])
        result = {
            "audit": {
                "processed_without_agb": [{"stats": [{"n": 4}]}],
                "published_inventory_evidence": {"agb_references": []},
            },
            "stats": [],
            "agb_mg_ha": 75.0,
            "literature_reference": {},
            "data_origin": "SAR_TEST_FIXTURE",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(desktop_app, "read_vector", return_value=fixture),
                patch.object(desktop_app, "geom_metrics", return_value={"area_ha": 1.0}),
                patch.object(desktop_app, "automatic_pipeline", return_value=result),
                patch.object(desktop_app.tempfile, "gettempdir", return_value=tmp),
            ):
                summary = desktop_app.acceptance_test("fixture.kmz")

            progress = Path(tmp, "enform_verde_acceptance_progress.txt").read_text(
                encoding="utf-8"
            )
            stages = [json.loads(line)["stage"] for line in progress.splitlines()]
            self.assertEqual(
                stages,
                [
                    "START",
                    "READ_AOI_BEGIN",
                    "READ_AOI_DONE",
                    "GEOMETRY_METRICS_BEGIN",
                    "GEOMETRY_METRICS_DONE",
                    "AUTOMATIC_PIPELINE_BEGIN",
                    "AUTOMATIC_PIPELINE_DONE",
                ],
            )
            self.assertEqual(summary["pixel_count"], 4)
            saved = json.loads(
                Path(tmp, "enform_verde_acceptance_result.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(saved["agb_status"], "ESTIMATIVA_QUANTITATIVA_DISPONIVEL")


if __name__ == "__main__":
    unittest.main()
