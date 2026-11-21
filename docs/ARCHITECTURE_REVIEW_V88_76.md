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
