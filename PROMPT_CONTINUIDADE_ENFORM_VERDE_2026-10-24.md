# PROMPT DE CONTINUIDADE — ENFORM VERDE SAR
Atualizado em 24/10/2026. Usar este documento para retomar a implementação sem perder requisitos.

## Estado comprovado
Repositório: claudiodcandrade-lgtm/Enform-Verde.exe
Branch de trabalho: feature/agricultural-identification-native-carbon
Base operacional preservada: commit 04b26aa982c6ec25c872a79b3c1c4676d2b1a52a, workflow #40038576776.
Módulos acrescentados na branch (não comprovadamente integrados à aplicação):
- agricultural_native_policy.py — regras conservadoras de classes, máscara nativa e soma de estoque;
- sar_crop_timeseries_discovery.py — descoberta inicial de cenas;
- sar_crop_catalog.py — descoberta Sentinel-1 STAC com paginação e metadados;
- carbon_report_clarity.py — formato de resultados e incertezas tC/ha e %;
- carbon_dashboard_html.py — painel HTML independente com trilha expansível.
ATENÇÃO: nenhum destes módulos, por si, comprova classificação agrícola operacional, integração ao aplicativo, testes reais de cenas, nem executável Windows validado.

## Objetivo obrigatório
Concluir aplicação Windows autônoma com estimativas de carbono exclusivamente em vegetação nativa, identificação conservadora de oito culturas e pastagens, séries temporais SAR atuais e painel de resultados claro, sem regressão das funcionalidades já operacionais.

## Não regressão
1. Criar inventário verificável de módulos, interfaces, testes, empacotamento, workflows e artefatos da base operacional antes de editar o núcleo.
2. Preservar AOI SHP/GPKG/GeoJSON/KML/KMZ; mapa IBGE raster offline (municípios, estados, hidrografia, infraestrutura), scroll, zoom, polígono semitransparente, hectares, formatação pt-BR e controles existentes.
3. Preservar cálculo de AGB, altura SAR e prioridades ESA BIOMASS P; rotas alternativas compatíveis; IBGE legenda_1; MapBiomas para uso/cobertura; inventários e biblioteca; compartimentos AGB, raízes, necromassa aérea/subterrânea, serapilheira e solo; fontes e limitações.
4. Preservar simultaneamente tC, tCO2e, densidades por hectare, totais e conversão 44/12. Preservar horários UTC e UTC-3 quando realmente existirem; ESA CCI anual informa ano de referência, sem hora fictícia.
5. Criar testes de regressão por AOI e compartimento, comparar resultados com versão-base e justificar qualquer mudança numérica.

## Identificação agrícola
Culturas-alvo: soja, milho, sorgo, café, cana-de-açúcar, arroz, feijão e citros. Pastagem só quando separação segura; se não for possível distinguir de outros usos agrícolas, rotular 'áreas cultivadas'. Não atribuir cultura por simples aparência ou classe geral MapBiomas. Sempre exibir fonte, período, modelo/versão, confiança e limitações; classe incerta deve permanecer genérica.
- Priorizar séries temporais Sentinel-1 GRD VV/VH do Copernicus STAC; alternativa ASF, com proveniência e atualidade da aquisição; consulta diária configurável, histórico inicial 24 meses, acompanhamento 90 dias.
- Completar paginação, autenticação/licenças quando necessárias, download, cache, checagem de integridade, correções radiométricas/terreno, máscaras de borda/ruído, alinhamento espacial, harmonização por órbita relativa, polarização, geometria e incidência, índices temporais e indicadores fenológicos.
- Fusionar dados ópticos quando cientificamente justificável, documentando contribuição e limitações.
- Incorporar somente classificadores efetivamente disponíveis e com domínio, calibração, dados de treino, validação independente e métricas por cultura documentados. Não inventar pesos ou probabilidades; não apresentar protótipo como modelo validado.
- Reportar disponibilidade, datas, lacunas temporais e atraso de publicação; ausência de imagem não autoriza inferência.
- Avaliar generalização espacial/temporal e matriz de confusão, precisão/recall/F1 por classe, incerteza e limiar de abstenção.

