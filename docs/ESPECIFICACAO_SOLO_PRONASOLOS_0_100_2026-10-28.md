Warning: truncated output (original token count: 32858)
Total output lines: 802

<!-- V88_16_NATIONAL_RESULT_WITH_UNCERTAINTY -->
## V88.16 — resultado nacional com incerteza e estado auditável (12/11/2026)
Objetivo obrigatório: para qualquer AOI do Brasil, concluir cada módulo com o melhor resultado cientificamente sustentado ou estado N/D/ERRO_TECNICO, sempre com fonte, período, cobertura, método e incerteza. Quantificar incerteza quando suportada por dados/desenho amostral; caso contrário declarar “incerteza não quantificada” e motivo, sem inventar precisão ou converter N/D em zero.

Hierarquia: preservar AOI original, CRS, hash, run_id e versão; verificar pixels reais (catálogo não equivale a leitura); priorizar altura SAR diretamente medida (ESA BIOMASS FH quando adequada); para biomassa integrar equações publicadas com altura SAR, distribuição diamétrica e área basal média de inventários compatíveis, favorecendo parcelas da AOI, microrregião/região e mesma fitofisionomia. Alternativa experimental requer fundamento, sensibilidade/validação, fontes e rótulo experimental. Para agricultura, SAR atual precede MapBiomas histórico e PAM agregada; quando cultivo for sustentado mas espécie não, indicar “área cultivada”.

Ausência SAR só pode ser certificada depois de busca/paginação/leitura completas e zero pixels adequados sem erro. Falhas de autenticação, rede/TLS, timeout, paginação, decodificação, leitura, dependência ou interrupção são ERRO_TECNICO; retentar, testar rotas tecnicamente diferentes e corrigir na mesma AOI. Não acionar contingência para esconder falha. Contingência de carbono/altura usa inventários nacionais microrregionalizados/regionais da mesma fitofisionomia com tratamento estatístico e incerteza, rotulados como estimativa indireta. Incerteza ausente de suporte deve ser declarada como não quantificada.

No Excel, a aba Gráficos contém linha de fustes/ha por DAP, parâmetros/tabela de área basal média, linha de altura SAR (ou média de inventário da mesma fitofisionomia apenas com ausência certificada) e barras das dez espécies dominantes; todas as fontes, unidade, período e condição observada/fallback. Bloquear regressão de sobreposição dos dados auxiliares DAP com a área D:E do painel de altura. O dashboard valida run_id/hash, aceita estados por módulo e mostra divergência de áreas como não reconciliada, sem atribuí-la a uma classe ou carbono.

Estado do PR #51: branch patches-3.26.6, HEAD 88b463813665dfb6b82071b39c24913864af37b4, draft/não mesclado. A correção do teste de separação DAP/altura passou nos seis testes direcionados locais; no último status, dashboard e build Windows estavam em execução, smoke semântico SAR e contrato rápido passaram, gate científico falhou. O código declara 3.26.21, mas descrição do PR continua 3.26.16. A Fazenda Maria Eduarda integral, ciclo app→dashboard, áreas raster-vetor e validação nacional permanecem pendentes. Não afirmar conclusão ou homologação até evidência no mesmo SHA e AOI integral.


<!-- V87_94_WINDOWS_BUILD_AND_REAL_OPTICAL_SMOKE -->
## V87.95 — build Windows final 3.26.16 no commit b70894e (11/11/2026)
- Run Windows `43050581961` concluiu verde no SHA `b70894e1796121027aaaf09c00a533d131e5a749`. Artefato Actions `Enform-Verde-Windows-v3.26.16-PRECAMPO-EXPERIMENTAL`, ID `13871576858` (533.400.808 bytes, SHA-256 ZIP `1abc923ed7133ce259c1130b5b7be729c827226891e52e5739aab82777b7d4f6`); SHA-256 do EXE `66c17b8d8fad210a9e3aa92e16a05e3d11d3c4655d0b8722e2477f7958a6cc97`.
- Teste do EXE em cópia limpa, paridade Python/Windows, padrão visual e network-check TLS ativo passaram. Aceite SAR KMZ Tapajós: `SAR_PROCESSADO`, 1.290,69 ha, 302.348 pixels, 5 cenas; não houve AGB quantitativa (`fallback_agb_mg_ha=null`). Prova operacional limitada ao fixture, sem validação de campo.
- Smoke óptico nacional amostral: 11/11 AOIs com pixels válidos (CBERS-4A em 9, Sentinel-2 fallback em 2); renderização CBERS worker→canvas Tk passou em janela de Sinop. Não é prova exaustiva do Brasil nem processamento do KML integral da Fazenda Maria Eduarda.
- Gate científico segue reprovado. ESA BIOMASS FH leu pixels em Sinop, mas não houve cobertura FH confirmada para as AOIs de alta biomassa de Tapajós. Manter carbono/altura/agricultura da propriedade sem alegação de resultado aferido até executar o KML integral no Windows e obter validação independente.

