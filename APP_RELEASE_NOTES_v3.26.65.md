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

### V88.136 — acesso autenticado FH e primeira ponta da previsão
- A investigação do fluxo real mostrou FH L2A no catálogo, mas HTTP 401 no download. O workflow SAR agora fornece o secret ESA MAAP à chamada de carbono; os relatórios nunca exibem o token.
- Falhas do ativo FH contam como erros técnicos e bloqueiam a contingência por ausência. A leitura positiva de pixels é marcada como concluída, sem confundir pixels existentes com ausência.
- O ensaio live inclui chamada real ao modelo de previsão agrícola usando a mesma AOI/resultado SAR. Só informa uso de vigor quando a auditoria do modelo confirma a participação na distribuição de produtividade.
- Testes locais direcionados passaram (11). Workflow Windows, pixels FH autenticados e execução ponta a ponta da previsão continuam pendentes; manter candidata experimental até a inspeção dos novos artefatos. O ensaio CBERS em ponto público não comprova abertura na geometria integral privada.

### V88.137 — integridade da publicação de código
- O primeiro runner do patch de token FH não iniciou: encontrou U+2026 dentro de `sar_pipeline.py`, porque a transferência do arquivo extenso ao objeto GitHub havia sido truncada. A checagem local isolada não detectou a diferença entre arquivo local e blob remoto.
- Fonte completa retransmitida e publicada em `b99f92fbda4cef0ba49edd139c1e22dd81cf0183`. O resultado do build anterior foi interrompido e não pode ser distribuído. O novo runner precisa passar sintaxe, regressão, live SAR/carbono/previsão e build limpo antes de declarar a versão corrigida.
- A prova separada conseguiu pixels FH em Sinop, mas a etapa substituta Borneo falhou e o fluxo SAR integrado não executou. O vigor ainda não foi comprovado no cálculo da produtividade.

### V88.138 — resultados do primeiro fluxo live autenticado
- O fluxo SAR integrado leu FH L2A: 23,35 m/333 pixels na formação florestal e 11,91 m/4 pixels na formação savânica da caixa pública de Sinop. AGB ainda veio do ESA CCI; não há equação inventário×H100 validada para Sinop. A comparação IFN foi N/D porque esse job não materializou o banco, embora a base tenha sido reconstruída e testada no job Windows.
- A previsão de soja calculou a distribuição PAM/clima, mas não usou vigor: `used_in_yield_distribution=false`, por ausência de cenas/referências elegíveis nos recortes amostrados. O relatório seguinte precisa reter as razões por cena e amostra.
- CBERS passou no teste nacional 11/11 e canvas público Sinop; não comprova o KML privado integral. Build do EXE e autoteste limpo passaram; artefato `14392522195`, SHA256 ZIP `5c0518737ca3294a4647c3e54409623cf875e7091f20f6c35c1f97e3f183c21a`. A homologação científica segue bloqueada; versão experimental.
- O SHA `88affb8d2c5903c9c970b3758b08623ea16c8625` atualiza o ensaio live para materializar IFN e registrar as razões completas do N/D de vigor/FH. A execução desse SHA ainda está pendente.

### V88.139 — correção do primeiro bloqueio real de vigor
- O live identificou um `NameError` por sombreamento de `datetime` no ramo anual da busca Sentinel‑1, mascarado como N/D e deixando a previsão seguir sem vigor. Corrigido o fechamento temporal e adicionada auditoria por provedor para impedir que busca incompleta seja confundida com ausência de cena.
- No AOI público de Sinop, o live anterior também não encontrou cenas VV/VH nos últimos 30 dias. O reparo remove o erro lógico, mas vigor só será calculado quando uma cena recente e pixels/referências passarem os gates. A próxima previsão precisa demonstrar `used_in_yield_distribution=true`; sem isso, permanece previsão sem vigor com motivo explícito.
- Novos testes cobrem ausência comprovada e erro de catálogo. Neste container, `py_compile`/AST passaram; a suíte geoespacial depende do runner com GeoPandas. Código e documentação atualizados; Windows/live ainda precisam concluir antes de distribuição. A candidata segue experimental.

### V88.140 — correção de expectativas da regressão
- A suíte completa encontrou quatro falhas nos testes: import faltante, fixtures de busca sem estado de completude dos dois provedores, e um teste que buscava cena live sem querer ao validar apenas o encaminhamento da máscara agrícola. Os fixtures agora controlam ausência/cena explicitamente, sem relaxar os gates de produção.
- A suíte Windows e os jobs SAR/live foram disparados novamente; até concluírem no SHA documental final, não há novo pacote para distribuição. Candidata permanece experimental.
