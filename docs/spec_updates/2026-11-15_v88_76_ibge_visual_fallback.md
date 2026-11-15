# Revisão arquitetural — Enform Verde V88.73

Data: 15/11/2026  
Código candidato: 3.26.42-PRECAMPO-EXPERIMENTAL  
Base revisada: relatórios de carbono do Tapajós e Fazenda Maria Eduarda e monitoramento agrícola da Fazenda Maria Eduarda.

## Causas demonstradas nos relatórios

1. **Mistura temporal SAR.** A classificação LEM+ usa o último ano agrícola completo (2025/26) e era inserida na mesma lista de camadas do monitoramento atual. O relatório também incluía a triagem Sentinel-1 de janela móvel de 150 dias. A partição conjunta fechava 100% da AOI, embora os produtos fossem de épocas distintas. A presença do modelo anual ativava o estado “contingência não necessária”, mesmo sem classificador semântico da data atual.
2. **Agregação de carbono escondia suportes parciais.** As tabelas só calculavam densidade quando cada compartimento cobria toda a área nativa. Por isso raízes, necromassa e serapilheira apareciam N/D no resumo apesar de valores suportados em quase toda a formação dominante. A conclusão de estoque total incompleto era correta; a tabela parcial não era.
3. **Leitura SAR lenta e repetitiva.** O fluxo tentava até cinco estratégias por cena, com timeout GDAL de 45 s e retries internos. Os diagnósticos mostram 60 tentativas para 12 cenas legíveis e erros de decodificação/auth repetidos.
4. **Smoke óptico permissivo.** O gate verificava metadados, dimensões e item de imagem no canvas, sem medir pixels do canvas. Uma imagem preta podia satisfazer essa verificação.

## Mudanças de arquitetura incluídas na candidata

- O campo annual_sar_classification registra safra, identificador e escopo. LEM+ anual não conta como semântica atual; pixels experimentais recentes permanecem num produto separado.
- A contingência é decidida pela disponibilidade do classificador semântico atual, não pela execução de LEM+ anual.
- O sumário SAR anuncia explicitamente quando as classes mostradas pertencem ao último ano completo.
- Cada compartimento de carbono mostra densidade por área quantificada e cobertura em hectares/percentual. Nenhum valor é projetado para área não quantificada. O total permanece parcial/incompleto até atender os gates completos.
- Sentinel-1 tenta leitura COG padrão e, em seguida, crop binário limitado à AOI; timeout/retry cai de 45 s/3 para 12 s/1 na leitura GDAL e de 180 s para 30 s na rota HTTP de contingência.
- O smoke live captura os pixels do canvas e rejeita resultado sem brilho, variação e fração visível mínimos.
- Na falha óptica, a interface exibe o perímetro e a camada IBGE potencial já carregada, quando disponível. O mapa IBGE é cartografia de referência; não confirma cobertura atual nem é insumo de cálculo.

## Critérios obrigatórios antes de distribuição

- CI verde no commit exato, incluindo suíte integral, regressões de separação temporal e cobertura parcial, smoke live do canvas e build Windows.
- Teste real na AOI integral privada da Fazenda Maria Eduarda em instalação Windows, com os diagnósticos locais anexados. A fixture pública de Sinop não substitui esse KML.
- Verificação de relatórios Tapajós e Maria Eduarda com painéis que separem mapa anual, monitoramento atual, candidatos SAR e áreas N/D.
- Análise de duração por estágio. A redução das estratégias repetidas limita esperas por cena, mas não certifica ainda o tempo total de uma AOI até a rodada de CI.
- Validação de campo e externa independente para retirar o rótulo pré-campo/experimental.

## Limites

Nenhum código garante disponibilidade contínua dos provedores remotos, leitura da geometria privada que não está no ambiente, ou verdade de classe sem referência local independente. Falha de fonte deve terminar em motivo e N/D, nunca em máscara vazia tratada como zero. Esta revisão identifica e corrige causas comprovadas nos relatórios; a resolução operacional depende dos gates executados sobre o commit gerado.


## Checkpoint V88.76 — fallback visual IBGE não bloqueante

CBERS/Sentinel-2 são opcionais e não bloqueiam a análise. A UI mantém um fundo de contingência visível e, após falhas ópticas, carrega a camada IBGE de fitofisionomia em worker assíncrono. A camada é rotulada como formação potencial e não entra em mapas de cobertura atual, carbono ou cultura. Se o dado IBGE também falhar, a AOI permanece visível com aviso. O smoke nacional registra locais sem óptica sem reprovar o build; o smoke de canvas mede pixels reais e aceita apenas imagem visível ou cartografia de contingência, nunca uma tela preta.


## V88.77 — correção do smoke de compilação

No SHA `c24e441e396ea3f19bd8ec4d0845e52e3245ee43`, a CI identificou uma docstring não encerrada no script `tools/live_optical_coverage_brazil.py`. Isso interrompia o `compileall` e impedia o build Windows antes do empacotamento, apesar dos testes unitários e regressivos passarem. A docstring foi fechada no commit corretivo. É obrigatório repetir compilação, suíte, smoke óptico/cartográfico, smoke de pixels do canvas, SAR live e build no SHA final. A correção do teste não prova cobertura óptica nacional; a UI deve manter a contingência IBGE/AOI.


## V88.79 — validação do build e handoff SAR (15/11/2026)

Código testado: `8551bcaf84586af71ae574abda8a6e37e467f4d3`. Aplicação: `3.26.42-PRECAMPO-EXPERIMENTAL`.

- CI dashboard: suíte integral 1.173 testes e guard documental aprovados.
- Build Windows: concluído; UI smoke em pasta limpa, teste de módulos e paridade Python/EXE, leitura real de rede e aceitação do KMZ Tapajós aprovados.
- CBERS-4A/WFI: 11/11 AOIs de amostra com pixels e cobertura de 100%; isso não é prova exaustiva de todo o território.
- Tela Windows: `PASS_AOI_FALLBACK`; o perímetro e canvas não ficam pretos, mas este smoke específico não capturou imagem CBERS nem fundo IBGE dentro da janela.
- Sentinel-1: handoff ponta a ponta passou em amostra pública Sinop e KMZ Tapajós: processamento → uso da terra → carbono → payload dashboard. Artefatos registram `BOTH_AOIS_END_TO_END_HANDOFF_PASSED`.
- Pacote EXE: SHA-256 `796561975818f2e6a6db8d7858875f6d080b926d523885583bf9907c5c7fff35`; ZIP do artifact SHA-256 `31653bc1c2edb1b066b5ccb3e1056858c8114bbcca91b82872bdd6aa70849312`.

**Pendências e interpretação:** o SAR transmitido e aplicado é mapa experimental do último ano agrícola completo 2025/2026, não monitoramento semântico atual; classificação atual N/D e rota radar alternativa `ACESSO_RESTRITO`. Estoque de carbono entregue é parcial/incompleto, com compartimentos sem suporte e incertezas não quantificáveis explicitamente. A amostra pública Sinop não é o KML privado integral Fazenda Maria Eduarda. Homologação científica/campo não passou. A entrega pode ser chamada de build operacional testado no escopo descrito, não de versão homologada ou garantia universal.
