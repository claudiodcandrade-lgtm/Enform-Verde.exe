"""Synthetic contract fixtures, NOT independent scientific observations."""
import copy
import unittest

from tools.materialize_release_evidence import PLACEHOLDER, materialize
from tools.scientific_release_gate import SECTIONS

SHA="a"*40


def evidence_template():
    return {
        **{key: ([] if key in ("biomes","carbon") else None) for key in SECTIONS},
        "source_sha":PLACEHOLDER,
        "metadata":{"note":"synthetic fixture, no real evidence"},
    }


class MaterializeReleaseEvidenceTests(unittest.TestCase):
    def test_only_source_sha_is_inserted_without_mutating_source(self):
        template=evidence_template()
        original=copy.deepcopy(template)
        out=materialize(template,SHA)
        self.assertEqual(template,original)
        self.assertEqual(out["source_sha"],SHA)
        self.assertEqual(out["metadata"],template["metadata"])
        for section in SECTIONS:
            self.assertEqual(out[section],template[section])
        self.assertIsNone(out["sar"])
        self.assertEqual(out["carbon"],[])

    def test_missing_section_never_becomes_fabricated_evidence(self):
        template=evidence_template()
        template.pop("soil",None)
        template.pop("carbon")
        with self.assertRaisesRegex(ValueError,"lacks required sections"):
            materialize(template,SHA)

    def test_stale_sha_is_rejected(self):
        template=evidence_template()
        template["source_sha"]="b"*40
        with self.assertRaisesRegex(ValueError,"stale"):
            materialize(template,SHA)

    def test_source_sha_cannot_be_nonhex_or_truncated(self):
        for bad in ("bad","x"*40,"a"*39,"a"*41,123,None):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,"40 hexadecimal"):
                materialize(evidence_template(),bad)

    def test_template_without_sha_placeholder_is_supported(self):
        template=evidence_template()
        del template["source_sha"]
        self.assertEqual(materialize(template,SHA)["source_sha"],SHA)

    def test_non_object_template_is_rejected(self):
        for bad in (None,[],42,"template"):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,"JSON object"):
                materialize(bad,SHA)

    def test_json_nan_cannot_enter_runtime_manifest(self):
        template=evidence_template()
        template["metadata"]["invalid"]=float("nan")
        with self.assertRaises(ValueError):
            materialize(template,SHA)


if __name__=="__main__":
    unittest.main()
