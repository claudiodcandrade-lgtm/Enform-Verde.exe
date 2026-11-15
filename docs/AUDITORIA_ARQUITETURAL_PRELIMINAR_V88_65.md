# Auditoria arquitetural preliminar V88.57

Data da leitura: 14/11/2026. Base de código examinada: `417e93141ec035d5bb414abb620224d490580927` (3.26.35-PRECAMPO-EXPERIMENTAL). Esta é uma revisão estática inicial de fronteiras críticas, não uma auditoria exaustiva nem execução ponta a ponta. Os achados abaixo são riscos observados no código; ainda precisam de correção/regressão e confirmação com a AOI real.

## Achados verificáveis

1. **Caminho com SAR local executa trabalho pesado no thread da interface.** Em `desktop_app.py:2780`, `execute()` chama `_execute_main()` diretamente quando `self.sar_paths` existe. `_execute_main()` executa uso do solo, carbono, aquisição/leitura SAR, pedologia e fertilidade antes de atualizar os painéis (`desktop_app.py:2870–2932`). Isso cria um caminho capaz de bloquear a janela durante I/O e processamento. A rota padrão sem SAR local inicia worker (`desktop_app.py:2781` em diante). **Ação:** unificar ambas as rotas no worker; manter widgets e publicação no thread Tk; incluir cancelamento, timeout e erro por estágio.

2. **A contingência de inventário pode repetir a aquisição/modelagem SAR.** `native_carbon_analysis()` chama `sar_estimator(aoi, biome, physiognomy)` dentro do loop de interseções de fitofisionomia potencial (`desktop_app.py:498–502`) depois de `summarize_native_carbon()` já ter executado estimadores. A cache declarada é por análise e pode reduzir algumas consultas, mas não demonstra que todo download, raster e processamento seja reutilizado. **Ação:** guardar um resultado SAR por AOI/execução e consultar o certificado de ausência uma única vez; fazer a contingência consumir esse objeto imutável, sem reiniciar o pipeline.

3. **A evidência do teste de handoff não é uma execução real do core.** `tests/test_core_to_dashboard_handoff.py:23–32, 87–115` cria resultados de fixture e chama o callback da interface; comprova encaminhamento/representação desses objetos no dashboard, mas não comprova aquisição de cenas, leitura de pixels, classificação e cálculo pela AOI completa. **Ação:** preservar o teste rápido e adicionar um teste de integração com resultado real gravado/reprodutível e hash da AOI, além de execução Windows da Fazenda Maria Eduarda até o painel.

4. **A contingência IFN implementada tem cobertura geográfica restrita.** `ifn_carbon_fallback.py:51–89` aceita Amazônia e Floresta Estacional Sempre-Verde em MT, seleciona até cinco unidades IFN em raio de 250 km e exige cinco unidades válidas. Isso é um cenário regional explicitamente condicionado, não uma rota nacional para todas as fitofisionomias. **Ação:** publicar a matriz de cobertura por bioma/fitofisionomia e implementar/evidenciar fontes compatíveis onde houver dados; onde não houver suporte, retornar N/D com motivo e sem extrapolação disfarçada.

5. **O estado agregado do pipeline merece contratos mais estritos.** `desktop_app.py:2927–2936` classifica falha parcial principalmente por prefixos `ERRO/FAILED/FAILURE`. Estados de indisponibilidade ou ausência de dado com outros nomes podem acabar em `CONCLUIDA_COM_ESTADOS_DECLARADOS`. Essa etiqueta é menos forte do que sucesso, mas o consumidor precisa de um contrato explícito para diferenciar execução concluída, resultado parcial, ausência confirmada e etapa não executada. **Ação:** usar enumeração de estado por etapa e agregação baseada em estado tipado; testar estados `ERRO_TECNICO`, `AUSENCIA_CENAS`, `N/D_DADOS`, `NAO_EXECUTADO` e sucesso.

## Limites e plano de revisão

