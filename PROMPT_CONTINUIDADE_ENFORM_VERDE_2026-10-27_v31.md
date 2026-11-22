# PROMPT DE CONTINUIDADE — ENFORM VERDE
Atualizado em 27/10/2026 — v29: checkpoint executável de identificação e auditoria de acesso SAR

## Contexto e objetivo
Retomar o desenvolvimento real do Enform Verde no repositório claudiodcandrade-lgtm/Enform-Verde.exe, branch `feature/agricultural-identification-native-carbon`, PR #50. Preservar funcionalidades já operacionais e concluir rotas efetivas, com testes e incerteza cientificamente defensável. Não confundir catálogos de artigos, regras isoladas ou testes unitários com modelos orbitais treinados e integrados. Não anunciar EXE sem artefato Windows verificado.

## Requisitos permanentes
- Aplicativo Windows autônomo; importar SHP, GPKG, GeoJSON, KML e KMZ; mapa raster IBGE offline com municípios, estados, hidrografia e infraestrutura; zoom, scroll, polígono semitransparente, área em hectares; separadores brasileiros.
- Cobrir Amazônia, Cerrado, Mata Atlântica, Caatinga e Pantanal; classificar fitofisionomias por evidências confiáveis, usando IBGE `legenda_1` e MapBiomas quando apropriado, sempre com fonte.
- Prioridade absoluta para AGB derivada de SAR: ESA BIOMASS P, ALOS/PALSAR L, SAR X, Sentinel-1 C, e ESA CCI Biomass v7 como fallback documentado. Não apresentar estatística regional como estimativa SAR pixel a pixel. Altura RH98 de GTDX não entra diretamente em modelo H100 sem conversão validada.
- Estimar, quando houver suporte científico, AGB, raízes, necromassa, serrapilheira e carbono do solo; priorizar inventários microrregionais, IFN/SFB, SINAFLOR e Embrapa Solos. Informar limites quando faltar estimativa defensável. Preservar tC e tCO2e e não confundir OPEX, CAPEX ou outros parâmetros financeiros com carbono.
- Identificar lavoura (milho, soja, sorgo, café, cana, arroz, feijão, citros e algodão) somente com classificadores validados; caso contrário 'áreas cultivadas'. Preservar 'pastagem' quando segura. MapBiomas silvicultura classe 9 indica floresta plantada, não prova eucalipto ou pinus. Só distinguir gêneros com modelo e validação específicos.
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


## Atualização de conclusão — integração SAR×PAM×clima (24/10/2026)

A incompatibilidade entre a montagem do painel e o treinador foi corrigida no código. `build_pam_sar_panel(pam_path, sar_path, weather_path, output_path=None)` agora exige uma tabela climática explícita, valida chaves únicas e proveniência, requer bloco espacial e status de atualidade fenológica calibrada e emite `municipality_code` (código N9), `spatial_block`, flags de validação SAR, variáveis SAR e clima no esquema aceito por `crop_yield_modeling.py`. Linhas sem aprovação independente ou sem correspondência de clima são descartadas; rótulos MapBiomas não viram verdade de validação. Marcadores de aprovação recebidos são requisitos de contrato e ainda precisam de auditoria documental independente.

Verificação desta alteração: 17 testes focados em rotas de evidência, unidades e painel executivo passaram; `git diff --check` e `py_compile` passaram. O workflow Windows iniciado para o commit anterior permanece em andamento.

**Estado de conclusão:** conclusão técnica local das rotas e integração de painel/modelo; conclusão científica e liberação de previsão continuam pendentes. Não foram baixados rótulos independentes YieldSAT nem produzido painel real PAM×SAR×clima, calibração de atualidade por cultura/fase ou backtest espaço-temporal. Consequentemente não há correlação validada nem previsão liberada. O painel executivo deve continuar mostrando “Bloqueada”/“Indisponível” até todos esses requisitos serem satisfeitos com dados auditados.


## ADENDO URGENTE v4 — operação remota e altura SAR na fenologia e previsão (24/10/2026)

### Restrição de operação: sem dados de campo da AOI
A aplicação e a inferência devem funcionar remotamente, sem exigir coleta, upload ou acesso a dados de campo do usuário ou da AOI analisada. Obter por rotas remotas as cenas Sentinel-1/Sentinel-2/Landsat, meteorologia e previsões, relevo, máscaras públicas de culturas, estatísticas oficiais e referências científicas/datasets abertos. Registrar fonte, licença, data, versão, cobertura espacial, resolução e latência. Usar rótulos públicos de produtividade em sua escala original (município/microrregião/estado); jamais convertê-los em verdade de talhão ou pixel. Uma referência de campo publicada ou dataset aberto pode apoiar desenvolvimento e validação, mas não constitui requisito operacional do usuário nem autoriza extrapolação para qualquer AOI. Se uma fonte externa indispensável não puder ser obtida por rota remota, indicar exatamente a lacuna e executar as rotas alternativas; não simular observações.

A ausência de medidas locais não impede a extração remota de um produto SAR, mas limita a afirmação científica: altura absoluta só pode ser publicada se o algoritmo de recuperação tiver validação independente aplicável à cultura, região, fase, sensor e processamento. Uma altura de dossel obtida por produto remoto sem essa validação deve aparecer como proxy estrutural experimental, com unidade e incerteza explícitas, nunca como altura observada ou como predição validada. Se não houver produto defensável, registrar “altura SAR não disponível/validada neste domínio” e manter o preditor desligado.

### Evidência fenológica: valores de referência, não limites universais
Use as publicações abaixo para estruturar curvas e janelas de observação; não transforme médias de um ensaio em limiares de classificação universais. Cultivar, hábito de crescimento, época de semeadura, densidade, irrigação, água, fertilidade, poda/soqueira e ambiente alteram altura e calendário. Sempre harmonizar a definição de altura (solo ao ápice, ápice do colmo, panícula, altura de dossel SAR), estádio e relógio (DAE/DAS/DAP/DAC/graus-dia).

