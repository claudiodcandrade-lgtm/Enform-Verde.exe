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

## Pendência de previsão de produtividade por cultura (revisão científica 24/10/2026)
- Busca internacional priorizando agricultura tropical: a melhor rota SAR + clima é arroz com série Sentinel-1 para área/início/fenologia acoplada ao modelo processual ORYZA/Rice-YES (IRRI/CGIAR; estudos validados em países asiáticos). Adaptar e validar no Brasil antes de qualquer saída local. MLER (arroz Jiangsu) e RicEns-Net (arroz Mekong) apoiam fusão SAR + óptico + meteorologia, porém não são pesos brasileiros conhecidos.
- Referências nacionais promissoras: APSIM + ML/clima/sensoriamento para cana em escala municipal (2026); modelo agrometeorológico por fases para café arábica (Embrapa, 14 anos examinados); modelo espectral-climático de café MODIS/ETA; estimativa climática por fase para citros; NDVI fenológico para feijão; SAR + óptico com monitor de produtividade para sorgo (duas safras/um local). SAFY-WB em milho é referência mecanística internacional, com limite declarado para SAR sem óptico.
- Soja e milho têm baselines meteorológicos/ópticos brasileiros e internacionais; VITA é clima, EUA, sem SAR. Nenhuma evidência encontrada valida previsão combinada SAR fenológico + clima dinâmico, em escala de talhão brasileira, para as oito culturas (soja, milho, sorgo, café, cana, arroz, feijão e citros).
- Próximo trabalho: por cultura reproduzir baseline climatológico e referência publicada; comparar SAR-only, clima-only e combinação/modelo de processo; usar validação bloqueada por ano e região e rótulos na mesma escala da saída; publicar MAE/RMSE/viés e intervalos preditivos. NASA POWER é referência de histórico recente; CPTEC é previsão futura. Só combinar previsões por pesos estimados em hindcasts coincidentes com covariância dos erros. Até validação local completa, não exibir estimativa numérica operacional de rendimento/produção.
- Evidências e fontes estão em `PRIORIDADE_MODELOS_PRETREINADOS_FENOLOGIA.md` e `BIBLIOTECA_CIENTIFICA_FENOLOGIA_CLIMA_SAFRAS_2026.md`. Esta busca é uma seleção direcionada, não uma revisão sistemática exaustiva.

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


## Atualização de continuidade — 24/10/2026, após correções do painel, meteorologia e vegetação nativa

### Última alteração e status verificado
- Último commit de código verificado: `833291007d234cd79fdc2e44e4cd1877433b9ca0`.
- Branch: `feature/agricultural-identification-native-carbon`; PR #50.
- Na consulta após esse commit, workflows `Dashboard dual - tests` (40121550836) e `Build Enform Verde Windows` (40121550784) estavam **em andamento**; consultar novamente antes de declarar sucesso.
- A compilação **anterior**, v3.24.40-CANDIDATE (run 40117129255), havia passado e possuía artefato Windows; **não confundir esse pacote anterior com as alterações recentes**. Só oferecer novo download após artefato da revisão atual comprovadamente gerado e validado.