- A CI da versão reporta 1.156 testes e testes remotos de componentes; a CI disparada para o commit documental `6097f9cb9bf07b2738d4eb6c8f7805b0ef983a5f` ainda estava em execução na consulta desta atualização. Não somar essa execução pendente às evidências concluídas.
- A prova da Fazenda Maria Eduarda permanece incompleta: o KML integral não foi executado do carregamento até o dashboard nesta base de evidências. O gate científico independente continua reprovado por falta de medições de campo; o produto permanece pré-campo experimental, não homologado.
- A revisão seguinte deve percorrer entrada/CRS/geometria, busca e paginação dos provedores, autorização/renovação, leitura e validade dos pixels, alinhamento temporal/orbital, máscaras/cobertura, modelos e incerteza, cache/concorrência/memória, contratos de saída, serialização/exportação e atualização dos dois painéis. Para cada achado: arquivo/linha, gatilho, consequência, correção, teste de regressão e evidência Windows.
- Priorizar depois: refatorar o caminho síncrono `sar_paths`; eliminar processamento SAR repetido na contingência; ampliar matriz de cobertura de inventários sem extrapolação sem suporte; formalizar máquina de estados; completar a execução ponta a ponta com KML real e manter artefatos de auditoria.

## Conclusão

A revisão profunda pode avançar e já revelou riscos concretos de arquitetura e lacunas de cobertura. Ainda não está concluída e nenhum destes achados deve ser declarado corrigido pela CI atual. As correções e a prova ponta a ponta são o próximo gate antes de afirmar que os erros recorrentes foram resolvidos.


## V88.58 — estado das primeiras correções

No código `2eda195edf89986381e2cf55651f0de16ab4edef` (3.26.36), os achados 1 e 2 receberam correções: fluxo SAR local no worker e cache de uma execução SAR para a contingência AOI-wide. Foram incluídos testes de regressão. Status desta atualização: implementação publicada na branch, CI ainda em execução; não marcar como validada até o dashboard/build concluírem. Os achados de handoff real, cobertura nacional IFN e máquina de estados continuam pendentes. O teste com KML integral da Fazenda Maria Eduarda continua pendente.


## V88.59 — resultado da regressão e estado do build

No commit a52b9818ba8c31ba62a238d30a54f0a280d0c0c5, regressões SAR local/worker e reutilização do SAR passaram; a suíte completa passou com 1.158 testes e todos os módulos foram compilados. O workflow dashboard falhou somente no guard documental por exigir atualização de prompt, DOCX e especificação de solo depois do último commit de teste; a sincronização foi publicada após esse commit. Build Windows ainda em execução; aguardar a CI do commit documental antes de declarar o empacotamento concluído. Os achados de execução real do core até a AOI e cobertura nacional IFN continuam pendentes.


## Fechamento operacional V88.60

O workflow Windows da versão 3.26.36-PRECAMPO-EXPERIMENTAL concluiu com sucesso, incluindo o self-test do EXE em pasta limpa e upload do artefato. Os smokes live documentados cobriram óptico, Sentinel-1 RTC/INPE nos seis biomas, IBGE Tapajós e BIOMASS FH em AOIs com inventário. A evidência não elimina a necessidade de confirmar a execução local até o dashboard da Fazenda Maria Eduarda. O gate científico permanece reprovado sem observações independentes de campo. Consulte `APP_RELEASE_NOTES_v3.26.36.md` para o hash verificável e o link do artefato.


## Adendo V88.61 — fontes de inventários e resposta sobre causas (14/11/2026)

### Causa: o que a auditoria realmente comprovou