## V87.94 — build Windows, leitura óptica em amostras nacionais e limites da prova (11/11/2026)
- Fonte do executável testado: SHA `a1a11b1e406af0d322c5697222012403c92735ba`; versão `3.26.16-PRECAMPO-EXPERIMENTAL`; artefato Actions `Enform-Verde-Windows-v3.26.16-PRECAMPO-EXPERIMENTAL`, ID `13867841475`, 533.397.855 bytes. O EXE passou compilação, runtime, self-test em pasta limpa, network check e aceite SAR com AOI de Tapajós. SHA-256 do executável: `95aa798b72ddcafc9c962ffd338b5cf7f7e4740488ed325fde7ee710c8e2631f`.
- Build Windows restaurou o mapa IBGE offline de um pacote anterior; mapa/quadrantes verificados. Alterada a regra do workflow para não publicar release automaticamente de branch/PR; o artefato experimental permanece disponível como artefato temporário de Actions. Publicação em release deve ocorrer em fluxo explícito a partir de `main`.
- Smoke óptico real em 11 pontos distribuídos pelos biomas/extremos: pixels ópticos carregados em 11/11 AOIs de teste, com cobertura mínima observada >=95%; CBERS-4A primário em 9/11 e Sentinel-2 de fallback nos demais, incluindo a janela amostral de Sinop. CBERS-4A também passou pela rota worker→canvas Tk em Sinop. Isso não é prova exaustiva de todos os pixels/épocas do Brasil nem teste do KML integral de 1.459,91 ha.
- Prova SAR independente em Sinop: 30 cenas Sentinel-1 RTC VV/VH e 1.692 pixels numa janela de teste de 1.084,73 ha; polígonos cobrem 1.079,26 ha. É uma inferência experimental para a safra 2025/26, não representa a fazenda completa, não foi aferida em campo e não deve sustentar estoques de carbono. A leitura real de pixels ESA BIOMASS FH em Sinop também passou, sem demonstrar cobertura nacional.
- A suíte de regressão do dashboard passou; o job ainda reprovou exclusivamente o gate que exige prompt e Word após a última alteração efetiva do workflow. Este checkpoint e os quatro documentos sincronizados neste commit corrigem a ordem documental. O gate científico independente continua reprovado, portanto manter o piloto como EXPERIMENTAL, sem alegar homologação, calibração regional ou uso decisório.
- Pendências que permanecem: executar o KML integral de Sinop no Windows do usuário, conferir imagem e relatórios nesse perímetro, observar estimativa de carbono por compartimento e agricultura nesse KML, obter validação independente de campo. Não transferir áreas da janela de teste para a propriedade.

<!-- V87_89_UNMEASURED_UNCERTAINTY_LABEL_AND_TRACE -->
## V87.89 — incerteza não mensurada e trilha de cálculo
- Quando a incerteza necessária de um resultado de carbono não puder ser quantitativamente sustentada, usar o rótulo literal “estimativa com incerteza não mensurada” e declarar o que é conhecido e desconhecido.
- Sempre registrar fontes, filtros, unidades amostrais, equações, conversões, área-base e valores intermediários. DP de parcelas não substitui erro de transferência ou de composição de carbono.
- Esta regra não altera o carbono do solo: continuam obrigatórios Embrapa/PronaSolos, interseção espacial e estoque 0–100 cm sem extrapolação.

<!-- V87_87_IFN_CONDITIONAL_CARBON -->
## V87.87 — separação do cenário de inventário IFN do compartimento de carbono do solo
- Commit `d26a4f8`; versão `3.26.14-PRECAMPO-EXPERIMENTAL`, incluindo CSV/módulo no pacote Windows.
- A nova contingência de inventários SFB/IFN aplica-se somente ao cenário condicional de biomassa/carbono da vegetação potencial IBGE quando o gate confirma ausência de pixels SAR utilizáveis. A classificação atual permanece não confirmada e falha técnica bloqueia o fallback.
- O valor estadual/regional IFN não altera carbono do solo, profundidade ou cobertura. O compartimento de solo continua restrito a Embrapa/PronaSolos, interseção espacial e profundidade 0–100 cm; perfil raso, fertilidade e cenário de biomassa não substituem essa medição/modelagem.
- A conversão AGB→carbono do cenário usa fator 0,47 com incerteza não quantificada e não é combinada com carbono do solo nem apresentada como IC95%.
- Se a incerteza total da estimativa não puder ser declarada, usar a expressão **“estimativa com incerteza não mensurada”** e anexar a trilha do cálculo. O DP entre unidades IFN é uma medida descritiva parcial e não substitui a incerteza de transferência ou do fator de carbono.

