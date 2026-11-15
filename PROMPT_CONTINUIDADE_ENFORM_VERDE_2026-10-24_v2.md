# PROMPT DE CONTINUIDADE — ENFORM VERDE
Atualizado em 24/10/2026

## Contexto e objetivo
Retomar o desenvolvimento real do Enform Verde no repositório claudiodcandrade-lgtm/Enform-Verde.exe, branch `feature/agricultural-identification-native-carbon`, PR #50. Preservar funcionalidades já operacionais e concluir rotas efetivas, com testes e incerteza cientificamente defensável. Não confundir catálogos de artigos, regras isoladas ou testes unitários com modelos orbitais treinados e integrados. Não anunciar EXE sem artefato Windows verificado.

## Requisitos permanentes
- Aplicativo Windows autônomo; importar SHP, GPKG, GeoJSON, KML e KMZ; mapa raster IBGE offline com municípios, estados, hidrografia e infraestrutura; zoom, scroll, polígono semitransparente, área em hectares; separadores brasileiros.
- Cobrir Amazônia, Cerrado, Mata Atlântica, Caatinga e Pantanal; classificar fitofisionomias por evidências confiáveis, usando IBGE `legenda_1` e MapBiomas quando apropriado, sempre com fonte.
- Prioridade absoluta para AGB derivada de SAR: ESA BIOMASS P, ALOS/PALSAR L, SAR X, Sentinel-1 C, e ESA CCI Biomass v7 como fallback documentado. Não apresentar estatística regional como estimativa SAR pixel a pixel. Altura RH98 de GTDX não entra diretamente em modelo H100 sem conversão validada.
- Estimar, quando houver suporte científico, AGB, raízes, necromassa, serrapilheira e carbono do solo; priorizar inventários microrregionais, IFN/SFB, SINAFLOR e Embrapa Solos. Informar limites quando faltar estimativa defensável. Preservar tC e tCO2e e não confundir OPEX, CAPEX ou outros parâmetros financeiros com carbono.
- Identificar lavoura (milho, soja, sorgo, café, cana, arroz, feijão e citros) somente com classificadores validados; caso contrário 'áreas cultivadas'. Preservar 'pastagem' quando segura. MapBiomas silvicultura classe 9 indica floresta plantada, não prova eucalipto ou pinus. Só distinguir gêneros com modelo e validação específicos.
- Mostrar cena e horários como 'horário de aquisição (UTC)' e 'horário de aquisição (UTC -3)', quando de fato disponíveis; verificar metadados antes de informar indisponibilidade.

## Identificação de sistemas integrados
Implementar ILP (lavoura-pecuária), ILF (lavoura-floresta), IPF (pecuária-floresta), ILPF (lavoura-pecuária-floresta). Coocorrência de componentes em uma fazenda não comprova integração de manejo. Distinguir usos adjacentes, rotação sem integração e sistemas verdadeiros. Quando a evidência for parcial, rotular como candidato ou não comprovado, sem falsa certeza.

## Referências científicas a verificar e reproduzir
1. Embrapa Solos/UERJ, U-Net com Sentinel-2 para iLPF: https://www.alice.cnptia.embrapa.br/handle/doc/1178498
2. Embrapa Territorial/UNICAMP, Random Forest para ILP no Maranhão: https://www.alice.cnptia.embrapa.br/handle/doc/1175472
3. Embrapa Agricultura Digital/UNICAMP, IA e imagens para ILP: https://jornal.unicamp.br/noticias/2024/03/20/metodo-alia-inteligencia-artificial-a-imagens-de-satelite-para-mapear-areas-com-integracao-lavoura-pecuaria/
4. Séries PlanetScope e deep learning, Remote Sensing of Environment: https://www.sciencedirect.com/science/article/pii/S0034425723004376
5. Embrapa Pecuária Sudeste, forragem com HLS e clima: https://www.sciencedirect.com/science/article/pii/S0168169925006027
Investigar ainda Embrapa Gado de Corte, Instrumentação, ESALQ, UFV e outras. Para cada método verificar código, pesos, dados, licença, definição das classes, validação espacial/temporal e domínio de transferência. Referência publicada não equivale a pesos operacionais.

## Cadeia de processamento requerida
Aquisição de Sentinel-1, Sentinel-2, Landsat/HLS e outras fontes adequadas -> máscaras e correções -> alinhamento espacial e séries temporais -> inferência com modelos treinados efetivamente disponíveis -> fusão de evidências espacial, espectral e temporal por unidade de manejo -> decisão ILP/ILF/IPF/ILPF ou abstenção -> relatório e mapas com rastreabilidade. Integrar ao desktop_app e pipeline principal. Testar AOIs reais nos cinco biomas; não gerar probabilidades sintéticas.

## Rigor de incerteza
Publicar matriz de confusão, precisão, revocação, F1, amostras independentes, região/ano, modelo e domínio. IC95% Wilson pode expressar precisão binomial quando suas premissas forem atendidas; não é intervalo de confiança de área nem probabilidade por pixel. Para área usar desenho amostral e estimadores adequados com correção de erro de classificação. Evitar pseudorreplicação e explicitar erro de transferência. Se não houver validação, indicar 'incerteza não quantificada', sem inventar RMSE, F1 ou IC.

## Estado real conhecido no GitHub
Repositório: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe
Branch: feature/agricultural-identification-native-carbon
PR: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/pull/50
- 92ea80d: `integrated_system_classifier.py` com decisão conservadora ILF/IPF/ILPF a partir de evidências.
- eee07cc: testes iniciais.
- 173b0d6: inclusão de testes no workflow Windows.
- c446054: intervalo de Wilson para precisão condicional.
- 4be3627: catálogo de referências, marcado não operacional sem pesos/validação.
- 96b6f40: testes de incerteza e bloqueio de modelos não validados.
- 8695cfa: `classify_integrated_batch`, decisão em lote com exportação JSON.
- cd64c6c: testes de lote e abstenção.
O dashboard havia passado em execução anterior, mas a situação dos workflows deve ser consultada novamente. Ainda não está demonstrada inferência orbital U-Net/Random Forest operacional nem integração completa com a interface. Não afirmar o contrário.

## Ordem de execução obrigatória
1. Inspecionar branch, PR, arquivos, workflows e artefatos; identificar regressões.
2. Obter código/pesos/dados e licenças dos modelos científicos; se não disponíveis, reproduzir treinamento com amostras reais, separação espacial e temporal e métricas independentes.
3. Implementar aquisição e pré-processamento de imagens e adaptadores de inferência.
4. Integrar resultados à decisão ILP/ILF/IPF/ILPF e ao mapa/relatório com abstenção.
5. Publicar incertezas compatíveis com o desenho de validação e área.
6. Testar Tapajós, Santo Ambrósio, Brasília e AOIs adicionais em Pantanal/Mata Atlântica/Caatinga, sem misturar fitofisionomias.
7. Rodar CI Windows, corrigir falhas, gerar EXE e disponibilizar link real de artefato verificado.
8. Atualizar este prompt a cada marco e preservar todo avanço anterior.

## Critério de conclusão
Somente concluir quando as rotas estiverem realmente ligadas à aplicação, com evidências rastreáveis, testes passando e artefato Windows verificável. Documentar claramente funcionalidades operacionais, experimentais e indisponíveis.
# ADENDO DE RETOMADA — estado em 24/10/2026

## Estado do repositório
- Repositório: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe
- Branch: `feature/agricultural-identification-native-carbon`
- PR #50: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/pull/50 — aberto como rascunho, não mesclar.
- HEAD observado: `98c655cd049e3cb372946d4e27b4e1b7e1733740`.
- Dashboard dual no HEAD atual: runs 146 e 147 passaram. Build Windows run 631 (ID `40125746120`) concluiu com sucesso no HEAD `98c655cd049e3cb372946d4e27b4e1b7e1733740`: testes funcionais/científicos, testes ao vivo, compilação, runtime empacotado e auto-teste em pasta limpa passaram. Artefato: `Enform-Verde-Windows-v3.24.41-CANDIDATE`, artifact ID `12573641862`, 522.544.606 bytes, SHA-256 `04c5b9967740c93df842edd6522ac84a685501266a858bd0d7ea3c5d475b147d`, expira em 23/11/2026. Runs 627/628 são falhas antigas anteriores à correção do teste; run 630 é de HEAD obsoleto.

## Alterações recentes
- Restaurado `tests/test_land_use_sar.py` de conteúdo ilegível que interrompia a suíte com `source code string cannot contain null bytes`; expectativa do MapBiomas corrigida para “Áreas cultivadas” quando a cultura não pode ser distinguida com segurança.
- SAR específico com validação independente precede MapBiomas; MapBiomas cobre lacunas. Teste de regressão usa sobreposição espacial e exige SAR para os pixels validados. O teste passa localmente após informar `config_path=SAR_TEST`; aguardar CI Windows atual.
- Painel agrícola agora separa “Painel executivo” de “Auditoria técnica” em abas próprias. O resumo mostra classes, áreas, fontes, estado da análise e bloqueios de previsão; a auditoria mantém metodologia, cobertura, validação, métricas, distribuição original e proveniência das fontes.
- Meteorologia executiva fica no painel; URL, período, dados completos, erros e rastreabilidade vão à auditoria. NASA POWER é prioridade para histórico recente em grade; CPTEC/INPE complementa previsões futuras. Não calcular média ponderada sem datas/variáveis comparáveis e pesos validados; produtos atuais têm funções/períodos distintos.
- `assess_crop_stress` só admite proveniência SAR com sensor e aquisição datada, descreve anomalias como inespecíficas e não diagnostica doença/praga.
- `evaluate_yield_forecast` bloqueia previsões sem fontes climáticas estruturadas e evidência validada SAR para identificação de cultura, vigor e sinal indicativo fitossanitário. Exige intervalo preditivo, método, pelo menos 50 previsões independentes em holdout espacial e temporal e cobertura compatível com o nível nominal pelo IC95% Wilson. RMSE/MAE/viés não substituem intervalo de previsão.
- A suíte de incerteza foi incluída no workflow Windows; o GUI contract testa a separação entre painel executivo e auditoria. O reset da análise limpa ambas as abas para evitar auditoria antiga. Nenhuma previsão está ligada à interface enquanto não existir modelo treinado, dados e validação exigidos.