Não foi encontrada uma única causa raiz para todas as versões malsucedidas. A auditoria preliminar observou múltiplos mecanismos: (a) trabalho SAR pesado no thread de interface quando havia SAR local; (b) risco de repetir a execução SAR na contingência por fitofisionomia; (c) teste de handoff baseado em fixtures que não percorre aquisição→pixels→classificação→cálculo→dashboard para o KML completo; (d) fallback de inventário baseado apenas em um domínio limitado do IFN; (e) estado agregado do pipeline com distinções insuficientemente tipadas. Os itens (a) e (b) receberam correções e regressões reportadas em 3.26.36. Os demais continuam sendo pendências ou achados em verificação; a auditoria não provou que expliquem, sozinhos, todos os sintomas históricos. A falha da Fazenda Maria Eduarda até o dashboard integral continua sem reprodução validada.

### Atualização da estratégia de inventários

A cobertura limitada do fallback IFN é uma limitação de arquitetura/dados, não evidência de que o IFN seja a única fonte disponível no Brasil. PNLA permite localizar informações básicas de licenciamento; SINAFLOR/IBAMA disponibiliza bases de PMFS/POA, planilha padrão de Inventário Florestal 100% e dados de volumes explorados. Porém uma licença ou registro de PMFS não garante que as tabelas de parcela estejam abertas, anexadas ou ingestíveis automaticamente. Portanto, registrar estados distintos: fonte descoberta, documento obtido, dados primários extraídos, campos validados e estudo elegível.

A seleção deve abranger inventários publicados no Brasil por instituições reconhecidas (incluindo Embrapa, INPA, universidades, órgãos ambientais e repositórios), mais IFN e estudos técnicos de licenciamento/PMFS quando acessíveis. Prioridade máxima: instituições reconhecidas com inventários na mesma fitofisionomia e na mesma microrregião/região; entre esses, preferência pelos que oferecem dados primários de parcelas abertas. Depois, outras fontes publicadas progressivamente menos específicas, com transferência e incerteza explicitadas. Instituição reconhecida favorece confiabilidade documental, mas não substitui avaliação de método, amostragem, domínio ecológico e qualidade dos dados. Não reconstruir microdados de médias publicadas.

Fontes oficiais consultadas nesta atualização: PNLA/MMA (serviço de consulta de licenciamentos); IBAMA, SINAFLOR (conjuntos de PMFS/POA e planilhas padrão); dados abertos IBAMA “Volumes Explorados — IF 100%”. Os dados de volumes explorados não são equivalentes a observações completas de parcelas.

### Estado e próximos gates

Este adendo corrige a especificação da cobertura de fontes; não adiciona, por si só, conectores nem dados ingeridos ao programa. Implementação exige catálogo versionado com proveniência, conectores de aquisição legal, parsers e validação, deduplicação, testes de elegibilidade por região/fitofisionomia e execução reproduzível. A aprovação de software exige ainda executar o KML integral da Fazenda Maria Eduarda até o painel no Windows; a homologação científica exige validação independente de campo. Build e testes de contrato não substituem esses gates.


## V88.62 — reafirmação dos requisitos de incerteza e serrapilheira

Reafirma-se o requisito arquitetural já estabelecido: toda estimativa de carbono deve reportar incerteza por compartimento e para o total, com método, unidades, cobertura, componentes considerados e limitações. Intervalo de confiança só pode ser chamado de IC95% quando sustentado por cálculo estatístico apropriado. Incerteza parcial deve ser rotulada; quando não quantificável, exibir N/D e motivo. A auditoria da implementação deve percorrer painéis, relatórios, planilhas, mapas e exportações para encontrar valores sem incerteza ou com rótulos indevidos.

Reafirma-se também a inclusão arquitetural do compartimento serrapilheira no escopo de carbono nativo. Priorizar estudos gravimétricos e inventários compatíveis com a mesma fitofisionomia e microrregião/região, publicados por instituições reconhecidas; entre os compatíveis, dar preferência aos dados primários de parcelas abertas. IFN é uma referência válida quando aderente e pode servir de contingência. Validar massa seca, protocolo e estação, fator de carbono, unidade, parcelas e incerteza; separar serrapilheira de necromassa e SOC. Não converter médias publicadas em dados de parcelas. Sem base suficiente, saída N/D, não zero.

