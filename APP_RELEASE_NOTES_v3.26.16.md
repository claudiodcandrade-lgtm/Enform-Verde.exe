# Enform Verde 3.26.16-PRECAMPO-EXPERIMENTAL

## Corrige leitura SAR e restaura contingência auditável de carbono

- Ajusta retentativas HTTP do GDAL para `GDAL_HTTP_MULTIRANGE=SERIAL`, opção válida; remove `NO`, que não era suportada e não ativava leitura sequencial.
- Diferencia falha de pixels de ausência no catálogo ou de série temporal insuficiente; mantém tentativas e exceções na trilha da execução.
- Corrige a função de interseção da fitofisionomia potencial IBGE que gerava `NameError` no módulo de uso do solo.
- Após esgotar as rotas SAR sem pixel/altura utilizável, volta a permitir estimativa condicional de carbono com IFN/parcelas abertas compatíveis primeiro e literatura regional/nacional em seguida. Falhas permanecem visíveis, cobertura potencial não vira cobertura observada, e incerteza não mensurada recebe rótulo literal e trilha de cálculo.
- Mantém altura por ESA BIOMASS FH como prioridade, com GTDX TanDEM-X+GEDI como alternativa condicionada à interseção de pixels e ao erro informado.

## Evidência / limitações

Build final do commit `b70894e1796121027aaaf09c00a533d131e5a749`: run Windows 43050581961 aprovado; artefato ID 13871576858 (533.400.808 bytes), SHA-256 ZIP `1abc923ed7133ce259c1130b5b7be729c827226891e52e5739aab82777b7d4f6`; SHA-256 do EXE `66c17b8d8fad210a9e3aa92e16a05e3d11d3c4655d0b8722e2477f7958a6cc97`. Self-test em pasta limpa, paridade Python/Windows, padrão visual, network-check e aceite SAR Tapajós passaram. O aceite SAR leu 302.348 pixels em cinco cenas para 1.290,69 ha (`SAR_PROCESSADO`), mas não retornou AGB quantitativa (`fallback_agb_mg_ha=null`). Smoke óptico e CBERS canvas tiveram sucesso em amostras; a AOI integral da Fazenda Maria Eduarda ainda não foi processada.

Verificação local: 1.063 testes aprovados, 1 ignorado; coleta de 154 módulos aprovada. O contrato visual de janela foi ignorado e a checagem da interface não pôde executar por falta de `$DISPLAY`.

No CI foram lidos pixels reais ESA BIOMASS FH em Sinop. Uma execução independente também processou 30 cenas Sentinel-1 RTC VV/VH (out/2025–set/2026) e 1.692 pixels em uma janela experimental ao redor do centroide, gerando polígonos e classes exploratórias para 1.079,26 ha. A janela de pixels tinha 1.084,73 ha; ela não é o KML integral de 1.459,91 ha. O resultado não está validado em campo e não autoriza transferência para a propriedade ou estimativa de carbono com base nessas classes.

A build Windows inicialmente parou antes dos testes e do empacotamento: o workflow tentava restaurar um artefato antigo inexistente (`v3.24.20`) e o download oficial IBGE excedeu o tempo limite do runner Windows. O caminho de restauração foi atualizado para um pacote Windows anterior bem-sucedido ainda disponível (`v3.26.15`, run `42921624944`), para desacoplar o build do download cartográfico no momento da compilação. A nova tentativa do run 43043275464 confirmou a recuperação e verificação do mapa offline; o build/executável foi concluído com sucesso no SHA `a1a11b1e406af0d322c5697222012403c92735ba`.

Esta revisão corrige defeitos identificados em código e testes e comprova leitura real de pixels SAR/altura em áreas de prova limitadas. O smoke óptico em 11 pontos do Brasil carregou pixels em 11/11 AOIs de teste: CBERS-4A em 9/11 e Sentinel-2 em fallback nos demais, incluindo Sinop; o teste CBERS-4A worker→canvas Tk em Sinop também passou. Isso não comprova cada local/data do Brasil nem processamento do KML integral. O SAR real em Sinop foi uma janela amostral (30 cenas, 1.692 pixels) e não está aferido em campo. O build 3.26.16 passou o teste do EXE em pasta limpa e o aceite SAR de Tapajós; artefato Actions ID 13867841475. SHA-256 do executável: `95aa798b72ddcafc9c962ffd338b5cf7f7e4740488ed325fde7ee710c8e2631f`.

O gate científico independente continua reprovado. A execução integral do KML privado de Sinop no Windows e as medições de carbono/agricultura nesse perímetro ainda não foram comprovadas; não chamar os modelos de homologados ou calibrados. A publicação de release fica restrita a fluxo explícito em `main`.