## Evidência científica revisada — candidatos, não modelos operacionais do Enform Verde
- **Milho, SAR + óptico + balanço hídrico/agrometeorológico:** Ameline et al. (2018), SAFY-WB, Sentinel‑1 derivando GAI, Landsat‑8, dois ciclos no sudoeste da França. O resumo do CIRAD reporta R²>0,75 e rRMSE<12,75% em diagnóstico; cenário de previsão teve desempenho menor, erro relativo <13,95% e R²>0,69. É o candidato publicado mais direto de assimilação SAR em modelo de safra localizado nesta revisão, mas não identifica cultura via SAR, não incorpora sinal fitossanitário e não foi validado no Brasil. DOI: https://doi.org/10.1109/JSTARS.2018.2878502 ; registro CIRAD: https://publications.cirad.fr/une_notice.php?dk=590361
- **Arroz, SAR + óptico + meteorologia:** estudo Sentinel‑1/Sentinel‑2 e clima em campos/distritos da China reporta MLER R²=0,89 e RMSE=0,54 t/ha, além de safra independente de teste; não transfere automaticamente ao Brasil. https://www.sciencedirect.com/science/article/pii/S0168192323004197
- **Arroz, SAR + ORYZA:** sistema de modelo de crescimento validado em países do Sudeste Asiático; serve de referência para arquitetura, não como coeficiente brasileiro pronto. https://doi.org/10.1080/01431161.2018.1547457
- **Milho tropical, RHEAS/DSSAT + MODIS + clima:** validação leave-one-year-out em Quênia, Malawi e Zâmbia; não utiliza SAR e gera previsões em unidades administrativas. https://pmc.ncbi.nlm.nih.gov/articles/PMC11283090/
- **Soja no Paraná:** RF/SVR/regressão com sensoriamento remoto óptico e meteorologia, com validação temporal; referência municipal/regional, sem SAR e sem fitossanidade remota. https://isprs-archives.copernicus.org/articles/XLVIII-M-1-2023/197/2023/isprs-archives-XLVIII-M-1-2023-197-2023.pdf
- **Café:** modelo agrometeorológico-espectral INPE/Embrapa usa MODIS/LAI/NDVI e meteorologia no sul/sudeste de Minas Gerais, safra 2003/04–2007/08; baseline regional de arábica, sem SAR. https://doi.org/10.1590/S1678-3921.pab2010.v45.8623
- **Cana:** foram localizados estudos com Landsat, clima e variáveis agronômicas; verificar dados, cortes/soqueiras, código e validação antes de reproduzir. https://www.sciencedirect.com/science/article/abs/pii/S0168169921000818
- **Citros:** estudo australiano usa 14 anos e mais de 3.500 registros, LOYO e validação forward; reporta SVM RMSE=15,5 t/ha, MAE=12,1 t/ha, R²=0,88, MAPE=29%, com séries remotas de fenologia/produtividade; não é SAR e o erro/MAPE sinalizam limites práticos. Candidato de benchmark, sem transferência direta ao Brasil. https://www.sciencedirect.com/science/article/pii/S1569843223002583
- **Feijão seco:** modelo para 41 distritos no México combina clima e índices de vegetação com estatísticas oficiais; escala administrativa e sem SAR. https://www.sciencedirect.com/science/article/pii/S0303243421003305
- **Sorgo:** a busca encontrou trabalhos climáticos/EO e ferramentas baseadas em observações fenotípicas, mas não identificou solução pública que cumpra simultaneamente SAR, vigor, sinal remoto de estresse, clima dinâmico, produtividade e validação independente transferível às áreas-alvo.

Nenhum desses estudos satisfaz sozinho todos os requisitos atuais: identificação de cultura via SAR, indicadores SAR de vigor e anomalia de estresse sem diagnóstico indevido, integração com clima dinâmico, previsão por cultura/região, intervalo preditivo calibrado e validação independente aplicável ao Brasil. Não habilitar estimativas numéricas até completar essa cadeia para a cultura e domínio solicitados. Nenhum dado de produtividade de campo da AOI será exigido para a operação; referências independentes externas podem ser usadas apenas quando sua adequação e transferência forem demonstradas.

## Diretriz nova do usuário — autorização para desenvolver modelos
O usuário autorizou criar modelos matemáticos próprios quando os disponíveis não forem suficientes, desde que fundamentados na literatura global e apresentem incerteza quantificável. Dar continuidade ao desenvolvimento; a pendência não está resolvida apenas por um plano. Manter forecast fail-closed até obter treinamento real, validação espacial/temporal independente e cobertura adequada. Não pedir dados de campo da AOI como condição necessária: priorizar estatísticas oficiais, datasets abertos com rótulos e transferência validada; identificar explicitamente a escala de inferência (município/região ou talhão).

### Bases e evidências localizadas nesta revisão
- **ACYD (Agricultural Crop Yield Dataset):** Brazil admin-2/municípios, produtividade oficial até 2025 conforme cultura, clima semanal AgERA5, LAI e NDVI AVHRR/VIIRS, solo SoilGrids; pipeline MIT, dados subjacentes mantêm licenças originais. Cobre milho, soja, sorgo, cana, arroz e feijões, entre outras. É base potencial de treino e validação climática/remota municipal, mas não contém séries SAR e não lista café/citros na cobertura Brasil declarada. https://huggingface.co/datasets/notadib/ACYD
- **SIDRA/PAM IBGE, tabela 1612/5457:** rendimento, área e produção oficiais em nível municipal para lavouras temporárias e permanentes; mapear códigos e anos sem misturar variáveis/produtos. Fonte: https://sidra.ibge.gov.br/pesquisa/pam/tabelas/ e https://www.ibge.gov.br/en/statistics/economic/agriculture-forestry-and-fishing/16773-municipal-agricultural-production-temporary-and-permanent-crops.html
- **YieldSAT (CVPR 2026):** rótulos de monitor de colheita e Sentinel‑2, clima, solo e topografia, Brasil/Argentina/Uruguai/Alemanha, 2016–2024; Brasil inclui 118 talhões de milho e 293 de soja. Bom holdout/benchmark para testar fusão e transferência nesses dois cultivos; não contém Sentinel‑1 segundo a ficha consultada. https://yieldsat.github.io/ ; artigo: https://arxiv.org/abs/2604.00940
- **Soja Brasil:** modelo municipal publicado usa 2001–2020, clima, ENSO e sensoriamento remoto; desempenho nacional médio rRMSE ~16%, pior que 30% em partes do Sul, mostrando heterogeneidade; estudo recente com transferência entre EUA e Brasil melhorou R² 0,29→0,44, ainda com erro de transferência relevante. Usar como baseline/benchmark, não como pesos prontos. https://www.sciencedirect.com/science/article/pii/S016819232300360X ; https://www.sciencedirect.com/science/article/pii/S1569843225006284
- **Milho:** SAFY‑WB assimilou GAI de Sentinel‑1 e óptico mais balanço hídrico; validado em dois ciclos na França, não no Brasil. https://publications.cirad.fr/une_notice.php?dk=590361
- **Arroz:** estudos de Sentinel‑1/2 + meteorologia e ORYZA mostraram capacidade de previsão em China/Índia/SE Asiático, em domínios locais. Usar como estrutura candidata, com recalibração e teste brasileiro; não transferir métricas. https://www.sciencedirect.com/science/article/pii/S0168192323004197 ; https://doi.org/10.1080/01431161.2018.1547457
- **Sorgo:** GROW‑Africa contém registros de produtividade georreferenciados para cultivos tropicais, incluindo sorgo, arroz e milho; cobertura africana pode apoiar pré-treino/benchmark, nunca substituir validação brasileira. https://zenodo.org/records/16544448
- **Cana:** dataset recente aberto de talhões comerciais brasileiros em São Paulo combina produtividade medida, meteorologia e Sentinel‑2; avaliar licença CC BY‑NC antes de uso em software comercial e verificar se os arquivos e geometria estão acessíveis. https://pmc.ncbi.nlm.nih.gov/articles/PMC12925426/ ; pipeline de RF/USP-ESALQ para cana utiliza >20 mil observações e Sentinel‑2/clima: https://github.com/raulpoppiel/sugarcane-yield-prediction

### Implementação autorizada e critérios por cultura
1. Criar pipeline executável que harmonize IBGE/PAM, ACYD e datasets de talhão com Sentinel‑1 calibrado (VV/VH, razão VH/VV, coerência/retroespalhamento temporal e métricas de fenologia/vigor), NASA POWER histórico e previsão meteorológica operacional. Guardar licença, versão, fonte, unidade, CRS, safra, geometria e método para cada observação. Não usar rótulos de MapBiomas como validação independente.
2. Treinar modelos por cultura e regime de produção (soja, milho, sorgo, café, cana, arroz, feijão e citros). Comparar baseline histórico/climático, modelos de árvore/boosting e híbridos crop-model/SAR onde os parâmetros existirem. Seleção somente em validação interna; manter testes finais intactos. Não extrapolar um mesmo coeficiente para as oito culturas.
3. Validar com expansão temporal e holdout espacial por municípios/estados, além de validação prospectiva quando houver safras publicadas depois do treino. Fechar a lacuna de SAR retrospectivo com Sentinel‑1 por AOI/unidade amostral. Medir ganho incremental de SAR versus clima/óptico por ablação; se SAR não melhorar ou não for transferível, não alegar integração efetiva.
4. Intervalos por conformalização com calibração separada, considerando agrupamento espacial e safra; relatar cobertura em holdout final e IC95% adequado por cluster. Rejeitar extrapolação fora do suporte. Estimar produção apenas com área cultivada/classificação validada; separar erro de área e de produtividade.
5. Painel executivo deve mostrar cultura, escala, previsão t/ha e produção quando elegível, intervalo (ex.: 90%/95%), data de emissão, confiança/domínio e status. Painel de auditoria separado deve mostrar treinamento, fontes, versões, split espacial/temporal, n efetivo, métricas, cobertura/IC, variáveis SAR/clima, licenças e limitações.
6. Para cada cultura que não disponha de n independente suficiente, intervalo calibrado ou SAR retrospectivo validável, apresentar indisponibilidade motivada; isso indica pendência específica da cultura, não autorização para estimativa sem erro.

