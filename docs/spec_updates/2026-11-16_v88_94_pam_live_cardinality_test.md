# V88.94 — corrige cardinalidade do teste live PAM no Windows (16/11/2026)

## Defeito reproduzido

O build Windows `43792729175`, no commit `a7f9ff5606e1aef3361e052097b0a238a583dea5`, executou corretamente a materialização live da PAM/SIDRA, que retornou 150.660 registros. O teste `tests.test_sidra_pam_materializer` ainda exigia a contagem histórica fixa de 133.920 linhas (oito produtos) e reprovou antes dos smokes restantes e da compilação do EXE. O materializador já inclui nove produtos, entre eles algodão herbáceo. É uma asserção de teste desatualizada; não se deve reduzir nem descartar os dados atuais para satisfazê-la.

## Correção aplicada

O teste agora valida cardinalidade e integridade contra os metadados gerados na mesma execução: contagem total, SHA-256, unicidade da chave produto/território/ano/variável, correspondência dos produtos à fonte registradora, cobertura dos anos, variáveis e contagens por produto, e tripletos numéricos reconciliáveis. Não fixa número de linhas nem total de culturas. Isso permite crescimento legítimo do conjunto live sem remover a verificação de integridade.

## Verificação e estado

Os dois testes locais de `tests.test_sidra_pam_materializer` passaram após a correção; `py_compile` e `git diff --check` também passaram. A primeira execução Windows falhou somente nesse teste; portanto, não houve EXE nessa execução. O novo commit precisa repetir a suíte Windows, smokes ópticos/SAR, integração SAR→carbono/dashboard em Sinop e Tapajós e compilação/autoteste do EXE antes de disponibilizar o binário. O teste SAR de integração da execução anterior ainda estava em andamento no momento deste registro. O gate científico permanece separado e bloqueado até evidência independente de campo.
