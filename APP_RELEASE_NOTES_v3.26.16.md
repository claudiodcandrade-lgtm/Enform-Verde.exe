# Enform Verde 3.26.16-PRECAMPO-EXPERIMENTAL

## Corrige leitura SAR e restaura contingência auditável de carbono

- Ajusta retentativas HTTP do GDAL para `GDAL_HTTP_MULTIRANGE=SERIAL`, opção válida; remove `NO`, que não era suportada e não ativava leitura sequencial.
- Diferencia falha de pixels de ausência no catálogo ou de série temporal insuficiente; mantém tentativas e exceções na trilha da execução.
- Corrige a função de interseção da fitofisionomia potencial IBGE que gerava `NameError` no módulo de uso do solo.
- Após esgotar as rotas SAR sem pixel/altura utilizável, volta a permitir estimativa condicional de carbono com IFN/parcelas abertas compatíveis primeiro e literatura regional/nacional em seguida. Falhas permanecem visíveis, cobertura potencial não vira cobertura observada, e incerteza não mensurada recebe rótulo literal e trilha de cálculo.
- Mantém altura por ESA BIOMASS FH como prioridade, com GTDX TanDEM-X+GEDI como alternativa condicionada à interseção de pixels e ao erro informado.

## Evidência / limitações

Verificação local: 1.063 testes aprovados, 1 ignorado; coleta de 154 módulos aprovada. O contrato visual de janela foi ignorado e a checagem da interface não pôde executar por falta de `$DISPLAY`.

No CI foram lidos pixels reais ESA BIOMASS FH em Sinop. Uma execução independente também processou 30 cenas Sentinel-1 RTC VV/VH (out/2025–set/2026) e 1.692 pixels em uma janela experimental ao redor do centroide, gerando polígonos e classes exploratórias para 1.079,26 ha. A janela de pixels tinha 1.084,73 ha; ela não é o KML integral de 1.459,91 ha. O resultado não está validado em campo e não autoriza transferência para a propriedade ou estimativa de carbono com base nessas classes.

A build Windows inicialmente parou antes dos testes e do empacotamento: o workflow tentava restaurar um artefato antigo inexistente (`v3.24.20`) e o download oficial IBGE excedeu o tempo limite do runner Windows. O caminho de restauração foi atualizado para um pacote Windows anterior bem-sucedido ainda disponível (`v3.26.15`, run `42921624944`), para desacoplar o build do download cartográfico no momento da compilação. A nova tentativa deve confirmar esse reparo.

Esta revisão corrige defeitos identificados em código e testes e comprova leitura real de pixels SAR/altura em áreas de prova limitadas. Ainda não comprova abertura óptica CBERS/Sentinel-2 no Windows, processamento do KML integral, cobertura de altura em todo o país, validação científica por bioma/cultura, nem build/liberação do executável. O gate científico independente continua reprovado; não chamar estes resultados de homologados ou calibrados.
