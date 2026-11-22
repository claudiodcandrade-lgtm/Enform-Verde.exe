# Enform Verde v3.26.53-PRECAMPO-EXPERIMENTAL

## Fluxo de processamento

- A análise pedológica e de fertilidade, que depende apenas da AOI, agora executa em paralelo com a classificação de uso da terra e o processamento SAR/carbono. O limite é de duas etapas concorrentes; entradas, modelos, cálculos, precedência dos resultados e tratamento de erro permanecem iguais.
- O checkpoint e a auditoria passam a registrar tempo de uso da terra, carbono, pedologia, fertilidade, duração total e modo de execução. Esta versão ainda não comprova redução do tempo total: comparar execução fria e aquecida na Fazenda Maria Eduarda, com a mesma AOI, cache e resultados, antes de declarar ganho.

## Inventários

- A microbase histórica foi integrada ao catálogo: 2.144 árvores/167 parcelas da Ilha Mexiana e 246 registros/10 parcelas do Jalapão. As cópias repetidas da mesma campanha não são somadas.
- Mexiana permite derivar estrutura horizontal e AGB alométrica por parcela com a área histórica de 250 m²; média de AGB derivada: 418,66 Mg/ha; área basal média derivada: 36,43 m²/ha. AGB não é biomassa destrutiva. Parcelas sem coordenadas; FOD aluvial e de terras baixas não estão separadas por parcela; não há validação SAR. A fonte é referência estrutural regional complementar para a várzea estuarina da foz do Amazonas, conforme escopo indicado pelo proprietário.
- Jalapão permanece em métricas amostrais não normalizadas: área de parcela e subtipo IBGE não confirmados; valores por hectare e calibração SAR ficam indisponíveis.
- A prioridade principal permanece com parcelas/dados de pesquisa publicados e dados oficiais aprovados cujo anexo e aceite expresso sejam verificáveis. Contagens de autorizações/processos não contam como inventários.
- O catálogo adiciona quatro fontes públicas em estado `METADADO_VERIFICADO_DADOS_NAO_BAIXADOS` (IFN DAP10 set/2025, Dryad Amazônia Oriental, ORNL Acre 1563, NASA/ORNL Paisagens Sustentáveis). Nenhuma entra nos cálculos até baixar, validar licença, unidade amostral, geografia e variáveis.

## Smoke do mapa Windows

- O smoke redimensiona e centraliza a janela no desktop e reprova capturas em que o canvas excede a tela. Isso corrige o bloqueio de CI anterior, que mostrava imagem Sentinel-2 e canvas parcialmente fora do recorte.

## Estado de liberação

Candidata experimental pré-campo. A suíte local completa, verificação de coleta, padrão visual e build/smokes Windows no SHA final são obrigatórios. Não há homologação de campo nem executável liberado até todos os gates Windows passarem. A análise de Mexiana/Jalapão não é validação de área nem pareamento SAR.
