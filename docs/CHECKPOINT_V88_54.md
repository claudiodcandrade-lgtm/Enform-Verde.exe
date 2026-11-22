# Checkpoint V88.54 — CBERS-4A prioritária, Sentinel-2 alternativa

Data: 14/11/2026

## Código entregue neste checkpoint

- `3.26.35-PRECAMPO-EXPERIMENTAL` mantém CBERS-4A/WFI (INPE) como primeira fonte óptica, seguido por Sentinel-2 L2A Earth Search e Sentinel-2 Planetary Computer.
- As leituras COG são divididas em blocos de saída de no máximo 512 × 512 pixels; pool limitado a três cenas e tentativas/transporte limitados para reduzir o tempo de espera.
- A cena só é aceita após leitura RGB real, pixels válidos e cobertura mínima de 95% da AOI. A origem e data são preservadas no crédito/cache.
- Removida a criação/empacotamento do raster nacional cartográfico IBGE, que consumia tempo no build e não deve substituir uma imagem óptica. Se as cenas CBERS e Sentinel-2 não puderem ser lidas, o perímetro fica visível junto com erro rastreável. NASA VIIRS e Esri são contexto visual de contingência, nunca entrada para cálculo.
- Conversão de COG inteiro mascarado para float antes de preencher NoData como NaN, prevenindo exceção em fontes raster de tipo inteiro.

## Verificações deste ambiente

- `python -m py_compile desktop_app.py`: aprovado.
- `python tools/check_test_collection.py`: executado, mas bloqueado por 39 módulos que não importam devido a dependências indisponíveis neste ambiente, em particular `requests`, `rasterio` e `geopandas`.
- Três contratos estáticos focados em pixels reais/limite de cobertura/prioridade CBERS passaram (3/3).
- YAML de `.github/workflows/build-windows.yml` parseado com sucesso.
- O teste raster local que usa Rasterio e qualquer leitura de pixels em rede não puderam ser executados aqui.

## Pendências que não podem ser declaradas concluídas

1. Executar suíte integral e build Windows no SHA final; o pipeline atualizado ainda precisa demonstrar instalação, PyInstaller, self-test e artefato.
2. Confirmar visualmente CBERS-4A no canvas Windows, seguida de Sentinel-2 em caso de indisponibilidade CBERS; este ambiente sem dependências/raster remoto não prova a leitura real.
3. Executar KML integral Fazenda Maria Eduarda (1.459,91 ha) desde upload até painel; nenhuma prova foi criada por este checkpoint.
4. A homologação científica continua reprovada por falta de observações independentes de campo. O candidato permanece experimental e não homologado.

A prioridade CBERS-4A está preservada no código e nas verificações estáticas. Nenhuma contingência cartográfica será rotulada como CBERS ou Sentinel-2.
