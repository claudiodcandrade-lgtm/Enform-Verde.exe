# Enform Verde — Plano executável para desbloqueio científico, sem fabricar evidências

**Data:** 2026-10-29 (UTC−3)  
**PR:** #50, branch `feature/agricultural-identification-native-carbon`.  
**Natureza:** estratégia metodológica e rotas de dados; **não é atestado de homologação**.  
**Baseline científico:** o gate `tools/scientific_release_gate.py` exige evidência independente real para 5 biomas × 6 compartimentos e demais componentes. O arquivo `validation/release_evidence.json` ainda não foi encontrado nos runs auditados; testes de contrato e ZIP Windows verde não suprem a lacuna.

## 1. Fontes reais prioritárias — procedência, acesso e limites

| Fonte oficial ou publicação | URL confirmada | Uso defensável | Limite de validade |
|---|---|---|---|
| SFB — Painel IFN de Biomassa e Carbono (2026), CC Attribution | https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono | CSV de biomassa, árvores mortas, necromassa e equações, com unidade amostral quando fornecida; avaliar conjuntos por bioma/uso/fitofisionomia, estimar variância por unidades amostrais | Granularidade do portal declarada *estadual*. Identificador UA **não prova** coordenada pública, independência de um raster ou estoque de necromassa em pé e caída separadamente. Verificar dicionário e metadados originais antes de classificar compartimentos. |
| IFN — dados biofísicos com parcelas, madeira caída e serapilheira retificada | https://dados.florestal.gov.br/group/ifn | Priorizar planilhas primárias com parcela, estrato, massa seca, desenho amostral, diâmetros/altura quando houver; selecionar fonte da fitofisionomia correta | O IFN tem grade típica 20 × 20 km e alguns arquivos não têm licença ou localização aberta; transposição a AOI exige erro adicional. Verificar corrigenda da serrapilheira. |
| PronaSolos/Embrapa/SGB — estoque C solo a 90 m | https://geoportal.sgb.gov.br/server/rest/services/pronasolos/estoque_carbono_90m/MapServer | Cinco camadas **não cumulativas** 0–5, 5–15, 15–30, 30–60, 60–100 cm, IDs 2–6, perfis pareados na mesma célula. O serviço informa mapas de incerteza e relatório técnico | O desvio entre pixels não é incerteza preditiva. Localizar o **raster e definição estatística reais** de incerteza, covariância entre horizontes e validar com perfis físicos independentes; não inventar IC95%. |
| NASA GEDI L4A v3 (2026), DOI 10.3334/ORNLDAAC/2508 | https://daac.ornl.gov/GEDI/guides/GEDI_L4A_AGB_Density_V3.html | AGBD por footprint ~25 m, erro-padrão da predição, filtros de qualidade/sensibilidade e seleção de estrato do modelo; dados auxiliares espaciais de AGB/altura | É **lidar**, não SAR nem inventário de campo independente. Não usar GEDI como verdade única para avaliar modelo que tenha sido treinado com GEDI sem separação; incerteza de predição não é necessariamente erro de transferência local. |
| NASA GEDI L4B v2.1 | https://data.nasa.gov/dataset/gedi-l4b-gridded-aboveground-biomass-density-version-2-1-5fb8b | AGBD espacial média em células de 1 km e erro-padrão com componentes de amostragem/modelagem, referência auxiliar auditável | Não degradar nem reamostrar para 25–100 m como se fossem observações independentes; não confundir zero/nodata com zero biomassa. |
| MapBiomas — pontos de referência de cobertura (Coleção 9) | https://brasil.mapbiomas.org/downloads/pontos-de-validacao/ | 85.152 pontos estratificados com rótulo visual anual, concordância, borda e pesos para testar **cobertura nativa vs. antrópica** e grupos de uso; adaptar desenho ponderado | Só é amostra independente de um novo classificador se **nenhum desses pontos** tiver sido usado no treino/tuning/seleção; a própria página diz que apenas a cobertura 30m tem acurácia consolidada. Não presumir que classes agrícolas por cultura tenham verdade de campo. |
| IBGE PAM/SIDRA | https://apisidra.ibge.gov.br/ | 133.920 registros 2015–2024 já materializados no projeto; alvo regional cultura×microrregião×ano para **modelo regional** | PAM não mede produtividade por talhão nem fornece rótulo SAR por pixel. Manter fronteiras territoriais/ano e datas de disponibilidade. |
| Publicação de alometria raízes — Mokany et al. (2006) | https://doi.org/10.1111/j.1365-2486.2005.001043.x | Selecionar relações raízes/parte aérea **somente** para fitofisionomia, domínio de biomassa e unidade compatíveis; pesquisar erro/covariância da equação | Uma razão de médias publicada sem variância, desvio residual e evidência de transferência não autoriza IC95% da AOI. |
| NASA / GEDI L4B métodos e variâncias | https://daacweb-prod.ornl.gov/GEDI/guides/GEDI_L4B_Gridded_Biomass.html | Separar componente de erro de modelo e de amostragem ao usar AGB agregada | Não confundir qualidade do próprio produto NASA com validação independente do Enform Verde. |

