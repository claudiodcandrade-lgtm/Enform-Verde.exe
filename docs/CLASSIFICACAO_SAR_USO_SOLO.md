# Classificação SAR de uso e cobertura — implementação candidata 3.24.40

## Requisito do usuário

Confiança mensurável é obrigatória e inegociável. Onde não for possível demonstrá-la, preservar IBGE / MapBiomas. Ordem implementada, conforme a última instrução: **SAR elegível primeiro; nas lacunas, IBGE para fitofisionomia e MapBiomas para cobertura/uso atual; sem evidência, não classificado**. IBGE e MapBiomas mantêm suas legendas; classes genéricas não se tornam subclasses IBGE.

## O que está implementado

`land_use_sar.py`: Random Forest novo, com calibração logística multiclasse em conjunto separado, validação espacial independente, discriminação por classe e recuo para grupo agropecuário quando apenas o grupo é elegível. É uma adaptação operacional da família metodológica publicada; não se trata dos pesos treinados dos artigos. Os demais métodos catalogados são referências candidatas, não adaptadores executáveis.

A interface continua permitindo carregar um contrato JSON manualmente, mas **a nova rota tenta automaticamente os identificadores SAR instalados** no início de `IDENTIFICAR USO DO SOLO` e da execução geral, sem exigir seleção manual. Instalação padrão: `~/.enform_verde/modelos_sar/ativo.json` e demais `*.json` da mesma pasta. Opcionalmente, usar `ENFORM_LAND_USE_SAR_CONFIG` para indicar um contrato ou `ENFORM_SAR_MODELS_DIR` para outro diretório. Contrato explicitamente selecionado pelo operador tem precedência. Apenas configurações com amostras reais, GeoTIFF de preditores SAR existente, domínio cobrindo a AOI e fontes científicas documentadas são tentadas; mesmo assim cada uma precisa passar **a execução real de `classify_config` e a validação independente por classe**. A mera descoberta do JSON não torna o modelo elegível. Não há pesos nacionais ou internacionais treinados pré-instalados comprovados. No ausência de modelo operacional, o software utiliza o MapBiomas como **fonte cartográfica de cobertura atual**, com IBGE exclusivamente para nomear fitofisionomias compatíveis; nunca apresenta esse resultado como SAR.

Os campos de auditoria `sar_model_config`, `sar_selection`, `validation`, `warnings` e `mapbiomas_source` distinguem automaticamente modelo executado, configuração recusada e fallback cartográfico. A execução geral também chama a classificação. Resultados: GeoTIFF de classes SAR elegíveis quando realmente produzido; GeoJSON da partição final dentro da AOI; JSON de validação e auditoria; relatório e abas Excel de classes e validação.

Cada célula é convertida em polígono e intersectada com o perímetro, incluindo frações das células de borda. As camadas são particionadas na ordem de prioridade; sobreposição contraditória dentro de uma fonte fica para o nível seguinte. Áreas usam EPSG:6933, projeção equivalente. Percentuais usam a AOI inteira, incluindo área não classificada, e fecham em 100%. São áreas cartográficas, não estimativas de área corrigidas pelo erro de classificação.

`native_carbon.py` aplica o novo requisito: carbono apenas em formações nativas confirmadas. Lavouras, perenes, pastagens plantadas, SAFs cultivados e silvicultura são apenas ocorrências, com área e percentual. Cada fitofisionomia nativa recebe chamadas independentes ao motor SAR, referências locais e PronaSolos sobre sua própria geometria. O total conhecido é soma de tC/ha × hectares da interseção por classe/compartimento; jamais média dominante × área total.

Nas lacunas do SAR, IBGE fornece a fitofisionomia e MapBiomas a máscara de cobertura/uso atual. `legenda_1` isolada descreve região fitoecológica e não comprova que toda a região ainda esteja coberta por vegetação nativa. Assim, o cruzamento IBGE × máscara nativa MapBiomas detalha as formações, enquanto áreas agropecuárias atuais ficam fora do carbono. As previsões SAR elegíveis prevalecem sobre ambas. Sem evidência de cobertura nativa atual, a área é indicada como não confirmada e não recebe estoque.

Não se calcula carbono em área sem classe confirmada. Valores ausentes não são zero; componentes/classes sem dado geram soma parcial com área quantificada e faltante explícitas. Erros de área, transferência e covariâncias não quantificados impedem um IC total; os erros individuais dos dados/produtos são preservados por classe. A equação genérica de raízes de floresta de terras altas não é aplicada automaticamente a campos, savanas, várzeas ou mangues. Uma nova aba Excel apresenta carbono por formação; o total da propriedade usa a soma das interseções nativas, incluindo solo somente nessas interseções.

