# Enform Verde v3.26.65-PRECAMPO-EXPERIMENTAL

## Correções em andamento após análise do uso real

- A comparação CCI × inventários deixa de ser exclusiva ao IFN e passa a consultar também as estatísticas publicadas com AGB que estão harmonizadas no pacote. Cada fonte permanece separada e comparativa; nenhum valor é somado ao estoque principal.
- Hash do painel IFN normalizado para LF/CRLF: evita que checkout Windows rejeite dados idênticos. Na geometria reportada para Fazenda Maria Eduarda, a comparação IFN selecionou cinco UAs e gerou média experimental de 152,55 Mg AGB/ha.
- Resumo fitossociológico reaproveita o resultado do IFN por estrato, sem exigir CSV opcional.
- Amostragem de vigor SAR condicional tenta blocos de 16/8/4/2 ha para máscaras agrícolas fragmentadas, mantendo ≥90% de pureza e pelo menos seis blocos de referência independentes. O fluxo do PAM×clima usa probabilidades de vigor apenas quando a cena atual e a amostra são válidas; máscaras 2025/26 continuam condicionais. Alvos menores sem suporte permanecem N/D.
- O cartão executivo agrícola mostra por cultura se o vigor entrou na distribuição de produtividade ou por que ficou fora; a trilha de cenas e probabilidades fica na auditoria.
- Trilha de busca/download/leitura FH e GTDX é preservada no relatório de carbono. No relatório anterior, duas cenas FH apareceram no catálogo, mas nenhum pixel foi lido; ainda não há comprovação de altura média FH para a fazenda.
- Diagnóstico óptico por provedor aparece no painel espacial para a AOI executada. A correção da imagem só será considerada confirmada depois de uma execução real em Windows que mostre pixels CBERS/Sentinel no canvas.

## Estado

Versão experimental e não homologada. A suíte completa e os gates de Windows ainda não foram executados nesta candidata; a execução ponta a ponta com o KML privado ainda é necessária. Não distribuir como versão corrigida até esses gates confirmarem o comportamento.
