# V88.46 — leitura Windows ao vivo sem HTTP 429 via SAS de coleção (13/11/2026)

## Resultado no SHA 8334643eadb4d82366c06eed789c9e659c752b09

O build Windows #2726 executou o gate distribuído sobre oito AOIs representativas de seis biomas. Em todas as oito, a candidata leu pixels reais VV e VH do mesmo produto Sentinel-1 GRD usando `COLLECTION_SAS_TOKEN`; `rate_limited=false`, sem erros de leitura, e idade das aquisições entre 0,65 e 10,62 dias. A sondagem incluiu Sinop e Petrolina. Contagens válidas por polarização variaram de 128.484 a 196.249 pixels.

O catálogo Sentinel-1 RTC do INPE retornou zero cenas compatíveis nas oito AOIs, com paginação completa. Isso confirma que, para esta amostra e execução, a rota MPC com token SAS de coleção contornou o 429 observado anteriormente. Não demonstra indisponibilidade do INPE em geral nem cobertura wall-to-wall do Brasil.

## Outros resultados observados

O dashboard dual #3448, contratos rápidos #805 e máscaras SAR experimentais Sinop #207 passaram no mesmo SHA. O teste de pixels no KMZ do Tapajós, as sondagens ópticas brasileiras e a abertura do fundo óptico no canvas de Sinop passaram. O build Windows #2726 ainda estava em andamento no momento deste registro, na execução dos contratos de equações/recalibração; o artefato executável final e o percurso integral do KML da Fazenda Maria Eduarda até o dashboard ainda não estavam confirmados.

A homologação científica independente #3035 reprovou por insuficiência de evidência observacional independente. Manter a candidata como `3.26.31-PRECAMPO-EXPERIMENTAL`, sem homologação. O resultado distribuído é amostral; não garante cenas, pixels ou precisão em qualquer coordenada/data do Brasil, e não transforma Sentinel-1 C-band isolado em estimativa de AGB.

## Relatório

O workflow anexou `inpe_sentinel1_rtc_live.json`, com evidência por AOI/provedor, par VV/VH, aquisição e estado da rota, e `national_sar_gate_status.txt` com `PASS_DISTRIBUTED_SAMPLE`. Evidência gerada no workflow Windows #2726 para o SHA acima.
