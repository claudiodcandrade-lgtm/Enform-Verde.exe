# Rotas para fechar a validação SAR × produtividade

Atualizado em 24/10/2026. Este documento distingue rotas implementadas de dados já adquiridos e resultados já validados. **Não há correlação SAR–PAM nem previsão de safra liberada por este plano.**

## Fontes e papel permitido

| Fonte/rota | Acesso e cobertura verificada | Uso permitido | Não pode sustentar |
|---|---|---|---|
| **YieldSAT** | Página oficial informa Brasil: 118 campos de milho, 293 de soja e 140 de trigo; 2017–2024. Dados de monitor de produtividade da colhedora, polígonos de campo inspecionados e Sentinel‑2; acesso por formulário do próprio dataset. | Referência independente de identidade de cultura e produtividade de campo. Associar, com auditoria de geometria/ano, à série Sentinel‑1 RTC independente extraída no MPC/CDSE/ASF. Avaliar transição S2→S1 e prever rendimento de campo apenas para os domínios cobertos. | Validar culturas ausentes, outras regiões sem amostras, ou provar sozinho transferência nacional. O fato de YieldSAT conter S2 não equivale a evidência SAR. |
| **CropHarvest** | Repositório aberto informa 95.186 pontos, incluindo rótulos multiclasses e binários, com subconjunto acompanhado por Sentinel‑1/Sentinel‑2/clima; licença CC BY‑SA 4.0 no repositório. | Pré-treino, comparação externa e teste exploratório de transferência, após auditar origem, país, cultura, ano e duplicatas. | Teste independente brasileiro automático: a coleção harmoniza 21 fontes e os rótulos têm origem/semântica heterogêneas; documentar subset e bloquear sobreposição espacial/temporal com treino. |
| **MapBiomas Agricultura** | Mapas e pontos de validação públicos; download nacional GeoTIFF ou recorte via GEE. | Pseudorrótulos para treino, estratificação e prior de cultivo com safra/coleção explicitadas. | Validação independente de modelo treinado, selecionado ou calibrado usando a mesma coleção/pontos. |
| **IBGE PAM/SIDRA — N9** | Série materializada: 8 produtos, 558 microrregiões, 2015–2024; variável 112 rendimento em kg/ha, mais produção e área. | Resultado regional real para associar com estatísticas SAR somente dentro de máscara de cultura independente, agregadas à mesma unidade e safra. Comparar baseline defasado, clima e clima+SAR. | Rótulo de pixel/talhão. Unidade histórica N9 requer harmonização territorial e safra/ano agrícola documentados. |
| **GloCAB/outros polígonos de talhão** | Referência complementar de geometria; atributos, licença e período variam por fonte. | Unidade espacial, buffer interno e amostragem. | Identidade de cultura ou produtividade sem atributo verificado de fonte independente. |
| **Calendário agrícola / fenologia** | Calendário oficial por município/região e cultura, combinado com datas publicadas em rótulos de campo quando disponíveis. | Definir fases/safras; especificar expectativa temporal antes de examinar o teste. | Inferir fenologia apenas da data da cena ou de regra global fixa. |
| **Sentinel‑1 RTC** | Rota MPC pública testada; há também adaptadores/alternativas CDSE e ASF. O novo `sentinel1_mpc.py` descobre páginas STAC, assina assets MPC em runtime e lê janelas COG com TLS verificado. | Acquisition datetime, VV/VH, órbita, geometria, nodata, cobertura, janela, estatísticas e proveniência por cena; o extrator zonal aceita polígono verificado. | Chamar ponto/janela de cultura; atribuir unidade física não declarada; declarar fenologia/cultura/atualidade validada só porque existe cena. |
| **Clima** | Fontes integradas existentes: INMET/BDMEP, NASA POWER, CPTEC, com resolução temporal/proveniência diferenciadas. | Baselines meteorológicos e covariáveis com período, variável, unidade e fonte. | Tratar reanálise como medição local ou confundir observado e previsão futura. |

Fontes: YieldSAT oficial https://yieldsat.github.io/ (dados via formulário indicado no site); CropHarvest https://github.com/nasaharvest/cropharvest e artigo https://openreview.net/forum?id=JtjzUXPEaCu; MapBiomas https://brasil.mapbiomas.org/downloads/; PAM https://apisidra.ibge.gov.br/; MPC https://planetarycomputer.microsoft.com/docs/.

## Rotas executáveis incorporadas

