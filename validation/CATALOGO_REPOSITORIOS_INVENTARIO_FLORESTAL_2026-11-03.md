# Catálogo de repositórios de inventários florestais para evidência Enform Verde
**Verificação:** 03/11/2026  
**Objetivo:** localizar inventários nacionais, estaduais e de instituições públicas/de pesquisa para usar dados microrregionais quando disponíveis e, na ausência deles, estimativas regionais SFB/IFN com transferência explícita por fitofisionomia e distância. Este é um inventário de fontes prioritárias verificadas, não uma declaração impossível de exaustividade de toda tese, fazenda ou projeto.

## Regra de seleção espacial e ecológica

A busca e a seleção são feitas **nesta ordem**:

1. Inventário de campo dentro da AOI, com desenho, data, geometria, fitofisionomia compatível e dados brutos/licença verificáveis.
2. Inventário da mesma microrregião ou unidade ecológica, mesma fitofisionomia IBGE legenda_1 e período/ecologia compatíveis.
3. Inventário regional estadual/bioma **do SFB/IFN** mais próximo que ainda tenha a mesma fitofisionomia ou equivalência ecológica documentada.
4. Modelo hierárquico de transferência entre classes/regiões somente se o erro dessa transferência puder ser estimado por validação em blocos/regiões retidas. Sem isso, publicar apenas um envelope experimental com limitações explícitas ou N/D.

A compatibilidade de fitofisionomia é requisito anterior à distância: um ponto mais próximo de classe incompatível não vence um ponto mais distante da mesma formação. Não usar médias do mesmo bioma como se fossem fitofisionomia. Não usar uma camada de cobertura/legenda como inventário de biomassa.

### Chave, distância e agregação
- Preservar identidade física por `UF + UA`; subparcelas, indivíduos, transectos, equações e ciclos repetidos são observações aninhadas, não novas UAs independentes.
- Preferir a geometria real da parcela/subparcela. Se só houver coordenada central do conglomerado, registrar precisão e tamanho/forma da UA; um centroid overlay sem precisão posicional conhecida é estrato regional, não validação pixel–parcela.
- Depois de filtrar por fitofisionomia, ordenar por distância geodésica AOI–UA e compatibilidade ambiental (clima, solo, altitude, estágio/sucessão, perturbação). Não fixar raio arbitrário; selecionar alcance por validação espacial.
- Para modelos experimentais, estimar erro de transferência com leave-one-microregion/UF-out e bootstrap por UA/cluster. Informar RMSE, MAE, viés e cobertura dos intervalos quando as observações possibilitarem. Se só houver média/DP agregados, não reconstruir microdados nem fingir que a dispersão é erro de transferência. Separar incertezas de amostragem, equação/parâmetro, sensor, classe, geolocalização e transferência.
- Resultados sem amostras elegíveis permanecem N/D. Uma fonte estadual do SFB pode preencher uma lacuna regional como estimativa experimental, mas não converte o resultado em validação independente.

## Repositórios e utilidade confirmada

