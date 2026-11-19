"""Regression coverage for namespace-prefixed Word specification updates."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from update_spec_docx import update  # noqa: E402


class UpdateSpecDocxTests(unittest.TestCase):
    def test_updates_fh_dashboard_cover_state_label(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
 <w:body>
  <w:p><w:r><w:t>Enform Verde</w:t></w:r></w:p>
  <w:p><w:r><w:t>FH→PAINEL LOCAL: TESTE LOCAL PASSOU; BUILD PENDENTE</w:t></w:r></w:p>
  <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Especificação antiga</w:t></w:r></w:p>
 </w:body>
</w:document>'''
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.docx"
            output = Path(td) / "output.docx"
            with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", xml)
            report = update(source, output, "# V88.169 teste\\nConteúdo\\n",
                            baseline="c12ed76", head_sha="abc123",
                            code_sha="def456", date="19 de novembro de 2026",
                            cover_state="FH REAL SINOP→DASHBOARD OK; GATE GUI CORRIGIDO")
            self.assertTrue(report["cover_state"])
            with zipfile.ZipFile(output) as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = " ".join(node.text or "" for node in document.findall(".//w:t", ns))
            self.assertIn("FH REAL SINOP→DASHBOARD OK; GATE GUI CORRIGIDO", text)
            self.assertNotIn("TESTE LOCAL PASSOU", text)

class UpdateSpecDocxTests(unittest.TestCase):
    def test_namespace_prefixed_document_keeps_entry_inside_word_body(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<ns0:document xmlns:ns0="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
 <ns0:body>
  <ns0:p><ns0:r><ns0:t>Estado vigente — candidata 3.26.29</ns0:t></ns0:r></ns0:p>
  <ns0:p><ns0:r><ns0:t>CANDIDATA PRÉ-CAMPO EXPERIMENTAL; versão antiga</ns0:t></ns0:r></ns0:p>
  <ns0:p><ns0:r><ns0:t>V88.162 | 3.26.73-PRECAMPO-EXPERIMENTAL</ns0:t></ns0:r></ns0:p>
  <ns0:tbl><ns0:tr>
   <ns0:tc><ns0:p><ns0:r><ns0:t>SHA atual do código</ns0:t></ns0:r></ns0:p></ns0:tc>
   <ns0:tc><ns0:p><ns0:r><ns0:t>versão antiga</ns0:t></ns0:r></ns0:p></ns0:tc>
  </ns0:tr></ns0:tbl>
  <ns0:p><ns0:pPr><ns0:pStyle ns0:val="Heading1"/></ns0:pPr><ns0:r><ns0:t>Especificação antiga</ns0:t></ns0:r></ns0:p>
 </ns0:body>
</ns0:document>'''
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.docx"
            output = Path(td) / "output.docx"
            with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", xml)
            report = update(source, output, "# V88.45 teste\n## Seção\nConteúdo\n",
                            baseline="candidata 3.26.31", head_sha="abc123",
                            code_sha="def456", date="13 de novembro de 2026",
                            cover_state="CANDIDATA PRÉ-CAMPO EXPERIMENTAL; BUILD PENDENTE",
                            cover_version="V88.167 | 3.26.77-PRECAMPO-EXPERIMENTAL")
            self.assertTrue(report["control_sha"])
            self.assertTrue(report["cover_state"])
            self.assertTrue(report["cover_version"])
            with zipfile.ZipFile(output) as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = " ".join(node.text or "" for node in document.findall(".//w:t", ns))
            self.assertIn("V88.45 teste", text)
            self.assertIn("def456", text)
            self.assertIn("BUILD PENDENTE", text)
            self.assertIn("V88.167 | 3.26.77-PRECAMPO-EXPERIMENTAL", text)
            self.assertNotIn("<w:p>", text)
            refreshed = Path(td) / "refreshed.docx"
            second = update(output, refreshed,
                            "# V88.45 teste\n## Seção revisada\nConteúdo atualizado\n",
                            baseline="candidata 3.26.31", head_sha="abc123",
                            code_sha="def456", date="13 de novembro de 2026")
            self.assertFalse(second["entry_inserted"])
            self.assertTrue(second["entry_refreshed"])
            with zipfile.ZipFile(refreshed) as archive:
                second_doc = ET.fromstring(archive.read("word/document.xml"))
            second_text = " ".join(node.text or "" for node in second_doc.findall(".//w:t", ns))
            self.assertEqual(second_text.count("V88.45 teste"), 1)
            self.assertIn("Conteúdo atualizado", second_text)
            self.assertNotIn("Conteúdo\n", second_text)


if __name__ == "__main__":
    unittest.main()
