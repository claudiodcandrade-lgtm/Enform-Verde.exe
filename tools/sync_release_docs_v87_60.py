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
VERSION = "V87.62"
STAMP = "2026-11-10"
MARKER = "ENFORM_CHECKPOINT_V87_62_SAR_GRID_ABSTENTION"
FILES = [
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md",
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md",
    "docs/ESPECIFICACAO_SOLO_PRONASOLOS_0_100_2026-10-28.md",
]
WORD = "docs/ESPECIFICACAO_TECNICA_COMPLETA.docx"

POINTS = [
    "V87.62: regressao Windows anterior teve 1020 testes, uma falha no teste sintetico de recuperacao SAR. Tres cenas VV/VH foram lidas, mas a separabilidade de assinaturas foi insuficiente; o teste agora verifica recuperacao de grade independente da interpretacao semantica.",
    "recent_sar_landcover agora registra committed_grid_shape, committed_grid_crs e source_scene_count apos sucesso de leitura VV/VH, antes da classificacao. Falhas de tentativa nao poluem a grade seguinte. Arrays sem valores validos positivos sao descartados.",
    "Quando VV/VH sao lidos mas assinaturas nao separam classes, registrar N/D_VALIDACAO com SAR_SIGNATURE_SEPARABILITY_INSUFFICIENT; nao rotular ERRO_TECNICO, nao afirmar cultivo/floresta/solo exposto, nao estimar area de classe ou vigor.",
    "O teste nacional otico anterior produziu relatorio, mas o proprietario nao viu imagens em Sinop. Manter falha optica como bloqueio de liberacao real da GUI, independente do CI, ate reproduzir abertura CBERS-4A ou Sentinel-2 com o KML original.",
    "A ausencia de FH L2B no Tapajos nao e prova de falha de autenticacao MAAP; investigar L2A, disponibilidade, paginacao e intersecao. Nao substituir altura por dados artificiais.",
    "V87.61 10/11/2026: teste real informado pelo proprietario na Fazenda Maria Eduarda, Sinop (1459,91 ha, EPSG:6933), reproduziu falha de imagem optica, falha SELECTED_SCENES_PIXEL_READ_FAILED para Sentinel-1 RTC, e ausencia de mascara nativa/cultivada; carbono, vigor e safra ficaram N/D. Build/CI verdes da V87.60 nao asseguraram abertura em Windows de usuario; tratar como REGRESSAO REAL bloqueante.",
    "SAR atual: recent_sar_landcover.py agora faz rollback da grade de reprojecao de cena falha, so publicando provider_grid apos VV e VH efetivamente lidos, e rejeita arrays sem pixels positivos validos; teste sintetico tests/test_recent_sar_grid_recovery.py documenta o defeito. Essa correcao ainda exige teste Windows live em Sinop para comprovar recuperacao; nao marcar como resolvida por teste mock.",
    "LIBERACAO: regressao de CI e autoteste Windows devem ser complementados por teste em AOI real Sinop com imagem otica visivel no aplicativo, VV/VH lidos em mais de uma data/orbita adequada, mascara e areas semanticas defensaveis, e quadros de carbono/agricultura/Excel consistentes. Sem amostras rotuladas independentes, manter informacao experimental, com N/D para dados sem suporte.",
    "Nao confundir IBGE H potencial e legenda_2 cartografica com cobertura atual da propriedade. Nunca apresentar 99,41% de floresta como resultado SAR. Relatorio do proprietario aponta N/D completo, nao ausencia de vegetacao.",
    "Diagnostico obrigatorio: registrar provider, scene id nao sigiloso, momento de aquisicao, contador de tentativas, tipo de erro, status de leitura VV/VH, pixels validos, scene failover e data/qualidade da imagem optica. Segredos e URLs assinadas ficam redigidos.",
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