Status desta atualização: localizadas bases abertas promissoras para várias culturas, mas ainda não se treinou e validou no repositório um modelo com dados SAR + clima para as oito culturas. Implementar, não apenas documentar. A etapa de entrega permanece aberta até código, dados/pesos legais, validação e integração ao painel estarem prontos.

## Rota permitida para modelos globais com transferência quantificada
A ausência de dados de campo na AOI não impede, por si só, toda estimativa: modelos publicados e bases independentes globais podem embasar uma solução transferida se houver suporte de domínio e a incerteza da transferência for explicitamente medida. Não declarar validação local sem dados locais independentes.

- Implementar uma arquitetura por cultura e região que compare baselines agrometeorológicos (SAFY/SAFY-WB ou DSSAT/APSIM/ORYZA, conforme adequação), modelos estatísticos e aprendizado de máquina. Usar séries SAR para área cultivada, fenologia/vigor e anomalias, e clima observado/previsão como covariáveis; óptico pode complementar. Identificação SAR da cultura prevalece sobre MapBiomas; MapBiomas preenche lacunas sem substituir identificação SAR validada.
- Buscar rótulos de produtividade em estatísticas oficiais, experimentos publicados e repositórios abertos, preservando safra, cultivar, manejo, unidade, escala e licença. Harmonizar definições e excluir observações incompatíveis. NASA POWER é prioritária para histórico climatológico em grade; CPTEC/INPE complementa previsão futura. Não combinar produtos em média ponderada sem sobreposição comparável e avaliação independente de viés/erro.
- Fazer validação temporal prospectiva e espacial em blocos/regiões, com conjunto final intocado; não dividir pixels vizinhos aleatoriamente. Avaliar transferência leave-one-region/year/country-out e detectar extrapolação por cultura, clima e fenologia. Usar adaptação/reponderação apenas com amostra independente de suporte; senão ampliar intervalos ou abster-se.
- Calibrar intervalos preditivos por cultura e horizonte com conformalização em blocos espaço-temporais ou abordagem Bayesiana hierárquica. Reportar cobertura nominal/observada, IC95% da cobertura (Wilson ou método apropriado), largura do intervalo, n efetivo, RMSE, MAE, viés e desempenho por safra/região. Incluir incerteza de parâmetros, rótulos, clima futuro, transferência e erro observacional; pixels correlacionados não são amostras independentes.
- Liberar previsão transferida apenas se o holdout independente alcançar cobertura predefinida e utilidade agronômica, e a AOI estiver no domínio de suporte. Caso contrário, mostrar intervalo amplo com aviso de extrapolação ou “previsão indisponível”, sem valor pontual.

Esta rota permite avaliar candidatos globais e quantificar incerteza; não significa que os modelos já foram treinados, incorporados ou aprovados. Neste HEAD não há previsão operacional validada para as oito culturas.

## Incerteza obrigatória
Toda previsão futura precisa apresentar produtividade e intervalo preditivo (t/ha, nível nominal e método), cobertura empírica independente, tamanho amostral efetivo, IC95% Wilson da cobertura, RMSE, MAE e viés. Testar por safra e região, evitar pseudorreplicação de pixels e manter conjunto final fora da calibração. A incerteza deve incluir o domínio de transferência e a incerteza de clima futuro. Se o intervalo não estiver calibrado, omitir previsão numérica e abster-se.

## Próximas ações
1. Acompanhar workflows do HEAD `98c655cd049e3cb372946d4e27b4e1b7e1733740`; corrigir falhas e confirmar painel executivo, auditoria, testes SAR e teste de intervalo preditivo.
2. Artefato Windows v3.24.41-CANDIDATE está publicado e o auto-teste limpo passou. Disponibilizar o ZIP publicado; confirmar funcionamento final no ambiente do usuário quando aplicável. Não reutilizar artefato v3.24.40 como build desta revisão.
3. Confirmar a pesquisa do Tapajós: diagnóstico L-band anterior não encontrou GeoTIFF no prefixo público consultado (`BLOCKED_DATA_COVERAGE`); não relatar altura operacional até localizar e validar cobertura.
4. Manter previsão de safra bloqueada: não há no repositório pesos/modelos integrados e validados para as oito culturas. Buscar licença, código, dados de treino/calibração e teste independente, priorizando Embrapa, INPE, universidades brasileiras, CIRAD, CGIAR/CIAT e centros tropicais.
5. Após dados apropriados, fazer benchmark por cultura, adaptar em treino/calibração separados e medir transferência por região/safra. Executar teste prospectivo. Só então liberar previsão e atualizar este prompt para conclusão.
6. Preservar formato do produto: resultados simples e legíveis no painel executivo; fontes, métodos, dados brutos, métricas, validação, limitações e logs em auditoria separada.

## Adendo — produtividade microrregional oficial para treinamento (24/10/2026)
Fonte primária nacional confirmada: IBGE, Produção Agrícola Municipal (PAM), SIDRA tabela 5457, variável 112 (rendimento médio da produção, kg/ha), nível N9 (Microrregião Geográfica). A PAM publica área, produção e rendimento para municípios e microrregiões, com séries históricas anuais; o SIDRA indica série desde 1974. Consultar sempre a tabela para descobrir o último ano efetivamente divulgado e não fixar anos por suposição.

Endpoint reproduzível (exemplo, rendimento 2023, todas microrregiões e produtos): `https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112/p/2023/c782/all`. A classificação 782 identifica o produto. Códigos confirmados pela resposta oficial para 2023:

| Cultura solicitada | Produto SIDRA | Código 782 | Regra |
|---|---|---:|---|
| Arroz | Arroz (em casca) | 40102 | Manter o grão como publicado; kg/ha |
| Café | Café total | 40139 | Preferir desagregar arábica 40140 e canephora 40141 se o sistema/modelo souber identificar o tipo; não misturar tipos sem ponderar pela área/produção |
| Cana-de-açúcar | Cana-de-açúcar | 40106 | kg/ha; harmonizar ciclos e manejo como limitação |
| Feijão | Feijão (em grão) | 40112 | Distinguir 1ª, 2ª, 3ª safras somente se o produto/registro permitir; não somar rendimentos simples |
| Milho | Milho (em grão) | 40122 | Para safras, usar categorias de primeira/segunda safra quando disponíveis e compatíveis com a máscara/ano |
| Soja | Soja (em grão) | 40124 | kg/ha |
| Sorgo | Sorgo (em grão) | 40125 | O rótulo IBGE é sorgo em grão; não transferir para sorgo forrageiro |
| Citros | Laranja (proxy específico) | 40151 | Não rotular o dado como citros genéricos. Requer cultura confirmada como laranja; limão, tangerina e demais citros ficam como modelos/series distintos |

Use a variável oficial de rendimento médio quando disponível e faça auditoria de consistência por `produção / área colhida`. Se reconstruir uma média da microrregião a partir de municípios, calcular `Σ produção / Σ área colhida` (equivalente à média ponderada por área colhida), nunca a média aritmética simples dos rendimentos municipais. Registrar municípios incluídos, área total, quantidade de registros válidos, proporção da área/produção coberta e observações suprimidas/faltantes (`..`, `...`, `-`, `X` não são zero). Separar classes/safras e unidades; para permanentes, tratar a idade do pomar e a bienalidade do café como fontes potenciais de heterogeneidade.

No treino, derivar por cultura e microrregião: rendimento defasado (lag), mediana/mediana ponderada móvel de 3–5 anos, tendência robusta temporal (Theil–Sen ou equivalente), dispersão interanual robusta (MAD/IQR) e cobertura da estatística. Usar a média microrregional como baseline/preditor histórico, não como previsão final isolada. Fazer backtest expanding-window por safra e deixar microrregiões inteiras fora do treino; testar o ganho incremental de SAR + clima contra (a) média microrregional histórica e (b) modelo só clima. Intervalos devem incluir a variabilidade microrregional e erro de transferência; não transportar uma média nacional/estadual para o talhão.

A tabela 5457 é a fonte de referência para os oito produtos; tabela 1612 é alternativa histórica apenas para lavouras temporárias e deve ser usada quando a tabela/ano/cultura realmente se aplica. A tabela completa da PAM confirma os níveis Brasil, regiões, UFs, mesorregiões, microrregiões e municípios. Links institucionais: https://sidra.ibge.gov.br/pesquisa/pam/tabelas/ ; https://sidra.ibge.gov.br/tabela/5457 ; https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal-culturas-temporarias-e-permanentes.html .

Status: identificados a fonte oficial, nível microregional, variável, classificação de produto e protocolo de ponderação. Próximo passo obrigatório: baixar séries históricas por produto/MI, calcular e salvar tabela de baselines com metadados e depois incorporá-las à validação/treino SAR-clima. A busca de fonte não substitui o dataset efetivamente materializado e auditado.

## Atualização urgente — previsão de safra e estado verificado em 24/10/2026

### Resposta à pergunta operacional
As equações ainda **não estão operacionais na aplicação**. O branch contém um módulo de treinamento (crop_yield_modeling.py) com regressão Random Forest/HistGradientBoosting, seleção por validação espacial agrupada, calibração split-conformal de resíduos absolutos e gates de domínio/intervalo. Isso é um arcabouço de treino, não um modelo treinado nem integrado ao painel. Não há previsão de safra validada disponível para as oito culturas. Não apresentar valores numéricos até completar painel real, treino, teste independente e integração.

