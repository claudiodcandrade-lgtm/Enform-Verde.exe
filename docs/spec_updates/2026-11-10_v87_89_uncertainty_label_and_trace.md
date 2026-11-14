# V87.89 — Rótulo obrigatório e trilha de cálculo quando a incerteza não é mensurável (10/11/2026)

## Regra de saída
- Emitir o rótulo literal **“estimativa com incerteza não mensurada”** somente quando a incerteza necessária para interpretar o valor não puder ser declarada de forma defensável.
- Não confundir medidas parciais conhecidas, como DP entre inventários, com incerteza total da estimativa da AOI. Nomear cada medida e seu escopo.
- Expor trilha reprodutível dos dados e filtros, amostra/unidades, valores intermediários, parâmetros e equações, área-base, fatores de conversão e resultado final. Registrar quais fontes de incerteza permanecem sem quantificação.
- Para carbono IFN sem pixels SAR, manter cenário separado, condicional à área de fitofisionomia potencial IBGE, sem confirmar cobertura atual e sem adicionar o número ao estoque nativo confirmado.

## Implementação e verificação
- Em `ifn_carbon_fallback.py`, o JSON inclui `estimate_label`, estatísticas amostrais, `calculation_trace` e incertezas ainda não mensuradas. O painel imprime o rótulo literal e a trilha.
- Testes focais aprovados. A regressão completa local foi bloqueada por dependências ausentes (856 executados, 57 erros, 1 falha associada ao ambiente, 28 ignorados). Build Windows e ensaio do KML integral ainda não confirmados.
- Commit de código/empacotamento `d26a4f8`; versão em avaliação `3.26.14-PRECAMPO-EXPERIMENTAL`. Não liberar até CI Windows, regressão e teste real passarem no mesmo SHA.