### Correção do relatório de carbono — já codificada, validação pendente
- `executive_carbon_report.py` (commit 5907868) implementa `executive_carbon_lines` e `uncertainty_for_pool`.
- `desktop_app.py` (commit 6c5262d) insere **PAINEL EXECUTIVO** antes do relatório técnico; `tests/test_executive_carbon_report.py` testa unidades, intervalos e ausências; build gate modificado em 648a9ea.
- Preservar para cada compartimento densidade tC/ha, tCO₂e/ha, totais tC e tCO₂e, **incerteza absoluta em tC/ha e relativa em % quando quantificável**, fonte e significado estatístico. Nunca confundir desvio-padrão espacial, SD de produto e IC95%, nem somar incertezas heterogêneas para forjar IC do total.
- Tapajós — AOI de referência 1.290,69 ha; estoque parcial conhecido 262.202,00 tC (961.407,35 tCO₂e), 203,15 tC/ha. Exemplos da execução enviada pelo usuário: AGB 123,64 tC/ha (produto AGB_SD 126,75588 Mg/ha, conversão exploratória a 0,47: ±59,58 tC/ha, 48,19%, **não IC95%**); BGB 22,42 tC/ha (erro não quantificado); necromassa aérea 8,70 tC/ha (IC95% publicado 7,4–10,0; semiamplitude ±1,30, 14,94%, **sem erro de transferência**); serapilheira 2,33 tC/ha (intervalo em massa seca 3,0883–6,8117 Mg/ha; verificar fator de carbono compatível antes de afirmar IC convertido); solo 0–30 cm 46,06 tC/ha (SD espacial 2,07473 tC/ha, 4,50%, **não erro de predição**). Necromassa subterrânea não estimada e total parcial: lacunas científicas ainda não resolvidas.
- Testar o painel efetivamente renderizado no EXE, a exportação Excel e a consistência entre resultados por classe e por AOI. Evitar repetição de classes com 0,00 ha, blocos JSON brutos e dados técnicos no topo. O painel executivo deve anteceder auditoria/proveniência detalhada.

### Meteorologia — já codificada, consulta real e BDMEP pendentes
- Remover Climatempo completamente da interface, relatório e fontes propostas, pois requer contrato.
- `inmet_weather_client.py` mantém o conector e os testes de INMET para uso futuro, mas a consulta ao vivo em Tapajós achou A250 Santarém (~64 km) e não recebeu observações pelo endpoint público testado (HTTP 204). Não chamar esse caminho a cada atualização da interface até que exista rota pública funcional documentada.
- `desktop_app.py` prioriza NASA POWER para o monitoramento do histórico diário recente em grade e usa CPTEC/INPE como complemento para previsão futura, em produtos separados, preservando período, URL, hora e limitações. NASA POWER não é observação local; CPTEC não é histórico observado. INMET fica declarado como indisponível nessa consulta; BDMEP permanece sem integração automática. O uso comercial dos produtos CPTEC depende de autorização. `tests/test_inmet_weather_client.py` cobre seleção da estação e painel sem dados inventados.
- Consulta pública INMET testada sem observações (HTTP 204) em 24/10/2026; não tratar como fonte operacional. Retomar somente após obter endpoint oficial documentado e resposta com observações verificáveis. Investigar rota oficial e permissões de acesso BDMEP se um canal público suportado surgir.
- Previsão CPTEC deve deduplicar datas/períodos e não apresentar sete linhas repetidas como sete dias independentes. Usar números no padrão brasileiro (pontos milhares, vírgulas decimais) e resumo legível, deixando URLs e registros brutos na seção técnica.
- Dados ilustrativos enviados para Tapajós (NASA POWER 25/07–22/10/2026): temperatura média 30,83 °C, chuva 1.473,84 mm, GDD base 10 °C 1.887,94 °C dia, 89 dias com temperatura. Esses números não são nova consulta nem medição de estação INMET.

### Mensagem quando apenas vegetação nativa — codificada, testes pendentes
- Commit `8332910` alterou `_present_cultivated_monitoring` em `desktop_app.py`: quando a classificação tiver área nativa positiva, nenhuma área não nativa positiva e status não indicar erro, mostrar exatamente:
  **Não detectada a ocorrência de lavouras. Apenas vegetação nativa**
- Confirmar em testes com AOI totalmente nativa, AOI cultivada, AOI mista e AOI com cobertura desconhecida. **Não** exibir essa afirmação quando a classificação for inconclusiva ou houver pastagem, corpos d'água ou outros usos não nativos; nesses casos reportar o que é conhecido, sem inventar lavoura.
- Manter cálculo de carbono nativo independente da aba agrícola.

