"""Synchronize required Enform Verde release documents without erasing their history.

The CI documentation gate requires these four paths to change in the same
release-documentation commit. The Word file is updated as an actual DOCX,
not a renamed text file. Credential material is never read by this tool.
"""
from datetime import datetime, timezone
from pathlib import Path
from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
VERSION = "V87.60"
STAMP = "2026-11-10"
MARKER = "ENFORM_CHECKPOINT_V87_60_MAAP_DISCOVERY"
FILES = [
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md",
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md",
    "docs/ESPECIFICACAO_SOLO_PRONASOLOS_0_100_2026-10-28.md",
]
WORD = "docs/ESPECIFICACAO_TECNICA_COMPLETA.docx"

POINTS = [
    "PR #51, branch patches-3.26.6: piloto pre-campo experimental; release Windows so pode ser anunciado apos build, autoteste e regresao completos no mesmo SHA.",
    "ESA MAAP: teste live confirmou ACCESS_TOKEN_ISSUED em 10/11/2026, portanto a troca do offline token em access token funciona. A busca retornou NO_FH_PRODUCTS e exit code 5; isto NAO confirma ausencia de produtos ou pixels.",
    "A busca atual por FP_FH__L2A e FP_FH__L2B precisa distinguir erro de catalogo, consulta/colecao, filtro, paginacao, restricao de acesso e verdadeira ausencia de cobertura; nunca converter erro em lista vazia sem diagnostico.",
    "Implementados no PR: fallback para download ZIP de FH, sonda autenticada tools/verify_esa_maap_live.py, workflow manual verify-esa-maap-live.yml, diagnostico GET STAC por bbox em quatro colecoes e testes de contrato.",
    "ACEITE MAAP: autenticacao bem sucedida + produto FH com intersecao espacial verificada + ativo HTTP legivel + download integro + pixels de altura validos dentro da AOI, com QA, data, resolucao, fonte e incerteza. Ate la, status N/D e nao afirmar produto processado.",
    "Imagem de fundo optica CBERS-4A ou Sentinel-2 efetivamente aberta; IBGE para nomenclatura e classes pedologicas, nao como comprovacao de cobertura atual.",
    "Identificacao de cobertura e agricultura por SAR observado, rotulando modelos experimentais e dominio. Vigor via observacoes SAR sem transformar proxy VV+VH em altura metrica; previsao apenas quando matriz clima-PAM-vigor estiver documentada.",
    "Carbono nativo por formacao/compartimento com AGB, raizes, necromassa, serrapilheira, carbono de solo brasileiro 0-100 cm e respectivas incertezas. N/D quando nao sustentado; nunca evidencias sinteticas para homologacao.",
    "Correcoes tecnicas de regressao: agregar poligonos da mesma classe e preservar talhoes repetidos; eliminar conflito de nomes do unittest. Teste rapido de modelos aprovado, homologacao cientifica independente bloqueada; CI completa deve ser verificada novamente apos commit de documentacao.",
    "O token ESA MAAP e geometria privada nao devem aparecer em codigo, relatórios, logs ou artefatos. Usar exclusivamente segredo do Actions/entrada protegida.",
]

def section():
    header = f"## {VERSION} - checkpoint ESA MAAP e piloto experimental ({STAMP})"
    return "\n".join([f"<!-- {MARKER} -->", header, ""] + ["- "+point for point in POINTS] + ["", "---", ""])

def update_markdown(path):
    original = path.read_text(encoding="utf-8")
    if MARKER in original:
        return False
    path.write_text(section() + "\n" + original, encoding="utf-8")
    return True

def update_word(path):
    d = Document(path)
    if any(MARKER in p.text for p in d.paragraphs[:40]):
        return False
    body = d.element.body
    appendix = Document()
    appendix.add_paragraph(MARKER)
    appendix.add_heading(f"{VERSION} - ESA MAAP e piloto experimental ({STAMP})", level=1)
    for line in POINTS:
        appendix.add_paragraph(line, style="List Bullet")
    appendix.add_paragraph("HISTORICO INTEGRAL DA ESPECIFICACAO ANTERIOR - PRESERVADO ABAIXO")
    from copy import deepcopy
    for idx, el in enumerate([x for x in appendix.element.body if not x.tag.endswith("sectPr")]):
        body.insert(idx, deepcopy(el))
    d.save(path)
    return True

def main():
    changed = [str(f) for f in FILES if update_markdown(ROOT / f)]
    if update_word(ROOT / WORD):
        changed.append(WORD)
    print("Checkpoint", VERSION, "updated files:", changed)
    if not all((ROOT / f).is_file() for f in FILES + [WORD]):
        raise RuntimeError("One or more required documents are absent")

if __name__ == "__main__":
    main()
