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


def para(text, style=None, prefix="w:"):
    ppr = f'<{prefix}pPr><{prefix}pStyle {prefix}val="{style}"/></{prefix}pPr>' if style else f"<{prefix}pPr/>"
    return f'<{prefix}p>{ppr}<{prefix}r><{prefix}t xml:space="preserve">{escape(text)}</{prefix}t></{prefix}r></{prefix}p>'


def entry_xml(markup, prefix="w:"):
    out = []
    for line in markup.splitlines():
        if not line.strip():
            continue
        for marker, style in STYLE.items():
            if line.startswith(marker):
                out.append(para(line[len(marker):].strip(), style, prefix)); break
        else:
            out.append(para(line.strip(), prefix=prefix))
    return "".join(out)


def _replace_paragraph_text(xml, startswith, new_text, prefix="w:"):
    """Replace the whole text of the first paragraph whose text starts with ``startswith``."""
    tag = re.escape(prefix)
    for m in re.finditer(rf"<{tag}p[ >].*?</{tag}p>", xml, re.S):
        p = m.group(0)
        text = "".join(re.findall(rf"<{tag}t[^>]*>([^<]*)</{tag}t>", p))
        if text.startswith(escape(startswith)) or text.startswith(startswith):
            ppr = re.search(rf"<{tag}pPr>.*?</{tag}pPr>|<{tag}pPr/>", p, re.S)
            rpr = re.search(rf"<{tag}rPr>.*?</{tag}rPr>|<{tag}rPr/>", p, re.S)
            newp = (f"<{prefix}p>" + (ppr.group(0) if ppr else "") + f"<{prefix}r>" + (rpr.group(0) if rpr else "")
                    + f'<{prefix}t xml:space="preserve">{escape(new_text)}</{prefix}t></{prefix}r></{prefix}p>')
            return xml[:m.start()] + newp + xml[m.end():], True
    return xml, False


def _replace_cell_after(xml, label, new_text, prefix="w:"):
    """Replace text of the table cell that follows the cell containing ``label``."""
    tag = re.escape(prefix)
    i = xml.find(f">{escape(label)}<")
    if i < 0:
        return xml, False
    tc_end = xml.find(f"</{prefix}tc>", i)
    nxt = re.compile(rf"<{tag}tc>.*?</{tag}tc>", re.S).search(xml, tc_end)
    if not nxt:
        return xml, False
    cell = nxt.group(0)
    count = {"n": 0}

    def sub(m):
        count["n"] += 1
        body = escape(new_text) if count["n"] == 1 else ""
        return f'<{prefix}t xml:space="preserve">' + body + f"</{prefix}t>"
    cell2 = re.sub(rf"<{tag}t(?:\s[^>]*)?>[^<]*</{tag}t>", sub, cell)
    if count["n"] == 0:
        return xml, False
    return xml[:nxt.start()] + cell2 + xml[nxt.end():], True


def update(docx_in, docx_out, entry_markup, *, baseline, head_sha, code_sha, date,
           footer_label=None, footer_date=None, cover_state=None,
           cover_checkpoint=None, cover_verification=None):
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(docx_in) as z:
        names = z.namelist(); z.extractall(tmp)
    doc = tmp / "word" / "document.xml"
    xml = doc.read_text(encoding="utf-8")
    root_match = re.search(r"<([A-Za-z_][\w.-]*:)?document\b", xml)
    if not root_match:
        raise ValueError("document.xml root element was not found")
    prefix = root_match.group(1) or ""
    report = {}
    xml, report["baseline"] = _replace_paragraph_text(xml, "Linha de base da revisão:", "Linha de base da revisão: " + baseline, prefix)
    xml, report["head"] = _replace_paragraph_text(xml, "SHA do HEAD documental:", "SHA do HEAD documental: " + head_sha, prefix)
    xml, report["date"] = _replace_paragraph_text(xml, "Revisão documental:", "Revisão documental: " + date, prefix)
    xml, report["control_sha"] = _replace_cell_after(xml, "SHA atual do código", code_sha, prefix)
    if cover_state:
        xml, report["cover_state"] = _replace_paragraph_text(xml, "Estado vigente", cover_state, prefix)
    if cover_checkpoint:
        xml, report["cover_checkpoint"] = _replace_paragraph_text(xml, "Checkpoint V", cover_checkpoint, prefix)
    if cover_verification:
        xml, report["cover_verification"] = _replace_paragraph_text(xml, "Verificação local atual:", cover_verification, prefix)
    # Legacy full specification versions may not contain a dedicated HEAD
    # paragraph. Add it before the first Heading1 rather than failing the
    # entire documentation synchronization or replacing the full document.
    if not report["head"]:
        first_h1 = re.search(rf'<{re.escape(prefix)}pStyle\b[^>]*{re.escape(prefix)}val="Heading1"', xml)
        at = xml.rfind(f"<{prefix}p>", 0, first_h1.start()) if first_h1 else -1
        if at >= 0:
            xml = xml[:at] + para("SHA do HEAD documental: " + head_sha, prefix=prefix) + xml[at:]
            report["head"] = True
    first_h1 = re.search(rf'<{re.escape(prefix)}pStyle\b[^>]*{re.escape(prefix)}val="Heading1"', xml)
    if not first_h1:
        raise ValueError("first Heading1 not found; refusing to append outside the Word document body")
    p_start = xml.rfind(f"<{prefix}p>", 0, first_h1.start())
    if p_start < 0:
        raise ValueError("could not locate the paragraph containing the first Heading1")
    xml = xml[:p_start] + entry_xml(entry_markup, prefix) + xml[p_start:]
    doc.write_text(xml, encoding="utf-8")
    if footer_label or footer_date:
        footer_replaced = False
        for f in (tmp / "word").glob("footer*.xml"):
            fx = f.read_text(encoding="utf-8")
            footer_root = re.search(r"<([A-Za-z_][\w.-]*:)?ftr\b", fx)
            footer_prefix = (footer_root.group(1) or "") if footer_root else prefix
            tag = re.escape(footer_prefix)
            if footer_label:
                pat = re.compile(rf"(<{tag}t(?:\s[^>]*)?>)[^<]*V88\.\d+[^<]*(</{tag}t>)")
                replacement = escape(footer_label) + (" · " + escape(footer_date) if footer_date else "")
                fx, n = pat.subn(lambda m: m.group(1) + replacement + m.group(2), fx, count=1)
                footer_replaced = footer_replaced or n > 0
            elif footer_date:
                fx, n = re.subn(r"\d{2}/\d{2}/\d{4}", footer_date, fx, count=1)
                footer_replaced = footer_replaced or n > 0
            f.write_text(fx, encoding="utf-8")
        report["footer"] = footer_replaced
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
    ap.add_argument("--cover-state"); ap.add_argument("--cover-checkpoint"); ap.add_argument("--cover-verification")
    a = ap.parse_args()
    out = a.out or a.docx
    r = update(a.docx, out + ".tmp", Path(a.entry).read_text(encoding="utf-8"), baseline=a.baseline,
               head_sha=a.head_sha, code_sha=a.code_sha, date=a.date,
               footer_label=a.footer_label, footer_date=a.footer_date,
               cover_state=a.cover_state, cover_checkpoint=a.cover_checkpoint,
               cover_verification=a.cover_verification)
    Path(out + ".tmp").replace(out)
    required = {"control_sha"}
    if a.cover_state: required.add("cover_state")
    if a.cover_checkpoint: required.add("cover_checkpoint")
    if a.cover_verification: required.add("cover_verification")
    missing = [k for k in required if not r.get(k, False)]
    print({"updated": out, "replaced": r})
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