O HEAD verificado agora é 46652cceb2bdb6bbbf8993f6dddfebcb7d508821 (branch feature/agricultural-identification-native-carbon). Isso substitui qualquer HEAD mais antigo registrado acima. Há código de treinamento e um gate que exige identificação/vigor/estresse SAR validados, mas a função atual ainda não inclui preditores microrregionais, não baixa os rótulos PAM e compara SAR+clima contra clima-only, sem manter a base microrregional na ablação. Verificar/corrigir esses itens antes de declarar pronto.

### Série oficial e aquisição reproduzível
Foi confirmada resposta válida do endpoint oficial SIDRA para PAM tabela 5457, território N9 (microrregião), variável 112 (rendimento médio em kg/ha), classificação 782 (produto). Exemplo:
https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112/p/2023/c782/all

Códigos de produto já confirmados: arroz 40102; café total 40139 (arábica 40140; canephora 40141); cana 40106; feijão 40112; laranja 40151; milho 40122; soja 40124; sorgo 40125. Laranja é apenas proxy de laranja, não citros genéricos. Série consultada de 2015–2024 retornou 558 microrregiões por ano e produto; disponibilidade varia por cultura e valores suprimidos/faltantes não são zero. Materializar CSV/Parquet com código SIDRA, descrição, ano, MI, variável, unidade, valor original, área colhida, quantidade produzida, fonte, data de consulta e status de qualidade. Fazer reconciliação entre rendimento publicado e produção/área. Se agregar municípios: rendimento = soma(produção)/soma(área), jamais média simples dos rendimentos. Nunca desagregar o rótulo PAM para pixels/talhões como se fosse verdade de campo.

### Especificação do modelo que deve ser implementada
Para cada cultura separadamente, estabelecer primeiro baseline de produtividade microrregional usando somente safras anteriores: mediana móvel ponderada pela área colhida (3–5 safras), tendência Theil–Sen, MAD/IQR interanual e cobertura observacional. Em seguida treinar modelos comparáveis:
1. baseline histórico microrregional;
2. baseline de clima + baseline microrregional;
3. SAR fenologia/vigor + clima + baseline microrregional;
4. modelo híbrido de crescimento de cultura (SAFY-WB/DSSAT/ORYZA, apenas quando cultura e parâmetros forem adequados) como candidato comparativo, nunca como verdade sem calibração.

Não fundir produtos de clima que não compartilhem períodos/variáveis. NASA POWER prioriza histórico em grade; CPTEC/INPE complementa previsão futura. SAR deve incluir séries Sentinel-1 com calibração/orbita/incidência/ruído documentados, variáveis VV/VH/razão e métricas temporais fenológicas justificadas. SAR de identificação de cultura mantém prioridade sobre MapBiomas. Sinal de estresse é inespecífico, não diagnóstico de praga/doença. Medir o ganho incremental do SAR em teste independente contra baseline microrregional+clima; se não houver ganho demonstrado, não afirmar que SAR melhora a previsão.

### Incerteza e validação: critérios científicos
Usar validação temporal expanding-window e holdout espacial em blocos contíguos de microrregiões/estados, com conjunto final intacto. Evitar vazamento de estatísticas futuras na construção de médias móveis e tendências. A calibração e teste devem separar microrregiões e safras; não tratar anos/pixels correlacionados como observações binomiais independentes. O split-conformal marginal só sustenta cobertura sob exchangeability; declarar essa hipótese, testar cobertura por região/safra e não anunciar garantia condicional fora do domínio. Para dependência espacial, calibrar por grupos/blocos ou usar conformalização em blocos; reportar método, nível nominal, cobertura no holdout, tamanho efetivo por clusters, IC de cobertura ajustado ao desenho e largura dos intervalos. Fazer bootstrap em clusters espaciais/safras para métricas e diferenças de MAE/RMSE. Incluir incerteza de rótulo, clima futuro e transferência. Verificar cobertura e utilidade agronômica por cultura, região e horizonte; detectar extrapolação e abster-se se fora do suporte.

A regra de Wilson simples do código atual não prova validade de intervalo sob dependência entre microrregiões nem calibração condicional. Revisar os critérios de elegibilidade: relatório por bloco e cobertura agrupada não podem ser contados como independentes se os blocos se sobrepõem; um bloco com poucos registros não é evidência de calibração. Não fixar thresholds arbitrários (p.ex. n mínimo) como substituto de justificativa estatística, e explicar decisões no relatório de auditoria.

### Pendências de integração
- Criar ingestor SIDRA com cache versionado, retries, validação de esquema e licença/proveniência; materializar séries PAM/N9 para oito produtos e validar anos/códigos.
- Criar painel anual harmonizado com clima histórico (NASA POWER) e séries SAR retrospectivas por MI ou unidades amostrais, preservando escala administrativa; metadados do sensor e processamento são obrigatórios. Documentar municípios que compõem cada MI e mudanças de limites/códigos.
- Integrar microregionais somente como baseline/preditor com defasagem, sem vazamento temporal, e como unidade de inferência declarada.
- Revisar o trainer para ablações baseline MI, MI+clima e MI+clima+SAR; adicionar teste de não vazamento, teste de dependência espacial e teste de abstensão fora do domínio.
- Só após dados reais, treino e avaliação final elegíveis, integrar a saída ao painel executivo (previsão e intervalo simples, cultura, safra, MI/região, data e status). Fontes, fórmulas, parâmetros, datasets, licenças, métricas, cortes e limitações ficam na aba Auditoria.
- Rodar CI Windows e gerar/inspecionar executável novo após integração. O build v3.24.41-CANDIDATE do HEAD 98c655cd é anterior ao módulo de previsão e não comprova essa funcionalidade.

### Fontes primárias e limites da evidência
- IBGE PAM/SIDRA tabela 5457: https://sidra.ibge.gov.br/tabela/5457
- API oficial SIDRA: https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112/p/2023/c782/all
- Estudo de soja com sensoriamento remoto e clima em escala municipal no Sul do Brasil (demonstra método local; não comprova transferência a outras culturas/regiões): https://www.sciencedirect.com/science/article/pii/S0168192319305027
- SAFY-WB com GAI derivado de Sentinel-1, óptico e balanço hídrico para milho em dois ciclos na França; referência metodológica, não validação brasileira: https://doi.org/10.1109/JSTARS.2018.2878502
- Modelo de arroz com SAR, óptico e meteorologia em domínio asiático; referência metodológica, não coeficientes transferíveis: https://www.sciencedirect.com/science/article/pii/S0168192323004197

**Estado final deste adendo:** a série de produtividade oficial microrregional está identificada e o endpoint foi consultado, mas ainda precisa ser materializada e pareada a dados SAR/clima. As equações existentes são treináveis no código, porém nenhum modelo de previsão de safra está operacional/validado na aplicação. Manter previsão bloqueada até concluir aquisição, integração, backtest e incerteza por cultura.

## Atualização urgente — construção de séries reais SAR × produtividade PAM (24/10/2026)

### Progresso de aquisição verificado nesta sessão
- API SIDRA oficial respondeu com dados reais para PAM tabela 5457, microrregiões N9, 2015–2024. Consulta anual com variáveis 112 (rendimento médio, kg/ha), 214 (produção, t) e 216 (área colhida, ha) retorna registros oficiais e unidades identificadas. Exemplo para soja: https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112,214,216/p/2015-2024/c782/40124. A API aceitou 2015–2024 para um produto e retornou 5.581 linhas incluindo cabeçalho (558 microrregiões × 10 anos + cabeçalho); os valores variam por produto e supressões.
- Códigos de cultura SIDRA: arroz 40102, café total 40139 (arábica 40140, canephora 40141), cana 40106, feijão 40112, laranja 40151, milho 40122, soja 40124 e sorgo 40125. Não tratar laranja como citros genéricos nem sorgo em grão como forrageiro.
- Catálogo STAC oficial Copernicus Data Space está acessível em https://stac.dataspace.copernicus.eu/v1/search. Uma busca de teste por bbox no oeste do Pará e safra 2022/23 retornou itens Sentinel‑1 GRD com datetimes UTC precisos e assets VV/VH mais assets de produto/calibração/ruído. Isso prova descoberta de cenas, mas ainda não a extração dos valores SAR por pixels da cultura.
- Não existe ainda série SAR×PAM numérica correlacionada e validada no repositório. A aquisição SIDRA e a descoberta de cenas são passos reais; não declarar correlação, associação, ganho preditivo ou modelo operacional enquanto faltar máscara SAR de cultura validada e extração radiométrica espacial.

