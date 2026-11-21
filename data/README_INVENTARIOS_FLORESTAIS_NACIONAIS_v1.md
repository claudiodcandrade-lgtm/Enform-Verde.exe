# Catálogo nacional inicial de inventários florestais — v1

O arquivo `national_forest_inventory_catalog_v1.sqlite` é um catálogo pesquisável em SQLite. Ele separa rotas institucionais, metadados de descoberta, referências com estatísticas publicadas, dados de parcelas realmente carregados e indicadores de elegibilidade. Uma busca de catálogo não comprova que o arquivo exista, esteja aberto, contenha parcelas ou possa calibrar SAR.

## Conteúdo local contabilizado

| Nível | Registros | Interpretação |
|---|---:|---|
| Rotas de portais | 62 | REDAPE/Alice/Infoteca e Embrapa; SFB/IFN/SNIF; IBAMA/Sinaflor/licenciamento; PNLA/PAMGIA; sistemas estaduais; IEF-MG/IFFSC; PPBio, ForestPlots, ICMBio, universidades, periódicos e catálogos de dados. Inclui rotas, não inventários individuais. |
| Registros candidatos de fonte/portal | 44 | Referências para triagem; não são downloads nem observações harmonizadas. |
| Referências publicadas agregadas | 28 | Registros bibliográficos com estatísticas/metadados iniciais; requerem auditoria do texto integral e de cada variável antes de uso quantitativo. |
| Conjuntos públicos listados | 24 | Inclui SINAFLOR/PMFS/POA/UAS, IF100, licenças federais, bases estaduais e institucionais; cada conjunto tem status explícito, sem confundir metadado com dado já ingerido. |
| Capturas agregadas oficiais com hash | 3 | SINAFLOR/PMFS Amazônia Legal, SINAFLOR Volumes Explorados IF100 e licenças federais IBAMA; só métricas agregadas e hashes, sem dados pessoais ou linhas brutas. |
| Conjuntos primários locais com microdados | 3 | ORNL DAAC 1552 / Tapajós (dataset institucional publicado), Mexiana/Santo Ambrósio e Jalapão (dados complementares do projeto). A contagem de datasets não equivale a três bases institucionais nem cobertura nacional. |
| Outros arquivos tabulares locais | 2 | Candidatos/agregados IFN de biomassa e necromassa, sem harmonização como parcelas primárias. |

Os níveis do catálogo podem se sobrepor e **não** equivalem a inventários independentes prontos. Referências, artigos, datasets de pesquisa, arquivos por UF e parcelas/remedições precisam ser deduplicados antes de contar a base.

## Capturas e estimativa de volume de inventários

Captura reproduzível realizada em 15/11/2026 (detalhes, URLs, tamanhos, SHA-256 e regra de contagem em `national_inventory_source_metrics_v1.json`):

- SINAFLOR PMFS Amazônia Legal: 10.273 linhas, 1.508 IDs de registro e 6.619 IDs de autorização, em 9 UFs. São processos/autorizações associados a planos de manejo, não 6.619 inventários independentes comprovados. O CSV original contém dados pessoais; a base local retém apenas estatísticas agregadas.
- SINAFLOR Volumes Explorados IF100: 2.438.833 linhas entre 2017–2026, 2.665 IDs distintos de registro/autorização, 847 nomes científicos e 16 UFs observadas. 2.436.353 linhas incluem coordenadas de árvore. São registros de exploração seletiva, com viés de corte e sem DAP/área basal no schema publicado; não entram na dominância natural nem como parcelas aleatórias.
- Licenças federais IBAMA: 14.376 linhas em 2.532 processos, com registros ASV em 761 processos. Esses processos ajudam a localizar EIA/RIMA e anexos, mas não revelam por si quantos estudos de inventário foram publicados.

Assim, a estimativa defensável é: **pelo menos 27 referências de estudos/publicações candidatas na curadoria atual**, além de milhares de registros administrativos de manejo/licenciamento que podem levar a inventários. O número de inventários únicos acessíveis permanece **não mensurável nesta etapa** até extrair e deduplicar os documentos/estudos, confirmar anexos, geografia, método, licença e unidade amostral. Nunca somar processos e IDs como se fossem campanhas independentes.

