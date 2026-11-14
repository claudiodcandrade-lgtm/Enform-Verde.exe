# V88.36 — recuperação SAR e validação Windows concluídas (13/11/2026)

## Correções e evidência operacional

A leitura de COGs Sentinel-1 grandes usa recorte limitado da AOI no Microsoft Planetary Computer quando necessário: grade máxima de 1,8 milhão de células, resposta transmitida em blocos limitada a 128 MiB, verificação TIFF e TLS ativo. Erros persistentes continuam como `ERRO_TECNICO`, sem serem confundidos com ausência de cenas.

O primeiro autoteste do EXE revelou um erro no contador, não uma falha comprovada de leitura: Rasterio retorna `array.mask=False` escalar quando o raster não tem pixels mascarados, e `(~array.mask).sum()` contabilizava apenas 1. O contador foi corrigido para `numpy.ma.count`, com regressão para arrays totalmente válidos e parcialmente mascarados.

No workflow Windows do commit `32cac735fe9e26c664b832b755606e7e0d4fd6b0` passaram o build, paridade Python/Windows, teste visual, leitura CBERS‑4A no executável com TLS ativo, leitura Sentinel‑1 VV/VH real via GDAL e via rota HTTPS/recorte, e aceitação SAR/AOI em KMZ real do Tapajós. O `--network-check` contou 170.820 pixels GDAL por polarização e 169.168 pixels pela rota HTTPS local por polarização; cena `S1D_IW_GRDH_1SDV_20261112T091635_20261112T091700_005432_00A5E9_rtc`, aquisição 12/11/2026 09:16 UTC. A prova CBERS‑4A usou dados de 01/11/2026.

A aceitação do executável no KMZ de teste do Tapajós retornou `SAR_PROCESSADO`, 5 cenas, 302.348 pixels, 1.290,688 ha, origem `SAR_DERIVED_CCI` e sem AGB fallback. Isso comprova a execução nesse AOI de aceitação, não a fazenda Maria Eduarda nem a homologação científica nacional.

## Build Windows auditado

- Versão: `3.26.25-PRECAMPO-EXPERIMENTAL`
- Commit-fonte compilado e testado: `32cac735fe9e26c664b832b755606e7e0d4fd6b0`
- SHA-256 do `Enform Verde.exe`: `e7ae5ee65a84af6168f813ec85192fdaa0dbf81255b5cd73b64a373c56482dfa`
- Artefato Actions: `Enform-Verde-Windows-v3.26.25-PRECAMPO-EXPERIMENTAL` (531.984.389 bytes)
- SHA-256 do ZIP do artefato: `3791ae997ad82aec768b65639128403996ba7c8cc1ff7e70d9f2eb9741435b63`
- Run Windows: `43453754591`; dashboard: `43453754533` (ambos aprovados).

## Limites mantidos

A suíte local completa passou com 1.135 testes e 1 ignorado por ausência de display. As máscaras SAR experimentais e contratos rápidos passaram. A homologação científica independente continua pendente de dados de campo. O fluxo do KML integral da Fazenda Maria Eduarda até carbono, agricultura e dashboard não foi comprovado; não inferir esse resultado a partir do teste do Tapajós.