Os CSV nacionais do SFB têm rotas explícitas no coletor `tools/harvest_ifn_field_data.py` (biomassa, árvores mortas, necromassa, equações). Manifesto registra SHA-256, UA/bioma, coordenadas **se realmente presentes**, contagens, licença e falhas, com `validation_status=harvested_not_validated`. Não completar coordenadas ausentes por inferência. O arquivo de necromassa separado do IFN sem licença confirmada continua bloqueado até autorização; o painel 2026 é um conjunto distinto com CC Attribution explícita.

## 2. Estimação por estrato, nunca por média bibliográfica mapeada

1. Intersectar AOI com máscara temporalmente válida de cobertura nativa (classificação validada, MapBiomas de ano declarado, interpretação independente) e **IBGE legenda_1** de fitofisionomia. Resultado `A_s` em hectares para cada estrato; incerteza de cobertura/área registrada separadamente. A legenda IBGE, sozinha, não comprova cobertura atual.
2. Para cada `s`, selecionar medições efetivas segundo hierarquia: parcelas **microrregionais compatíveis** > regionais > estaduais IFN por fitofisionomia, com critérios explícitos de amostragem, ano, decomposição, licenciamento, e tamanho efetivo independente. Qualquer resultado com dados estaduais é fallback de transferência, não calibração local.
3. AGB: conferir unidade de massa seca, equação para DAP/altura/espécie/densidade, inclusão de árvores pequenas, e evidência de parcelas. SAR deve contribuir com **pixels realmente processados** (HH/HV, VV/VH, P-band, conforme domínio) pareados a parcelas independentes. Priorizar ESA BIOMASS L2B AGB quando realmente publicado e acessível; usar GEDI L4A/L4B como informação auxiliar com proveniência e sem chamá-lo de SAR. Não extrapolar L-band saturada para floresta úmida de alta biomassa.
4. Raízes: alometria original compatível com distribuição de fitofisionomia + incerteza dos coeficientes, resíduo e AGB. `root_allometry_uncertainty.py` hoje sabe diferenciar intervalo **condicional** de cobertura real; só liberar IC validado após avaliação externa.
5. Madeira morta em pé e caída: determinar no dicionário oficial quais componentes cada arquivo mede. Aplicar delineamento amostral/área de transecto, classes de decomposição, gravidade específica e fração de C medidas/publicadas; nunca usar alometria de árvore viva para criar necromassa. Não dividir artificialmente um único valor agregado entre os dois pools.
6. Serrapilheira: converter massa seca por superfície em t/ha e C por fator medido ou reconhecido para o domínio, incluindo amostragem e variância; priorizar IFN **retificado**. Espessura sem densidade de massa não é estoque.
7. Solo: compor somente cinco profundidades da mesma célula até **100 cm**, sem repetir horizontes ou incluir camada 100–200. Preferir integração espacial raster com área ponderada e validação por perfis independentes; na impossibilidade técnica, amostras sistemáticas espaciais geram **estatística do mapa**, não IC de acurácia. Densidade e fragmentos grosseiros são essenciais quando estoque for calculado a partir de teor SOC.