## Hierarquia de uso

1. Dados primários abertos de parcelas, com coordenadas e licença, mesma fitofisionomia; selecionar primeiro a microrregião e ordenar por distância dentro da classe compatível.
2. Se não houver parcelas compatíveis, médias ou estatísticas já totalizadas em publicação de fonte idônea, preferindo a mesma microrregião/fitofisionomia e depois região/fitofisionomia. Preservar unidade, n, desenho, período, erro/desvio/IC e citação. Um agregado não é parcela e não vira calibração SAR por existir.
3. Metadados de PNLA, PAMGIA, Sinaflor ou repositórios acadêmicos são apenas localizadores. Processos de licenciamento, inventário obrigatório citado e camada de inspeção não devem ser confundidos com dados de árvores.

## Biodiversidade e estrutura fitossociológica

Os CSVs de árvores licenciados usam `scientific_name` e `common_name` explicitamente. O nome `species` legado é preservado como `name_as_published`; nunca é promovido silenciosamente a nome científico. O indicador é qualitativo e apresenta as “espécies de ocorrência mais provável”, top 10 por área basal média nas parcelas, com nome vulgar, científico, dominância relativa, frequência, fitofisionomia, escala geográfica e fontes. Primeiro agrega a mesma fitofisionomia na microrregião solicitada; se indisponível, amplia somente para a mesma fitofisionomia e bioma e marca `REGIONAL`. Não afirma presença na propriedade.

Para estruturar biomassa e altura, parcelas abertas podem fornecer área basal, DAP, distribuição diamétrica e alturas medidas, caso existam. A altura de árvore de inventário é referência regional e não equivale a altura de dossel SAR. Estatísticas publicadas podem ser usadas como referências no nível de estudo quando os microdados não existem, sem criar parcelas sintéticas.

**Estado real da composição taxonômica local:** o conjunto Tapajós incluído não contém lista de espécies. Assim, nenhuma composição top 10 está embarcada automaticamente nesta v1; sem CSV taxonômico licenciado e compatível, a resposta correta é N/D com motivo.

## Rotas de descoberta

- Execute `python -m national_inventory_database --summary` para criar/atualizar o catálogo local.
- `python -m national_inventory_database --discover-open-portals` tenta descoberta paginada no CKAN do SFB, REDAPE Embrapa e Sinaflor/IBAMA quando rede/dependências permitirem. Não baixa anexos e não faz scraping de áreas autenticadas.
- A opção `--discover-open-portals` agora usa `inventory_source_access.py`: consulta CKAN do SFB/IFN e IBAMA, Dataverse REDAPE, OAI-PMH de Alice/Infoteca e repositórios acadêmicos registrados, DSpace REST público onde disponível e API de datasets do Zenodo. As demais fontes do catálogo entram no índice HTML como links de consulta ou têm seu erro/limite de acesso registrado. Saída padrão: `Enform_Verde_Biblioteca_Inventarios/`; pode ser alterada com `--output-library "pasta"`.
- A coleta produz `manifest_fontes_hierarquizadas.json`, `fontes_hierarquizadas.csv`, `acesso_fontes_hierarquizadas.html` e uma cópia SQLite pesquisável com os leads. O HTML abre links por nível; o SQLite registra metadados como `model_eligible=0`. Use o índice para chegar aos registros e baixe dados somente sob termos/licença permitidos.
- A aba **Base Científica** executa essa descoberta e abre o índice de fontes. A hierarquia implementada exige a mesma fitofisionomia; tenta microrregião primeiro e amplia para região compatível apenas se não houver fonte local. Dentro do escopo, parcelas abertas institucionais vêm primeiro; estatísticas publicadas idôneas vêm em seguida; inventário de licenciamento/plano é último recurso e exige prova de aceite do próprio anexo. Distância desempata candidatos do mesmo nível.
- Os conectores OAI/Dataverse/CKAN/DSpace/Zenodo retornam **leads**, não microdados prontos. PDFs, suplementos, licenças, geometria e unidade amostral continuam sujeitos à auditoria. O acesso a PNLA, PAMGIA autenticado, ForestPlots e portais estaduais sem API pública confirmada fica no índice como rota manual; nenhuma autenticação é contornada.
- Dados fitossociológicos são elegíveis para estrutura horizontal/vertical, área basal, DAP/distribuição diamétrica e lista qualitativa de dez espécies de ocorrência mais provável quando contêm registros de parcelas, nome científico e vulgar (se informado), área da parcela, fitofisionomia, microrregião, esforço, condição viva/morta, método, licença e fonte. Registros de herbário/ocorrência, nomes vagos e exploração seletiva não são convertidos em dominância.
- A regra geográfica é determinística no ranqueador: se a AOI informar microrregião e houver candidato compatível nela, a seleção fica restrita a essa microrregião; se não houver, pode ampliar a região/bioma e marca `REGIONAL_FALLBACK`. A fitofisionomia continua estrita. Fontes de menor tier e metadados nunca são promovidos automaticamente a inventário ou calibração.
- O arquivo `national_inventory_portals_v1.csv` registra instituição, rota, tipo de acesso, método e limite conhecido.
- O arquivo `national_inventory_datasets_v1.csv` distingue os conjuntos federais/estaduais e de pesquisa. `national_inventory_source_metrics_v1.json` guarda a captura sanitizada, hashes e regras de interpretação.
- `python tools/harvest_inventory_source_metrics.py` atualiza as três contagens oficiais. O script mantém arquivos brutos apenas em diretório temporário, apaga-os ao encerrar e grava somente agregados/hashes.

