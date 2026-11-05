"""Document gate contract: each substantive code change must keep three living specs in sync."""
import unittest
from tools.check_docs_updated import (
    check, latest_change_window, SPEC, PROMPT, HISTORICAL_PROMPT, SOIL_SPEC,
)

class WordSyncGateTests(unittest.TestCase):
    P = "docs/spec_updates/2026-11-05_v87_2_ci_contracts.md"
    WORKFLOW = "- " + P + "\n--entry " + P
    REQUIRED_DOCS = {PROMPT, HISTORICAL_PROMPT, SOIL_SPEC}

    def test_original_code_commit_may_use_active_word_bot(self):
        changed = {"desktop_app.py", self.P} | self.REQUIRED_DOCS
        self.assertEqual(check(changed, workflow_text=self.WORKFLOW, word_exists=True)[1], [])

    def test_all_three_documentation_files_are_required(self):
        base = {"desktop_app.py", self.P} | self.REQUIRED_DOCS
        for missing_file in self.REQUIRED_DOCS:
            with self.subTest(missing_file=missing_file):
                changed = base - {missing_file}
                self.assertIn(missing_file, check(changed,
                    workflow_text=self.WORKFLOW, word_exists=True)[1])

    def test_checkpoint_and_word_both_mandatory(self):
        self.assertIn(SPEC, check({"desktop_app.py"} | self.REQUIRED_DOCS,
            workflow_text=self.WORKFLOW, word_exists=True)[1])
        self.assertIn(SPEC, check({"desktop_app.py", self.P} | self.REQUIRED_DOCS,
            workflow_text="", word_exists=True)[1])
        self.assertIn(SPEC, check({"desktop_app.py", self.P} | self.REQUIRED_DOCS,
            workflow_text=self.WORKFLOW, word_exists=False)[1])

    def test_later_documentation_satisfies_latest_code_change(self):
        commits = [
            {"desktop_app.py"},
            {PROMPT, HISTORICAL_PROMPT, SOIL_SPEC, self.P},
        ]
        changed = latest_change_window(commits)
        self.assertEqual(check(changed, workflow_text=self.WORKFLOW, word_exists=True)[1], [])

    def test_older_documents_do_not_certify_new_code(self):
        commits = [
            {PROMPT, HISTORICAL_PROMPT, SOIL_SPEC, self.P, SPEC},
            {"desktop_app.py"},
        ]
        changed = latest_change_window(commits)
        self.assertIn(PROMPT, check(changed, workflow_text=self.WORKFLOW, word_exists=True)[1])
        self.assertIn(SPEC, check(changed, workflow_text=self.WORKFLOW, word_exists=True)[1])

    def test_documentation_only_or_word_bot_commit_needs_no_rebuild(self):
        self.assertEqual(latest_change_window([{SPEC}, {PROMPT}]), set())

    def test_another_code_change_requires_newer_documentation(self):
        changed = latest_change_window([
            {"desktop_app.py"},
            {PROMPT, HISTORICAL_PROMPT, SOIL_SPEC, self.P},
            {"tests/test_car_kml_map_setup_regression.py"},
        ])
        self.assertIn(SOIL_SPEC, check(changed, workflow_text=self.WORKFLOW, word_exists=True)[1])

    def test_same_commit_word_still_valid(self):
        changed = {"desktop_app.py", SPEC} | self.REQUIRED_DOCS
        self.assertEqual(check(changed, workflow_text="", word_exists=True)[1], [])

if __name__ == "__main__":
    unittest.main()
