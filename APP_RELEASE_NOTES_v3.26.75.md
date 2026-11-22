# Enform Verde v3.26.75-PRECAMPO-EXPERIMENTAL

Data: 18/11/2026

## Correções e otimização

- Mantém a compatibilidade explícita pai/subformação para listar referências agregadas do Tapajós como balizas separadas. Essas referências não geram AGB da AOI, calibração FH ou acréscimo ao estoque.
- O registro harmonizado de referências agregadas é lido e indexado em memória uma vez por revisão do arquivo. A chave considera caminho, tamanho e data de modificação; alterações invalidam o cache. Leitores de AGB, estrutura e fontes reutilizam o mesmo índice.
- A seleção IFN consulta primeiro o índice composto de bioma e legenda_1 do IBGE; mantém a busca compatível de grafia como fallback. Leituras de árvores seguem sob demanda, limitadas às UAs selecionadas e usando o índice da base SQLite de 466 MiB.
- O status de integridade dessa base grande já é armazenado em cache por revisão do arquivo para evitar novas contagens completas em cada consulta.

## Estado científico e de distribuição

Esta é uma candidata pré-campo experimental, não homologada. Referências agregadas não substituem parcelas pareadas e não geram estimativa quantitativa. AGB continua N/D quando não há modelo elegível. A disponibilização de executável requer build Windows, autoteste limpo e gates de aceite no SHA final; nenhum EXE ou resultado homologado é declarado por estas alterações locais.

## Verificação local (18/11/2026)

- Regressão integral: 1.312 testes aprovados e 1 ignorado; coleção: 191 módulos.
- `--self-test` e `--module-check` passaram; o Word V88.165 foi sincronizado no branch de validação.
- O build Windows e o autoteste de cópia limpa ainda precisam concluir no SHA final. Este registro não declara EXE liberado nem homologação científica.