Cada coleta futura deve adicionar data/estado da consulta, URL persistente, licença, hash do arquivo e manifesto de ingestão; não sobrescrever uma captura anterior sem trilha.

## Atualização V88.104 — microdados locais e prioridade institucional (16/11/2026)

A base local agora reúne três conjuntos primários com suporte calculável, que não devem ser confundidos entre si: 30 parcelas de estrutura do ORNL DAAC/Tapajós já empacotadas; 167 parcelas e 2.144 árvores da Fazenda Santo Ambrósio/Ilha Mexiana, recuperadas da microbase fornecida no histórico do projeto; e 10 parcelas/246 registros do Jalapão. A atualização registra estes dois últimos como dados locais do proprietário, sem os contabilizar como inventários publicados por instituição.

| Conjunto | Unidades | Métricas permitidas | Limites aplicados |
|---|---:|---|---|
| ORNL DAAC 1552 / Tapajós | 30 parcelas | DAP, área basal, altura de campo e AGB já presentes no resumo por parcela | Referência primária de pesquisa; calibração/transferência restrita ao domínio Tapajós registrado; não há pareamento SAR nacional |
| Mexiana / Santo Ambrósio | 167 parcelas; 2.144 árvores | DAP, altura, área basal e AGB alométrica calculáveis; a área de 250 m² por parcela vem do histórico do projeto | Sem coordenadas de parcela nem pares SAR. A amostra reúne FOD aluvial e de terras baixas sem classe por parcela; somente referência estrutural agregada para a várzea estuarina da foz do Amazonas, conforme indicação do proprietário. Excluir savanas e campos; não separar ou atribuir as classes por parcela. A biomassa de 418,66 Mg/ha é estimativa alométrica da planilha, não biomassa destrutiva |
| Jalapão | 10 parcelas; 246 registros arbóreos | Frequências observadas de DAP, altura e táxons na amostra | Área das parcelas e subtipo IBGE não confirmados; DAP/área basal/AGB por hectare ficam N/D; sem coordenadas e pares SAR |

O arquivo local `microdados_inventarios_harmonizados_v1.csv` mantém a proveniência e seu SHA-256. Os registros de Mexiana e Jalapão têm `open_data=0`, licença de redistribuição não declarada e `model_eligible=0`; sua inclusão serve à análise interna e à referência explicitamente rotulada. Nenhum dos dois pode ser promovido a treinamento ou validação SAR.