## Carbono somente em vegetação nativa
- Máscara de vegetação nativa confirmada por fontes apropriadas, com geometria/área rastreáveis, aplicada ANTES de amostrar pixels, integrar inventários e totalizar todos os compartimentos, inclusive solo.
- Pastagem, culturas, áreas urbanas, água e áreas incertas fora dos totais. Não apresentar valor de estoque por hectare em estrato de área zero.
- Diferenciar 'não estimado' de 'zero medido' e de 'fora do escopo'; indicar estoque total como PARCIAL quando algum compartimento não foi estimado.
- Não criar falsa estimativa nem IC quando inexistentes; buscar fontes secundárias compatíveis para lacunas (necromassa subterrânea, serrapilheira etc.), com erro de transferência explicitado.

## Painel de resultados
- Resumo executivo com área nativa, área por uso, fitofisionomia, AGB SAR, estoque parcial conhecido tC e tCO2e, densidades tC/ha e tCO2e/ha; indicar ano do produto e status de cada estimativa.
- Tabela e gráfico por compartimento com estoque tC/ha, total tC, tCO2e/ha e total tCO2e; incerteza em ±tC/ha e ±%, e TIPO da medida (SD do produto, SD espacial, IC95%, erro de predição).
- Para ESA CCI AGB_SD, converter Mg biomassa/ha para tC/ha SOMENTE com fração de carbono usada/documentada. Não equiparar AGB_SD médio a IC95% da média ou total.
- Para Embrapa Solos/PronaSolos, mostrar desvio espacial tC/ha e % claramente, mas NÃO chamá-lo de erro preditivo; buscar mapas/camadas de incerteza preditiva reais se existirem. Se indisponíveis, indicar isso.
- Intervalos em massa seca de serapilheira só podem ser convertidos a tC/ha com fração de C e incerteza documentadas.
- Rastreabilidade em seção expansível: AOI, estrato, pixel/cena, sensores, datas, produto/versão, arquivos, fórmulas, inventários, fontes, métricas, parâmetros e logs; evitar JSON bruto no resumo.
- Integração real ao aplicativo Windows, exportação e layout responsivo/legível. Não apenas gerar HTML solto.

## Critérios de aceite e liberação
1. Inspecionar a árvore real e ligar os módulos ao fluxo principal, sem sobrescrever rotinas operacionais.
2. Testes unitários, integração, regressão e cenários reais de AOIs (floresta alta biomassa, savana, Pantanal, área agrícola mista). Testar soma por área e máscara nativa; evitar dupla contagem de perfis 0-60/0-100/0-200 cm.
3. Validar cenas recentes Sentinel-1 de fato acessadas, com aquisição UTC verificável; validar ao menos um classificador por cultura ANTES de alegar cobertura das oito.
4. Gerar novo workflow Windows; exigir conclusão SUCCESS e artefato Windows do mesmo SHA; testar executável empacotado, não só código-fonte.
5. Somente então informar link de download e declarar explicitamente o que foi validado e o que permanece pendente. Nunca chamar de versão concluída se algum critério não foi atendido.

## Exemplo de problema que deve ser corrigido
Relatório da AOI 1.290,69 ha Floresta Ombrófila Densa: AGB 263,07 Mg/ha, carbono aéreo 123,64 tC/ha; ESA CCI AGB_SD médio 126,76 Mg biomassa/ha, dispersão espacial AGB 78,73 Mg/ha; solo 0–30 cm 46,06 tC/ha com SD espacial 2,07 tC/ha; necromassa aérea 8,70 tC/ha, IC95% publicado 7,40–10,00; raízes 22,42 tC/ha sem erro quantificado; serapilheira 2,33 tC/ha com intervalo original em massa seca; necromassa subterrânea não estimada; soma PARCIAL 262.202,00 tC e 961.407,35 tCO2e. Relatório anterior repetia 'NÃO ESTIMADO' em classe de 0 ha, ocultava incertezas em JSON e confundia variabilidade com erro.

## Próxima ação
Verificar código real da aplicação e do workflow, identificar pontos de integração e testes. Não alegar finalização antes da execução e verificação dos critérios.


## Ampliação de escopo — fitossanidade e previsão de safra (24/10/2026)
Commit de módulo inicial: 80dd7633e634ee752ea2b5d80b16ff9a4bde8341, arquivo crop_health_yield_quality.py. Implementado SOMENTE contrato de avaliação e travas de evidência; não há ainda modelo treinado, dados meteorológicos conectados ou previsão operacional.