## 3. Matemática mínima auditável de propagação

Para densidade de carbono de compartimento `p` e estrato `s`, `C_sp` em tC/ha:

```text
T_p (tC)      = Σ_s A_s × C_sp
T_total (tC)  = Σ_p Σ_s A_s × C_sp
T_total (tCO2e) = T_total (tC) × 44/12
Var(T)        = g' Σ g        (método delta com covariância completa)
ou Monte Carlo hierárquico: sorteio conjunto da máscara/área, parcelas,
parâmetros alométricos, resíduo, erro de mapa, dependência espacial,
transferência geográfica/temporal e variação entre horizontes,
preservando fatores comuns correlacionados entre compartimentos.
IC95% = quantis 0,025 e 0,975 de uma distribuição apropriadamente calibrada
ou intervalo de desenho amostral/modelo, com cobertura testada em holdout.
```

**Proibições:** nunca somar intervalos individuais como se covariâncias fossem zero, usar desvio entre pixels como RMSE de mapa, duplicar erro entre camadas, calcular tCO2e antes da fração de C sem checar unidades ou afirmar `5% a 95%` sem tamanho amostral suficiente. Nas árvores vivas, manter conversão de biomassa seca para C por fração publicada, com incerteza quando aplicável. Para totas, distinguir variância compartilhada (AGB→raízes) de variância independente de transecto.

## 4. Validação que realmente habilita os cinco biomas

Criar no conjunto `validation/` datasets **licenciados e auditáveis**, sem dados pessoais, para os 30 pares mínimos = 5 biomas × `agb, roots, standing_deadwood, downed_deadwood, litter, soil_0_100`. Cada pacote deve conter:

- `sources.json`: instituição, licença, URL, versão/ano, hashes, método de coleta, geometria consentida, resolução e fitofisionomia original/IBGE harmonizada.
- `samples.parquet/csv` quando permitidos: parcela/UA pseudonimizada se necessário, coordenadas publicáveis ou unidade espacial legítima, estoque observado, variância/design weights, profundidade e C%.
- `holdout_definition.json`: treino/calibração/teste por blocos geográficos, por inventário e, quando viável, por ano; sem reaproveitar parcelas entre conjuntos ou variogramas ajustados no teste.
- `validation_report.json`: n e n efetivo, percentuais de cobertura, RMSE, MAE, viés, R² quando informativos, validação cruzada espacial com blocos pré-definidos, bootstrap por bloco/grupo, incerteza de transferência e taxa de cobertura real do IC95%.
- `integration_report.json`: checksum de entrada, retorno do motor no AOI, status de cobertura e cada pool, nomes de classes, tC/ha, tC, tCO2e, decisão de elegibilidade e razões de abstenção.
- `windows_artifact.json`: SHA de código e EXE no **mesmo SHA homologado**, URL real do ZIP, digest ZIP, SHA-256 EXE, smoke em pasta limpa, regressões e benchmark.

Para cada estrato com amostra insuficiente, registrar a ausência, reportar a estimativa como **exploratória** quando cálculo e incerteza defensáveis existirem, e **não** atestar homologação daquela fitofisionomia. A aprovação dos cinco biomas exige representatividade, não apenas um ponto ou uma média por bioma.

## 5. SAR, cobertura nativa e agricultura: trilhas independentes

