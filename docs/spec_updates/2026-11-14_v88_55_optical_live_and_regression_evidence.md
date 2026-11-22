# V88.55 — evidência óptica real e regressão Windows

Data: 14/11/2026. Candidata: `3.26.35-PRECAMPO-EXPERIMENTAL`. Branch: `patches-3.26.6`. SHA de origem: `417e93141ec035d5bb414abb620224d490580927`.

## Alteração

Mantida a prioridade de CBERS-4A/WFI, seguida por Sentinel-2 L2A. A leitura COG divide a prévia em quadrantes limitados, e o fallback de cartografia raster não se apresenta como imagem orbital. O commit complementar ajusta regressões de teste para refletirem o leitor por quadrantes e mantém a política de não substituir pixels SAR processados por referência de inventário.

## Evidência observada

- Workflow Windows #43633560279: cobertura óptica CBERS-4A/WFI em 11/11 janelas representativas no Brasil; cobertura reportada de 100% em cada janela, com limiar mínimo de aceite de 95%.
- Smoke Tk em Sinop: imagem real CBERS-4A/WFI visível em uma janela ao redor do centroide da fazenda; canvas 673×562. O teste não usou o KML integral.
- Sentinel-2 L2A em cena real no Tapajós: passou.
- Workflow dashboard #43633560291: 1.156 testes da suíte integral terminaram `OK`. O job foi marcado como falha apenas no guard de sincronização documental; esta atualização registra o resultado nos documentos obrigatórios.
- O build Windows #43633560279 terminou verde no SHA de código 417e93141ec035d5bb414abb620224d490580927. O EXE 3.26.35 passou o autoteste em pasta limpa. Artefato Actions 14129607134 (197.843.132 bytes), SHA-256 do ZIP `3ff077bc0a002190028732a27c76de6a9332f1fd773df2d1d249fc22eda814`, SHA-256 do EXE `ac9b68b0139f4a1694e5545d98bc3eb8902c17cee4aa771caf0b040330ad6f44`. O fluxo incluiu leitura óptica, testes live SAR, contratos e build. O workflow ESA BIOMASS FH real em Sinop passou.
- Gate científico independente #43633560339 reprovado por ausência de validação observacional independente.

## Limites e pendências

As amostras geográficas não comprovam cobertura contínua nacional ou para todas as datas e propriedades. A janela de Sinop não equivale à execução do KML integral da Fazenda Maria Eduarda até o dashboard. O produto permanece pré-campo experimental e não homologado. O relatório de cada análise deve preservar provedor, cena/data, cobertura, origem dos pixels e erro de leitura/transporte.
