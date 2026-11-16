# Catálogo nacional inicial de inventários florestais — v1

O arquivo `national_forest_inventory_catalog_v1.sqlite` é um catálogo pesquisável em SQLite. Ele separa rotas institucionais, metadados de descoberta, referências com estatísticas publicadas, dados de parcelas realmente carregados e indicadores de elegibilidade. Uma busca de catálogo não comprova que o arquivo exista, esteja aberto, contenha parcelas ou possa calibrar SAR.

## Conteúdo local contabilizado

| Nível | Registros | Interpretação |
|---|---:|---|
| Rotas de portais | 53 | REDAPE/Alice/Infoteca e Embrapa; SFB/IFN/SNIF; IBAMA/Sinaflor/licenciamento; PNLA/PAMGIA; sistemas estaduais; IEF-MG/IFFSC; PPBio, ForestPlots, ICMBio, universidades, periódicos e catálogos de dados. Inclui rotas, não inventários individuais. |
| Registros candidatos de fonte/portal | 27 | Referências para triagem; não são downloads nem observações harmonizadas. |
| Referências publicadas agregadas | 27 | Registros bibliográficos com estatísticas/metadados iniciais; requerem auditoria do texto integral e de cada variável antes de uso quantitativo. |
| Conjuntos públicos listados | 20 | Inclui SINAFLOR/PMFS/POA/UAS, IF100, licenças federais, bases estaduais e institucionais; cada conjunto tem status explícito, sem confundir metadado com dado já ingerido. |
| Capturas agregadas oficiais com hash | 3 | SINAFLOR/PMFS Amazônia Legal, SINAFLOR Volumes Explorados IF100 e licenças federais IBAMA; só métricas agregadas e hashes, sem dados pessoais ou linhas brutas. |
| Conjunto harmonizado de parcelas | 1 | ORNL DAAC 1552 / FLONA Tapajós: 30 linhas, uma por parcela, com métricas estruturais publicadas. Não há dados árvore a árvore nesse arquivo. |
| Outros arquivos tabulares locais | 2 | Candidatos/agregados IFN de biomassa e necromassa, sem harmonização como parcelas primárias. |

Esses níveis somam 80 registros internos e 53 rotas de fontes; **não** equivalem a 80 inventários prontos. Sete candidatos catalográficos têm campos que sugerem dados primários abertos; ainda requerem confirmação de arquivos, licença, georreferenciamento e compatibilidade.

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

### Gate para anexos ambientais

Inventário de processo ambiental só pode sustentar estimativas como último nível e quando o próprio documento, com URL e SHA-256, for identificado e citado como aceito por parecer/decisão oficial. Aceite do licenciamento, plano ou processo sem referência inequívoca ao inventário não basta. Exigir acesso autorizado, método, unidades, métrica e fitofisionomia/localização compatíveis. Sem erro amostral, declarar “incerteza não mensurável”. Autorizações e licenças não contam como inventários. A contagem de 9.284 autorizações PMFS+IF100 não é número de estudos independentes.
