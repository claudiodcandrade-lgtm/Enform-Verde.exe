# Enform Verde v3.26.31-PRECAMPO-EXPERIMENTAL

## Contingência para HTTP 429 no Sentinel-1

- O leitor MPC Sentinel-1 GRD tenta primeiro o token SAS de coleção, que permite abrir VV e VH sem chamar o endpoint de assinatura por ativo para cada polarização.
- O token é mantido apenas em memória. A auditoria registra `COLLECTION_SAS_TOKEN` ou `PER_ASSET_SIGNER_FALLBACK`; nenhum token ou URL assinada é incluído nos diagnósticos.
- O signer por ativo permanece como contingência limitada e encerra a busca por cenas após HTTP 429.
- INPE RTC e CDSE continuam como rotas independentes; ASF OPERA e AWS Sentinel-1 GRD foram identificados como alternativas possíveis com requisitos e diferenças explicitados na especificação.
- `PROCESSADO` continua exigindo leitura real de VV e VH na mesma cena. Band C não vira AGB sem modelo e calibração pertinentes.

**Verificação local:** 1.150 testes passaram; 1 foi ignorado por ausência de display gráfico.

**Status:** candidata pré-campo experimental, não homologada. A leitura live da rota de token no Windows, o diagnóstico nacional e o build no SHA final ainda precisam ser concluídos. Não há garantia de cobertura em toda coordenada/data do Brasil.
