# V87.45 — gates de Windows e científicos na branch 3.26.6 (09/11/2026)

## Correção de processo de liberação
A branch `patches-3.26.6` estava publicada, mas os workflows de Windows e homologação científica não eram acionados por `push` nela. Os workflows agora incluem explicitamente essa branch. A correção altera somente os gatilhos de CI; não altera a lógica científica, o conteúdo dos patches V87.39–V87.43 nem a branch principal. O commit do gatilho é `028dcd6bcbcb7267038a66b767a7b897ed9cc4cb` localmente; o commit publicado via API é `e2aa95ad7d0e02d3043253cdce7a20099127fb4e`.

## Critérios de interpretação
O build Windows deve verificar o SHA exato, dependências, regressões, leitura real de fontes e o autoteste `--network-check` antes de produzir o ZIP pré-campo experimental. O gate científico é independente e fail-closed. Se não houver evidência observacional real para um domínio ou módulo, seu resultado permanece N/D com motivo; saída experimental ou concordância com PRODES/TerraClass não vira homologação de campo. Modelos testados/homologados compatíveis continuam prioritários; experimentais são contingência explicitamente identificada.

## Estado nesta revisão
O gatilho foi publicado e a consulta de status imediatamente após o push ainda não retornou verificações. A suíte local completa iniciou, mas a execução não terminou dentro da janela observada e foi interrompida; portanto não há declaração de suite completa aprovada. A liberação do executável depende de confirmar build e artefato no SHA final. Homologação científica nacional continua bloqueada até os manifests e dados independentes exigidos pelo gate.
