# Enform Verde v3.26.33-PRECAMPO-EXPERIMENTAL

## Auditoria de fluxo e redução de trabalho repetido

- O cache de descoberta/download ESA CCI Biomass v7 é compartilhado somente dentro da análise atual e por telhas de 10°; as estatísticas continuam sendo recalculadas para a geometria de cada estrato.
- A auditoria do Sentinel-1 preserva os diagnósticos independentes MPC e CDSE em `sentinel1_provider_routes`. O resumo compatível mantém a primeira rota que efetivamente leu pixels, sem apagar o diagnóstico da outra.
- O monitoramento agrícola deixa de repetir tentativas de transporte quando um erro local determinístico comprova que a cena não contém pixels válidos/intersectantes para a AOI ou que excede os limites de leitura. Falhas de rede, TLS e leitura continuam acionando os fallbacks existentes.
- O restante da análise, incluindo seleção por aquisição, leitura por AOI/estrato, rastreabilidade e abstinência N/D, não é substituído por um cache de resultados científicos.

## Evidência e limites

Esta versão reorganiza aquisições e retentativas; não altera equações, não adiciona calibração nem transforma Sentinel-1 C-band isolada em AGB. O teste de regressão completo no SHA anterior `ee42b631f3ce69de3f78aaebbb366acfa4e82599` passou; o guard documental desse SHA falhou porque as mudanças de código não tinham sido sincronizadas ao Word e aos prompts. O novo SHA precisa passar novamente pelo CI, pela construção Windows e pelo teste do fluxo integral Fazenda Maria Eduarda → dashboard.

O PR #51 permanece em rascunho. O gate científico independente continua reprovado por evidência observacional insuficiente; portanto, manter `PRECAMPO-EXPERIMENTAL` e não declarar homologação.