Objetivos:
- Detectar anomalias de vigor/estresse em séries SAR (VV/VH, retroespalhamento, coerência quando aplicável), fundidas com óptico (NDVI, NDRE, índices de água, temperatura superficial quando disponível) e clima. Comparar com linha de base por cultura, estádio fenológico, local, época e geometria de aquisição; produzir indicadores e mapas com datas e confiança.
- Não afirmar diagnóstico específico de doença/praga por simples anomalia SAR. Identificação etiológica requer treinamento, referência de campo e validação específica. Distinguir seca, encharcamento, deficiência nutricional e fitopatologia somente se separabilidade demonstrada.
- Ingerir dados meteorológicos dinâmicos com metadados de fonte, hora, resolução, qualidade, interpolação e atraso: INMET/estações, ERA5-Land (reanálise), NASA POWER (histórico), CHIRPS (chuva), previsões meteorológicas com horizonte explícito. Priorizar estação local qualificada quando disponível; não tratar reanálise como observação direta nem previsão como medição.
- Calcular ET0 (FAO-56 Penman–Monteith quando entradas suficientes), déficit hídrico, graus-dia, chuva acumulada, radiação e indicadores de extremos; parametrizar solo, fenologia e irrigação. Não usar equações fora do domínio.
- Previsão de produtividade (t/ha) e produção (t) por cultura e talhão, com área cultivada confirmada, horizonte, data de referência, intervalos de predição calibrados e métricas de erro. Comparar baseline estatístico (histórico regional), modelos agrometeorológicos, AquaCrop (FAO), DSSAT, APSIM, WOFOST quando parâmetros e licenças permitirem, e ML temporal com SAR+óptico+clima. Priorizar modelos que superem baseline em safras/regiões independentes.
- Validar com colheitas observadas, particionamento por talhão, ano e região, evitando vazamento espacial/temporal; reportar MAE, RMSE, viés, R², erro percentual quando apropriado, cobertura de intervalos e erro por fase fenológica. Para previsão antes da colheita, não usar dados futuros na entrada.
- No painel: estado da cultura, anomalias e sua severidade/qualidade, risco fitossanitário NÃO diagnóstico etiológico, produtividade prevista t/ha, produção t, intervalo de predição, fontes e última aquisição, última atualização meteorológica, estágio fenológico e rastreabilidade integral.
- Atualização automática da previsão após cada nova observação válida; registrar versões de modelos e permitir abstinência se qualidade insuficiente.
- Preservar integralmente cálculo de carbono SOMENTE na vegetação nativa e todas as rotas anteriormente operacionais.
- Próximas tarefas: verificar APIs e licenças; implementar adaptadores, pré-processamento, modelos com pesos e calibração reais, testes de ponta a ponta e integração Windows. Não declarar recurso concluído antes de validação.


## Política adicional: prioridade a modelos efetivamente treinados (24/10/2026)
Preferir pesos de inferência realmente disponíveis e fontes científicas/institucionais confiáveis. Verificar DOI, autores, afiliação, versão, licença de código e pesos, documentação de treino, rótulos, sensores, pré-processamento, métricas por classe/fase, partição independente e domínio. Diferenciar: (a) pesos publicados; (b) código para treinar; (c) artigo sem pesos. Nunca equiparar.
Candidatos a auditar:
- VITA, AAAI 2026, pesos https://huggingface.co/notadib/VITA e código https://github.com/neehan/VITA — previsão milho/soja em condados dos EUA, meteorologia NASA POWER. Transferência ao Brasil exige teste local e compatibilidade de escala.
- Wadhwani AI, https://huggingface.co/wadhwani-ai/AI-Enhanced-Crop-Field-Data-Curation — XGBoost treinado com Sentinel-1/Sentinel-2 e referências do Mahalanobis National Crop Forecast Center, Índia; conferir classes, arquivos, licença, entradas e domínio.
- S2-PhenoCNN, https://huggingface.co/kavayam/s2-phenocnn — pesos para milho, arroz, soja e sete fases fenológicas do arroz; apenas Sentinel-2, sem alegar cobertura SAR nem estágios de todas as culturas.
- BreizhCrops, DOI 10.5194/isprs-archives-XLIII-B2-2020-1545-2020 — benchmark com pesos pré-treinados, Sentinel-2 e classes europeias.
- CropTypeMapper, https://github.com/agroimpacts/croptypemapper — código e exemplo de inferência, requer obter e conferir parâmetros treinados.
Não habilitar nenhum candidato sem ensaio reproduzível e validação local independente, por talhão, safra, região e fase; abstenção obrigatória em caso de incompatibilidade. Para fitossanidade não inferir doença específica a partir de anomalias; para safra reportar RMSE, MAE, viés, intervalos e horizonte.
Status: seleção de candidatos e documentação; ainda NÃO foram integrados pesos nem executadas inferências reais.

