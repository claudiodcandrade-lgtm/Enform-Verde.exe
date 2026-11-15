Warning: truncated output (original token count: 100565)
Total output lines: 1747

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
- **Vencimento:** módulo `esa_maap_token_renewal.py`, prazo estimado de 90 dias corridos a partir da data real de geração e alerta nos últimos 15 dias ou após o vencimento. Na abertura do aplicativo perguntar se deseja abrir a página oficial quando EXPIRED/EXPIRING_SOON. Quando emissão desconhecida, exibir UNKNOWN sem afirmar validade. O registro local contém somente `schema`, `issued_on` e `validity_days` (não grava token, senha nem hash de token).
- **Estado científico:** a renovação da credencial não implica existência de cenas ou capacidade automática de estimar altura/AGB; distinguir 401/403 de catálogo vazio e erros técnicos. Consultas públicas ESA MAAP permanecem preferenciais quando não requerem autenticação.
- **Testes:** `tests/test_esa_maap_token_renewal.py` cobre expiração dia 90, aviso dia 75, desconhecido, ausência de persistência do token e presença dos controles de substituição na interface Python/Windows. Testes do EXE compilado e validação em PC do proprietário permanecem obrigatórios.

<!-- ENFORM_V87_81_PYTHON_WINDOWS_PARITY -->
## V87.81 — Paridade observável entre Python e EXE Windows (10/11/2026)
- O fato de `python desktop_app.py` executar não garante que o bundle Windows tenha dependências, modelos, certificados, dados ou caminhos corretos. A validação é separada do gate científico e da verificação do usuário.
- O motor `module_check` agora precisa carregar efetivamente o RF SAR `data/models/sar_brasil_rf_v2.joblib`, comparar SHA-256 com o manifesto, verificar o ciclo histórico 2025/2026 de 12 meses e exercitar coeficientes do balanço hídrico da soja; importar o módulo não é suficiente.
- O workflow captura o resultado dos mesmos módulos executados diretamente pelo Python antes do build e no `Enform Verde.exe --module-check` extraído em pasta limpa. Compara igualdade de versão, estoque solo raster 0–100, proibição de evidência sintética pré-campo, microrregião PAM e dez anos, matriz de produtividade, modelo RF SAR e balanço hídrico. Diferença ou chave ausente bloqueia o ZIP.
- O fluxo existente também exige `--ui-smoke`, `--visual-check`, `--network-check` (pixels ópticos CBERS-4A ou Sentinel-2 e SAR Sentinel-1), `--acceptance-test` Tapajós e SHA/checksum. Esses testes são verificações distintas; resultados quantitativos na fazenda inteira, classificação de cultura por safra e homologação em todos os biomas ainda requerem prova observacional.
- Escopo e lacunas: paridade dos submódulos explicitamente comparados NAO equivale a paridade de TODAS as funcionalidades; auditar no Windows em AOIs reais de diferentes biomas, falha de rede, tokens, CBERS/S2, SAR VV/VH, estimativas completas de carbono, água e safra. O modelo RF anual é retrospectivo e experimental.
- O pacote final só pode ser chamado de funcional após CI completa aprovada no SHA exato, EXE Windows acessível e teste real no KML Sinop FAZENDA_MARIA_EDUARDA.kml, sem resultados de uso/vegetação falsamente definidos por IBGE.
<!-- V87_80_NETWORK_ACCEPTANCE_2026_11_10 -->
## V87.80 — Correcao do gate Windows e regressao optica/SAR (10/11/2026)
- **FALHAS OBSERVADAS NA CI 3.26.11:** compilacao interrompida no contrato GUI devido a verificacao literal do antigo titulo singular; regressao completa identificou quatro falhas: titulo singular, dois testes antigos que proibiam a contingencia Esri e especificacao DOCX sem a versao atual. Nao confundir falha de contrato com falha de pixels, nem esconder qualquer falha real de teste.
- **TESTES CONSERTADOS:** workflow build-windows e testes test_v82_national_ci_contract, test_nasa_gibs_keyless, test_sentinel2_scene_failover_contract alinham o titulo plural «Fitofisionomias presentes na propriedade» e exigem a nova rota Esri somente apos CBERS-4A, Sentinel-2 e NASA VIIRS, como contexto optico e nunca insumo de classificacao.
- **WORD HISTORICO SINCRONIZADO:** workflow Sync V87.79 full Word specification foi aprovado e publicou o DOCX completo com 3.26.11, sem apagar historico. V87.80 complementa o DOCX para documentar a correção do autoteste de rede.
- **AUTO-TESTE DO EXE:** network_check nao exige mais exclusivamente CBERS-4A; aceita leitura real CBERS-4A OU Sentinel-2 Earth Search/MPC. A rota Sentinel-1 usa sign_asset_href do servico MPC, sem token SAS global obrigatorio, mantendo verificacao TLS. Teste continua exigindo pixels reais nas amostras de Sinop e deve falhar se os dados forem inacessiveis.
- **ACEITE:** nao liberar EXE Windows como funcional ate obter build/teste do mesmo SHA, autoteste limpo, prova real de imagens opticas e pixels SAR no Windows e teste no KML INTEGRAL 1.459,91 ha da Fazenda Maria Eduarda. Prova do piloto em pequena caixa de Sinop nao valida a propriedade inteira. Estoques de carbono de vegetacao nativa permanecem N/D sem mascara nativa elegivel, e previsao de safra permanece experimental/condicional.
- **LIMITACOES:** homologacao cientifica nacional segue independente e bloqueada quando faltam dados reais de campo. Nao substituir ausencia por zero, nao inventar IC95, nem interpretar a classificacao da safra 2025/26 como cobertura novembro/2026.
<!-- ENFORM_CHECKPOINT_V87_79_REAL_WINDOWS_REGRESSION -->
## V87.79 — Regressão Windows real, correções incorporadas e piloto 3.26.11 (10/11/2026)

