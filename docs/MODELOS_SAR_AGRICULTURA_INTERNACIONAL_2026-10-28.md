# Referências SAR agrícolas internacionais, dissertações e teses — 28/10/2026

## Princípio decisório
Na ausência de modelo nacional comprovadamente treinado, **admitir algoritmos, classificadores, produtos e modelos internacionais de instituições reconhecidas**. A proveniência estrangeira **não** é motivo de exclusão. Aplicação à AOI brasileira depende de:
1. predictores com unidades, polarizações, janelas sazonais, resolução e pré-processamento compatíveis;
2. parâmetros ou pesos executáveis e licença de uso/distribuição verificados (artigo sem pesos é referência metodológica, não executável);
3. domínio ecológico e fitofisionômico/cultural avaliado (arroz inundado não é arroz sequeiro; café arábica não prova conilon; lavoura anual não prova plantio perene);
4. teste brasileiro independente espacial e temporal, calibração de probabilidades, IC95% inferior da precisão por classe (Wilson) >= 0,90, ao menos 50 unidades independentes, matriz de confusão e registro de abstenção;
5. nenhum diagnóstico fitossanitário causal por radar e nenhuma previsão de produtividade antes de validação preditiva fora da amostra e cobertura do intervalo;
6. se a identificação de cultura específica falhar, preferir classe 'áreas cultivadas' somente com evidência de área cultivada; nunca rotular terra desconhecida como cultivada.