Estes requisitos documentais ainda não são prova de implementação ou de funcionamento ponta a ponta. O fechamento técnico requer regressões que cubram todas as saídas, dado gravimétrico realmente ingerido, build do mesmo commit e execução integral da Fazenda Maria Eduarda até o dashboard; homologação científica continua a depender de validação independente.


## V88.63 — achado de apresentação de incerteza

A revisão estática do candidato 3.26.36 identificou que, apesar de estimativas sustentadas serem impressas, o relatório executivo e o resumo de clareza ainda podiam mostrar “N/D” ou “não quantificada” em campos de incerteza, sem o rótulo requerido “incerteza não mensurável”. Isso é uma lacuna no contrato de apresentação, não evidência de que o valor principal esteja necessariamente sem suporte. A correção prevista preserva valor sustentado, rotula o parâmetro e a razão e usa N/D somente para estoque não estimável.

O IFN e estudos gravimétricos compatíveis já possuem rotas no código; esta alteração não cria essas bases nem valida uma fonte nova. O candidato 3.26.37 ainda precisa passar regressões, suíte integral, documentação sincronizada e build Windows do mesmo SHA. A execução integral do KML Sinop e validação científica independente continuam pendentes.


## V88.63 — sincronização das regressões da candidata 3.26.37

O teste integral da revisão anterior executou 1.160 testes; as regressões agora exigem “incerteza não mensurável” para estoques suportados sem incerteza quantificável. A nova revisão deve repetir CI e build Windows no mesmo SHA; manter resultado experimental pré-campo até esses gates e as validações de campo.

## Evidência de validação da candidata 3.26.37

Commit validado: `9c4c60c76ce5cd88ec6ff29420db36c2d631c8e2`. Dashboard: 1.160 testes aprovados e guard documental sem pendências (execução 43652675732). Build Windows: aprovado, incluindo smoke óptico nacional, leitura no canvas Tk, SAR real e autoteste do EXE em pasta limpa (execução 43652675738). Provas independentes reais ESA BIOMASS FH e Sentinel-1 Sinop também aprovadas. Artefato `Enform-Verde-Windows-v3.26.37-PRECAMPO-EXPERIMENTAL`: 197.799.200 bytes; SHA-256 do pacote: `sha256:65b49f7980f3058bd5b8c55fdbd806d62188b1a931e1e37bbdc28e1062832232`.

Estado: candidata experimental pré-campo. A homologação científica independente permanece reprovada por ausência de validação de campo e de execução ponta a ponta do KML completo da Fazenda Maria Eduarda até o painel; não usar estes gates como comprovação de homologação ou desempenho de campo.


# V88.64 — auditoria do caminho SAR até o painel (14/11/2026)

## Resposta à falha recorrente

A evidência histórica de leitura de pixels SAR descrevia a etapa SAR isoladamente. Ela não demonstrava que a execução da aplicação continuou, que módulos subsequentes terminaram, nem que os dados chegaram ao painel. A causa concreta identificada no código é o tratamento de exceção amplo do worker: uma falha após o processamento de uso da terra podia substituir todos os resultados por uma mensagem de erro, descartando da interface saídas SAR e de classificação já válidas. Isso é consistente com o sintoma descrito pelo usuário. Outras causas de falha de leitura (credenciais, transporte, paginação, decodificação, leitura raster e dependências) continuam distintas e devem permanecer classificadas como ERRO_TECNICO.

## Alterações preparadas em 3.26.38

- Capturar erros de carbono nativo, pedologia e fertilidade individualmente e manter resultados das etapas bem-sucedidas.
- Representar carbono indisponível como N/D com motivo, sem declarar cobertura nativa zero ou imputar estoques.
- Propagar um analysis_run_id e hash da geometria AOI entre SAR, uso da terra, carbono e dashboard.
- Persistir resumo da execução em checkpoint local; falha de escrita não deve apagar resultados em memória.
- Mostrar no painel/auditoria status, erro por etapa e vínculo com a mesma AOI.
- Acrescentar regressões de entrega worker→painel para falha de carbono e solo.