- **BASE DA REGRESSÃO:** o usuário testou o KML `Sinop FAZENDA_MARIA_EDUARDA.kml`, AOI 1.459,91 ha (EPSG:6933), centroide -11,872667/-55,190498. O EXE 3.26.10 NÃO abriu CBERS-4A nem Sentinel-2, NÃO produziu máscara SAR de cobertura, classe agrícola, vigor nem carbono; a entrega 3.26.10 NÃO foi aprovada operacionalmente pelo proprietário.
- **EVIDÊNCIA SAR:** foram encontradas 12 cenas MPC elegíveis, com 24 tentativas VV/VH e zero leituras válidas; mensagens UnicodeDecodeError, falha TOKEN_REFRESH, RasterioIOError /vsicurl. Trata-se de ERRO_TECNICO e não de ausência de cenas, floresta ou culturas.
- **CORREÇÕES DE ACESSO:** `sentinel1_mpc.py` incorpora assinatura individual autorizada `sign_asset_href`, independente do SAS global; `recent_sar_landcover.py` e `sar_landcover_lemplus.py` usam contingência e novas tentativas de leitura raster. Proteger URLs SAS/tokens em logs. Testes de assinatura foram incluídos, mas só leitura no KML integral comprova correção no Windows.
- **ÓPTICO:** `desktop_app.py` tenta CBERS-4A/WFI → Sentinel-2 Earth Search → Sentinel-2 MPC → NASA VIIRS para contexto → mosaico Esri World Imagery de data/sensor N/D, antes da contingência cartográfica. Esri e VIIRS não alimentam classificação, vigor nem carbono. Não confundir mosaico de referência com Sentinel-2 recente. O teste de tela do Windows do proprietário continua pendente.
- **MAPEAMENTO E MODELO:** o modelo `data/models/sar_brasil_rf_v2.joblib` e seu manifesto são empacotados no PyInstaller; o alerta sobre modelos opcionais no diretório do usuário não significa necessariamente ausência do RF embutido. O RF anual 2025/26 NÃO prova cultura de novembro/2026. Na falta de máscara contemporânea datada, manter N/D para cobertura atual; permitir mapa SAR experimental retrospectivo explicitamente rotulado e cenários condicionais de safra conforme documentação.
- **CARBONO:** regressão real teve todos os compartimentos N/D por ausência de área nativa atual defensável; não atribuir ao imóvel a área cartográfica IBGE (99,41% floresta) nem transformar N/D em zero. Recuperar cálculos anteriores somente quando fontes observacionais e máscaras elegíveis justificarem os estoques, com incerteza, compartimentos e rastreabilidade. Solo 0–100 cm permanece separado, exigindo os horizontes adequados; verificar por que ficou N/D apesar de haver rasters de fertilidade disponíveis.
- **RELATÓRIO/GUI:** rótulo atualizado para «Fitofisionomias presentes na propriedade»; removida duplicação de «Outros usos» com falso 0,00 ha no caso de cobertura desconhecida.
- **VERSÃO:** novo número `3.26.11-PRECAMPO-EXPERIMENTAL` para não adulterar tag/artefato imutável 3.26.10. Não disponibilizar novo ZIP como funcional sem build Windows e autoteste no SHA idêntico, leitura óptica em tela, pixels SAR na AOI real, classificação auditável, carbono e agricultura coerentes.
- **EVIDÊNCIA EM CI:** live SAR de Sinop com dados reais passou em uma janela de teste menor que a fazenda; ESA BIOMASS FH real já foi observado. Essas provas NÃO substituem AOI privada integral nem validação independente. Homologação científica permanece separada.
- **COMPROMISSO DOCUMENTAL:** preservar histórico e sincronizar prompt, especificação, notas de release e código. Não preencher lacunas com evidências sintéticas ou IC95 fabricados. Estado técnico da build 3.26.11 deve ser verificado no commit final antes da entrega.

<!-- ENFORM_CHECKPOINT_V87_77_WINDOWS_REGRESSION -->
## V87.77 - checkpoint ESA MAAP e piloto experimental (2026-11-10)

- V87.77 — build 3.26.10 no SHA e77310ba falhou: regressao geral 1037 testes com 3 falhas e 1 erro, e build Windows reprovou teste nativo; portanto ZIP NAO liberado. Corrigidos contrato de identidade atual vs anual, fixtures de ausencia de modelo SAR, e campo scenario_intervals_are_not_CI95 no modulo hidrico.
- CLASSIFICACAO ATUAL vs EXPERIMENTAL RETROSPECTIVA: crops_in_land_result retorna exclusivamente SAR_VALIDADO; experimental_crops_in_land_result retorna exclusivamente SAR_EXPERIMENTAL_MODELO. monitoring_forecast utiliza estimativa historica apenas para PREVISAO CONDICIONAL, nunca identifica cultura atual com ela. Origem e incerteza de transferencia aparecem no relatorio.
- TESTE CI: tests/test_current_mapping_contract agora assegura as duas rotas distintas; tests/test_crop_forecast_experimental_sar_contract agora verifica que RF anual NAO entra como classe contemporanea; testes sem modelo mockam especificamente o classificador RF embutido, sem inferir falta do modelo por ausencia de arquivo adicional instalado.
- AGUA SOLOS: scenarios retorna campo scenario_intervals_are_not_CI95=True para demarcar que seco/central/umido nao e IC95. Preserva a necessidade de fonte real de solo e clima, n/d na ausencia dos dados e cenarios etiquetados como modelados.
- SUITE e build no mesmo commit sao obrigatorios, incluindo MAAP FH real, …85565 tokens truncated…amais podem ser usados para apresentar vigor atual específico da cultura; se forem a única fonte de espécie/área, a previsão fica condicional e separada do vigor genérico atual.
- A classe candidata deve ser obtida do vetor SAR corrente ou, quando a vetorização for omitida por fragmentação, recuperada do raster SAR classe 2. Dados MapBiomas não participam dessa seleção. A implementação precisa passar testes de contrato e integração no SHA exato antes de distribuição; não considerar observações de teste ou referências de inventário como validação de campo.
- Compatibilidade de apresentação: quando vigor não puder ser estimado, manter o cabeçalho visível **“Vigor: N/D”** seguido do motivo e do estado SAR condicional; esse texto não confirma cultura nem vigor.
## V88.32 — registro de validação da apresentação N/D (13/11/2026)
- A regressão encontrada na suíte completa foi somente de texto de painel: manter “Vigor: N/D” com o motivo SAR quando não houver cálculo. O ajuste não altera estimativa de solo nem habilita confirmação de cultura ou vigor. A suíte e o build do SHA corrigido permanecem como gates.
## V88.33 — contrato de contingência de carbono separado do SAR (13/11/2026)
- No build do SHA `784b29fafe76a19bb4b631b11aff4dec86121703`, a falha ocorreu porque um teste antigo exigia ausência de `literature_reference` mesmo depois de esgotadas as rotas de biomassa SAR, apesar de não haver `agb_mg_ha` quantitativa. A saída preservou SAR auxiliar e referência regional de inventário em campos separados; ela não converteu inventário em AGB SAR.
- O teste do build passa a exigir `agb_mg_ha=None`, fonte `SAR_ATRIBUTOS_ESTRATIFICADORES`, gate elegível, e referência de inventário com origem própria, `sar_processed=false` e trilha SAR vazia. Rotas técnicas ainda não esgotadas não liberam contingência; falhas e ausência de cobertura continuam diferenciadas.

