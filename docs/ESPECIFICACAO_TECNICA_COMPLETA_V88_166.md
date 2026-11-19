Warning: truncated output (original token count: 276459)
... 57260 bytes omitted ...

# Especificação Técnica Completa — Enform Verde V88.166

**Data:** 18/11/2026
**Candidata:** 3.26.76-PRECAMPO-EXPERIMENTAL
**Estado:** candidata pré-campo experimental; build e aceite Windows no SHA final pendentes; não homologada e sem EXE liberado.

## V88.166 — correção do runtime de evidência de inventário

O aceite Tapajós do EXE revelou que `structural_aggregate_evidence_v1.csv` estava somente em `dist/data`, enquanto os módulos congelados consultam `_internal/data`. O build inclui agora o arquivo no runtime PyInstaller e valida a presença das referências KM72/KM117. O JSON/erro de aceite expõe estado, diagnóstico e fontes do registro. O primeiro gate integral encontrou também um defeito do sincronizador Word: a capa continuava em 3.26.73 mesmo após inserir o checkpoint V88.166. O gerador e workflow atualizam agora a linha de estado e a versão da capa, com testes de regressão. A execução pré-campo seguinte revelou uma asserção antiga que exigia texto V87.1 nos documentos correntes; o gate agora compara `APP_VERSION` com o DOCX e verifica V88.166 no prompt v52 e na especificação do solo, sem exigir conteúdo do prompt histórico v43. Build e regressão integral do SHA corrigido ainda pendentes. Candidata 3.26.76, não homologada.

## Histórico V88.165 — indexação sob demanda das bases de inventários

O registro CSV de referências harmonizadas é cacheado por revisão de arquivo e reutilizado em consultas de fontes, AGB e estrutura. A seleção IFN aplica primeiro a chave composta indexada de bioma e legenda_1 do IBGE, com fallback de normalização quando a grafia varia. A base SQLite de 466 MiB só consulta registros de árvores das unidades selecionadas, por índice de UA; auditoria de integridade é cacheada por versão do arquivo. Testes focados passaram; após sincronização documental, a regressão integral local passou: 1.312 testes OK, 1 ignorado; 191 módulos coletados; self-test e module-check passaram. Gates Windows pendentes. Continua candidata experimental, sem homologação ou EXE validado neste SHA.

## Histórico V88.164 — correção da aceitação Tapajós

A referência pai/subformação reconhecida para Floresta Ombrófila Densa das Terras Baixas agora permite listar separadamente Santos et al. KM72 e KM117 com SAR presente. As médias publicadas são apenas balizas: sem agrupamento, adição ao estoque ou calibração FH. Sem modelo quantitativo AGB aplicável, AGB permanece N/D.

## Conteúdo integral da especificação Word

O texto e as tabelas abaixo preservam o conteúdo acumulado da especificação Word, com o checkpoint V88.165 no início e o histórico das revisões anteriores.

Enform Verde Especificação Técnica Completa

## CANDIDATA PRÉ-CAMPO EXPERIMENTAL; NÃO HOMOLOGADA; EXECUTÁVEL NÃO LIBERADO

V88.162 | 3.26.73-PRECAMPO-EXPERIMENTAL

O gate de aquisição ESA CCI foi antecipado para evitar downloads inelegíveis. Regressão local: 1.305 testes OK e 1 ignorado; coleção: 190 módulos sem falhas; autoteste do aplicativo passou. Build Windows, inspeção visual em ambiente gráfico, integração live final e modelo AGB FH aplicável ainda pendentes. Não há novo EXE liberado nem validação científica independente.

REVISÃO V87.1 — referência histórica mantida para compatibilidade do controle documental legado; não representa o estado atual da candidata. CORREÇÃO CIENTÍFICA V87.1 permanece registrada no histórico da especificação.

# V88.162 — Bloquear consulta CCI antes do gate de elegibilidade (18/11/2026)

## Alteração

O pipeline avalia primeiro o certificado da rota prioritária ESA BIOMASS FH/GTDX e os metadados de calibração CCI–inventário.

A busca/download do histórico ESA CCI só é iniciado quando todos os critérios de contingência já estão satisfeitos. Com pixels FH válidos, busca prioritária incompleta/erro técnico ou calibração ausente, a aquisição CCI é pulada e registrada como `NAO_ADQUIRIDO_GATE_BLOQUEADO`.

A auditoria distingue download pulado por gate (`download_skipped`) de busca executada com falha técnica. A causa impeditiva e a rota prioritária continuam explícitas.

Não se converte erro técnico em ausência real de cena, e não se promove CCI sem calibração validada. A mudança reduz uma consulta/download grande sem alterar limiares científicos.

Teste de regressão instala uma falha se o download CCI for chamado enquanto FH não foi resolvido; valida status, gate e trilha de auditoria.

## Limites e estado

Esta correção de fluxo não cria coeficientes, pares de calibração, estimativa de AGB, validação independente ou certificação científica.