## Confiança: critério operacional conservador

- Conjuntos separados `train`, `calibration`, `validation` e unidades de referência sem repetição.
- Distância mínima de 1 km entre treino/calibração/validação e entre pontos de validação. É uma triagem contra vazamento espacial, não prova de independência: o responsável precisa documentar o desenho amostral e autocorrelação residual.
- Calibração logística sobre log-probabilidades RF, sem usar validação para ajustar pesos ou limiares. A probabilidade da classe predita deve ser exibida como probabilidade estimada, não convertida em acurácia comprovada.
- **Não existe limiar mínimo universal de acurácia, precisão, recall, probabilidade ou tamanho amostral para excluir um modelo:** qualquer acurácia quantitativa efetivamente mensurada e publicada por instituição/periódico reconhecido pode ser considerada. Priorizar modelos de maior desempenho demonstrado **quando métricas, cultura, período e domínio são comparáveis**.
- Aceitar modelos com desempenho inferior a 90%, 50% ou qualquer percentual arbitrário, divulgando o valor publicado com fonte, domínio, amostra, matriz de confusão e incerteza (IC95% Wilson quando contagens independentes estiverem disponíveis). Desempenho de classe não deve ser confundido com acurácia global.
- Publicação de desempenho em outro país **não** comprova esse mesmo percentual para uma AOI brasileira. Na ausência de validação local, identificar como 'desempenho publicado no domínio de origem; transferibilidade não aferida'. Quando existir modelo executável e SAR real, podem ser exibidos sinais provisórios com essa ressalva; jamais chamar de validação local.
- Referências sem pesos/coeficientes executáveis permanecem bibliografia e fonte de método, nunca classificação de pixels. Não inventar intervalos quando o artigo não apresenta contagens/erros suficientes. O IC pressupõe unidades independentes e representativas. Repetir seleção de modelos no mesmo conjunto de validação invalida independência.
- Matriz de confusão, precisão, recall, F1, Brier multiclasse e tabela de confiabilidade/ECE são armazenados. Wilson é da precisão da classe aceita, não IC de probabilidade de cada pixel nem IC da área.
- Rejeitar extrapolação do intervalo dos atributos do treino e AOI fora do domínio geográfico documentado. O intervalo marginal não prova ausência de mudança de domínio; época, sensor, processamento e amostragem devem ser auditados.
- Se o cultivo específico não passa, testar o grupo pai com sua própria validação e probabilidades agregadas. Não basta trocar o nome de uma previsão incerta.
- Fallback cartográfico não herda confiança do SAR. Não inventar acurácia local do IBGE ou MapBiomas.

## Contrato JSON e dados de entrada

Selecionar `CONFIGURAR CLASSIFICAÇÃO SAR DE USO` e então `IDENTIFICAR USO DO SOLO`, ou usar a execução geral. O JSON deve ter:

```json
{
  "institution": "Instituição responsável pelas observações",
  "reference_url": "https://repositorio.institucional/dados-reais",
  "publication_url": "https://doi.org/DOI-do-metodo",
  "reference_kind": "independent_observations",
  "sensor": "Sentinel-1",
  "processing": "RTC gamma0 linear, órbita e parâmetros documentados",
  "period": "período real das imagens e referências",
  "features": [
    {"name": "VV_mediana_seca", "unit": "gamma0 linear", "source": "SAR"},
    {"name": "VH_mediana_seca", "unit": "gamma0 linear", "source": "SAR"}
  ],
  "classes": {
    "Soja": {"parent": "uso agropecuário"},
    "Pastagem": {"parent": "uso agropecuário"},
    "Formação florestal": {"parent": "vegetação natural"}
  },
  "domain": {"type": "Polygon", "coordinates": []},
  "samples": "referencias.geojson",
  "feature_raster": "atributos_sar.tif"
}
```

O exemplo é deliberadamente incompleto: substituir domínio e referências por dados comprovados; não é modelo nacional. Arquivos relativos ao JSON. GeoTIFF de atributos georreferenciado com nomes de bandas na ordem exata de `features`; tags `sensor`, `processing`, `period` iguais ao contrato. Amostras vetoriais de pontos com CRS e campos `label`, `split`, `unit_id`; uma observação por unidade independente. `split` aceita train/calibration/validation. Classes presentes nos três conjuntos. Grupos pais permitidos: uso agropecuário, silvicultura, vegetação natural, água, outro.

