# V88.115 — SEMA-MT: fonte primária de inventários de PMFS identificada

Consulta de 16/11/2026. Esta atualização do catálogo e da especificação não altera a versão executável 3.26.59-PRECAMPO-EXPERIMENTAL e não declara os microdados da SEMA-MT como ingeridos.

## Evidência e dimensão da fonte

A página oficial da Gestão Florestal da SEMA-MT funciona como entrada para Projetos e Ações, SIMLAM, termos de referência, Geoportal e outros serviços. A categoria pública “Projetos e Ações” estava sem arquivos cadastrados nesta consulta. O portal de transparência da SEMA oferece Portal de Metadados Geográficos e Geoportal; a página oficial do Geoportal declara visualização, consulta e download de dados geográficos, incluindo autorizações. Um relatório público do programa REM/FUNBIO descreve dados de inventário obtidos da Coordenação de Manejo Florestal/SEMA via SIMLAM.

O relatório documenta um lote delimitado de inventários de planos de manejo: 188 arquivos recebidos da SEMA, dos quais três estavam corrompidos e 185 foram analisados, cobrindo 34 municípios e totalizando 1.830.561 árvores inventariadas. Os arquivos citados incluíam feições geográficas em shapefile e tabelas processadas compatíveis com Excel; o relatório também diz que havia arquivos brutos baixados do SIMLAM. Esses 185 são um subconjunto escolhido para uma análise de espécies-alvo, não o total estadual, não uma amostra estatística de todo MT e não evidência de que todos os arquivos possam ser redistribuídos. O relatório afirma que o acesso aos dados de inventário era realizado pela SEMA, na coordenação de Manejo Florestal.

A notícia oficial da SEMA, publicada em 26/06/2026, informa 402 planos autorizados em execução, 5,2 milhões de hectares em áreas de manejo e recebimento digital de dados com 100% do inventário georreferenciado. A notícia comprova o fluxo e a escala administrativa, não disponibiliza as observações em si. Não converter 402 planos em 402 microdatasets recuperados.

## Catálogo e ingestão

- Foi criado o portal `SEMA_MT_GESTAO_FLORESTAL`, ligado à página de Gestão Florestal, SIMLAM e Geoportal.
- Foi catalogado `SEMA_MT_PMFS_INVENTORIES_REPORTED_185`: microdados primários documentados por fonte oficial, com acesso via SEMA ainda não resolvido. Contagem do catálogo: 185 inventários analisados no lote reportado; estado do produto: lead de alta prioridade, sem arquivos primários locais, hash, harmonização ou licença de redistribuição confirmada.
- Foi separado `SEMA_MT_GEOSERVER_AUTEX_PMFS`: camadas de polígonos de autorizações e áreas de manejo podem auxiliar a descoberta e vinculação espacial; não são dados de árvores nem substituem o inventário.
- O IFN DAP10 de MT continua sendo parte da campanha nacional já ingerida (705 UAs; 80.711 observações no snapshot). Não se somam essas UAs às campanhas de PMFS, nem o lote REM à captura do IFN.
- Nenhum documento público localizado nesta rodada contém os arquivos brutos mencionados. Portanto, não se acrescentam os 185 ao total local de datasets com microdados integrados. O relatório e a notícia são referências verificáveis de existência e escala, não microdados de entrada para biomassa.

## Próxima recuperação oficial

Solicitar à SEMA-MT, via SIC/LAI ou Coordenação de Manejo Florestal, listagem e acesso aos inventários PMFS/POA aprovados que possam ser reutilizados, priorizando um pacote público/anônimo de microdados e documentação: ID do processo/PMFS/UPA/POA/AUTEX, município/bioma/fisionomia, ciclo/data de mensuração, parcelas ou censo, DAP/CAP e altura se medidos, espécie e validação botânica, área amostrada, fatores de expansão, incerteza/erro, geometrias/CRS, situação e ato de aprovação, dicionário de dados, termos/licença e hash. Preferir recuperação em lote e por API/serviço oficial quando permitido; não contornar autenticação ou controles do SIMLAM.

Somente avançar um arquivo para `BAIXADO_HARMONIZADO_LOCAL` após obtenção autorizada, hash, varredura de PII, validação de esquema e deduplicação por plano, UPA, POA, ciclo, parcela e remedição. Preservar a distinção entre inventário 100% comercial para manejo e parcelas ecológicas: adequação a carbono dependerá do domínio de DAP, altura, espécie, definição de biomassa, desenho e cobertura da área.

## Fontes oficiais consultadas

- SEMA-MT, Gestão Florestal: https://www.sema.mt.gov.br/site/index.php/unidades-administrativas/gestao-florestal
- SEMA-MT, Portal de Metadados Geográficos: https://geonetwork.sema.mt.gov.br/geonetwork/srv/por/catalog.search
- SEMA-MT, Geoportal / SIMGEO: https://www.sema.mt.gov.br/transparencia/index.php/sistemas/simgeo
- SEMA-MT, notícia sobre 402 planos autorizados em execução (26/06/2026): https://www.sema.mt.gov.br/site/index.php/sema/noticias/7244-sema-monitora-mais-de-400-planos-de-manejo-em-execu%C3%A7%C3%A3o-no-estado-de-mato-grosso
- REM-MT/FUNBIO, termo de encerramento e relatório técnico do contrato 154/2023: https://rem.sema.mt.gov.br/wp-content/uploads/2024/06/REM-MT-Termo-de-Encerramento-ao-contrato-de-apoio-no-154_2023-FUNDACAO-DE-APOIO-AO-ENSINO-SUPERIOR-PUBLICO-ESTADUAL-%E2%80%93-FAESPE-assinado.pdf

## Estado da versão

Esta é uma atualização de pesquisa, catálogo e documentação. Não modifica o software nem comprova a disponibilidade pública dos microdados SEMA-MT, uma análise de carbono com esses dados, benchmark de processamento, validação científica nacional ou homologação Windows. A versão permanece 3.26.59-PRECAMPO-EXPERIMENTAL.
