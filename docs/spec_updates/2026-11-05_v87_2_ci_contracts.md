# REVISÃO V87.2 — 05/11/2026 — TESTES DE CONTRATO DE DOCUMENTAÇÃO E COMPILAÇÃO

Referência: execução Windows `41967733301` no SHA `132512d68ecf99e7424cb6cd43c7d2212e9c501f`; 920 testes executados, 3 testes de contrato falharam por expectativas obsoletas (não por algoritmos biofísicos): `test_docs_sync_checkpoint.WordSyncGateTests.test_original_code_commit_may_use_active_word_bot`; `test_docs_sync_checkpoint.WordSyncGateTests.test_same_commit_word_still_valid`; `test_v82_national_ci_contract.NationalCIContractTests.test_workflows_group_by_sha_and_never_cancel_doc_build`.

## Alterações implementadas e motivo

1. As regras atuais em `tools/check_docs_updated.py` exigem, a cada modificação efetiva, atualização conjunta de `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v52.md`, `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md` e `docs/ESPECIFICACAO_SOLO_PRONASOLOS_0_100_2026-10-28.md`, além de Word diretamente no commit OU por checkpoint ativo em `.github/workflows/sync-full-spec-word.yml` com Word existente. Dois testes antigos omitiam os dois documentos históricos. Os testes foram corrigidos para exigir os três documentos no sucesso, e para recusar a ausência de qualquer um deles, do checkpoint, do Word ou da referência no workflow.
2. O gate antigo exigia `cancel-in-progress:false`, incompatível com a regra posterior de não desperdiçar recursos e evitar que jobs obsoletos do mesmo PR continuem a compilar. Agora o teste exige `cancel-in-progress:true`, concorrência por número PR/ref, checkout por `github.event.pull_request.head.sha || github.sha` e verificação `git rev-parse HEAD` nos workflows Windows e dashboard.
3. O código científico, limites de incerteza SOC 0–100 cm (V87.1), estimativas experimentais/sem observações fictícias (V86–87), pedologia, fertilidade, SAR e agricultura permanecem inalterados.
4. `APP_VERSION=3.26.1-PRECAMPO-EXPERIMENTAL` permanece; executável é candidato somente até `Build Enform Verde Windows` passar, `--ui-smoke`, `--module-check`, `--visual-check`, `--acceptance-test` passarem e o ZIP/manifesto SHA256 do SHA final existir. A homologação independente continua fail-closed sem dados primários.

## Status e trilha de auditoria
A revisão e as alterações de contrato constituem um checkpoint versionado, não uma aprovação retroativa dos 920 testes nem uma alegação de compilação já concluída. Os últimos testes, build e artefatos devem ser aferidos pela execução do SHA novo.