Em especial, FH com pixels válidos, mas sem modelo AGB horizontal aplicável, permanece uma pendência de modelo e bloqueia CCI. Isso não autoriza inventar biomassa nem declarar ausência de FH.

A regressão integral passou localmente (1.305 testes OK, 1 ignorado); a verificação da coleção passou (190 módulos sem falhas). Build Windows, teste visual/rede, aceite SAR→dashboard e gate científico ainda requerem evidência no SHA final.

Candidata `3.26.73-PRECAMPO-EXPERIMENTAL`; não é executável liberado nem versão homologada.

# V88.160 — referências agregadas de inventários integradas ao resultado FH (18/11/2026)

## Alterações

A consulta ao comparador de inventários publicado deixa de ocorrer somente quando ESA CCI fornece AGB; agora acompanha qualquer resultado quantitativo nativo, incluindo FH, preservando-o como comparação paralela.

Relatório executivo e planilha exportada têm uma seção/aba de referências estruturais publicada por fonte e fitofisionomia. Exibe região, métrica, centro, unidade, número de parcelas quando publicado, incerteza e citação/URL.

Médias e outros agregados regionais totalizados podem servir como baliza de plausibilidade quando microdados abertos não existem. Não são parcelas sintéticas, pareamentos espaciais/temporais, validação SAR nem adição ao estoque. Fontes e desenhos não comparáveis permanecem separados; incerteza ausente não é inventada.

A limitação de saturação tropical da CCI aparece na auditoria do relatório quando presente nos detalhes SAR.

Registro ausente/inválido permanece erro técnico; ausência de correspondência ecológica exata é distinta de erro de leitura.

## Evidência e limites

Regressão integral no branch atualizado: 1.305 testes OK, 1 ignorado; 190 módulos inspecionados sem falhas. `desktop_app.py --self-test` e `py_compile` passaram. O visual check local não pôde rodar por falta de display gráfico.

IFN oficial materializado: 27 planilhas estaduais, 841.387 observações, 8.951 unidades amostrais e 8.951 correspondências espaciais únicas à legenda_1 do IBGE.

Candidata `3.26.72-PRECAMPO-EXPERIMENTAL`; faltam gates do workflow Windows no SHA final, incluindo `--module-check`, `--visual-check`, `--network-check` e aceite SAR→dashboard. Sem executável ou calibração/homologação declarados como aprovados neste checkpoint.

O registro harmonizado é consultado integralmente, porém a cobertura científica continua limitada às fontes e métricas efetivamente presentes nele. O catálogo por si só não transforma inventário em referência quantitativa compatível.

# V88.156 — normalização de datas dos inventários IFN

Data: 18/11/2026

Código-base: 3.26.71-PRECAMPO-EXPERIMENTAL

## Falha encontrada

A colheita IFN convertia as datas das planilhas para texto antes de obter mínimo/máximo. Isso ordenava datas como DD/MM/AAAA lexicograficamente, e valores Excel como o serial 45541 ficavam sem conversão. Consequentemente, o manifesto podia exibir um máximo menor que o mínimo ou um número serial, prejudicando qualquer auditoria temporal para pares FH–campo.

## Correção

Foi adicionada normalização compartilhada que reconhece datas Python, textos DD/MM/AAAA/ISO e serials Excel; blanks, zero e valores inválidos não viram datas falsas. O manifesto passa a ordenar datas ISO cronologicamente e conta valores não interpretáveis. A ingestão SQLite aplica o mesmo parser à coluna measurement_date.

Teste de contrato cobre o serial 45541 → 2024-09-06, formatos textuais/datetime e valores ausentes/inválidos. Ele não prova formação de pares FH–inventário nem calibração AGB.

## Evidência de inventários e limite do modelo

O build anterior materializou 841.387 observações IFN em 8.951 unidades, com cruzamento único de legenda_1 IBGE, e 439.970 registros do painel SFB. O modelo local continua sem pareamento temporal/espacial FH–inventário validado no AOI amplo do Tapajós. O modelo ORNL tem suporte restrito às parcelas cadastradas e medições de 2010; sua referência de altura não deve ser pareada com FH contemporâneo sem justificativa temporal e validação. O teste 2010 tentou a rota regional Digital Earth Africa e detectou que ela não cobre o Brasil; não prova ausência de mosaico PALSAR global.

## Estado de liberação

O executável compilou, mas o autoteste em pasta limpa falhou no aceite Tapajós: pixels SAR foram lidos, porém não foi produzida AGB prioritária nem referência de inventário elegível. O job não publicou pacote. A checagem de módulo mostrou que o banco IFN foi incluído (841.387 registros; 8.951 UAs), porém não fornece, por si, um estimador por hectare nem altura de dossel. Correção de datas é necessária para a busca de pareamentos, mas não substitui a calibração e validação microrregional requeridas. Não liberar o 3.26.71 como nova versão operacional.

# V88.155 — correção do diagnóstico FH com modelo AGB ausente

Data: 18/11/2026

Aplicativo de referência: 3.26.71-PRECAMPO-EXPERIMENTAL

Base revisada: SHA `f945d9fd915b9f938e0a54a917eb8e33f5b9448b`