### Tarefa de construção de dados — continuar sem interrupção
1. Materializar em arquivos versionados os dados oficiais do SIDRA por produto, N9 e safra, com códigos, descrições, unidade, ano, município/MI, variáveis 112/214/216, resposta bruta, data de extração, URL, validação de qualidade e licença/termos de uso. Reconciliar rendimento publicado com produção/área quando houver suporte; suppressões não são zero.
2. Obter geometria compatível das microrregiões geográficas do IBGE (as unidades antigas N9; usar malha de referência temporal explícita e mapa de correspondência se limites/códigos mudarem). Recortar ou estratificar pixels pela geometria e preservar o código IBGE.
3. Consultar STAC Sentinel‑1 por interseção espacial e janela anual por MI, paginar todos os resultados e arquivar scene_id, sensor, órbita relativa, direção, polarização, datetime original UTC, footprint, URL e checksum/metadados de processamento. Para feature da safra, converter UTC→America/Sao_Paulo apenas para apresentação; nunca substituir o timestamp original.
4. Extrair VV/VH (unidade linear ou dB declarada), VH/VV, estatísticas robustas e trajetória temporal apenas em pixels classificados como a cultura pelo classificador SAR que passe validação independente. Corrigir/calibrar com assets de calibração/ruído; filtrar bordas, layover/shadow quando mapeáveis, água/inundação, órbita/incidência, speckle e observações contaminadas por chuva/umidade/água. Fixar e registrar janela fenológica por cultura/região usando calendários oficiais/estudos, não janelas globais arbitrárias.
5. Agregar para a mesma escala da PAM: mediana/quantis ponderados pela área de pixels válidos da cultura por MI×safra×janela. Guardar número de cenas, área válida, cobertura percentual, órbitas, distribuição e incerteza da extração. Não usar média da microrregião inteira como se fosse SAR da cultura, nem extrapolar uma média administrativa para talhão.
6. Parear o resultado SAR com produtividade PAM apenas na mesma microrregião e safra correta. Controlar clima histórico com NASA POWER como fonte prioritária; não misturar reanálise e previsão CPTEC num mesmo treino sem separar função temporal. Como PAM é produtividade em kg/ha agregada a nível MI e SAR de cobertura terrestre é observação remota, qualquer resultado é associação ecológica/administrativa, não causal nem produtividade medida no talhão.
7. Para cada cultura calcular correlações exploratórias robustas (Spearman/Kendall e regressões com efeitos de ano/estado, autocorrelação espacial/temporal e erros agrupados por MI). Apresentar n efetivo, cobertura, intervalo por bootstrap em blocos espaciais e safras, controle por clima, áreas colhidas, tendência tecnológica e mudança de limites. Comparar baseline PAM defasado, PAM+clima e PAM+clima+SAR. Separação por holdout geográfico e temporal antes de qualquer conclusão preditiva. SAR só é contribuição útil se melhorar baseline no teste final com intervalo de diferença de desempenho e calibração independente.
8. A escala exige cautela: PAM N9 cobre a divisão microrregional anterior às Regiões Geográficas Imediatas/Intermediárias de 2017. Não reutilizar shapefile/IDs antigos sem documentação. Efeito de mudança de limites deve ser resolvido por harmonização espacial consistente ao longo de toda a série ou as microrregiões incompatíveis ficam fora.
9. Se não houver classificador SAR de cultura validado que permita criar máscara sem MapBiomas pseudo-rótulo, não calcular “média SAR da lavoura” nem correlação SAR-produto. Ainda assim, materializar imediatamente série de produtividade e catálogo de cenas como inventário de cobertura; marcar a correlação como bloqueada pela máscara de cultura e continuar buscando dados abertos de validação. MapBiomas pode ajudar a escolher áreas candidatas/estratificação exploratória, nunca pode ser citado como validação independente do SAR.
10. Atualizar painel executivo somente com estimativas elegíveis; mostrar previsões e intervalos simples quando validadas. Séries, datas de aquisição, URLs, filtros, máscaras, distribuição, métodos, métricas e cobertura ficam na aba Auditoria técnica.

### Estado atualizado sem extrapolação
Dados reais de produtividade e áreas PAM são adquiríveis; catálogo Sentinel‑1 fornece datas auditáveis e ativos VV/VH. Ainda não há produto SAR agregado em máscara de cultura independente e alinhado à safra para calcular correlações válidas. A próxima ação é implementar o materializador SIDRA e coletor STAC, materializar seus arquivos e depois integrar extração espacial SAR com máscara validada. Até esses passos e a validação espacial/temporal, a previsão de safra continua não operacional e deve permanecer bloqueada.

## Última orientação e atualização da série (24/10/2026)

O usuário orientou: “concluir e validar correlação SAR‑produtividade” e pediu que o prompt fosse disponibilizado imediatamente. A série oficial PAM foi agora materializada localmente pelo script tools/build_sidra_pam_microregion_series.py em data/pam_microregion_yield_2015_2024.csv, com metadados em data/pam_microregion_yield_2015_2024.metadata.json. A extração retornou 133.920 registros (8 produtos × 558 microrregiões × 10 anos × 3 variáveis), 16.740 registros por produto. SHA-256 do CSV: 58fc371ab536e3499aa1561e2d8d996f0b5b082dfd181aca16232c37f8c9fffe. Isso constitui dados observados oficiais de rendimento/produção/área, não dados SAR nem correlação.

A última tentativa de associação confirmou cenas Sentinel‑1 no catálogo, mas não extraiu valores de retroespalhamento mascarados por cultura. Portanto, não afirmar que a correlação foi concluída ou validada. A pendência científica requer: (a) máscara de cultura confirmada por classificador SAR com validação externa independente; (b) processamento radiométrico e geométrico consistente das cenas; (c) pareamento de observações de safra correta e território harmonizado; (d) teste contra produtividade PAM com holdout espacial e temporal. A distribuição inteira da microrregião não pode substituir pixels identificados como a cultura.

Próxima implementação concreta: completar script de catálogo STAC paginado com geometrias IBGE de referência e janela temporal por cultura, gravar inventário de aquisições com datetime UTC/órbita/polarização/assets/proveniência; obter/validar máscara SAR de cultura; extrair estatísticas espaciais por microrregião×safra×fenologia; então calcular associação parcial após clima/tendência e intervalos por bootstrap em blocos espaço-temporais. Registrar suporte, número de unidades independentes, área/pixels válidos e resultado por cultura. Se os dados não permitirem máscara/validação, manter conclusão “correlação não validada” e previsão bloqueada.

Não confundir “prompt atualizado” nem “série PAM materializada” com conclusão da correlação. Prompt deve permanecer atualizado com os resultados reais de cada marco.

## Atualização urgente — artefatos de dados e limite de acesso SAR

Foi materializado no checkout do repositório:
- data/pam_microregion_yield_2015_2024.csv.gz — 133.920 registros brutos da PAM/SIDRA (8 culturas × 558 microrregiões × 10 anos × 3 variáveis); SHA-256 gzip: aa6f33a3371aa77e5b454c610569a603654cf6599870893da545c2e74286139d.
- data/pam_microregion_yield_2015_2024.metadata.json — endpoints consultados, códigos, unidades, data/hora de consulta, contagens e limitações.
- tools/build_sidra_pam_microregion_series.py — rotina reproduzível com tentativas, cabeçalho/esquema, preservação dos valores originais e marcação de dados ausentes/suprimidos.

Contagens de valores válidos (variáveis de rendimento/produção/área; cada variável tem a mesma máscara de disponibilidade oficial observada nesta extração): arroz 3.448; café total 2.415; cana 4.682; feijão 5.249; laranja 4.394; milho 5.334; soja 2.951; sorgo 1.538, de 5.580 possibilidades por cultura/variável. Isso significa cobertura desigual; análises precisam documentar n e não imputar ausentes como zero.

O STAC Copernicus devolveu cenas Sentinel‑1 reais, IDs, timestamps UTC e assets VV/VH. Porém, ao tentar acessar os COGs para ler pixels, os URLs S3/HTTPS responderam acesso negado/indisponível sem autenticação. O checkout não tem credenciais Copernicus. Não foi extraído qualquer retroespalhamento, média por pixel ou estatística SAR correlacionável à PAM. Além disso, não existe máscara de cultura via SAR com validação externa disponível no branch. Portanto, **correlação SAR‑produtividade ainda não está calculada nem validada**. Não usar estatísticas de toda a microrregião, nem máscara MapBiomas, para alegar uma validação SAR.

A próxima execução depende de uma rota legítima de acesso aos COGs (OAuth Copernicus com credenciais fornecidas de forma segura, ou fonte pública equivalente licenciada) e de uma máscara SAR de cultura treinada/validada com rótulos independentes. Em seguida: extrair C-band VV/VH na área de cultura, emparelhar na fenologia/safra com PAM N9, controlar clima NASA POWER e validar holdout espaço-temporal com bootstrap em blocos. Sem esses dados, a entrega correta é a série PAM real e inventário de cenas auditáveis com status de correlação bloqueada, nunca uma correlação artificial.

O arquivo do prompt foi atualizado para a orientação mais recente do usuário e deve ser disponibilizado com link estável da Biblioteca além do arquivo para download do workspace.

## Nova orientação do usuário — remover bloqueio de autenticação SAR

O usuário pediu solucionar a pendência de acesso aos rasters e concluir/validar a correlação SAR–produtividade e, em seguida, orientou incluir no prompt essa nova direção. Não condicionar a extração à conta Copernicus: avaliar e priorizar catálogos públicos que forneçam COGs assinados e acesso sem credenciais individuais. A coleção Sentinel‑1 RTC do Microsoft Planetary Computer foi confirmada acessível por STAC e endpoint público de SAS token durante esta sessão; testar imediatamente para substituir a rota CDSE bloqueada, documentando versão da coleção, sistema de calibração, unidade, órbita e limitações.

O candidato de máscara independente deve ser investigado em paralelo. O estudo brasileiro de soja em western Bahia (Parreiras et al., 2022; HLS óptico e validação de classificação) é evidência de método local para soja, mas não é classificador SAR nem máscara SAR; não o declarar como validação SAR. MapBiomas pode servir de referência/estratificação independente provisória para análise exploratória, conforme orientação do produto, mas não deve substituir o identificador SAR validado nem servir simultaneamente como rótulo e teste independente. Buscar pontos/parcelas agrícolas observados com licença pública ou benchmarks de talhões com produtividade e geometrias (incluindo YieldSAT quando acessível); cruzar as geometrias com Sentinel‑1 RTC para treinar/validar classificação em unidades agrupadas por fazenda/ano.

Fluxo obrigatório atualizado:
1. Validar publicamente a assinatura/abertura de um COG RTC Sentinel‑1 para uma geometria das microrregiões com maior área/produção PAM; salvar prova de leitura, aquisição UTC e checksum/ID.
2. Materializar inventário de cenas e métricas temporais por MI e cultura; manter a série PAM oficial já materializada.
3. Criar a máscara SAR de cultura com verdade de referência independente e split espacial-temporal; relatar matriz de confusão, precisão, revocação, F1, IC e domínio. Se não houver rótulo suficiente, manter máscara como exploratória e não usar para a correlação validada.
4. Extrair estatísticas VV/VH em pixels de cultura confirmados e fenologia/safra; documentar cobertura espacial e incerteza da extração.
5. Parear a série SAR com PAM na geografia e safra harmonizadas, controlar clima e tendência, calcular associação por correlação parcial/regressão em painel com efeitos de microrregião/ano e bootstrap em blocos; avaliar ganho preditivo em holdout espacial-temporal.
6. Se resultar associação válida em uma cultura/região, relatar exatamente esse domínio e intervalo; não generalizar para as oito culturas. Se os rótulos/máscara forem insuficientes, explicar a lacuna remanescente sem fabricar correlação.