1. `agricultural_evidence_routes.py` contém catálogo de rotas, priorização por tarefa e impedimentos. A função `plan_evidence_routes()` nunca retorna `release_ready=True` automaticamente; pseudo-rótulo MapBiomas não recebe elegibilidade de validação independente.
2. `sentinel1_mpc.py` consulta o STAC RTC paginado por AOI e período, deduplica itens, obtém SAS temporário só em runtime, restringe hosts e abre COG via Rasterio com validação TLS. `extract_cog_point()` é diagnóstico pontual; `extract_cog_polygon()` calcula estatísticas VV/VH em polígono verificado e fração de pixels válidos. Nenhum deles classifica cultura: o rótulo independente vem da rota de referência separada. Segredos não entram em logs/manifestos.
3. `build_pam_sar_panel()` aceita PAM oficial e CSV de agregados SAR por `product_key × N9 × ano`; rejeita agregados sem status explícito de máscara independente aprovada, proveniência e hash do modelo. A flag é um contrato de entrada, não auditoria automática da aprovação. Exige uma tabela SAR válida, não fabricada.
4. `crop_map_training.py` segue sendo a rota de pseudorrótulo apenas para treino. `independent_sar_validation.py` calcula métricas de predições de campo em amostras separadas e audita origem/unicidade, sem converter MapBiomas em verdade de teste.
5. `crop_yield_modeling.py` aceita somente painéis com SAR para identidade, vigor, estresse inespecífico e clima, com splits espaço-temporais e calibração. `evaluate_yield_forecast()` exige ainda evidência atualizada e intervalo preditivo independente; sem isso abstém.

## Fluxo para ativar cada rota sem vazamento

### Identidade de cultura / máscara SAR

1. Obter o pacote YieldSAT por seu canal oficial; conferir licença, países/estados, safra, qualidade de mapa e termos de uso. Não automatizar envio de formulário nem contato a terceiros.
2. Para cada campo YieldSAT elegível, baixar Sentinel‑1 RTC público em MPC; quando indisponível, tentar CDSE GRD/OData e ASF HyP3/Earthdata. Guardar cena/data UTC, órbita relativa, polarização, footprint, fonte e hash dos features, nunca token.
3. Produzir amostras S1 apenas em interiores de polígonos verificados, remover bordas e áreas inválidas, separar por fazenda/grupo e safra antes de treinamento. Agricultura sem rótulo de cultura vira `área cultivada` ou abstenção.
4. Treinar modelos crop-specific. MapBiomas/CropHarvest podem ampliar treino/pré-treino, com `source_domain` preservado; excluir de teste qualquer unidade do mesmo rótulo/mapa/base.
5. Validar com campos YieldSAT que ficaram completamente fora do treino/tuning, por safra e agrupamento geográfico. Reportar matriz de confusão, precisão/recall/F1, calibração, IC por cluster, cobertura, classes não resolvidas e domínio. Se poucos grupos independentes ou transferência falhar, classe específica não é liberada.

YieldSAT tem trigo, milho e soja brasileiros. Para arroz, feijão, sorgo, café, cana e citros, procurar, em paralelo, registros georreferenciados de ensaios/parcelas, dados de cooperativas/colhedoras com licença, pesquisa Embrapa/universidades e campanhas publicadas; usar CropHarvest e mapas como treino/pre-treino. Uma fonte precisa conter identidade + coordenada/polígono + data/safra + rastreabilidade. Sem isso, não substituir por PAM ou mapa usado no treino.

### Série SAR e calibração de atualidade

1. Por AOI/fase, descobrir cada aquisição em MPC e consultar CDSE/ASF como fallbacks; deduplicar por plataforma, horário, órbita e footprint. Diferenciar aquisição, publicação e ingestão; não declarar latência com `published` nulo.
2. Baixar asset VV/VH com assinatura temporária em runtime; ler pixels na geometria agrícola elegível; checar CRS, nodata, escala/unidade, ângulo/orbita, qualidade e cobertura. Não misturar RTC e GRD sem harmonização documentada.
3. Definir fases antes do teste a partir de calendário agrícola verificável e janela de plantio/colheita dos campos com acesso. Para cada cultura/região/fase/órbita, calcular distribuição empírica de revisit gaps. Falha de cobertura e gap longo ficam registrados, não interpolados como aquisição.
4. Calibrar limite de idade pela degradação em holdout independente: testar horizonte/idade da última aquisição contra erro de fase/vigor e depois contra erro/intervalo de produtividade. Escolher limite com protocolo pré-registrado e aceitabilidade agronômica definida; reportar número de grupos/safras e IC agrupado. A cadência orbital observada sozinha não define limite biológico.
5. Até existir esse estudo, `threshold_source` deve estar ausente e o status de atualidade continua não definido; nem 12 dias nem qualquer limite global vira padrão.

### Associação e previsão de safra — dois produtos de validação