## Resultado que o build anterior realmente demonstrou

No aceite Windows do AOI Tapajós (1.290,688 ha), o leitor zonal encontrou 1.512 pixels válidos de FH e não registrou erros de leitura. Portanto, o rótulo `ERRO_TECNICO_ROTA_PRIORITARIA` era incorreto para esse caso. O ESA CCI foi corretamente bloqueado porque havia FH, mas a aplicação não dispunha de um modelo AGB compatível com a extensão/domínio do AOI. O aceite do EXE falhou e nenhum artefato foi publicado.

## Correção de código

A distinção foi implementada: FH lido sem modelo recebe `FH_DISPONIVEL_AGB_MODELO_NAO_DISPONIVEL`; CCI continua bloqueado; falhas reais de rota sem pixels válidos continuam sinalizadas separadamente. A saída mantém AGB como N/D e não converte o diagnóstico em estimativa.

## Pendências que bloqueiam uma versão operacional

A calibração FH×campo e sua integração ao fluxo de AGB não estão implementadas. O modelo Tapajós existente está restrito às zonas dos sítios ORNL e não cobre o AOI extenso do aceite. A base local inclui dados IFN e outras fontes, mas ainda não foi demonstrado pareamento FH–inventário multiprovedor, validação espacial independente nem incerteza propagada em domínio microrregional. Não substituir essa lacuna por CCI, médias de inventário ou uma regra de aceite permissiva.

A rotina corrigida precisa ser incorporada ao executável, e a versão candidata só poderá ser liberada após demonstrar, no mesmo SHA: consulta da base expandida, pares FH–inventário elegíveis, modelo único de AGB com validação e incerteza, integração até dashboard/relatório e autoteste Windows aprovado. A homologação científica independente permanece separada.

## Registro do checkpoint documental

Commit da correção diagnóstica: `0cc8bfa2f65a6060f85f8908d4cb8bcc4daa8268`. Workflow atualizado para sincronizar este checkpoint na especificação Word completa. A sincronização Word e o novo build Windows estão em execução; a aprovação depende dos resultados finais.

# V88.154 — Calibração FH com toda a base de inventários

Data: 18/11/2026

Aplicativo de referência: 3.26.71-PRECAMPO-EXPERIMENTAL

## Regra de seleção da base

Calibração da altura ESA BIOMASS FH não pode depender exclusivamente do IFN/SFB. Consultar a base expandida inteira e selecionar cada fonte conforme as variáveis e a qualidade disponíveis. Inventários de árvore/parcela, bases institucionais, levantamentos acadêmicos, inventários de manejo e estudos publicados podem contribuir para calibração de altura, estrutura horizontal, AGB ou validação, desde que cada uso respeite a unidade amostral, o domínio e a proveniência.

Para pares de calibração H100–FH, exigir altura de campo compatível com H100 ou dados individuais suficientes para derivá-la, área amostral conhecida, localização/footprint, data, método, definição da métrica, fitofisionomia compatível e produto FH identificado. A métrica H100 é a média das 100 árvores mais altas por hectare; em parcelas menores, derivar o número equivalente a partir da área amostral. Não derivar H100 a partir de fonte sem área. Isso não impede que essa fonte contribua para parâmetros horizontais ou AGB quando esses indicadores tiverem denominadores e métodos compatíveis.

No pareamento, agregar FH ao footprint da parcela, respeitar resolução e erro de localização, manter a defasagem temporal explícita e impedir pseudorreplicação. Harmonizar a tipologia com IBGE legenda_1 e estratificar por microrregião/fitofisionomia. Validar por sítios/estudos independentes e propagar a incerteza de campo, produto, pareamento, tempo e transferência. Preservar FH bruto e calibrado em campos distintos. O modelo FH×estrutura horizontal gera uma estimativa única de AGB; CCI é contingência exclusiva para ausência FH real certificada.

## Correção da evidência de teste

No SHA `96f279c8d03e4e32376f5b6c2a2480c600efaa93`, a regressão Python e os checks de UI, imagem óptica CBERS-4A e pixels Sentinel-1 passaram. A prova MAAP separada leu pixels reais ESA FH em Sinop. Contudo, o autoteste do EXE compilado falhou no AOI de aceitação Tapajós com `ERRO_TECNICO_ROTA_PRIORITARIA` em FH/GTDX; o gate bloqueou corretamente a contingência e a publicação. O resumo detalhado da aceitação não foi impresso no log, então o próximo build inclui sua emissão sanitizada para identificar a causa concreta. Não liberar o artefato desse SHA como versão aprovada.

## Estado de implementação

A rotina de derivação H100 foi generalizada para aceitar um quadro harmonizado de qualquer fonte confiável e manter fontes distintas separadas mesmo quando os códigos de parcela coincidem. A rotina continua não criando pares FH–parcela nem integrando calibração ao fluxo AGB. A consulta de todas as fontes, a harmonização geoespacial/temporal, a calibração com validação espacial, a propagação de incerteza e o handoff até dashboard seguem como gates. A homologação científica permanece separada e pendente de validação de campo independente.