<!-- V87_86_EXECUTABLE_SAR_ALGORITHM_PORTFOLIO -->
## V87.86 — Arquitetura científica de algoritmos SAR executáveis e estado da arte (10/11/2026)
- Prioridade a métodos publicados e testados por Embrapa, UnB, universidades brasileiras e institutos internacionais: Random Forest, SVM e KNN para imagens SAR multitemporais; LSTM/CNN/Transformer, WorldCereal/Presto, DSSAT e AquaCrop apenas quando a execução, os pesos, as entradas e licenças estiverem realmente implantados.
- IMPLEMENTADO AGORA: `sar_algorithm_portfolio.py`, com treinamento de Random Forest (300 árvores), SVM-RBF e KNN, GroupKFold por grupos espaciais, avaliação comparativa balanced accuracy/macro-F1 e matrizes de confusão, treinamento e inferência experimentais com pesos salvos apenas mediante matrizes reais rotuladas e proveniência. **Não inventar amostras de campo nem usar mapas históricos como verdade-terreno.** Validação cruzada não equivale a validação de campo independente.
- `tests/test_sar_algorithm_portfolio.py`: todos os 3 modelos são efetivamente treinados no contrato sintético de CI, rejeitando grupos/feições inadequados e pseudo-rótulos. `desktop_app.module_check()` confirma presença dos modelos no Windows congelado sem alegar que já estão calibrados.
- O RF brasileiro SAR já instalado é a rota operacional anterior; o portfólio é uma rota adicional **treinável**, condicionada a dados de treinamento e validação regional. Não relatar um novo classificador como implantado em Sinop se nenhum peso regional foi gerado.
- O encadeamento obrigatório permanece aquisição ótica CBERS/S2 → pixels SAR RTC → identificação nativa/cultivada → fitofisionomia IBGE por interseção somente em nativa → compartimentos de carbono e monitoramento/vigor/safra com incerteza. A falha `UnicodeDecodeError` do KML Fazenda Maria Eduarda ainda exige teste real Windows antes de declarar a correção definitiva.
- Versão de build **3.26.13-PRECAMPO-EXPERIMENTAL**; notas `APP_RELEASE_NOTES_v3.26.13.md`; documentação técnica completa no checkpoint `docs/spec_updates/2026-11-10_v87_86_sar_algorithm_portfolio.md`; Word completo V87.86.

<!-- V87_85_1_GUI_AND_IBGE_REGRESSION_FIX -->
## Checkpoint V87.85.1 — ajuste dos testes SAR × IBGE e da GUI Windows
- A regressão Windows havia falhado com os testes antigos que exigiam a classe genérica `Formação savânica` e o título `Fitofisionomias presentes na propriedade:` mesmo depois da regra nova nomear `Savana Arborizada` por interseção SAR × IBGE.
- Contratos atualizados: `tests/test_sar_landcover_lemplus.py` exige `SAR_EXPERIMENTAL_MODELO+IBGE`, classe de soja continua não nativa e fechamento de áreas; `tests/test_v82_national_ci_contract.py` e contrato `GUI contract test` do build exigem o texto `Fitofisionomias (SAR atual / potencial IBGE):`. Não mudar a nova semântica apenas para passar um teste obsoleto.
- Etapas ainda obrigatórias: regressão completa, compilação EXE e autodiagnóstico Windows, leitura real de pixels CBERS-4A/Sentinel-2 e Sentinel-1 na AOI completa da Fazenda Maria Eduarda (1.459,91 ha), classificação nativa/agricultura e estimativas experimentais de carbono sem dados inventados. O novo build não prova funcionamento local por si só.
- Detalhes e histórico: `docs/spec_updates/2026-11-10_v87_85_native_sar_ibge_intersection.md`. Sincronização Word V87.85 pelo workflow oficial.

<!-- ENFORM_V87_85_SAR_NATIVE_IBGE_INTERSECTION -->
## V87.85 — Máscara de vegetação nativa SAR e fitofisionomia IBGE por interseção (10/11/2026)
- Identificar a **presença atual** de vegetação nativa com cenas **SAR Sentinel-1 RTC VV/VH realmente lidas**, apoiando-se na diferenciação de padrões temporais e estruturais entre formações naturais e cultivos, com modelo aplicável. Usar ESA BIOMASS conforme cobertura/compatibilidade para estrutura/altura; não usar IBGE nem MapBiomas como sensor atual.
- Confirmada uma **máscara SAR modelada**, intersectar seus polígonos apenas de vegetação nativa com IBGE **legenda_1** em EPSG:6933, usando recorte geométrico exato e denominador AOI, para nomear cada fitofisionomia. Não nomear a cultura/pastagem com classes nativas, não converter floresta potencial IBGE em presença atual, não preencher lacunas por proximidade.
- O modelo SAR instalado experimental deve permanecer explicitamente **SAR_EXPERIMENTAL_MODELO+IBGE** após nomeação; **sem validação independente na AOI**, essa classificação NÃO equivale a confirmação de campo. A estimativa de carbono calcula cada compartimento apenas sobre as áreas nativas SAR mapeadas, em caráter experimental com fontes, incerteza e N/D quando ausentes. Não inventar estoques nem declarar IC95% sem dados.
- Monitoramento agrícola usa exclusivamente área cultivada identificada pelo classificador SAR para identidade cultural/vigor; caso sem evidência de cultura específica, relatar **área cultivada — cultura N/D**; sem pixels legíveis, distinguir **ERRO_TECNICO** de inexistência de cenas.
- Corrigir fluxo `land_use_sar.name_native_from_ibge` e `native_carbon.native_class` para que os polígonos nativos SAR experimentais recebam nome IBGE por interseção e sejam reconhecidos no painel nativo sem perder o indicador experimental.
- Testes `tests/test_native_sar_ibge_intersection_experimental.py` com sobreposição parcial, não nomeação de agricultura e proibição de inferir nativa por IBGE sem pixels. **A avaliação completa do KML da Fazenda Maria Eduarda, 1.459,91 ha, no Windows ainda é pendente.**
- Release em desenvolvimento: **Enform Verde 3.26.12-PRECAMPO-EXPERIMENTAL**. Histórico e detalhes: `docs/spec_updates/2026-11-10_v87_85_native_sar_ibge_intersection.md`. O Word completo deve ser sincronizado para **V87.85**.