### Pendências científicas e de entrega ainda obrigatórias
1. SAR AGB/altura realmente validado para as fitofisionomias de todos os cinco biomas; ESA BIOMASS prioritária, sem usar RH98 como H100 incompatível e sem mascarar fallback bibliográfico como SAR.
2. Incertezas/erros de todos os compartimentos com metodologia verificável; não transformar dados insuficientes em precisão fictícia. Resolver raízes mortas, transferências microrregionais, necromassa, serapilheira e solo.
3. Classificadores efetivamente treinados/integrados para culturas, florestas plantadas e ILP/ILF/IPF/ILPF; evidência espacial e temporal, confiança, validação independente e abstenção.
4. Testes integrados reais para Tapajós, Santo Ambrósio, Cerrado, Pantanal, Mata Atlântica e Caatinga, sem regressão de mapas, rolagem, exportações, tC/tCO₂e e horários UTC/UTC−3.
5. Verificar workflows, corrigir falhas, obter artefato Windows **desta** revisão, fazer smoke test de painel executivo e meteorologia, disponibilizar link comprovado e atualizar novamente o prompt. Não declarar versão científica concluída sem evidências.

### Instrução operacional ao retomar
Começar inspecionando o HEAD atual e os dois workflows associados ao commit 8332910 ou posterior. Corrigir imediatamente testes ou build se falharem. Depois testar de ponta a ponta a renderização e os números dos painéis de carbono e meteorologia, verificar a mensagem exata para AOIs exclusivamente nativas e completar integração INMET/BDMEP dentro dos limites de acesso realmente existentes. Preservar funcionalidades anteriores. Prosseguir com as pendências científicas, sem confundir implementação parcial com validação concluída.

## Regra obrigatória para previsão de safra — 24/10/2026
- Previsões numéricas de produtividade (t/ha), produção (t) e intervalos somente podem ser liberadas por modelo matemático cientificamente robusto, implementado e validado independentemente, integrando **identificação da cultura via SAR**, indicadores de **vigor**, indicadores **fitossanitários** e **climatologia** pertinente à cultura/região/fase fenológica/safra.
- Identificação SAR deve demonstrar classificação por cultura com validação espacial e temporal; vigor deve ter indicador mensurável e validado; fitossanidade deve usar indicadores com validação agronômica, sem confundir anomalia de sensoriamento remoto com diagnóstico de doença; clima deve informar fonte, cobertura, lacunas e escala temporal. Exigir compatibilidade e tratamento de dados ausentes.
- Modelo integrado precisa apresentar dados independentes de validação, calibração regional e por cultura, erro de previsão (MAE, RMSE, viés e intervalos com cobertura empírica, quando disponíveis), limites de aplicabilidade, proveniência e rastreabilidade.
- Se **qualquer requisito** faltar, **bloquear cálculo e exibição de previsão numérica**, sem inventar valores ou usar modelo bibliográfico não operacional. Pode apresentar dados descritivos, mas claramente separados de previsão.
- Commit 4c71c43: a interface explicita bloqueio; isso **não constitui implementação do modelo integrado**. Implementar futuramente motor central de autorização da previsão e testes que rejeitem entradas ausentes, não validadas e fora do domínio, incluindo outras rotas de exportação/API, não apenas texto de interface.

### Ajuste obrigatório — fitossanidade exclusivamente remota via SAR
- Não haverá coleta nem entrada de dados de campo para a AOI. Os indicadores fitossanitários admitidos no motor de previsão são **exclusivamente padrões de retroespalhamento, coerência, polarimetria, séries temporais e/ou textura SAR** que possam sugerir alterações de vigor/estrutura/umidade associáveis a estresse, dentro da capacidade demonstrada do sensor e do modelo. Não exigir observações de campo da propriedade.
- Não classificar padrões SAR como diagnóstico inequívoco de doença, praga ou deficiência nutricional; seca, fenologia, manejo, inundação e geometria de aquisição podem produzir assinaturas semelhantes. Relatar **anomalia SAR indicativa de possível estresse**, com confiança, qualidade temporal e fatores de confusão, ou **não determinado**.
- Validação científica externa pré-existente (artigos, conjuntos de referência independentes, modelos testados) pode ser usada para estabelecer desempenho e domínio de aplicação; não pressupor amostras locais. Se não houver evidência independente transferível para cultura, sensor, clima e região, abster-se.
- A previsão de safra continua bloqueada até haver modelo integrado, implementado e validado, que combine cultura identificada via SAR, vigor remoto, padrões indicativos SAR de estresse e climatologia, com métricas de erro de produção. Não substituir ausência de evidência por valores arbitrários.
- A alteração de interface correspondente foi registrada no commit edb0ca6; faltam motor central, validação e testes ponta a ponta.