# V88.153 — referência H100 de inventário para calibração ESA FH

Data: 18/11/2026

Base: Enform Verde v3.26.71, branch `patches-3.26.6`

## Definição de altura

O produto ESA BIOMASS FH expressa H100: a média das alturas das 100 árvores mais altas por hectare. A função `derive_inventory_h100` deriva essa métrica de alturas totais por árvore nos microdados IFN, com área amostrada validada, bioma, fitofisionomia e microrregião. Registros de múltiplas hastes são consolidados por árvore; contagem insuficiente, ausência de área ou domínio incompleto bloqueiam o cálculo. A implementação não substitui nem corrige valores SAR diretamente.

## Uso em calibração

Para cada domínio produto × região × legenda_1 IBGE:

parear H100 de inventário com pixels FH espacialmente compatíveis e da época compatível;

reservar sítios externos completos para validação;

avaliar viés, RMSE, MAE, R² e intervalos dos resíduos;

só liberar modelo se a validação externa satisfizer limites previamente definidos;

avaliar o requisito de missão de RMSE abaixo de 30% para árvores acima de 10 m como referência de qualidade, sem tratá-lo como validação local.

A calibragem AGB deve então usar FH validado e parâmetros horizontais médios de inventários microrregionais (G, DAP, densidade e distribuição diamétrica), tendo AGB de inventário como resposta. ESA CCI segue contingência exclusiva quando ausência de FH foi comprovada em rotas completas e sem erro.

## Estado

A função de derivação H100 e seus testes unitários foram adicionados. Isso torna executável a preparação da referência de altura, mas o fluxo ainda precisa construir pares reais IFN–FH por microrregião/fitofisionomia e validar os modelos no pipeline/executável. A funcionalidade nacional não pode ser rotulada como calibrada até esse gate terminar.

# V88.152 — base oficial de inventários e calibração FH/CCI

Data: 18/11/2026

Base: Enform Verde v3.26.71, branch `patches-3.26.6`

## Fonte oficial incorporada

O Painel de Biomassa e Carbono do Serviço Florestal Brasileiro disponibiliza AGB derivada dos levantamentos IFN. Os metadados oficiais descrevem UA e coordenadas, fitotipologia, área por tipologia, equação, média de AGB por hectare e variância. O SFB também publica a tabela de equações e os fatores de raízes. Os dados abrangem levantamentos de 2011–2024 e foram atualizados em 2026. O build agora materializa e registra hashes da tabela de biomassa e do catálogo de equações; a base crua IFN/IBGE permanece integrada.

A tipologia do painel tem ressalva de ser inferida com fontes secundárias. A compatibilidade final deve ser conferida com o cruzamento espacial do IFN para legenda_1 IBGE; discrepâncias não podem ser silenciosamente aceitas. AGB do painel é uma estimativa alométrica oficial, não biomassa destrutiva observada. Sua variância e equação têm de acompanhar o pareamento.

## Fluxo acordado para altura e AGB

1. Derivar H100 de campo das medições DAP/altura IFN, com expansão pelo desenho amostral e área real da tipologia.

2. Parear H100 com pixels ESA FH espacial e temporalmente compatíveis, estratificados por produto, fitofisionomia IBGE e região. Reservar sítios externos; publicar viés, RMSE, MAE e R² da altura.

3. Derivar médias horizontais regionais de G, DAP, número de árvores e distribuição diamétrica com pesos e áreas do inventário; priorizar microrregião e nunca contar subparcelas como sítios independentes.

4. Ajustar/validar AGB por pares de inventário com FH e estrutura horizontal compatíveis, com grupos espaciais e incerteza que combine AGB do painel, amostragem, erro de altura e transferência.

5. Se existir FH utilizável, gerar só a estimativa FH + inventário. Só com ausência real e auditada de FH, usar CCI calibrado contra AGB IFN pareado em suporte/época. Nunca publicar CCI bruto como segunda estimativa.

6. Estimar raízes por equação alométrica adequada. `valor_r` do painel SFB é fator raiz/parte aérea e não deve ser rotulado como equação.

## Limite de status

O código nesta alteração materializa os dados oficiais e conserva sua proveniência; isso disponibiliza a matéria-prima que faltava. Ainda é necessário gerar o pareamento real com FH/CCI por microrregião/fitofisionomia, ajustar os modelos e validar em sítios não usados no ajuste antes de declarar calibração operacional. Não apresentar coeficientes fictícios nem divulgar o bloqueio anterior como falta definitiva de fontes; a fonte já foi encontrada e está sendo integrada.

# V88.151 — seleção FH e calibração do ESA CCI

Data: 18/11/2026

Base: Enform Verde v3.26.71, branch `patches-3.26.6`

Commit de código: `9112bde95714a27ea1856a32ff76213d181582f6`

## Correção realizada

O gate de seleção do ESA CCI foi alterado para cumprir a precedência FH:

qualquer pixel FH válido bloqueia a promoção do CCI;

