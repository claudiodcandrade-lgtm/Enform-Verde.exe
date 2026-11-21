# V88.106 — Catálogo de inventários sob demanda

**Versão candidata:** 3.26.55-PRECAMPO-EXPERIMENTAL
**Data:** 16/11/2026

## Registro para a especificação técnica

Implementada a arquitetura SQLite de consultas sob demanda: carregamento idempotente de sementes por fingerprint SHA-256, índices compostos, consultas parametrizadas read-only, limite de 200 registros e cache LRU (128 chaves) invalidado por mudança física do banco. Descoberta remota permanece explícita. A triagem catalográfica não promove fontes a cálculo quantitativo. Testes focados passaram; validação de tempo total por benchmark comparável ainda pendente, assim como a suíte completa e gates Windows.

## Implementação

- A inicialização do catálogo mantém a atualização idempotente dos portais e calcula SHA-256 do conjunto de arquivos-semente. Se a impressão digital não mudou, a aplicação não relê nem reprocessa os CSVs estruturais, agregados e microdados.
- SQLite ganhou índices compostos para filtros de bioma/fitofisionomia/tipo/prioridade, fonte/nível/elegibilidade/acesso e UF/microrregião/bioma.
- `query_inventory_candidates()` faz consulta pontual com conexão `mode=ro`, `query_only`, parâmetros preparados, limite máximo 200 e cache LRU de até 128 consultas. O cache usa caminho, mtime e tamanho do banco, filtros e limite; gravações detectáveis invalidam a chave.
- A consulta do catálogo serve para descoberta e triagem. Não injeta médias nem inventários candidatos automaticamente nos cálculos de biomassa/carbono; permanecem exigidos compatibilidade de fitofisionomia, proveniência, licença, método, unidade, suporte e elegibilidade verificada.
- O cache só cobre consultas de metadados; resultados científicos, SAR, cálculos da AOI e artefatos de carbono não são reutilizados sem suas próprias chaves de identidade e validação.

## Ganho e limites

A leitura repetida de CSVs e a busca sem filtros na inicialização foram removidas quando o catálogo está atualizado. Não há benchmark controlado nesta revisão; portanto, a redução de tempo total da análise ainda não está quantificada. A primeira inicialização após alteração dos arquivos-semente continuará fazendo a carga completa uma vez. A descoberta remota continua separada e só ocorre por ação explícita.

## Verificação

Testes específicos cobrem: carga idempotente, consulta limitada, abertura em modo somente leitura, fontes de pesquisa e regras de aceite/processo. A suíte completa e `tools/check_test_collection.py` devem passar antes de push. Interface visual/build Windows dependem do ambiente Windows e permanecem gates próprios.

## Resultado desta revisão

- `python -m unittest discover -s tests`: **1.237 testes passaram; 1 skip**.
- `tools/check_test_collection.py`: passou; **183 módulos** verificados.
- `git diff --check`: passou após remover espaços finais das novas linhas de catálogo.
- `ui_visual_standard.py`: não executável para validação visual neste ambiente sem display (`TclError: no $DISPLAY`). O gate visual Windows e o build/autotestes Windows não foram executados; manter candidata experimental.
