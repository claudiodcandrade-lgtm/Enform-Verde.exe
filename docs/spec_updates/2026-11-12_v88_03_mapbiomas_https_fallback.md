# V88.03 — Recuperação local do COG MapBiomas após falha de /vsicurl/ (12/11/2026)

## Evidência observada
- O relatório recente da Fazenda Maria Eduarda registra `MAPBIOMAS_open_cog_RasterioIOError` e que o GeoTIFF `/vsicurl/` não foi reconhecido como dataset. As retentativas com opções HTTP do GDAL repetiam o mesmo caminho virtual; isso não contornava builds Windows sem suporte funcional ao `/vsicurl/`.
- LEM+ também não encontrou pares VV/VH nos 12 meses da janela sazonal e a triagem SAR informa falhas técnicas de leitura. Isso não demonstra ausência de cenas; a causa de leitura e a recuperação fim a fim ainda não foram comprovadas.

## Correção local
- `mapbiomas_zonal.py` passa a detectar a falha específica de abertura por `/vsicurl/`, baixar o GeoTIFF oficial via HTTPS para cache por usuário e reexecutar o mesmo recorte de pixels da AOI pelo arquivo local.
- A transferência é temporária e atômica, limita o arquivo a 5 GB, rejeita respostas HTML/JSON, conteúdo vazio ou truncado e valida metadados GeoTIFF antes de manter o cache. Cache inválido é descartado. O relatório continua apontando a URL publicada pelo MapBiomas.
- A contingência permanece referência anual histórica, condicionada ao esgotamento auditado das rotas SAR; não se transforma em cobertura atual nem em validação SAR.
- Foi incluído um teste de regressão de integração usando GeoTIFF pequeno e simulação de GDAL sem `/vsicurl/`.

## Estado e limites de validação
- Alteração apenas no workspace, sobre o commit-base `63c12e8f4adf5048153ff6859bbc71a081d5a13c`; não foi enviada ao GitHub nem incluída em novo executável.
- `py_compile` e `git diff --check` passaram. O teste de regressão geoespacial não pôde rodar porque o ambiente atual não contém Rasterio; a suíte GUI também não importou por ausência de `requests`. `tools/check_test_collection.py` inspecionou 157 módulos, mas reportou 36 falhas de importação por dependências ausentes. Não houve leitura do GeoTIFF oficial, dos pixels SAR/ópticos, nem do KML integral no Windows.
- O erro do MapBiomas recebe uma rota de recuperação testável, mas a contingência ainda não está comprovada operacionalmente. Imagem CBERS/Sentinel-2, leitura SAR da fazenda, classificação agrícola e exibição do cenário de carbono por inventário permanecem pendentes de validação fim a fim. Não declarar correção concluída nem publicar uma nova versão com base apenas nessa alteração.
