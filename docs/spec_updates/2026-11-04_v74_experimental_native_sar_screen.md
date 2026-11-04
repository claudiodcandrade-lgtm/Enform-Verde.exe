# ADENDO À ESPECIFICAÇÃO TÉCNICA — REVISÃO V74
**Enform Verde 3.26.0-SOLO-SAFRA — 04/11/2026 (UTC−3)**

Este adendo registra a camada experimental SAR para triagem de vegetação nativa, sua integração ao fluxo de análise e os limites de inferência. Deve ser lido com a especificação técnica completa v73.

## 1. Objetivo do módulo

Permitir que o usuário gere resultados experimentais reprodutíveis a partir de cenas Sentinel-1 VV/VH GeoTIFF para selecionar candidatos de vegetação com estrutura compatível com formação nativa e planejar aferição de campo. A ausência de validação de campo bloqueia homologação da acurácia, mas não bloqueia a execução como triagem experimental. O programa deve expor os limites em cada saída e não converter score em probabilidade.

## 2. Entrada e integração no aplicativo

A interface já permite selecionar GeoTIFFs SAR. O fluxo de identificação de uso passa os caminhos selecionados ao módulo native_sar_experimental.py. Para a triagem atual, são necessários pares VV e VH identificáveis no nome do produto como Sentinel-1/S1A/S1B/S1C. As grades são alinhadas por reamostragem bilinear de VH à grade VV, recortadas à AOI e limitadas a oito milhões de pixels por execução. CRS ausente, par incompleto ou menos de 49 pixels válidos produzem N/D com motivo.

A saída fica separada da classe/área de cobertura do classificador cartográfico: (i) índice de estrutura SAR experimental em GeoTIFF; (ii) polígonos candidatos em GeoJSON no limiar 0,65; (iii) resumo auditável com entradas, semântica das variáveis, área por limiar e atribuição IBGE por proximidade. A camada de candidatos não altera nem duplica os totais de uso do solo ou carbono.

## 3. Variáveis e cálculo do índice

Se o produto estiver em potência linear, os valores são convertidos para dB; se estiver em dB, são preservados. Para cada pixel válido:

- textura/rugosidade radiométrica: média da variabilidade local VV/VH em janelas 3×3 e 7×7;
- granulometria de imagem: resposta de abertura/fechamento morfológico a elementos 3×3, 5×5 e 7×7; este indicador descreve escala espacial de textura e não tamanho de partículas do solo;
- indício geométrico: anisotropia entre gradientes locais horizontais e verticais, como medida de alinhamento direcional;
- cada atributo é transformado em quantil relativo dentro da AOI.

O score é:
[
S = 0{,}40,Q_{textura}+0{,}35,Q_{morfologia}+0{,}25(1-Q_{anisotropia}),
]
onde cada Q representa a posição quantílica do atributo na AOI. S pertence a [0,1], mas é índice relativo de ordenação, sem interpretação probabilística ou comparabilidade nacional garantida.

## 4. Faixa experimental de área candidata

Para limiares 0,55, 0,65, 0,75 e 0,85, o programa converte a máscara score ≥ limiar em polígonos e calcula área em projeção equivalente. Publica área e número de manchas por limiar. A diferença entre áreas nos limiares 0,55 e 0,85 é uma análise de sensibilidade à escolha do corte, não incerteza estatística nem intervalo de confiança. O mapa 0,65 é uma lista preliminar de candidatos para campo.

## 5. Nomeação fitofisionômica IBGE

Para cada polígono candidato, a legenda IBGE legenda_1 mais próxima do centroide em projeção métrica é anexada somente quando a distância é ≤ 3 km. A distância e o método são registrados no GeoJSON. A classe IBGE nomeia uma referência cartográfica próxima; não comprova que o candidato pertence à classe ou que seja vegetação nativa. Sem IBGE disponível, os candidatos permanecem sem nome fitofisionômico.

## 6. Altura e bandas

A altura é um produto independente do score de textura:

1. ESA BIOMASS FP_FH__L2B banda P, quando o ativo cobrir a AOI e houver pixels válidos.
2. Se a rota P estiver indisponível, produto GEDI–TanDEM-X (X-band) com unidade, métrica, incerteza e cobertura verificáveis; produtos X locais/licenciados podem ser sumarizados se forem altura geofísica explícita.
3. L-band somente quando P e X não estiverem disponíveis; usar produto de altura explícito ou modelo experimental com domínio, coeficientes, dados de referência e incerteza rastreáveis.

Sentinel-1 é observação atual de estrutura/textura complementar, não altura em metros. Sem produto de altura direta ou modelo aplicável, não estimar metros a partir de backscatter bruto. A função de ajuste X/L disponível exige pares observacionais independentes; ela não deve ser apresentada como modelo de previsão de altura integrado enquanto não houver procedimento de treinamento/referência, chamada no fluxo, evidência de execução e incerteza de predição documentada.

## 7. Status, teste e homologação

A camada é operacional como triagem experimental quando há um par Sentinel-1 VV/VH e a execução grava as saídas. O status deve ser SAR_EXPERIMENTAL_CANDIDATE_SCREEN. N/D significa entrada insuficiente ou inválida. O resultado não é “vegetação nativa validada”. O pacote reporta zero métricas de acurácia em ausência de referência independente.

Os testes sintéticos verificam bounds do score, N/D com máscara sem pixels, alinhamento/recorte, geração dos artefatos e monotonicidade da área com limiar crescente. Eles comprovam o contrato de software e não a validade ecológica nem a precisão de classificação. A aferição posterior requer amostragem de campo independente, matriz de confusão por bioma/fitofisionomia, métricas e desenho amostral auditáveis.

## 8. Fontes e fundamentação

- ESA MAAP, produtos BIOMASS L2B, FP_FH__L2B (Forest Height) e FP_AGB_L2B (AGB): https://portal.maap.eo.esa.int/biomass/biomass-data-offer/
- ESA Biomass Product User Guide e ATBD, documentos oficiais: https://climate.esa.int/en/projects/biomass/
- Forest/non-forest separability using Sentinel-1 C-band: https://doi.org/10.3390/rs12111899
- Balling et al. (2023), Sentinel-1 GLCM texture for tropical forest disturbance mapping: https://doi.org/10.1016/j.jag.2023.103463
- Gonçalves et al. (2018), ORNL DAAC 1552, parcelas/estrutura no Tapajós: https://doi.org/10.3334/ORNLDAAC/1552

As publicações embasam o uso de retroespalhamento, textura e estrutura SAR como preditores. Elas não validam automaticamente o índice local ou seus limiares.

## 9. Pendências ainda mensuráveis

A integração experimental permite gerar mapas candidatos para aferição, mas a acurácia ecológica permanece desconhecida até campo independente. Não estão homologadas: classificação nacional de vegetação nativa, transferibilidade entre biomas, calibração de acurácia a partir do score, nem estimativas em metros oriundas de backscatter X/L bruto. A nova versão Windows só pode ser anunciada após concluir CI e confirmar EXE/artefato do mesmo SHA.