O catálogo de fontes foi ampliado para refletir a prioridade solicitada: dados primários publicados por instituições de pesquisa; inventários de planos ambientais oficialmente aprovados, incluindo PMFS aprovado no SINAFLOR, cujo aceite do inventário subjacente é reconhecido por decisão do proprietário; e anexos de outros processos ambientais com aceite comprovado. Para uso quantitativo, recuperar o inventário/anexo exato em repositório oficial e registrar plano/processo, prova de aprovação, URL, SHA-256, método, unidade e domínio. Autorizações, planos não aprovados, ASVs e contagens agregadas continuam sendo localizadores administrativos, não inventários independentes.

Foram incorporados ao catálogo, inicialmente sem baixa local, o IFN DAP 10, o estudo Dryad da Amazônia Oriental, o inventário ORNL 1563 do Acre e o catálogo NASA/ORNL do Projeto Paisagens Sustentáveis Brasil. O IFN DAP 10 passou a ter uma carga oficial registrada na atualização de 16/11/2026 abaixo; os outros três continuam como candidatos públicos e não entram em qualquer cálculo até ingestão com hash, licença, unidade amostral e compatibilidade verificados.

### Gate para anexos ambientais

Inventário ambiental só sustenta estimativas como último nível. Para PMFS aprovado e vinculado ao SINAFLOR, a aprovação do plano conta como evidência de aceite do inventário que o fundamentou, conforme decisão do proprietário registrada em V88.105. Ainda é necessário identificar e recuperar o inventário/anexo exato, vincular ao plano/processo e registrar URL oficial e SHA-256, método, unidade e domínio. Para licenciamentos ambientais efetivamente aprovados, a aprovação conta como evidência de aceite do inventário que os fundamentou, conforme decisão do proprietário em V88.105. Exigir prova oficial da aprovação e vínculo ao documento primário. Licenças/processos sem aprovação não qualificam. Exigir acesso autorizado, método, unidades, métrica e fitofisionomia/localização compatíveis. Sem erro amostral, declarar “incerteza não mensurável”. Autorizações e licenças não contam como inventários. A contagem de 9.284 autorizações PMFS+IF100 não é número de estudos independentes.


### V88.105 — PMFS/licenciamentos aprovados e triagem por unidade de pesquisa

O proprietário determinou que o inventário que fundamenta PMFS aprovado no SINAFLOR ou licenciamento ambiental aprovado é considerado aceito pelo órgão. Não exigir decisão separada sobre o inventário. Para cálculo, localizar o inventário/anexo exato em repositório oficial, vincular ao PMFS/licença aprovada e registrar prova oficial de aprovação, URL, SHA-256, método, unidade, fitofisionomia, área/período, desenho e termos. Processo aprovado não substitui o anexo nem se torna uma parcela; dados administrativos agregados continuam fora dos cálculos de estrutura.

A triagem prioritária inclui todas as unidades Embrapa, com foco adicional em Florestas, Amazônia Oriental, Pantanal, Cerrados e Semiárido; INPA, UFV/SIF, UFPR, UFLA/IEF-MG, ESALQ/USP, UNESP, Museu Goeldi, Jardim Botânico do Rio de Janeiro e fontes publicadas de grandes reservas como a Vale. O catálogo agora registra fontes específicas e seus estados de acesso. Não foi constatado acesso de microdados aos arquivos MFT da Embrapa Amazônia Oriental; a instituição reporta mais de 125 mil árvores e 8 milhões de observações. Inventário Mineiro IEF/UFLA 2008 é apresentado em dois volumes da mesma campanha (4.456 parcelas em 169 fragmentos; 1.763 parcelas Cerrado e 2.122 no Domínio Atlântico). O estudo Embrapa/UnB de mata ripária no DF foi adicionado como agregado de um único hectare: 568 árvores, 73 espécies e madeira seca de fuste/copa 127,49 t/ha, sem interpretação como AGB/AGC e sem erro amostral informado. Outros estudos identificados (Caatinga Embrapa Semiárido, UFRA, UFPR/PELO e INPA/PDBFF) aguardam extração do texto/dados e/ou autorização. Expedição Silvicultura (446 parcelas) permanece em estrato de florestas plantadas.

