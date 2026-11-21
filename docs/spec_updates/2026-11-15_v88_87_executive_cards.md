# V88.87 — quadros executivos claros em todas as abas (15/11/2026)

## Mudança de apresentação
- Todas as seis abas principais agora exibem um quadro executivo com borda e título, com resumo curto e dinâmico da tarefa/resultado central.
- Os quadros exibem valores e estados centrais; relatórios extensos e proveniência técnica ficam sob títulos próprios de detalhes/auditoria.
- Propriedade e área: perímetro e hectares; mapas: bioma e fitofisionomia potencial com aviso de que não confirmam cobertura atual.
- SAR/AGB: estado de processamento; catálogo é separado de leitura de pixels; altura SAR só é indicada como entregue quando há produtos no payload.
- Carbono: cobertura nativa, estoque conhecido, completude e incerteza; o estoque permanece parcial quando faltam compartimentos.
- Agricultura: estado SAR atual, cultura e previsão extraídos do próprio relatório; o quadro se atualiza também após a resposta climática assíncrona.
- Base científica: apresenta a hierarquia de inventários e compatibilidade; dados regionais continuam identificados como referência, não medição da propriedade.
- Ao iniciar pesquisa nova, os quadros limpam os valores anteriores para evitar mistura entre AOIs.

## Verificação
- `compileall` e `tests.test_executive_panels` (2 testes) passaram.
- `tools/check_test_collection.py` inspecionou 175 módulos, mas terminou com código 1 porque módulos geoespaciais não importam sem as dependências do ambiente.
- O padrão visual da janela não pôde ser verificado localmente: `ui_visual_standard.py` não importou `desktop_app` porque este ambiente não contém `requests`. Executar a suíte visual e o smoke da interface no Windows/CI antes de publicar o EXE.
- Não altera modelo científico, sensores, limiares nem estoques. O código candidato é 3.26.46-PRECAMPO-EXPERIMENTAL, SHA `88f9b67cc4f9cfdce04e9f974cff192dcc03af82`, e permanece pré-campo experimental e não homologada.