<!-- ENFORM_V87_84_SINOP_WINDOWS_RECOVERY -->
## V87.84 — Correção dos erros reais Sinop 1.459,91 ha (10/11/2026)
- **Causa operacional observada:** 12 cenas MPC Sentinel-1 RTC selecionadas, 24 leituras VV/VH falhas por `UnicodeDecodeError` no Windows (byte 0xe3); marcar `ERRO_TECNICO`, não `AUSENCIA_CENAS`. Sem máscaras atuais, carbono nativo e agricultura permanecem N/D até processamento efetivo.
- **Recuperação experimental SAR:** acrescentada terceira tentativa com assinatura individual de ativo e GDAL HTTP/1.1 sem HEAD nem multipart range, preservando pixels medidos e registro de cada falha; monitorar empiricamente se a falha nativa foi resolvida.
- **Imagem óptica CBERS-4A/S2:** parâmetros GDAL COG sem multipart; corrigida comparação de tamanho canvas × imagem, que disparava novos carregamentos; relatório de falhas por provedor em `~/.enform_verde/ultimo_diagnostico_imagem_otica.json`, URLs de assinatura ocultas.
- **Fitofisionomias:** exibir referência `Floresta Estacional Sempre-Verde` explicitamente como *potencial IBGE*, não confundi-la com vegetação nativa presente no momento. Não inferir 100% de floresta da legenda IBGE.
- **Testes adicionados:** `tests/test_sinop_windows_recurring_failures.py` para regras SAR/ótica/UI, **mas não comprova operação no KML completo**. A validação Windows, classificação, carbonos por compartimento, vigor agrícola e previsão devem ser ensaiados em campo/remote sensing auditável sem números fabricados.
- Especificação Word completa recebe este checkpoint por `docs/spec_updates/2026-11-10_v87_84_sinop_windows_recovery.md`; preservar histórico.


<!-- V87_83_CI_SYNC_FINAL_20261110 -->
## Checkpoint V87.83 — sincronização final do release 3.26.11
- Token ESA MAAP atual emitido em 08/11/2026 (informação fornecida pelo proprietário); prazo nominal 90 dias; aviso a partir de 22/01/2027; vencimento estimado 06/02/2027.
- O Enform Verde deve manter campo mascarado para introdução/substituição do token, abrir a página oficial de renovação e registrar apenas a data de emissão. Uma data de renovação posterior prevalece sobre a emissão inicial.
- Paridade Python/EXE Windows exige mesmos resultados dos diagnósticos de modelos SAR, água, produtividade, PronaSolos e PAM, além de provas reais de pixels ópticos e SAR. Homologação científica e ensaio integral da Fazenda Maria Eduarda permanecem gates independentes.
- Este checkpoint sincroniza os três documentos obrigatórios depois da última alteração do workflow; a especificação Word completa já foi sincronizada para V87.83.
<!-- ENFORM_V87_83_MAAP_ISSUED_NOV08 -->
## V87.83 — Data confirmada do token ESA MAAP ativo (10/11/2026)
- O proprietário confirmou explicitamente que o token ESA MAAP **atual foi emitido em 08/11/2026**. Essa informação refere-se à data de emissão, não revela o token e não comprova seu estado atual junto ao servidor.
- Validade nominal **90 dias corridos**: prazo estimado em **06/02/2027**. Aviso nos últimos 15 dias: a partir de **22/01/2027**. Essas datas são estimativas locais; um erro 401/403 ou revogação requer renovação imediata mesmo antes delas.
- `esa_maap_token_renewal.initialize_current_token_date` registra **uma única vez** a emissão 2026-11-08 ao abrir a GUI, apenas se ainda não houver registro e o prazo de 90 dias não tiver terminado. Nunca sobrescrever data posterior informada em «REGISTRAR DATA DE EMISSÃO / RENOVAÇÃO» e nunca presumir validade dessa data inicial em nova instalação após o prazo.
- O local `~/.enform_verde/esa_maap_token_renewal.json` armazena somente data, esquema e validade nominal; o token é mantido somente em memória no campo mascarado e **SUBSTITUIR TOKEN** limpa seu conteúdo antes de aceitar outro. «RENOVAR TOKEN NO PORTAL ESA» abre o portal oficial https://portal.maap.eo.esa.int/ini/services/auth/token/ .
- Testar **2026-11-08 → 2027-02-06**, primeiro alerta em 2027-01-22, inicialização idempotente, renovação posterior prevalecendo e ausência de suposição de token ativo após expirar. Empacotar no Windows; CI e teste local da interface são provas distintas.

