# Enform Verde 3.26.1-PRECAMPO-EXPERIMENTAL

**Estado:** candidato a versão técnica experimental; **NÃO É LIBERAÇÃO HOMOLOGADA**. A presença deste arquivo não demonstra que houve build, testes Windows ou download. Apenas distribuir após aprovação de testes compilados do mesmo SHA e publicação de pacote/manifesto com SHA256.

## Objetivo e escopo

Operacionalizar resultados modelados oriundos de dados reais para futura comparação com medições de campo, sem preencher evidências independentes com dados artificiais e sem perder os módulos anteriores de carbono, SAR, Embrapa/PronaSolos 0–100 cm, classificação de solos, fertilidade, agricultura, vigor, clima e safra.

## Alterações desde 3.26.0

- Motor `modeled_field_validation.py`: previsão por fitofisionomia e compartimento, com área espacial, densidade (tC/ha), estoque (tC, tCO2e), método, fonte, `trace_sha256`, intervalo condicionado e lacunas marcadas N/D. A origem e o método não podem ser “N/D”, “desconhecido”, “None” ou vazio; não há previsão válida em área nula.
- `previsoes_experimentais_pre_campo.json` e `planilha_entrada_medicoes_campo.csv` (sem observações inventadas) ficam junto aos demais relatórios espaciais da análise.
- Excel: aba `Modelo Para Campo`, com onze colunas e a coluna de medição de campo em branco, além das abas existentes. Contexto e validade das estimativas preservados.
- Biomassa subterrânea: preserva intervalos condicionais de alometria (quando fornecidos), sem apresentar IC95% da propriedade. Modelos de biomassa e inventários carregam identificadores de fonte; solo 0–100 cm transporta metadados institucionais e envelope de limites marginais, quando recuperáveis.
- Fertilidade química e estoque SOC: cache bruto WCS autenticado pelo ID do produto, fonte e checksum SHA256 antes de reutilização; pixels N/D/fora da AOI não contam como estimativa. Média espacial não equivale a análise laboratorial no imóvel; DP espacial não é IC95% da previsão.
- `enform_build_source.py` é gerado no build PyInstaller com SHA exato dos fontes compilados; testes do EXE exigem SHA, módulos e dados locais. Gate científico independente permanece fail-closed.
- CI GitHub: workflows de build e dashboard substituídos cancelam jobs obsoletos de commits anteriores; a execução do SHA atual deve ser verificada antes da liberação.
- Código e documentação atualizados: revisão V87, dois prompts, especificação de solos, checkpoint científico e especificação Word.
 
## Testes e limitações

Testes unitários de contratos experimentais e geoespaciais passaram em SHA anterior da V86. Os novos testes da V87, GUI Windows, aceitação real, disponibilização dos dados SAR, licenças oficiais, acurácia em cinco biomas e compilação final aguardam execução e evidência do **SHA final**. Os intervalos declarados são de fonte/cenário ou condicionais; não constituem cobertura calibrada da AOI. Não permitir certificação científica por este candidato experimental.


### CORREÇÃO CIENTÍFICA V87.1 — 05/11/2026 — ENVELOPE MARGINAL DE SOC NÃO É INCERTEZA PREDITIVA VALIDADA

Em `soil_pronasolos_zonal.py`, quando houver os dez rasters oficiais de limites (`lower`/`upper` por cinco horizontes), o resultado deve manter `status=ENVELOPE_MARGINAL_OFICIAL` e `sum_bounds_envelope_tc_ha=[soma(L), soma(U)]`, mas **`predictive_uncertainty_quantified=False`** tanto em `official_uncertainty` quanto no compartimento `0–100 cm`. A nova chave `marginal_envelope_available=True` identifica a existência dos limites informativos sem inferir erro de previsão calibrado da AOI. Os testes `test_marginal_bounds_envelope_not_joint_ci` passam a verificar as duas semânticas. Não retirar limites, transformar DP espacial em intervalo ou atribuir IC95% da propriedade. Esta correção é parte do candidato experimental **3.26.1-PRECAMPO-EXPERIMENTAL**, não constitui nova homologação científica. O build Windows, contratos no HEAD e artefato assinado SHA256 continuam obrigatórios para liberação.


### REVISÃO V87.2 — 05/11/2026 — CORREÇÃO DOS TRÊS TESTES DE CONTRATO DESATUALIZADOS

A suíte completa Windows no SHA `132512d68ecf99e7424cb6cd43c7d2212e9c501f` executou **920 testes, com três falhas**; nenhum daqueles três achados prova regressão no código de carbono: `test_original_code_commit_may_use_active_word_bot` e `test_same_commit_word_still_valid` aceitavam apenas o prompt recente (não exigiam prompt histórico e especificação de solos), contrariando a regra efetiva do validador; `test_workflows_group_by_sha_and_never_cancel_doc_build` exigia `cancel-in-progress:false` apesar de a política atual cancelar compilações obsoletas do mesmo PR e conferir SHA exato em checkout e pacote.

**Correções incorporadas aos testes, sem relaxar os gates:** `tests/test_docs_sync_checkpoint.py` usa `PROMPT`, `HISTORICAL_PROMPT`, `SOIL_SPEC`, `SPEC` e checkpoint ativo; testa tanto sucesso documental completo (Word direto ou revisão em bot) quanto recusa de cada documento ausente, checkpoint ausente e Word indisponível. `tests/test_v82_national_ci_contract.py` exige checkout pelo SHA do PR/push, verificação `git rev-parse HEAD`, agrupamento do mesmo PR/branch e `cancel-in-progress:true` para jobs obsoletos. O cancelamento nunca autoriza reutilizar EXE de SHA diferente. V87.2 preserva todos os resultados experimentais, SOC e sua semântica V87.1, pedologia, fertilidade e interface; muda apenas os contratos de CI e documentos associados.

**Condição de saída:** repetir a suíte completa e compilar `3.26.1-PRECAMPO-EXPERIMENTAL` em Windows sobre o mesmo SHA final, verificar testes reais de exe, arquivo ZIP, manifesto SHA256 e link de artefato; não declarar homologação científica independente enquanto faltarem observações e evidências verificáveis. A publicação de versão experimental poderá ocorrer com avisos claros de modelos condicionais e N/D, sem falsificar acurácia.
