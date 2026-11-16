# Enform Verde v3.26.49 — pré-campo experimental

## Inclusão de fontes nacionais, estaduais e de pesquisa

- Amplia o catálogo para 53 rotas: SFB/SNIF/IFN; IBAMA/SINAFLOR/licenciamento/PAMGIA; PNLA; SIMLAM Pará e Mato Grosso; SIAM, SLA, IDE-Sisema, IEF/MG e IFFSC/SC; IPAAM, SEDAM, IMAC; Embrapa, PPBio/INPA, ForestPlots, ICMBio, universidades, periódicos, CAPES/BDTD, SiBBr, NeoTropTree, speciesLink, Zenodo, Dryad e Dados.gov.br.
- Adiciona 20 conjuntos-base catalogados e corrige a associação das referências publicadas ao repositório/instituição de origem.
- Baixa temporariamente três recursos públicos oficiais do IBAMA, calcula contagens agregadas com SHA-256 e descarta os arquivos brutos ao fim. O banco embarca somente contagens, classificação, URLs e hash, sem dados pessoais ou linhas brutas.
- Captura 15/11/2026: PMFS SINAFLOR Amazônia Legal — 10.273 linhas, 1.508 IDs de registro e 6.619 autorizações; Volumes Explorados IF100 — 2.438.833 linhas, 2.665 IDs e 847 nomes científicos; licenças federais — 14.376 linhas, 2.532 processos, sendo 761 processos com ASV.
- As contagens de registros administrativos são pistas para localizar inventários, não contagens de inventários científicos independentes. A lista de SINAFLOR IF100 reflete exploração seletiva; não estima dominância natural, DAP ou área basal.
- Registra sistemas estaduais e fontes institucionais com método e status de acesso, incluindo inventários estaduais de Minas Gerais e Santa Catarina, PPBio, ICMBio e canal Fala.BR/LAI.

## Estado dos dados e validação

- O banco contém 80 registros catalográficos e 53 rotas. Permanecem 27 referências agregadas candidatas e somente um conjunto harmonizado local de 30 resumos por parcela do Tapajós; ele não contém composição árvore a árvore.
- A estimativa do número de inventários únicos acessíveis continua não mensurável até recuperar e deduplicar documentos de licenciamento/planos, teses e bases estaduais, conferindo método, licença e unidade amostral.
- 42 testes focados e compilação local passaram na validação final disponível. Suíte completa, build Windows e validação de campo não foram executados nesta rodada. Não declarar homologação nem EXE pronto.

## Auditoria Tapajós e limite geográfico para nomes de cultura

- O relatório recebido mostra 0,64 ha de soja e 1,92 ha de café na AOI Tapajós. No modelo de grade 80 m, 0,64 ha corresponde a um pixel e 1,92 ha a três pixels.
- A trilha de classificação recalcula as observações VV/VH para a AOI fornecida; não há cache compartilhado de classes por propriedade nessa rota. Não há evidência de que essas áreas tenham sido copiadas de Sinop.
- Foi encontrado um problema real: o modelo aceitava extrapolação experimental fora do envelope geográfico de treinamento, permitindo rótulos de cultura específicos. A versão agora só libera nomes de cultura quando a extensão completa da AOI está dentro desse envelope. No Tapajós, mantém possível área agrícola genérica como “cultura não identificada” e bloqueia previsão específica de soja/café. Sinop segue elegível a rótulos experimentais.
- Regressões cobrem Tapajós, Sinop, AOI que cruza a borda, granularidade 80 m e bloqueio de forecast específico. O resultado Tapajós fornecido não contém o KML privado; não foi possível reproduzir a classificação exata nesta execução.
- 42 testes focados e compilação dos módulos alterados passaram no ambiente local. O teste integrado SAR depende de `geopandas`, ausente neste ambiente; build Windows, CI e validação de campo não foram executados. Manter candidata pré-campo, sem homologação.

## V88.91 — acesso às fontes hierarquizadas de inventários (16/11/2026)

- A coleta acionada na aba **Base Científica** agora consulta CKAN do SFB/IFN e IBAMA, REDAPE/Dataverse, repositórios institucionais com OAI-PMH, REST público DSpace onde disponível e Zenodo. PNLA, PAMGIA autenticado, ForestPlots e fontes sem API confirmada permanecem links de acesso manual com status explícito.
- Cada coleta grava manifesto JSON, tabela CSV, índice HTML com links por nível e catálogo SQLite com metadados de descoberta persistidos como não elegíveis. Os recursos já baixados por conectores existentes REDAPE/Sinaflor continuam disponíveis.
- A seleção requer a mesma fitofisionomia; tenta a microrregião e amplia para a região compatível somente se não existir candidato local. Prioriza parcelas primárias abertas de instituições reconhecidas, depois estatísticas institucionais publicadas; inventário ambiental só pode entrar como último nível quando o próprio anexo tiver aceite expresso comprovado.
- Estudos fitossociológicos primários compatíveis podem alimentar estrutura horizontal/vertical e uma lista qualitativa top 10 por dominância, com nomes vulgar/científico e fonte. Registros descobertos não são usados automaticamente: exigem licença, método, escala, unidade amostral, n, métricas e incerteza auditados. Sem erro disponível, “incerteza não mensurável”.
- Acesso às fontes e regras de elegibilidade foram implementados; a cobertura nacional ainda não está ingerida/harmonizada. Permanecem apenas 27 referências agregadas candidatas e um conjunto local do Tapajós com 30 resumos de parcelas. Não afirmar quantidade nacional de inventários únicos nem calibração SAR a partir de metadados.
- Não foram executados testes, CI ou build Windows nesta etapa; esta alteração requer validação automatizada e execução dos conectores antes de compor novo executável.