<!-- ENFORM_V87_82_MAAP_TOKEN_RENEWAL -->
## V87.82 — Renovação ESA MAAP e substituição segura de token (10/11/2026)
- **Fonte oficial:** o ESA MAAP Long-Lasting / Offline Token tem validade nominal de 90 dias. A renovação é manual após autenticação do usuário no portal documentado https://portal.maap.eo.esa.int/ini/services/auth/token/ . Não criar nem transmitir automaticamente um novo segredo.
- **GUI / desktop_app.py:** na aba SAR, manter campo de entrada mascarado `ESA MAAP Long Lasting Token`; adicionar botões «RENOVAR TOKEN NO PORTAL ESA», «SUBSTITUIR TOKEN» (apaga o token anterior da variável de interface e foca o campo para colar o novo) e «REGISTRAR DATA DE EMISSÃO / RENOVAÇÃO» (informa data AAAA-MM-DD). Após colar o token, esse segredo fica somente em memória para uso no processamento; não deve ser logado, persistido no projeto nem enviado para servidores não ESA.
- **Vencimento:** módulo `esa_maap_token_renewal.py`, prazo estimado de 90 dias corridos a partir da data real de geração e alerta nos últimos 15 dias ou após o vencimento. Na abertura do aplicativo perguntar se deseja abrir a página oficial quando EXPIRED/EXPIRING_SOON. Quando emiss…22858 tokens truncated… aba `Comparação AGB IFN`. Se FH+estrutura local já estimar AGB, a comparação CCI/IFN não aparece como segunda estimativa da área. Outras regiões sem dados AGB compatíveis permanecem N/D; a base estrutural expandida não autoriza por si só extrapolação para Mg/ha.
- CCI: mantém média zonal da camada de AGB e incerteza do produto; `C=0,47×AGB`, estoque=`C×área nativa SAR`, e `tCO2e=tC×44/12`. A incerteza do produto não equivale a validação local.
- A versão candidata passa a 3.26.64-PRECAMPO-EXPERIMENTAL. O fluxo completo de relatório/Excel, a análise da geometria integral da Fazenda Maria Eduarda e os gates Windows ainda precisam ser exercitados no SHA final; não declarar homologação.
## V88.129 — vigor no modelo vigente, referências de inventários e imagem óptica (17/11/2026)

Versão candidata: `3.26.64-PRECAMPO-EXPERIMENTAL`.

- **Previsão de safra:** preservar o modelo de painel PAM + FAO-56/FAO-33 que já era usado. A vigor SAR contemporânea, quando datada e com cena válida, deve alterar a distribuição de rendimento condicionando a seleção Monte Carlo dos tercis de resíduos históricos PAM. O relatório registra `used_in_yield_distribution`, probabilidades empregadas e medianas dos resíduos por classe. Sem vigor válido, o modelo segue com a distribuição histórica completa e informa explicitamente a razão. Não ativar WOFOST, Gamma challenger ou outro candidato nesta versão.
- **Identificadores agrícolas:** manter os identificadores existentes para soja, milho, cana, arroz, café, citros e algodão; a análise não rotula uma cultura quando o identificador não passa seus gates. O uso de vigor no cálculo de safra é separado da classificação semântica da cultura.
- **IFN e biodiversidade:** consultar a base expandida por localização, bioma e `legenda_1` IBGE. Exibir as dez espécies de maior frequência entre as unidades amostrais elegíveis, contando presença por UA, com frequência percentual, unidade amostral, fonte e limitações. É um indicador fitossociológico descritivo, não um índice completo de biodiversidade; os registros IFN não são transformados em densidade/ha ou AGB sem área, pesos de expansão e modelo compatível.
- **Comparação de carbono:** quando CCI for a rota quantitativa efetiva e houver cinco UAs compatíveis, mostrar a referência AGB IFN separadamente, com média, DP entre UAs, amplitude, distância e incertezas não quantificadas. Não somar ao estoque CCI. FH × parâmetros horizontais segue prioritário somente nos domínios com coeficientes suportados; fora deles, registrar N/D e mostrar as contingências disponíveis. Registros agregados publicados (incluindo Embrapa Amazônia Oriental, Embrapa Semiárido, UFV, UnB e outros constantes no catálogo) servem como referências quantitativas/qualitativas apenas após harmonizar bioma, fitofisionomia, unidade, escala e tipo de incerteza. Catálogo não significa base já baixada ou operacional.
- **Fundo óptico:** remover o mapa raster IBGE como fallback de apresentação. IBGE vetor continua sendo referência analítica para a fitofisionomia. O mapa de fundo exige imagem óptica real; CBERS‑4A/WFI é prioridade, Sentinel‑2 é rota seguinte e NASA GIBS/Esri/cache óptico são alternativas visuais. Se tudo falhar, mostrar falha com diagnóstico por provedor, sem simular sucesso com mapa IBGE ou perímetro. Gate Windows exige pixels da fonte óptica realmente visíveis no canvas Tk e recorte integral dentro da tela. O teste em onze pontos deve falhar se algum local não retornar pixels ópticos de CBERS, Sentinel‑2, GIBS ou Esri.
- **Desempenho:** a validação integral da base IFN passa a ser cacheada por caminho, tamanho e `mtime_ns`, evitando repetir contagens integrais nas análises da mesma sessão. A base de 841.387 observações continua no pacote: não a remover sem instalar uma alternativa externa versionada, pois isso tornaria as referências IFN indisponíveis. A leitura em quadrantes dos COGs ópticos e o checksum do vetor IBGE cacheado são mantidos. A origem dos 16 minutos precisa ser medida por fase em execução com AOI comparável; não atribuir ao mapa raster IBGE que não é mais usado como fundo.
- **Escopo e gates:** a geometria privada integral da Fazenda Maria Eduarda não está neste checkout; usar o centróide público para testar o pipeline visual não equivale a processar o KML da fazenda. Esta candidata só pode ser distribuída após suíte local, checker de coleta e workflow Windows passarem no SHA final. Build ou smoke visual aprovado não equivale a homologação científica.
# Nota de integração V88.131 (17/11/2026)

