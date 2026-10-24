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
