"""ESA MAAP: 90-day date reminder, privacy, GUI integration."""
import ast
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import esa_maap_token_renewal as renewal

ROOT=Path(__file__).resolve().parents[1]


class MAAPRenewalTests(unittest.TestCase):
    def test_exact_90_day_boundary_and_15_day_warning(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"renewal.json"
            issued=date.today()-timedelta(days=75)
            renewal.save_renewal_date(issued,path=p)
            s=renewal.renewal_status(path=p,today=issued+timedelta(days=75))
            self.assertEqual(s["state"],"EXPIRING_SOON")
            self.assertEqual(s["days_remaining"],15)
            s=renewal.renewal_status(path=p,today=issued+timedelta(days=90))
            self.assertEqual(s["state"],"EXPIRED")
            self.assertEqual(s["days_remaining"],0)

    def test_unknown_date_does_not_claim_validity(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(renewal.renewal_status(path=Path(td)/"absent")["state"],"UNKNOWN")

    def test_only_issue_date_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"renewal.json"
            renewal.save_renewal_date(date.today(),path=p)
            doc=json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(set(doc),{"schema","issued_on","validity_days"})
            self.assertNotIn("token",p.read_text(encoding="utf-8").lower())

    def test_protected_token_input_and_renewal_controls_in_app(self):
        src=(ROOT/"desktop_app.py").read_text(encoding="utf-8")
        ast.parse(src)
        for required in (
            'self.maap_token_input=ttk.Entry(edl,textvariable=self.esa_token,show="•"',
            'text="RENOVAR TOKEN NO PORTAL ESA"',
            'text="SUBSTITUIR TOKEN"',
            'text="REGISTRAR DATA DE EMISSÃO / RENOVAÇÃO"',
            "self.esa_token.set(\"\")",
            "self.after(1600,self._check_maap_token_renewal)",
        ):
            self.assertIn(required,src)


if __name__=="__main__":
    unittest.main()