A auditoria do carbono nativo preserva a proveniência por estrato e não deve reportar como “IFN não carregado” uma consulta IFN concluída. A correção não altera os métodos, fontes, profundidades ou incertezas do compartimento de carbono do solo descritos nesta especificação. Os diagnósticos de altura FH e imagem óptica permanecem fora do método de solo.

## Nota V88.135 (17/11/2026)

A correção da auditoria e formatação do painel agrícola não modifica as fontes, profundidades, modelos ou incertezas de carbono do solo especificados neste documento. Sua inclusão atende à sincronização documental da candidata 3.26.65, sem alterar os cálculos do compartimento solo.

## Nota V88.138 (18/11/2026)

O smoke live de carbono FH e vigor não modifica o método do compartimento solo. A fonte PronaSolos continua separada das estimativas de biomassa e sua variabilidade espacial não deve ser chamada de IC95% ou erro de predição. Esta nota sincroniza a especificação às mudanças efetivas auditadas no mesmo ciclo.

## Nota V88.139 (18/11/2026)

A correção do escopo temporal da busca de cenas Sentinel‑1 para vigor agrícola não altera o método do compartimento solo, suas fontes, profundidades ou incertezas. As rotas MPC e INPE precisam concluir a busca antes de declarar ausência de cena; falha de catálogo permanece erro técnico. Esta nota sincroniza a especificação documental sem modificar o cálculo do solo.

## Nota V88.140 (18/11/2026)

Ajustes em fixtures e expectativas de regressão da busca de vigor não alteram o método, fontes, profundidades ou incertezas do carbono do solo. Mantêm-se os gates do produto e a separação entre compartimentos.


## Sincronização V88.142 — apresentação dos resultados agrícolas e executivos (18/11/2026)

Os quadros executivos devem estar no início das abas/relatórios e permanecer separados da trilha de auditoria. A atualização assíncrona de clima não pode remover do quadro agrícola o vigor e seu efeito no modelo de safra. A interface informa participação apenas quando `vigor_model_audit.used_in_yield_distribution=true`, junto com classe/probabilidades, amostragem, data da cena e safra da máscara. N/D e não confirmação devem manter o motivo visível.

Teste live Sinop confirmou uma amostra de soja em uma cena Sentinel‑1 RTC de 12/11/2026: aproximadamente 8 ha, seis referências e 2,456% de cobertura da máscara SAR retrospectiva 2025/2026; auditoria confirmou uso condicional do vigor nos resíduos PAM×clima. É evidência experimental de integração, não validação agronômica nem comprovação de cultura atual. Build Windows e handoff final continuam sujeitos aos gates do SHA; não elevar o status científico por esta amostra.

## Nota V88.143 (18/11/2026)

A remoção da exceção no fluxo de apresentação do monitoramento agrícola não modifica métodos, fontes, profundidades ou incertezas do compartimento carbono do solo.


## V88.143 — atualização para 3.26.66-PRECAMPO-EXPERIMENTAL (18/11/2026)

A correção dos quadros executivos e da apresentação do vigor condicionando a previsão foi incorporada. A versão da aplicação foi incrementada de 3.26.65 para 3.26.66-PRECAMPO-EXPERIMENTAL. A versão 3.26.65 compilou e passou o autoteste Windows em pasta limpa; a regressão integral teve 1.271 testes OK e o gate documental passou após sincronização. Esses resultados pertencem ao SHA 3.26.65; a versão 3.26.66 requer novos gates de regressão, build/autoteste e handoff live.

A homologação científica independente permanece reprovada por ausência de validação de campo independente. Manter explicitamente o status pré-campo/experimental; não declarar release homologada. A auditoria live Sinop confirma integração condicional do vigor da soja, sem validar cultura atual ou transferência da máscara retrospectiva 2025/2026.

## Nota V88.144 (18/11/2026)

O compartimento solo e seus métodos não mudam. A regra sistêmica que afeta a apresentação do total mantém a estimativa AGB prioritária separada das referências CCI/IFN. Erro técnico na rota ESA BIOMASS FH não pode promover CCI ou inventários a estimativa selecionada; a auditoria deve identificar causa, rota e estado incompleto. Permanecem as regras de incerteza e de não somar referências independentes.


## Nota V88.144a (18/11/2026)

O workflow live do handoff SAR inclui mudanças em `sar_pipeline.py` nos gatilhos push/PR, para validar a saída de carbono que alimenta os relatórios junto das alterações de prioridade de AGB. Sem alteração metodológica do solo.

