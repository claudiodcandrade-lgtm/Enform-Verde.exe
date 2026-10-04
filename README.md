# Enform Verde.exe

Aplicativo desktop Windows para biomassa e carbono florestal.

O GitHub Actions compila automaticamente o pacote operacional Windows. Após baixar o artefato **Enform-Verde-Windows-operacional**, extraia o ZIP e dê duplo clique em **Enform Verde.exe**.

A compilação executa um autoteste do código-fonte e outro do executável compilado antes de publicar o artefato.

## Estrutura de inventários e calibração SAR

A aba **Base Científica e Modelos** permite selecionar um CSV harmonizado e exportar médias de DAP e área basal por inventário/parcela. Área basal é calculada como `Σ π(DBH/2)² / área amostrada`; árvores mortas ficam fora da estrutura viva. O resumo marca explicitamente que estes inventários não têm pareamento SAR.

O módulo `sar_calibration.py` aceita somente dados em suporte de parcela com `site_id`, `agb_ref_mg_ha`, `basal_area_m2_ha`, `mean_dbh_cm`, `stems_ha` e `height_sar_m`. Compara por validação cruzada agrupada por sítio a estrutura sem SAR com estrutura acrescida da altura SAR. Exige pelo menos 30 pares completos e cinco sítios independentes como mínimo exploratório. O resultado nunca fica marcado como implantável: calibração final ainda exige sítios externos, auditoria do rótulo AGB e diagnóstico de resíduos/incerteza.

X, L e P não são intercambiáveis. Produtos FH P-band, altura InSAR/PolInSAR X-band, observáveis L-band e simples retroespalhamento são reportados separadamente; altura não é AGB. Os microdados disponíveis de Mexiana/Santo Ambrósio e Jalapão fornecem estrutura e modelos altura–DAP de campo, mas não são usados como pares de treino SAR enquanto as geometrias e datas compatíveis faltarem.

## Estratos de alta biomassa

A rota prioritária para florestas densas é o produto geofísico ESA BIOMASS P-band `FP_AGB_L2B`, quando houver cobertura da AOI. O programa registra a origem, banda, produto, média zonal de AGB, número de pixels e separadamente a incerteza de pixel (`AGB_Std_Dev`) e a dispersão espacial; a incerteza do produto não é erro de validação local. O produto `FP_FH__L2B` é altura florestal e não substitui AGB. Se não houver produto AGB elegível, L-band dual-pol saturado e modelos de Cerrado aberto não são extrapolados para floresta densa.

A aceitação adiciona a AOI de consulta do sítio AfriSAR Lopé (Gabão), com mapa AGB a 50 m derivado de parcelas de campo e LiDAR (ORNL DAAC DOI 10.3334/ORNLDAAC/1681). O workflow consulta a cobertura de `FP_AGB_L2B`; a ausência de tile é reportada como indisponibilidade, não como falha do modelo. O mapa AfriSAR é benchmark derivado: seus pixels não são parcelas independentes e não validam por si só AGB P-band.

O candidato CASINO P-band (Soja et al. 2021, DOI 10.1016/j.rse.2020.112153) está registrado como modelo calibrável, não como equação pronta: requer canopy backscatter ground-cancelled e alvos locais de AGB com validação espacial independente. Referências de PALSAR full-pol continuam limitadas aos respectivos preditores, sensor e domínio publicados. Sem esses insumos, a saída permanece bloqueada para estimativa local calibrada.

## Mapa-base IBGE offline

O fundo padrão do mapa é gerado localmente a partir da malha municipal IBGE 2025 e da Base Cartográfica Contínua do Brasil 1:250.000 (BC250): limites de estados e municípios, rodovias, ferrovias, hidrografia, hidrovias, aeroportos, portos e localidades. A interface rasteriza essas camadas para a visualização e sobrepõe o polígono estudado. O aplicativo empacota os dados em `offline_ibge_map.json.gz` e não depende de mosaico de satélite para mostrar a AOI. Imagem de satélite segue opcional.
# Política SAR para biomassa e altura

1. Quando coberto e liberado pelo catálogo, `ESA BIOMASS FP_AGB_L2B` fornece a estimativa AGB primária e sua camada de desvio-padrão do produto. Ela é reportada como incerteza do produto, separada da dispersão espacial e sem alegação de validação local.
2. `ESA BIOMASS FP_FH__L2B` é consultado separadamente e pode fornecer altura superior do dossel (H100). Essa camada não é convertida em AGB. O relatório mantém a altura SAR ao lado da AGB sempre que ambos estiverem disponíveis.
3. Fora da cobertura desses produtos, apenas modelos com sensor, polarização, domínio fitofisionômico e preditores compatíveis podem produzir AGB quantitativa. L-band dual-pol não é promovido a modelo de alta biomassa por si só. Referências e inventários não pareados servem como contexto/prior, não como calibração SAR.
4. Recalibração brasileira exige inventário de parcelas com localização/suporte espacial, período compatível e resposta AGB documentada, além de pixel SAR coincidente. A validação é agrupada por sítio. DAP/área basal medidos em campo são preditores estruturais preferenciais; alturas de campo são usadas apenas para auditoria independente, pois têm maior erro de mensuração.
5. A fitofisionomia permanece determinada pelo diagnóstico IBGE vigente nesta versão. Se nenhum produto/modelo AGB compatível processar, o resultado declara essa lacuna e separa claramente qualquer referência bibliográfica da estimativa SAR.

## AOI brasileira de aceitação SAR

`acceptance/Teste_SAR_Cerrado_DF.kml` é o polígono de aceitação no Cerrado do Distrito Federal (aprox. 475 ha; limites −15,960/−15,940° latitude e −47,950/−47,930° longitude). Na execução de aceitação anterior, pixels reais ALOS/PALSAR HV produziram AGB de 16,75 Mg/ha pelo modelo publicado Yu & Saatchi (2016); a dispersão espacial propagada foi ±11,24 Mg/ha. O resultado é uma prova de processamento SAR ponta a ponta para vegetação savânica de baixa biomassa, não validação local: usa equação global transferida, o limite operacional é AGB ≤100 Mg/ha e ±11,24 não é intervalo de confiança nem inclui o erro de transferência. O arquivo pode ser aberto em QGIS, Google Earth ou carregado na aplicação para repetir a aceitação. Para floresta densa/alta biomassa, use a rota P-band ESA BIOMASS quando o produto oficial cobrir a AOI; não transfira a equação de savana.