ausência real de FH deve estar certificada por auditorias completas, paginaç…252152 tokens truncated…https://www.sema.mt.gov.br/transparencia/servico/Formulario/simlam/SIMLAM.html .

Minuta preparada: docs/solicitacao_LAI_SEMA_MT_inventarios_florestais.md

# V88.118 — Atualização do canal de pedido de informação

A página e-SIC da SEMA apresenta um link profundo de protocolo que retornou HTTP 404 na consulta de 16/11/2026. A página atual do Fale Cidadão é https://ouvidoria.cge.mt.gov.br/falecidadao/. A orientação da Ouvidoria-Geral/CGE indica autenticação pelo MT Login ou Gov.br, preenchimento do formulário “Informação”, delimitação do período e seleção do órgão responsável; o prazo publicado é 20 dias, com prorrogação por mais 10 dias mediante justificativa.

A minuta foi corrigida para apontar ao formulário ativo, indicar SEMA-MT e solicitar todos os períodos disponíveis. O solicitante deve autenticar-se diretamente no portal e não compartilhar credenciais. O pedido continua sem protocolo e nenhum microdado SEMA-MT foi obtido; a contagem de inventários utilizáveis não muda.

Fontes: https://ouvidoria.cge.mt.gov.br/saiba-mais-sobre-a-ouvidoria ; https://www.cge.mt.gov.br/en/perguntas-frequentes1 . Minuta revisada: docs/solicitacao_LAI_SEMA_MT_inventarios_florestais.md

# V88.119 — fechamento de testes locais e estado da candidata (16/11/2026)

O catálogo é consultado sob demanda, com limite de resultados e abertura em modo somente leitura para consulta. A alteração desta rodada atualiza apenas as expectativas dos testes para os dados já ingeridos; não incorpora novos microdados nem altera elegibilidade científica.

Contagem auditável: 4 conjuntos primários locais; 2 harmonizados em nível de parcela (IFN/DAP10 e Tapajós/ORNL); 2 microbases do projeto (Mexiana e Jalapão), que mantêm limitações de georreferenciamento/área. O IFN possui 841.387 registros arbóreos distribuídos por 8.951 UAs; volume de registros não equivale a parcelas validadas para modelagem, e o campo model_eligible permanece falso. SINAFLOR segue como agregados e localizadores administrativos, sem promoção automática a inventário primário.

Verificação de código: ambiente geoespacial isolado com GeoPandas, Requests, Shapely, Rasterio e Pillow; suíte integral com 1.247 testes OK e 1 skip; `tools/check_test_collection.py` passou em 183 módulos. A leitura live isolada de Sentinel-1 VV/VH retornou 9 pixels válidos por polarização em uma cena. É prova pontual de conectividade/leitura, não ensaio de vigor nem valida cobertura brasileira.

Limitações que permanecem: padrão visual sem execução por falta de servidor gráfico/display; handoff completo do cálculo de carbono ao dashboard pendente; build Windows/EXE pendente; ensaio end-to-end integral da Fazenda Maria Eduarda pendente; validação independente de vigor, previsão de safra e campo pendente; nenhum benchmark comparável de tempo foi realizado. Portanto, a candidata 3.26.59 segue experimental e não homologada.

# V88.132 — Correções pós-regressão e gates de evidência

A regressão completa executou 1.260 testes e registrou quatro falhas e um erro. Três problemas provinham da falta do passo de cruzamento espacial no workflow do dashboard: ingestão IFN não cria a tabela de cruzamento com o IBGE. O workflow foi corrigido para executar explicitamente tools/build_ifn_ibge_crosswalk.py após a ingestão, antes dos testes de seleção por localização, bioma e fitofisionomia. A seleção só é operacional quando a tabela ifn_sampling_unit_ibge_crosswalk está presente e auditável; ausência de correspondência não autoriza inferência de classe. O resultado da nova regressão permanece pendente.

A previsão de safra só recebe vigor SAR quando existem probabilidades completas, válidas, normalizadas e uma cena Sentinel-1 com identificador e acquisition_utc válidos dentro de 30 dias, sem aquisição futura. Sem evidência, a distribuição PAM permanece sem condicionamento de vigor e o painel informa o motivo.

A asserção de área dos blocos de 2 ha foi ajustada para admitir tolerância numérica de 1e-6 ha após reprojeção; o cálculo do algoritmo continua em EPSG:6933, com área mínima e pureza ≥90% inalteradas. Regressão após a correção pendente.

Evidência Windows desta execução: cobertura óptica CBERS-4A/WFI com pixels reais em 11 de 11 locais de amostragem e captura worker→Tk com pixel visível. O teste é de smoke e não equivale ao processamento do KML integral privado da Fazenda Maria Eduarda. A prova real de ESA BIOMASS FH ocorreu em Sinop e não comprova extração FH na fazenda. A homologação científica independente continua pendente.

# V88.133 — Vigor SAR aplicado à previsão e ao painel executivo

