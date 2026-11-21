# Enform Verde v3.26.38-PRECAMPO-EXPERIMENTAL

Data: 14 de novembro de 2026

## Correção

A auditoria identificou que uma falha após o processamento de uso da terra podia fazer o worker descartar os resultados SAR já produzidos antes da apresentação no painel. Esta candidata trata erros de carbono nativo, pedologia e fertilidade por etapa, preserva resultados anteriores, declara o estado e o motivo da falha e vincula os módulos ao mesmo identificador de execução e hash da AOI. Um checkpoint local registra um resumo da execução sem guardar a geometria ou credenciais.

Foram acrescentados testes de regressão ao handoff do worker para o dashboard, incluindo falhas nas etapas de carbono e pedologia. A versão só deve ser considerada validada após a suíte completa, o dashboard e o build Windows passarem no mesmo SHA.

## Limites

A evidência anterior de pixels SAR na Fazenda Maria Eduarda corresponde a uma etapa isolada. O fluxo do KML integral até painel/relatório não foi demonstrado nesta candidata. O KML permanece privado e não foi incluído neste repositório. A candidata é pré-campo experimental e não tem validação científica independente de campo.
