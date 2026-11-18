# Enform Verde v3.26.67-PRECAMPO-EXPERIMENTAL

Esta candidata endurece a prioridade da mensuração FH + estrutura horizontal de inventários. Erro de script, busca incompleta ou pixel não legível na rota prioritária deixa de permitir que ESA CCI AGB seja promovido silenciosamente como estimativa principal.

## Alterações

- ESA CCI AGB só é selecionado como contingência depois de a rota prioritária ESA BIOMASS FH estar auditada sem erro e não haver modelo FH × estrutura horizontal aplicável, ou depois de ausência de altura SAR certificada nas rotas exigidas.
- Pixels CCI podem permanecer registrados como candidatos na auditoria, mas não substituem uma rota prioritária tecnicamente falha.
- O resultado mantém o erro técnico, sobe `ERRO_TECNICO_ROTA_PRIORITARIA` e informa a ação necessária: corrigir ou repetir a rota prioritária antes de selecionar contingência.
- A contingência de médias de inventários continua separada, sem soma com ESA CCI e bloqueada por erro técnico ou ausência de cenas não certificada.
- Foi acrescentado um teste de integração reproduzindo busca FH com erro e CCI disponível.

## Status

Candidata experimental/pré-campo. Esta nota não declara validação concluída. Suíte completa, checker de coleta, build Windows, autoteste em pasta limpa, regressão documental e handoff live devem passar no SHA final. A homologação científica independente e a validação da geometria integral da Fazenda Maria Eduarda permanecem requisitos separados.
