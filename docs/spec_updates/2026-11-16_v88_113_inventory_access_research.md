# Complemento de pesquisa sobre acesso a inventários florestais públicos

Consulta realizada em 16/11/2026 para orientar a curadoria e a descoberta de microdados primários. Este complemento não altera a versão do software (3.26.59-PRECAMPO-EXPERIMENTAL / V88.113) e não promove automaticamente um catálogo ou uma autorização administrativa a inventário utilizável.

## Serviço Florestal Brasileiro e Inventário Florestal Nacional

O portal oficial do SFB disponibiliza conjuntos do IFN por variável e Unidade da Federação. Entre os arquivos estão levantamentos de árvores com DAP ≥ 10 cm e DAP ≥ 5 cm, além de regeneração, uso da terra, solos, coletas botânicas e outros componentes. A página do IFN DAP 10 lista arquivos CSV estaduais e informa atualização em 02/07/2026; a página DAP 5 também lista arquivos estaduais e informa atualização em 01/07/2026. A página oficial do mapa interativo, publicada em setembro de 2025, informa cobertura de 68% do território brasileiro e exploração por bioma, estado e lotes de coleta/unidades de planejamento.

Como escala histórica, o SFB informou em janeiro de 2025 que, até dezembro de 2024, havia medido 1.000.185 árvores, concluído coleta em 21 UFs e inventariado 5,13 milhões de km². Esses números referem-se ao IFN como um programa nacional; não são contagem de inventários independentes nem de conjuntos primários locais.

## IBAMA e SINAFLOR

O Portal de Dados Abertos do IBAMA publica conjuntos SINAFLOR para PMFS e POA, separados entre Amazônia Legal e outros biomas, com recursos CSV, XML e JSON. As páginas de PMFS Amazônia Legal e POA Outros Biomas registraram atualizações em julho de 2026 e frequência semanal.

O esquema público de POA Outros Biomas expõe campos de processo e unidade de manejo e, conforme o tipo de inventário, atributos por árvore como nome científico, DAP/CAP, altura comercial, volume, área basal e coordenadas, além de processo de amostragem, forma/área de parcela, total de parcelas e estatísticas amostrais. É uma rota potencialmente capaz de revelar microdados primários, e não apenas uma lista bibliográfica. A unidade de contagem, o status de aprovação, o tipo de inventário e os campos preenchidos precisam ser verificados nos arquivos baixados; linhas de árvores não equivalem a inventários distintos.

O FAQ oficial do IBAMA confirma que projetos submetidos no SINAFLOR incluem planilhas de inventário e mapas armazenados no sistema, disponíveis aos órgãos ambientais competentes. Isso não significa que todos os anexos de qualquer processo estejam abertos para download público. Manter a rota de acesso oficial, sem contornar autenticação; quando houver dados publicados, coletar somente os campos necessários à análise e excluir CPF/CNPJ e demais dados pessoais do banco analítico.

## Contagem e consequência para a base do projeto

Não foi localizado nas fontes oficiais consultadas um total nacional deduplicado de inventários independentes publicamente acessíveis. O IFN publica várias famílias de arquivos por estado e variável; SINAFLOR publica registros de planos, autorizações, árvores e estatísticas. Não contar arquivos, árvores, parcelas, autorizações ou processos como inventários independentes.

A base primária local documentada permanece com três campanhas/conjuntos harmonizados: Tapajós/ORNL (fonte institucional publicada) e os dados de Mexiana/Santo Ambrósio e Jalapão fornecidos no projeto. Somente uma fonte institucional pública está integrada como conjunto primário pronto; os dois conjuntos locais mantêm sua proveniência e limites próprios. As novas páginas do IFN/SINAFLOR são rotas prioritárias de recuperação, ainda não constituem ingestão nem aumentam essa contagem até download, hash, deduplicação e validação de parcelas/campos.

## Rotina operacional acrescentada

1. Ingerir os CSV estaduais DAP 10 e DAP 5 do IFN e preservar UF, ID de unidade/subunidade/parcela, árvore, DAP, altura, espécie, coordenada, data, status e metadados disponíveis; registrar versões e SHA-256.
2. Consultar os datasets SINAFLOR PMFS e POA (Amazônia Legal e outros biomas). Filtrar processos aprovados segundo evidência oficial, distinguir censo 100% de inventário amostral e separar árvores, parcelas, autorizações e campanhas.
3. Vincular o inventário aprovado ao processo/plano e ao documento/anexo ou recurso primário específico. Aprovação do plano é evidência de aceite conforme decisão do proprietário, mas não substitui a recuperação do conteúdo necessário ao cálculo.
4. Harmonizar apenas após validar unidade, variáveis, limiar DAP/CAP, geometria/posição, desenho amostral, data e licença/acesso. Deduplicar por processo, campanha, parcela, árvore e remedição. Não incluir PII no banco de análise.
5. Promover a `BAIXADO_HARMONIZADO_LOCAL` somente após arquivo recuperado, hash, parser validado e compatibilidade ecológica/estatística. Até lá, conservar como lead de alta prioridade.

## Fontes oficiais consultadas

- SFB, IFN DAP 10 por UF: https://dados.florestal.gov.br/pt_BR/dataset/dap-10-por-uf-ifn
- SFB, IFN DAP 5 por UF: https://dados.florestal.gov.br/pt_BR/dataset/dap-5-por-uf-ifn
- SFB, mapa interativo IFN: https://www.gov.br/florestal/pt-br/assuntos/noticias/2025/setembro/novo-mapa-interativo-facilita-acesso-aos-dados-do-inventario-florestal-nacional-ifn
- SFB, mais de um milhão de árvores medidas: https://www.gov.br/florestal/pt-br/assuntos/noticias/2025/janeiro/ifn-ultrapassa-a-marca-de-1-milhao-de-arvores-medidas-no-brasil
- IBAMA, SINAFLOR PMFS Amazônia Legal: https://dadosabertos.ibama.gov.br/pt_BR/dataset/sinaflor-pmfs-amazonia-legal
- IBAMA, SINAFLOR POA Outros Biomas: https://dadosabertos.ibama.gov.br/dataset/sinaflor-poa-outros-biomas
- IBAMA, esquema de dados POA Outros Biomas: https://dadosabertos.ibama.gov.br/dados/SINAFLOR/poaOutrosBiomas.html
- IBAMA, FAQ SINAFLOR e envio de planilhas de inventário: https://www.gov.br/ibama/pt-br/acesso-a-informacao/perguntas-frequentes/sistemas/sinaflor