Sem pesos nacionais embutidos ou referências reais adequadas, o SAR não ganha prioridade. A aquisição/preparação automática de séries SAR de classificação e o treinamento de modelos científicos nas AOIs Santo Ambrósio e Tapajós **ainda não foram validados**. As rotas existentes de AGB não produzem automaticamente esse contrato de atributos.

Limites de memória são explícitos: até 4 milhões de células na janela de classes e 40 milhões de valores na janela de atributos; AOIs maiores precisam ser subdivididas. Contratos devem indicar órbita/incidência, sazonalidade, fonte dos rótulos e desenho da validação. URLs e metadados fornecidos por usuário não certificam autenticidade por si sós; exigir revisão de proveniência antes de uso de produção.

## Pesquisa institucional — fontes consultadas em 23/10/2026

| Trabalho | Instituições / algoritmo | Aplicação e limite |
|---|---|---|
| Viana (2012), *Análise de imagens do satélite ALOS PALSAR para discriminar fitofisionomias do bioma Cerrado*, https://repositorio.unb.br/handle/10482/12211 | UnB, orientação Edson Sano; ISOSEG, MAXVER-ICM, SVM; ALOS/PALSAR | Chapada dos Veadeiros; exatidão global 75–78%; não equivale a validação para todo Cerrado. |
| Camargo et al. (2019), *A Comparative Assessment of Machine-Learning Techniques for Land Use and Land Cover Classification of the Brazilian Tropical Savanna Using ALOS-2/PALSAR-2 Polarimetric Images*, https://doi.org/10.3390/rs11131600 | Autores ligados a Embrapa Cerrados / INPE / UnB; ML, segmentação e atributos polarimétricos | Uso/cobertura do Cerrado; full-pol não pode ser substituído por mosaico HH/HV sem novo ajuste. |
| Haddad et al. (2023), *Atributos temporais derivados da combinação de dados PlanetScope e Sentinel-1 para classificação de savanas brasileiras*, https://proceedings.science/sbsr-2023/trabalhos/atributos-temporais-derivados-da-combinacao-de-dados-planetscope-e-sentinel-1-pa?lang=pt-br | INPE, UFSM, UCLA; RF, métricas fenológicas e textura VV/VH | ESEC Águas Emendadas; acurácia global 0,71, F1 médio 0,79. Necessita óptico + SAR. |
| Vilarmau e Bussinguer (2023), *Avaliação da separabilidade de fitofisionomias do bioma Cerrado no Parna Brasília mediante técnicas de classificação de imagens SAR Sentinel-1*, https://proceedings.science/sbsr-2023/trabalhos/avaliacao-da-separabilidade-de-fitofisionomias-do-bioma-cerrado-no-parna-brasili?lang=pt-br | UnB; RF, K-means, SVM; SLC/C2 | Florestal, savânica e campestre; RF/K-means >71,3%, SVM máximo 52,39%; não usar K-means como rótulo sem validação. |
| Silva Filho et al. (2024), *Mapping the Brazilian savanna’s natural vegetation: A SAR-optical uncertainty-aware deep learning approach*, https://doi.org/10.1016/j.isprsjprs.2024.09.019 | ITA / University of Twente e colaboradores; DL hierárquico, MRLP, calibrated dual focal loss | Sentinel-1/2; acurácia global 70,37%; quantificação de incerteza. Código https://github.com/pauloffsf/CerradoVegetationMappingISPRS ; dados https://doi.org/10.17026/dans-xne-cdhn . Repositório inspecionado; fornece scripts de treino/teste, não pesos nacionais prontos conferidos. |
| *Mapping Secondary Vegetation ... Brazilian Amazon* (2022), https://doi.org/10.3390/f13091457 | Registro e PDF Embrapa: https://www.alice.cnptia.embrapa.br/handle/doc/1147359 | Comparação C/L no período chuvoso; referência para vegetação secundária. Exige extrair protocolo/atributos e validar antes de adaptação. |
| Toro et al. (2023), *SAR and Optical Data Applied to Early-Season Mapping of Integrated Crop–Livestock Systems Using Deep and Machine Learning Algorithms*, https://doi.org/10.3390/rs15041130 | Embrapa Agricultura Digital / Unicamp; RF, LSTM, Transformer | Dois sítios brasileiros; Sentinel-1/2; resultados locais elevados não são garantia nacional. RF é a família executável nesta implementação. |
| Silva et al. (2026), *Seasonal behavior and yield penalty classification in pasture areas based on SAR polarimetry and machine learning techniques*, https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/1189675/seasonal-behavior-and-yield-penalty-classification-in-pasture-areas-based-on-sar-polarimetry-and-machine-learning-techniques | Embrapa Agricultura Digital; polarimetria SAR/ML | Pastagens: penalidade produtiva/sazonalidade, não classificador nacional de uso. Registro encontrado; coeficientes/artefatos não incorporados. |
| Numbisi et al. (2019), *Delineation of Cocoa Agroforests Using Multiseason Sentinel-1 SAR Images...*, https://doi.org/10.3390/ijgi8040179 | Ghent University; GLCM + RF | Cacau agroflorestal em Camarões; transferência para SAF brasileiro exige novas referências. |
| Maskell et al. (2021), *Integration of Sentinel optical and radar data for mapping smallholder coffee production systems in Vietnam*, https://doi.org/10.1016/j.rse.2021.112709 | Registro institucional University of Twente; RF, texturas SAR + óptico | Café sombreado/consorciado, pleno sol e jovem; acurácia usuário café consorciado 56%, portanto não aceitar espécie/sistema por simples extrapolação. |
| Mestre-Quereda et al. (2020), *Time Series of Sentinel-1 Interferometric Coherence and Backscatter for Crop-Type Mapping*, https://doi.org/10.1109/JSTARS.2020.3008096 | Universidades/ESA e parceiros; intensidade + coerência | 17 culturas na Espanha; >86% global no estudo. Coerência exige pares SLC, não deriva de GRD isolado. |
| Mauya e Jonas (2026), *Integrating Sentinel-1 SAR and Sentinel-2 multispectral data for tree species classification and mapping in smallholder planted forests of Tanzania*, https://doi.org/10.1007/s44415-026-00085-w | Pesquisa universitária na Tanzânia; RF/SVM | Silvicultura; eucalipto e Pinus, comparação SAR/óptico; validar transferência ao Brasil. |