A primeira ponta agrícola deve manter coerentes leitura de vigor SAR, previsão e resumo executivo. O pipeline rejeita vigor sem identificador de cena e acquisition_utc válidos, aquisições futuras ou com mais de 30 dias e probabilidades inválidas. O painel não deve inferir incorporação a partir de uma lista de cenas ou de probabilidades apenas; seus indicadores positivos devem refletir fields[cultura].vigor_model_audit.used_in_yield_distribution, retornado pela simulação do modelo.

Quando a auditoria do modelo indicar não uso, os flags de vigor aplicado ficam falsos e o relatório apresenta motivo/N/D. Foi adicionada uma regressão de monitoramento→previsão→painel para cena datada sem scene_id. O modelo vigente continua PAM×clima com condicionamento de resíduos Monte Carlo por vigor elegível. A confirmação de leitura real e aplicação na AOI integral ainda depende dos gates live do novo SHA.

# Atualização V88.142 — quadros executivos e vigor no dashboard

Requisito geral de apresentação: iniciar cada relatório com um quadro executivo legível, no topo, e manter a trilha de auditoria separada do quadro. As abas de propriedade, área e referências, SAR/AGB, carbono nativo, agricultura/vigor/safra e base científica exibem cartões executivos antes do conteúdo detalhado. Se os rótulos esperados mudarem, o resumo deve recorrer às primeiras linhas dos resultados em vez de permanecer vazio.

A atualização assíncrona de clima no painel agrícola não pode remover o vigor SAR nem seu efeito no modelo PAM×clima. O cartão exibe, por cultura, status/classe, confirmação de uso baseada exclusivamente em vigor_model_audit.used_in_yield_distribution, probabilidades usadas, área e cobertura amostradas, aquisição Sentinel‑1 e safra da máscara. Classe SAR isolada não confirma uso na distribuição; a auditoria detalhada permanece em área separada.

A execução live de Sinop confirmou uma amostra experimental de soja: Sentinel‑1 RTC de 12/11/2026, aproximadamente 8 ha, seis blocos de referência, cobertura de 2,456% da máscara retrospectiva 2025/2026 e uso confirmado na distribuição PAM×clima. A área/cultura atual não foi confirmada, e a transferência para a safra projetada não foi quantificada. Café permaneceu N/D por ausência de blocos elegíveis.

A regressão integral do SHA 0f273d425115a38311c96ed0f0f1d30af083ffa5 executou 1.271 testes, todos OK; o gate documental falhou porque o prompt V52, a especificação de solos e este Word ainda não estavam sincronizados. Os testes focados do quadro executivo e a compilação de todos os módulos passaram. O build Windows e handoff live devem terminar no SHA final antes de liberar pacote; esta amostra não equivale a validação agronômica nem homologação de campo.

# V88.143 — versão 3.26.66-PRECAMPO-EXPERIMENTAL

A versão da aplicação foi incrementada para 3.26.66-PRECAMPO-EXPERIMENTAL após a correção dos quadros executivos e da persistência do resultado de vigor SAR no painel agrícola. Resumos devem permanecer no início dos relatórios e separados da trilha de auditoria; o quadro agrícola informa o uso do vigor somente quando vigor_model_audit.used_in_yield_distribution=true.

A versão 3.26.65 no SHA anterior compilou, passou o autoteste de EXE em pasta limpa e sua regressão integral executou 1.271 testes OK. Esses resultados não substituem os gates do novo SHA 3.26.66, que deve passar novamente pela regressão integral, build e autoteste Windows e handoff SAR live.

A prova de Sinop é experimental: vigor de soja calculado sobre amostra de aproximadamente 8 ha, seis referências, 2,456% da máscara retrospectiva 2025/2026 e auditoria confirmando uso condicional na distribuição PAM×clima. Não confirma cultura atual nem transferência para a safra projetada. O gate científico independente permanece bloqueado por falta de validação de campo independente; não declarar homologação científica.

# V88.145 — Inventários multifonte e prioridade FH

A comparação independente da ESA CCI consulta todas as referências de AGB numéricas, harmonizadas e compatíveis por bioma e fitofisionomia, sem depender da disponibilidade do IFN. O IFN é uma fonte, não a base completa. Cada estudo fica separado com instituição, região, citação, tamanho amostral e incerteza publicada quando disponíveis. Não agrupar estudos sem compatibilidade estatística demonstrada e não somar referências ao estoque CCI.

Metadados de catálogo, microdados sem área amostral ou sem vínculo espacial e fitofisionômico confiável não sustentam AGB/ha; permanecem pendentes de harmonização e não são convertidos em valores estimados.

O gate FH preserva SAR_PROCESSADO_SEM_MODELO_AGB quando há pixels SAR auxiliares, registrando separadamente priority_height_route_status=ERRO_TECNICO_ROTA_PRIORITARIA. A falha técnica permanece explícita e bloqueia promoção de CCI. Testes focados locais: 18 passaram e 2 foram pulados por dependências; regressão integral, build/autoteste Windows e handoff live precisam passar no SHA final. Status pré-campo/experimental; sem declaração de homologação científica ou de execução da geometria privada integral da Fazenda Maria Eduarda.

# V88.145a — correção de falha no handoff do dashboard