## Controle de escopo V88.35 — transporte SAR e estados independentes (13/11/2026)

A candidata 3.26.25 trata de transporte/leitura de COG Sentinel-1 e publicação de estados parciais do pipeline. Não altera dados, fontes, método, profundidade de 0–100 cm, incerteza nem cálculos de carbono orgânico do solo. O estoque do solo continua independente de erro ou indisponibilidade de imagem óptica/SAR.
- O gate Windows da candidata passou a testar também a rota HTTPS local de pixels Sentinel-1; essa alteração não afeta a metodologia nem a estimativa de carbono orgânico do solo.


## Controle de escopo V88.36 — recuperação da leitura SAR (13/11/2026)

Esta atualização não altera os métodos de carbono do solo ou fertilidade. Registra apenas que o fallback SAR pode recuperar a leitura por recorte limitado da AOI quando o COG integral exceder o limite de transferência ou falhar por assinatura, transporte ou resposta inválida. Erro persistente continua ERRO_TECNICO e não autoriza substituir SAR por uma contingência de ausência. Testes locais: 1.135 aprovados e 1 ignorado. O workflow Windows validou a leitura SAR real no EXE após corrigir o contador de pixels; esta correção não altera os métodos de solo ou fertilidade. A homologação científica e o teste ponta a ponta do KML Maria Eduarda permanecem pendentes.

# V88.40 — parsing resiliente do XML de capacidades PronaSolos

## Diagnóstico

O estoque SOC Embrapa/PronaSolos de 0–100 cm foi calculado, mas a leitura das camadas WCS de incerteza parou em `ParseError: reference to invalid character number`. O erro ocorre antes da descoberta das dez camadas (limite inferior/superior para cinco horizontes). Ele caracteriza conteúdo de resposta inválido para XML 1.0, não ausência de serviço ou credencial. Não zerar incerteza nem eliminar o estoque já calculado por esse erro secundário.

## Correção de software

Antes do `ElementTree.fromstring`, inspecionar referências numéricas XML e remover somente aquelas cujo código Unicode não pertence à produção `Char` do XML 1.0. Preservar referências válidas e todo o restante da resposta. O hash SHA-256 da resposta WCS original e a quantidade de referências removidas entram na proveniência. Respostas truncadas, estruturalmente inválidas ou sem as dez camadas continuam como `ERRO_TECNICO`/N/D; nunca são interpretadas como ausência confirmada.

Após a descoberta, manter os contratos existentes: baixar limites inferior e superior para os cinco horizontes, validar formato GeoTIFF, CRS, resolução, NoData, grade alinhada, cobertura da AOI e conteúdo dos rasters. Repetir somente falhas transitórias com tentativas limitadas e TLS validado. Enquanto qualquer requisito falhar, manter estoque SOC quando disponível e exibir sua incerteza como N/D com motivo específico. O envelope marginal publicado não deve ser rotulado como IC95% conjunto.

## Teste e limites

Teste de regressão: referência inválida `&#x0;` é removida, referência XML legal `&#x20;` permanece, e o identificador de cobertura reparado é descoberto. A suíte completa e os workflows devem ser reportados pelo SHA exato antes de atualizar o branch. A candidata 3.26.26-PRECAMPO-EXPERIMENTAL continua pré-campo experimental, não homologada; não declarar resultado de incerteza até leitura de dados reais passar no runtime.

# V88.40 — parsing resiliente do XML de capacidades PronaSolos

## Diagnóstico

O estoque SOC Embrapa/PronaSolos de 0–100 cm foi calculado, mas a leitura das camadas WCS de incerteza parou em `ParseError: reference to invalid character number`. O erro ocorre antes da descoberta das dez camadas (limite inferior/superior para cinco horizontes). Ele caracteriza conteúdo de resposta inválido para XML 1.0, não ausência de serviço ou credencial. Não zerar incerteza nem eliminar o estoque já calculado por esse erro secundário.

## Correção de software

Antes do `ElementTree.fromstring`, inspecionar referências numéricas XML e remover somente aquelas cujo código Unicode não pertence à produção `Char` do XML 1.0. Preservar referências válidas e todo o restante da resposta. O hash SHA-256 da resposta WCS original e a quantidade de referências removidas entram na proveniência. Respostas truncadas, estruturalmente inválidas ou sem as dez camadas continuam como `ERRO_TECNICO`/N/D; nunca são interpretadas como ausência confirmada.

Após a descoberta, manter os contratos existentes: baixar limites inferior e superior para os cinco horizontes, validar formato GeoTIFF, CRS, resolução, NoData, grade alinhada, cobertura da AOI e conteúdo dos rasters. Repetir somente falhas transitórias com tentativas limitadas e TLS validado. Enquanto qualquer requisito falhar, manter estoque SOC quando disponível e exibir sua incerteza como N/D com motivo específico. O envelope marginal publicado não deve ser rotulado como IC95% conjunto.

## Teste e limites

Teste de regressão: referência inválida `&#x0;` é removida, referência XML legal `&#x20;` permanece, e o identificador de cobertura reparado é descoberto. A suíte completa e os workflows devem ser reportados pelo SHA exato antes de atualizar o branch. A candidata 3.26.26-PRECAMPO-EXPERIMENTAL continua pré-campo experimental, não homologada; não declarar resultado de incerteza até leitura de dados reais passar no runtime.


# V88.41 — acesso SAR recente do INPE e contingência com pixels reais (13/11/2026)

O usuário reforça que dados SAR recentes são fundamentais tanto para carbono quanto para monitoramento de lavouras e previsão de safra. A regra temporal operacional é: a aquisição SAR mais recente usada como evidência atual na AOI deve ter até 30 dias. Séries para fenologia podem abranger até 150 dias, desde que a aquisição final tenha até 30 dias e as datas/órbitas sejam auditadas. Sem observação recente, mostrar N/D/ERRO com motivo; não reaproveitar uma cena antiga como monitoramento atual.