## Estado da correção candidata v3.24.41 — 24/10/2026
- O branch de trabalho é `feature/agricultural-identification-native-carbon`, PR #50. Não mesclar nem declarar sistema agrícola cientificamente concluído sem pesos/modelos reais validados no Brasil.
- Correção implementada: MapBiomas `Pastagem` permanece como classe distinta; culturas cartográficas sem distinção independente ficam em `Áreas cultivadas`. A consulta meteorológica agora inicia automaticamente somente quando há classe de cultivo positiva e preserva o relatório agrícola. Respostas atrasadas de uma AOI anterior são descartadas.
- Fonte licenciada removida: Climatempo não deve aparecer em interface, relatório nem registro de fontes. Prioridade: NASA POWER para dados históricos recentes em grade; CPTEC/INPE para previsão futura, sujeito a atribuição e autorização para uso comercial. A consulta pública INMET testada não trouxe observações; a interface declara essa limitação e não insiste no endpoint. BDMEP é histórico diário/convencional; o portal oficial entrega CSV mediante solicitação por e-mail, e esta versão não automatiza essa solicitação nem apresenta BDMEP como observado.
- Pedido de agregação estatística: não formar média única entre NASA POWER e CPTEC, pois o primeiro fornece histórico recente e o segundo previsão futura, sem datas comuns no produto atual. Não atribuir pesos arbitrários. Se fontes futuras tiverem variável/unidade/período comparáveis, pesos devem vir de erro fora da amostra por região/época e considerar dependência/covariância entre produtos; enquanto não houver validação independente, reportar fontes e dispersão separadas.
- Algoritmos: Random Forest SAR configurável e calibrado já existe no fluxo geral de uso do solo, mas depende de GeoTIFF SAR e amostras independentes fornecidas; não há pesos brasileiros nacionais embutidos. Embrapa/UERJ U-Net (Sentinel-2), RF Embrapa/Unicamp do Maranhão e PlanetScope/deep learning estão registrados como candidatos, não como inferência executável do aplicativo. O S2-PhenoCNN tem pesos públicos, porém é Sentinel-2 e foi treinado/avaliado no nordeste da China; usar apenas como benchmark óptico. Nenhum desses métodos atende sozinho à exigência de identificação SAR para previsão de safra.
- O artigo brasileiro de previsão de soja com RF/SVR e dados de sensoriamento/clima é baseline de pesquisa, não modelo integrado de safra para o sistema: não usa identidade SAR nem indicadores fitossanitários e sua validação municipal não autoriza previsão por talhão. Continuar pesquisa bibliográfica direcionada; não declarar cobertura exaustiva.
- Versão candidata alterada para `3.24.41-CANDIDATE`; novos testes cobrem a identificação de classe cultivada, pastagem sem cultivo e remoção de Climatempo. A interface agenda consulta apenas para classes de cultivo positivas. Antes de disponibilizar, conferir novo workflow Windows no commit atualizado; o build v3.24.40 é obsoleto para esta revisão. O ambiente local não contém `geopandas`, então `tests.test_native_carbon` e `tests.test_land_use_sar` precisam ser confirmados no CI Windows.
- Pendências científicas inalteradas: nenhuma classificação específica de cultura, detecção fitossanitária SAR ou previsão numérica de safra está validada/operacional; não liberar previsões até completar cadeia de imagem, modelo, referência independente, métricas e incerteza.