| Repositório / instituição | Conteúdo e granularidade observados | Uso elegível no Enform | Situação/licença a verificar |
|---|---|---|---|
| **SFB / IFN / SNIF — Mapa interativo e Dados Abertos** | Dados botânicos, biofísicos e socioambientais; filtro nacional/bioma/UF/lote. O SFB informou 11.826 UAs e >937 mil árvores, cobrindo 68% do território no mapa divulgado em 2025; cobertura não é completa. | Fonte-padrão nacional. Priorizar DAP/altura/espécie e UA; juntar necromassa/serrapilheira/uso de terra por UF+UA; geolocalizar com cadastro oficial de unidades; estratificar por legenda_1 e selecionar unidades mais próximas compatíveis. | Licença e metadados variam por recurso/versão; verificar cada CSV/XLSX e retificação. Relatórios agregados não substituem dados brutos. |
| **SFB — Painel de Biomassa e Carbono** | Estimativas de AGB, árvores mortas e necromassa derivadas do IFN; filtros por bioma, vegetação, UF e antropismo; 222 equações listadas no painel. Granularidade divulgada como estadual. | Benchmark/regionalização e fonte de saída experimental com equações rastreadas. Pode informar estimadores por estado/bioma quando não houver microdados utilizáveis. | Não validar o próprio modelo com suas estimativas; dados do painel derivam do IFN e não são referência independente SAR. Restringir ao domínio/tipologia que os metadados efetivamente suportam. |
| **FlorestaSC / FURB / SINFLOR** | Inventário contínuo compatível com IFN; até 1.153 UAs, grade 10×10 km e adensamento 5×5 km em Floresta Estacional Decidual. Relatórios públicos incluem estoques médios por tipologia com IC95%; SINFLOR permite filtros por fitofisionomia, estágio, bacia, microrregião, município e UC e CSV de relatórios. Distingue árvores, necromassa e usos fora da floresta. | **Fonte microrregional prioritária para AOIs em Santa Catarina**, especialmente Mata Atlântica. Usar relatório por tipologia/microregião e, se autorizado, microdados para estimar distribuição por UA e teste de transferência. | A página informa que dados de usuários não cadastrados são limitados ao que é público; acesso ampliado exige registro. Licença/uso comercial e precisão dos pontos devem ser confirmados antes de embutir ou redistribuir. IC95 publicado da média regional não é IC95 da AOI nem inclui automaticamente transferência. |
| **PPBio / INPA / CENBAM / PELD** | Inventários RAPELD sistemáticos, dados geográficos e temporais, metadados de esforço; parcelas e grades em diversos sítios, sobretudo Amazônia. Há repositório de inventários e localização de 70 grades/módulos. | Fonte de alta prioridade para inventários microrregionais da Amazônia e alguns sítios de outros biomas, quando medem árvores/biomassa e protocolo pode ser harmonizado. Pode fornecer parcela–pixel somente se geometria, data e licença forem adequadas. | A política publicada prevê período de até dois anos antes de dados coletados se tornarem públicos sem autorização do coletor; conjuntos variam em acesso e protocolo. Confirmar status e licença por dataset; espécies/ocorrências sem DAP/altura não são biomassa. |
| **IEF/SISEMA Minas Gerais / Inventário Florestal de MG** | Relatórios de Cerrado, Floresta Estacional Decidual, Ombrófila e outras fisionomias; publicação específica de equações de volume, peso de matéria seca e carbono por fisionomia; camadas geográficas no IDE-SISEMA. | Prioridade regional para AOIs em MG; extrair modelos/coeficientes e relatórios de municípios/microrregiões; usar geodados para fitofisionomia/área, não como observação de biomassa. | Nesta verificação foi localizado catálogo de relatórios e mapas, mas não confirmada disponibilização aberta e licenciada de microdados georreferenciados de parcelas. Não tratar PDF agregado como raw points. |
| **Instituto de Pesquisas Ambientais / DataGEO-SP** | Inventários cartográficos de cobertura vegetal nativa (1990/91, 2000/01, 2010 e mapeamentos recentes), com recortes por região fitoecológica, bacia, município e UC. | Delimitar estratos/tipologias e área de cobertura; localizar classes que necessitam inventário próximo. | É mapeamento de cobertura, não inventário biofísico de parcela/biomassa. Não usar para estimar tC/ha ou validar SAR-carbono. |
| **SFB — relatórios IFN por estado e município** | Relatórios publicados para CE, DF, ES, MA, Caçador, PB, PR, RJ, RN, RO, RS, SC, SE e TI Mangueirinha; sínteses de campo e resultados estaduais/municipais. | Referência regional para localizar classes e estimativas quando o dado tabular estiver acessível; orientar o pedido de microdados e identificar lacunas de amostragem. | Relatórios não equivalem a tabela de parcelas. Para estatística nova, baixar dados primários do IFN e metadados correspondentes. |
| **Embrapa — Alice, Infoteca-e, Sabiia e unidades de pesquisa** | Repositórios de artigos, teses, relatórios e boletins: exemplos localizados incluem FLOTA Amapá (biomassa/raízes/carbono), inventários da Amazônia Oriental, Caatinga e protocolo Itaipu. | Busca sistemática de parcelas locais, equações por fisionomia, massa seca/teor C e apêndices/datasets suplementares; dados primários abertos têm alta prioridade. | São repositórios bibliográficos, não banco único de plots. Licença e dados suplementares devem ser verificados item a item; estimativas publicadas sem amostra/variância utilizável são envelope, não IC. |
| **Repositórios de universidades, periódicos e datasets (UFV/UFLA/UFPR/UnB/UFRA/UFMS, PELD, SciELO, GBIF/DataCite/ORNL DAAC)** | Inventários e experimentos de sítio, às vezes com dados suplementares, parcelas, espécies e equações; cobertura e forma de acesso heterogêneas. | Completar a etapa microrregional antes do fallback SFB; priorizar dados com identificador de parcela, coordenadas, datas, protocolo, medidas por árvore/UA, variância e licença. | Não assumir que tese/artigo tem microdados abertos. GBIF de ocorrência não é estoque; ORNL/Zenodo podem conter dados brasileiros primários, mas licença e pareamento precisam ser checados. |

