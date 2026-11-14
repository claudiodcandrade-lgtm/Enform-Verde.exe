# Checkpoint V88.46 — validação Windows da rota SAS de coleção

Data: 13/11/2026  
Versão candidata: `3.26.31-PRECAMPO-EXPERIMENTAL`  
SHA avaliado: `8334643eadb4d82366c06eed789c9e659c752b09`  
Branch: `patches-3.26.6`, PR #51 em rascunho; não mesclar.

## Resultado SAR distribuído

O Windows CI #2726 registrou `PASS_DISTRIBUTED_SAMPLE`: 8 de 8 AOIs em seis biomas tiveram pixels reais VV e VH recentes (0,65 a 10,62 dias) lidos na mesma aquisição Sentinel-1 GRD via `COLLECTION_SAS_TOKEN`. Cada banda teve de 128.484 a 196.249 pixels válidos. Nenhuma AOI registrou HTTP 429. A amostra inclui Sinop e Petrolina.

O INPE Sentinel-1 RTC não listou cenas compatíveis nas oito AOIs, com paginação completa. Isso vale para os recortes/data consultados; não prova indisponibilidade nacional do INPE. O MPC SAS de coleção resolveu o limitador observado no teste anterior para esta amostra.

## Outros gates

- Dashboard dual #3448: aprovado.
- Contratos rápidos #805: aprovados.
- Máscaras SAR experimentais Sinop #207: aprovadas.
- Pixels SAR no KMZ de teste Tapajós, sondagens ópticas brasileiras e fundo óptico no canvas Sinop: aprovados.
- Build Windows #2726: ainda em execução no contrato de equações/recalibração quando este checkpoint foi escrito.
- KML integral da Fazenda Maria Eduarda até o dashboard: não comprovado ponta a ponta.
- Homologação científica #3035: reprovada por falta de validação observacional independente.

## Decisão

Manter `3.26.31-PRECAMPO-EXPERIMENTAL`, sem chamar de homologada. O teste cobre oito AOIs, não todas as coordenadas/datas do país. Não inferir AGB de Sentinel-1 C-band isolada. Consultar o relatório `inpe_sentinel1_rtc_live.json` anexado ao workflow #2726 e `national_sar_gate_status.txt`.