A execução live do SHA b8972bf concluiu a amostra Sinop e falhou no processamento Tapajós porque a contagem de pixels válidos de altura FH chegou como None e o payload a comparou diretamente com zero. None é um estado legítimo de rota sem pixels; a decisão de existência agora normaliza esse campo para zero sem alterar nem remover o valor bruto da auditoria. Uma regressão dedicada cobre o contrato. O novo SHA deve repetir a suíte integral, build/autoteste Windows e handoff live antes da candidata ser considerada tecnicamente verificada.

# V88.146 — Enform Verde 3.26.68-PRECAMPO-EXPERIMENTAL (18/11/2026)

Correção da leitura de altura: o cliente GTDX prioriza os URLs HTTPS oficiais retornados pelo CMR e não passa os links s3:// destinados a acesso em nuvem ao cliente HTTP. Falhas técnicas permanecem identificadas como falhas; não são convertidas em ausência de cobertura.

A rota ESA BIOMASS FH tenta os rasters disponíveis nos produtos candidatos e preserva o resultado da leitura por arquivo. Zero pixels só certifica ausência quando download, busca e leitura de todos os candidatos foram concluídos sem erro. Mensagens e caminhos de erros técnicos são mantidos na auditoria.

O autoteste do EXE grava o artefato de diagnóstico antes de falhar e diferencia o bloqueio técnico FH/GTDX de indisponibilidade de referência de inventário. A contingência permanece bloqueada enquanto a rota prioritária estiver tecnicamente incompleta.

A comparação ESA CCI × inventários utiliza todas as referências numéricas harmonizadas e compatíveis do registro, não apenas IFN. Estudos permanecem separados, não são somados ao CCI, e registros de catálogo/microdados sem harmonização não geram estimativa por hectare.

Esta é uma candidata pré-campo/experimental. Build, suíte integral, handoff live e autoteste precisam passar no mesmo SHA antes de distribuição. Homologação científica e execução da geometria completa da Fazenda Maria Eduarda não estão comprovadas por testes em outras AOIs.

# V88.147 — Enform Verde 3.26.69-PRECAMPO-EXPERIMENTAL (18/11/2026)

Smoke live do SHA 49c2f17 processou o handoff de Sinop e Tapajós e leu altura ESA BIOMASS FH no Tapajós: 1.263 pixels válidos dentro da AOI e zero erros técnicos. O primeiro raster candidato não cobria a geometria, e o leitor avançou ao próximo candidato válido.

O artefato identificou falha de proveniência na apresentação: os valores e a distribuição de altura vinham do FH, mas o nome e caminhos exibidos pertenciam ao AGB ESA CCI. A correção mantém sar_height como objeto independente por estrato; dashboard, resumo e planilha usam produto, fonte, banda e caminhos do FH/GTDX. AGB CCI permanece em campos separados e nunca é rotulado como altura.

A comparação de inventários consultou IFN e o registro de todas as fontes agregadas harmonizadas. Para o recorte Tapajós, não houve UAs suficientes ou agregados compatíveis com a tipologia disponível; a comparação permanece N/D, sem extrapolação. Referências continuam separadas e não são somadas ao CCI.

Candidata 3.26.69-PRECAMPO-EXPERIMENTAL: repetir a regressão integral, handoff live, build e autoteste do EXE no SHA que contém a correção. A leitura FH do Tapajós no teste público não prova a geometria da Fazenda Maria Eduarda. A homologação científica depende de validação independente de campo.

# V88.148 — Enform Verde 3.26.70-PRECAMPO-EXPERIMENTAL (18/11/2026)

O artefato live do SHA 3999058 verificou que a altura FH L2A aparece com H100, fonte ESA BIOMASS e raster próprio, enquanto AGB permanece ESA CCI em campo separado. Foram lidos 1.263 pixels FH na formação florestal e um pixel savânico no recorte Tapajós; 333 e 4 pixels, respectivamente, no teste Sinop.

O relatório live agora resume altura a partir do objeto sar_height e informa produto, caminho e fonte de altura separadamente dos metadados da estimativa AGB. A exportação executiva deixa de exibir campos de altura sem métrica ou proveniência.

A comparação de inventários registra separadamente fontes pesquisadas, fontes harmonizadas cadastradas, referências compatíveis e fontes efetivamente elegíveis. A base inclui microdados IFN, painel SFB/IFN e todos os agregados harmonizados do registro; apenas compatibilidade exata sustenta valores por hectare. Ausência de registros compatíveis gera N/D com auditoria, não extrapolação.

Candidata 3.26.70-PRECAMPO-EXPERIMENTAL. A regressão e o handoff anteriores passaram em SHA 3999058; estas alterações de relatório/inventário aguardam CI, build e autoteste no novo SHA. Sem homologação científica independente ou execução da geometria integral da Fazenda Maria Eduarda.

# V88.149 — Enform Verde 3.26.71-PRECAMPO-EXPERIMENTAL (18/11/2026)

