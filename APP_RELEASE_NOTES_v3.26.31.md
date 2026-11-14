# Enform Verde v3.26.31-PRECAMPO-EXPERIMENTAL

## Contingência para HTTP 429 no Sentinel-1

- O leitor MPC Sentinel-1 GRD tenta primeiro o token SAS de coleção, que permite abrir VV e VH sem chamar o endpoint de assinatura por ativo para cada polarização.
- O token é mantido apenas em memória. A auditoria registra `COLLECTION_SAS_TOKEN` ou `PER_ASSET_SIGNER_FALLBACK`; nenhum token ou URL assinada é incluído nos diagnósticos.
- O signer por ativo permanece como contingência limitada e encerra a busca por cenas após HTTP 429.
- INPE RTC e CDSE continuam como rotas independentes; ASF OPERA e AWS Sentinel-1 GRD foram identificados como alternativas possíveis com requisitos e diferenças explicitados na especificação.
- `PROCESSADO` continua exigindo leitura real de VV e VH na mesma cena. Band C não vira AGB sem modelo e calibração pertinentes.

**Verificação local:** 1.150 testes passaram; 1 foi ignorado por ausência de display gráfico.

**Evidência live Windows (SHA `8334643`):** 8/8 AOIs amostrais de seis biomas tiveram pixels VV/VH recentes lidos com o SAS de coleção MPC, sem HTTP 429. INPE RTC não retornou cenas compatíveis nesses recortes. Gate: `PASS_DISTRIBUTED_SAMPLE`, sem garantia wall-to-wall. Dashboard, contrato rápido, máscara SAR Sinop, SAR no KMZ de teste Tapajós e smokes ópticos passaram. O workflow Windows #2726 concluiu com sucesso: EXE em pasta limpa, paridade Python/Windows, smoke da GUI, padrão visual, TLS, pixels CBERS-4A/WFI e Sentinel-1 VV/VH. O aceite SAR do KMZ de teste Tapajós passou, com `SAR_DERIVED_CCI` e sem fallback de AGB. Artifact ID `14087567135`; ZIP SHA-256 `1ad43f1281171b2eb49678bbc6ca5631587eef8f9b8ba69fa00904df1e2b9e77`; EXE SHA-256 `b7743a0d046390c14d3bdb97332fd15aeb82c8f72af85b07a0331e6db927264c`. A análise integral da Fazenda Maria Eduarda até o dashboard permanece pendente. Homologação científica independente: reprovada.

**Status:** candidata pré-campo experimental, não homologada. A leitura live da rota de token no Windows, o diagnóstico nacional e o build no SHA final ainda precisam ser concluídos. Não há garantia de cobertura em toda coordenada/data do Brasil.