## Prioridade operacional: ESA WorldCereal
- ESA / VITO / IIASA WorldCereal: [repositório executável](https://github.com/WorldCereal/worldcereal-classification), [documentação](https://worldcereal.github.io/worldcereal-documentation/), [projeto e mapas](https://esa-worldcereal.org/en/products/global-maps).
- Pipeline executável público, com modelo global de extensão de lavouras e infraestrutura para treinar/aplicar cabeças específicas de culturas com séries Sentinel-1, Sentinel-2 e Landsat (Presto / CatBoost).
- A classificação de lavouras é uma rota de **prioridade 1 de experimento**: obter dados SAR temporais reais e executar o modelo WorldCereal com API/openEO autorizada, antes de buscar treinar um classificador nacional do zero.
- O fato de existir código e modelo global **não** comprova precisão em uma AOI brasileira nem prontidão do EXE, e WorldCereal é multimodal, não P-band. Ao registrar fonte, escrever 'Sentinel-1 SAR / Sentinel-2 / Landsat' conforme os inputs efetivamente usados. Não atribuir ao radar precisão de um modelo fusão sem análise ablatória.
- Comparar com MapBiomas, IBGE (somente fitofisionomia potencial) e classificador local; usar abstenção se o padrão temporal não for compatível.

## Fontes peer-reviewed e teses identificadas (catálogo verificável)
| Referência | Instituição | Tipo | Cultura ou função | Sensor e abordagem | Limitação para uso direto no Brasil |
|---|---|---|---|---|---|
| Nelson et al. (2014), *Towards an Operational SAR-Based Rice Monitoring System in Asia* | IRRI e parceiros | Artigo | Arroz | SAR multitemporal, assinaturas fenológicas | Testes na Ásia, sem calibração para Brasil; [artigo](https://www.mdpi.com/2072-4292/6/11/10773) |
| Setiyono et al. (2017), *SAR-based paddy rice monitoring system* | IRRI | Artigo | Arroz e rendimento | SAR C/X + ORYZA | Arroz irrigado tropical e parâmetros locais; [DOI](https://doi.org/10.1088/1755-1315/54/1/012015) |
| *High resolution paddy rice maps in cloud-prone Bangladesh and Northeast India* (2019) | Nature Scientific Data | Artigo | Arroz | Sentinel-1 RF e validação independente | Requer teste no sistema de plantio local; [artigo](https://www.nature.com/articles/s41597-019-0036-3) |
| Orynbaikyzy (2023), *Crop type classification using Sentinel-1 and Sentinel-2 data* | DLR / Martin-Luther Universität Halle-Wittenberg | **Tese de doutorado** | Classes de cultura | Série SAR + óptico / RF | PDF registrado com acesso restrito no DLR; extrair equações/séries permitidas; [registro e DOI](https://elib.dlr.de/198848/) |
| Nikaein (2025), *From InSAR Time-Series to Crop Growth* | TU Delft | **Tese de doutorado** | Crescimento e vigor | InSAR temporal + modelos físicos/ML | Modelos de pesquisa, não previsão validada de rendimento brasileiro; [repositório](https://repository.tudelft.nl/record/uuid:d5c77c32-2f3e-455b-9187-06c76f9abc22) |
| Khan (2023), *A SAR-based generalized approach for sunflower mapping* | University of Maryland | **Dissertação acadêmica / tese** | Girassol e transferibilidade | Sentinel-1 banda C | Não constitui classificador para milho, soja, sorgo etc.; [registro](https://drum.lib.umd.edu/items/a0e58179-a2a0-418d-be90-ccac475b504f) |
| Arias Cuenca (2023), *Sentinel-1 time series applications over agricultural fields* | Universidad Pública de Navarra | **Tese de doutorado** | Monitoramento de cultivos | Séries SAR Sentinel-1 | Confirmar modelo exportável e cultura específica; [repositório](https://academica-e.unavarra.es/entities/publication/ec975a59-015b-456d-99da-cb71d82f58dd) |
| *Classification Model of Sugarcane Growth Phases from Sentinel-1 Multi-temporal Images* (2023) | IPB University, Indonésia | **Tese** | Cana, fases | Sentinel-1 RF | Acurácia publicada insuficiente para a regra de 90% do Enform Verde; [repositório](https://repository.ipb.ac.id/handle/123456789/123546?show=full) |
| Sooksomnuek et al. (2026), *Development of a Sugarcane Plantation Classification Model* | Hydro-Informatics Institute / Srinakharinwirot University, Tailândia | Artigo | Cana | Sentinel-1 VV/VH + Sentinel-2 red-edge, RF | Melhor desempenho foi por fusão, não é comprovadamente SAR isolado; [artigo](https://ph01.tci-thaijo.org/index.php/jsid/article/view/266216) |
| Barboza et al. (2026), *Mapping of coffee cultivation... Peru* | INIA Peru | Artigo institucional | Café tropical | Sentinel-1 + Sentinel-2 + topografia / RF | Diferenciar arábica, conilon e SAF; [repositório](https://repositorio.inia.gob.pe/items/4a63c959-5c88-4bc4-845d-8f32b1b3f28e) |
| Manoel (2026), *Classificação Multitemporal de Café Arábica em Ciclos Bienais* | USP | **Tese de doutorado** | Café arábica | Sentinel-1 + Sentinel-2 + Landsat, RF | Validar conilon e transferências geográficas; [tese](https://teses.usp.br/teses/disponiveis/8/8135/tde-08072026-125841/pt-br.html) |
| Chaves (2025), *Classificação de monoculturas de café via redes neurais* | UNICAMP | **Dissertação de mestrado** | Café | Fusão Sentinel; investigar uso SAR no texto integral | Pesos/abertura e domínio ainda não demonstrados; [dissertação](https://repositorio.unicamp.br/acervo/detalhe/1552081) |

### Bases ampliadas de busca
- Catálogos de teses: DLR elib, TU Delft, DRUM/UMD, universidades ibéricas, IPB Indonesia, USP, UNICAMP, BDTD/IBICT, UFV, UFLA, UFPR, UFRA, UFT, Embrapa, INPA.
- Buscar nas línguas português, espanhol, inglês, indonésio, francês e alemão; verificar autoria, universidade, data, full text, dados, algoritmo, coeficientes, licença, incerteza e domínios.
- Para milho/soja/sorgo/feijão/citros, não inventar pesos específicos: testar WorldCereal genérico/transferência e ampliar busca dirigida por cultura, com teste brasileiro independente.

## Implementação parcial no repositório
`agricultural_external_models.py`: catálogo declarativo das rotas, consulta por cultura e pré-verificação de transferência com sensores, hash de artefato e avaliação brasileira independente. O catálogo **não contém pesos de classificação nem executa SAR por si só**. `tests/test_agricultural_external_models.py`: regressões para prevenção de falsa homologação.

**Não homologado** até cenas reais, treinamento/inferência com pesos verdadeiros, validação independente por classe e integração Windows no mesmo SHA.
