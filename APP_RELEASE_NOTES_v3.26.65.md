# Enform Verde v3.26.65-PRECAMPO-EXPERIMENTAL

## Correções em andamento após análise do uso real

- A comparação CCI × inventários deixa de ser exclusiva ao IFN e passa a consultar também as estatísticas publicadas com AGB que estão harmonizadas no pacote. Cada fonte permanece separada e comparativa; nenhum valor é somado ao estoque principal.
- Hash do painel IFN normalizado para LF/CRLF: evita que checkout Windows rejeite dados idênticos. Na geometria reportada para Fazenda Maria Eduarda, a comparação IFN selecionou cinco UAs e gerou média experimental de 152,55 Mg AGB/ha.
- Resumo fitossociológico reaproveita o resultado do IFN por estrato, sem exigir CSV opcional.
- Amostragem de vigor SAR condicional tenta blocos de 16/8/4/2 ha para máscaras agrícolas fragmentadas, mantendo ≥90% de pureza e pelo menos seis blocos de referência independentes. Antes de condicionar a previsão PAM×clima, o sistema valida as três probabilidades e uma cena Sentinel‑1 identificada e datada (máximo 30 dias, sem cenas futuras). Máscaras 2025/26 continuam condicionais; alvos menores sem suporte permanecem N/D.
- O cartão executivo agrícola mostra por cultura se o vigor entrou na distribuição de produtividade ou por que ficou fora; a trilha de cenas e probabilidades fica na auditoria.
- Trilha de busca/download/leitura FH e GTDX é preservada no relatório de carbono. No relatório anterior, duas cenas FH apareceram no catálogo, mas nenhum pixel foi lido; ainda não há comprovação de altura média FH para a fazenda.
- Diagnóstico óptico por provedor aparece no painel espacial para a AOI executada. A correção da imagem só será considerada confirmada depois de uma execução real em Windows que mostre pixels CBERS/Sentinel no canvas.
- O botão de imagem óptica também rola a aba espacial até o canvas; o teste visual deve acionar o caminho normal do programa sem preparação de rolagem manual.

## Estado

Versão experimental e não homologada. A regressão completa executou 1.260 testes e reportou cinco problemas (quatro falhas e um erro): o workflow não materializava o cruzamento IFN–IBGE antes dos testes, uma mensagem de vigor não preservava a expressão “sem data” e uma asserção ignorava erro de reprojeção inferior a 1e-6 ha. Correções já preparadas; a regressão e os gates Windows no novo SHA ainda precisam concluir. Não distribuir como versão corrigida antes da aprovação desses gates e da execução com o KML privado integral.


### V88.132 — correções verificadas na regressão
- O workflow completo materializa explicitamente o cruzamento espacial IFN × IBGE `legenda_1` depois da ingestão, antes de testar seleção por localização, bioma e fitofisionomia.
- Corrigida a mensagem de vigor sem cena/data e tolerância numérica do teste de blocos de 2 ha sem relaxar os critérios de área/pureza do algoritmo.
- Smokes Windows: CBERS-4A/WFI carregou pixels reais no canvas; o smoke de cobertura registrou 11/11 locais. Aplicabilidade à geometria integral da propriedade ainda não foi demonstrada.
- Candidata permanece experimental até todos os jobs da revisão e evidências da AOI integral terminarem.