A base local continua com 3 conjuntos contendo microdados (Tapajós/ORNL institucional, Mexiana e Jalapão do projeto); apenas o primeiro é dataset institucional harmonizado. A contagem de 28 agregados publicados não significa 28 campanhas independentes. Pesquisa bibliográfica indica rotas para expansão, mas a alegação de maior base nacional aguarda ingestão, deduplicação e comparação sistemática.

## Consulta e atualização leve do catálogo (V88.106)

A base SQLite é consultada sob demanda com filtros por bioma, fitofisionomia, UF e microrregião; as conexões de consulta são somente leitura, os resultados limitados a 200 e os filtros usam parâmetros SQL. Índices compostos e cache LRU atendem buscas repetidas. A carga das sementes só é refeita quando seu fingerprint SHA-256 muda. Essa arquitetura acelera o acesso ao catálogo, mas não comprova redução do tempo de processamento SAR/carbono. Descobertas remotas seguem explícitas, e lead catalográfico não é dado de inventário quantitativo.

## V88.107 — unidades de conservação e novo agregado da FLONA Tapajós

A triagem passou a incluir explicitamente os planos de manejo e diagnósticos de UCs federais publicados pelo ICMBio, além das rotas já registradas para pesquisa e fontes ambientais. Cada inventário recuperado deve ser vinculado à UC, plano/versão e ato oficial de aprovação, e deduplicado contra artigos, anexos de licenciamento e outras versões do plano. Planos são localizadores; sua contagem não equivale à contagem de inventários.

Foi integrado ao catálogo um inventário publicado de 2012 na FLONA Tapajós (Andrade et al., 2015): 204 unidades amostrais em uma campanha, com resultados agregados por duas áreas para densidade, área basal, fitossociologia e distribuição diamétrica. Quatro métricas resumidas foram incluídas; elas não são quatro inventários. O artigo disponibiliza dados agregados, não microdados árvore-a-árvore. Preservar a discrepância textual de 110/112 unidades para a Área 2 e não associar a afirmação de erro global <10% às métricas de densidade/área basal sem erro específico. Link do registro primário: https://www.alice.cnptia.embrapa.br/alice/handle/doc/1025613?mode=full .

Contagens após a atualização: 63 portais/rotas, 110 registros de catálogo, 32 linhas de estatísticas agregadas (as quatro novas linhas representam uma campanha), e 3 conjuntos com microdados primários locais, dos quais 1 é institucional harmonizado. O censo PDBFF consultado no OpenDataBio segue restrito e não conta como dataset recuperado. A existência de grade ou shapefile das parcelas Ducke não substitui medições de árvores.

## V88.108 — busca de páginas oficiais de planos de UCs

O coletor hierárquico acessa a página oficial do ICMBio e armazena links internos de planos/documentos como `catalog_lead`, com limite de 500 e chave derivada da URL. Links externos são rejeitados; a descoberta não baixa o documento nem habilita uso quantitativo. O link do dataset central anunciado pelo ICMBio no Portal de Dados Abertos devolveu 404 em 16/11/2026, por isso a coleta usa a página oficial e registra a indisponibilidade. O número de rotas/registros estáticos não mudou: 63 portais, 110 registros, 32 linhas agregadas, e 3 conjuntos primários locais com microdados (um institucional harmonizado).

## Atualização da base IFN, SINAFLOR e IEF-MG — 16/11/2026

O IFN DAP ≥10 cm foi baixado e indexado a partir do conjunto público do Serviço Florestal Brasileiro, versão de setembro de 2025. São 27 planilhas estaduais do mesmo programa nacional, com **841.387 registros de árvores/fustes e 8.951 unidades amostrais em 27 UFs**. Todos os registros desta captura contêm DAP e altura total de campo. As coordenadas são do centro da unidade amostral; não representam a posição de cada árvore. Não multiplicar por UF como se fossem campanhas independentes, nem transformar DAP/altura em estimativa por hectare sem aplicar o desenho, fatores de expansão e metadados válidos do IFN. A licença informada no conjunto é Creative Commons Atribuição.

