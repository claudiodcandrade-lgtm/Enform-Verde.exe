# Enform Verde v3.26.67-PRECAMPO-EXPERIMENTAL

Esta candidata endurece a prioridade da mensuração FH + estrutura horizontal de inventários. Erro de script, busca incompleta ou pixel não legível na rota prioritária deixa de permitir que ESA CCI AGB seja promovido silenciosamente como estimativa principal.

## Alterações

- ESA CCI AGB só é selecionado como contingência depois de a rota prioritária ESA BIOMASS FH estar auditada sem erro e não haver modelo FH × estrutura horizontal aplicável, ou depois de ausência de altura SAR certificada nas rotas exigidas.
- Pixels CCI podem permanecer registrados como candidatos na auditoria, mas não substituem uma rota prioritária tecnicamente falha.
- O resultado mantém o erro técnico, sobe `ERRO_TECNICO_ROTA_PRIORITARIA` e informa a ação necessária: corrigir ou repetir a rota prioritária antes de selecionar contingência.
- A contingência de médias de inventários continua separada, sem soma com ESA CCI e bloqueada por erro técnico ou ausência de cenas não certificada.
- Foi acrescentado um teste de integração reproduzindo busca FH com erro e CCI disponível.
- A comparação independente ESA CCI passou a consultar todo o registro numérico de AGB harmonizado e compatível por bioma/fitofisionomia, mesmo sem IFN; cada estudo fica separado e não é somado ao estoque. Fontes em catálogo ou microdados não harmonizados seguem explicitamente não elegíveis.
- O estado SAR auxiliar é preservado quando existe leitura de pixels, enquanto falha FH fica registrada em `priority_height_route_status` e continua impedindo a promoção do CCI.
- Corrigido o handoff do dashboard quando a contagem de pixels FH é `None`: a interface usa zero somente no teste de existência de pixels e preserva o valor nulo e a auditoria na trilha original. O live do SHA anterior concluiu Sinop e identificou essa falha no Tapajós; a correção aguarda repetição do handoff.

## Status

Candidata experimental/pré-campo. Testes focados locais passaram (18, 2 skips ambientais); a suíte integral local falhou por dependências geoespaciais/base IFN ausentes e erros live dependentes dessas bibliotecas. Checker documental, build Windows, autoteste em pasta limpa e handoff live devem passar no SHA final. A homologação científica independente e a validação da geometria integral da Fazenda Maria Eduarda permanecem requisitos separados.

## Resultado dos gates — SHA 7198a6d

A suíte integral, o gate documental e o handoff live Sinop/Tapajós passaram. O vigor SAR foi usado pela distribuição PAM+clima na amostra Sinop (`used_in_yield_distribution=true`), condicional à máscara retrospectiva. A prova de pixels FH separada passou em Sinop, mas o handoff FH→AGB nos recortes carbonizados reportou erro técnico e leitura incompleta; motivo não foi preservado, portanto não equivale a ausência certificada. O build criou o EXE, mas o autoteste limpo falhou porque o teste de aceitação ainda exige referência de biomassa Tapajós quando o gate FH bloqueia corretamente a contingência. Sem pacote/publicação nesta revisão. Corrigir e auditar a causa FH e alinhar o teste de aceitação, depois repetir os gates e autoteste.
