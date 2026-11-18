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

Versão experimental e não homologada. A execução Windows no SHA anterior `50431f39eeb2570e7b7320137277710090885761` concluiu 1.261 testes e encontrou dois erros em fixtures incompletos dos contratos do painel de previsão (ambos abortavam na formatação por falta de campos). Isso não é uma falha comprovada do modelo de vigor, mas impede aprovar aquele resultado. O commit `137cd80e940b126d803c4b8c2ac2c9957e4e2159` corrige os fixtures e preserva a auditoria antes de formatar. A nova regressão/build Windows e os demais gates ainda precisam concluir; não distribuir como versão corrigida até verificar a execução do SHA novo e testar a geometria privada integral.


### V88.132 — correções verificadas na regressão
- O workflow completo materializa explicitamente o cruzamento espacial IFN × IBGE `legenda_1` depois da ingestão, antes de testar seleção por localização, bioma e fitofisionomia.
- Corrigida a mensagem de vigor sem cena/data e tolerância numérica do teste de blocos de 2 ha sem relaxar os critérios de área/pureza do algoritmo.
- Smokes Windows: CBERS-4A/WFI carregou pixels reais no canvas; o smoke de cobertura registrou 11/11 locais. Aplicabilidade à geometria integral da propriedade ainda não foi demonstrada.
- Candidata permanece experimental até todos os jobs da revisão e evidências da AOI integral terminarem.


### V88.133 — coerência entre vigor calculado e vigor informado
- O painel agora consulta a auditoria emitida pela previsão (`used_in_yield_distribution`) para informar se o vigor efetivamente entrou na distribuição Monte Carlo. Uma lista de cenas sem identidade/data válida não basta.
- Cena sem `scene_id` e `acquisition_utc` válida é recusada na entrada do modelo; o painel informa N/D/motivo e não apresenta vigor como aplicado.
- Adicionada regressão da primeira ponta: saída do monitoramento → forecast → trilha executiva, incluindo cena sem ID. O runner do novo SHA está pendente.


### V88.135 — isolamento da formatação e auditoria de altura FH
- Corrigidos os dois fixtures incompletos que causavam erros no teste do painel. A aplicação grava previsão, proveniência e trilha de uso do vigor antes da renderização textual, preservando-as se o formatador falhar.
- A consulta de catálogo discrimina FH `FP_FH__L2A`/`FP_FH__L2B`, cenas L1C e consultas/paginação incompletas. Encontrar produto não equivale a ler pixels ou integrar altura à estimativa de carbono; ausência de L2B não é ausência demonstrada de altura.
- A validação do novo commit `137cd80e940b126d803c4b8c2ac2c9957e4e2159` ainda depende dos workflows em andamento. A versão permanece experimental, sem alegação de funcionamento completo do vigor ou FH→carbono, sem build aprovado e sem homologação científica.
