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
