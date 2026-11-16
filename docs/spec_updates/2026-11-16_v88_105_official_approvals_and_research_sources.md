# V88.105 — inventários de processos aprovados e ampliação da curadoria institucional (16/11/2026)

## Versão e decisão de aceitação

- Candidata `3.26.54-PRECAMPO-EXPERIMENTAL`, sem homologação científica ou executável liberado.
- Decisão do proprietário: inventário que fundamenta PMFS aprovado no SINAFLOR é considerado aceito pelo órgão, sem exigir decisão separada sobre o inventário. A mesma regra vale para inventário ligado a licenciamento ambiental aprovado.
- A evidência de aprovação precisa identificar o processo/plano e vir de fonte oficial. Para uso quantitativo, continua obrigatório obter o documento/anexo exato, vincular ao processo, registrar URL, SHA-256, método, unidades, fitofisionomia, período, desenho amostral e termos de uso. Processo, licença, plano ou contagem agregada não substituem o inventário nem são parcela independente. Bases administrativas não são promovidas a calibração SAR.
- A regra altera a interpretação do aceite, conforme decisão explícita do proprietário, e prevalece sobre redações anteriores que exigiam aceite separado do anexo para todo PMFS/licenciamento. Para outros estudos sem processo de aprovação associado, mantém-se a evidência de publicação/aceite e as prioridades institucionais.

## Prioridade e centralização de fontes

1. Parcelas e microdados publicados por instituições de pesquisa, com preferência a todas as unidades Embrapa e, em particular, Embrapa Florestas, Amazônia Oriental, Pantanal, Cerrados e Semiárido; INPA; UFV/SIF; UFPR; UFLA; IEF-MG; ESALQ/USP; UNESP; Museu Paraense Emílio Goeldi; Jardim Botânico do Rio de Janeiro; e estudos públicos de reservas operadas por empresas, como a Reserva Natural Vale.
2. Inventários oficialmente aprovados associados a PMFS/licenciamento, com o documento primário recuperado e vinculado à respectiva decisão.
3. Estatísticas e inventários institucionais publicados, no nível de suporte e erro realmente publicados.
4. Leads sem dado primário continuam identificados como pendentes/restritos; não contam como fontes prontas.

Meta de produto: organizar progressivamente um repositório centralizado de inventários florestais do Brasil, com deduplicação por campanha, parcela, árvore, remedição e DOI/processo. Registrar proveniência, licença, geografias e fitofisionomias, datas, limiares DAP/DNS, desenho, variável, unidade, incerteza e nível de acesso. O volume bruto de registros não prova maior acurácia; estimativas de carbono dependem de compatibilidade de domínio, cobertura amostral, dados espaciais, pareamento com SAR e validação independente.

## Fontes verificadas nesta triagem

- Embrapa Amazônia Oriental/UFOPA: publicação institucional reporta monitoramento de longo prazo, com mais de 125 mil árvores observadas e mais de 8 milhões de registros de variáveis; os arquivos/backups MFT não foram baixados. Candidato de alta prioridade; resolver acesso, estrutura, coordenadas, remedições e licença antes de harmonizar.
- IEF-MG/UFLA (Inventário Florestal de Minas Gerais, 2008): volumes publicados descrevem 4.456 parcelas em 169 fragmentos; 1.763 parcelas em formações do Cerrado e 2.122 em formações do Domínio Atlântico. São dois volumes da mesma campanha/base, sem microdados locais baixados nesta revisão.
- Mata ripária do Córrego Capãozinho/DF, publicação Embrapa/UnB de 1993: 1 ha, 568 árvores DAP≥5 cm, 73 espécies e valor publicado de madeira seca do fuste/copa 127,49 t/ha. Integrado como uma referência agregada pontual; não equivale a AGB ou carbono, não informa erro no resumo e não deve ser extrapolado para toda vegetação ripária.
- Embrapa Semiárido: artigo de 2014 registra 10 unidades de 8×40 m em duas áreas de Caatinga, DNS≥3 cm e altura; tabelas/dados precisam ser extraídos e DNS não pode ser misturado a DAP sem conversão metodológica apropriada.
- Embrapa Florestas/Expedição Silvicultura 2025: 446 parcelas e mais de 38 mil pontos de controle. Fonte de florestas plantadas, não de vegetação nativa; dados primários e acesso dos parceiros ainda não conferidos.
- INPA/PDBFF OpenDataBio: censos em parcelas de 1 ha, DAP≥10 cm, mas o dataset consultado informa acesso restrito; solicitar autorização, sem contabilizá-lo como aberto.
- UFRA: publicação de inventário contínuo em 30 parcelas permanentes de 20×50 m em Igarapé-Açu; arquivo tabular/licença por verificar.
- UFPR/PELO: publicação descreve estrutura e dinâmica em quatro parcelas permanentes de Floresta Ombrófila Mista; buscar dados anexos.
- ESALQ/USP, UFV/SIF, UNESP, Museu Goeldi, JBRJ e Reserva Natural Vale permanecem na fila de buscas por estudo e arquivo primário. Publicações institucionais/corporativas não implicam dados em formato de parcela nem acesso aberto.
- Embrapa Florestas/Pantanal/Cerrados/Semiárido foram explicitados como rotas por unidade. A Embrapa Amazônia Oriental já é lead prioritário. A varredura ainda não é exaustiva nem autoriza declarar que a maior base nacional já foi alcançada.

## Estado da base e números

- Microdados locais: 3 conjuntos de campanhas, sendo um institucional (ORNL DAAC 1552/Tapajós) e dois complementares do projeto (Mexiana/Santo Ambrósio e Jalapão). Mexiana não tem georreferenciamento por parcela; Jalapão não tem área de parcela confirmada.
- Referências publicadas agregadas no catálogo: 28 após a inclusão da referência ripária. Agregados não equivalem a microdados nem a 28 campanhas independentes.
- O catálogo institucional/regulatório continua separando download, metadado, publicação e arquivo primário. PMFS/licenciamentos agregados não aumentam a contagem de inventários até recuperar e deduplicar seus inventários correspondentes.
- Performance: a paralelização controlada iniciada na V88.104 e a instrumentação de durações permanecem; ganho total não demonstrado. Comparar mesma AOI, hash, fontes, parâmetros, cache e resultados.

## Verificação e liberação

- Testes de regressão cobrem o aceite implícito condicionado à prova de aprovação e ao documento/URL/hash do inventário, bem como bloqueio de processo não aprovado e de anexos não verificados.
- Executar suíte integral, coleta de testes, atualizar o DOCX técnico e passar CI Windows, `--module-check`, `--visual-check`, `--network-check`, canvas, smokes e autoteste do EXE no mesmo SHA.
- O gate visual local exige ambiente com display; sem isso, não registrar aprovação. Não declarar redução de tempo, cobertura nacional, maior base do Brasil ou homologação científica sem as respectivas evidências.