A busca multiprovedor Sentinel-1 consulta MPC e INPE RTC e ordena as cenas por aquisição. A nova rota do pipeline de carbono lê diretamente VV/VH de COGs da coleção pública INPE `sentinel-1-rtc-1`, em TLS verificado e recorte na AOI. A rota realiza também a leitura INPE mesmo quando MPC obtém pixels, para comparar datas reais; apenas descoberta de catálogo não conta como processamento. MPC, INPE e CDSE recebem janela temporal de 30 dias nas consultas instantâneas.

O teste de aceitação live `tools/probe_inpe_sentinel1_rtc_live.py` deve obter ≥100 pixels válidos em VV e VH na mesma cena, tanto para Sinop quanto para o AOI KMZ do Tapajós, e registrar cena/data/CRS/contagem sem URL assinada. O `--network-check` valida leitura VV/VH com data dentro de 30 dias. Séries do módulo agrícola permanecem experimentais: exigem uma série de mesma órbita e pixels reais; ausência de cena recente é distinta de falha de rede.

Limite científico: Sentinel-1 banda C é evidência para cobertura/monitoramento e entrada SAR compatível, mas não se converte isoladamente em AGB. O estimador quantitativo de biomassa continua a exigir produto/modelo compatível, inventário e validação aplicáveis. O gate de aceite depende da aprovação live no SHA final. Versão candidata 3.26.27-PRECAMPO-EXPERIMENTAL; não homologada.


# V88.42 — handoff ponta a ponta do core para os dashboards (13/11/2026)

A verificação do fluxo worker → fila → `_execute_main` → painéis encontrou duas lacunas: a auditoria agrícola não preservava explicitamente a proveniência SAR recebida do core, e o painel de carbono podia ocultar a data quando recebia `acquisition_utc` sem o campo derivado de Brasília. A auditoria agora registra ID da execução, estado da etapa do pipeline e proveniência SAR com datas, cenas, pixels, provedor e diagnósticos; o painel de carbono deriva a apresentação UTC−03:00 do timestamp de aquisição confirmado. Nenhuma data é inferida de nome de arquivo ou horário de download.

As rotas públicas agora fazem repetição limitada de consultas transitórias (MPC/INPE, até três tentativas com backoff); a chamada STAC de pixels MPC usa timeout (15 s de conexão, 45 s de leitura). Nenhuma rota transforma timeout em ausência confirmada.

Regressão de integração: `tests/test_core_to_dashboard_handoff.py` atravessa a fila assíncrona, executa o caminho principal real e os dois apresentadores reais, com fixtures determinísticas. Verifica carbono e data de cena no painel de carbono, candidatos VV/VH com data/provedor/pixels no painel e auditoria agrícola sem convertê-los em área de cultura validada, propagação de falha SAR/status parcial e persistência JSON. A prova live de acesso consulta MPC e INPE em oito AOIs distribuídas nos seis biomas, incluindo Sinop e o perímetro de aceitação do Tapajós; cada AOI exige que pelo menos uma rota pública leia VV/VH da mesma cena, aquisição de até 30 dias e ao menos 100 pixels válidos por polarização. A rota sem cena ou com erro fica registrada, e o gate só reprova quando ambas não fornecem pixels. Isso testa conectividade em pontos representativos, não uma garantia wall-to-wall em cada coordenada ou época; cada AOI real continua auditada e pode declarar N/D/ERRO.

Resultado live neste ambiente (13/11): a busca de catálogo MPC encontrou cenas de até 30 dias para Manaus, Sinop e Brasília; o catálogo INPE não retornou cenas nesses recortes. A tentativa live de ler pixels no primeiro recorte falhou por `ReadTimeout` no MPC e erro HTTP transitório no INPE. Portanto, ainda não há evidência live de pixel lido nesta execução, e o teste permanece obrigatório no CI/Windows; não marcar conexão como resolvida até essa evidência passar.

A suíte completa passou localmente: 1.141 testes aprovados e 1 ignorado por ausência de display; coleta: 168 módulos. Build/CI, consulta live no SHA final, execução completa do KML Maria Eduarda no Windows e validação científica de campo permanecem gates separados. Candidata 3.26.28-PRECAMPO-EXPERIMENTAL; não homologada.

# V88.43 — integridade do par SAR e status operacional (13/11/2026)

Uma leitura isolada de VV podia ser registrada como processamento SAR concluído mesmo quando a leitura VH da mesma aquisição falhava. A rota MPC agora publica resultados completos somente quando VV e VH são lidos da mesma cena; leituras parciais ficam separadas em `partial_stats`/`partial_paths`, com estado `VV_VH_PAIR_INCOMPLETE`, e `available=false`. Isso impede que o dashboard ou os módulos seguintes interpretem uma polarização isolada como par SAR processado.

O teste `test_mpc_single_polarization_is_partial_not_processed` reproduz falha de VH após VV válido. Verificação local concluída: 1.145 testes passaram, 1 foi ignorado por ausência de display; a coleta inspecionou 168 módulos. O contrato do assinador MPC também foi ajustado para exercer até três tentativas transitórias; o teste de 429 agora comprova limite de três chamadas e encerramento fechado. Nenhuma tentativa ignora TLS, Retry-After ou limites configurados.

A candidata é `3.26.29-PRECAMPO-EXPERIMENTAL`. O ensaio local mede contratos, não demonstra conectividade remota. Catálogo encontrado não equivale a pixels decodificados: só declarar acesso operacional após leitura VV/VH real, recente (≤30 dias) e auditada no SHA final. A cobertura amostral em oito AOIs distribuídas nos seis biomas não é garantia para toda coordenada/época do Brasil; cada AOI deve preservar N/D/ERRO quando aplicável.

A atualização do prompt, da especificação de solo e da especificação técnica registra o estado de testes, build Windows, leitura live e ensaio do KML como gates independentes. A checagem visual local não pôde abrir Tk por falta de display; requer CI/Windows. Não declarar homologação científica sem validação observacional independente.

# V88.44 — diagnóstico nacional SAR e pacote pré-campo auditável (13/11/2026)

## Resultado confirmado no SHA V88.43

