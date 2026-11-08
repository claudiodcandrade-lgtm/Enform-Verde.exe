# Enform Verde 3.26.0-SOLO-SAFRA

Status: **build funcional / piloto experimental**. Não constitui homologação científica (gate independente continua fail-closed).

## Solo 0–100 cm por interseção exata com o mapa Embrapa/PronaSolos
- Os cinco horizontes brutos de 90 m (0–5, 5–15, 15–30, 30–60, 60–100 cm) são obtidos do WCS oficial da Embrapa GeoInfo **apenas na janela do polígono**, validados (GeoTIFF, EPSG:4326, pixel 1/1200°, ponto flutuante), guardados com SHA-256 e reutilizados em cache.
- Cada pixel pesa pela área exata da sua interseção com a fitofisionomia nativa (EPSG:6933). Cobertura parcial do mapa: estoque só na área mapeada, sem extrapolação.
- Relatórios TXT/Excel mostram método, área da interseção, área mapeada, % de cobertura, nº de pixels, data de obtenção e licença (CC BY-NC 3.0 BR — uso comercial exige autorização da Embrapa).
- Amostragem por pontos passou a contingência rotulada e cobre estratos finos/fragmentados.

## Agricultura (experimental)
- Hierarquia de identificadores: Brasil → savanas africanas (CIRAD primeiro) → internacional; só modelos com incerteza quantificável e matemática auditável. Sem pesos instalados, a saída permanece “cultura não identificada”.
- Vigor em três classes (baixo/adequado/alto), favorabilidade climática (déficit hídrico FAO-56 e calor) e previsão por microrregião (PAM/IBGE 2015–2024) com Monte Carlo e dependências. Ainda não ligado ao painel; disponível como módulo verificado no EXE.

## Correções
- IBGE × classes: áreas por classe passam a fechar com a AOI (densificação antes da reprojeção).
- Arquivo PAM corrompido no repositório substituído; binários protegidos em `.gitattributes`.
- CI passa a executar todos os módulos de teste e falha se algum coletar zero testes.

## Padrão visual
- Padrão visual das versões anteriores congelado e verificado automaticamente (testes e `--visual-check` no EXE compilado). Ver `docs/PADRAO_VISUAL_ENFORM_VERDE.md`.

## Previsão de safra calibrada em dados históricos
- Novo modelo principal: painel por microrregião `y = a_u + b_u·t + β·RY`, com RY do balanço hídrico FAO-56 e Ky de Doorenbos & Kassam (FAO-33), água disponível Embrapa/PronaSolos e clima NASA POWER; β calibrado em 2015–2024 (PAM/IBGE) nas 40 maiores microrregiões de soja e de milho.
- Validação fora da amostra (deixando um ano-safra inteiro de fora): soja Sul −24% de erro vs. só tendência (10/12 microrregiões melhoram); milho Centro-Norte −19% (25/32); soja Centro-Norte −7%; milho Sul −2%.
- O vigor (experimental) posiciona o resultado no terço correspondente dos erros históricos; sem vigor, o intervalo cobre todos os erros. A matriz vigor × clima não calibrada fica como contingência rotulada.

## Identificadores consolidados, vigor automático e previsão na aba de monitoramento
- As oito culturas listadas têm rota única e incerteza declarada: soja, cana, arroz irrigado, café e citros pelo mapa brasileiro anual MapBiomas C11 (acurácia global 88,78 %, ~85 mil pontos; mapa do ano anterior); milho, sorgo e feijão não são separados por nenhuma fonte disponível e recebem apenas probabilidade a priori pela área colhida da microrregião (PAM), nunca nome.
- Vigor automático pelo Sentinel-1 RTC mais recente (Planetary Computer), comparado a talhões da mesma classe MapBiomas num raio de 8 km na mesma cena.
- A aba “Monitoramento — áreas cultivadas” passa a mostrar identificação consolidada, vigor automático e previsão calibrada (soja e milho).
- Aviso: em 03/11/2026 o link oficial do GeoTIFF MapBiomas C11 retornou HTTP 403; sem esse mapa (ou cópia local em ~/.enform_verde/mapbiomas), culturas e vigor ficam N/D e a previsão segue sem vigor.


### Dados de referência no piloto 3.26.0
O pacote-fonte integra a série oficial PAM N9 2015–2024 corrigida e o limite simplificado IBGE para identificação microrregional, com SHA-256 e metadados de proveniência. São insumos para modelos experimentais; não substituem testes de acurácia nas propriedades reais.
