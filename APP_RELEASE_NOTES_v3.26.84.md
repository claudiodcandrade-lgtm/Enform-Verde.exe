# Enform Verde v3.26.84-PRECAMPO-EXPERIMENTAL

## Ajustes do relatório e painel de carbono

- O relatório executivo de carbono apresenta cada incerteza mensurável em tC/ha, tCO₂e/ha e %, além do estoque total/conhecido em tC e tCO₂e.
- O quadro por compartimento foi redesenhado como tabela com bordas em todas as células, cabeçalhos legíveis e rolagem horizontal/vertical. Cada linha explicita densidade, estoque, área, situação e natureza da incerteza.
- Sensibilidade parcial é mostrada nas três unidades, separada da incerteza total. Desvio padrão espacial do solo também é mostrado nos três valores, identificado como descritivo (não é erro preditivo nem IC95%).
- A aba executiva do Excel inclui as três unidades de incerteza por compartimento.
- Não foram alteradas as equações, densidades, estoques, fontes nem regras de elegibilidade já aplicadas a áreas como Tapajós. Quando uma AOI não tem suporte para quantificar uma incerteza específica, o campo permanece N/D com o motivo; isso não apaga resultados mensuráveis de outra área.

## Verificação e limites

A mudança passou 43 testes focados de quadro, cálculo, relatório, exportação, mapa, versionamento e contratos de interface, além de `py_compile`. Na regressão ampla posterior à atualização do DOCX foram coletados 1.107 testes: 74 erros de importação/execução, 32 ignorados e uma falha na leitura live VV/VH Sentinel-1. O coletor inspecionou 197 módulos e falhou por ausência de dependências geoespaciais neste runtime. Não houve build Windows, validação visual Tk nem EXE em pasta limpa. A candidata não está liberada para distribuição e não representa homologação científica nem prova de eliminação geral do congelamento.