Não foi confirmado nesta pesquisa um único algoritmo SAR nacional operacional para todas as fitofisionomias de Amazônia, Cerrado, Caatinga, Mata Atlântica e Pantanal. Trabalhos só ópticos, estimadores de biomassa sem classificação e radares aéreos não foram apresentados como classificadores SAR orbitais validados. IBGE, IFN/SFB e INPA são prioridades institucionais de busca, mas citar a instituição não comprova a existência de um classificador executável publicado.

## Ampliação global solicitada para agropecuária e silvicultura

A busca/modelagem dessas classes não se limita a instituições brasileiras. Milho, soja, sorgo e outras anuais; pastagens plantadas; café e citros; e florestas plantadas podem usar métodos publicados globalmente. A restrição permanece científica: origem reconhecida, preditores disponíveis e compatíveis, calibração e validação no domínio de aplicação. Um algoritmo global é uma alternativa metodológica; não significa transferência automática dos pesos e do erro publicado.

| Classe | Referência adicional | Situação |
|---|---|---|
| Milho e soja | Kussul et al. (2017), *Deep Learning Classification of Land Cover and Crop Types Using Remote Sensing Data*, https://doi.org/10.1109/LGRS.2017.2681128 ; Landsat-8 + Sentinel-1A, Ucrânia | Referência global; redes profundas; não confundir com RF executável. |
| Milho, soja, sorgo | *Synergy of Sentinel-1 and Sentinel-2 Imagery for Early Seasonal Agricultural Crop Mapping* (2021), https://doi.org/10.3390/rs13234891 | Acurácia por cultura varia; presença do sorgo na legenda não comprova confiança suficiente para aceitá-lo. |
| Sorgo, soja, milho | *Research on Remote Sensing Crop Classification Based on Improved U-Net*, https://www.scielo.br/j/eagri/a/HbGMvqgQWcvnYRRPS8H3ffR/?lang=en | CBAM-U-Net, S1/S2, Jianshan/China; inspecionar definições de índices e independência antes de reproduzir; tabelas apresentam inconsistências de fórmulas. Não incorporado como modelo validado. |
| Citros | Boryan et al., IGARSS 2018, avaliação Sentinel-1A C-band para citros na Flórida, https://data.nass.usda.gov/Research_and_Science/Cropland/docs/Boryan_IGARSS2018_Citrus.pdf | USDA NASS, See5 com boosting, S1/Landsat; acurácia total citros ~67,5% SAR, 71,33% melhor óptico. Referência metodológica; não atende por si só a política de aceitação. |
| Citros | Chakhar et al. (2024), avaliação de classificadores com S1/S2 em Cap Bon, Tunísia, https://doi.org/10.5194/piahs-385-443-2024 | Melhor SVM ~91%; comparação de 22 classificadores; conferir desenho de validação por talhão. |
| Citros | *Identification of Gannan Citrus Planting Area Based on Sentinel-2 and Temporal Sentinel-1 SAR Features*, https://www.aeeisp.com/nyjxxb/en/article/id/147d50a6-cbbe-4ba4-b31d-61dbad635ea6 | RF, S1/S2, China. Candidato bibliográfico, não pesos prontos conferidos. |
| Pastagem plantada versus campo nativo | *Compact polarimetric response of native grassland and seeded forage across a gradient of Southern Alberta Prairie ecoregions* (2026), https://doi.org/10.1080/07038992.2026.2626107 | SAR compacto polarimétrico; forrageiras semeadas e pastagens. Não substituir compact-pol por GRD VV/VH. |
| Pastagens — produto técnico complementar, não artigo | AAFC *Prairie Grassland Land Cover*, https://open.canada.ca/data/en/dataset/17736d36-ffe3-40fc-ba73-383a90862123 | RF S1/S2, separação campo nativo/forrageiras perenes cultivadas; fonte oficial para comparação de legendas e dados. |

