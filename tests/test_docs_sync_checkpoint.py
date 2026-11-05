import unittest
from tools.check_docs_updated import check,SPEC,PROMPT
class WordSyncGateTests(unittest.TestCase):
    P="docs/spec_updates/2026-11-04_v80_national_audit.md"
    WORKFLOW="- "+P+"\n--entry "+P
    def test_original_code_commit_may_use_active_word_bot(self):
        self.assertEqual(check({"desktop_app.py",PROMPT,self.P},workflow_text=self.WORKFLOW,word_exists=True)[1],[])
    def test_must_have_prompt_and_checkpoint(self):
        self.assertTrue(check({"desktop_app.py",self.P},workflow_text=self.WORKFLOW,word_exists=True)[1])
        self.assertTrue(check({"desktop_app.py",PROMPT},workflow_text=self.WORKFLOW,word_exists=True)[1])
    def test_checkpoint_must_be_tied_to_active_word_workflow(self):
        self.assertTrue(check({"desktop_app.py",PROMPT,self.P},workflow_text="",word_exists=True)[1])
        self.assertTrue(check({"desktop_app.py",PROMPT,self.P},workflow_text=self.WORKFLOW,word_exists=False)[1])
    def test_same_commit_word_still_valid(self):
        self.assertEqual(check({"desktop_app.py",PROMPT,SPEC},workflow_text="",word_exists=True)[1],[])
if __name__=="__main__":unittest.main()
