# V87.2 — liberação experimental Windows: verificação por SHA

Este registro foi criado após a sincronização da especificação Word V87.2 pelo workflow [41969843046](https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/41969843046), que concluiu com sucesso e gerou o commit de documento binário. O commit de código `d20ea7ffb3493f6b56a031d79193576463028eb3` corrige três contratos da suíte regressiva antiga: exigência de ambos os prompts e especificação de solo no gate Word, e cancelamento de build obsoleto do PR sem dispensar conferência de SHA. A suite rápida nesse código passou em runs 41969843073 e 41969848499.

Este commit exclusivamente documental posterior ao commit do bot permite que os workflows de PR iniciem novamente sob uma autoria habilitada a Actions. Antes de liberar o executável, exigir: suite integral sem falhas, build PyInstaller Windows bem-sucedido, `--ui-smoke`, `--module-check`, `--visual-check`, `--acceptance-test` em pasta Windows limpa, correspondência de Git SHA, manifesto SHA256 e artefato ZIP de download não expirado.

**A homologação científica independente continua condicionada a evidências observacionais reais.** A versão `3.26.1-PRECAMPO-EXPERIMENTAL` é uma candidata técnica operacional que não pode ser chamada de validação científica ou certificação de estoques.