## Fallback SFB: contrato de cálculo
Para cada AOI×fitofisionomia×compartimento:
1. pesquisar primeiro repositórios científicos e inventários microrregionais;
2. consultar IFN/SFB e selecionar UAs com classe/fitofisionomia compatível e domínio ecológico comparável;
3. usar a menor distância entre candidatos elegíveis, mantendo representatividade de UA/cluster e datas;
4. calcular predição com pesos/modelo espacial ou hierárquico; validar transferência retendo áreas inteiras, não árvores ou subparcelas aleatórias;
5. propagar variância amostral do IFN + incerteza da equação/teor de carbono + transferência + geolocalização/classificação; reportar cada componente e a incerteza total compatível;
6. se existirem apenas valores estaduais agregados, usar como fallback experimental estadual com dispersão/envelope publicado, nunca como estimativa microrregional medida;
7. se a classe não corresponder ou faltar erro de transferência defensável, não gerar tC/ha confirmado: emitir cenário experimental com aviso de domínio ou N/D.

A ponderação de distância não deve superar incompatibilidade ecológica. Proposta para avaliar, não coeficiente pré-fixado:
[
w_i propto q_i;K(d_{geo,i});K(d_{env,i}),
]
em que (q_i) representa qualidade/desenho/licença, (d_{geo}) a distância física e (d_{env}) uma distância ambiental calculada com variáveis comparáveis. Calibrar alcances e pesos em validação leave-one-site/region-out. Se o ajuste não for identificável, usar estrato exato/mais próximo como cenário e não fingir estimador validado.

## Ações vinculantes para montar a evidência de homologação
- Para cada dataset identificado, baixar bytes originais, obter licença e SHA-256, guardar metadados/dicionário/versão e registrar se a localização é parcela, UA ou centroid.
- Montar catálogo canonical com um registro por fonte e uma tabela de UAs por bioma×UF×fitofisionomia×ano.
- Conciliar SFB/IFN e dados locais por `UF+UA`; não contar repetição de equação, subunidade ou ciclo como UA independente.
- Fazer crosswalk IBGE legenda_1 somente onde geometria/resolução e correspondência ecológica estiverem documentadas. Manter classe desconhecida se ponto/centroide não demonstrar equivalência.
- Priorizar os experimentos microrregionais de AGB, necromassa caída e litter stock onde existirem dados por UA; raízes derivadas de AGB e alometria só se domínio/variância forem explícitos.
- Criar relatório auditável por variável, região e tipologia; preencher experimental somente se a incerteza (com unidade) e limitações estão documentadas. Caso contrário, N/D.
- O inventário IFN/SFB cobre grandes áreas mas não todo o território; não declarar “nacionalmente completo”. Consultar o mapa dinâmico do SFB em cada versão.

## Fontes oficiais consultadas
- SFB/SNIF IFN: https://snif.florestal.gov.br/pt-br/temas-florestais/ifn
- Mapa/dados abertos IFN (11.826 UAs, >937 mil árvores, 68% território na divulgação 2025): https://www.gov.br/florestal/pt-br/assuntos/noticias/2025/setembro/novo-mapa-interativo-facilita-acesso-aos-dados-do-inventario-florestal-nacional-ifn
- SFB Painel Biomassa e Carbono (CC BY indicado no portal): https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono
- FlorestaSC — dados, mapas e relatórios: https://www.iff.sc.gov.br/dados-e-mapas
- FlorestaSC — metodologia, rede e 1.153 UAs: https://www.floresta.sc.gov.br/nossas-a%C3%A7%C3%B5es/invent%C3%A1rio-florestal/metodologia/invent%C3%A1rio-florestal
- SINFLOR — filtros por fitofisionomia/microrregião e CSV: https://www.iff.sc.gov.br/nossas-a%C3%A7%C3%B5es/invent%C3%A1rio-florestal/produtos/mapas-e-plataformas/banco-de-dados-sinflor
- PPBio/INPA Componente Inventários: https://ppbio.inpa.gov.br/node/956
- PPBio/INPA disponibilidade e política: https://ppbio.inpa.gov.br/inventarios/disponibilidade
- IEF Minas — inventário florestal: https://www.ief.mg.gov.br/invent%C3%A1rio-florestal
- IPA-SP — inventário da cobertura vegetal: https://www.infraestruturameioambiente.sp.gov.br/ipa/inventario-da-cobertura-vegetal-nativa-do-estado-de-sao-paulo/
- SFB — relatórios IFN estaduais: https://www.gov.br/florestal/pt-br/centrais-de-conteudo/publicacoes/relatorios/relatorios-ifn
- Embrapa Infoteca-e FLOTA Amapá: https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1004540

## Situação
Este catálogo define seleção e fallback e identifica fontes adicionais relevantes à busca anterior. A extração/harmonização de microdados, checagem de licença e cálculo dos erros de transferência **ainda precisam ser executados** por AOI/fitofisionomia. Não declara gate aprovado nem cria estimativas.