- **Pares parcela–pixel:** alinhar footprint, data, geometria e resolução; usar agregação de pixels conforme tamanho real de parcela e georreferenciamento, não pixel central automático. Separar radar L/P/C, incidência, orbitas e níveis de processamento. Repetir validação independente de anos e localidades, excluindo áreas desmatadas após inventário. `GEDI L4A` e `L4B` são checagens auxiliares, jamais rotulados como sensor SAR.
- **Robustez do acesso MPC:** `sar_pipeline._planetary_sign_asset` passa a tratar 429/500/502/503/504 e timeout com tentativas limitadas, `Retry-After` e jitter, sem misturar cenas/polarizações. Quando `Retry-After` exceder orçamento de espera, **não reconsultar antes da quota**. Há testes simulados, mas o processamento real e os runs de CI precisam ser comprovados. Não solucionar erro 401 contornando autenticação/licença; marcar status N/D.
- **Uso da terra:** MapBiomas valida cobertura por pontos interpretados visualmente com pesos; teste independente **somente** se esses pontos não integraram treino/tuning. Classe agrícola específica exige exemplos rotulados de cultura/ano/geometria, pesos e estudo de transferibilidade por cultura. Sem prova, mostrar `áreas cultivadas`; sem máscara atual confiável, mostrar indeterminado, não `sem cultivos detectados`.
- **Vigor:** classes `pouco vigorosa`, `vigor adequado`, `muito vigorosa` dependem de rótulos independentes ligados à cultura e fase, calibração de limiares SAR e comprovação da matriz de confusão. Não declarar fitossanidade real por mudança de retroespalhamento.
- **Safra:** série oficial PAM (2015–2024) + máscara de cultura independente + cenas SAR (tempo de aquisição e corte preditivo) + clima observado/disponível `as-of`; validar para N9 região/ano, e só extrapolar para talhão com medida real de produtividade do próprio domínio. Comparar lags+clima vs. lags+clima+SAR, em holdout espacial e temporal; erro MAE/RMSE/viés, bootstrap em blocos, intervalos com cobertura observada e análise de drift. Se ganho incremental/intervalo não demonstrado, **previsão bloqueada** é comportamento defensável, não modelo homologado.
- **Clima:** NASA POWER, INMET/BDMEP e CPTEC com distinção observação/reanálise/previsão e proveniência, datas, qualidade, unidades e latência. Combinação de fontes exige verificação de erros/correlações antes de pesos.

## 6. Plano de execução e prova de conclusão

1. Executar `Harvest public IFN field records` e `Audit IFN components` com registro de recursos realmente baixados (não apenas links); auditar licença, colunas/UA, presença real de coordenadas e suficiência por bioma/fitofisionomia.
2. Levantar produto de **incerteza** e relatório técnico PronaSolos; quando indisponível publicamente, solicitar autorização/documentação ou calcular resíduos com perfis abertos compatíveis, sem assumir mapa de incerteza inexistente. Condicionar estimativas publicáveis ao erro espacial.
3. Baixar GEDI L4A v3/L4B v2.1 e fontes SAR compatíveis em AOIs representativas, com hashes, qualidade e datas; unir apenas a inventários com coordenadas legalmente acessíveis.
4. Construir dataset independente por compartimento/bioma, com protocolo e métricas; priorizar Tapajós/Santo Ambrósio, Cerrado DF, Pantanal, Mata Atlântica e Caatinga. **Sem campo novo** é viável somente se as bases existentes fornecerem medições e metadados suficientes. A ausência é limitação real, não algo a completar artificialmente.
5. Implementar `validation/release_evidence.json` **somente quando cada registro referenciar relatórios e dados reais existentes**. O gate atual compara SHA e exige campos de proveniência, mas não verifica sozinho amostras, hashes em disco, licença ou conteúdo científico: acrescentar checagem de integridade dos anexos/holdouts e revisão científica independente antes do verde.
6. Executar `scientific-release-gate.yml` fail-closed e CI de regressões/benchmark. Somente após gate `homologated=true` demonstrado, construir e testar EXE/ZIP Windows com **mesmo SHA de código/científico**, checksum e link de download; manter PR #50 draft caso contrário.

**Status em 29/10/2026:** soluções e rotas **identificadas**; coletor SFB 2026 e testes foram adicionados ao código. Não há aqui resultados observacionais independentes suficientes nem evidência de homologação. **Não inventar valores, IC, coordenadas, artefato ou aprovações.**