No commit `431833f1cec7693d8892d5a615cdaac02eb8a879`, os testes do dashboard, contratos pré-campo e máscara semântica SAR experimental Sinop passaram. A leitura ESA BIOMASS FH real em Sinop também passou. O build Windows chegou à sondagem nacional de pixels e reprovou em Petrolina: havia cenas recentes no catálogo MPC, mas o assinador devolveu HTTP 429 em VV/VH; a coleção RTC do INPE retornou zero cenas nesse recorte. O relatório de oito áreas não foi salvo porque a sondagem parou no primeiro ponto sem par legível. O gate de homologação científica reprovou por falta de evidência independente e artefato final.

## Ajustes na candidata 3.26.30

- Ao receber HTTP 429 do assinador MPC, interromper a busca por cenas antigas no mesmo provedor/AOI e registrar `rate_limited`; não ampliar a carga no serviço enquanto a limitação estiver ativa.
- A sondagem distribuída executa todos os oito AOIs (seis biomas), salva o resultado incrementalmente, sanitiza URLs e devolve código de saída reprovado se qualquer área não tiver par VV/VH recente com pixels válidos. A falha gera relatório por AOI/provedor, não desaparece nem vira sucesso.
- O gate SAR distribuído não bloqueia a compilação do pacote pré-campo. O relatório `DIAGNOSTICO_SAR_NACIONAL.json` e `STATUS_GATE_SAR_NACIONAL.txt` seguem dentro do ZIP portátil, e o LEIA-ME declara que não há garantia de cobertura em toda coordenada/data do Brasil.
- A regressão automatizada verifica que uma resposta 429 interrompe o fan-out por cenas e que uma polarização isolada continua parcial, nunca `PROCESSADO`.

## Limites e aceitação

Permitir a compilação experimental após o gate SAR reprovado não significa que o acesso nacional foi solucionado. Os resultados por AOI precisam ser lidos no diagnóstico do pacote; cada área sem par VV/VH recente mantém N/D/ERRO. A passagem em amostras de Sinop, Tapajós ou outro ponto não prova cobertura em qualquer local do Brasil. O monitoramento de lavouras e a estimativa de carbono devem manter seus limites científicos e não converter banda C isolada em AGB. A versão continua pré-campo experimental, sem homologação. Build, dashboard, sondagem e gate científico serão novamente avaliados no SHA 3.26.30.

# V88.45 — contingência ao HTTP 429 no acesso Sentinel-1

Para separar a limitação do assinador de indisponibilidade dos dados, a candidata `3.26.31-PRECAMPO-EXPERIMENTAL` usa primeiro o SAS token de coleção MPC para a coleção GRD em VV/VH; o token fica somente em memória e a auditoria registra a rota. O signer por ativo é fallback limitado e interrompe solicitações após HTTP 429. Rotas já disponíveis no core incluem INPE RTC público e CDSE autenticado. ASF OPERA RTC-S1 (Earthdata) e AWS Sentinel-1 GRD COG foram identificados como alternativas técnicas, mas não estão integrados à leitura de pixels desta candidata; ESA MAAP não é acesso Sentinel-1 e continua servindo a rota ESA Biomass para carbono/altura.

Uma falha local no MPC ou ausência de cenas INPE em uma AOI não prova indisponibilidade nacional. Sem par recente VV/VH lido na mesma cena, o painel mantém N/D/ERRO e não converte C-band em AGB. A suíte local completa passou: 1.150 testes aprovados e 1 ignorado por ausência de display gráfico. O teste Windows da rota SAS de coleção, o build no SHA final, a execução integral do KML Maria Eduarda até o painel e a validação independente continuam gates pendentes. Não homologar.


## Atualização V88.46 — evidência SAR de Windows

No Windows CI #2726 (SHA `8334643eadb4d82366c06eed789c9e659c752b09`), VV/VH recentes foram lidos em 8/8 AOIs representativas de seis biomas por SAS de coleção MPC, sem HTTP 429. Isso confirma a rota SAR na amostra, mas não é evidência de carbono de solo nem de cobertura nacional contínua. A estimativa de SOC 0–100 cm permanece sujeita aos seus próprios requisitos de dados oficiais, cobertura, incerteza e auditoria. O build e a análise integral da Fazenda Maria Eduarda ainda não estavam concluídos no checkpoint; a homologação científica foi reprovada por falta de evidência independente.


## Atualização V88.47 — build Windows concluído

O executável da candidata 3.26.31 foi construído e passou os smokes de Windows, paridade de módulos, padrão visual, rede TLS e aceite SAR do KMZ de teste Tapajós. Isso confirma a operacionalidade de empacotamento, não acrescenta evidência ao estoque SOC. O carbono do solo 0–100 cm continua sujeito aos dados oficiais, interseção, incerteza e auditoria especificados acima. O teste integral da Fazenda Maria Eduarda até o dashboard e a validação científica independente seguem pendentes; manter como experimental e não homologado.


---

## V88.48 — previsões experimentais de campo no painel (14/11/2026)

- Versão em desenvolvimento: `3.26.32-PRECAMPO-EXPERIMENTAL`. O painel de carbono agora expõe cada valor numérico que o manifesto pré-campo conseguiu derivar, por formação e compartimento: densidade, área-base, estoque associado, faixa disponível, tipo de incerteza, modelo, fonte, ID e hash de rastreio. Previsões de produtividade elegíveis mostram t/ha, produção-base, área, faixa, modelo, fonte e rastreio.
- Resultados incompatíveis ou sem fonte/método continuam N/D com o motivo; nenhuma média sintética é introduzida. A previsão experimental permanece fora do total conhecido/consolidado quando assim classificada. JSON e CSV mantêm previsões separadas de observações de campo; medições, parcelas e coordenadas ficam em branco até coleta independente.
- A regressão do handoff ganhou biomassa aérea numérica de fixture e valida que a previsão, o identificador de rastreio e a separação previsão/medição chegam ao painel. No commit executado antes desta sincronização, os testes direcionados passaram; a suíte completa executou 1.150 casos e falhou somente porque o Word ainda não continha a versão 3.26.32. Essa especificação e os documentos de continuidade foram sincronizados; repetir suíte completa e build Windows no novo SHA.
- A homologação científica independente continua reprovada por ausência de observações de campo e validação compatível. Não chamar o resultado de homologado. O teste integral do KML Fazenda Maria Eduarda até o dashboard permanece pendente.
- Esta alteração apresenta valores já calculados pelo manifesto existente; não modifica equações, calibra modelos, transforma Sentinel-1 C-band isolado em AGB nem garante resultado numérico para toda AOI. Onde não houver dado/modelo compatível, permanece N/D.