| Bioma registrado no IFN | Unidades amostrais | Registros de árvores/fustes |
|---|---:|---:|
| Amazônia | 2.249 | 319.586 |
| Caatinga | 2.048 | 101.328 |
| Cerrado | 3.076 | 239.430 |
| Mata Atlântica | 1.372 | 158.670 |
| Pampa | 198 | 21.842 |
| Pantanal | 8 | 531 |

Há observações nos seis biomas, mas a distribuição é muito desigual. As oito UAs do Pantanal não garantem representatividade para o bioma; contagens de UAs e indivíduos descrevem a captura, não a suficiência estatística para uma estimativa por fitofisionomia.

O banco `national_inventory_microdata_v1.sqlite` mantém observações, resumos por unidade, proveniência por arquivo/linha, hashes e índices para consultas somente leitura sob demanda. `inventory_microdata_library.py` expõe consultas limitadas a 200 observações e a tabelas regionais de equações. Nenhum resultado é promovido automaticamente a biomassa, carbono, calibração SAR ou validação; a adequação à fitofisionomia, à unidade amostral e ao desenho precisa ser demonstrada.

O CSV POA Outros Biomas do SINAFLOR foi capturado em 16/11/2026 e sanitizado, removendo CPF/CNPJ, identificadores de imóvel/CAR, nomes de detentores e responsáveis e ART. A captura contém 2.883 linhas agregadas por operação/produto/espécie, 1.096 números de autorização distintos e 509 vínculos a PMFS. Ela informa dados administrativos e alguns campos de método, localização, área, espécie, volume e equação; **não é microdado árvore-a-árvore nem parcela bruta**. As situações observadas (emitida, vencida ou suspensa) são preservadas como estado da captura e não provam, por si, aprovação do plano nem aceitação de um inventário específico. Os registros são pistas para localizar POAs e anexos primários.

A página do IEF-MG adicionada pelo proprietário é um índice oficial para nove publicações do Inventário Florestal de Minas Gerais, incluindo volumes de Cerrado, Floresta Estacional Decidual, Floresta Estacional Semidecidual/Ombrófila e equações de volume, matéria seca e carbono. O inventário estadual de 2008 é uma campanha/base, não vários inventários por volume: a publicação descreve 4.456 parcelas em 169 fragmentos, com 1.763 parcelas no Domínio Cerrado e 2.122 no Domínio Atlântico. O capítulo de equações recuperado foi transcrito em 18 registros regionais de matéria seca individual em modelo Schumacher–Hall. Não são medições de campo novas nem microdados de parcelas; o arquivo consultado não permite atribuir automaticamente biomassa aérea ou carbono. Aplicar apenas após confirmar compartimento, fisionomia, bacia/região, intervalo diamétrico e tratamento de retransformação logarítmica. A licença do capítulo não foi verificada.

Arquivos desta atualização: `official_inventory_microdata_ingestion_v1.json` (manifesto e contagens/hash), `national_inventory_microdata_v1.sqlite` (base consultável), `sinaflor_poa_outros_biomas_sanitized_v1.csv` (captura sem PII) e `ief_mg_2008_dry_matter_equations_v1.csv` (18 referências de equações). Para contagem de conjuntos/campanhas, o IFN é uma fonte/programa nacional; o SINAFLOR é um catálogo administrativo de operações; e os dois volumes IEF são partes de uma mesma campanha estadual. Não contar linhas, arquivos por UF, autorizações ou volumes bibliográficos como inventários independentes.

## SEMA-MT: inventários de planos de manejo documentados em relatório público (16/11/2026)

A página oficial da Gestão Florestal conduz ao SIMLAM, Geoportal e Portal de Metadados. O Geoportal informa que permite visualizar, consultar e baixar dados geográficos, incluindo autorizações; isso não equivale a microdados de árvores. Um relatório público REM-MT/FUNBIO registra que a Coordenação de Manejo Florestal da SEMA forneceu 188 arquivos de inventários de PMFS, três corrompidos e 185 analisados, em 34 municípios, totalizando 1.830.561 árvores. O lote examinado foi selecionado por espécies-alvo e não representa o total do estado. Os arquivos referidos incluíam shapefiles e tabelas processadas; o relatório informa que o acesso aos microdados ocorre por meio da SEMA/SIMLAM. A notícia SEMA de 26/06/2026 informa 402 planos autorizados em execução, mas não publica os respectivos inventários.

