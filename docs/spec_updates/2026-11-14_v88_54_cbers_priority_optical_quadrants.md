# V88.54 — CBERS-4A prioritário, Sentinel-2 alternativo


## V88.54 — fundo óptico CBERS‑4A prioritário e leitura COG em quadrantes (14/11/2026)

- Prioridade mantida: CBERS‑4A/WFI do INPE é a primeira rota de imagem óptica; Sentinel‑2 L2A (Earth Search e Planetary Computer) é a alternativa. ESA MAAP/BIOMASS continua rota de dados SAR/canopy quando o produto e a cobertura forem adequados; não substitui o fundo CBERS/Sentinel‑2.
- Leitura das bandas COG agora usa janelas de saída de até 512 × 512 px e limita candidatos remotos a três cenas por provedor. Reduz dimensões de prévia e timeouts/retries por cena; cenas só são aceitas depois da leitura RGB real e cobertura de ao menos 95% da AOI. O cache óptico é identificado pela origem e atualizado em paralelo ao pedido CBERS prioritário.
- Removida a geração, empacotamento e cópia do grande raster/cartografia IBGE offline no workflow Windows, além do fallback cartográfico como se fosse imagem orbital. Em falha de CBERS e Sentinel‑2, o perímetro permanece visível e o diagnóstico mostra a falha. NASA VIIRS e Esri permanecem contingências visuais inferiores, identificadas e sem uso nos cálculos.
- O helper trata bandas de origem inteira e pixels mascarados convertendo para float antes de preencher NaN; evita erro ao ler COGs com dtype inteiro. O workflow removeu o bloco de teste/cartografia obsoleto e verificará quadrantes limitados e a prioridade dos provedores.
- Versão candidata `3.26.35-PRECAMPO-EXPERIMENTAL`. `py_compile` passou localmente; não foi possível executar suíte local neste ambiente porque faltam `requests`, `rasterio` e `geopandas`. A execução CI Windows e o smoke de pixels CBERS→Sentinel‑2 no SHA final ainda são necessários. Ainda não foi comprovada imagem no KML integral de Fazenda Maria Eduarda até o dashboard.
- Remover o raster offline não garante que um provedor remoto esteja disponível em qualquer instante. A falha deve permanecer distinguida de ausência de cenas, com provedor, etapa, cena/data e erro rastreáveis; nenhuma visualização de contexto pode ser chamada de imagem CBERS/Sentinel‑2. Não homologado.