## V88.49 — desempenho e fluxo de resultados experimentais (14/11/2026)

A versão de código da candidata é `3.26.33-PRECAMPO-EXPERIMENTAL` (`3a7086011c61caf0a19dc8763a3276783d2e7b23`). As alterações não modificam o modelo de SOC, profundidades, camadas, incerteza ou conversão de unidades. O compartilhamento da rota CCI ocorre somente dentro da análise e por telhas; o cálculo zonal continua usando a geometria de cada estrato. Falhas SAR determinísticas de geometria/pixel não provocam repetição desnecessária de transportes; falhas técnicas recuperáveis preservam contingências. Estoques de carbono e SOC nunca são reutilizados entre estratos. O teste completo do novo SHA e o build Windows seguem pendentes; a execução integral da Fazenda Maria Eduarda no dashboard e a validação externa também não estão comprovadas. Manter status experimental e não homologado.

## V88.50 — integridade da versão de código (14/11/2026)

A versão candidata permanece `3.26.33-PRECAMPO-EXPERIMENTAL`, agora identificada pelo SHA `0f1cb66313bb0e989a8966dde3bc183b357128e2`. O código-fonte principal foi restaurado após a auditoria detectar conteúdo binário inválido no commit anterior; a restauração não altera o modelo de carbono do solo nem as suas profundidades e incertezas. `py_compile` e seis testes direcionados passaram localmente; CI completo, build Windows e execução ponta a ponta continuam pendentes. Não homologar.

## V88.51 — estimativas obrigatórias e entrega SAR ao dashboard (14/11/2026)

- Regra do produto: todos os compartimentos de carbono aplicáveis devem apresentar estimativa experimental rastreável e incerteza compatível com a fonte. As únicas exceções de saída são necromassa acima do solo e necromassa abaixo do solo, para as quais não há equações alométricas aplicáveis; mostrar explicitamente “não estimada — sem equação alométrica aplicável”, sem inserir zero. Biomassa aérea, biomassa subterrânea, serapilheira e carbono do solo 0–100 cm não podem desaparecer silenciosamente do painel. Se houver suporte publicado/inventário compatível, aplicar a hierarquia microrregional/regional com extrapolação estatística declarada; toda saída permanece pré-campo e não homologada.
- Prioridade de proveniência: quando houver cenas e pixels SAR utilizáveis, a estimativa SAR/modelo compatível deve permanecer a origem do resultado e ser distinguida de qualquer referência de inventário. A contingência de inventário só pode preencher a estimativa quando todas as rotas configuradas concluírem buscas completas, sem erros e com certificado verificável de ausência de cenas. Cena encontrada, pixels auxiliares, falha de leitura, autenticação, HTTP, TLS, paginação incompleta ou rota sem auditoria bloqueiam a contingência. Esses estados precisam chegar ao dashboard como motivo rastreável, não como ausência de dados.
- Defeito de handoff identificado: o worker enviava `sar: {}`; `_execute_main` apagava `project['sar_result']` e não consumia `precomputed_sar`; os painéis ainda consultavam `project['sar_result']`. A alteração 3.26.34 deriva um pacote AOI de SAR a partir das auditorias/detalhes por estrato nativo e da cobertura SAR agrícola e o preserva em `project['sar_result']`, mantendo cenas, estatísticas, origem, motivo e certificado de altura. O teste de integração foi ampliado para impedir que o payload SAR pré-computado seja descartado.
- A auditoria local também encontrou erro de indentação em `sar_pipeline.py`, impedindo a importação do pipeline; corrigido. `py_compile` passou nos cinco módulos alterados. Os testes direcionados não puderam ser executados neste ambiente: faltam `requests` e `geopandas`; não registrar esses casos como aprovados.
- Esta sincronização de código e documentação é candidata pré-campo, versão 3.26.34. CI completo, build Windows, teste real da AOI até o dashboard, estimativas numéricas de todos os compartimentos em AOIs brasileiras e homologação científica independente ainda não foram comprovados. Não chamar de homologado nem prometer cobertura numérica universal sem esses resultados.

## V88.52 — CI Windows e sincronização documental (14/11/2026)

- Candidata `3.26.34-PRECAMPO-EXPERIMENTAL`; o guard das notas de versão exigia o título `Enform Verde v<APP_VERSION>`. Corrigido no SHA `486eee54e65a53382feb6ca5af50494bd8209b9e`.
- O runner Windows instalou os requisitos geoespaciais/HTTP e executou a suíte completa: 1.155 testes, 1 falha em `test_versioned_spec_is_valid_docx_with_current_update`, porque o DOCX ainda registrava a versão anterior. DOCX e prompts foram sincronizados; repetir CI no próximo SHA antes de declarar suíte aprovada.
- Contrato rápido de modelos, máscara SAR experimental de Sinop e leitura real ESA BIOMASS FH em Sinop passaram. O workflow de build ainda não terminou no momento deste checkpoint. Homologação científica independente reprovada por falta de evidência observacional; o KML completo de Fazenda Maria Eduarda até o dashboard continua sem prova ponta a ponta.
- A ausência local de `geopandas` e `requests` foi contornada no CI Windows, que instalou os requisitos de desktop e rodou os testes. É possível instalar localmente com o ambiente/arquivo de dependências do projeto, mas não é pré-requisito para CI. Manter versão pré-campo experimental e não homologada.

## V88.53 — regressão completa aprovada no Windows (14/11/2026)

- No SHA `15e0c0bc0742901d63892497f79c9c61148e11c4`, o runner Windows instalou os requisitos desktop/geoespaciais e passou compilação completa dos módulos, guard de coleta e suíte integral: 1.155 testes aprovados.
- A única falha da execução anterior era documentação: DOCX em 3.26.33 com código em 3.26.34. O Word e os prompts foram sincronizados; a suíte completa seguinte passou.
- Passaram também contrato rápido pré-campo, máscara semântica SAR experimental de Sinop e prova ESA BIOMASS FH com pixels reais em Sinop. Isso não equivale a análise integral da Fazenda Maria Eduarda até o dashboard.
- Build Windows ainda preparava a base cartográfica IBGE offline; sem conclusão verde não declarar EXE pronto. Homologação científica independente reprovada por ausência de observações de campo independentes. Manter experimental, não homologado.

## V88.54 — fundo óptico CBERS‑4A prioritário e leitura COG em quadrantes (14/11/2026)