## Nota V88.145 (18/11/2026)

A comparação ESA CCI × inventários deve consultar todas as fontes de AGB numéricas harmonizadas e compatíveis, sem restringir a comparação ao IFN. Referências publicadas ficam separadas por fonte; não se calcula média conjunta quando desenho, unidade amostral, domínio espacial ou incerteza não forem comparáveis, e nenhuma referência paralela é adicionada ao estoque CCI. Fontes presentes apenas em catálogo ou microdados sem harmonização espacial/fitofisionômica e denominador amostral não sustentam AGB/ha; sua incorporação quantitativa segue pendente até harmonização. Esta atualização não altera métodos ou profundidade do carbono do solo.

O handoff live no SHA `b8972bf` concluiu Sinop e falhou na etapa seguinte do Tapajós com `TypeError` ao comparar contagem de pixels FH nula no payload do dashboard. A contagem nula é normal quando não há pixels FH válidos; deve ser tratada como zero para a decisão de status, preservando `None` e a auditoria original nos detalhes. Correção e regressão adicionadas; aguardam nova execução no SHA posterior. Sem mudança nos métodos do solo.


## Nota V88.146 (18/11/2026)

A correção de transporte dos arquivos GTDX e de leitura dos produtos FH não altera as fontes, profundidades, métodos ou incertezas do carbono do solo. Link de acesso inválido, erro de autenticação, falha de download ou falha de leitura de raster deve ser reportado como erro técnico; não comprova ausência de pixels e não autoriza substituir a mensuração prioritária por CCI ou inventários. A comparação paralela ESA CCI × inventários abrange fontes quantitativas harmonizadas compatíveis de todo o registro, sem ficar limitada ao IFN, e continua separada do estoque CCI.

A candidata 3.26.68-PRECAMPO-EXPERIMENTAL aguarda suíte integral, handoff live, build e autoteste no mesmo SHA; esta nota não declara liberação nem validação científica.

## Nota V88.147 (18/11/2026)

A auditoria live do SHA `49c2f17` confirmou leitura ESA BIOMASS FH dentro do KML Tapajós (1.263 pixels válidos, sem erro técnico) e processamento até o dashboard. Ela também detectou conflito de proveniência: a altura medida vinha de FH, mas o objeto de AGB ESA CCI fornecia rótulo e caminhos apresentados no quadro de altura. A interface e a planilha passam a preservar o produto FH/GTDX dentro do campo de altura, deixando a origem ESA CCI apenas nos campos de AGB. CCI é produto multissensor de AGB e nunca deve ser mostrado como mensuração de altura.

Esta correção não altera método, profundidade ou fontes do carbono do solo. A comparação paralela de inventários consultou o registro completo; sem UAs ou agregados compatíveis para a tipologia do smoke, manteve N/D. A candidata 3.26.69 segue pré-campo enquanto seus gates completos e autoteste do EXE aguardam novo SHA.

## Nota V88.148 (18/11/2026)

O smoke live do SHA `3999058` confirmou a separação de origem: FH foi apresentado como altura (H100, pixels e raster ESA BIOMASS) e CCI como AGB, sem misturar seus caminhos ou rótulos. A etapa live seguinte transporta os mesmos campos para a auditoria executiva `height_inventory_routes`. Esta mudança não altera fontes, método ou profundidade de carbono do solo.

A consulta de comparação agora informa separadamente rotas de inventário pesquisadas, fontes existentes no registro harmonizado, correspondências exatas e fontes utilizáveis. Isso evidencia quando todo o registro foi consultado sem produzir referência compatível e mantém N/D quando bioma/fitofisionomia/unidade não sustentam comparação. Não muda o método do solo.

Candidata 3.26.70-PRECAMPO-EXPERIMENTAL; regressão/handoff anteriores aprovados em SHA anterior, build/autoteste e gates da revisão final ainda devem passar no SHA que contém estas alterações.

## Nota V88.149 (18/11/2026)

O autoteste Windows anterior detectou bloqueio técnico da rota FH/GTDX no EXE. A investigação localizou a causa no workflow: a etapa de prova MAAP tinha o segredo ESA configurado, mas o processo de aceite do executável não o recebia. O passo de aceite agora recebe o token offline por variável protegida; o pipeline utiliza essa variável quando não há token explícito. Erros de autenticação permanecem técnicos e não são tratados como ausência de cobertura. Sem alteração de métodos, profundidade ou fontes do carbono do solo.

A candidata 3.26.71 aguarda os gates finais no novo SHA.


## V88.151 — interface com calibração de biomassa radicular

Carbono/biomassa de raízes permanece compartimento separado do carbono orgânico do solo (0–100 cm). A conversão de AGB em biomassa abaixo do solo deve usar equação ou razão raiz:parte aérea publicada para a formação e domínio adequados, com fonte e incerteza. A especificação edáfica não autoriza usar carbono do solo como proxy de raízes, nem somar raízes mortas novamente quando a equação incluir raízes vivas e mortas. Na versão examinada, a rotina de carbono ainda usa Cairns et al. como aproximação ampla para formações florestais altas; a seleção por fitofisionomia e sua incerteza completa são pendência explícita, não calibração local.


