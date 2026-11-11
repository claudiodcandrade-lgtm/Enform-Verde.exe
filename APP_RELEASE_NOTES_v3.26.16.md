# Enform Verde 3.26.16-PRECAMPO-EXPERIMENTAL

## Corrige leitura SAR e restaura contingência auditável de carbono

- Ajusta retentativas HTTP do GDAL para `GDAL_HTTP_MULTIRANGE=SERIAL`, opção válida; remove `NO`, que não era suportada e não ativava leitura sequencial.
- Diferencia falha de pixels de ausência no catálogo ou de série temporal insuficiente; mantém tentativas e exceções na trilha da execução.
- Corrige a função de interseção da fitofisionomia potencial IBGE que gerava `NameError` no módulo de uso do solo.
- Após esgotar as rotas SAR sem pixel/altura utilizável, volta a permitir estimativa condicional de carbono com IFN/parcelas abertas compatíveis primeiro e literatura regional/nacional em seguida. Falhas permanecem visíveis, cobertura potencial não vira cobertura observada, e incerteza não mensurada recebe rótulo literal e trilha de cálculo.
- Mantém altura por ESA BIOMASS FH como prioridade, com GTDX TanDEM-X+GEDI como alternativa condicionada à interseção de pixels e ao erro informado.

## Evidência / limitações

Verificação local: 1.063 testes aprovados, 1 ignorado; coleta de 154 módulos aprovada. O contrato visual de janela foi ignorado e a checagem da interface não pôde executar por falta de `$DISPLAY`.

Esta revisão corrige defeitos identificados em código e testes. Não comprova, por si só, acesso real a pixels no Windows, abertura óptica no KML inteiro, cobertura de altura em todo o país, validação científica por bioma nem build/liberação do executável.