Uma consulta STAC ou um token SAS só demonstra acesso e disponibilidade de metadados; só a abertura do COG e extração espacial de pixels contam como acesso aos valores SAR. O teste real do Microsoft Planetary Computer ainda precisa ser feito. Atualizar prompt novamente com resultado de abertura, extração e validação assim que verificados.



## ATUALIZAÇÃO URGENTE — PAM materializada e rota pública para pixels Sentinel‑1 encontrada (24/10/2026)

### Dados PAM/SIDRA materializados nesta retomada
Foi criado e executado `tools/build_sidra_pam_microregion_series.py`, com retries, validação do esquema SIDRA, preservação de valores suprimidos como ausentes e registro de proveniência. Arquivos produzidos localmente; o CI os materializa novamente e publica o conjunto validado:
- `data/pam_microregion_yield_2015_2024.csv.gz`: 133.920 células — 8 produtos × 558 microrregiões N9 × 10 anos (2015–2024) × 3 variáveis. SHA‑256 atual: `3d73b520e88c7cd6cc527257d435341ef7eb1715fed378ac9be46f122e87f30f`.
- `data/pam_microregion_yield_2015_2024.metadata.json`: URLs SIDRA, unidades, data/hora de extração, cobertura, contagem de supressões e reconciliação.
- `tests/test_sidra_pam_materializer.py`: verifica integridade da série/checksum e que `...`, `..`, `-` e `X` não viram zero. Dois testes locais passaram.

O CSV completo é gerado localmente e novamente no início do workflow Windows; o workflow publica CSV e metadados como artefato de dados por 30 dias para evitar consumir um arquivo incompleto ou desatualizado do checkout.

Reconciliado rendimento oficial (kg/ha) com produção × 1000 / área colhida em todos os tripletos numéricos: 30.011 tripletos por variável no conjunto de oito produtos; a diferença relativa mediana por produto é menor que 0,03%, e praticamente todos estão dentro de 2%. Esta checagem atesta consistência das colunas PAM, não SAR nem produtividade de talhão. Os 14.629 valores ausentes/suprimidos por variável permanecem nulos. Para feijão e milho há poucos tripletos fora de 2%, que devem continuar auditados e não ser sobrescritos.

### Nova rota pública de aquisição SAR — teste efetivamente realizado
O catálogo CDSE/STAC inicial era acessível, mas os COGs retornavam erro de autenticação. Foi testada a rota pública Microsoft Planetary Computer:
- STAC search sem login: `https://planetarycomputer.microsoft.com/api/stac/v1/search`, coleção `sentinel-1-rtc`.
- Solicitação de token SAS temporário pelo endpoint público do próprio catálogo: `https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel1euwestrtc/sentinel1-grd-rtc`.
- AOI de teste: bbox em Brasília `[-47.95, -15.85, -47.90, -15.80]`, janela 01–31/01/2023.
- Cena descoberta: `S1A_IW_GRDH_1SDV_20230129T084531_20230129T084556_046996_05A31F_rtc`; aquisição `2023-01-29T08:45:43.608955Z`; assets VV e VH disponíveis.
- Ativos sem assinatura falharam com HTTP 409. Com SAS temporário obtido anonimamente, pedido HTTP `Range: bytes=0-1023` ao asset VV retornou HTTP 206 e 1.024 bytes; o objeto COG tem 1.856.447.477 bytes.

**Interpretação rigorosa:** o teste prova descoberta de cena, emissão pública de assinatura e acesso por range ao objeto; ainda não prova leitura/decodificação de valores de píxel, nem extração espacial da AOI, máscara de cultura, associação SAR–PAM ou previsão. O próximo passo é abrir o COG assinado com Rasterio/GDAL e ler uma janela pequena de VV/VH sobre a geometria, conferir CRS, escalas/unidades e nodata, registrar `id`/data UTC/checksum da resposta e depois automatizar download parcial por range. Não imprimir nem persistir o SAS token; solicitar token renovável em runtime e reemitir quando expirar.

A rota pública MPC passa a ser **prioridade para resolver os COGs inacessíveis**. Copernicus Data Space OAuth2 fica como primeira alternativa; ASF HyP3/Earthdata como segunda alternativa (requer login); Earth Engine autenticado como rota de validação/prototipagem. O produto MPC é RTC, não o mesmo produto nem a mesma cadeia de processamento que o GRD do CDSE: guardar processador/versão, retroespalhamento, escala, órbita e limitações em cada cena, e não misturar sem harmonização.

### Alternativas para a máscara e validação de cultura
- **YieldSAT** é o candidato prioritário para rótulos independentes de milho e soja: a documentação reporta 118 campos brasileiros de milho e 293 de soja, 2017–2024, com colheita georreferenciada e Sentinel‑2. Não lista Sentinel‑1; cruzar as geometrias/anos com Sentinel‑1 RTC e treinar/validar máscara SAR temporal em split separado por fazenda/região e safra. Confirmar acesso e licença antes de usar comercialmente; o site oferece fluxo de solicitação de acesso. Não enviar solicitação a terceiros sem autorização explícita.
- YieldSAT não supre validação de arroz, café, cana, feijão, laranja/citros ou sorgo. Não transferir modelo entre culturas. Para culturas sem amostras independentes, continuar com classe genérica “áreas cultivadas” ou abstenção.
- MapBiomas e PAM podem apoiar estratificação/prior fraco ou checagem de áreas candidatas; não usar MapBiomas como teste independente do classificador que o utilizou como rótulo, nem converter rótulo PAM municipal em pixels verdadeiros.

### Próximo plano operacional obrigatório
1. Implementar adaptador `sentinel-1-rtc` para MPC: STAC com paginação, token SAS anônimo renovável, leitura COG por range, extração efetiva de pixels em bbox de Brasília e AOIs prioritárias, datas/órbitas VV/VH, janela espacial, filtro de água e tratamento explícito de nodata. Guardar rastreabilidade sem token.
2. Comparar uma amostra pontual de valores lidos com a visualização/estatística independente do mesmo item e testar diferentes ângulos e unidades. Uma amostra de pixels não é produto de cultura.
3. Obter, conforme licença, rótulos de campo de YieldSAT e parear os campos com a série Sentinel‑1 RTC. Validar classe em holdout agrupado por região/fazenda e safra; publicar matriz de confusão, precisão, revocação, F1, IC e domínio.
4. Só após máscara independente aprovada, computar estatísticas SAR sobre pixels dessa cultura por N9×safra×janela fenológica. Não usar a distribuição inteira da microrregião.
5. Parear com o CSV PAM existente; executar baseline PAM defasado, PAM+clima e PAM+clima+SAR, controlando clima/tendência e usando holdout espaço-temporal e bootstrap em blocos. Relatar associação por cultura/região com intervalos e escala administrativa. Previsão numérica continua fail-closed até superar o baseline em teste independente e calibrar intervalo preditivo.
6. Atualizar a interface e gerar novo EXE somente depois de integração funcional e CI Windows aprovado. O artefato v3.24.41-CANDIDATE run 639 (`40127189189`) antecede estas alterações e não deve ser apresentado como nova versão funcional de previsão ou correlação.

### Alternativas resumidas e prioridade
1. **MPC Sentinel‑1 RTC público com SAS temporário:** primeira escolha; acesso STAC e leitura range do objeto foram confirmados sem credencial individual nesta retomada.
2. **CDSE/OData + OAuth2:** alternativa para dados nativos e processamento local controlado.
3. **ASF HyP3 + Earthdata Login:** alternativa para RTC/ortorretificação sob demanda.
4. **Earth Engine `COPERNICUS/S1_GRD_FLOAT` ou `S1_GRD`:** protótipo ou checagem cruzada, condicionado a conta/quotas.

### Fontes consultadas
- Microsoft Planetary Computer STAC/API e acesso aos dados: https://planetarycomputer.microsoft.com/docs/ ; SAS: https://planetarycomputer.microsoft.com/docs/concepts/sas/ ; item RTC: https://planetarycomputer.microsoft.com/explore?d=sentinel-1-rtc
- Copernicus Data Space OData e autenticação: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- ASF HyP3/Earthdata: https://hyp3-docs.asf.alaska.edu/using/authentication/
- Google Earth Engine Sentinel‑1: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD
- YieldSAT dados e distribuição: https://yieldsat.github.io/ ; artigo: https://arxiv.org/abs/2604.00940

**Estado verdadeiro após a atualização:** dados PAM reais estão materializados e auditados; descoberta de cenas Sentinel‑1 RTC e acesso autenticado anonimamente a ranges do COG foram confirmados. Correlação SAR × produtividade ainda NÃO VALIDADA; previsão numérica ainda NÃO OPERACIONAL. O gargalo seguinte é leitura real de píxeis, acesso/licença a rótulos de cultura independentes e validação espaço-temporal.

## ADENDO URGENTE — atualidade SAR como critério central (24/10/2026)

O usuário reforçou que a atualidade das aquisições SAR é fundamental para acompanhar fenologia e prever safra. Tratar atualidade como critério de elegibilidade central em toda análise agrícola e previsão:

- Usar data/hora de aquisição (`datetime` original UTC) para atualidade. Publicação, processamento e ingestão no catálogo não substituem aquisição. Exibir também UTC−3, área coberta, órbita relativa, polarização, fonte, última aquisição válida e idade em dias/horas.
- Consultar mais de um catálogo quando necessário e comparar a aquisição mais recente disponível por AOI: MPC Sentinel‑1 RTC, CDSE/STAC e ASF/HyP3. Relatar falhas, lacunas e defasagem de cada provedor. A cena encontrada em janeiro/2023 prova cobertura histórica, mas não atualidade para monitoramento em 2026.
- Derivar critérios temporais por cultura, região e fase fenológica a partir de calendário agrícola verificável, cadência orbital realmente observada na AOI e desempenho do modelo. Não usar limite global fixo de 12 dias, janela fixa de 90 dias ou número fixo de cenas como prova de atualidade.
- Sem limite de idade, janela de série e número mínimo de observações empiricamente justificados e registrados, o status deve ser `criterios_temporais_nao_definidos` e a inferência fenológica/previsão fica bloqueada. Cenas recentes no catálogo não bastam: exigir pixels válidos, cobertura da cultura e pré-processamento efetivo.
- Se a cena mais recente superar o limite validado para a fase, classificar como desatualizada e abster-se de diagnóstico/previsão. Reportar a aquisição efetiva mais recente, idade, revisita esperada e falhas de cobertura.
- Modelos fenológicos exigem uma trajetória no intervalo relevante da cultura; verificar observações válidas e lacunas de aquisição em relação à fase, sem misturar órbitas, sensores e processadores sem harmonização.
- A previsão deve usar imagem SAR observada até a data de emissão e separar aquisição observada de previsão meteorológica futura. Indicar `as of` e timestamp da última aquisição realmente incluída nas features.

### Alteração de código nesta retomada

`agricultural_sar_freshness.py` deixou de assumir idade máxima de 12 dias, janela de 90 dias e mínimo de 3 cenas. Agora recebe cultura, região, fase, idade máxima, janela da série, mínimo de cenas e fonte dos critérios. Se faltar qualquer critério, retorna `criterios_temporais_nao_definidos` e o gate impede chamar o diagnóstico de atual. Testes novos verificam bloqueio sem limites definidos, avaliação com critérios explícitos e abstensão quando a aquisição está desatualizada.

### Pendências e próximos passos imediatos

1. Integrar esse gate ao pipeline executivo de previsão, associando cultura e fase vigente ao calendário agrícola regional.
2. Implementar consulta de atualidade a MPC/CDSE/ASF, com deduplicação de cenas e relatório de cobertura/latência por fonte.
3. Ler pixels reais dos COGs MPC assinados e medir a latência da coleção RTC para uso operacional, comparando com a aquisição mais recente do CDSE.
4. Só disponibilizar análise fenológica atualizada após a aquisição recente e pixels válidos. Acesso a COG histórico ou inventário de metadados não satisfaz atualidade nem habilita previsão.

**Estado após esta orientação:** requisito incorporado no prompt e gate de atualidade atualizado no código local; consulta a aquisições recentes de 2026 concluída para Brasília; ainda faltam latência de publicação, leitura/decodificação de pixels geoespaciais, integração ao painel, máscara independente, correlação SAR–PAM e previsão validada. Não declarar esses itens concluídos.

O gate atualizado foi verificado localmente em 3 testes de atualidade; os 2 testes PAM também passaram. O workflow Windows agora regenera e publica a série PAM, e inclui esses testes na suíte do PR.

## ADENDO — aquisição SAR recente encontrada para Brasília (24/10/2026)

Para responder ao requisito de atualidade, foi feita uma consulta real ao STAC do Microsoft Planetary Computer Sentinel‑1 RTC, com bbox `[-47.95, -15.85, -47.90, -15.80]` e janela 24/09/2026–24/10/2026. O catálogo retornou 3 aquisições na mesma órbita aproximada:

- `S1D_IW_GRDH_1SDV_20261023T084435_20261023T084500_005140_009BDC_rtc` — `2026-10-23T08:44:48.422103Z`;
- `S1D_IW_GRDH_1SDV_20261011T084435_20261011T084500_004965_0095DD_rtc` — `2026-10-11T08:44:48.369349Z`;
- `S1D_IW_GRDH_1SDV_20260929T084435_20260929T084500_004790_008FB0_rtc` — `2026-09-29T08:44:48.209219Z`.

A última aquisição listada é de 23/10, aproximadamente um dia antes da consulta; as três datas mostram intervalos de 12 dias nesta AOI/período. O resultado comprova que o catálogo RTC pode oferecer observações recentes sobre Brasília em 2026, sem login individual. **Não comprova latência sistemática de publicação** (o campo de publicação ainda precisa ser verificado), leitura/decodificação de VV/VH, pixels válidos, cobertura da lavoura, identificação de cultura ou vigor. Não generalizar a atualidade para outras AOIs, órbitas ou datas.

### Próxima verificação operacional de atualidade

1. Em consultas programadas por AOI, registrar separadamente acquisition datetime, published/created datetime quando presentes, diferença aquisição→disponibilização, IDs e footprints.
2. Assinar os assets da aquisição de 23/10/2026 e abrir uma janela COG por GDAL/Rasterio sobre a área de teste; guardar valores VV/VH, CRS, nodata, unidade/escala e pixels válidos. Nunca salvar o token SAS.
3. Comparar a série observada de cada AOI com revisita e órbita realmente presentes; usar os intervalos observados como evidência, mas calibrar o limite de idade por cultura/região/fase antes de habilitar previsão.
4. Manter abstenção quando o catálogo não tiver aquisição suficientemente recente segundo critério validado, mesmo que haja dados históricos acessíveis.

**Atualização de estado:** existe evidência concreta de cenas SAR atuais no catálogo para Brasília (última aquisição 23/10/2026, 1 dia antes da busca) e de cadência observada de 12 dias nessa série curta. A adequação para monitoramento de safra continua pendente até medir latência, ler pixels válidos e validar máscara/fenologia; previsão e correlação SAR–PAM seguem bloqueadas.

### Resultado adicional — janela recente e latência de publicação

Foi assinado o asset VV da aquisição de 23/10/2026 e feito pedido `Range: bytes=0-1023`; a resposta foi HTTP 206, `Content-Range: bytes 0-1023/1863517334`, confirmando leitura parcial do COG recente da Sentinel‑1D. O cabeçalho TIFF começou com bytes válidos, mas a abertura por Rasterio/GDAL não concluiu a leitura geoespacial nesta tentativa. Portanto **nenhum valor VV/VH por pixel foi extraído ainda**. Os itens STAC consultados não expuseram `published` ou `created`; a latência entre aquisição e publicação continua não quantificada. Repetir a leitura Rasterio/GDAL com tratamento explícito do SAS e validar CRS/janela/nodata antes de declarar extração de pixel.

## ADENDO DE CONCLUSÃO TÉCNICA — pixels SAR recentes e bloqueio de previsão por atualidade (24/10/2026)

### Evidência SAR que substitui afirmações anteriores

A tentativa de leitura que falhou por configuração de certificados foi repetida com a CA do sistema configurada explicitamente para GDAL/Rasterio, mantendo verificação TLS habilitada. O COG Sentinel‑1 RTC público do Microsoft Planetary Computer foi aberto e VV/VH foram lidos de fato por janela georreferenciada na cena `S1D_IW_GRDH_1SDV_20261023T084435_20261023T084500_005140_009BDC_rtc` (aquisição `2026-10-23T08:44:48.422103Z`), sobre a amostra de Brasília.

- CRS do raster: EPSG:32723; tipo float32; nodata `-32768`; janela 3×3 com 9/9 pixels válidos em VV e VH.
- Mediana da janela: VV `0.34589219`; VH `0.09606396` (valores nativos do produto RTC).
- O item identifica gamma naught/RTC, mas não fornece unidade explícita nos metadados consultados. Não converter para dB, não nomear como potência calibrada em unidade específica e não tratar a amostra como estatística de lavoura.
- Isso prova abertura geoespacial e leitura de pixels válidos sobre uma janela de teste; não prova que os pixels sejam soja/milho ou outra cultura, vigor fenológico validado, cobertura agrícola, latência sistemática de publicação ou correlação com PAM. `published`/`created` continuam ausentes. A leitura pontual não equivale à extração por polígono/cultura.

Este resultado **corrige e substitui** os trechos anteriores deste prompt que diziam “nenhum valor por pixel foi extraído” ou que a leitura COG ainda precisava ser feita. O teste de range HTTP foi seguido por leitura Rasterio bem-sucedida. A lacuna de publicação e os bloqueios de máscara, fenologia e validação permanecem.

### Alteração implementada no caminho de previsão

`evaluate_yield_forecast` agora exige `freshness_provenance` explicitamente. A elegibilidade é negada se os critérios temporais não estiverem definidos, se o estado não indicar cenas recentes, se cultura/região não corresponderem, se faltar fase fenológica, se a idade exceder o limite por cultura/fase, se a quantidade mínima de cenas não for atingida ou se a aquisição for posterior à data de referência. `forecast_crop_yield` propaga essa proveniência como argumento obrigatório. Os testes cobrem atualidade ausente, SAR desatualizada e divergência de região; o forecast permanece condicionado também a evidência SAR independente, validação espaço-temporal e intervalo preditivo calibrado.

### Verificação local e estado de entrega

- Testes focados de atualidade SAR, forecast/incerteza e materializador PAM: **14 passaram** após disponibilizar a série PAM materializada no checkout para execução do teste.
- Descoberta completa de testes: **183 executados; 16 ignorados; 6 erros por dependências ausentes/incompletas neste ambiente** (`requests`/`Session` e `geopandas`). Não atribuir esses erros ao código agrícola alterado; a suíte equivalente precisa ser confirmada no workflow Windows com dependências completas.
- O gate de atualidade foi conectado ao módulo de qualidade e ao entry point de previsão, mas não há chamada desse entry point pelo desktop/interface identificada nesta revisão. Não afirmar integração visual.

### Pendências científicas que continuam bloqueando correlação e previsão publicadas

1. Disponibilizar máscara/labels independentes com licença adequada e validação SAR para cada cultura, região e safra; sem isso, pixel RTC não é pixel de cultura.
2. Implementar extração por polígonos/unidades N9 e calendário fenológico validado, guardando cobertura, órbita, qualidade e incerteza por cena.
3. Medir aquisição→publicação em observações repetidas e consultar cadência atual por AOI/cultura/fase; a amostra recente de Brasília não define atualização operacional geral.
4. Parear SAR/clima/PAM e executar comparação baseline vs. SAR com holdout espaço-temporal independente e incerteza agrupada por blocos.
5. Integrar a API de previsão ao fluxo da aplicação e produzir novo build Windows; a versão candidata anterior não contém essas mudanças.