## ADENDO — SIF/UFV E REVISTA ÁRVORE — 03/11/2026

A busca solicitada foi ampliada à Sociedade de Investigações Florestais (SIF), à Universidade Federal de Viçosa (UFV) e à Revista Árvore. A revista é publicada pela SIF, vinculada ao Departamento de Engenharia Florestal da UFV, é revisada por pares e cobre inventário, mensuração e modelagem florestal. É repositório bibliográfico científico, não uma base nacional padronizada de parcelas: cada artigo e suplemento deve ser triado individualmente para coordenadas, unidade amostral, fitofisionomia IBGE, data, variáveis, incerteza, dados reutilizáveis e licença.

### Estudos encontrados e uso adequado
- **Mata Atlântica, fragmento florestal (artigo de 2025/vol. 50):** dez parcelas de 0,1 ha em fragmento de 17 ha; comparação de Sentinel-1, Sentinel-2, fotogrametria e fusão para biomassa; RMSE de mapeamento relatado de 41% para fusão e 64% para DAP, enquanto o estimador de regressão baseado em S2 apresentou SE populacional de 21 Mg/ha. Evidência útil para método e benchmark de escala local, não parâmetro nacional nem erro transferível para qualquer AOI; verificar suplemento e disponibilidade dos dados antes de incorporar.
- **Floresta Estacional Semidecidual em MG:** estudo de parcelas permanentes medidas em 2002 e 2007, estágios médio e médio/avançado, com volume, biomassa, carbono e crescimento. Candidato para contexto local e desenho temporal; confirmar número/geometria das parcelas e dados por UA antes de qualquer validação independente.
- **Carbono em árvores do campus UFV:** estudo inventariou árvores urbanas DAP≥5 cm e cubou amostras (721 não palmeiras e 100% de palmeiras) para ajustar equações. É base metodológica/calibração de arborização urbana; não transferir equações automaticamente a floresta nativa.
- **Biomassa/carbono de povoamento de eucalipto:** comparação de métodos destrutivos e não destrutivos e equações Schumacher–Hall. Relevante apenas a povoamentos plantados com domínio compatível; excluir de estimativa de vegetação nativa.
- A coleção SciELO da Revista Árvore inclui artigos de Cerrado e outros biomas, mas resultados de busca por artigo não equivalem a catálogo exaustivo nem comprovam que microdados estejam disponíveis.

### Como incorporar à busca e ao gate
1. Pesquisar títulos/resumos da Revista Árvore e repositório institucional Locus/UFV por fitofisionomia e variável; registrar DOI, local, desenho, n de parcelas/árvores, domínio e métricas.
2. Dar prioridade a datasets/suplementos abertos com coordenadas ou unidades rastreáveis e observações primárias. Se o artigo só publicar média/coeficientes, usar como literatura/modelo de referência (experimental) e não fabricar registros por parcela.
3. Fazer deduplicação por estudo/dataset e separar treino, calibração e validação. Um artigo usado para desenvolver a equação não valida independentemente a equação ou o SAR contra os mesmos dados.
4. Confirmar licença de reutilização de dados e permissão de redistribuição por suplemento/dataset. Acesso gratuito ao texto da revista não significa licença aberta dos dados nem autorização para embutir microdados em produto.
5. Aplicar a hierarquia microrregional→SFB já definida somente após esta triagem: estudo da SIF/UFV conta como inventário microrregional se tiver cobertura, parcelas, tipologia e condições de reutilização adequadas; na falta delas, não substitui automaticamente o IFN nem o fallback regional SFB.

### URLs primárias consultadas
- Revista Árvore/SciELO: https://www.scielo.br/rarv
- Sobre a revista (SIF vinculada à UFV, escopo e revisão): https://revistaarvore.ufv.br/rarv/about
- Estudo de fragmento de Mata Atlântica com múltiplos sensores: https://www.revistaarvore.ufv.br/rarv/article/view/263981
- Estudo de parcelas permanentes em Floresta Estacional Semidecidual: https://locus.ufv.br/items/761ddecf-5936-4fe5-b8d0-15c4e86a7048
- Equações de carbono em árvores urbanas de Viçosa: https://www.scielo.br/j/rarv/a/zXWQRyhLynQXhRWLWnVBLKt/
- Comparação destrutiva/não destrutiva em eucalipto: https://revistaarvore.ufv.br/rarv/article/view/256163

**Limite da verificação:** esta etapa fez busca e triagem bibliográfica, mas não baixou suplementos nem integrou os dados desses artigos ao pipeline; também não atesta licença comercial. O gate científico permanece sem aprovação.