**Associação regional SAR–PAM:** agregar SAR apenas em pixels classificados por modelo crop-specific aceito; juntar PAM pela chave cultura × código N9 harmonizado × ano/safra; adicionar clima INMET/NASA/CPTEC e tendência. Comparar três modelos: produtividade histórica defasada; histórico+clima; histórico+clima+SAR. Fazer validação temporal futura e espacial em blocos inteiros, sem vazamento de vizinhos, preprocessamento ou decisões de features. Reportar n de N9 independentes e anos, correlação bruta e parcial, RMSE/MAE/viés, ganho contra baselines, IC bootstrap em blocos, análise de resíduos e falhas. Uma associação não é previsão.

**Previsão de campo:** para soja/milho (e trigo se campo/ano elegível), usar YieldSAT como rendimento observado com separação por campo/região/ano. Extrair SAR recente e clima de growing season; avaliar previsões emitidas em várias datas de corte (pré-plantio, emergência, florescimento, enchimento, pré-colheita) sem imagens posteriores ao `as_of`. Comparar SAR+clima com histórico+clima; quantificar calibração e cobertura de intervalos em holdout espacial e temporal. YieldSAT não fornece validação de safras posteriores a 2024. O alvo de campo e o alvo PAM regional são avaliações separadas.

## Critério de conclusão

Uma rota de dados só passa a “concluída” após download legal e auditável, manifestos sem segredos, contagens e hashes, pareamento de geometria/data/unidade, teste automático, resultados independentes e análise de viés/uncertainty. Até então o software deve exibir o status concreto (rota disponível, aguardando acesso, cenas sem cobertura, máscara em treino, validação insuficiente, atualidade não calibrada ou previsão bloqueada).

**Estado atual:** catálogo/planejador de rotas, adaptador MPC, assinatura temporária, leitura segura de pixels em ponto e polígono, junção auditável PAM×SAR e testes contratuais foram adicionados. As rotas YieldSAT, CropHarvest e MapBiomas estão especificadas com limites de uso. Ainda não há pacote de labels YieldSAT adquirido, máscara SAR validada, extração por lavoura, painel SAR×PAM real, limites temporais calibrados ou resultado de backtest. Portanto a pendência foi convertida em rotas e contratos de execução, mas a validação científica não deve ser anunciada antes de executar as etapas com os dados licenciados/reais.

## Campos de previsão no painel executivo

Na mesma área executiva, separada da auditoria, incluir as três leituras solicitadas e, no grupo **Previsão de safra**, os dois valores derivados:

- **Idade provável da lavoura:** exibir idade/dias apenas com fenologia SAR validada e status de atualidade `cenas_recentes_identificadas`.
- **Estado fitossanitário aparente:** apenas **Bom**, **Médio** ou **Ruim**, com modelo/avaliação e SAR atual validados; caso contrário “Indisponível”. Não é diagnóstico fitossanitário.
- **Produtividade provável:** `sacas/ha` com conversão explícita para saca de 60 kg quando esse for o padrão usual documentado para a cultura (soja, milho, café em grão, arroz em casca, feijão, sorgo e trigo); cana, citros e demais culturas sem padrão adequado permanecem em `t/ha`. Fonte/conversão fica na auditoria.
- **Produção provável:** produtividade provável × área efetivamente ocupada pela cultura dentro do polígono analisado. Exibir total em toneladas e, quando aplicável, equivalente em sacas de 60 kg. Propagar o intervalo preditivo para o total, condicionado à área fixa; se a área da cultura não estiver quantificada, exibir “Indisponível”, sem assumir que todo o polígono é lavoura.

Produtividade e produção só aparecem com `forecast_status="previsao_validada"` e limites de intervalo coerentes. Sem validação, exibir “Bloqueada”. O contrato de entrada usa `yield_t_ha`, `prediction_interval_t_ha` e `crop_area_ha`; a camada visual não estima nenhum desses valores.

## Painel executivo solicitado

Exibir, em leitura rápida e fora da trilha de auditoria, por unidade agrícola:

- **Idade provável da lavoura:** idade/dias apenas quando houver estimativa fenológica SAR validada e atualidade `cenas_recentes_identificadas`; do contrário “Indisponível”.
- **Estado fitossanitário aparente:** somente “Bom”, “Médio” ou “Ruim” quando classe, proveniência, validação independente e atualidade SAR forem adequadas. Caso contrário, “Indisponível”. Isso descreve sinal remoto aparente e não diagnóstico.
- **Previsão de safra:** exibir valor em t/ha e intervalo apenas com status `previsao_validada` e intervalo coerente; caso contrário, “Bloqueada”. Uma estimativa pontual sem calibração não aparece como previsão.

Fontes de dados, cenas e datas UTC, fase, versão/hash do modelo, métricas, critérios de atualidade SAR e motivos de abstenção permanecem em aba separada de auditoria. A visualização não calcula os indicadores: exige os contratos de status `crop_age_validation_status`, `phytosanitary_validation_status`, `sar_freshness_status` e `forecast_status` validados pelo pipeline.
