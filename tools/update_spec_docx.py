#!/usr/bin/env python3
"""Append a dated update to the Word technical specification (no reformatting).

Usage:
  python tools/update_spec_docx.py --docx docs/ESPECIFICACAO_TECNICA_COMPLETA.docx \
      --entry docs/spec_updates/2026-11-03_v3.26.0.md --version 3.26.0-SOLO-SAFRA \
      --baseline "..." --code-sha "..." --date "3 de novembro de 2026"

Entry markup (one item per line):  "# " Heading1 · "## " Heading2 · "- " bullet ·
"$$ " equation line · blank line ignored · anything else = normal paragraph.

The newest update is inserted right after the cover block (before the first
Heading1), so earlier sections are preserved as history. Cover lines
("Linha de base da revisão:", "SHA do HEAD documental:", "Revisão documental:")
and the control-table cell after "SHA atual do código" are replaced.
"""
from __future__ import annotations

import argparse
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

STYLE = {"# ": "Heading1", "## ": "Heading2", "- ": "ListBullet", "$$ ": "EquationBlock"}


def para(text, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else "<w:pPr/>"
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def entry_xml(markup):
    out = []
    for line in markup.splitlines():
        if not line.strip():
            continue
        for prefix, style in STYLE.items():
            if line.startswith(prefix):
                out.append(para(line[len(prefix):].strip(), style)); break
        else:
            out.append(para(line.strip()))
    return "".join(out)


def _replace_paragraph_text(xml, startswith, new_text):
    """Replace the whole text of the first paragraph whose text starts with ``startswith``."""
    for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S):
        p = m.group(0)
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
        if text.startswith(escape(startswith)) or text.startswith(startswith):
            ppr = re.search(r"<w:pPr>.*?</w:pPr>|<w:pPr/>", p, re.S)
            rpr = re.search(r"<w:rPr>.*?</w:rPr>|<w:rPr/>", p, re.S)
            newp = ("<w:p>" + (ppr.group(0) if ppr else "") + "<w:r>" + (rpr.group(0) if rpr else "")
                    + f'<w:t xml:space="preserve">{escape(new_text)}</w:t></w:r></w:p>')
            return xml[:m.start()] + newp + xml[m.end():], True
    return xml, False


def _replace_cell_after(xml, label, new_text):
    """Replace text of the table cell that follows the cell containing ``label``."""
    i = xml.find(f">{escape(label)}<")
    if i < 0:
        return xml, False
    tc_end = xml.find("</w:tc>", i)
    nxt = re.compile(r"<w:tc>.*?</w:tc>", re.S).search(xml, tc_end)
    if not nxt:
        return xml, False
    cell = nxt.group(0)
    count = {"n": 0}

    def sub(m):
        count["n"] += 1
        body = escape(new_text) if count["n"] == 1 else ""
        return '<w:t xml:space="preserve">' + body + "</w:t>"
    cell2 = re.sub(r"<w:t(?:\s[^>]*)?>[^<]*</w:t>", sub, cell)
    if count["n"] == 0:
        return xml, False
    return xml[:nxt.start()] + cell2 + xml[nxt.end():], True


def update(docx_in, docx_out, entry_markup, *, baseline, head_sha, code_sha, date,
           footer_label=None, footer_date=None):
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(docx_in) as z:
        names = z.namelist(); z.extractall(tmp)
    doc = tmp / "word" / "document.xml"
    xml = doc.read_text(encoding="utf-8")
    report = {}
    xml, report["baseline"] = _replace_paragraph_text(xml, "Linha de base da revisão:", "Linha de base da revisão: " + baseline)
    xml, report["head"] = _replace_paragraph_text(xml, "SHA do HEAD documental:", "SHA do HEAD documental: " + head_sha)
    xml, report["date"] = _replace_paragraph_text(xml, "Revisão documental:", "Revisão documental: " + date)
    xml, report["control_sha"] = _replace_cell_after(xml, "SHA atual do código", code_sha)
    # Legacy full specification versions may not contain a dedicated HEAD
    # paragraph. Add it before the first Heading1 rather than failing the
    # entire documentation synchronization or replacing the full document.
    if not report["head"]:
        first_h1 = xml.find('<w:pStyle w:val="Heading1"/>')
        at = xml.rfind("<w:p>", 0, first_h1) if first_h1 >= 0 else -1
        if at >= 0:
            xml = xml[:at] + para("SHA do HEAD documental: " + head_sha) + xml[at:]
            report["head"] = True
    first_h1 = xml.find('<w:pStyle w:val="Heading1"/>')
    p_start = xml.rfind("<w:p>", 0, first_h1)
    xml = xml[:p_start] + entry_xml(entry_markup) + xml[p_start:]
    doc.write_text(xml, encoding="utf-8")
    if footer_label or footer_date:
        for f in (tmp / "word").glob("footer*.xml"):
            fx = f.read_text(encoding="utf-8")
            if footer_label:
                fx = re.sub(r"SHA [0-9a-f]{7,40}", escape(footer_label), fx)
            if footer_date:
                fx = re.sub(r"\d{2}/\d{2}/\d{4}", footer_date, fx)
            f.write_text(fx, encoding="utf-8")
        report["footer"] = True
    out = Path(docx_out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(tmp / n, n)
    shutil.rmtree(tmp)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", required=True); ap.add_argument("--out")
    ap.add_argument("--entry", required=True); ap.add_argument("--baseline", required=True)
    ap.add_argument("--head-sha", required=True); ap.add_argument("--code-sha", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--footer-label"); ap.add_argument("--footer-date")
    a = ap.parse_args()
    out = a.out or a.docx
    r = update(a.docx, out + ".tmp", Path(a.entry).read_text(encoding="utf-8"), baseline=a.baseline,
               head_sha=a.head_sha, code_sha=a.code_sha, date=a.date,
               footer_label=a.footer_label, footer_date=a.footer_date)
    Path(out + ".tmp").replace(out)
    missing = [k for k, ok in r.items() if not ok]
    print({"updated": out, "replaced": r})
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