Se o cultivo específico não atingir confiança mensurável, publicar apenas o grupo agropecuário quando ele tiver validação própria elegível; caso contrário manter IBGE / MapBiomas. Não identificar pastagem como plantada apenas pela altura baixa, nem cafezal/citros como floresta pela cobertura arbórea.

Cada estimativa identifica nominalmente a fitofisionomia utilizada no modelo, fonte da classe, hectares e percentual da AOI. Quando só existe classe ampla de cobertura, o relatório declara que o subtipo fitofisionômico não foi determinado; não fabrica FOD Aluvial ou outra subclasse.

## Regra final: formação nativa e nomenclatura IBGE

Classificadores priorizam usos não naturais. Classes nativas elegíveis limitam-se a Floresta/Formação florestal, Savana/Formação savânica e Campo/Formação campestre. Rótulos detalhados e o grupo genérico vegetação natural não recebem prioridade. A classificação nativa exige contrato `native_structure` com `height_feature`, `uncertainty_feature`, `uncertainty_kind: interval_half_width` e `validation_reference`; ambos os atributos precisam de origem SAR e unidade m. Os limites do intervalo de altura devem permanecer no domínio observado e conservar a classe e probabilidade calibrada elegível. Esse teste de sensibilidade não substitui validação da altura nem constitui IC conjunto. Não há limiar universal de altura. Sem esses requisitos, conservar fallback cartográfico.

O IBGE fornece apenas o nome compatível com a formação reconhecida: primeiro interseção local, depois referência compatível próxima dentre as feições disponíveis. Não exibir distância. A formação SAR fica na taxonomia da saída. Sem nome compatível, manter formação ampla. A busca depende da extensão do conjunto IBGE fornecido/cache; não implica busca nacional nem identidade florística demonstrada. Não há pesos nacionais validados embutidos.

### Nome da cultura
Mostrar a cultura somente quando elegível pelos gates independentes de alta confiança. Configurar culturas com parent `área cultivada` para que o fallback agregado, validado separadamente, seja exibido exatamente como **Área cultivada**. O grupo genérico uso agropecuário não comprova cultivo: não convertê-lo em área cultivada nem misturar pastagem/silvicultura. Sem confiança nem para cultivo, manter fallback cartográfico ou lacuna. Cultivos provenientes apenas da legenda MapBiomas são apresentados como Área cultivada; a legenda original permanece na auditoria.

### Atualização prevalente: pastagem versus ciclo curto
A classe de apresentação agregada é **Áreas cultivadas**. Só apresentar Pastagem separadamente quando houver a mesma validação independente de alta confiança exigida para culturas específicas. Quando não for possível separar pastagem e cultura de ciclo curto, usar Áreas cultivadas, desde que o grupo tenha validação própria. Referências de treino devem agrupar essas classes no parent `área cultivada`; o rótulo final desse parent é Áreas cultivadas. O rótulo é operacional e pode incluir pastagem na ambiguidade, sem afirmar uma cultura específica. A cartografia isolada de pastagem/cultura não demonstra a confiança local dessa separação; ambas são generalizadas na apresentação, com fonte original preservada na auditoria. Silvicultura permanece distinta.