- Prioridade mantida: CBERS‑4A/WFI do INPE é a primeira rota de imagem óptica; Sentinel‑2 L2A (Earth Search e Planetary Computer) é a alternativa. ESA MAAP/BIOMASS continua rota de dados SAR/canopy quando o produto e a cobertura forem adequados; não substitui o fundo CBERS/Sentinel‑2.
- Leitura das bandas COG agora usa janelas de saída de até 512 × 512 px e limita candidatos remotos a três cenas por provedor. Reduz dimensões de prévia e timeouts/retries por cena; cenas só são aceitas depois da leitura RGB real e cobertura de ao menos 95% da AOI. O cache óptico é identificado pela origem e atualizado em paralelo ao pedido CBERS prioritário.
- Removida a geração, empacotamento e cópia do grande raster/cartografia IBGE offline no workflow Windows, além do fallback cartográfico como se fosse imagem orbital. Em falha de CBERS e Sentinel‑2, o perímetro permanece visível e o diagnóstico mostra a falha. NASA VIIRS e Esri permanecem contingências visuais inferiores, identificadas e sem uso nos cálculos.
- O helper trata bandas de origem inteira e pixels mascarados convertendo para float antes de preencher NaN; evita erro ao ler COGs com dtype inteiro. O workflow removeu o bloco de teste/cartografia obsoleto e verificará quadrantes limitados e a prioridade dos provedores.
- Versão candidata `3.26.35-PRECAMPO-EXPERIMENTAL`. `py_compile` passou localmente; não foi possível executar suíte local neste ambiente porque faltam `requests`, `rasterio` e `geopandas`. A execução CI Windows e o smoke de pixels CBERS→Sentinel‑2 no SHA final ainda são necessários. Ainda não foi comprovada imagem no KML integral de Fazenda Maria Eduarda até o dashboard.
- Remover o raster offline não garante que um provedor remoto esteja disponível em qualquer instante. A falha deve permanecer distinguida de ausência de cenas, com provedor, etapa, cena/data e erro rastreáveis; nenhuma visualização de contexto pode ser chamada de imagem CBERS/Sentinel‑2. Não homologado.

## Atualização operacional V88.55 (14/11/2026)

Esta alteração de imagem não modifica os métodos de carbono do solo, as profundidades nem as fontes de dados da especificação. Para contexto operacional do produto: CBERS-4A/WFI é o fundo óptico prioritário e Sentinel-2 L2A a alternativa. A evidência Windows observou cobertura CBERS em 11/11 janelas representativas e exibição em canvas Tk numa janela ao redor do centroide de Sinop; não foi executado o KML integral da Fazenda Maria Eduarda. A suíte completa do dashboard teve 1.156 testes aprovados; o job foi bloqueado exclusivamente pelo guard de sincronização documental. Permanecem necessários novo CI após esta atualização, execução ponta a ponta da AOI integral e validação de campo. O estado segue pré-campo experimental, não homologado.


# REVISÃO V87.1 — 05/11/2026 — CORREÇÃO CIENTÍFICA V87.1: limites marginais do SOC 0–100 cm

Preservar, para os horizontes 0–5, 5–15, 15–30, 30–60 e 60–100 cm, a soma ponderada dos limites marginais oficiais e a rastreabilidade por horizonte. Identificar o resultado como envelope marginal oficial (`marginal_envelope_available=true`); manter `predictive_uncertainty_quantified=false`, pois a soma dos limites não representa intervalo conjunto de confiança de 95% e não inclui correlação, transferência, viés ou incerteza total da propriedade. Ausência/erro de serviço permanece N/D com motivo. O estoque central recuperado não deve desaparecer apenas porque os limites marginais não estão disponíveis. Esta regra não altera as fontes oficiais Embrapa/PronaSolos nem a profundidade de 0–100 cm.


## V88.56 — confirmação final de CI e build Windows (14/11/2026)

- O código da versão 3.26.35 permanece no SHA `417e93141ec035d5bb414abb620224d490580927`. O SHA `b4f7adcd4da162021df35187dabef7cc435fcd1e` contém apenas sincronização documental, restauração das marcações científicas V87.1 e rebuild; nenhuma alteração de runtime foi introduzida depois do código testado.
- No dashboard CI #43635716670, a suíte completa terminou com 1.156 testes aprovados. O contrato rápido pré-campo #43635716654 e a máscara SAR experimental de Sinop #43635716643 passaram. Uma execução intermediária do contrato pré-campo falhou porque o marcador V87.1 havia sido omitido dos documentos; o texto foi restaurado e o contrato passou no SHA final.
- O build Windows #43635716635 passou no SHA documental b4f7adcd4da162021df35187dabef7cc435fcd1e. O EXE 3.26.35 passou autoteste em pasta limpa. Artefato Actions 14130517119, 197.798.620 bytes; SHA-256 do ZIP `33b359aea8f60573b4ae39851b096e1616bb85d4b39654fdf03c0bfedd050aab`; SHA-256 do EXE `a7bc32707554ff870fa470d83381172bb0427751d508e9b28263a1a214fc81f4`.
- CBERS-4A/WFI foi lido com pixels reais em 11/11 janelas brasileiras representativas, com cobertura reportada de 100% por janela (mínimo de aceite 95%). O painel Tk mostrou CBERS real numa janela ao redor do centroide de Sinop; Sentinel-2 real no Tapajós passou. Foram aprovados o teste live de SAR no Tapajós, o catálogo INPE Sentinel-1 RTC em amostras dos seis biomas e a prova de pixels ESA BIOMASS FH em Sinop.
- Essas evidências não incluem o KML integral da Fazenda Maria Eduarda até o dashboard e não provam cobertura contínua nacional para todo local e data. O gate científico independente #43635716646 permanece reprovado por ausência de observações de campo independentes. Não homologado; manter pré-campo experimental.


### Auditoria do código e limite da evidência

A revisão V88.49 cobriu cache CCI por análise, retentativas e persistência da auditoria Sentinel-1 e o handoff SAR ao dashboard. Foi uma auditoria direcionada, não uma auditoria exaustiva de todos os módulos e fluxos do produto. Os testes verdes cobrem os contratos e cenários executados; não provam que todas as falhas recorrentes estejam eliminadas nem cobrem toda AOI. Manter essa distinção e realizar revisão estrutural/integração ponta a ponta antes de alegar correção definitiva.


