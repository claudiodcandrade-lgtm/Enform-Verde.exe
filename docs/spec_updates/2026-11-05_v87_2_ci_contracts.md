# REVISÃO V87.2 — 05/11/2026 — TESTES DE CONTRATO DE DOCUMENTAÇÃO E COMPILAÇÃO

Referência: execução Windows `41967733301` no SHA `132512d68ecf99e7424cb6cd43c7d2212e9c501f`; 920 testes executados, 3 testes de contrato falharam por expectativas obsoletas (não por algoritmos biofísicos): `test_docs_sync_checkpoint.WordSyncGateTests.test_original_code_commit_may_use_active_word_bot`; `test_docs_sync_checkpoint.WordSyncGateTests.test_same_commit_word_still_valid`; `test_v82_national_ci_contract.NationalCIContractTests.test_workflows_group_by_sha_and_never_cancel_doc_build`.

## Alterações implementadas e motivo

1. As regras atuais em `tools/check_docs_updated.py` exigem, a cada modificação efetiva, atualização conjunta de `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md`, `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md` e `docs/ESPECIFICACAO_SOLO_PRONASOLOS_0_100_2026-10-28.md`, além de Word diretamente no commit OU por checkpoint ativo em `.github/workflows/sync-full-spec-word.yml` com Word existente. Dois testes antigos omitiam os dois documentos históricos. Os testes foram corrigidos para exigir os três documentos no sucesso, e para recusar a ausência de qualquer um deles, do checkpoint, do Word ou da referência no workflow.
2. O gate antigo exigia `cancel-in-progress:false`, incompatível com a regra posterior de não desperdiçar recursos e evitar que jobs obsoletos do mesmo PR continuem a compilar. Agora o teste exige `cancel-in-progress:true`, concorrência por número PR/ref, checkout por `github.event.pull_request.head.sha || github.sha` e verificação `git rev-parse HEAD` nos workflows Windows e dashboard.
3. O código científico, limites de incerteza SOC 0–100 cm (V87.1), estimativas experimentais/sem observações fictícias (V86–87), pedologia, fertilidade, SAR e agricultura permanecem inalterados.
4. `APP_VERSION=3.26.1-PRECAMPO-EXPERIMENTAL` permanece; executável é candidato somente até `Build Enform Verde Windows` passar, `--ui-smoke`, `--module-check`, `--visual-check`, `--acceptance-test` passarem e o ZIP/manifesto SHA256 do SHA final existir. A homologação independente continua fail-closed sem dados primários.

## Status e trilha de auditoria
A revisão e as alterações de contrato constituem um checkpoint versionado, não uma aprovação retroativa dos 920 testes nem uma alegação de compilação já concluída. Os últimos testes, build e artefatos devem ser aferidos pela execução do SHA novo.


## Revisão V87.3 — otimização do processamento de análises

Data: 05/11/2026. Commit de implementação: `ccbb2498f4d0ada11d48ec04989812e6b0bf8d77`. Prompt canônico V43 atualizado no commit anterior desta revisão.

### Alteração no algoritmo

Em `mapbiomas_zonal.py::summarize_class_grid`, agregação de classes foi reestruturada para operar em blocos de 64 linhas. Em cada bloco, uma única seleção NumPy reúne os códigos válidos e `numpy.bincount` soma suas áreas ponderadas por linha. Isso elimina a chamada a `numpy.unique` e a iteração Python em cada linha, mantendo memória temporária limitada pelo tamanho do bloco.

### Contrato funcional preservado

A máscara espacial, NoData, exclusão de classes não positivas, áreas geodésicas por linha, legenda, área mapeada e cálculo dos percentuais continuam com as mesmas definições. Apenas a ordem da acumulação de números de ponto flutuante pode mudar arredondamentos nas últimas casas. Não há mudança na classificação, nos dados, no carbono, na incerteza ou nos critérios científicos.

### Gate de desempenho e qualidade

Não afirmar percentual de aceleração sem benchmark controlado e repetível. Para o SHA final, exigir regressão numérica em casos com múltiplas classes, NoData, pixels externos à AOI e áreas distintas por linha, suíte completa, build Windows e autoaceitação do executável em diretório limpo. Comparar valores com tolerância numérica explícita e verificar memória em AOIs pequenas e grandes. Se surgir divergência material ou regressão, reverter a alteração antes da liberação.

A revisão é uma otimização localizada do agrupamento zonal MapBiomas. Outras otimizações devem ser guiadas por perfilamento do fluxo completo e manter chaves/invalidação corretas de cache por AOI, fonte, versão e parâmetros. O SHA `ccbb2498f4d0ada11d48ec04989812e6b0bf8d77` tem workflows Windows e suíte integral disparados; a liberação depende dos resultados no commit final, incluindo os documentos desta revisão.

Estado científico: candidato operacional `3.26.1-PRECAMPO-EXPERIMENTAL`; a homologação científica independente continua pendente de observações reais e não é substituída por regressões ou build.


## Revisão V87.4 — Google Satélite online e mapa offline sob demanda

Data: 05/11/2026. Código: commits `791a3d91a4bba8585761c740228489ddcca8080f` e `c49535ce025b2e0ad0c47cad97d4bdfa3e64f30b`. Prompt canônico atualizado no commit `9ba244196f7509503911a476bcfc914d13ae76f2`; PR #50.

### Fluxo da visualização

Ao carregar uma AOI, a interface desenha inicialmente somente o contorno da geometria e inicia as fontes online em worker. Quando há chave, a primeira tentativa é Google Maps Static API com `maptype=satellite`. Sem chave ou diante de falha do Google, o fluxo tenta Sentinel-2 e serviços Esri. A rasterização do mapa vetorial IBGE fica para o caso em que todas as fontes online falhem. O mapa IBGE continua empacotado como fallback offline; não é removido.

O satélite do Google é apenas fundo visual: não pode alimentar classificação de vegetação/cultura, análise SAR, biomassa, carbono, solo ou produtividade. A chave deve vir de `GOOGLE_MAPS_API_KEY` ou da entrada local do programa, nunca de um valor fixo no repositório. API Static Maps requer API key e billing ativo, tem cobrança por carregamento conforme uso e recomenda restrição da chave à API habilitada. Não persistir imagens fora das regras aplicáveis.

### Viewport e proporção

Altura do canvas ampliada de 420 para 560 px. A solicitação calcula dimensões dentro do limite de 640×640 mantendo a proporção do viewport, e a imagem usa scale 2 para preservar resolução. O pedido online fica fora da thread da interface. A visualização normal deixa de rasterizar o mapa offline antes da resposta online; isso reduz trabalho de abertura do mapa, mas não altera nem acelera os cálculos científicos SAR, biomassa, solo ou uso da terra.

### Verificações de liberação

No SHA final, verificar build Windows, suíte de interface, Google com chave válida, ausência de chave, falha Google com fallback online, falha de todas as fontes com fallback IBGE, aspect ratio/viewport e isolamento entre fundo visual e motores analíticos. Não declarar esta revisão como aceleradora do processamento numérico sem benchmark independente. A otimização V87.3 MapBiomas permanece isolada e exige sua própria regressão de equivalência. A homologação científica independente continua separada.

Referências oficiais Google Maps Platform: Maps Static API start, usage and billing e API key setup, links mantidos no prompt canônico V87.4.
