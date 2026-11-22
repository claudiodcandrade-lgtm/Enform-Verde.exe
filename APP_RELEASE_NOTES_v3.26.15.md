# Enform Verde 3.26.15-PRECAMPO-EXPERIMENTAL

## Correção de apresentação do classificador SAR sazonal

- Preserva no painel executivo áreas de classes experimentais derivadas de pixels SAR reais, mesmo quando o modelo não é homologado como classificação atual.
- Distingue explicitamente a safra completa observada do monitoramento atual e informa safra, cenas, pixels, modelo e SHA quando disponíveis.
- Identifica as áreas como “estimativa com incerteza não mensurada”; as métricas do holdout do modelo não são tratadas como incerteza da AOI.
- Mantém o estado de cobertura atual validada separado e não extrapola a janela classificada para todo o KML.

## Evidências e limitações

Esta alteração de código não prova, sozinha, aquisição de cenas atuais, leitura no KML integral da Fazenda Maria Eduarda, execução no Windows, build do EXE ou homologação científica. A evidência histórica da safra 2025/2026 (30 cenas, 1.692 pixels, 1.084,73 ha) é sazonal e limitada à janela então classificada.

Verificação local: 1.062 testes aprovados, 1 ignorado; coleta: 154 módulos. O padrão visual não pôde ser verificado neste ambiente sem `$DISPLAY`. Build Windows e ensaio com o KML integral continuam pendentes.