## Evidência e limites

O KML integral da Fazenda Maria Eduarda foi prevalidado quanto à geometria e área, mas isso não é processamento do aplicativo. Históricos de pixels e cenas processadas representam evidência de etapa SAR, não prova ponta a ponta; não há neste checkpoint evidência reproduzível ligada ao mesmo SHA de que o KML integral chegou ao dashboard com SAR, classes, carbono/estados N/D e relatório. O arquivo KML não foi incluído no commit nem deve ser publicado.

A alteração preparada passou por compilação sintática local de desktop_app.py e do novo arquivo de regressão. A suíte completa, guard documental, workflows Windows/dashboard e execução integral da AOI ainda devem ser confirmados no commit final. Até lá, 3.26.38 não está validada e não há novo artefato a disponibilizar como versão funcional. A candidata permanece pré-campo experimental; validação de campo e homologação científica permanecem pendentes.

## Checklist de aceite da AOI

1. Reproduzir no Windows usando o KML privado e gravar hash da geometria, versão, commit e run_id.
2. Registrar a leitura real de cenas/pixels com datas e contagens, distinguindo ausência comprovada de falha técnica.
3. Confirmar que a mesma execução entrega classes e áreas; conferir carbono por compartimento ou N/D/ERRO_TECNICO com motivo.
4. Confirmar painel, relatório e checkpoint com run_id/hash idênticos e divergências de área explicitadas.
5. Arquivar logs sem tokens, credenciais, URLs assinadas ou limites da propriedade em repositórios/artefatos públicos.


# V88.65 — resultado final de CI/build da candidata 3.26.38 (14/11/2026)

## Resultado verificado

- Commit de código: dc79606d4073da23cf5c83aed54a23d500f1ef1a.
- Dashboard 43659083027: 1.160 testes aprovados; descoberta integral, compilação dos módulos e guard documental sem falha.
- Build Windows 43659082998: aprovado. O EXE foi construído, testado em pasta limpa e empacotado.
- Gates live aprovados: smokes ópticos nacionais; Sentinel-1 com pixels reais no Tapajós e fontes nacionais nos seis biomas; prova ESA BIOMASS FH em Sinop; IBGE/SICAR e contratos de biomassa.
- Artefato Enform-Verde-Windows-v3.26.38-PRECAMPO-EXPERIMENTAL, 197.808.715 bytes; SHA-256 ZIP e85085a2085453cfd8a54e9a601fc85c2e237434c39146a83b4cc0f829f93c2a. A publicação do PR permanece draft.

## Interpretação e limite da Fazenda Maria Eduarda

Esses gates demonstram funcionamento operacional dos testes e rotas indicadas. Eles não executaram o KML integral da Fazenda Maria Eduarda do carregamento à classificação, carbono/estados por compartimento, painel e relatório numa única execução vinculada pelo mesmo run_id/hash. Portanto, a versão foi construída e validada pelos gates de CI, mas a propriedade ainda não foi homologada ponta a ponta. A evidência antiga de pixels SAR deve continuar classificada como resultado de etapa isolada.

O gate independente de homologação científica permanece reprovado por falta de validação de campo e da execução integral da AOI. A versão 3.26.38 continua experimental pré-campo; não declarar funcionamento comprovado na fazenda, homologação nacional ou validação de campo.

## Causa e contenção

Uma exceção após o processamento de uso da terra podia descartar saídas SAR/classificação antes da entrega à interface. A candidata captura os erros posteriores por módulo, preserva etapas válidas e vincula os resultados à mesma execução/AOI. Falhas de aquisição SAR continuam classificadas separadamente como erros técnicos; pixel isolado não significa análise concluída.
