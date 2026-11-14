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
