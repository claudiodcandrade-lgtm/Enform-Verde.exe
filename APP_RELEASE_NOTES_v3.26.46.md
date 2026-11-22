# Enform Verde 3.26.46-PRECAMPO-EXPERIMENTAL

## Quadros executivos em todas as abas

- Cada uma das seis abas principais passa a ter um quadro executivo com borda, título e texto curto, usando a paleta e tipografia existentes.
- Propriedade e mapas resumem perímetro, área, bioma e fitofisionomia potencial; o fundo visual é explicitamente separado dos dados analíticos.
- SAR/AGB resume estado do processamento, distingue catálogo de pixels lidos e indica quando altura SAR chegou ao painel.
- Carbono destaca área nativa, estoque conhecido, completude e estado da incerteza; resultados longos permanecem em seção identificada como relatório detalhado e auditoria.
- Agricultura resume classificação atual, cultura, produtividade e produção; a auditoria e proveniência seguem em área separada. Base científica resume hierarquia e aplicação de inventários.
- Os quadros são atualizados ao carregar perímetro, consultar dados e concluir análise; ao apagar a pesquisa, os resumos anteriores são limpos.

## Verificação

- Compilação Python aprovada.
- `tests.test_executive_panels`: 2 testes aprovados; verifica quadro nas seis abas e separação das áreas de detalhes.
- `tools/check_test_collection.py` inspecionou 175 módulos, mas não concluiu por falta de dependências geoespaciais; `ui_visual_standard.py` não executou porque falta `requests`. Build Windows e smoke visual são necessários antes de liberar o executável.
- KML privado integral da Fazenda Maria Eduarda e validação científica de campo continuam pendentes. Candidata pré-campo experimental, não homologada.