## Etapa painel executivo — alteração de código (24/10/2026)
Commit 7492382162b7d25aab033b2c91878d7d19f74a46: carbon_dashboard_html.py agora exibe tCO2e, densidade tC/ha, alerta de total parcial, lista de compartimentos sem incerteza e alerta explícito de ausência de incerteza total. Não inferir incerteza conjunta de incertezas heterogêneas sem covariância e propagação validada. Ainda é um HTML independente, NÃO integrado ao fluxo principal Windows; testes e empacotamento não executados. Conferir execução do renderizador, escaping e casos zero/ausentes antes de liberar.
Regra universal: todos os painéis executivos de carbono, fitossanidade e previsão agrícola devem ter campo visível de incerteza, unidade, tipo estatístico, intervalo/nível quando houver, método, amostra/validação, fontes e status 'não quantificada' quando necessário. Nunca inventar incerteza para preencher lacuna. Não habilitar previsão sem RMSE/MAE/viés e validação independente; risco de estresse não é diagnóstico etiológico.
Referência verificada: AquaCrop FAO v7.3 https://www.fao.org/aquacrop e código oficial https://github.com/un-fao/fao-AquaCrop ; modelo mecanístico, não substitui calibração por cultura, região e solo. Para culturas perenes arbóreas não assumir cobertura equivalente a culturas herbáceas.
Próxima etapa OBRIGATÓRIA: integrar renderizador ao programa Windows e pipeline de estimativas, ligar fontes meteorológicas reais, pesos validados e inferência real, rodar testes e construir artefato Windows. Não declarar concluído antes.

## Duas análises independentes no dashboard (24/10/2026)
Commit db3a245a884bd9e7a7832845630b7f885a85fc1a adicionou dual_executive_dashboard.py, renderizador HTML independente com navegação por abas: (1) Carbono em formações nativas, reutilizando carbon_dashboard_html.py, com estoques tC/tCO2e, densidades, compartimentos, incertezas, status parcial e rastreabilidade; (2) Monitoramento de áreas cultivadas, por talhão/cultura, área, fase fenológica, indicador de estresse, produtividade t/ha, produção t, incerteza t/ha e t, status e proveniência. Incerteza da produção obtida por multiplicação da incerteza de produtividade por área é condicional à área fixa e não inclui erro da área/classificação; aviso no painel. Sem resultados, indicar indisponível; não inventar incertezas.
ATENÇÃO: renderizador independente ainda NÃO integrado à GUI Windows nem validado por testes automatizados. Verificar navegação de abas nos motores HTML suportados, teste de segurança de escaping, casos vazios, unidades e incertezas, interface principal e empacotamento antes de liberar versão. Próximo passo integrar dados reais e workflow, preservando todas as rotas operacionais.

## Avanço em testes (24/10/2026)
- aec870b04ccb00ddffe6c03c10fad20e2164543e: tests/test_dual_dashboard.py com testes de duas abas, tC/tCO2e, incertezas, total parcial, escaping HTML e rejeição de área/incerteza negativa.
- 693a2fbdf488eac69314ea982cffe8fed6680d29: .github/workflows/dashboard-dual-tests.yml, execução de py_compile e unittest em windows-latest, por push/PR/manual.
- A criação do workflow não prova execução nem sucesso. Confirmar status e logs do GitHub Actions; resolver falhas antes de integrar no executável.
- Acesso ao README.md e commit-base no GitHub confirmado. Ainda não foi recuperada a árvore completa, nem localizado/alterado o ponto de entrada da interface Windows. Não há novo executável. Preservar 3.24.40-CANDIDATE.