Autoteste Windows anterior bloqueou a rota prioritária FH no Tapajós porque o processo do EXE em pasta limpa não recebia ESA_MAAP_OFFLINE_TOKEN, embora o job ESA MAAP separado tivesse o segredo. É uma falha de configuração de autenticação, não ausência de produto ou cobertura.

O passo de aceite EXE recebe o token por variável de ambiente protegida. automatic_pipeline aceita token explicitamente fornecido e, quando ausente, usa ESA_MAAP_OFFLINE_TOKEN; o token não é gravado em logs/auditoria. Um teste cobre essa precedência.

A mesma candidata incorpora o resumo de auditoria altura FH/GTDX separado de AGB CCI e lista de fontes de inventários pesquisadas/compatíveis. FH válido no Tapajós foi demonstrado em SHA anterior; build, handoff e aceite Windows desta nova configuração ainda precisam passar no SHA final.

# V88.157 — checkpoint de calibração FH, inventários e release

Data: 18 de novembro de 2026 | Aplicativo em validação: 3.26.71-PRECAMPO-EXPERIMENTAL | Branch: patches-3.26.6 | Commit: 894835bae7fdf35a972efe652f95a79ce55e413f

## Diretrizes consolidadas

Consultar toda a base expandida de inventários confiáveis, sem limitar a análise ao IFN/SFB. Avaliar separadamente altura, suporte/área, coordenadas, erro posicional, período, método, fitofisionomia, estrutura diamétrica, área basal, AGB e proveniência. Inventários sem área amostral para H100 ainda podem contribuir para parâmetros horizontais e AGB quando denominadores e métodos forem sustentados.

Calibrar ESA BIOMASS FH com alturas compatíveis, pareadas espacial e temporalmente com pixels e máscara QA. Derivar H100 de árvores apenas quando métrica, área/footprint e protocolo estiverem documentados. Preservar FH bruto e calibrado separadamente.

Construir modelos microrregionais por fitofisionomia IBGE legenda_1 integrando FH e parâmetros horizontais, com validação independente por sítio/estudo ou blocos espaciais e propagação de incerteza. Exibir uma única estimativa AGB e intervalo preditivo de 95% quando sustentados.

Usar CCI AGB somente após ausência real e auditada de FH em todas as rotas, sem erro técnico, e com calibração compatível. Usar médias de inventário somente se nenhum SAR utilizável existir de fato. FH disponível sem modelo aplicável não é ausência de cena e não autoriza contingência.

Estimar biomassa abaixo do solo com equações alométricas adequadas ao domínio e incerteza explícita; não tratar relações raiz:parte aérea como constantes universais.

## Auditoria de dados e software

A ingestão CI anterior contou 841.387 observações IFN, 8.951 unidades em seis biomas e 439.970 linhas agregadas do painel SFB com 222 equações. Esses quantitativos comprovam dados carregados, não pares FH–inventário nem calibração.

A base de projeto contém 2.390 árvores sem georreferenciamento; ORNL Tapajós contém 30 parcelas com H100, G e AGB de 2010 e domínio limitado aos suportes documentados. A prova MAAP em Sinop leu 2.304 pixels FH (média 18,284 m), comprovando leitura, não calibração.

O commit 4305b29 normalizou datas textuais, datetime e seriais Excel. O commit 894835b corrigiu a comparação cronológica com datas ausentes. O teste rápido pré-campo passou; o workflow de homologação científica independente falhou por falta de evidência validada de campo.

No momento do checkpoint, os workflows Windows, SAR live e dashboard ainda estavam concluindo a materialização/testes da base IFN. Não havia EXE nem SHA-256 novo publicado para 894835b. O build anterior falhou em produzir AGB prioritária/inventário elegível para o AOI amplo do Tapajós apesar de FH válido.

Não declarar esta versão operacional ou cientificamente homologada até que a suíte integral, SAR até dashboard e autoteste do EXE limpo passem no mesmo SHA e que haja suporte empírico/validação para o modelo AGB. Não inventar coeficientes, pares, precisão ou cobertura.

# V88.158 — recuperação verificável do download SFB

Data: 18 de novembro de 2026. O build Windows materializou 841.387 observações IFN em 8.951 unidades e gerou 8.951 correspondências únicas à legenda_1 do IBGE. A etapa falhou ao baixar o CSV do Painel SFB: a conexão terminou em 53.099.717 bytes, restando 45.819 bytes, sem retentativa/resume no downloader anterior.

Foi implementado download em streaming com retentativas limitadas, retomada Range com validação de Content-Range e ETag/Last-Modified, reinício seguro quando Range é ignorado e verificação do comprimento. O arquivo final é substituído atomicamente somente depois de validar o CSV. Cinco testes locais de unidade passaram. A correção aguarda a nova execução CI/live.

Os timeouts PronaSolos em três locais ocorreram em etapa opcional continue-on-error e foram registrados como indisponibilidade técnica, não ausência de solo. A prova real FH em Sinop passou, mas a homologação científica independente segue bloqueada por falta de pares FH–inventário e validação de campo. A versão segue pré-campo; não há EXE/hash novo neste checkpoint.