**Conclusão responsável:** a PAM foi materializada e auditada; há leitura real de VV/VH RTC recente e o gate de atualidade foi inserido no código de previsão. A correlação SAR–produtividade e a previsão operacional continuam não validadas e devem permanecer bloqueadas até fechar as cinco pendências acima. Prioridade para monitoramento fenológico continua sendo idade de aquisição e atualidade por AOI/fase, com abstensão explícita quando a evidência temporal não satisfizer critérios calibrados.

## ADENDO URGENTE — rotas alternativas para evidência independente SAR × PAM e previsão (24/10/2026)

O usuário solicitou criar todas as rotas possíveis para solucionar a falta de máscara independente, extração por área agrícola, atualidade calibrada e backtest. Foi criado `docs/ROTAS_EVIDENCIA_SAR_PAM_CULTURAS_E_PREVISAO.md`, com fontes, papéis permitidos, alternativas e fluxo separado para (1) associação regional com PAM e (2) previsão de rendimento em campo.

### Rotas implementadas neste adendo

- `agricultural_evidence_routes.py`: catálogo priorizado de YieldSAT, CropHarvest, MapBiomas Agricultura, IBGE PAM/N9 e polígonos de talhão; `plan_evidence_routes()` declara limitações e blockers por tarefa e nunca habilita liberação científica automaticamente. A junção `build_pam_sar_panel()` pareia PAM real à tabela SAR por cultura×N9×ano e exige uma aprovação explícita de máscara independente, hash de modelo e proveniência. Essa flag é contrato/auditoria de entrada, não certificado automático de validade.
- `sentinel1_mpc.py`: busca Sentinel‑1 RTC via STAC público paginado, deduplica cenas, obtém SAS curto em runtime, restringe hosts e lê janela COG por coordenada ou estatísticas zonais VV/VH em polígono verificado usando Rasterio com verificação TLS habilitada e CA do sistema. Não guarda token. A leitura não classifica cultura; identidade e independência do polígono vêm da fonte de referência separada.
- `tests/test_agricultural_evidence_routes.py`: contratos de priorização de fontes, bloqueio de pseudo-rótulos MapBiomas, hash/proveniência na junção PAM×SAR e segurança da URL do asset.
- Os gates já existentes seguem obrigatórios: `crop_map_training.py` admite mapas apenas como pseudorrótulo para treino; `independent_sar_validation.py` recebe predições SAR feitas em unidades de campo independentes; previsão exige evidência SAR de cultura/vigor/sinal inespecífico de estresse, clima, atualidade e intervalo calibrado.

### Alternativas de referência identificadas

1. **YieldSAT** (fonte principal para validação externa brasileira de soja/milho/trigo): 293 campos de soja, 118 de milho e 140 de trigo no Brasil segundo a página oficial, safra entre 2017–2024; combina polígonos de campo revisados e rendimento monitorado por colhedora com série Sentinel‑2. A página disponibiliza o fluxo de acesso ao dataset. Cruzar por campo/safra com Sentinel‑1 RTC adquirido pelo sistema. Não considerar a camada Sentinel‑2 como validação SAR, e conferir licença/geografia e distribuição dos holdouts.
2. **CropHarvest**: dataset global aberto com labels binários e multiclasses e subconjunto acompanhado de Sentinel‑1/Sentinel‑2/clima; usar para pré-treino e transferência depois de auditar países, fonte original, classe e duplicatas. Não substitui referência independente específica do Brasil.
3. **MapBiomas Agricultura**: produtos e mapas recortáveis para treinamento fraco, prior/estratificação e amostragem. Proibido usá-los como verdade independente quando o modelo os usou em treino, ajuste ou seleção.
4. **IBGE PAM/SIDRA em N9**: alvo observado agregado para associação regional em 2015–2024; nunca identifica píxeis/talhões. Exige máscaras SAR independentes, harmonização de código territorial e safra e clima alinhado.
5. **Rótulos de campo complementares para arroz, feijão, sorgo, café, cana e citros**: buscar ensaios e parcelas georreferenciados, cooperativas/colhedoras com licença, publicações Embrapa/universidades e dados de pesquisa. CropHarvest/MapBiomas podem complementar treino, não substituir o teste independente específico da cultura.
6. **Geometrias de talhão (ex.: GloCAB e bases públicas/research)**: suportam unidade amostral/buffer, mas sem classe de cultura e safra auditadas não contam como rótulo. PAM municipal ou microrregional não deve ser rasterizada para inventar verdade de pixel.
7. **Aquisição SAR alternativa**: MPC RTC público e paginado (implementado); CDSE STAC/OData para GRD e ASF HyP3/Earthdata como rotas de contingência. Manter órbita, RTC/GRD, versão, unidade e cadeia de processamento segregadas até harmonização.
8. **Atualidade fenológica**: combinar revisita observada por AOI/órbita (MPC/CDSE/ASF) com calendário oficial e pontos de fenologia/rendimento independentes. Calibrar limite de idade com erro do classificador/vigor e do yield por corte temporal em holdout separado; a distribuição de gap orbital sozinha não determina limite biológico. Sem estudo, limite ausente e inferência bloqueada.

### Verificação desta rodada e estado de evidência

Na validação inicial, os testes de rotas, atualidade SAR, previsão/incerteza, treino de pseudorrótulos e contratos de treinamento passaram. **A verificação final desta rodada passou em 31 testes direcionados**. As rotas de código e seus contratos estão preparados; o pacote YieldSAT ainda não foi baixado, a submissão de formulário não foi feita, e não há campos independentes SAR processados, painel real SAR×PAM, limite de atualidade calibrado nem backtest concluído. Portanto a pendência foi avançada com caminhos executáveis e alternativas para cobrir as culturas; a previsão e a correlação continuam não validadas e bloqueadas até consumir os dados reais/licenciados e aprovar o holdout externo.

Fontes primárias registradas no documento de rotas: YieldSAT https://yieldsat.github.io/ ; CropHarvest https://github.com/nasaharvest/cropharvest e https://openreview.net/forum?id=JtjzUXPEaCu ; MapBiomas https://brasil.mapbiomas.org/downloads/ ; IBGE SIDRA https://apisidra.ibge.gov.br/ ; Microsoft Planetary Computer https://planetarycomputer.microsoft.com/docs/.

## ADENDO URGENTE — campos obrigatórios no painel executivo de previsão de safras (24/10/2026)

O usuário solicitou que, em painel executivo simples e separado da trilha de auditoria, sejam apresentados literalmente **“Idade provável da lavoura”**, **“Estado fitossanitário aparente”**, **“Produtividade provável”** e **“Produção provável”**, dentro da previsão de safra. A produção provável é a quantidade total da cultura que ocupa o polígono analisado, calculada pela produtividade estimada × área efetivamente mapeada como aquela cultura dentro do AOI. Não usar a área total quando houver parte sem cultura, nem exibir produção total sem área de cultura conhecida. Implementação desta rodada:

- No desktop, a aba `Painel executivo` mostra os indicadores em linguagem simples e a aba `Auditoria técnica` mantém fontes e evidências em separado. Quando não há evidência aprovada, exibe “INDISPONÍVEL” ou “BLOQUEADA”. A seção de safra apresenta **Produtividade provável** e **Produção provável** como linhas separadas.
- Idade provável só é visível quando a estimativa fenológica é validada e o gate informa `cenas_recentes_identificadas`.
- Unidade obrigatória da idade provável da lavoura: **meses**. O valor deve vir do campo fenológico validado em meses (`probable_crop_age_months` no dashboard ou `probable_crop_age.months` no relatório desktop); não converter dias para meses por divisão fixa. Sem esse valor mensal validado e SAR atual, exibir “Indisponível”.
- Estado fitossanitário aparente aceita apenas **Bom / Médio / Ruim** e exige validação e SAR atual. É um indicador remoto inespecífico; não rotular praga, doença ou deficiência.
- Produtividade provável converte para sacas/ha com base explícita de 60 kg quando esse for o padrão documentado para a cultura (soja, milho, café em grão, arroz em casca, feijão, sorgo e trigo); cana-de-açúcar, citros e demais culturas sem padrão de saca adequado ficam em t/ha. Mostrar a base da conversão. A fonte IBGE registra equivalências em sacas de 60 kg para soja/café/feijão/arroz; a CONAB informa unidades de 60 kg para sorgo; usar padrão regional diferente só com fonte local explicitada.
- Previsão só exibe produtividade provável e seu intervalo coerente sob status `previsao_validada`. Produção provável usa a área da cultura dentro do polígono, mostra total (t) e, quando padronizado, equivalente em sacas. Incluir intervalo total propagado pela incerteza por hectare, condicionado à área fixa; explicitar que incerteza da área/classificação não está propagada se não quantificada. Estimativa pontual sem intervalo/calibração não aparece como previsão.
- O dashboard HTML `dual_executive_dashboard.py` aplica os mesmos gates e separa a aba agrícola do carbono nativo. Contrato dos campos e proveniência está descrito em `docs/ROTAS_EVIDENCIA_SAR_PAM_CULTURAS_E_PREVISAO.md`.

Os testes do painel verificam rótulos, idade expressa em meses, abstenção, não divulgação de previsão pontual não calibrada, conversão de unidades, produção total pela área de cultura, separação do painel de carbono e rejeição de valores inválidos. A suíte direcionada final passou em **35 testes**; `git diff --check` e compilação sintática dos módulos alterados passaram. A UI não cria modelos nem valida dados; continua mostrando indisponibilidade enquanto o pipeline não fornecer evidência real elegível. O workflow Windows deve ser confirmado após esta alteração; builds anteriores não validam o commit atual.