## V88.152 — integração do Painel SFB/IFN

A ingestão do Painel SFB/IFN inclui referências de AGB e equações empregadas no cálculo. O campo `valor_r` do painel representa um fator raiz/parte aérea informado pela metodologia do SFB, não uma equação alométrica de raízes. Carbono do solo 0–100 cm continua independente. Para raízes, o sistema deve priorizar equações alométricas publicadas aplicáveis ao estrato; usar `valor_r` somente como fator de expansão compatível, declarando a fonte e sua dispersão, sem chamar o fator de alometria calibrada.


## V88.153 — métrica H100 e carbono do solo

ESA BIOMASS FH é H100, média de altura das 100 árvores mais altas por hectare. Alturas IFN podem formar a referência de campo se a área amostrada e a identidade de árvore forem conhecidas, a densidade amostral cobrir o equivalente a 100 indivíduos/ha e a fitofisionomia estiver validada. Esse pareamento calibra a leitura de altura SAR; não modifica nem substitui carbono do solo 0–100 cm. O erro de altura deve ser propagado ao modelo AGB e reportado separadamente do erro edáfico.


## V88.157 — auditoria de continuidade do release (18/11/2026)

O código em validação está no SHA `894835bae7fdf35a972efe652f95a79ce55e413f`. Correção recente normaliza datas IFN e trata datas vazias sem falha de agregação; testes específicos foram adicionados. Esta mudança de ingestão não altera os métodos pedológicos nem comprova uma nova análise de solo.

O workflow independente científico segue bloqueando homologação por ausência de evidência de validação de campo. O build Windows, SAR live e dashboard ainda estavam em execução na materialização/teste da base IFN, sem novo executável/checksum publicado. Preservar o status pré-campo/experimental. Não converter falha técnica em ausência de dados nem inferir cobertura/estoques sem resultado observável. Para qualquer cenário ou camada pedológica, conservar fonte, profundidade, cobertura e incerteza conforme as seções existentes desta especificação.


## V88.158 — continuidade após falha do transporte (18/11/2026)

A ingestão IFN e o crosswalk concluíram: 841.387 observações em 8.951 UAs, com correspondência única à IBGE legenda_1. O job Windows falhou no CSV SFB porque o servidor interrompeu a conexão antes dos últimos 45.819 bytes. Correção adiciona streaming, retentativas limitadas, resume por Range com Content-Range e validator ETag/Last-Modified, reinício quando Range é ignorado, verificação de tamanho e escrita atômica após validação do CSV. Cinco testes locais passaram; a correção aguarda CI.

Timeouts do probe PronaSolos em três AOIs são indisponibilidade técnica de um passo opcional (continue-on-error), não evidência de ausência de dados. A homologação científica segue bloqueada; nenhum novo EXE foi publicado. Aplicar as diretrizes FH/AGB e contingências já registradas na seção V88.157 sem afrouxá-las.

### Nota de checkpoint V88.160 (18/11/2026)
Esta alteração é restrita à consulta e apresentação de referências de inventários para biomassa aérea e estrutura horizontal. Não modifica fontes, métodos, profundidade, equações ou incerteza do carbono do solo. A regressão completa local passou (1.288 testes; 1 ignorado) com base IFN espacial materializada; aguarda-se o workflow Windows no SHA atualizado.


## Nota V88.162 — processamento ESA CCI

Alteração exclusiva do agendamento da contingência AGB: o raster ESA CCI não é consultado/baixado antes do gate FH/GTDX e calibração CCI–inventário. Esta mudança não modifica método, dados, profundidade, equações ou incerteza do carbono orgânico do solo 0–100 cm. Biomassa radicular permanece compartimento separado e a estimativa total do solo não substitui nem serve de proxy para raízes.


## Nota V88.164 — aceite Tapajós

A compatibilidade hierárquica foi corrigida somente na listagem comparativa de inventários AGB; não altera métodos, fontes, profundidade ou incerteza do carbono no solo. Referências agregadas não integram o estoque da AOI nem substituem compartimentos.

## Nota V88.165 — indexação de inventários

O cache e a seleção SQLite sob demanda otimizam exclusivamente o acesso às fontes de inventário usadas para referência de AGB/estrutura. Não modificam fonte, método, unidade, profundidade, incerteza ou compartimento do carbono do solo (0–100 cm), que permanece independente de biomassa radicular.

A geração automatizada da cópia Word versionada V88.165 não altera os métodos ou resultados edáficos.

### Nota de sincronização Word V88.166
O teste integral encontrou a capa do DOCX canônico ainda na versão anterior, embora o checkpoint tivesse sido inserido no histórico. O sincronizador agora substitui o estado e a versão da capa automaticamente; essa correção documental não modifica fonte, método, unidade, profundidade ou incerteza do carbono orgânico do solo. O novo gate Windows permanece pendente até a regressão e o build terminarem no SHA corrigido.

## Nota V88.166 — empacotamento da evidência de inventários

A correção posiciona o registro agregado de inventários no runtime congelado do PyInstaller e melhora o diagnóstico do aceite. Não altera fonte, unidade, profundidade, método ou incerteza de carbono orgânico do solo de 0–100 cm; raízes permanecem compartimento separado.