Status para o banco: lead primário de alta prioridade, ainda sem arquivos locais, hash, esquema auditado, prova de reutilização/licença, nem elegibilidade para modelos. Foram catalogados separadamente o lote PMFS reportado e a camada de polígonos AUTEX. Não somar os 185 como microinventários integrados nem misturar com as 705 UAs/80.711 observações IFN já presentes no recorte estadual de MT. Próximo passo é solicitação oficial em lote à SEMA via SIC/LAI ou Coordenação de Manejo, condicionada à autorização, com metadados, geometrias, medições, desenho, situação de aprovação e termos de uso.


## Complemento V88.116 — auditoria de dados abertos SEMA-MT (16/11/2026)

A consulta ao Portal de Dados Abertos de Mato Grosso identificou o conjunto “Exploração florestal”, com três relatórios PDF para 2013–2014, 2016–2017 e 2020–2021. São relatórios de monitoramento da exploração/aderência às autorizações; não foram identificadas tabelas de árvores, parcelas ou microdados de inventário nesses recursos. Portanto, eles são referências contextuais e não aumentam a contagem de inventários recuperados. A página informa que os arquivos não têm licença fornecida.

Também foi localizada a obra pública “Flora Arbórea de Mato Grosso — tipologias vegetais e suas espécies”. Ela serve como referência taxonômica e de ocorrência associada à tipologia vegetal, mas não fornece por si só abundância por parcela, DAP, altura, área basal ou biomassa. O Geoportal oferece camadas geográficas de autorizações, inclusive polígonos AUTEX/PMFS, úteis para localização e vinculação; não são medições de árvores.

Status final da verificação pública: nenhum microdado árvore-a-árvore adicional da SEMA-MT foi localizado em download público. O lote de 185 inventários primários segue como prioridade para pedido oficial, com obtenção autorizada, protocolo e variáveis verificadas. Contagens de inventários integrados permanecem inalteradas. Nenhum contato ou pedido externo foi enviado nesta etapa.

Fontes consultadas: Portal de Dados Abertos MT — Exploração florestal (https://dadosabertos.mt.gov.br/dataset/exploracao-florestal); SEMA-MT — base de referência (https://www.sema.mt.gov.br/transparencia/index.php/gestao-ambiental/base-de-referencia); SIMGEO/Geoportal (https://sema.mt.gov.br/transparencia/index.php/sistemas/simgeo); Biblioteca SEMA-MT (https://www.sema.mt.gov.br/site/index.php/bibliotecas/category/130-livros).

## V88.117: via SIMLAM Público e solicitação SEMA-MT preparada (16/11/2026)

O SIMLAM Público oferece busca por título/processo, município e documentos, mas a presença de inventários brutos entre os documentos não foi confirmada. O e-SIC da SEMA-MT aceita pedidos de acesso à informação e permite acompanhar a tramitação. Foi preparada a minuta `docs/solicitacao_LAI_SEMA_MT_inventarios_florestais.md`, solicitando o lote documentado de 185 inventários, um índice de inventários aprovados em PMFS/POA e referências a inventários anexados a licenciamentos, com metadados e salvaguardas de dados pessoais. A minuta está pronta para revisão e envio pelo solicitante; não foi protocolada. Sem novos microdados, os totais de inventários integrados permanecem inalterados.


## V88.118: rota e-SIC corrigida (16/11/2026)

O link profundo de pedido exposto na página e-SIC da SEMA retornou 404. A orientação atual da CGE aponta para https://ouvidoria.cge.mt.gov.br/falecidadao/, com autenticação pelo MT Login ou Gov.br, seleção do formulário “Informação”, órgão e período. A minuta local foi atualizada para este fluxo. Ela permanece não protocolada e nenhum dado novo foi obtido.
