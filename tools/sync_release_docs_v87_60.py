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
VERSION = "V87.68"
STAMP = "2026-11-10"
MARKER = "ENFORM_CHECKPOINT_V87_68_FH_L2A_AUTOMATIC"
FILES = [
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md",
    "docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md",
    "docs/ESPECIFICACAO_SOLO_PRONASOLOS_0_100_2026-10-28.md",
]
WORD = "docs/ESPECIFICACAO_TECNICA_COMPLETA.docx"

POINTS = [
    "V87.68 — corrigido em sar_pipeline.automatic_pipeline o bloqueio que ignorava produtos ESA BIOMASS FP_FH__L2A. O pipeline agora seleciona FH L2A ou L2B, executa estatistica zonal georreferenciada real, registra quantidade de pixels, produto de origem e altura H100, sem converter FH diretamente em AGB.",
    "Teste de contrato tests/test_maap_fh_l2a_automatic.py criado: atesta roteamento L2A, produto, media, n pixels e separacao entre altura e biomassa. Seus dados sao sinteticos e NAO equivalem a comprovacao de campo ou cobertura da propriedade.",
    "Evidencia live valida independente: 2304 pixels FH reais e altura media 18,284244 m numa janela de teste Sinop (GitHub Actions run 42813753319); a media nao caracteriza o KML completo Fazenda Maria Eduarda.",
    "Condicoes de liberacao permanecem: teste CBERS-4A ate tela Tk, leitura Sentinel-1 VV/VH real, mascara semantica rastreavel na AOI, altura ESA FH por formacao nativa e carbonos com incerteza. CI e build devem ser aprovados no mesmo commit; homologacao cientifica independente e separada.",
    "V87.67 — PROVA LIVE ESA BIOMASS EM SINOP: GitHub Actions run 42813753319, job maap-real-fh-proof, concluido SUCCESS em 10/11/2026; logs: authentication ACCESS_TOKEN_ISSUED, discovery FH 2 produtos FP_FH__L2A, HTTP 206 em enclosure_i_fh_tiff, leitura real FH_PIXELS_READ com 2304 pixels validos e media 18.284244156328196 m. Evidencia: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/42813753319/artifacts/13763952334.",
    "ESCOPO E LIMITACAO DA PROVA: a media de 18,28 m pertence a pequena bbox de teste em Sinop (-55.21,-11.89,-55.17,-11.85), NAO ao KML completo da Fazenda Maria Eduarda (1459,91 ha). A leitura de pixels H100 nao comprova area nativa, AGB, carbono, precisao metrica local, amostras independentes ou homologacao cientifica.",
    "CORRECAO PENDENTE IDENTIFICADA: em sar_pipeline.automatic_pipeline, a condicao de download de altura utiliza apenas FP_FH__L2B, desconsiderando FP_FH__L2A que efetivamente foi lido. Adequar a condicao para ambos os tipos e identificar no resultado o tipo realmente processado. Nao afirmar que essa integracao GUI foi concluida ate teste de compilacao e de AOI real.",
    "PIPELINE CIENTIFICO: tratar altura florestal ESA BIOMASS H100 em metros como compartimento estrutural separado de AGB; associar somente a mascara de floresta atual comprovada, inventarios microrregionais e equacoes especificas validas. Nao converter media H100 em Mg/ha, tC/ha ou tCO2e sem modelo documentado e incerteza.",
    "GATE DE ACEITACAO DA PROPRIEDADE: processar produto de altura com intersecao efetiva da Fazenda Maria Eduarda, contabilizar pixels e nodata, registrar fonte/data/identificador/QA/erro, cruzar com mascara SAR de vegetacao nativa comprovada, comparar inventarios e exportar mapas/planilhas com unidades, incerteza e N/D quando necessario.",
    "BLOQUEIOS PARA RELEASE COMPLETO: imagem CBERS-4A ou Sentinel-2 nao apareceu na GUI real do usuario; leitura/classificacao Sentinel-1 e mascara semantica da Fazenda Maria Eduarda continuam pendentes; regressao dashboard da CI atual reprovada; homologacao independente reprovada. Nao confundir job FH exitoso com EXE validado.",
    "V87.66 — evidencia MAAP LIVE em 10/11/2026: bbox de Sinop encontrou 2 produtos verdadeiros ESA BIOMASS FP_FH__L2A; o ativo enclosure_i_fh_tiff respondeu HTTP 206 e 1024 bytes validos. Isto comprova descoberta e acesso a arquivo, mas ainda NAO pixels georreferenciados de altura dentro do KML.",
    "Uma segunda consulta em Borneo mostrou defeito concreto: POST intersects produziu NO_FH_PRODUCTS, enquanto GET bbox retornou 100 itens iniciais e reconheceu 50 produtos FH, com proxima pagina. A producao maap_search foi corrigida para priorizar o GET bbox oficial e usar POST como fallback, sem esconder erros.",
    "Novo gate MAAP em GitHub Actions deve executar --download primeiro para bbox Sinop; a rota de exemplo Borneo e contingencia para prova global, nao autorizacao para atribuir seus valores a Sinop. Somente FH_PIXELS_READ em coordenadas da AOI permite declarar integracao completa nessa area.",
    "A integracao deve registrar produto, classe FP_FH__L2A ou L2B, data, CRS, pixel count, altura media em metros e validade da mascara. FH mede estrutura florestal H100, NAO AGB; derivacao de AGB exige produto FP_AGB_L2B ou modelo alometrico com inventario e incerteza.",
    "V87.65 10/11/2026: integracao ESA MAAP corrigida para busca STAC por POST intersects com fallback oficial GET bbox, paginacao real de links next, limite explicito e erros de HTTP/catalogo separados de ausencia de produtos. Nao registrar dados privados nem tokens em logs.",
    "BiomassLevel2a/L2b e IOC: falhas de todas as colecoes disparam MAAP_ALL_COLLECTION_SEARCHES_FAILED, nunca NO_FH_PRODUCTS falso; filtro FH usa metadados do item/ativos e evita confundir titulo de colecao com produto efetivo.",
    "Produtos FP_FH__L2A na rota /data/zipper/ sem extensao ZIP agora sao reconhecidos; suportar ativos product/download/enclosure/data e testar ZIP caso um GeoTIFF direto falhe. Raster FH so pode virar altura se pixels georreferenciados reais e validos forem lidos na AOI.",
    "Novo job paralelo de CI maap-real-fh-proof: usar ESA_MAAP_OFFLINE_TOKEN exclusivamente como segredo GitHub, sondar Sinop, e executar download/pixels reais em bbox Borneo exemplificado na documentacao oficial STAC. Resultado naquele local demonstra integracao global, NAO cobertura da Fazenda Maria Eduarda/Tapajos. Job falha se dados reais nao forem lidos; nao ocultar isso como sucesso.",
    "A ESA documenta colecoes BiomassLevel2a/L2b e tipos FP_FH__L2A, FP_FH__L2B e FP_AGB_L2B. FH H100 a 200 m nao e diretamente AGB, nem constitui area nativa confirmada; AGB exige produto quantitativo ou alometria/inventarios compativeis e erro.",
    "V87.64: o relatorio de uso da terra agora imprime diagnostico por provedor Sentinel-1 (cenas candidatas, serie elegivel, tentativas, leituras reais, falhas) e ate seis erros de leitura VV/VH com URL/token redigidos. O motivo SELECTED_SCENES_PIXEL_READ_FAILED nao pode permanecer sozinho sem causa auditavel.",
    "FALHA DE SINOP: distinguir indisponibilidade de rede, acesso SAS/TLS, erro de COG, falta de mascara semantica, baixa separabilidade SAR e ausencia de cenas. O texto do relatorio deve permitir diagnostico sem captura de credenciais.",
    "V87.63: inclusao do teste end-to-end tools/live_gui_optical_sinop.py em .github/workflows/build-windows.yml. O gate exige pixels reais CBERS-4A apresentados no canvas Tk, com foto, provedor e itens visiveis; nao basta receber cenas no catalogo ou ler COG em processo isolado.",
    "O gate de GUI usa pequena janela ao redor do centroide da Fazenda Maria Eduarda e NAO substitui teste do KML original no Windows do proprietario. Falha em GUI bloqueia build e gera evidencia optical_gui_sinop_live.json sem segredo.",
    "Reporte do GitHub Actions build anterior, 11 localidades, registra CBERS-4A/WFI com 100 por cento de pixels de preview em todas, inclusive Sinop em 2026-10-27. Isso demonstra disponibilidade no CI, mas nao exibe a imagem no computador do usuario.",
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
