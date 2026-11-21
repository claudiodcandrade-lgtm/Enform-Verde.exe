# V88.104 — inventários integrados e paralelização segura (16/11/2026)

## Versão e estado

- Candidata `3.26.53-PRECAMPO-EXPERIMENTAL`.
- O smoke Windows do canvas recebeu correção geométrica: centraliza/redimensiona a janela dentro do desktop e verifica que o recorte inteiro do canvas está visível antes de aceitar pixels.
- A suíte local completa e o novo build/smokes Windows ainda são gates; não liberar EXE até todos passarem.

## Tempo de processamento

- Pedologia e fertilidade dependem apenas da AOI. As duas etapas agora rodam em um worker dedicado ao mesmo tempo que uso da terra e carbono/SAR, com no máximo duas etapas concorrentes no worker principal.
- Nenhuma fonte, limiar, pixel, resolução, estrato, modelo, equação, incerteza ou fallback científico foi removido ou reduzido. Falhas de cada etapa mantêm o status e a justificativa próprios.
- A auditoria/checkpoint registra duração de uso da terra, carbono, pedologia, fertilidade, worker e modo de execução. A sobreposição pode diminuir o tempo total quando solo e carbono têm duração relevante; ganho real ainda não foi medido. Comparar execuções fria e aquecida na mesma AOI e configuração antes de declarar redução. Referência histórica: 292 s fria; a repetição aquecida não concluiu em 180 s.

## Base de inventários

- Foi integrada a microbase harmonizada do histórico do projeto: 2.144 árvores em 167 parcelas de Mexiana/Santo Ambrósio e 246 registros distribuídos em 10 parcelas de Jalapão; campanhas duplicadas não são contadas outra vez.
- Mexiana: parcelas de 250 m² conforme histórico; média derivada de AGB alométrica `418,6616 Mg/ha`; área basal média derivada `36,4256 m²/ha`; DAP médio arbóreo `25,1882 cm`; altura média medida `14,9603 m`. A biomassa não é destrutiva. Sem georreferenciamento por parcela e sem pares SAR; as classes FOD aluvial e FOD de terras baixas estão agregadas, não atribuídas por parcela. Pode sustentar referência estrutural regional para várzea estuarina na foz do Amazonas conforme solicitação do proprietário, mas não é calibração/validação SAR nem autoriza separar as duas formações. Excluir savanas e campos.
- Jalapão: manter DAP, altura e táxons observados. Área de parcela e subtipo IBGE não confirmados; não calcular stems/ha, área basal/ha ou AGB/ha, não inferir coordenadas nem validar SAR.
- Tapajós/ORNL 1552 continua como a única base institucional primária já harmonizada no pacote. Assim, há três conjuntos primários locais ao todo (um institucional publicado e dois dados do projeto); somente um está empacotado como base institucional pública pronta. Essa contagem não equivale a cobertura nacional.

## Prioridade de ingestão de fontes

1. Dados primários publicados por instituições de pesquisa, com unidade amostral, licença, método e domínio verificáveis.
2. Inventários ambientais cujo anexo esteja disponível em repositório oficial e cujo aceite expresso do próprio inventário esteja comprovado por documento/decisão, URL, hash, método e unidade. Anexos sem essa prova continuam apenas como leads.
3. Dados locais fornecidos pelo proprietário como referência complementar, com estado de acesso, georreferenciamento e limites explícitos.
4. Bases oficiais administrativas e números de autorizações/processos servem para localizar estudos; não contam como inventários independentes nem entram em modelos.

O catálogo inclui como metadados ainda não baixados: IFN DAP10 set/2025 (27 planilhas por UF), Dryad/Amazônia Oriental (126 parcelas secundárias), ORNL DAAC 1563/Acre e NASA/ORNL Paisagens Sustentáveis Brasil. Nenhum desses quatro registros alimenta cálculos até download, hash, licença, unidade amostral e compatibilidade serem verificados. A versão SFB set/2025 foi listada no catálogo oficial como 27 arquivos estaduais; isso é uma família de dados por UF, não 27 inventários independentes.

## Evidências e testes

- Testes novos verificam as métricas derivadas de Mexiana, o bloqueio de métricas por hectare no Jalapão, a classificação das fontes no catálogo e o registro dos tempos por etapa.
- A evidência de redução de tempo, a suíte completa e o build/smokes Windows permanecem pendentes até a execução final.
- Fontes verificadas para o catálogo: SFB IFN DAP10 set/2025 (`https://dados.florestal.gov.br/pt_BR/dataset/ifn-dap-10-por-uf_disp-set2025`); Dryad DOI `10.5061/dryad.6t1g1jxdp`; ORNL DAAC DOI `10.3334/ORNLDAAC/1563`; NASA Open Data Portal para Sustainable Landscapes Brazil.