| Cultura | Parâmetro fenológico/altura observado na literatura | Interpretação para o modelo remoto |
|---|---|---|
| Soja | Em ensaios multi-localidade do RS, altura do ápice da haste foi medida nos estádios R1 e R8; o crescimento depois de R1 variou com hábito determinado/indeterminado, grupo de maturidade, data e local. A literatura brasileira reporta faixa ampla de altura madura, com dependência ambiental e varietal. | Priorizar trajetória de altura e incremento R1→R8, estádio/época e grupo de maturidade, sem uma altura-alvo fixa. Altura sozinha não revela idade em meses. [Bragantia, 2016](https://www.scielo.br/j/brag/a/pqqrvD6LgJbBcWKhBcJdsfk/?lang=en); [RCA, Teresina](https://www.scielo.br/j/rca/a/QtfP9W4BbRkrTz5F4WRj5sc/?lang=pt) |
| Milho | No estudo brasileiro de desenvolvimento inicial, o estádio III começa aproximadamente aos 40 dias após semeadura e inaugura rápido crescimento contínuo; isso descreve fase, não uma altura universal. O retrieval Sentinel-1 publicado fora do Brasil mostrou sensibilidade à altura durante parte do ciclo e degradação conforme fechamento/arquitetura do dossel. | Associar série temporal, estádio vegetativo/reprodutivo, sazonalidade e clima. Não transportar coeficientes europeus. Comparar retrieval com altura independente in-domain antes de incorporar altura em metros. [RBEAA, 2014](https://www.scielo.br/j/rbeaa/a/5bP4fnyPtSfJTHddQ9dktXs/); [Agriculture, 2022](https://www.mdpi.com/2077-0472/12/6/800) |
| Feijão comum | Curva brasileira: crescimento em altura relativamente lento até ~20 DAE, fase intermediária com maiores taxas e fase final com desaceleração. Ensaios citados observaram máximas entre 55–140 cm e 30–88 DAE, uma amplitude que evidencia diferenças de ambiente/manejo, não um intervalo normativo. | Usar forma sigmoide/fases, dias térmicos e variáveis de cultivo; detectar compatibilidade de fase, não cultivar por altura isolada. Evidência SAR de altura específica precisa ser adquirida antes do uso operacional. [Ciência e Agrotecnologia](https://www.scielo.br/j/cagro/a/CQHVMXJYc98nDGsgCL7DnkM/?lang=pt) |
| Sorgo granífero | Estudo brasileiro semiárido mediu altura do solo ao ápice da panícula aos 30, 45, 60, 75 e 90 DAS; comparou híbridos e estresse hídrico pré/pós-floração. | Estádios e déficit hídrico precisam condicionar a trajetória. Não generalizar de sorgo granífero para sorgo biomassa/forrageiro. SAR de C-band pode saturar/ser ambíguo; requer validação por tipo de sorgo. [Pesquisa Agropecuária Tropical, 2026](https://www.scielo.br/j/pat/a/Jh8xJhh5j6psvv7QrhRnDcs/?lang=en) |
| Arroz | Embrapa descreve avaliação da altura no enchimento/maturação pela distância solo–extremidade da panícula primária; descritores incluem classes curtas <65 cm, médias 66–85 cm, longas >86 cm (protocolo de caracterização, não padrão de produtividade). Há pesquisa Sentinel-1/Sentinel-2 em outros países; a melhor associação encontrada dependeu de fusão SAR+óptico e teve RMSE 14,14 cm. | Diferenciar arroz irrigado/terras altas, cultivar, água e estádio; produtos SAR devem tratar inundação e estrutura do dossel. Os números de retrieval estrangeiro não validam altura no Brasil. [Embrapa, descritores](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/216465/1/doc226.pdf); [estudo Sentinel 1/2, Bulgária/Türkiye](https://impact.yildiz.edu.tr/articles/exploring-sentinel-1-and-sentinel-2-time-series-sensitivity-to-rice-height-28065) |
| Cana-de-açúcar | Curvas brasileiras logística/Gompertz com 17 medições até 360 DAP/DAC; pico de taxa de crescimento de altura entre 129–146 DAP em cana-planta e 79–90 DAC em soqueira. Outras curvas observaram maior crescimento do colmo entre 120–240 dias. | Modelar cana-planta e cada soqueira separadamente; usar tempo desde plantio/corte, água e fase. Altura final não distingue idade/ciclo sem histórico de corte; fonte SAR disponível é candidata e exige validação brasileira. [Ciência Rural, 2020](https://www.scielo.br/j/cr/a/NKmXRCDsN5cNfxWgQ8khdpj/?lang=en); [RBEAA, 2009](https://www.scielo.br/j/rbeaa/a/gYvmhTCZgV9JWVMNZG8pwVn/?lang=pt) |
| Café | Evidência brasileira após poda monitora altura, diâmetro de copa e ramos; crescimento vegetativo oscila sazonalmente e a poda altera a arquitetura. Manejo “safra zero” limita deliberadamente a altura. | Café é perene: altura/copa estima estrutura e resposta à poda, não idade cronológica. A evidência encontrada é sobretudo óptica, não recuperação direta por Sentinel-1; manter altura SAR desligada até haver retrieval independente para sistema/região. [Revista Ceres, 2024](https://www.scielo.br/j/rceres/a/8pBfQv3Ws8jFZrTJDSrLTYx/?format=html&lang=en); [Coffee Science](https://coffeescience.ufla.br/index.php/Coffeescience/article/view/269) |
| Citros | Evidência consultada indica grande variação de altura de árvores maduras e efeito de variedade, porta-enxerto e sistema de manejo; não foi identificada curva brasileira robusta altura–idade–fenologia nem retrieval de altura por SAR pronto para uso. | Tratar como cultura perene de copa; altura e idade são variáveis distintas. Não inferir idade ou condição fitossanitária a partir de altura sem série temporal e validação por combinação copa/porta-enxerto/região. |

A tabela é uma síntese direcionada da literatura identificada, não uma alegação de revisão sistemática exaustiva. Para ampliar a busca, indexar publicações e dados por cultura, cultivar, região, estádio, desenho experimental, definição de altura, unidade temporal, sensor, algoritmo, métrica, validação independente e licença. Marcar separadamente altura de planta medida em campo, altura estrutural remota e altura inferida por modelo.

### Evidência de altura por SAR e regra de uso
- Sentinel-1 C-band não mede diretamente altura; retroespalhamento, coerência, fase e índices respondem à estrutura, umidade, orientação de fileiras, biomassa, solo e água. Não chamar VV/VH, RVI ou índice SAR de “altura média” sem retrieval explícito.
- A literatura dá prova de viabilidade localizada para milho e arroz; há estudo de cana com Sentinel-1A e trabalhos multimodais com soja. São rotas candidatas, não calibrações brasileiras do Enform Verde. Em particular, fusionar Sentinel-2 não transforma um modelo SAR+óptico em medida SAR-only.
- Implementar aquisição remota e cubo espaço-temporal Sentinel-1 com filtros orbitais, máscara de água/nuvem quando houver fusão, normalização radiométrica, incidência, georreferenciamento, correção de terreno e metadados de aquisição. Priorizar a cena mais recente disponível; reportar data/idade do dado e lacunas. Calibrar a janela de atualidade por cultura/fase e densidade real de cenas; não inventar um limiar universal de frescor.
- Agregar somente dentro de máscara de cultura/polígono aprovada, após remover bordas, solo descoberto, água, estradas e pixels mistos. Relatar fração válida, área, percentis e distribuição, não somente uma média que esconda heterogeneidade.
- Para candidatar altura: recuperar média/mediana e incerteza (m), taxa temporal (m/dia ou cm/dia), diferença para curva fenológica condicionada à cultura/região/fase, e número/idade das cenas. Propagar o erro de altura até produtividade. Usar altura como feature de estrutura e indicador auxiliar de fase/vigor; “idade provável (meses)” vem da curva/histórico de emergência ou plantio e do estádio inferido com incerteza, nunca de uma conversão universal metros→meses. Vigor exige tendência/resíduo relativo à curva, clima e etapa fenológica; altura estática não equivale a vigor ou estado fitossanitário.
- A altura somente entra no modelo matemático de produtividade para as combinações cultura × região × fase em que tenha: produto SAR de recuperação identificável, código/versão e hash do modelo, documentação e licença, referência externa reproduzível, teste independente e espacialmente bloqueado, bias/RMSE, cobertura de intervalo, faixa de suporte e datas compatíveis. Exigir teste de ablação que prove ganho incremental sobre clima + histórico + SAR fenológico; se não melhorar desempenho/cobertura no holdout, excluir a altura.
- Usar para previsão a altura da cena disponível no instante de emissão, não cenas futuras. Reexecutar auditoria de leakage temporal para cada feature. Se a altura não satisfizer a validação, os caminhos continuam remotos mas a feature deve ficar experimental/desligada e a previsão segue os gates científicos existentes.

### Treinamento e validação inteiramente remotos
1. Automatizar obtenção e versionamento de dados públicos. Alvos PAM/IBGE, ACYD ou outros dados abertos são agregados e servem apenas à previsão na mesma escala geográfica; dados de talhão abertos como YieldSAT podem ser usados para testar somente classes/culturas/anos/licenças cobertos. Evitar contar duas vezes o mesmo IBGE/PAM quando datasets derivados reapresentam seus dados.
2. Juntar as séries Sentinel-1 ao polígono/território de origem do rótulo, agregando a resolução dos alvos. Não atribuir o rendimento municipal a todos os pixels como verdade independente. Dividir por blocos espaciais e safras; manter holdout final intocado e validar por cultura e região.
3. Para a altura, preferir publicações/datasets com retrieval e avaliação independentes, produtos públicos compatíveis ou informação estrutural satelital independente. Se fonte remota não oferecer rótulo de altura apropriado, não fingir que rendimento municipal valida altura. A investigação pode continuar e o resto da cadeia remota pode operar, mas a altura absoluta não será habilitada.
4. Comparar modelos: (a) clima + histórico; (b) clima + histórico + identidade/vigor/fenologia SAR; (c) (b) + altura SAR validada; e, quando disponível, (d) óptico/fusão. Selecionar em CV espacial; testar no último período e em regiões retidas. Fazer ablação por cultura, horizonte e grupo de fase.
5. Aplicar intervalos calibrados em dados de calibração que não treinaram o modelo e avaliar cobertura/largura em holdout espacial-temporal. Quantificar transferência, variabilidade de rótulos agregados, incerteza meteorológica, erro de máscara/área, erro do retrieval SAR e incerteza de produtividade separadamente. Detectar extrapolação e abster-se quando fora do suporte.
6. A interface continua remota e não pede dados de campo. Se dados públicos não permitem um estimador validado para a AOI/escala solicitada, mostrar “previsão indisponível neste domínio” e a causa concreta. Não produzir valor numérico de aparência precisa.

### Painel executivo e trilha de auditoria
Manter painel executivo separado e simples; não misturar explicações técnicas. Quando e somente quando o modelo passar os gates, apresentar: cultura e área cultivada válida do polígono; idade provável em meses e intervalo; estado fitossanitário aparente “bom”, “médio” ou “ruim” como classificação não diagnóstica de sinal remoto; produtividade provável em sacas/ha quando essa for a unidade usual da cultura, caso contrário t/ha; produção provável para a área cultivada estimada dentro do polígono e intervalo; data/hora da emissão e última aquisição SAR; cobertura válida e status de domínio. Sem calibração, exibir indisponibilidade motivada para cada item.

A aba “Auditoria técnica” apresenta somente detalhes verificáveis: cena Sentinel-1/UTC e idade; fontes e versões; máscara de cultura e cobertura; versão/hash/licença do retrieval de altura; definição de altura e estágio; curva de referência; split espaço-temporal; quantidade de regiões/safras independentes; RMSE, MAE, viés, cobertura e largura dos intervalos; ablações com/sem altura; limitações e extrapolação. Estado fitossanitário não diagnostica doença, praga ou causa de estresse.

### Estado científico ao fechar este adendo
A literatura brasileira fornece curvas e relações fenológicas observacionais úteis para soja, feijão, sorgo, arroz, milho e cana; em café destaca efeitos de poda e sazonalidade; para citros faltam referências de curva altura–fase/idade suficientemente sólidas nesta busca. Literatura estrangeira demonstra que altura por SAR pode ser recuperada em condições específicas, mas isso não é validação brasileira. Logo, o desenvolvimento remoto pode prosseguir integralmente sem dados da AOI, mas o uso operacional de altura em metros, idade provável derivada dela e previsões de safra continuam condicionados aos gates de validação. Não declarar a pendência científica resolvida apenas porque a rota de processamento ou a feature foi implementada.


## ADENDO DE EXECUÇÃO v5 — correções, dados recuperados e estado de validação (24/10/2026)

### Correções implementadas
- A rota municipal PAM × SAR admite colunas `sar_height_*` somente com contrato aprovado de validação independente: status `INDEPENDENT_DOMAIN_VALIDATION_APPROVED`, indicador de validação, URL do produto e da referência, hash SHA-256, cultura e fase compatíveis. O painel/modelo preserva os metadados da altura.
- O modelo exige separadamente os grupos SAR de identidade de cultura, vigor/fenologia, anomalia inespecífica de estresse e clima; altura não substitui vigor ou fenologia.
- Quando houver preditor de altura validado, comparar o modelo completo com a mesma família sem altura em holdout espaço-temporal independente. O treino é recusado se o limite inferior do bootstrap por blocos espaciais não demonstrar ganho positivo.
- Atualizados testes sintéticos para atender ao contrato completo de altura sem reduzir os gates de produção.
- Recuperada em `data/pam_microregion_yield_2015_2024.csv.gz` a série PAM pública completa (133.920 registros; oito produtos, 2015–2024). O arquivo local foi verificado por contagem, unicidade das chaves e checksum SHA-256 `fe35d64f3c170cb04420bce9fa2065d2074d39cc59b3c1a07537df9d29d2db7e`; o metadado explica que o checksum foi recalculado após recompressão determinística do membro gzip do artefato de CI.

### Verificação
`python -m unittest discover -s tests`: 223 testes passaram. A suíte não foi encontrada pelo comando padrão `python -m unittest discover` porque os testes estão no diretório `tests`; usar sempre `-s tests`. O ambiente exigiu instalar `requests` e `geopandas` já listados em `requirements_desktop.txt`.

### Estado de ciência e produto — não confundir testes de contrato com previsão validada
O conjunto PAM é um alvo público agregado, não rótulo de talhão. Ainda não existe no projeto um painel histórico alinhado e auditado com imagens SAR Sentinel-1 para as mesmas unidades e datas de origem, máscara independente de cultura aprovada e fonte climática completa para treinar os modelos por cultura. Também não existe retrieval de altura SAR validado no domínio brasileiro, nem artefato de previsão com validação espacial-temporal. Portanto:
- a recuperação remota do PAM e as rotas de busca Sentinel-1 estão operacionais como caminhos de aquisição; isso ainda não constitui correlação SAR–produtividade;
- idade, vigor, altura absoluta, estado fitossanitário aparente e previsão numérica não devem ser apresentados como validados sem seus respectivos produtos/dados e testes;
- nenhuma previsão de safra está liberada, e não foi gerado EXE novo nesta etapa;
- não exigir dados de campo do usuário ou da AOI na operação. Buscar, baixar e versionar automaticamente bases públicas; se a validação externa remota necessária não existir, abster-se com motivo explícito;
- a etapa seguinte é materializar e reconciliar o painel SAR/clima/PAM por cultura, unidade geográfica, fase e origem temporal; validar máscara, altura e atualidade SAR; executar ablação e holdouts em blocos; gerar artefato de modelo e só então integrar previsão ao painel executivo e criar o build Windows.

Este adendo substitui qualquer interpretação anterior de que a presença do código, um checksum PAM, ensaios unitários ou literatura de altura SAR resolvam a pendência de validação científica da previsão.


## ADENDO DE STATUS v6 — publicação na branch e CI (24/10/2026)

- Alterações de código, testes, documentação, dataset PAM e este prompt foram publicados na branch `feature/agricultural-identification-native-carbon`, commit `61080b03b0d8ac6673d37066d8e3d907bf927d6a`, PR #50.
- Validação local: `python -m unittest discover -s tests` passou com 223 testes após instalar as dependências já declaradas (`requests`, `geopandas`).
- GitHub Actions para o commit estão pendentes/em execução: `Build Enform Verde Windows`, run `40133758235` (in progress); `Dashboard dual - tests`, run `40133754201` (in progress) e `40133758283` (queued). O build Windows verde anterior, run `40132252516`, corresponde ao commit anterior `0d7b0a981a02e68f2f573322fcd038090f359097` e não certifica este commit.
- Não anunciar novo EXE até o run `40133758235` concluir com sucesso e o artefato deste SHA ser verificado.
- As pendências científicas permanecem explícitas: série Sentinel-1 histórica alinhada à PAM/clima, máscara independente de cultura, calibração de frescor por cultura/fase e validação brasileira independente da recuperação de altura SAR. Não existe modelo de previsão treinado/liberado nesta revisão.

---

# ADENDO v7 — rotas alternativas científicas para destravar monitoramento e previsão

Atualizado em 24/10/2026


## Contexto e objetivo
Retomar o desenvolvimento real do Enform Verde no repositório `claudiodcandrade-lgtm/Enform-Verde.exe`, branch `feature/agricultural-identification-native-carbon`, PR #50. Preservar as decisões e requisitos do prompt v6 e executar as rotas alternativas deste adendo. O objetivo é remover dependências desnecessárias de dados de campo na AOI e permitir entregas úteis na escala em que os dados sustentam inferência. Não declarar resolvida uma pendência científica só por adicionar uma rota de software, adquirir cenas ou passar testes de contrato.

## Regra de produto: previsão exclusivamente em nível de propriedade
O objetivo final do Enform Verde é prever produtividade e produção da lavoura dentro da propriedade/polígono analisado. Não apresentar rendimento municipal, microrregional ou estadual como previsão da propriedade.

- **Modelo final de propriedade:** exige rendimento georreferenciado de lavouras/propriedades externas para treinamento e validação, série SAR e clima alinhadas por cultura/safra/data de emissão, máscara independente de cultura e teste espacial e temporal em propriedades totalmente retidas. Não se exige dado de campo fornecido pelo usuário para a propriedade analisada; os dados de treino e validação podem vir de outras propriedades, bases abertas e estudos licenciados.
- **PAM/SIDRA e estatísticas regionais:** servem como baseline contextual, covariáveis agregadas, análise de consistência ou pré-treinamento/regularização explicitamente documentados. Não são verdade de campo e não autorizam desagregação de rendimento para a propriedade. Uma alocação espacial por sensoriamento remoto baseada somente no total municipal continua sendo estimativa exploratória, nunca previsão validada do polígono.
- **Produção provável da propriedade:** produtividade validada × hectares de cultura dentro do polígono, com incerteza da produtividade e da área propagada. Sem máscara e área cultivada validadas, exibir “Indisponível”; não usar a área total do imóvel como lavoura presumida.
- **Fallback sem rótulo georreferenciado elegível:** fornecer monitoramento SAR fenológico/descritivo e baseline regional identificado como contexto, mas manter “previsão de safra da propriedade” bloqueada. Não converter o baseline contextual em valor para o painel de safra.

## Rotas alternativas por pendência

### A. Não há dados de campo fornecidos para a AOI
- Usar PAM/IBGE, SIDRA, ACYD e estatísticas oficiais para alvos administrativos; alinhar código territorial, cultura, unidade e ano. Treinar primeiro o produto regional e identificá-lo como tal.
- Para soja/milho, avaliar YieldSAT como fonte de referência de talhão (polígonos e dados de colheita brasileiros publicados para parte do período). Primeiro confirmar acesso aos arquivos, campos efetivamente brasileiros, definição/unidade do rendimento, geometria, licença e independência entre treino/teste. O benchmark publicado usa dados multissensores Sentinel‑2, clima, solo/topografia; extrair Sentinel‑1 retrospectivo separadamente. Nenhuma métrica publicada em Sentinel‑2 valida por si só o classificador ou o preditor SAR.
- Para demais culturas, procurar em paralelo parcelas georreferenciadas públicas, experimentos e dados de colhedoras/cooperativas abertos e licenciados. Rótulos interpretados, mapas oficiais, mapas de área e pseudorrótulos servem a funções distintas; não os chamar de rendimento de campo.
- Se não houver rótulo externo suficiente: oferecer monitoramento SAR descritivo e previsão regional. Não pedir dados de campo da AOI como condição do fluxo do usuário e não fabricar referência local.

### B. Falta uma máscara independente de cultura
Executar, nesta ordem, as rotas de evidência, mantendo origem e papel de cada fonte:

1. **Campos com rendimento georreferenciado** (YieldSAT e datasets equivalentes): fonte de treino/teste apenas após auditoria de licença, integridade, qualidade e separação por campo/fazenda/ano.
2. **Dados de referência harmonizados** (por exemplo, WorldCereal/INPE‑LEM/JECAM quando houver amostras brasileiras adequadas): usar as amostras de referência independentes para avaliação; excluir qualquer amostra ou fonte reaproveitada no treinamento do mesmo experimento.
3. **Mapas de cultura oficiais/secundários** (Conab, MapBiomas e outros): usar para estratificação, prior espacial ou concordância, salvo documentação de amostras primárias e independência que autorize outro papel. Nunca treinar e testar no mesmo rótulo/mapa.
4. **Supervisão fraca com PAM/SIDRA**: admitir aprendizado por proporções/agregados como etapa exploratória para composição regional. PAM não fornece localização de pixels/campos; portanto não mede acurácia da máscara. Comparar área inferida com estatísticas agregadas é verificação de coerência, não validação pixel a pixel.
5. **Sem referência independente adequada**: classificar apenas “área cultivada” ou “cultura não determinada”, abster-se de cultura específica e não agregar SAR seletivamente como se a máscara fosse verdadeira.

A máscara só entra no treinamento/associação SAR–rendimento com referência espacial independente, avaliação por fazenda/região e safra retidas, matriz de erro por classe, cobertura e domínio de transferência documentados. Para estimar área, usar desenho amostral e correção de erro; área bruta classificada não equivale automaticamente à área corrigida.

### C. Não há Sentinel‑1 histórico/recentemente acessível em uma fonte
Criar um adaptador comum com tentativas ordenadas e registro de falha:

1. Microsoft Planetary Computer STAC/RTC para busca e leitura em janela de COG; testar VV/VH, CRS, escala, nodata, órbita, ângulo, cobertura e leitura Rasterio real. SAS assinado é temporário, obtido em runtime e nunca persistido.
2. Copernicus Data Space (CDSE): localizar Sentinel‑1 GRD/SAFE via STAC/OData, autenticar OAuth2, baixar apenas a cena necessária e processar SNAP/GDAL com parâmetros/versionamento registrados.
3. ASF DAAC/HyP3: alternativa para pesquisa e RTC on-demand, com autenticação Earthdata e manifesto reproduzível.
4. Google Earth Engine: alternativa para protótipo/checagem quando a autenticação e os termos permitirem; registrar coleção e pré-processamento. Resultados não são intercambiáveis sem harmonização.

Tentar a próxima fonte se a anterior falhar; não simular aquisições nem preencher lacunas com médias climatológicas ou vizinhas. O status deve distinguir data de aquisição, publicação e ingestão. Se nenhuma rota produzir pixels auditáveis e atuais, manter histórico como histórico, marcar cobertura recente insuficiente e suprimir inferência que dependa de frescor.

### D. Não existe limite calibrado de atualidade SAR por cultura/fase
- Não adotar uma janela global arbitrária (por exemplo, 12 dias) como limiar agronômico.
- Estimar primeiro a distribuição observada de lacunas de revisita por cultura, região, fase, órbita e fonte. Isso descreve disponibilidade, não tolerância fenológica.
- Em validação retida, degradar deliberadamente a idade da cena e medir deterioração de classificação/fase, vigor, anomalia e previsão por data de corte. Pré-registrar regra de aceitação e selecionar limite por risco/erro admissível; calcular incerteza em blocos espaciais e safras.
- Até a calibração, publicar idade da última aquisição e percentual de área coberta, mas status `atualidade_nao_calibrada`; não liberar idade provável, estado fitossanitário aparente ou previsão como indicadores atuais validados.

### E. Altura de planta SAR não foi validada no Brasil
- Não inferir metros de altura diretamente de VV/VH nem converter retroespalhamento em “meses de idade” com equação universal. Altura, arquitetura, cultivar, densidade, umidade e fechamento do dossel alteram a relação.
- Rota alternativa imediata: usar assinaturas temporais SAR (VV, VH, VH/VV, amplitude, coerência/textura apenas onde tecnicamente adequada) como características de fase/estrutura aprendidas, sem denominá-las altura. Combinar com calendário agrícola local, clima e óptico válido, sinalizando falhas de cobertura/nuvem.
- Manter altura como módulo opcional. Ativá-la por cultura × região × fase somente após produto de recuperação identificável, referência externa de altura, split espacial independente, viés/RMSE/intervalo e ablação que mostre ganho no rendimento. Estatística PAM não valida altura.
- “Idade provável” em meses só pode ser exibida se houver modelo independente que estime tempo desde plantio/estabelecimento e validação compatível. Sem data de plantio observada, o resultado é idade fenológica/proxy e deve ser nomeado como tal; se só houver fase ampla, mostrar fase, não meses.

### F. PAM não resolve previsão de talhão ou falta uma cultura/ano
- PAM (IBGE, tabela 5457) é o rótulo oficial de área, quantidade e rendimento médio em escala municipal; usá-la na escala administrativa correspondente. Preservar diferenças entre rendimento, produção e área colhida, e harmonizar códigos e mudanças territoriais.
- Para anos/culturas não cobertos ou baixa qualidade: buscar SIDRA/PAM atualizada, Conab para produtos e escopos em que a metodologia seja comparável, ou bases abertas de parcela; não preencher com uma cultura substituta nem imputar como observado.
- Quando só existir série regional curta, comparar modelo com persistência/mediana histórica e clima simples, usar regularização/hierarquia entre regiões como candidato, e reportar abstenção se o holdout não sustentar intervalo. Pooling/hierarquia melhora compartilhamento de informação, mas não cria evidência independente nem autoriza inferência de talhão.

### G. N pequeno, poucos blocos ou validação impossível
- Não tratar “50 previsões” ou “5 blocos” como leis universais. Definir tamanho/quantidade de grupos por precisão de cobertura e poder para detectar ganho, considerando correlação intrabloco e variação entre safras; documentar protocolo antes de abrir o teste final.
- Revisar no código os gates fixos atuais (incluindo 50 observações e 5 blocos) e substituí-los apenas quando houver critério de suficiência amostral pré-especificado e reproduzível baseado em precisão/poder e dependência por grupo. Até lá, os gates atuais são limites conservadores de abstinência; jamais reduzi-los apenas para fazer o modelo passar.
- Quando a amostra efetiva for pequena, reduzir escopo geográfico/temporal ou agregar ao nível estadual/regional, ampliar anos/fonte compatíveis e recalibrar. Se ainda insuficiente, publicar baseline descritivo ou bloquear previsão; não compensar pseudorreplicação por pixels.
- A validação deve separar tuning e avaliação final no espaço e no tempo. Relatar MAE, RMSE, viés, skill frente aos baselines e intervalos preditivos; avaliar cobertura e largura no holdout por cultura, fase, safra e bloco. Conformalização não garante cobertura sob mudança de distribuição; indicar evidência empírica e limites de transferência.

## Modelo matemático: comparar alternativas e manter interpretação
Treinar por cultura e por data/fase de emissão, comparando no mesmo holdout:

- **B0 Persistência**: último rendimento oficial disponível ou média histórica, conforme o cenário de emissão.
- **B1 Clima + histórico**: variáveis meteorológicas que estariam de fato disponíveis na data de corte e rendimento defasado oficial.
- **M1 SAR fenológico + clima + histórico**: features SAR retrospectivas alinhadas, máscara elegível e clima disponível até o corte.
- **M2 Híbrido de cultura**: modelo de crescimento/agrometeorológico (por exemplo, SAFY‑WB para milho ou ORYZA para arroz) assimilando SAR apenas quando parâmetros, dados e domínio forem reproduzíveis e testáveis.
- **M3 Estrutural com altura**: M1 + altura recuperada independentemente; candidato sujeito a teste de ablação. Se não provar ganho fora da amostra, rejeitar M3 e manter M1/B1.

Selecionar modelos em validação interna. O teste final deve ser espacial e temporal, grupos inteiros retidos, sem vazamento de climatologia futura, colheita futura, fronteiras de campo vizinhas ou imagens após `forecast_origin_utc`. Declarar contribuição SAR somente se superar o melhor baseline no teste final com incerteza por blocos compatível com ganho positivo. Correlação bruta, desempenho de treino e teste sintético não são validação.

## Saídas do painel executivo (preservar requisitos prévios)
Painel simples separado da auditoria. Mostrar por AOI e escala:

- **Idade provável da lavoura:** unidade meses, somente com modelo de idade/fase validado e SAR dentro da janela calibrada; caso contrário “Indisponível”. Não converter fase em idade cronológica.
- **Estado fitossanitário aparente:** “Bom”, “Médio” ou “Ruim” somente se indicador remoto inespecífico for validado para cultura/fase e atualidade adequada; não diagnosticar doença/praga. Caso contrário “Indisponível”.
- **Produtividade provável:** `sacas/ha` quando esse for o padrão documentado para a cultura; caso contrário `t/ha`. Exibir intervalo preditivo, data de emissão e escala.
- **Produção provável:** produtividade × hectares de cultura dentro do polígono, não área total presumida. Exibir toneladas e equivalente em sacas de 60 kg quando aplicável; propagar incertezas de rendimento e área.
- Estados visíveis: `Estimativa regional`, `Previsão validada no domínio`, `Bloqueada` ou `Indisponível`, com explicação curta. Auditoria separada contém aquisições UTC, frescor, fontes/licenças, máscara/cobertura, escala, modelo/hash, split, n efetivo, métricas, intervalos e motivo de abstenção.

## Fontes e fundamentos a usar (rever licença e atualização antes de integrar)
- IBGE/PAM, estatísticas municipais de área plantada/colhida, produção e rendimento: https://sidra.ibge.gov.br/pesquisa/pam/tabelas/ ; tabela 5457.
- YieldSAT, benchmark multimodal de rendimento de campo, com países que incluem Brasil; auditar acesso/licença e shift: https://arxiv.org/abs/2604.00940 ; https://yieldsat.github.io/.
- WorldCereal/reference data e dados harmonizados: https://esa-worldcereal.org/en/reference-data ; https://zenodo.org/records/7593734.
- Sentinel‑1 no Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/docs/ ; CDSE: https://documentation.dataspace.copernicus.eu/APIs/OData.html ; ASF HyP3: https://hyp3-docs.asf.alaska.edu/using/authentication/ ; Earth Engine: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD.
- SAFY‑WB com assimilação Sentinel‑1 para milho é referência metodológica estudada na França, não coeficiente brasileiro: https://doi.org/10.1109/JSTARS.2018.2878502.
- Validação de modelos ecológicos/espaciais: Roberts et al. 2017, bloqueio em dados dependentes: https://doi.org/10.1111/ecog.02881.

## Plano de execução e critério para considerar pendência resolvida
1. Auditar licença e arquivos de YieldSAT; verificar se geometria e rendimento brasileiros podem ser usados no software. Se não puderem, aplicar rota regional PAM e buscar alternativa aberta com licença compatível.
2. Completar leitura real de VV/VH COG em janela via MPC. Se falhar ou não cobrir anos/campos, executar fallback CDSE e depois ASF/HyP3; comparar amostras sobrepostas e documentar diferenças de processamento.
3. Construir primeiro benchmark soja/milho: rótulos de campo independentes, Sentinel‑1 retrospectivo, clima com corte temporal e teste por fazenda/região e safra. Não alegar SAR até M1 superar B1 no teste reservado.
4. Paralelamente, harmonizar painel PAM × clima × série SAR por município e safra e desenvolver modelo regional. Se a máscara independente falhar, não chamar resultado de SAR por cultura; avançar B0/B1 como benchmark regional separado.
5. Calibrar frescor por cultura/região/fase e propor calibração própria de altura. Até aprovação, manter idade/fitossanidade/previsão dependentes bloqueadas.
6. Expandir cultura a cultura somente com dados e validação; uma cultura aprovada não aprova outra.
7. Rodar verificações automatizadas locais e CI apenas quando solicitado ou como parte obrigatória da mudança de código; atualizar resultados reais, branch/HEAD e artefatos. Não alegar build Windows ou previsão liberada sem evidência observada.

**Critério de conclusão:** uma pendência é “resolvida” apenas para a cultura, escala, área, fase e período que tenham dados auditáveis, modelo executável, validação independente espacial/temporal e incerteza adequada. As demais ficam explicitamente bloqueadas. A falta de dados do usuário na AOI nunca deve ser disfarçada por pseudo-rótulo, correlação ecológica ou métrica de treino.

## Snapshot desta revisão
Este documento cria rotas alternativas e critérios de escolha; não declara que aquisição, treinamento, validação brasileira de altura, calibração de frescor, máscara independente, previsão regional SAR ou previsão de talhão já tenham sido concluídos. No workspace consultado, o prompt v6 existe e há alterações locais não commitadas em módulos agrícolas e testes. Confirmar estado do branch, CI e artefatos antes de usar o prompt para alegar entrega do software.

## ADENDO DE IMPLEMENTAÇÃO — planejador de evidência
No código local, `plan_evidence_routes()` agora separa papéis de evidência, exige a escala regional ou de lavoura ao planejar previsão, não considera uma fonte aprovada apenas por estar disponível e mantém `release_ready=False`. PAM/SIDRA só pode ser desfecho regional; não serve para validar máscara SAR, altura ou rendimento de talhão. Dataset climático com rendimento derivado de IBGE/PAM não é holdout independente contra o próprio PAM. O novo `plan_sar_source_routes()` ordena MPC, CDSE, ASF/HyP3 e Earth Engine sem afirmar que aquisição ou leitura de pixels ocorreu. O documento complementar `docs/ALTERNATIVAS_PENDENCIAS_SAR_PRODUTIVIDADE_2026-10-24.md` explica essa separação.

Essa mudança corrige o contrato do planejador e torna explícita a alternativa regional. Não completa o experimento: não há ainda valores Sentinel‑1 pareados com PAM/clima, máscara independente aprovada, calibração de atualidade nem previsão SAR validada. A alteração local não foi testada nesta etapa; antes de integrar/mesclar, executar a suíte e CI Windows, confirmar licenças/datasets e registrar os resultados. Não reduzir gates fixos de amostra sem justificativa estatística prévia.


---

# ADENDO v8 — esclarecimento vinculante da escala do produto

O usuário confirmou que o objetivo é prever safra em **nível de propriedade**. Este requisito prevalece sobre qualquer seção anterior que tenha descrito previsão regional como produto final.

1. A saída final deve estimar produtividade da lavoura e produção total dentro do polígono da propriedade, condicionadas à cultura e à área efetivamente cultivada validamente delimitadas.
2. PAM/SIDRA, ACYD e estatísticas municipais/microrregionais podem servir a baselines contextuais, covariáveis agregadas, regularização/pré-treinamento com limites explícitos e análise de coerência. Não são rótulos de propriedade e não podem ser desagregados para emitir a previsão final do imóvel.
3. O treino e a validação não dependem de dados de campo fornecidos pelo usuário para a AOI. Devem usar rendimentos georreferenciados de outras propriedades/campos, bases abertas/licenciadas e estudos externos auditados. Holdout deve separar propriedades/fazendas inteiras e safras, e avaliar transferência ao domínio da propriedade-alvo.
4. Se não houver rótulos georreferenciados de rendimento adequados, o software pode mostrar monitoramento SAR e baseline regional claramente contextual; a previsão de safra da propriedade permanece bloqueada. Downscaling ecológico de médias regionais não conta como previsão de propriedade validada.
5. A máscara de cultura e área produtiva precisam ser independentes e validadas. Produção provável = produtividade provável × área da cultura no polígono; propagar incertezas dos dois termos. Nunca usar a área total do imóvel como área agrícola presumida.

## Código alinhado ao requisito
- `agricultural_evidence_routes.py`: `plan_evidence_routes(task="yield_forecast")` exige escala `property`; `regional_context` é somente benchmark e recebe bloqueio explícito. PAM não tem papel de rótulo de rendimento de campo. Fontes georreferenciadas só se tornam elegíveis após disponibilidade e aprovação explícita de independência/licença/domínio.
- `crop_yield_modeling.py`: o artefato baseado em dados administrativos declara `target_scale=administrative_region` e `product_role=regional_context_baseline_only`. `forecast_crop_yield()` recusa usá-lo para emitir previsão de propriedade. Esse treinador não substitui o futuro modelo property-level.
- `docs/ALTERNATIVAS_PENDENCIAS_SAR_PRODUTIVIDADE_2026-10-24.md`: registra a interpretação científica e operacional.

## Estado de conclusão
A correção de escopo e o bloqueio contra uso indevido de PAM estão implementados localmente, ainda sem testes/CI nesta revisão. A previsão de safra em nível de propriedade **não está validada nem operacional**: continuam pendentes a aquisição/licença de dados independentes de rendimento georreferenciado, extração e alinhamento real de Sentinel‑1 por campo, máscara de cultura/área validada, calibração de atualidade SAR por cultura/fase, integração climática com corte temporal, validação espacial-temporal por propriedade e intervalo preditivo calibrado. Manter o painel em “Bloqueada” até concluir esses itens.


---

# ADENDO v9 — evidência, dados de campo externos e plano de execução property-level

## Candidatos de dados encontrados e seus limites
- **YieldSAT (CVPR 2026):** a página do projeto documenta 551 campos brasileiros entre 2017–2024: milho (118), soja (293) e trigo (140), com medições de rendimento de colhedora, imagens Sentinel‑2, clima, solo e topografia. O acesso do dataset é solicitado via formulário no site; a página consultada não publica uma licença comercial aberta. Tratar como candidato, auditar termos e obter os arquivos por rota autorizada antes de treinar ou distribuir pesos. A própria fonte descreve forte mudança entre regiões e anos; CV padrão não basta. Fonte: https://yieldsat.github.io/ ; https://arxiv.org/abs/2604.00940.
- **Sorgo no Brasil:** Cunha et al., *Engenharia Agrícola* 45 (2025; online 2026), analisam monitor de produtividade e Sentinel‑1/2 em duas safras de sorgo (2021, 2023) e uma de aveia (2022). O ganho do SAR aparece em certas comparações contra um índice óptico isolado, mas não quando quatro índices ópticos são combinados. Os dados são fornecidos pelo autor correspondente mediante solicitação. O artigo embasa ablação por cultura, mas não é um pacote de dados pronto nem demonstra transferência geral: https://doi.org/10.1590/1809-4430-Eng.Agric.v45nespe220250062/2025.

## Decisão operacional
1. O alvo final continua sendo produtividade e produção **por propriedade**. Rendimento PAM/SIDRA/ACYD administrativo pode auxiliar contexto, baseline e regularização; nunca é rendimento observado de cada imóvel e não pode ser redistribuído como previsão property-level.
2. Para soja/milho, a primeira rota de treino/teste é solicitar/usar YieldSAT apenas depois de confirmar acesso, licença, cobertura e arquivos de rótulos/áreas do Brasil. Extrair Sentinel‑1 retrospectivo e clima com `as_of` real. Fazer separação por propriedade/fazenda inteira, região e safra; recalibrar para cada domínio.
3. Para sorgo, avaliar a extração de Sentinel‑1 do estudo brasileiro ou obter dados independentes autorizados. Comparar clima+histórico, óptico+clima e SAR+óptico+clima com as mesmas propriedades/safras retidas. Liberar SAR somente se demonstrar ganho incremental fora da amostra. Para trigo, arroz, feijão, café, cana e citros, manter rota específica de busca/validação, sem transferir pesos de outra cultura.
4. Rendimento georreferenciado externo é permitido; dados de campo da propriedade-alvo não são requisito operacional. Se os dados externos não estiverem acessíveis/licenciados ou não cobrirem a região/tecnologia-alvo, emitir monitoramento remoto e manter a previsão da propriedade bloqueada. Não usar downscaling de PAM como substituto.

## Situação real do código e da ciência
O treinador existente em `crop_yield_modeling.py` usa rótulos administrativos; seu artefato agora é marcado como `administrative_region`/`regional_context_baseline_only`, e `forecast_crop_yield()` recusa seu uso para previsão de propriedade. O planejador em `agricultural_evidence_routes.py` exige `scale="property"` para previsão de safra, e só trata fonte como referência independente após aprovação explícita. Essas são barreiras corretivas, não um modelo property-level pronto.

Para concluir cientificamente o produto, ainda são necessários: (a) adquirir dados externos de rendimento por propriedade sob termos compatíveis; (b) obter polígonos, rótulos e qualidade por safra; (c) extrair séries SAR auditáveis por esses campos; (d) validar máscara de cultura, atualidade SAR por cultura/fase e área no polígono; (e) treinar e avaliar por fazenda/região/safra retidas, comparar baselines, verificar contribuição incremental do SAR e calibrar intervalo; (f) demonstrar transferência à região do imóvel-alvo. Até então, painel: “Previsão da propriedade — Bloqueada”. Nenhuma métrica publicada em fonte externa é métrica validada do Enform Verde.

A atualização do planejador/modelo e desta documentação ainda precisa passar por suíte automatizada e CI antes de integração/mesclagem.


## Nova rota global de evidência de rendimento por propriedade — atualização 25/10/2026

### Objetivo científico e escala
A pendência é obter rótulos independentes de rendimento observados em propriedades/campos para treinar e validar, remotamente, o modelo por propriedade. Não se exige dado de campo coletado pelo usuário na propriedade alvo: podem ser usados rendimentos de terceiros, com acesso e licença compatíveis. Porém, PAM, dados municipais/estaduais, mapas modelados e pseudorrótulos nunca contam como verdade observada daquela propriedade. Usá-los apenas como contexto, pré-treinamento ou baseline, explicitando a escala. A previsão executiva por propriedade só será liberada após teste externo espaço-temporal com propriedades inteiras retidas e calibração de incerteza.

### Rotas globais em ordem operacional

1. **Prioridade 1 — YieldSAT, Brasil e Cone Sul.** Verificar primeiro a coleção e seus termos de acesso. O conjunto publica rendimento de colhedora georreferenciado a 10 m e dados associados para 551 campos brasileiros (118 milho, 293 soja, 140 trigo), safras 2017–2024; no total inclui 2.173 campos em Brasil, Argentina, Uruguai e Alemanha. Pode fornecer o primeiro painel de rendimento por propriedade. O acesso é feito por formulário, e a página consultada não declara licença comercial irrestrita: registrar termos, finalidade permitida, retenção e redistribuição antes de baixar ou incorporar. Sem autorização clara, usar apenas para avaliação acadêmica permitida e manter o artefato fora de distribuição comercial. Extrair Sentinel‑1 independentemente para cada campo/safra; a coleção documenta Sentinel‑2, clima, solo e relevo. Separar campos, proprietários/regiões e anos no teste; observar que os autores reportam forte perda sob mudança de região e safra. Fonte: https://yieldsat.github.io/ .

2. **Prioridade 2 — YIPEEO / ESA Open Science Catalogue.** Solicitar/acessar a coleção de rendimento de campo, verificando por metadado se cada registro tem geometria, cultura, ano, unidade, método de pesagem, umidade e proveniência. O catálogo identifica os dados de rendimento de campo como protegidos; dados e produtos de observação associados podem ter níveis de acesso diferentes. Fazer auditoria de direitos antes de uso comercial e de qualquer exportação. É uma rota para validação externa europeia e adaptação de domínio, não evidência brasileira por si só. Fonte: https://opensciencedata.esa.int/projects/yipeeo/collection .

3. **Prioridade 3 — USDA BARC Gridded Yield Data Archive.** Baixar dados públicos de mais de 40 campos de produção em Beltsville, Maryland; grade interpolada a partir de monitores de rendimento, mais de um ano e múltiplas culturas, temporalmente 2014–2021; acesso sem restrição e licença declarada como domínio público dos EUA. Ideal para reproduzir pipeline, treinar representação estrutural e avaliar diferenças dentro do campo. Como o produto é interpolado por krigagem e tem cobertura geográfica concentrada, rastrear o mapa até medições e não tratá-lo como milhões de amostras independentes. Fonte: https://agdatacommons.nal.usda.gov/articles/dataset/USDA_Beltsville_Agricultural_Research_Center_BARC_Gridded_Yield_Data_Archive_version_1/28950746 .

4. **Rota de transferência — SICKLE, arroz na Índia.** Usar rótulos de produtividade por parcela junto às séries Sentinel‑1/2 e Landsat, datas fenológicas e variedade, para teste independente de arquitetura multimodal e resposta do arroz. São 351 amostras de arroz em 145 parcelas, dentro de 2.370 amostras de 388 parcelas. Confirmar licença e versão efetivamente baixada; transferir parâmetros para o Brasil somente com adaptação e holdout brasileiro, sem assumir equivalência de cultivar, manejo ou calendário. Fonte: https://sites.google.com/iiitd.ac.in/sickle/home .

5. **Rota de transferência / pré-treino — GROW‑Africa v2.** Disponibiliza 535.844 observações georreferenciadas para 25 culturas em 1960–2023, mas mistura cortes de parcela, pesquisas domiciliares e estatísticas regionais. Classificar linha a linha a escala, precisão de coordenada, método de rendimento, fonte, ano e licença. Só usar observações verificadas de corte/parcela com incerteza espacial compatível; pontos agregados ou deslocados servem para contexto e pré-treino regional, não para validação a 10 m. Fonte: https://zenodo.org/records/16544448 .

6. **Rota de transferência / corte de rendimento — Lacuna/PULA, Zimbábue.** Mede cortes aleatórios de 8 × 5 m, com peso úmido e seco e localização, útil para testar transferência a pequenos produtores e viés de protocolo. Baixar o GeoJSON/manual, auditar licença, precisão GPS, culturas, amostragem e correspondência temporal de SAR. Não representa automaticamente rendimento total do campo nem valida Brasil. Fonte: https://zenodo.org/records/10060610 .

7. **Rota de transferência por monitor — Yield monitor acadêmico e redes de pesquisa.** Auditar repositórios de universidades, estações experimentais e projetos de agricultura de precisão (por exemplo, KBS LTER e redes LTAR/USDA). Aceitar somente séries por talhão com geometria/grade rastreável, calibração e unidade, safra, cultura e política de uso explícitas. No USDA BARC, há uma rota pública confirmada; outras redes permanecem candidatas até confirmar arquivo e direitos. Não enviar solicitações a autores, instituições ou produtores nem preencher formulários com dados pessoais sem autorização explícita do usuário.

8. **Rotas sem rótulo fino, estritamente auxiliares.** QDANN fornece mapas anuais a 30 m de milho, soja e trigo de inverno nos EUA; o método faz transferência de escala a partir de rótulos de condado e foi validado contra cerca de um milhão de observações campo‑ano de monitores. Usar para benchmarking metodológico e aprendizagem exploratória, nunca como rótulo independente no Brasil; licença CC BY‑NC‑SA 4.0 restringe uso comercial. CY‑Bench/CropNet, Yield Gap Atlas, FAOSTAT, PAM/SIDRA, CONAB, EarthStat/GAEZ/CROPGRIDS e mapas globais de rendimento são agregados, modelados ou dependentes de estatísticas administrativas; usar apenas em baseline, contexto, covariáveis e regularização, mantendo proveniência e evitando vazamento.

### Rota de dados se os conjuntos prioritários forem inacessíveis

- **A. Dados públicos já depositados:** colher primeiro YieldSAT e BARC; depois SICKLE, GROW‑Africa e Lacuna, após auditoria técnica/legal individual.
- **B. Dados de terceiros sob acesso controlado:** manter adaptadores opcionais para YIPEEO, cooperativas, seguradoras, revendas, empresas de agricultura de precisão, usinas, concessionárias e projetos de pesquisa. Solicitação ou compartilhamento externo exige autorização explícita do usuário; nunca presumir direito de acesso ou redistribuição.
- **C. Dados sintéticos/simulados:** usar SAFY‑WB, WOFOST, DSSAT, APSIM, ORYZA ou AquaCrop apenas para pré-treino, desenho de features, priors e testes de consistência física, com parâmetros publicados e cenários locais. Simulação não é rótulo observado, não valida acurácia real e não destrava forecast executivo.
- **D. Aprendizado sem rótulo na propriedade alvo:** usar adaptação de domínio/escala (incluindo QDANN), auto-supervisão e covariáveis espaciais para produzir hipótese espacial experimental. Sem observações independentes de rendimento do domínio alvo ou protocolo de calibração externa representativa, não chamar previsão de validada nem atribuir nível de confiança calibrado.
- **E. Resultado operacional enquanto isso:** disponibilizar série SAR atual, fenologia, área de cultura e indicadores remotos como evidência observacional quando validados; exibir produtividade/produção como “bloqueada” ou “estimativa exploratória sem validação” conforme política de produto. PAM e outros agregados podem aparecer em painel contextual identificado como regional.

### Pipeline de admissibilidade e validação dos rótulos
Para cada fonte, criar registro com DOI/URL, versão/data, entidade responsável, licença/termos e uso comercial, país/região, culturas/safras, identificador de campo, geometria e precisão, unidade e teor de umidade, método/monitor/crop-cut, calibração, densidade de amostras, controle de qualidade, dados ausentes e vínculo às imagens disponíveis. Harmonizar rendimento seco para umidade padrão sem apagar valor original. Diferenciar rendimento total da área colhida e rendimento espacial rasterizado. Remover cabeceiras, linhas de manobra, pausas, mistura de talhões, bordas, valores fora do domínio e pixels não elegíveis; manter trilha das exclusões.

Dividir por fazenda/proprietário e blocos espaciais antes de qualquer ajuste; usar safra(s) inteiras como teste temporal. Impedir vazamento de pixels vizinhos do mesmo talhão, geografia, clima futuro e cenas posteriores à data de emissão. Avaliar por cultura, região, sistema de produção e data de corte com MAE, RMSE, viés, skill contra persistência e baseline clima+histórico, intervalos preditivos (cobertura e largura) e incerteza agrupada por campo/região/safra. Testar calibração fora do domínio. Executar ablação SAR versus óptico, clima, solo, relevo e crescimento; SAR só recebe crédito se acrescentar habilidade no holdout independente. Para rendimento de mapa interpolado/simulado, relatar a origem e não contar pixels como replicações independentes.

### Critério de encerramento da pendência
A busca de alternativas não significa que os rótulos foram obtidos, licenciados, pareados ou validados. Atualizar os estados individualmente: `descoberto`, `acesso_público_confirmado`, `termos_auditados`, `baixado`, `QA_concluído`, `SAR_pareado`, `split_independente`, `validado_no_domínio`. Só encerrar a pendência quando houver pelo menos uma fonte de rendimento observado de propriedade com direitos compatíveis, painel SAR atual e rastreável, validação espaço-temporal externa em propriedades retidas, desempenho e intervalo preditivo aprovados por critério pré-registrado e incerteza calibrada para o domínio de uso. Até lá, previsão de safra por propriedade continua bloqueada como produto validado.

### Fontes-base desta atualização
- YieldSAT, artigo CVPR 2026, dados e documentação: https://yieldsat.github.io/ ; https://arxiv.org/abs/2604.00940
- YIPEEO / ESA Open Science Catalogue: https://opensciencedata.esa.int/projects/yipeeo/collection
- USDA BARC Gridded Yield Archive, v2: https://doi.org/10.15482/USDA.ADC/28950746
- SICKLE (WACV 2024): https://sites.google.com/iiitd.ac.in/sickle/home ; https://arxiv.org/abs/2312.00069
- GROW‑Africa v2: https://doi.org/10.5281/zenodo.16544448
- Lacuna/PULA Zimbabwe: https://doi.org/10.5281/zenodo.10060610
- QDANN (Remote Sensing of Environment, 2024): https://doi.org/10.1016/j.rse.2024.114427 ; mapas e licença: https://gee-community-catalog.org/projects/qdann/


## Plano de contingência enquanto o acesso YieldSAT não é ativado — 25/10/2026

O cadastro YieldSAT do usuário está pendente de ativação. Não bloquear o trabalho técnico esperando esse único conjunto. Ao mesmo tempo, não declarar a pendência de validação científica resolvida: fontes alternativas têm escopos, culturas e direitos diferentes e nenhuma, isoladamente, valida generalização nacional em propriedades.

### Alternativas imediatas identificadas

1. **Soja, Brasil — Zenodo 10.5281/zenodo.13770031 (rota piloto imediata).** O repositório disponibiliza dois CSVs/XLSX com produtividade de soja em kg/ha, coordenadas projetadas X/Y, atributos de solo e condutividade elétrica para duas áreas no Sul do Brasil. O CSV demonstra 95 registros para a área Cachoeira e 50 para Curitibanos. Isso permite iniciar uma prova técnica: recuperar CRS/geometria correta com os metadados/artigo, extrair Sentinel‑1 retrospectivo, avaliar alinhamento e testar modelos e splits espaciais. Limites: apenas duas áreas, dependência espacial forte, época/safra e desenho amostral precisam ser confirmados; metadado Zenodo consultado não expõe licença de dados clara. Manter em `uso_piloto_com_direitos_pendentes`; não distribuir nem empregar em produto comercial até resolver direitos. Uma divisão aleatória de pontos não é validação independente de propriedades. Fonte e arquivos: https://zenodo.org/records/13770031 .

2. **Cana-de-açúcar, Brasil — dataset comercial de SP (rota piloto de pesquisa).** O Data in Brief 2026 e o depósito Hugging Face disponibilizam 2.157 observações temporais associadas a 12 campos em seis fazendas no nordeste paulista, com shapefiles, rendimento real `real_TCH`, datas de plantio/corte/colheita, variedade, ambiente de produção, clima e imagens Sentinel‑2. O card declara `CC-BY-NC-4.0`: pode ser estudado em contexto não comercial nos termos da licença, mas não integrar treino ou produto comercial do Enform sem permissão comercial separada. O número de linhas temporais não é número de campos independentes: a validação deve agrupar por fazenda/campo/safra e o n geográfico independente permanece pequeno. Parear Sentinel‑1 em separado. Fonte: https://doi.org/10.1016/j.dib.2026.112549 ; https://huggingface.co/datasets/lafbarbosa/sugarcane_dataset_northeast_sao_paulo_state_brazil .

3. **Diversas culturas, EUA — USDA BARC (rota técnica aberta).** O arquivo público de rendimento gridded do monitor de colhedora cobre mais de 40 campos de produção em Beltsville, 2014–2021; arquivos anuais baixáveis e licença Public Domain estão listados no catálogo oficial. Usar para verificar leitura dos arquivos, QA de mapas de rendimento, extração de séries Sentinel‑1 e avaliação técnica em domínio temperado. O grid é interpolado por krigagem e não equivale a novos talhões independentes. Não usar como validação brasileira ou como evidência de desempenho tropical. Fonte: https://catalog.data.gov/dataset/usda-beltsville-agricultural-research-center-barc-gridded-yield-data-archive-version-1 .

4. **Diversas culturas, Inglaterra — CYCleSS (baseline aberto, escala grosseira).** Dados CC0 derivados de rendimento de precisão para 934 campos, alinhados com satélite, meteorologia e solo em quadrículas de 10 km. Pode apoiar desenvolvimento de baselines e transferência a escala grosseira, mas a anonimização e a grade de 10 km impedem tratá-lo como rótulo da propriedade ou como validação de campo. Fonte: https://doi.org/10.6084/m9.figshare.27225807 .

5. **Arroz, Índia — SICKLE (transferência fenológica e de método).** 351 amostras de arroz em 145 parcelas apresentam produtividade e datas de cultivo junto a séries multi-sensor (Sentinel‑1, Sentinel‑2 e Landsat), 2018–2021. Confirmar a licença/termos e documentação do arquivo antes do uso. Aplicar como teste de método em arroz, não como evidência brasileira; exige holdout local brasileiro antes de liberar previsão no Brasil. Fonte: https://sites.google.com/iiitd.ac.in/sickle/home .

6. **Milho e múltiplas culturas, África — GROW‑Africa v2 e Lacuna/PULA.** GROW‑Africa v2 reúne 535.844 registros para 25 culturas, 1960–2023, misturando crop-cuts, levantamentos de agricultores e estatísticas subnacionais. Classificar e filtrar cada registro pela escala e precisão da coordenada. Lacuna/PULA fornece crop-cuts de 8×5 m, pesos úmido/seco e localização no Zimbábue. São potenciais dados de transferência; verificar licença, escala, GPS, cultura, protocolo e representatividade. Não preencher lacuna brasileira nem validar propriedade no Brasil. Fontes: https://doi.org/10.5281/zenodo.16544448 ; https://doi.org/10.5281/zenodo.10060610 .

7. **Dados sob acesso controlado — ESA YIPEEO / ScaleAgData / redes de colhedoras.** YIPEEO tem coleção de rendimento por campo protegida; ScaleAgData e redes de monitoramento de rendimento estão desenvolvendo acesso a dados de colhedoras sujeito a privacidade. Manter adaptadores, mas tratar como oportunidade de parceria/acesso futuro; não declarar dado aberto, enviar solicitação, aceitar termos ou compartilhar dados do usuário sem autorização específica. Fontes: https://opensciencedata.esa.int/projects/yipeeo/collection ; https://scaleagdata.eu/en/ri-labs/yield-monitoring .

8. **YieldSAT continua candidato, porém com condição de uso.** A conta do usuário ainda aguarda ativação. A plataforma RAISE classifica o acesso aos registros subjacentes como gerenciado e informa que a licença de dados permite acesso para fins científicos devido ao risco de reidentificação por geolocalização. Ao receber acesso, primeiro auditar termos para estudo acadêmico, pesquisa interna e uso comercial do produto; não presumir que cadastro ou download autoriza treinar/distribuir modelos comerciais. O conjunto é excepcionalmente relevante (551 campos brasileiros com rendimento de colhedora a 10 m), mas a adequação legal ao Enform depende dos termos concedidos. Fonte: https://raise4science.eu/practice/yieldsat/ ; https://yieldsat.github.io/ .

### Implementação em duas trilhas, sem confundir prontidão técnica e validade científica

**Trilha A — começar agora, com fontes disponíveis:** (i) obter metadados e arquivos públicos do Zenodo/Brasil-soja e iniciar QA do CRS, rendimentos, datas e independência; (ii) executar validação de pipeline com BARC (Public Domain); (iii) se permitido por escopo não comercial, usar o dataset de cana para estudo interno, auditoria da licença e pareamento S1; (iv) preparar SICKLE/GROW/Lacuna como testes externos por domínio após licença e QA; (v) acessar Sentinel‑1 dinâmico do OPERA RTC‑S1/ASF ou CDSE, pareando apenas cenas anteriores à data de previsão, com órbita/polarização/unidade/correção e cobertura registradas.

**Trilha B — manter gate de produto:** bloquear produtividade/produção provável validada por propriedade até existir rótulo elegível com licença compatível e holdout externo representativo para cada cultura/domínio. Não agregar estatística municipal para fingir observação de parcela; não usar mapa modelado como referência independente; não contar pixels, observações temporais repetidas ou pontos próximos como réplicas independentes. Para as culturas sem conjunto externo por talhão, manter monitoramento fenológico remoto e painel “previsão bloqueada/experimental”, com escala e motivo legíveis.

### Primeira execução recomendada para a alternativa brasileira de soja

- Recuperar metadados, CRS EPSG, safra, método de medição, suporte espacial do rendimento e licença do Zenodo 13770031; verificar se as coordenadas são centróides de células ou pontos de coleta, e identificar grupos de campo/área.
- Se direitos e metadados permitirem pesquisa, extrair VV/VH e séries temporais de Sentinel‑1 por grupo espacial, remover bordas/ruído e garantir cenas anteriores à previsão. Salvar um manifesto de cena–pixel–rótulo com hashes e data de acesso.
- Executar apenas um teste de integração e um piloto exploratório com leave-spatial-block-out. Com duas áreas, relatar n de áreas=2; não estimar uma distribuição confiável de generalização entre fazendas, nem calibrar intervalos nacionais.
- Abrir acesso a outras safras/fazendas por repositórios institucionais ou parceiros somente depois de permissão explícita de contato/compartilhamento pelo usuário. Não pedir que o usuário forneça observações da propriedade-alvo.
- Cruzar todos os resultados com baseline simples disponível antes da colheita; avaliar MAE, RMSE, viés, ganho frente ao baseline e intervalos. Se só houver n efetivo insuficiente, preservar abstenção e indicar a etapa que precisa de amostra externa adicional.

### Estado correto da pendência após esta busca

- Alternativa nacional de soja **encontrada** e arquivos tabulares de rótulo **publicamente visíveis**; licença/CRS/datas/independência **não completamente auditados**, então não é ainda conjunto aprovado para treino comercial nem validação de produção.
- Dataset brasileiro de cana **encontrado** com rótulos por campo, mas **não comercial** conforme licença declarada, e número de fazendas pequeno.
- USDA BARC **aberto e tecnicamente utilizável**, mas geograficamente não representativo do Brasil.
- CYCleSS **aberto**, porém com suporte de 10 km; não é propriedade.
- YieldSAT aguardando ativação/termos; não presumir autorização comercial.
- A validação de previsão por propriedade continua **pendente** até existir teste externo representativo e independente para cada cultura/domínio. Esta pesquisa resolve a dependência exclusiva de YieldSAT para iniciar QA e pilotos, mas não declara um forecast por propriedade validado.


## Rota Embrapa: fontes observadas por talhão, situação de acesso — 25/10/2026

A busca em Alice/Infoteca Embrapa identificou estudos brasileiros com rendimento de colhedora por talhão/campo e dados georreferenciados, mas não confirmou um pacote bruto de grande escala, aberto e licenciado para uso comercial. Registrar estas opções separadamente de dados já baixáveis:

1. **Algodão comercial no Cerrado (Vaz et al., 2025; Embrapa/Amaggi/IMAmt).** Estudo usa monitor de colhedora em 30 talhões comerciais de MT, seis safras 2019–2024 e 76 combinações talhão-safra. O artigo declara: “para verificar a possibilidade de usar dados e scripts, contate o autor correspondente”; agradece à Amaggi por fornecer os dados. Logo, a publicação é aberta, mas os rótulos brutos não estão depositados abertamente. É candidata forte para solicitar acesso controlado e validar algodão no Brasil, se o usuário autorizar contato, a Amaggi/Embrapa conceder acesso e os termos autorizarem o produto. O teste reportado no artigo é evidência do estudo, não validação independente do Enform. Fonte: https://doi.org/10.3390/agriengineering7110390 ; registro Embrapa Alice https://www.alice.cnptia.embrapa.br/alice/handle/doc/1186887 .

2. **Soja em ~5.000 talhões (Embrapa Arroz e Feijão, 2024).** Resumo em anais descreve produtividade, genótipo, solo, período de semeadura e clima em cerca de 5.000 talhões no Centro-Oeste, Sudeste e Sul. O item aberto na Alice é o resumo de uma página, não o conjunto de dados. Ele não documenta geometrias/identificadores espaciais disponíveis, safras exatas, licença, método de rendimento ou acesso aos registros. Tratar como contato institucional potencial, não como dado aberto nem como painel SAR-ready até obter documentação e permissão. Fonte: https://www.alice.cnptia.embrapa.br/alice/handle/doc/1175212 .

3. **Experimento de soja de longa duração em Dourados/MS (Embrapa Agropecuária Oeste).** Notícia institucional relata 28 safras 1998–2026 e mais de 4.300 pontos georreferenciados, com produtividade e atributos de manejo/solo. São repetições no tempo de um experimento/site e não 4.300 propriedades independentes. A página/notícia localizada não oferece os dados brutos ou a geometria para pareamento; solicitar ficha de dados, coordenadas/grade, nível de acesso, licença e limites de uso. Pode auxiliar fenologia/rendimento de soja e validação local/regional, não representa sozinho diversidade nacional. Fonte: https://www.embrapa.br/web/agropecuaria-oeste/busca-de-noticias/-/noticia/148182311/produtividade-da-soja-cresce-111-a-cada-avanco-nos-niveis-de-manejo-do-solo .

4. **Agritec/AgroAPI e SATVeg (Embrapa Agricultura Digital).** Agritec fornece previsão/modelo de produtividade para arroz, feijão, milho, soja e trigo construída em base municipal e monitoramento agrometeorológico. SATVeg fornece séries históricas EVI/NDVI MODIS e ciclos agrícolas, com resolução temporal de 16 dias e espacial de 250 m. São fontes úteis de baseline, calendário ou série óptica contextual, mas escala/observação não validam rendimento de uma propriedade; separar licença, credencial e custo da API antes de uso operacional. Fonte metodológica: https://doi.org/10.1016/j.satech.2023.100247 e documentação https://www.portal.agroapi.cnptia.embrapa.br/api-docs/agritec/v2 .

### Regra para avançar com Embrapa
A biblioteca Embrapa/Alice oferece artigos, resumos, métodos e APIs; presença de um estudo no repositório não implica que a base subjacente esteja pública. Para qualquer conjunto solicitado, exigir confirmação de: acesso aos arquivos brutos, licença de pesquisa e uso comercial, identificador e geometria/cobertura do talhão, safra e cultura, unidade/umidade e medição de rendimento, processamento do monitor, precisão espacial, número de fazendas independentes e regras de publicação/redistribuição. Não enviar mensagens nem compartilhar dados do usuário com autores, empresas ou unidades da Embrapa sem autorização explícita.

**Estado:** Embrapa amplia rotas promissoras de aquisição brasileira (algodão e soja), mas nenhum desses registros examinados remove imediatamente o bloqueio: para algodão/5.000 talhões/Dourados, os rótulos brutos e termos não estão abertamente comprovados; Agritec é municipal. Se autorizado, buscar acesso institucional a bases por talhão e combinar com o piloto aberto de soja Zenodo, BARC técnico e demais fontes elegíveis. O forecast da propriedade continua bloqueado até teste externo compatível.


## Recomendação incorporada: algodão na identificação e previsão por propriedade — v13

Incluir **algodão (Gossypium hirsutum)** como a nona cultura monitorada do Enform Verde. Usar o identificador canônico interno `algodao` e aliases de interface `algodão`, `cotton` e `Gossypium hirsutum`. Resolver qualquer código numérico de PAM/SIDRA consultando a tabela oficial vigente; não inventar nem reutilizar código de outra cultura. Manter algodão como produto separado das oito culturas já existentes, sem alterar retroativamente as séries históricas nem confundir algodão em caroço com pluma.

### Identificação da cultura
- Criar uma rota específica de identificação de algodão, por safra e região, com máscara de cultura e classificador próprios. Não classificar como algodão apenas por ser área agrícola, por proximidade de outras lavouras ou por classe genérica do MapBiomas. Não declarar que MapBiomas contém uma classe específica de algodão sem verificar a legenda oficial da coleção usada.
- A saída deve distinguir `algodão identificado`, `área cultivada sem cultura confirmada` e `sem evidência suficiente`. Calibrar limiar e abstenção em validação independente por fazenda, safra e região. Registrar fonte dos rótulos, datas, sensor, versão do classificador, métricas por classe e limitações de transferência.
- O estudo brasileiro de algodão citado abaixo combina monitor de colhedora e Sentinel-2; ele é candidato para desenho e aquisição de rótulos, não prova de um classificador SAR nem de desempenho do Enform. Avaliar Sentinel-1 separadamente e medir o ganho incremental de SAR contra baselines ópticos, climáticos e históricos.

### Previsão e unidades no painel
- Implementar uma rota de modelo específica para algodão, em nível de propriedade, com extração dentro do polígono agrícola de algodão validado e datas de corte explícitas. Separar treino e teste por fazenda/talhão e safra; não dividir observações repetidas do mesmo talhão entre treino e teste.
- Exibir **produtividade provável em t/ha** e **produção provável em toneladas**, calculada como produtividade provável multiplicada pela área efetivamente identificada como algodão dentro do polígono. Não usar sacas/ha para algodão.
- Exibir idade provável da lavoura em meses somente quando a data de plantio ou estimativa fenológica tiver suporte; caso contrário, informar indisponibilidade. Estado fitossanitário aparente (`bom`, `médio`, `ruim`) é indicador remoto incerto, não diagnóstico, e exige método validado e confiança legível. Manter essas saídas separadas da trilha de auditoria.
- Registrar produto medido e base de massa (algodão em caroço ou pluma), umidade e conversão quando aplicável. Nunca converter produtividade de caroço em pluma sem fator e fonte explicitamente validados.

### Dados brasileiros e gate de validade
O estudo Vaz et al. (2025) usa 30 talhões comerciais em Mato Grosso, seis safras (2019–2024) e 76 combinações talhão-safra. O artigo informa que dados e scripts podem ser solicitados ao autor correspondente e agradece à Amaggi pelo fornecimento dos dados. Portanto, tratar como **rota de aquisição controlada**, sem presumir acesso aberto, direito de treino ou licença comercial. O desempenho publicado pertence ao estudo e não valida o Enform. Referências: https://doi.org/10.3390/agriengineering7110390 e https://www.alice.cnptia.embrapa.br/alice/handle/doc/1186887 .

Antes de treinar ou ativar o forecast, obter os arquivos brutos, licença compatível com o uso pretendido, geometrias/identificadores dos talhões, datas de plantio e colheita, unidade e base de massa do rendimento, metadados do monitor e documentação de qualidade. Se autorizado, comparar pelo menos: baseline histórico/climático, modelo óptico reproduzível baseado no estudo, SAR Sentinel-1 e fusão SAR+óptico. Usar validação bloqueada por fazenda e safra, métricas MAE/RMSE/viés, calibração de intervalos, análise de domínio e ablação de sensores. As 76 combinações talhão-safra não equivalem a 76 fazendas independentes.

Até esses requisitos e o gate comum do registro de modelos serem satisfeitos: a cultura pode aparecer como **candidata/experimental** quando a identificação tiver evidência suficiente; produtividade e produção devem aparecer como **previsão bloqueada — dados e validação independentes pendentes**, sem números apresentados como validados. Não criar pesos, rótulos, resultados, acesso ou autorização fictícios.


## Fechamento da etapa: algodão, série PAM e situação das pendências — v14

### Alterações implementadas no repositório
- O catálogo de culturas foi ampliado para nove itens, incluindo algodão, nas políticas de diagnóstico e no registro fail-closed de classificadores. A classe no registro não significa que haja pesos ou modelo treinado.
- A rota brasileira de dados de algodão do estudo Embrapa/Amaggi foi registrada como acesso controlado. Exigir autorização, licença compatível, geometrias e metadados antes do treino; não contatar autores nem compartilhar dados do usuário sem autorização. Fonte: https://doi.org/10.3390/agriengineering7110390 .
- O materializador SIDRA foi atualizado e executado com categoria PAM 5457/782/40099, **Algodão herbáceo (em caroço)**, para variáveis 112, 214 e 216, anos 2015–2024, nível N9. A resposta é verificada pelo nome da categoria antes de gravar. O CSV contém agora 150.660 registros em nove produtos; algodão tem 16.740 registros (558 microrregiões × 10 safras × 3 variáveis). SHA-256: `efd07439b4470825fcfca62172e615706ad5e74125dae154e42c0c4fbc97b850`. A série é regional; jamais tratá-la como rótulo de talhão ou validação de previsão da propriedade. Fonte oficial da série: https://apisidra.ibge.gov.br/values/t/5457/n9/all/v/112,214,216/p/2015-2024/c782/40099 .
- No painel, algodão deve usar **t/ha** e produção em **toneladas**, especificando algodão em caroço. Não inferir pluma nem aplicar sacas de 60 kg.
- A literatura de Kaplan et al. (2023) demonstra um caminho candidato de altura/LAI de algodão com Sentinel-1 + Sentinel-2 em Israel, não um modelo SAR isolado nem validação brasileira. Reproduzir como estudo metodológico, com validação brasileira por cultura/fase/região antes de uso: https://doi.org/10.1016/j.agwat.2022.108056 .
- MapBiomas não é rotulado como referência de algodão. Sem máscara independente e classificador aceito, o sistema deve exibir “áreas cultivadas” ou abster-se.

### Pendências com rotas alternativas definidas
1. **Aquisição SAR atual:** iniciar pelo Sentinel-1 RTC público do Microsoft Planetary Computer (busca STAC, assets assinados temporariamente e leitura de raster); usar CDSE OAuth2 ou ASF/HyP3 como alternativas de reprocessamento. Cada cena precisa de timestamp UTC, órbita, polarização, processamento, unidade, cobertura válida e proporção de área extraída. URL assinada é segredo temporário: não persistir em logs/manifests.
2. **Máscara independente de cultura:** para milho/soja, YieldSAT é candidato após acesso e auditoria de licença; não cobre algodão segundo a composição brasileira divulgada. Para algodão, priorizar acesso controlado aos rótulos de talhão Embrapa/Amaggi e buscar outros rótulos georreferenciados autorizados. Mapas e PAM servem como estratos/baselines ou rótulos fracos, nunca como validação independente quando usados no treino.
3. **Associação regional SAR–PAM:** usar `product_key=algodao_caroço × território N9 × ano`; cruzar SAR exclusivamente em pixels da máscara validada, parear clima disponível no corte e comparar lags PAM, clima e clima+SAR com validação bloqueada espacial/temporal. Reportar correlação/ganho e incerteza somente após esse pareamento real.
4. **Previsão por propriedade:** treinar em rótulos de produtividade por talhão/licenciados, com validação por fazenda e safra não vistas, calibração de intervalos e avaliação de transferência. PAM, médias CONAB, mapas e reanálises não substituem rendimento medido de campo. Produção provável exige produtividade validada × hectares de cultura mapeados independentemente.
5. **Altura e fenologia do algodão:** a pesquisa internacional S1+S2 é candidata; medir altura por série e associá-la à idade/vigor apenas após validação no Brasil. Não inferir idade em meses diretamente da altura, nem declarar vigor ou estado fitossanitário a partir de uma cena isolada. Anomalias SAR são inespecíficas.

### Critério de conclusão e estado real
Nesta etapa estão concluídos: inclusão de algodão no catálogo e nas rotas, atualização real da série PAM regional para nove produtos e registro dos candidatos científicos/rotas de aquisição. Permanecem **bloqueadas** a identificação validada de algodão, a correlação SAR–PAM, a altura SAR do algodão no Brasil e a previsão de safra por propriedade, porque ainda faltam máscara/rótulos de talhão independentes e autorizados, calibração da atualidade por cultura/fase e backtest espacial-temporal. A disponibilidade da série PAM resolve o acesso a rendimento regional de algodão, mas não esses gates. Não apresentar números experimentais como previsão validada.


## Atualização de avanço e encerramento da etapa — v15

### Novo benchmark brasileiro para algodão
Foi identificada a publicação de de Siqueira et al. (2024): **281 talhões comerciais** de MT, GO e BA nas safras 2016–2022, divididos em 167 para treino e 114 para teste. O método publicado é regressão linear com índices de vegetação quinzenais MODIS (Terra/Aqua), para algodão em caroço; o resumo relata RMSE aproximado de 0,75 t/ha e R²≈0,70 em janelas entre 90–105 e 135–150 dias após semeadura. A publicação declara que os dados são disponibilizados sob solicitação ao autor correspondente. Referências: https://doi.org/10.3390/agriengineering6020054 ; https://www.alice.cnptia.embrapa.br/handle/doc/1164361 .

Usar essa fonte como o primeiro **baseline brasileiro óptico** para algodão e como oportunidade prioritária de acesso a rótulos georreferenciados. Não chamar o baseline publicado de modelo operacional do Enform; os dados brutos não são download aberto, o conjunto não é SAR e o teste do artigo não é validação do sistema. Depois de acesso autorizado, reproduzir o corte treino/teste e adicionar validação por fazenda e safra. Comparar MODIS/óptico, SAR, clima e SAR+clima no mesmo holdout. Investigar possível sobreposição com os 30 talhões Embrapa/Amaggi de 2019–2024 antes de somar as amostras ou declarar independência.

### Alterações técnicas realizadas
- O catálogo e o registro fail-closed aceitam algodão como nona cultura; aliases de nome são normalizados sem acentos nas rotas de evidência e altura. Nenhum classificador ou modelo é automaticamente aprovado por constar no catálogo.
- O planejador de evidências para algodão mostra as duas rotas brasileiras de rendimento por talhão (MODIS 2016–2022 e Sentinel‑2 2019–2024), ambas com acesso controlado e uso sujeito a licença. A classificação MapBiomas genérica não é promovida a máscara de algodão.
- A série PAM inclui algodão herbáceo em caroço, categoria SIDRA 40099, 2015–2024; nove produtos, 150.660 linhas. Usar como rendimento regional e baseline, nunca como rótulo de propriedade.
- A referência de altura de algodão via S1+S2 de Kaplan et al. (2023) continua candidata internacional; precisa de replicação e validação brasileira. Não inferir idade, vigor ou saúde a partir de altura de uma cena.

### Critério de encerramento e limite atual
Concluídas nesta etapa: inclusão técnica do algodão, ampliação da série regional PAM, rotas de acesso a dois estudos brasileiros por talhão, baseline óptico a reproduzir e registro da literatura de altura SAR multimodal. Ainda bloqueadas: máscara independente de algodão; modelo SAR+clima treinado; associação real SAR–PAM; calibração de frescor por cultura/região/fase; estado fitossanitário remoto validado; e previsão por propriedade com intervalo preditivo calibrado. A próxima execução deve priorizar acesso autorizado aos dados 281 talhões (benchmark) e aos dados Embrapa/Amaggi, sem enviar contato ou compartilhar dado do usuário sem autorização explícita. Se não houver acesso, manter a funcionalidade em modo experimental, com abstenção clara e sem exibir previsão numérica como validada.

Documento técnico atualizado: `docs/FECHAMENTO_PENDENCIAS_SAR_SAFRA_ALGODAO_2026-10-24.md`; inventário de evidências Embrapa: `docs/DADOS_EMBRAPA_RENDIMENTO_TALHAO_2026-10-25.md`.

## Atualização urgente v16 — algodão MapBiomas, fontes públicas e critério de conclusão

Esta seção é a atualização vigente e corrige qualquer formulação anterior que dizia que o MapBiomas não continha uma classe específica de algodão. A página oficial da Coleção 11 confirma **algodão (classe 62, beta)** no produto Uso Agrícola de 1ª Safra, cobrindo 1985–2025, e **algodão de 2ª Safra (classe 62, beta)** no produto complementar, cobrindo 2000–2025. A segunda safra tem GeoTIFF anual público direto, sem necessidade de conta; a URL oficial segue o padrão:

`https://storage.googleapis.com/mapbiomas-public/initiatives/brazil/lulc/collection_11/agriculture_second_crop/agriculture_second_crop-brazil_classification_{year}.tif`

Substitua `{year}` por inteiro entre 2000 e 2025. O asset GEE de 2ª safra é `projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_agriculture_second_crop_v1` e requer conta Earth Engine. O produto de 1ª safra cobre 1985–2025, mas a plataforma informa que o download está temporariamente suspenso; o asset de Cobertura 30m C11 é `projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3`, também via GEE. Preferir o GeoTIFF público direto da 2ª safra quando adequado. Fonte oficial: https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/agricultura/uso-agricola/ e página do produto 2ª safra: https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/agricultura/uso-agricola-2a-safra/ .

### Uso permitido e limitações

- As rotas de treino foram separadas no código: `mapbiomas_c11_first_season` e `mapbiomas_c11_second_season`. Não misturar safra/calendário nem aplicar a legenda de um produto no raster do outro. Conferir versão/ano, alinhamento espacial, CRS e transformação antes de extrair pontos; a URL aberta indica disponibilidade do arquivo, não que o arquivo foi baixado/processado nesta execução.
- Usar os mapas apenas como **pseudorrótulos beta para treinamento ou estratificação exploratória**. Não usar para validar acurácia, escolher limiar e depois reportar o mesmo mapa como verdade, nem para calcular métricas de previsão independente. A página oficial informa validação agregada de grandes classes para produto geral; isso não é validação independente da classe beta algodão do Enform.
- Atributos SAR devem ser da mesma área e janela temporal coerente. Registrar fonte e ano cartográfico, safra, data UTC da cena, sensor, órbita, polarização, unidade, processamento e proporção válida. MapBiomas é mapa anual Landsat, não observação SAR dinâmica nem medida de altura das plantas.
- Para avaliação independente, priorizar dados licenciados de talhões com rendimento por colhedora/registro confiável (estudos brasileiros de algodão mencionados acima, sob acesso controlado), YieldSAT para culturas que cubra e autorize, e novas bases públicas com geometria e rendimento verificáveis. Nenhuma conta será aberta nem contato a pesquisadores enviado automaticamente; isso exigiria credenciais/consentimento e validação humana do acesso/licença.
- Alternativas imediatas para treino: MapBiomas C11 beta 1ª/2ª safra; para referência de rendimento independente: obter autorização para dados Embrapa/Amaggi (30 talhões/76 combinações talhão-safra, Sentinel-2) e o estudo MODIS brasileiro (281 talhões, disponibilidade sob solicitação); para SAR dinâmico: fontes públicas Sentinel-1 RTC/SAR já registradas no inventário de rotas, sem confundir disponibilidade do catálogo com aquisição confirmada. PAM/SIDRA continua apenas baseline regional.

### Atualização do estado de conclusão

Concluída a pendência de **encontrar uma alternativa sem YieldSAT para adquirir mapa de algodão**: existe fonte beta pública por safra, com URL anual de GeoTIFF aberta para 2ª safra e código 62 em 1ª safra via C11. Integradas rotas de temporadas distintas no gerador de pseudorrótulos e nos documentos do projeto. Não afirmar que houve download ou processamento dos rasters MapBiomas nesta tarefa.

Continuam pendentes e não podem ser declaradas concluídas cientificamente: obter rótulos independentes/licenciados de talhão, validar máscara de cultura, calibrar frescor Sentinel-1 por cultura/fase/região, medir altura média por SAR no domínio brasileiro, estabelecer correlação SAR–PAM com amostras reais pareadas, treinar e validar previsão de produtividade por propriedade em holdouts espaciais e temporais e calibrar intervalo preditivo. Por isso, no painel executivo separar apresentação de pesquisa e previsão validada: mostrar “idade provável da lavoura (meses)”, “estado fitossanitário aparente (bom/médio/ruim)”, “produtividade provável” (unidade usual da cultura, algodão em caroço em t/ha) e “produção provável” somente quando cada saída tiver gate próprio aprovado. Caso contrário, exibir indisponível/experimental com motivo, nunca inventar números ou usar classe MapBiomas beta como prova. A produção é produtividade válida multiplicada pela área da cultura confirmada dentro do polígono.

### Implementação desta revisão

A lista `MAPBIOMAS_C11_CROPS` contém algodão classe 62 beta para 1ª safra; `MAPBIOMAS_C11_SECOND_CROP` e `mapbiomas_reference_route()` explicitam produto e janela anual de 2ª safra. Os dois produtos mantêm status pseudorrótulo e não são elegíveis para validação. O registro de rotas, documentação técnica e README foram atualizados. Validar mudanças com revisão estática e `git diff --check`; não declarar que testes automatizados foram executados.

## Atualização de execução v17 — alternativa YieldSAT atualizada e estado de encerramento

A checagem da página oficial do YieldSAT mostrou que os dados estão disponíveis **mediante solicitação** pelo formulário do projeto; isso não equivale a download público irrestrito. A descrição oficial registra 2.173 campos globais e 551 campos brasileiros para 2017–2024: 118 milho, 293 soja e 140 trigo. As medidas de rendimento vêm de monitores de colhedora georreferenciados; as imagens listadas são Sentinel‑2 L2A, mais clima, solo e topografia. O site também publica notebook e tutorial. O usuário já reportou solicitação de acesso submetida, ainda sem ativação. Não presumir que os dados foram entregues, não submeter formulário de novo, nem contatar autores pelo usuário.

### O que esta rota torna executável após liberação

1. Para milho e soja (culturas monitoradas pelo Enform), ingerir arquivos e respectivos metadados/termos; confirmar limites de fazenda, ano/safra, produto de rendimento, unidade, umidade padrão, datas de semeadura/colheita, qualidade do monitor, geometria, CRS, e licença de uso/comercialização. Trigo consta no YieldSAT, mas não deve ser incorporado como cultura do produto sem decisão explícita.
2. Parear, por campo e safra, os rótulos YieldSAT com uma série **real** Sentinel‑1 RTC/GRD até cada data de emissão. A fonte YieldSAT listada é Sentinel‑2, não SAR; extrair VV/VH, razão, órbita e atributos temporais da fonte SAR separadamente. Registrar datas UTC, latência, cobertura válida, processamento e unidades. Separar previsão em cortes fenológicos sem usar informação posterior ao corte.
3. Fazer partições agrupadas por fazenda/campo e safras inteiras; manter holdout espacial por região e temporal por ano. Testar baselines rendimento histórico/clima, óptico, SAR, SAR+clima; medir ganho incremental do SAR com MAE, RMSE, viés, R²/skill, intervalos preditivos calibrados, cobertura e desempenho por domínio. Nunca dividir pixels do mesmo campo entre treino e teste.
4. A própria página do benchmark relata queda de desempenho de 19 pontos percentuais de R² em LOYO e 22 pontos em LORO frente à validação cruzada aleatória CV10. Usar os resultados de CV10 apenas como baseline publicado, nunca como prova de transferência para uma propriedade nova. O domínio brasileiro (regiões, cultivar, sistema produtivo e safras presentes nos arquivos) precisa ser comparado à AOI alvo.
5. Antes de integrar pesos ou afirmar uso comercial, auditar licença e termos do conjunto e das modalidades derivadas. O acesso por formulário não comprova autorização comercial. Se termos não permitirem, limitar a pesquisa autorizada e remover/evitar artefatos derivados conforme contrato.

### Pendências — resultado honesto e critérios de fechamento

- **Rota de rótulos para milho/soja:** identificada e detalhada; pedido YieldSAT do usuário continua aguardando ativação. Não está adquirida nesta sessão. BARC/USDA é alternativa aberta para testar ingestão de monitor de rendimento em domínio norte-americano, não para validar transferência ao Brasil.
- **Máscara independente de cultura:** MapBiomas C11 pode auxiliar como pseudorrótulo beta, mas mascara independente de algodão e demais culturas do Enform ainda requer rótulos/avaliação independente. YieldSAT pode apoiar milho/soja se os dados incluírem geometrias e termos elegíveis; a classificação SAR deve ser separada do treino de produtividade para evitar circularidade.
- **Altura/idade/vigor e estado fitossanitário aparente:** sem conjunto brasileiro de referência independente por cultura/fase, essas saídas seguem “indisponível/não validada”. Altura SAR não determina idade de forma única; o estado é sinal inespecífico, não diagnóstico.
- **Frescor SAR:** estabelecer com backtest por cultura × região × fase e análise de lacunas de revisita; não generalizar limite de dias entre culturas/fases. Cada previsão precisa de séries SAR efetivamente adquiridas antes do corte.
- **Associação SAR–PAM:** PAM/N9 é rendimento agregado regional. Pode fornecer contexto e baseline regional; não gera resposta por propriedade nem valida rótulos de talhão. A correlação só será informada após pareamento real, máscara apropriada e controle espacial/temporal.
- **Previsão de propriedade:** permanece bloqueada para emissão validada até dados de campo de treinamento/teste autorizados, split por propriedade/safra, ganho SAR demonstrado sobre baselines, e intervalo preditivo calibrado. A falta de medição na propriedade analisada é compatível com o desenho: treino/teste pode vir de outras propriedades; a AOI em operação continua remota.

Esta etapa conclui a atualização das rotas de evidência, das salvaguardas do painel e da documentação. Não é cientificamente possível fechar a validade de previsão sem arquivos YieldSAT liberados ou outro conjunto compatível, termos de uso, cenas SAR correspondentes e resultados de holdout. O sistema deve continuar mostrando monitoramento observacional e explicitando bloqueios, sem preencher com números inventados. Fonte oficial: https://yieldsat.github.io/ ; formulário de solicitação no botão Dataset; referência: https://arxiv.org/abs/2604.00940 .


## Atualização científica v18 — CIRAD/JECAM e PAM até 2025 (vigente)

### Resposta sobre bases públicas CIRAD
Foi identificada uma rota CIRAD pública e utilizável para **referência de uso/cultura**, além de estudos e dados agronômicos auxiliares. O registro original CIRAD Dataverse do conjunto harmonizado JECAM foi transferido para o catálogo GeoNetwork da instituição. A publicação revisada por pares descreve observações in situ de escala de talhão em sete países tropicais e reporta licença CC BY; a ficha original indica CC BY 4.0. A ficha corrente registra 31.879 registros, 2013–2022, incluindo sítios brasileiros em São Paulo e Tocantins. URLs: DOI https://doi.org/10.18167/DVN1/P7OLAP ; catálogo corrente https://geonetwork.cirad.fr/geonetwork/srv/fre/catalog.search#/metadata/6855571d-677a-4852-afa8-7d7084ed2de8 . Antes de uso operacional, abrir o anexo migrado, conferir versão, checksum, campos, restrições e licença efetivamente anexada; a localização no catálogo foi confirmada, mas o arquivo não foi baixado nem pareado com Sentinel-1 nesta etapa.

A rota é adequada para treino/avaliação de **classe de cultura e uso da terra**, não para rendimento, saúde fitossanitária ou idade. Os sítios brasileiros cobrem contextos e culturas como soja, milho, cana, culturas de inverno e pomares em São Paulo, e soja/segunda safra de milho, sorgo/milheto e pastagem no Tocantins. As amostras são de oportunidade/estradas, pequenas e não representativas nacionalmente. No Tocantins, algumas labels vêm de resíduos e entrevistas; respeitar SOS/EOS e datas da observação antes do pareamento temporal. Para independência SAR, obter geometrias e datas, parear com cenas Sentinel-1 efetivamente adquiridas e separar sítios/talhões/anos entre treino e validação.

A hipótese do usuário é parcialmente aplicável: assinaturas visuais/temporais de uma mesma cultura na África podem servir para pré-treinamento de representações ou gerar hipóteses. Não presumir transferência de calendário, fenologia ou desempenho para o Brasil, pois cultivar, manejo, irrigação, clima, solo, tamanho de talhão e janelas sazonais diferem. Preferir o subconjunto JECAM brasileiro para adaptação e avaliação local. O conjunto não tem rendimento colhido.

Outras rotas CIRAD pesquisadas: (a) meta-análise de rendimento de conservação agrícola na África subsaariana, 1.071 observações experimentais compiladas de literatura, CC BY 4.0, útil somente como prior/contexto agronômico sem geometria de talhão; (b) dataset experimental 2026 de sorgo/milheto/caupi na África Ocidental, 91 observações e licença CC BY-NC-ND, útil apenas para ciência/parametrização não comercial dentro dos termos; (c) contagens semanais de pragas do algodão no Benin 2018–2023 são restritas por autorização, não públicas, e não validam saúde por satélite. Nenhuma fecha validação de rendimento por propriedade no Brasil.

### PAM/N9 atualizado
A série oficial materializada neste projeto agora cobre **2015–2025**, nove produtos e nível N9, com **165.726 linhas** (558 microrregiões × 11 anos × 9 culturas × 3 variáveis). SHA-256 do CSV compactado: `c0f02831d5cc5f395d63acf01c27b10b4b3185db41743b1e05b96d024b3eae76`. Arquivo local: `data/pam_microregion_yield_2015_2025.csv.gz`; metadados em `data/pam_microregion_yield_2015_2025.metadata.json`. Usar exclusivamente como série agregada para baseline/contexto e associação regional; não como rótulo de propriedade nem verdade de talhão. A série 2015–2024 anterior permanece como artefato histórico.

### Estado das pendências e ações de fechamento
- **Avanço concreto:** fonte pública CIRAD/JECAM encontrada, com observações brasileiras; rota adicionada ao inventário e priorizada para máscara/referência de cultura. Isso oferece alternativa local melhor que supor que padrões africanos sejam diretamente transferíveis.
- **Ainda pendente:** obter e auditar o arquivo migrado; confirmar licenças/termos correntes; extrair rótulos brasileiros e geometrias; associar cenas Sentinel-1 dinâmicas com atualização por cultura/fase; validar independente a máscara de cada cultura; acessar YieldSAT (pedido do usuário ainda pendente) ou outro rendimento georreferenciado autorizado; criar painel de rótulos com unidade, safra, propriedade e qualidade; validar modelos em holdouts espaciais e temporais por propriedades/fazendas inteiras.
- **Previsão de safra em nível de propriedade continua bloqueada.** CIRAD/JECAM não fornece rendimento; PAM só é regional; YieldSAT ainda não foi liberado; dados brasileiros de algodão por talhão seguem sob acesso controlado. Não exibir produtividade/produção como validada. Manter no painel executivo campos pedidos — idade provável em meses, estado fitossanitário aparente (bom/médio/ruim), produtividade na unidade usual da cultura e produção provável na área cultivada do polígono — mas usar “Indisponível”/“Bloqueada” até cada saída passar seu gate independente.

### Próximos passos operacionais, sem depender de nova pergunta
1. Resolver/download do anexo GeoNetwork JECAM e guardar URL de origem, hash, versão, licença, CRS, geometria, esquema e observações de SOS/EOS.
2. Filtrar apenas pontos/polígonos brasileiros e culturas contempladas; auditar amostragem, datas e suporte espacial. Fazer overlay/pareamento com Sentinel-1 dinâmico sem misturar rótulos de safra.
3. Gerar conjuntos de treino e validação por sítio/talhão/ano; reservar São Paulo ou Tocantins inteiro e temporadas para teste quando tamanho permitir. Rotular validação como local/limitada, não nacional.
4. Para rendimento, avançar em paralelo: concluir ativação e auditoria legal de YieldSAT para soja/milho; solicitar acesso autorizado aos dois estudos brasileiros de algodão; avaliar bases abertas internacionais apenas como transferência externa, nunca como comprovação brasileira.
5. Recalibrar atualidade Sentinel-1 por cultura, fase, região e disponibilidade real; nunca usar uma tolerância temporal universal sem validação. Depois executar ablações clima, SAR e fusão com dados conhecidos até o corte.
6. Só liberar previsão propriedade-level após backtest externo espacial-temporal, intervalo preditivo calibrado e verificação por unidade/propriedade. Idade/fitossanidade também exigem gates próprios; altura via SAR é proxy candidato de estrutura/vigor, não idade/saúde diretamente sem calibração local.

Este fechamento resolve a busca por uma alternativa CIRAD de referência de cultura, mas não afirma que a base migrada foi adquirida, que a máscara está validada, nem que previsão de safra está cientificamente concluída.


## Correção de status e conclusão da diligência CIRAD — v19 (substitui qualquer alegação mais forte em v18)

A busca confirmou uma referência científica CIRAD/JECAM útil para rótulos de uso/cultura, mas **não confirmou que o arquivo esteja atualmente baixável e operacional**. O artigo revisado por pares descreve observações de campo em escala de polígono, sete países tropicais, com sítios no Brasil (São Paulo e Tocantins), e informa distribuição CC BY e DOI do CIRAD Dataverse. A página atual desse DOI marca o dataset como *deaccessioned* porque foi transferido a outro repositório e aponta ao catálogo GeoNetwork do CIRAD. O catálogo atual depende de JavaScript, e a tentativa de resolver/baixar o anexo pelo acesso disponível não retornou o arquivo. Assim, registrar como **base documentada, com acesso ao arquivo migrado pendente de verificação**, nunca como download público confirmado. Referências: artigo/arquivos https://essd.copernicus.org/articles/13/5951/2021/essd-13-5951-2021.html ; página oficial de registro https://dataverse.cirad.fr/dataset.xhtml?persistentId=doi%3A10.18167%2FDVN1%2FP7OLAP ; catálogo GeoNetwork https://geode.cirad.fr/geonetwork/srv/fre/catalog.search#/metadata/6855571d-677a-4852-afa8-7d7084ed2de8 .

Há divergência de versão: o artigo descreve **27.197 registros** da versão de 2013–2020; um espelho de metadados posterior reporta **31.879** registros e cobertura até 2022. Não misturar os totais. Ao recuperar o arquivo, conferir versão, datas, observações, licença, checksum, schema e geometrias e documentar qual contagem é efetivamente reproduzida. O artigo diz que 87% das observações vieram de levantamento in situ e descreve controle de qualidade, porém informa também que representatividade se limita à zona/agrossistema correspondente, não a todo o país. Utilizar somente para classe de cultura/uso, com subamostra brasileira e validação local. Não contém rendimentos colhidos.

**Ação alternativa e critério de encerramento:** se o anexo GeoNetwork não puder ser obtido sem autenticação ou contato institucional, manter JECAM como rota de aquisição e seguir com as fontes brasileiras já no repositório: MapBiomas C11 apenas como pseudorrótulo beta; YieldSAT mediante ativação e termos do usuário para rendimento de milho/soja; estudos brasileiros de algodão mediante acesso autorizado; PAM/N9 apenas como baseline regional. Os estudos africanos CIRAD podem orientar hipótese/parametrização e transferência exploratória se houver dados efetivamente licenciados, mas não validam o Brasil por semelhança visual. Não enviar solicitação ou contato em nome do usuário sem autorização explícita.

**Conclusão:** a busca encontrou uma alternativa CIRAD cientificamente valiosa para identificação de cultura, com observações brasileiras na publicação, mas a disponibilidade atual do arquivo migrado permanece **não confirmada**. A pendência de rótulos SAR independentes, atualidade por cultura/fase e previsão de produtividade por propriedade permanece aberta. Nada nesta atualização libera previsão executiva numérica. Atualizar interface e materiais de retomada para evitar a formulação “base pública baixável”: usar “registro/publicação aberto; anexo migrado não verificado”.


## Atualização de execução v20 — arquivo JECAM/CIRAD Brasil recuperado via WorldCereal

### Diligência concluída: acesso público e licença confirmados para uma cópia específica
Foi localizada e baixada uma cópia pública do pacote `JECAM-CIRAD.zip` no repositório ESA WorldCereal/Zenodo, registro 7593734 (arquivo 5.825.674 bytes). O MD5 da cópia (`d1e24229728a0734532d4078c8e6f639`) coincide com o checksum publicado pelo Zenodo. A página do registro informa que o repositório inclui conjuntos originais publicados sob CC BY ou licença semelhante; adicionalmente, os XLSX de metadados de `2016_BR_JECAM_CIRAD_POLY_111` e `2017_BR_JECAM_CIRAD_POLY_111` dentro do próprio pacote especificam `CC_BY`, apontam para Creative Commons Attribution 4.0 e fornecem a citação do conjunto CIRAD. Assim, esta cópia brasileira pode ser usada sob CC BY 4.0 com atribuição e observância da licença. A descoberta resolve a pendência de localizar/acessar **uma referência pública JECAM para cultura**, apesar do Dataverse original estar deaccessioned. Fonte: https://zenodo.org/records/7593734 ; https://doi.org/10.5194/essd-13-5951-2021 ; https://doi.org/10.18167/DVN1/P7OLAP .

### Resultado da inspeção local do subconjunto Brasil
O zip contém arquivos SHP/DBF/SHX/PRJ/XML e planilhas XLSX/PDF de curadoria. Foram contadas as observações dos arquivos brasileiros: 2016 = **2.774 polígonos** (São Paulo 2.465; Tocantins 309); 2017 = **1.604** (São Paulo 1.604); total 4.378. A tabela detalhada por ano/sítio/cultura está em `data/references/JECAM_CIRAD_Brazil_2016_2017_class_counts.csv`, com proveniência, checksums, licença e limitações em `data/references/JECAM_CIRAD_Brazil_2016_2017_manifest.json` e `data/references/JECAM_CIRAD_Brazil_2016_2017_README.md`. O zip original está em `data/references/JECAM-CIRAD_WorldCereal_7593734.zip`.

Contagens brasileiras dos rótulos específicos na versão arquivada: milho 339, soja 205, cana-de-açúcar 769, laranjeira/citros 228, feijão 53, sorgo 29, milheto 26, café 23, trigo 61 e algodão 5; arroz 0. Há ainda 52 observações genéricas `Cereals` e 302 `Weakly vegetated agricultural`, que não devem ser artificialmente imputadas a espécies. Algodão (n=5) não sustenta treino ou validação robusta própria. Esses números contam polígonos/observações, não fazendas independentes.

Os metadados especificam levantamento de campo do tipo windshield (visita de campo ao longo das estradas/trilhas), amostragem oportunística e geometria de polígonos digitizada a partir de imagens de muito alta resolução. A precisão geométrica curada foi declarada como 0–10 m. A publicação explica que em Tocantins o crop-type pode registrar as duas safras a partir de resíduo ou entrevista e que acquisition date pode não refletir a cobertura ativa; usar SOS/EOS e `valtime` para escolher a safra. O desenho é adequado como referência local/benchmark histórico, mas não como amostra probabilística nacional. Alguns polígonos representam conjuntos homogêneos de campos adjacentes, não necessariamente uma única propriedade. Fontes: https://essd.copernicus.org/articles/13/5951/2021/essd-13-5951-2021.html ; a página informa coleta oportunística, campos homogêneos e datas de temporada; https://zenodo.org/records/7593734 .

### O que foi concretamente resolvido e o que permanece pendente
- **Resolvido:** fonte alternativa pública com arquivo brasileiro de rótulos JECAM/CIRAD foi encontrada, baixada e checksum-verificada; a licença CC BY 4.0 para os dois pacotes BR foi conferida nos XLSX; metadados e contagens locais foram documentados; rota foi atualizada no `agricultural_evidence_routes.py` e priorizada para tarefas de máscara de cultura.
- **Ainda por executar:** interpretar/normalizar geometrias e atributos para pipeline, confirmar codes/legend mapping, selecionar rótulos puros por espécie e safra, e parear cada polígono/datas válidas com cenas Sentinel‑1 reais do respectivo período. A consulta ao STAC Microsoft Planetary Computer pela extensão dos sítios retornou cenas Sentinel‑1 GRD em 2016 e 2017 (por exemplo, S1A 2016‑01‑01 e S1B/S1A 2017‑01‑01/06/07), confirmando que existe rota de arquivo SAR histórica. Isso foi somente descoberta de cenas por bounding box: não houve interseção de cada polígono, extração de pixels ou pareamento cena–rótulo. Não marcar a máscara Enform como validada apenas pela existência de rótulos ou cenas no catálogo.
- **Atualidade:** os anos 2016–2017 servem a backtest histórico e treino de representação/classificação; não são prova de área cultivada em 2026 e não calibram frescor SAR atual. O monitoramento remoto tem de consultar cenas dinâmicas recentes de Sentinel‑1 por AOI, safra, órbita e janela fenológica.
- **Previsão:** o JECAM não possui rendimento colhido, altura média mensurada ou diagnóstico fitossanitário. Logo, não resolve previsões de produtividade/produção por propriedade, idade em meses nem classe fitossanitária. PAM permanece contexto regional; YieldSAT segue sujeito à ativação/licença; algodão tem outras fontes brasileiras de rendimento sob acesso controlado. Manter as saídas executivas bloqueadas ou indisponíveis até seus gates independentes.

A conclusão correta agora é: **a rota CIRAD foi encontrada e o subconjunto aberto Brasil foi adquirido; a pendência científica de previsão de safra por propriedade permanece**. Não afirmar que o produto está operacional/validado até extrair/parear Sentinel‑1, treinar com unidade de independência correta, separar por sítio/fazenda/safra, validar temporal e espacialmente e calibrar a incerteza.


## Atualização de execução v21 — primeiro pareamento JECAM × Sentinel‑1 RTC real

Foi concluída uma leitura zonal demonstrativa de um polígono JECAM brasileiro contra uma cena **Sentinel‑1 RTC real**, por consulta do STAC usando a geometria observada e data adequada. A referência é o polígono `2017_BR_JECAM_CIRAD_POLY_111338`: soja, sítio São Paulo, 6,824 ha; `AcquiDate` 2017‑03‑27, `SOS` 2017‑04‑01, `EOS` 2017‑09‑30 e `valtime` 2017‑05‑01. A cena é `S1A_IW_GRDH_1SDV_20170507T083902_20170507T083927_016473_01B4B9_rtc`, plataforma Sentinel‑1A, órbita descendente relativa 126, aquisição 2017‑05‑07T08:39:14.503969Z, seis dias após `valtime`, dual-pol VV/VH, CRS EPSG:32723, raster float32.

Extração encontrou **45 pixels válidos por polarização**. VV: média nativa 0,05321596, mediana 0,05278995, min 0,01557298, max 0,08720287. VH: média nativa 0,01429082, mediana 0,01381782, p25 0,01100657, p75 0,01806673, min 0,00378736, max 0,02644649. Registrar somente valores nativos: não assumir conversão dB, sigma0 ou gamma0 sem confirmar escala/calibração no produto específico. Os resultados e proveniência estão em `data/references/JECAM_CIRAD_Sentinel1_pair_2017-05-07.csv` e `.json`. Credencial SAS temporária não foi gravada.

### Interpretação e decisão de qualidade
Esse pareamento prova que o arquivo JECAM/CIRAD e uma fonte pública dinâmica Sentinel‑1 RTC podem ser conectados tecnicamente para uma observação histórica. **Não é uma amostra aceita para treino/validação**: 45 pixels sobre um polígono de 6,824 ha indicam suporte reduzido; calcular explicitamente pixels internos totais, fração válida e posição de borda e aplicar limiar de área válida predefinido antes de aceitar qualquer polígono. Essa amostra demonstrativa está marcada como excluída do treino e da validação enquanto não passar esse critério. Não treinamos classificador nem computamos métricas de acurácia. O arquivo está documentado também no inventário técnico/README.

### Limites que continuam abertos
- Essa cena é de 2017 e não serve para declarar atualidade SAR em 2026 nem calibração de frescor por cultura/fase. Monitoramento executivo precisa consultar aquisições atuais no momento da AOI e da safra, registrando UTC, órbita, intervalo, latência, cobertura e áreas válidas.
- Precisamos ampliar o pareamento para centenas de polígonos e vários cortes temporais, controlando geometria, datas, classes, pixels válidos, orbitas e correspondência entre rótulo e estação. Houve 298 rótulos de cultura e 488 observações de todas as classes espacialmente candidatas a uma cena de 2017‑05‑07 com valtime próximo; esse total preliminar não foi todo extraído e não equivale a um conjunto SAR.
- Os cinco rótulos de algodão do arquivo continuam insuficientes; arroz não tem rótulos BR nessa cópia; a representatividade fica restrita aos sítios cobertos.
- YieldSAT continua aguardando acesso e termos; CIRAD/JECAM não fornece produção. PAM continua agregado regional. Sem rótulos de rendimento georreferenciados adequados, backtests espaço-temporais por propriedade, calibração de incerteza e dados SAR atuais, previsão de produtividade/produção por propriedade continua **bloqueada**.

A pendência operacional foi parcialmente fechada: agora há uma prova real de extração SAR por polígono em histórico público, com rejeição explícita por baixa cobertura. A pendência científica e de produção permanece; não apresentar essa observação como correlação, resultado de modelo ou validação.


## Correção v22 — gate de cobertura válido do extrator Sentinel‑1

Uma revisão do código após o pareamento piloto encontrou um erro no cálculo de `valid_pixel_fraction` de `sentinel1_mpc.extract_cog_polygon()`: o antigo denominador `np.ma.count(band)` já excluía nodata e pixels fora do polígono, podendo fazer a fração parecer 100% mesmo com cobertura parcial. O extrator foi corrigido para rasterizar o polígono completo sobre a grade Sentinel‑1, obter `expected_polygon_pixels`, contar separadamente `inside_scene_valid_pixels` e comparar pixels finitos válidos ao total esperado. Agora retorna `support_status` e usa limiar explícito de cobertura mínima, padrão 0,80, configurável via `min_valid_pixel_fraction`. Também retorna estado insuficiente se não houver pixels válidos. O limiar é controle operacional de qualidade geométrica, não evidência de acurácia do modelo.

**Consequência para o pareamento piloto:** as 45 amostras VV/VH de soja de 2017 continuam registradas como leitura real, mas não são amostras aceitas de treino ou validação até serem reextraídas com o denominador corrigido. A contagem anterior não informava o número esperado de células no polígono completo. O ambiente atual conseguiu ler o RTC com ponte local e TLS upstream verificado, mas a função do app usa leitura direta do COG; esta revisão não afirma que o extrator de produção foi reexecutado nem que a fração corrigida para o polígono piloto já foi calculada. Reprocessar a mesma cena e, em seguida, aplicar a regra em todos os registros com polígonos e datas válidas.

Esta correção melhora o controle de cobertura, mas não fecha validação de máscara ou previsão. Permanecem pendentes: pareamento em escala com numerosas geometrias, critérios de safra/validtime, holdouts independentes por sítio/fazenda e ano, amostras adequadas para culturas com pouca representação, cenas recentes para atualidade fenológica e rótulos de rendimento para previsão por propriedade. Não apresentar a previsão numérica de safra como validada.

# ADENDO DE CONTINUIDADE v23 — YieldSAT recusado e plano substituto (27/10/2026)

## Estado mais recente e precedência

O usuário informa que o acesso ao YieldSAT foi **recusado**. Esta informação substitui referências anteriores neste documento que diziam “aguardando ativação”, “pedido pendente” ou sugeriam que a liberação viria em breve. Não reenviar formulários, não abrir conta e não contatar o provedor em nome do usuário. Tratar YieldSAT como indisponível para este projeto até nova orientação explícita do usuário.

A indisponibilidade não deve paralisar o desenvolvimento técnico. Usar as fontes alternativas abaixo somente nos papéis compatíveis com seus dados e direitos. A existência de página, DOI ou rota no catálogo não comprova que os arquivos foram baixados, que o acesso funcionou ou que a licença permite uso.

## Rotas substitutas para rendimento

- **Soja brasileira — Zenodo 13770031:** dois campos/áreas no Sul do Brasil, grade amostral de 50 × 50 m e variáveis de rendimento/solo. Serve para piloto de leitura, QA, georreferenciamento e extração retrospectiva de Sentinel‑1 depois de auditar licença, CRS, safra, unidade, definição do rendimento e desenho amostral. Não é amostra representativa para validação de propriedades brasileiras.
- **USDA BARC Yield Archive v1:** dados públicos de monitor de colheita para anos disponibilizados entre 2014 e 2021, em milho, soja, trigo, sorgo e cevada. Usar observações brutas/limpas para QA e teste de transferência; preservar separadamente mapas krigados e camadas de erro. Domínio dos EUA: não valida previsão brasileira.
- **SICKLE — arroz na Índia:** rendimento/fenologia em parcelas junto de séries Sentinel‑1/2 e Landsat. Auditar arquivo e termos. Bom para testar método SAR-fenológico de arroz e transferibilidade; não calibra arroz brasileiro.
- **GROW-Africa v2:** grande base tropical multi-cultura, mas mistura crop-cuts de parcela, pesquisas e estatísticas administrativas. Para experimento de rendimento em parcela, filtrar somente observações com suporte, coordenada, método, unidade e licença verificados. Estatísticas agregadas não são rótulos de campo; África não é holdout brasileiro.
- **Cana brasileira no Hugging Face:** 12 campos em seis fazendas; licença CC BY-NC 4.0 conforme metadados consultados. Uso apenas dentro dos termos não comerciais; não usar em produto/treino comercial sem permissão separada. A dimensão pequena impede validação nacional.
- **Cana brasileira no Mendeley:** oito linhas/repetições experimentais, sem geometria de propriedade demonstrada. Referência agronômica auxiliar apenas, não validação espacial SAR.
- **Algodão brasileiro:** estudos Embrapa/Amaggi com rendimento por campos são candidatos sob autorização controlada; os arquivos brutos não são download aberto. Não presumir acesso/licença, não contatar autores sem autorização e não tratar artigos ou métricas publicadas como dados de validação do Enform. Mapas beta de algodão são apenas pseudorrótulos de máscara, nunca rendimento.
- **CYCLeSS, Inglaterra:** rendimento em suporte espacial próprio/agregado e dados de precisão. Usar apenas no suporte documentado e para transferência; nunca atribuir seus valores a propriedades individuais.
- **PAM/SIDRA/IBGE:** baseline/contexto regional apenas. É agregada e não constitui rótulo independente de rendimento de propriedade.

## Política de aquisição, proveniência e atualidade SAR

Não escrever “adquirido”, “baixado” ou “validado” sem confirmação observável dos arquivos e inspeção dos metadados. Para cada ingestão, guardar URL/DOI e data de acesso, termos/licença, hash, versão, safra, cultura, unidade e definição do rendimento, coordenadas/geometria e CRS, suporte espacial, método de coleta, qualidade e filtros aplicados. Separar observações de monitor de colheita de mapas interpolados/krigados e de estatísticas administrativas.

Rendimento e imagens são fontes independentes. Para retrospecção, parear cada rótulo por área e safra com Sentinel‑1 real adquirido até o corte temporal do forecast. Para monitoramento operacional, manter busca dinâmica e atualidade de Sentinel‑1 como requisito por cultura e fase fenológica; registrar datas UTC, órbita, polarização, produto/processamento, cobertura válida, latência e pixels realmente extraídos. Catálogo de fonte ou dado histórico não satisfaz frescor operacional. Não usar observações posteriores ao corte da previsão.

## Bloqueios científicos mantidos

As alternativas conhecidas permitem iniciar QA, pilotos e testes de transferência; **nenhuma substitui, por si só, um holdout brasileiro representativo e independente por propriedade**. A previsão de produtividade e produção em nível de propriedade permanece bloqueada até haver rótulos independentes compatíveis por cultura/domínio, máscara de cultura independente, extração real e auditável de SAR, calibração da atualidade por cultura/fase, validação espacial e temporal por fazenda/safra e incerteza calibrada. Fontes estrangeiras podem testar robustez/transferência; não podem ser renomeadas como validação brasileira.

No painel executivo, manter “idade provável da lavoura” em meses, “estado fitossanitário aparente” (bom/médio/ruim), “produtividade provável” na unidade usual da cultura (sacas/ha quando padrão; senão t/ha) e “produção provável” na área cultivada do polígono. Exibir valor apenas quando o gate próprio daquela saída estiver aprovado; de outro modo exibir “Indisponível” ou “Bloqueada”, sem preencher com PAM, valores simulados ou proxy não calibrado.

## Próxima execução

1. Implementar ingestores e manifestos para as rotas abertas após verificar arquivos e licenças; nunca simular download bem-sucedido.
2. Começar por BARC para QA do pipeline de monitores e pelo Zenodo de soja para piloto brasileiro, sujeito à verificação da licença e metadados.
3. Auditar o arquivo SICKLE e GROW-Africa para método/termos e filtragem de parcelas; não usar totais agregados como número de rótulos válidos.
4. Restringir o dataset de cana CC BY-NC a usos compatíveis; manter a base Mendeley como evidência experimental auxiliar.
5. Usar dados dinâmicos Sentinel‑1 e as regras de frescor do projeto quando os casos de teste forem preparados.
6. Manter previsão de propriedade bloqueada até validação independente brasileira representativa e relatório de holdout espaço-temporal. Acesso recusado ao YieldSAT não altera esse critério.

# ADENDO v24 — modelo matemático experimental SAR + clima para safra (27/10/2026)

**Ordem de prioridade retificada pelo usuário:** (1) identificação científica independente das culturas — primeira prioridade; (2) identificação do vigor e evolução fenológica — segunda; (3) previsão de safra — terceira e posterior. Consolidar os modelos e seus contratos de dados nessa sequência. Não antecipar integração de forecast para encobrir máscara de cultura não validada.

O documento `docs/MODELO_EXPERIMENTAL_PREVISAO_SAFRA_SAR_CLIMA_2026-10-27.md` especifica o modelo candidato híbrido: núcleo de processo de cultura/balanço hídrico inspirado em AquaCrop/FAO-66, assimilação da série Sentinel-1 para estados fenológicos e de dossel somente após calibração independente, e correção residual hierárquica por cultura/horizonte treinada com rendimentos observados por talhão. O preditor proposto é `log(Y+ε)=log(Y_proc+ε)+f_c,h(SAR, clima, solo, histórico)+efeitos de região/ano`; produção é `Y × área cultivada mapeada`, propagando a incerteza da máscara. Incerteza final deve combinar ensemble de estados/parâmetros e calibração split-conformal ou quantílica em propriedade/safra realmente reservadas.

Sequência de consolidação: primeiro, criar e validar classificadores específicos para soja, milho, sorgo, algodão, arroz, feijão, cana, café e citros; comparar RF/ExtraTrees e Gradient Boosting com modelos temporais SAR (LSTM/TCN/Transformer apenas se o tamanho da amostra justificar), usando grupos independentes por propriedade/fazenda, região e ano. Manter classes de fallback “áreas cultivadas” e “pastagem” conforme evidência e política do produto. Depois, consolidar estimadores SAR de trajetória de vigor/fenologia por cultura × fase × região, com atualidade calibrada e abstenção quando a série temporal não atender ao limite. Só então calibrar e integrar o forecast híbrido do documento técnico, com rótulos reais de rendimento, corte temporal auditado e holdout por fazenda/safra.

No código, `plan_crop_workflow()` registra essa ordem e indica a primeira etapa ainda sem aprovação. Não habilitar forecast apenas porque as três etapas aparecem no fluxo; manter `release_ready=False` até todos os critérios científicos completos, inclusive incerteza calibrada e aprovação de domínio.

Usar por cultura: soja, milho, sorgo, algodão, arroz, feijão, cana, café e citros, cada uma com calendário, fase crítica, alvo/unidade e parâmetros próprios; café/citros são perenes, cana separa cana-planta/soca/corte, algodão separa caroço/pluma. Altura obtida por SAR é covariável auxiliar e só entra após validação por cultura/região/fase; não converter altura universalmente para idade em meses nem confundir stress SAR com diagnóstico fitossanitário.

Prioridade de literatura: Brasil para calibrar e testar; savanas africanas como hipótese de transferência em milho/sorgo, com novo holdout brasileiro obrigatório. Estudos brasileiros de rendimento municipal (soja/PAM, Agritec etc.) informam apenas baseline regional; não são rótulos de lavoura. Estudos ópticos de feijão, algodão, café, citros e cana apoiam arquitetura/estágio, mas não provam previsão SAR.

Estado real: o modelo foi especificado, não calibrado; não há novos parâmetros ajustados nem resultados de desempenho nesta entrega. YieldSAT continua recusado. Alternativas atuais incluem piloto brasileiro de soja (2 áreas, licença a auditar), USDA BARC para QA/transferência, SICKLE arroz, GROW-Africa com filtro por crop-cut, estudos/datasets brasileiros condicionados por licença para algodão/cana e fontes experimentais para sorgo, feijão, café e citros. Não afirmar downloads sem adquirir e registrar os arquivos. A previsão de propriedade segue bloqueada até rótulos de rendimento por talhão adequados, máscaras independentes, SAR atual auditável e holdout representativo espaço-temporal com incerteza calibrada.

# ADENDO v25 — consolidação da prioridade 1: identificação científica das culturas

## Precedência e ordem obrigatória

Esta atualização torna explícita e operacional a sequência determinada pelo usuário: **1) identificação científica da cultura; 2) vigor e evolução fenológica; 3) previsão da safra**. Qualquer texto anterior que permita executar/preencher forecast antes da máscara independente fica subordinado a esta sequência. A cultura deve ser determinada sem exigir idade, altura ou estado fenológico; vigor/fenologia só recebe a cultura depois de aprovada a identificação. Previsão é uma etapa posterior e permanece bloqueada.

## Modelo consolidado para identificar culturas

Foi criado `crop_identification_modeling.py` como pipeline unificado para identificar nove culturas (soja, milho, sorgo, café, cana, arroz, feijão, citros e algodão), mais classes de fallback (“Áreas cultivadas”, “Pastagem”, “Não agrícola”). Por amostra, a unidade é campo/talhão × safra com série SAR multitemporal previamente agregada e identificadores auditáveis.

- Seleção candidata entre Random Forest e Extra Trees por validação cruzada agrupada por blocos espaciais apenas dentro do treino.
- Calibração logística em unidades e blocos independentes do treino.
- Avaliação final em blocos espaciais nunca vistos e safra(s) posterior(es), com matriz de confusão, macro-F1, balanced accuracy e métricas/gates por classe.
- Entradas obrigatórias: rótulo, unidade independente, bloco espacial, ano safra, split, origem/URL/licença, identificador de registro, datas de referência e observação, flag de referência de campo independente e atributos SAR reais. Fusão SAR+óptico exige variáveis óticas explicitamente identificadas.
- MapBiomas/IBGE, mapas derivados, PAM/SIDRA e pseudo-rótulos podem alimentar somente o split de treino conforme método/licença; nunca calibrar ou validar o classificador que usou esses rótulos.
- Não se exige dado de campo na propriedade-alvo; calibração/teste vêm de propriedades de referência independentes. Sem amostras elegíveis, não gerar peso nem acurácia.

`classify_crop()` verifica hash, esquema, domínio marginal dos atributos e gate por classe; fora do domínio ou sem aprovação, abstém. `decide_crop_identity()` é a decisão de identidade prioritária e opera sem altura/fenologia. `decide_crop_with_phenology()` é apenas compatibilidade legada/avaliação downstream; não deve bloquear a classificação primária. `plan_crop_workflow()` retorna a próxima etapa no encadeamento e mantém forecast desabilitado.

## Fontes e cobertura da primeira etapa

O repositório contém o subconjunto CIRAD/JECAM/WorldCereal do Brasil (4.378 polígonos históricos de SP/TO, 2016–2017, CC BY 4.0 conforme metadados do pacote) com classe observada pelo programa de campo. A extração pareada arquivada tem apenas um exemplo, 2017, 45 pixels válidos, e foi excluída de treino por suporte insuficiente. Os rótulos disponíveis são desbalanceados: cinco de algodão, nenhum de arroz, poucos registros de sorgo/café/feijão/citros em alguns anos. Essa fonte permite preparar/pilotar o pipeline; não valida um classificador nacional nem suporta por si só as classes raras.

A etapa v25 **consolida arquitetura e contratos; não concluiu o ajuste de pesos**, porque não há no repositório uma série de amostras SAR por campo com cobertura e split independentes suficientes para todas as culturas. O estágio 1 não é considerado aprovado. Não alegar acurácia nem liberar classificação específica por cultura até executar a validação dos pesos resultantes com rótulos independentes.

## Próxima execução imediata

1. Extrair um painel SAR multitemporal por polígono para CIRAD/JECAM histórico, preservando validity time, SOS/EOS, órbita, aquisição UTC, cobertura válida, mosaicos e unidade nativa; excluir talhões/cenas sem suporte adequado.
2. Usar as geometrias apenas nos intervalos em que rótulo e validade temporal são compatíveis. Agrupar por sítio/talhão e separar integralmente sites/blocos e safra futura entre treino, calibração e teste.
3. Tratar algoritmos como experimentos específicos por cultura e domínio; não alegar que um modelo global transferiu para o Brasil a partir da África ou de outro país. África pode informar prior/pretreino, sempre com validação brasileira independente.
4. Para culturas com rótulos insuficientes (especialmente algodão, arroz e demais classes pequenas), manter classe genérica/abstenção e adquirir rótulos adicionais licenciados. MapBiomas pode aumentar treino fraco apenas, nunca o conjunto independente.
5. Somente após o gate de cultura avançar para fenologia/vigor; só depois iniciar calibração de rendimento por talhão.

**Não executar testes sem solicitação do usuário.** Verificações de sintaxe/diff não substituem avaliação científica, e dados sintéticos não contam como validação.

# ADENDO v26 — CLI de treinamento e inferência da prioridade 1 (27/10/2026)

O primeiro estágio agora dispõe também de uma interface executável em `tools/train_crop_identification.py` e `classify_crop_identity_batch()` em `crop_fusion_batch.py`. A CLI lê CSV com um registro por campo-safra, features temporais SAR em colunas `sar_*`, metadados de referência/licença e splits separados; grava pesos experimentais e manifesto de auditoria. Ela não baixa cenas, cria pseudorrótulos nem transforma catálogo em aquisição. O lote de inferência usa `classify_crop()` e não chama o módulo fenológico.

Ainda não foi produzido peso/resultado de acurácia nesta tarefa. O conjunto CIRAD/JECAM no repositório tem labels históricos em SP/TO e uma extração Sentinel‑1 de demonstração com somente 45 pixels válidos, excluída por insuficiência de suporte. Antes de treinar, construir tabela por polígono e série SAR com validade temporal, geometria/CRS, aquisição UTC, órbita, polarizações, cobertura de pixels dentro do polígono, unidade nativa e fonte/licença. Agrupar talhão/fazenda inteiros nos splits; separação espacial e safra futura obrigatórias. Não aceitar resultados sintéticos como validação.

Prioridade permanece: identidade independente primeiro; vigor/fenologia por cultura depois; previsão por propriedade depois disso. Os gates de release seguem fechados. A previsão permanece `forecast_enabled=False` enquanto qualquer requisito posterior ou intervalo validado estiver ausente.

# ADENDO v27 — CropHarvest global: dados auditados e protótipos treinados (27/10/2026)

## Precedência e prioridade

Este adendo prevalece sobre trechos anteriores que afirmem que nenhum peso de identificação foi treinado. A ordem científica é: (1) identificação da cultura; (2) vigor fenológico; (3) previsão de safra. Cobertura global é útil para pré-treino e diversidade de padrões, como o usuário destacou. Ela não comprova desempenho no Brasil. Nenhum resultado de identificação, vigor ou previsão está validado para liberar operação nesta propriedade.

## Fonte aberta incorporada

Foi baixado e verificado o CropHarvest, DOI [10.5281/zenodo.5828893](https://doi.org/10.5281/zenodo.5828893), junto de seu código/documentação pública ([repositório NASA Harvest](https://github.com/nasaharvest/cropharvest)). O pacote completo declara 95.186 pontos, 33.205 multiclasse e 70.213 amostras pareadas a produtos de sensoriamento remoto/clima; o manifesto e arquivos auditados do projeto registram o subconjunto local efetivamente usado. O arquivo de atributos baixado passou no checksum MD5 publicado. Foram lidas 65.690 séries válidas, cada uma com 12 datas mensais e 18 variáveis: Sentinel‑1 VV/VH, Sentinel‑2, ERA5, relevo SRTM e NDVI.

A execução usou as séries pré-computadas (pontos/pixels), não patches espaciais de imagens brutas. O pacote separado de EO bruto, de cerca de 20,5 GB, não foi baixado. Portanto, não declarar que todas as imagens da web ou imagens de contexto espacial foram treinadas. CropHarvest agrega 21 referências e seus termos/licenças de origem variam; a licença CC BY-SA 4.0 do conjunto não elimina a obrigação de auditar as fontes constituintes antes de redistribuir dados ou pesos.

A contagem harmonizada usada pelo protótipo foi: algodão 3.083; milho 924; feijão 381; sorgo 281; citros 186; soja 202; arroz 161; café 39; cana-de-açúcar 417; outras classes/residual 60.016. Rótulos foram harmonizados por termos nominais (incluindo sinônimos em francês/inglês); essa harmonização precisa de revisão semântica e geográfica antes de um novo treino.

## Treino executado e interpretação correta

Foram ajustados dois protótipos ExtraTrees com 200 árvores, sem coordenadas como preditores: SAR VV/VH mensal isolado e todas as 18 variáveis (SAR + óptico + contexto). A avaliação diagnóstica reteve um de cinco folds espaciais agrupados por fonte e célula geográfica de 1 grau, com 12.866 exemplos no holdout. Resultado arredondado:

| Configuração | Acurácia bruta | Acurácia balanceada | F1 macro |
|---|---:|---:|---:|
| SAR VV/VH | 0,947 | 0,153 | 0,163 |
| SAR + óptico + contexto | 0,975 | 0,215 | 0,225 |

A acurácia bruta é inflada pela classe residual (60.016/65.690 amostras). A acurácia balanceada e o F1 macro foram calculados sobre as dez classes previstas, incluindo classe sem amostra no holdout, para não omitir categoria não avaliada. O desempenho balanceado é baixo: no fold diagnóstico, a maioria das culturas teve recall próximo de zero; citros não teve exemplo no holdout, então nem sequer tem métrica observada nesse fold. O maior F1 por cultura observado foi algodão; isso não valida algodão no Brasil. O resultado não sustenta uso operacional, previsão para propriedade, alegação de acurácia global nem calibração de probabilidades. O ensemble multissensor melhorou o F1 macro nesse split, mas ainda ficou inadequado.

Pesos e manifesto ficam em `models/experimental/cropharvest/`; o script reprodutível é `tools/train_cropharvest_global_id_baseline.py`. Os artefatos são protótipos exploratórios e não passam pelo gate de produção do classificador principal. Não conectar à interface da lavoura nem chamar `classify_crop()` com esses pesos como se fossem validados. O diagnóstico espacial usa rótulos originais heterogêneos, não conjunto de campo independente; também não é validação brasileira nem avaliação temporal futura.

## Próximas ações obrigatórias

1. Manter os pesos bloqueados para produto. Usar o conjunto global somente como pré-treino/referência, priorizando adaptação regional brasileira com rótulos independentes licenciados.
2. Corrigir o desequilíbrio e as classes residual/sem rótulo, revisar cada mapeamento de taxonomia e tratar amostras, fazendas e regiões inteiras como grupos. Comparar fusão SAR+óptico com SAR isolado e testar transferência em regiões que não apareceram no ajuste.
3. Incorporar o restante das referências brasileiras abertas (incluindo LEM+ e polígonos CIRAD/JECAM) somente depois de harmonizar safra, cultura, unidade espacial, licença e datas; extrair a mesma série Sentinel‑1 e Sentinel‑2. Não usar mapas derivados como referência independente contra si próprios.
4. Obter holdout independente de fazendas brasileiras, por cultura e região, com rótulo de campo ou referência de alta qualidade independente dos preditores. Reportar matriz de confusão, precisão/recall/F1 por cultura, intervalos agrupados espacialmente e desempenho por bioma/safra.
5. Avaliar o pacote EO bruto apenas se houver necessidade real de textura/padrões espaciais; isso exige processamento patch-based e uma divisão por fazenda/região para não vazar pixels vizinhos.
6. Só depois do gate de cultura passar, avançar para vigor fenológico; previsão de safra por propriedade continua bloqueada sem dados de rendimento georreferenciados, validação espaço-temporal independente e incerteza calibrada.

As imagens de fora do Brasil podem melhorar cobertura de padrões e o pré-treino, mas diferenças de cultivar, calendário, manejo, clima, órbita e cadeia de processamento permanecem fontes de mudança de domínio. Não assumir semelhança visual como evidência de transferência. Não executar uma declaração de validação sem holdout independente brasileiro.


# ADENDO v28 — expansão imediata das referências abertas (27/10/2026)

## Novos dados encontrados e auditados

A coleção pública WorldCereal Reference Data Module foi incorporada ao plano de identificação. Sua API permite descobrir e baixar conjuntos públicos sem autenticação, mas cada conjunto informa licença, citação e origem individual; usar sempre os metadados de cada fonte. A seleção `extract=1` indica amostras balanceadas para extração de dados EO.

Foi baixado e validado por checksum o pacote WorldCereal América do Sul 2022. Há 1.502.674 registros de origem e 8.710 pontos na amostra `extract=1`, todos os cinco conjuntos com licença CC BY 4.0 em seus metadados: Brasil MapBiomas-Song (894 pontos selecionados de soja); Argentina INTA verão (4.445: soja 954, sorgo 717, milho 681, cana 289, arroz 199, algodão 123); Argentina INTA inverno (2.543: cana 254 e cereal de inverno não especificado 1.296); Uruguai SIT/OAN (387 de arroz); Uruguai Song/OAN (441 de soja). A tabela detalhada está em `data/references/WORLDCEREAL_AMERICA_SUL_2022_AUDIT.csv`.

Esses rótulos provêm de mapas/classificações automatizadas, inclusive MapBiomas/Song e mapas nacionais. Eles são **treino fraco/pré-treino**; não usar para validar o mesmo mapa, sensor, ano ou classificação. A consulta dinâmica de catálogo confirmou 30 cenas Sentinel‑1 RTC para um ponto de referência de soja no Brasil na janela setembro de 2021–maio de 2022. A descoberta inicial retornou 30 cenas, mas uma nova consulta e a tentativa subsequente de leitura COG falharam com HTTPError. Portanto, disponibilidade no catálogo foi observada uma vez; acesso repetível a pixels e extração raster não estão confirmados. Não declarar a rota dinâmica operacional até repetir descoberta e leitura de pixels com êxito. O treinamento com esses novos rótulos ainda não foi executado.

Foi encontrado o Global Crop Type Validation Data Set do WorldCereal (DOI 10.5281/zenodo.7825628), 7.547 observações interpretadas visualmente em imagens de rua, licença CC BY 4.0. Um filtro preliminar por caixa envolvente aproximada do Brasil contém 3.854 observações: cana 1.726; milho 1.070; soja 548; arroz 81; sorgo 37; café-ou-chá 27. O recorte por caixa não é um recorte de fronteira nacional; classe café-ou-chá não separa café. Esta é uma **referência independente candidata**, não validação concluída: checar localização real da lavoura, distância entre observação e ponto, data da imagem e safra antes de parear com Sentinel. Não cobre de forma adequada algodão, feijão e citros. Um CSV menor de validação de 2021 tem 3.394 observações globais e 695 dentro da mesma caixa aproximada. O inventário está em `data/references/WORLDCEREAL_STREETVIEW_VALIDATION_AUDIT.csv`.

## Referências brasileiras adicionais

- INPE/Brazil Data Cube disponibiliza 922 pontos de treino de classes gerais cultivo/vegetação natural/pastagem e 1.258 pontos de validação em classes agregadas antrópico/natural. Pode servir para estudo de separação ampla de cobertura; não comprova a identificação das nove culturas.
- O benchmark Campo Verde descreve 14 cenas Sentinel‑1, 16 imagens Landsat 8 e rótulos em shapefile para soja, milho, algodão, sorgo e outras classes. Confirmar download e licença dos dados originais antes de incorporar.
- Priorizar também LEM/LEM+ e registros brasileiros de campo. Não duplicar amostras já representadas no CropHarvest e diferenciar rótulos de campo, declaração de produtor, interpretação visual e mapa automatizado.

## Próxima execução científica

1. Extrair `extract=1` de WorldCereal para a safra/data correspondente por Sentinel‑1 e Sentinel‑2; preservar datas e órbita SAR, qualidade, nuvens, geometria, fonte e licença. Começar por culturas/classes com amostra selecionada disponível.
2. Treinar como weak-label/pretreino e comparar com o protótipo CropHarvest; manter validação geográfica/fonte separada. Não reportar resultado como validação de campo.
3. Auditar o Street View Validation em nível de observação e mantê-lo intocado no ciclo de ajuste. Usar apenas amostras com correspondência inequívoca entre classe, data, pixel/campo e cena. Reportar por cultura e deixar classe sem suporte em abstenção.
4. Corrigir o protótipo anterior: as métricas espaciais balanceadas foram 0,153/0,163 (SAR) e 0,215/0,225 (multimodal) em acurácia balanceada/F1 macro sobre dez classes; não são adequadas para liberação. Os pesos continuam experimentais.
5. Não iniciar vigor antes da identidade passar validação independente por cultura/região; previsão por propriedade permanece bloqueada até validação espaço-temporal com rótulos de produtividade.

## Fontes públicas a preservar no histórico

- RDM e acesso REST sem autenticação para datasets públicos: https://worldcereal.github.io/worldcereal-documentation/rdm/explore.html
- Definição de referência, atributos de qualidade e amostragem `extract`: https://worldcereal.github.io/worldcereal-documentation/rdm/refdata.html
- Pacote harmonizado 2018–2024: https://doi.org/10.5281/zenodo.18769612
- Street imagery validation: https://doi.org/10.5281/zenodo.7825628
- INPE/Brazil Data Cube: https://gkhub.earthobservations.org/records/fne6k-zsd09
- Campo Verde dataset/paper: https://www.mdpi.com/2076-3417/11/9/4292


# ADENDO v29 — checkpoint executável e sem alegações prematuras (27/10/2026)

## Estado confirmado no encerramento desta etapa

1. O único treino executado continua sendo o baseline global CropHarvest (65.690 séries mensais pré-computadas). Os pesos SAR e SAR+óptico tiveram métricas fracas no holdout espacial: acurácia balanceada/F1 macro, sobre dez classes, 0,153/0,163 e 0,215/0,225. Eles permanecem experimentais; não estão aprovados para o painel nem para classificação de propriedades.
2. Os arquivos de referência WorldCereal América do Sul 2022 foram baixados e checados por checksum; a tabela auditada está em `data/references/WORLDCEREAL_AMERICA_SUL_2022_AUDIT.csv`. A validação Street View foi baixada e contabilizada; o CSV de auditoria está em `data/references/WORLDCEREAL_STREETVIEW_VALIDATION_AUDIT.csv`. Nenhum desses dois conjuntos foi convertido em atributos SAR/ópticos nem usado para retreinar pesos.
3. WorldCereal `extract=1` fornece 8.710 pontos de cinco fontes regionais, mas os rótulos inspecionados provêm de mapas/classificações automatizadas. Usar somente para treino fraco/pré-treino, jamais como teste independente contra o mapa/sensor de origem.
4. O Street View Validation oferece referência visual independente candidata para classes cobertas. Antes de teste, verificar se ponto, imagem, lavoura e safra coincidem; caixa aproximada do Brasil não equivale a limite nacional. Café está agregado a chá e não serve para validar café individualmente; não há suporte suficiente para algodão, feijão e citros nessa fonte.
5. A rota Microsoft Planetary Computer Sentinel‑1 RTC teve uma busca inicial de catálogo com 30 resultados para um ponto brasileiro. A repetição e a tentativa de leitura COG do pixel falharam com `HTTPError`. Portanto, ainda não há extração dinâmica de pixels confirmada nem série SAR nova para treinar. Não transformar disponibilidade STAC em aquisição bem-sucedida.

## Próxima execução obrigatória — prioridade 1

1. Recuperar acesso repetível aos pixels Sentinel‑1 (e ao Sentinel‑2 se usado), preservar o erro atual e testar aquisição/extração com timestamp, órbita, banda, CRS, validade/nodata e proveniência. Não registrar segredo temporário no log.
2. Fazer um piloto de extração com subconjunto `extract=1` estratificado por fonte/região/cultura e datas de safra. Confirmar valores, calendário, cobertura de pixel e licença; rótulos automatizados continuam sendo weak labels. Expandir apenas após o piloto reproduzível.
3. Manter Street View fora do treino e das decisões de hiperparâmetros. Depois de validar a ligação espacial/temporal, reservar observações elegíveis como holdout externo por região/fazenda e relatar métricas por cultura com intervalos apropriados.
4. Comparar o treino CropHarvest, treino fraco WorldCereal e treino combinado usando divisões agrupadas por fonte e região. Reportar matriz de confusão e precisão/recall/F1 para cada cultura; acurácia global não basta. Manter abstenção onde há poucos exemplos ou domínio divergente.
5. Atualizar os pesos de produção apenas se o teste independente suportar os gates por cultura. Até lá, `release_ready=false`, previsão desabilitada e vigor/fenologia aguardando identidade confiável.

## Fontes para retomar sem perder contexto

- Prompt anterior v28 no Library: manter como versão histórica. Este v29 é o checkpoint mais recente.
- Crops e rótulos regionais: `data/references/WORLDCEREAL_AMERICA_SUL_2022_AUDIT.csv`.
- Referências externas candidatas: `data/references/WORLDCEREAL_STREETVIEW_VALIDATION_AUDIT.csv`.
- Dados CropHarvest e protótipos: `data/cropharvest/` e `models/experimental/cropharvest/`.
- RDM público e metadados por coleção: https://worldcereal.github.io/worldcereal-documentation/rdm/explore.html
- Street-view validation DOI: https://doi.org/10.5281/zenodo.7825628
- Repositório CropHarvest: https://github.com/nasaharvest/cropharvest


# ADENDO v30 — programa 3.25.0: áreas cultivadas antes da cultura

## Requisito de produto e ordem de decisão
A próxima versão apresenta primeiro a detecção/interseção de áreas cultivadas no polígono da propriedade. Depois, identifica a cultura apenas onde a fonte cartográfica ou classificador conseguir sustentá-la. Pixels/áreas sem classe específica permanecem com o rótulo **“Áreas cultivadas”**. Rótulos específicos em português devem ser “Lavoura de soja”, “Lavoura de milho”, “Lavoura de cana-de-açúcar”, “Lavoura de arroz”, “Lavoura de café”, “Lavoura de citros”, “Lavoura de algodão”, “Lavoura de sorgo” ou “Lavoura de feijão”. Cultura fora do suporte fica genérica; não inferir por plausibilidade regional. Pastagem permanece distinta.

## Implementação concluída nesta entrega
- Programa fonte versionado como **Enform Verde 3.25.0 — Áreas Cultivadas**, a partir de `desktop_app.py`, com módulo `land_use_sar.py` atualizado.
- Poligonização MapBiomas agora preserva o código original da classe. Na camada anual C11 de 2025, as classes cartográficas explícitas soja (39), cana (20), arroz (40), café (46), citros (47) e algodão (62) são exibidas com rótulos “Lavoura de ...”. As classes amplas agricultura (18), lavoura temporária (19), outras lavouras temporárias (41), lavouras perenes sem subtipo (48) e classes sem identificação específica retornam a **“Áreas cultivadas”**.
- Um classificador SAR só pode produzir nome específico para classes que passaram pelo gate espacial independente já definido em `land_use_sar.py`; as demais áreas permanecem como grupo pai genérico/abstenção. A renderização amigável mapeia as nove culturas-alvo, inclusive milho, sorgo e feijão, apenas para rótulos SAR elegíveis. Protótipos CropHarvest permanecem bloqueados e não foram conectados à aplicação.
- O painel executivo inclui fonte e taxonomia para cada resultado e avisa quando o nome específico vem da classificação anual MapBiomas 2025. Essa indicação é uma classe cartográfica de referência, não uma observação SAR contemporânea ou validação independente na propriedade. Idade, vigor, estado fitossanitário e previsão continuam sujeitos aos bloqueios científicos anteriores.
- Sobreposição, precedência espacial e soma das áreas continuam calculadas pelo método atual. A estimativa da área segue cartográfica, sem ajuste por erro amostral.

## Artefatos
- Aplicação: `desktop_app.py`; módulos de suporte: arquivos Python de raiz do projeto; dependências: `requirements_desktop.txt`.
- Pacote de código: `Enform_Verde_v3.25.0_areas_cultivadas_source.zip`. O pacote é fonte executável por Python, não é um instalador/EXE Windows compilado. O EXE requer build Windows e verificação próprios.
- Prompt de continuidade: este arquivo v30.

## Limites conhecidos e próximo passo
MapBiomas C11 2025 tem legenda anual, resolução nominal de 30 m e os vieses/erros próprios da classificação. Ela não entrega nesta versão rótulos específicos para milho, sorgo ou feijão; essas culturas só podem ser nomeadas por SAR se uma configuração independente cumprir os requisitos de treino, calibração e validação. Não alegar desempenho por propriedade, atualidade SAR, acurácia específica ou previsão de rendimento com base apenas na classe MapBiomas. O v29 não foi apagado e seus protótipos experimentais continuam fora de produção.


# ADENDO v31 — mensagem sem cultivos e clima dinâmico no painel agrícola

## Mensagem para ausência de cultivos
Na aba **Monitoramento de áreas cultivadas**, quando a classificação cobrir integralmente o polígono e não houver classe de cultivo, apresentar exatamente **“sem cultivos detectados”**. Não emitir essa conclusão quando houver lacunas relevantes de cobertura, falha de fonte ou erro de classificação; nesses casos, informar que a detecção está inconclusiva/indisponível. A decisão deve reconhecer também os rótulos executivos “Lavoura de soja”, “Lavoura de milho” etc. como evidência de cultivo, além de “Áreas cultivadas”. A ausência de cultivos deve ser decidida pela classificação de uso/cobertura, sem exigir que toda a área seja vegetação nativa.

## Climatologia dinâmica sempre disponível na aba agrícola
A aba deve oferecer consulta e atualização manual, e iniciar consulta dinâmica de clima após a análise da propriedade, mesmo que nenhum cultivo tenha sido detectado. Exibir dados reais disponíveis da NASA POWER (histórico diário em grade, período consultado e horário da consulta) e previsão do CPTEC/INPE; identificar separadamente produto, período e fonte. Falhas de uma fonte devem aparecer como indisponibilidade dessa fonte, sem ocultar a outra. A meteorologia pode ser mostrada como contexto da propriedade, mas não deve ser apresentada como vigor fenológico, condição fitossanitária ou previsão de produtividade sem os modelos e validações independentes apropriados. Não combinar médias entre NASA POWER e CPTEC sem variáveis/períodos compatíveis e ponderação validada.

## Proteção contra regressão de carbono nativo
A entrega agrícola não pode modificar nem contornar os módulos, saídas, incertezas ou gates de mensuração de carbono em vegetação nativa. O build Windows deve executar e passar as verificações existentes de estratificação nativa/confiança, fallback Pantanal, processamento SAR real e AOIs de aceitação aplicáveis antes de liberar artefato. Registrar resultado individual dos gates de carbono; não declarar ausência de regressão com base apenas em compilação sintática. Se uma verificação de carbono falhar, corrigir e repetir antes de oferecer o executável.

## Estado da compilação Windows
O primeiro workflow Windows executou com sucesso os gates de estratificação de carbono nativo e de fallback do Pantanal. O job parou antes da compilação quando o endpoint STAC Planetary Computer respondeu HTTP 504 na verificação SAR do Cerrado. Isso é uma falha de serviço externo observada, não evidência de regressão de carbono. Uma repetição do job começou antes da inclusão desta recomendação de mensagem/clima; ela não substitui a build final do código v3.25.1. A build de entrega precisa conter este adendo e confirmar novamente os gates de carbono e o self-test do EXE.
