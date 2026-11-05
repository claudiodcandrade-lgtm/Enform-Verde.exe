"""Document gate contract: each substantive code change must keep three living specs in sync."""
import unittest
from tools.check_docs_updated import (
    check, SPEC, PROMPT, HISTORICAL_PROMPT, SOIL_SPEC,
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

    def test_same_commit_word_still_valid(self):
        changed = {"desktop_app.py", SPEC} | self.REQUIRED_DOCS
        self.assertEqual(check(changed, workflow_text="", word_exists=True)[1], [])

if __name__ == "__main__":
    unittest.main()