## V88.59 — sincronização documental do pacote (14/11/2026)

Esta versão sincroniza a especificação do solo com a candidata de software 3.26.36 e as correções arquiteturais SAR registradas no prompt e na especificação técnica. Não altera fontes, profundidade, métodos, cálculos, incertezas ou interpretação do carbono/fertilidade do solo.

## Nota de sincronização V88.60

O build Windows `3.26.36-PRECAMPO-EXPERIMENTAL` passou no self-test em pasta limpa (workflow `43642362176`). Esta atualização registra o estado da versão e não altera as exigências técnicas de carbono do solo 0–100 cm. O resultado de build não representa validação de campo nem homologação científica.


## V88.62 — incerteza transversal para estimativas de carbono

O carbono do solo 0–100 cm deve apresentar incerteza junto ao resultado em tC/ha e %, método, horizontes/atributos incluídos, cobertura, fonte e limitações. Distinguir incerteza amostral, de mapeamento/modelo e transferência; envelopes marginais por horizonte não devem ser rotulados IC95% conjunto. Se parcial, explicitar componentes e lacunas. Quando o valor estimado tiver suporte, mas a incerteza de algum parâmetro não puder ser mensurada, apresentar o resultado e rotular exatamente “incerteza não mensurável”, identificando o parâmetro e o motivo. N/D aplica-se ao valor somente quando ele próprio não tiver suporte. Esta regra integra o contrato comum a todos os compartimentos de carbono e não altera as fontes oficiais de solo ou a profundidade estabelecida.


## V88.63 — rótulo quando a incerteza não puder ser mensurada

Para o estoque de carbono do solo 0–100 cm, quando o valor tiver suporte mas a incerteza de um ou mais parâmetros não puder ser quantificada, manter a estimativa e apresentar exatamente “incerteza não mensurável”, com parâmetro, motivo e fonte consultada. N/D é reservado ao próprio estoque sem suporte. Distinguir limitações dos horizontes, envelope marginal, incerteza amostral e erro de transferência.


## V88.63 — sincronização das regressões da candidata 3.26.37

O teste integral da revisão anterior executou 1.160 testes; as regressões agora exigem “incerteza não mensurável” para estoques suportados sem incerteza quantificável. A nova revisão deve repetir CI e build Windows no mesmo SHA; manter resultado experimental pré-campo até esses gates e as validações de campo.

## Evidência de validação da candidata 3.26.37

Commit validado: `9c4c60c76ce5cd88ec6ff29420db36c2d631c8e2`. Dashboard: 1.160 testes aprovados e guard documental sem pendências (execução 43652675732). Build Windows: aprovado, incluindo smoke óptico nacional, leitura no canvas Tk, SAR real e autoteste do EXE em pasta limpa (execução 43652675738). Provas independentes reais ESA BIOMASS FH e Sentinel-1 Sinop também aprovadas. Artefato `Enform-Verde-Windows-v3.26.37-PRECAMPO-EXPERIMENTAL`: 197.799.200 bytes; SHA-256 do pacote: `sha256:65b49f7980f3058bd5b8c55fdbd806d62188b1a931e1e37bbdc28e1062832232`.

Estado: candidata experimental pré-campo. A homologação científica independente permanece reprovada por ausência de validação de campo e de execução ponta a ponta do KML completo da Fazenda Maria Eduarda até o painel; não usar estes gates como comprovação de homologação ou desempenho de campo.


## V88.64 — continuidade do pipeline quando a etapa de solo falha

A etapa de pedologia/PronaSolos não pode apagar resultados SAR, uso da terra ou carbono que já tenham sido calculados. Falhas de pedologia e fertilidade devem ser declaradas por módulo, com motivo e estado N/D/ERRO_TECNICO; os módulos anteriores permanecem vinculados à mesma execução e AOI. O status do solo não altera as fontes oficiais, a profundidade de 0–100 cm, nem autoriza imputação de carbono ou fertilidade. Um checkpoint de auditoria é complementar à apresentação do resultado; se falhar, registrar a falha sem descartar saídas válidas.

A candidata 3.26.38 ainda precisa passar suíte, dashboard e build Windows no mesmo commit. Esta alteração arquitetural não comprova cobertura PronaSolos nem execução integral da Fazenda Maria Eduarda.


## V88.65 — validação do pipeline e preservação dos estados de solo

No commit de código dc79606d4073da23cf5c83aed54a23d500f1ef1a, dashboard e build Windows passaram; a candidata preserva resultados SAR/uso da terra quando uma etapa posterior de carbono, pedologia ou fertilidade falha e apresenta estado e motivo por módulo. O build incluiu fontes live e autoteste do EXE. Isso não comprova cobertura PronaSolos em toda AOI nem substitui a execução integral do KML privado de Sinop até o painel. Carbono do solo permanece 0–100 cm e fontes de solo continuam oficiais; não imputar valores.

## Nota de sincronização V88.66

Nesta revisão foram priorizadas as rotas Sentinel-1 de uso do solo e carbono nativo. Não houve mudança nos métodos de carbono do solo, PronaSolos ou fertilidade. A estimativa pedológica continua independente do status de classificação SAR. O pipeline geral mantém o estado técnico e a evidência de cobertura SAR vinculados ao mesmo run_id/hash da AOI.


## Registro V88.67 de sincronização documental

Na candidata 3.26.39 (commit `3172277b02dd59de24861c8dd8abfc8e5159d49a`), a CI e o build Windows passaram; essa evidência não modifica nem valida por si só as estimativas de carbono do solo. O módulo PronaSolos 0–100 cm continua condicionado à interseção e leitura de perfis reais, profundidade efetiva e cobertura; incerteza não suportada deve aparecer como “incerteza não mensurável”. O handoff live SAR até máscara de carbono e dashboard ainda não foi comprovado na AOI integral da Fazenda Maria Eduarda. O estoque de carbono do solo não deve ser inferido da aprovação do build ou da prova de pixels SAR.


## Registro V88.68 — integração até os painéis

A mudança de handoff SAR em validação acrescenta ao payload executivo as máscaras semânticas e a identidade da execução. Ela não altera a metodologia de carbono do solo. Os estoques 0–100 cm continuam dependendo de interseção/leituras válidas de fontes Embrapa/PronaSolos e dos respectivos parâmetros; uma máscara SAR, por si só, não gera nem valida carbono do solo. Exibir N/D, motivo e “incerteza não mensurável” quando não houver suporte.
