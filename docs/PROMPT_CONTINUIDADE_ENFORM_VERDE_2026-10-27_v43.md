Warning: truncated output (original token count: 134064)
Total output lines: 2347

<!-- V88_16_NATIONAL_RESULT_WITH_UNCERTAINTY -->
## V88.16 — resultado nacional com incerteza e estado auditável (12/11/2026)
Objetivo obrigatório: para qualquer AOI do Brasil, concluir cada módulo com o melhor resultado cientificamente sustentado ou estado N/D/ERRO_TECNICO, sempre com fonte, período, cobertura, método e incerteza. Quantificar incerteza quando suportada por dados/desenho amostral; caso contrário declarar “incerteza não quantificada” e motivo, sem inventar precisão ou converter N/D em zero.

Hierarquia: preservar AOI original, CRS, hash, run_id e versão; verificar pixels reais (catálogo não equivale a leitura); priorizar altura SAR diretamente medida (ESA BIOMASS FH quando adequada); para biomassa integrar equações publicadas com altura SAR, distribuição diamétrica e área basal média de inventários compatíveis, favorecendo parcelas da AOI, microrregião/região e mesma fitofisionomia. Alternativa experimental requer fundamento, sensibilidade/validação, fontes e rótulo experimental. Para agricultura, SAR atual precede MapBiomas histórico e PAM agregada; quando cultivo for sustentado mas espécie não, indicar “área cultivada”.

Ausência SAR só pode ser certificada depois de busca/paginação/leitura completas e zero pixels adequados sem erro. Falhas de autenticação, rede/TLS, timeout, paginação, decodificação, leitura, dependência ou interrupção são ERRO_TECNICO; retentar, testar rotas tecnicamente diferentes e corrigir na mesma AOI. Não acionar contingência para esconder falha. Contingência de carbono/altura usa inventários nacionais microrregionalizados/regionais da mesma fitofisionomia com tratamento estatístico e incerteza, rotulados como estimativa indireta. Incerteza ausente de suporte deve ser declarada como não quantificada.

No Excel, a aba Gráficos contém linha de fustes/ha por DAP, parâmetros/tabela de área basal média, linha de altura SAR (ou média de inventário da mesma fitofisionomia apenas com ausência certificada) e barras das dez espécies dominantes; todas as fontes, unidade, período e condição observada/fallback. Bloquear regressão de sobreposição dos dados auxiliares DAP com a área D:E do painel de altura. O dashboard valida run_id/hash, aceita estados por módulo e mostra divergência de áreas como não reconciliada, sem atribuí-la a uma classe ou carbono.

ESTADO VIGENTE (13/11/2026, checkpoint V88.36): candidata `3.26.25-PRECAMPO-EXPERIMENTAL`. O workflow Windows anterior falhou no teste do EXE ao tentar baixar um COG Sentinel-1 de 2 GiB pelo caminho HTTPS local; isso é erro de transporte/tamanho, não ausência SAR. A correção agora direciona COGs grandes, falhas de assinatura, interrupção HTTP e respostas inválidas à rota de recorte limitado da AOI pelo Planetary Computer, preservando TLS e auditoria sem URLs assinadas. Suíte local completa: 1.135 aprovados, 1 ignorado por ausência de display; incluem testes simulados de COG grande, assinatura e transporte. O recorte real no Windows ainda precisa passar no workflow do SHA final; simulações locais não comprovam a rota live. Não há novo artefato Windows aprovado neste checkpoint. PR #51 permanece draft. A leitura do KML integral no aplicativo até o dashboard e a homologação científica independente continuam pendentes; resultados mantêm caráter experimental e incerteza declarada.


<!-- V87_95_FINAL_WINDOWS_BUILD -->
## V87.95 — build Windows final 3.26.16 no commit b70894e (11/11/2026)
- Run Windows `43050581961` concluiu verde no SHA `b70894e1796121027aaaf09c00a533d131e5a749`. Artefato `Enform-Verde-Windows-v3.26.16-PRECAMPO-EXPERIMENTAL`, ID `13871576858` (533.400.808 bytes; SHA-256 ZIP `1abc923ed7133ce259c1130b5b7be729c827226891e52e5739aab82777b7d4f6`). EXE SHA-256 `66c17b8d8fad210a9e3aa92e16a05e3d11d3c4655d0b8722e2477f7958a6cc97`.
- O EXE passou teste em pasta limpa, paridade núcleo Python/Windows, `--visual-check`, `--network-check` TLS ativo e aceite SAR Tapajós. Aceite: `SAR_PROCESSADO`, 1.290,69 ha, 302.348 pixels, 5 cenas; sem AGB quantitativa (`fallback_agb_mg_ha=null`). É execução observada em fixture, não validação de campo nem resultado de carbono.
- CBERS-4A/WFI real passou no network-check; smoke óptico 11/11 locais amostrais brasileiros (9 CBERS, 2 Sentinel-2 fallback) e CBERS worker→canvas Tk em janela Sinop passaram. Cobertura amostral não garante pixels em cada local/data nem comprova o KML integral de Sinop.
- Gate científico permanece reprovado; BIOMASS FH para as AOIs de alta biomassa do Tapajós não foi confirmado. Não declarar altura FH para Tapajós, homologação nacional ou resultados da Fazenda Maria Eduarda integral até testar o KML completo no Windows. PR #51 segue draft; release restrita a `main`.

<!-- V87_94_WINDOWS_BUILD_AND_REAL_OPTICAL_SMOKE -->
## V87.94 — build Windows, leitura óptica em amostras nacionais e limites da prova (11/11/2026)
- Fonte do executável testado: SHA `a1a11b1e406af0d322c5697222012403c92735ba`; versão `3.26.16-PRECAMPO-EXPERIMENTAL`; artefato Actions `Enform-Verde-Windows-v3.26.16-PRECAMPO-EXPERIMENTAL`, ID `13867841475`, 533.397.855 bytes. O EXE passou compilação, runtime, self-test em pasta limpa, network check e aceite SAR com AOI de Tapajós. SHA-256 do executável: `95aa798b72ddcafc9c962ffd338b5cf7f7e4740488ed325fde7ee710c8e2631f`.
- Build Windows restaurou o mapa IBGE offline de um pacote anterior; mapa/quadrantes verificados. Alterada a regra do workflow para não publicar release automaticamente de branch/PR; o artefato experimental permanece disponível como artefato temporário de Actions. Publicação em release deve ocorrer em fluxo explícito a partir de `main`.
- Smoke óptico real em 11 pontos distribuídos pelos biomas/extremos: pixels ópticos carregados em 11/11 AOIs de teste, com cobertura mínima observada >=95%; CBERS-4A primário em 9/11 e Sentinel-2 de fallback nos demais, incluindo a janela amostral de Sinop. CBERS-4A também passou pela rota worker→canvas Tk em Sinop. Isso não é prova exaustiva de todos os pixels/épocas do Brasil nem teste do KML integral de 1.459,91 ha.
- Prova SAR independente em Sinop: 30 cenas Sentinel-1 RTC VV/VH e 1.692 pixels numa janela de teste de 1.084,73 ha; polígonos cobrem 1.079,26 ha. É uma inferência experimental para a safra 2025/26, não representa a fazenda completa, não foi aferida em campo e não deve sustentar estoques de carbono. A leitura real de pixels ESA BIOMASS FH em Sinop também passou, sem demonstrar cobertura nacional.
- A suíte de regressão do dashboard passou; o job ainda reprovou exclusivamente o gate que exige prompt e Word após a última alteração efetiva do workflow. Este checkpoint e os quatro documentos sincronizados neste commit corrigem a ordem documental. O gate científico independente continua reprovado, portanto manter o piloto como EXPERIMENTAL, sem alegar homologação, calibração regional ou uso decisório.
- Pendências que permanecem: executar o KML integral de Sinop no Windows do usuário, conferir imagem e relatórios nesse perímetro, observar estimativa de carbono por compartimento e agricultura nesse KML, obter validação independente de campo. Não transferir áreas da janela de teste para a propriedade.

<!-- V87_89_UNMEASURED_UNCERTAINTY_LABEL_AND_TRACE -->
## V87.89 — “estimativa com incerteza não mensurada” e trilha de cálculo (10/11/2026)
- Usar a expressão literal somente quando a incerteza exigida não puder ser estimada defensavelmente. Medidas parciais conhecidas, como DP amostral entre parcelas, devem ser nomeadas como tal e não apresentadas como incerteza total/IC95%.
- Exibir trilha reproduzível com fontes/filtros, unidades independentes, soma/n, média e DP, parâmetros, equações, área-base, fatores e conversões; listar os termos de incerteza não mensurados.
- Implementada para o cenário IFN condicional no código `d26a4f8`, versão `3.26.14-PRECAMPO-EXPERIMENTAL`. Não confirma cobertura atual e não entra no estoque nativo confirmado.
- Teste focal passou; regressão completa local bloqueada por dependências não instaladas. CI/build Windows e ensaio do KML integral pendentes; não liberar.

<!-- V87_87_IFN_CONDITIONAL_CARBON -->
- Commit `d26a4f8`, build `3.26.14-PRECAMPO-EXPERIMENTAL`, com dados IFN incluídos no pacote Windows: quando não existirem pixels SAR quantitativos e a ausência operacional estiver confirmada sem falha técnica pendente, pode gerar cenário de AGB/carbono com UAs abertas do SFB/IFN compatíveis com Amazônia e Floresta Estacional Sempre-verde em MT. No centroide de Sinop, 30 UAs no raio de seleção regional de 250 km; AGB 138,29 ± 62,16 Mg/ha (DP entre UAs), faixa observada 27,39–332,68 Mg/ha. Não é IC95% da AOI; erro de transferência, equação e fração fixa de carbono não quantificados.
- Base de área é interseção potencial IBGE legenda_1 e o cenário é apresentado separadamente. Não afirmar cobertura nativa atual nem adicionar ao estoque confirmado. SAR lido bloqueia fallback; erros de acesso/leitura permanecem ERRO_TECNICO. Domínios sem inventário compatível seguem N/D.
- Quando a incerteza total necessária não puder ser quantificada, o valor deve ser rotulado **“estimativa com incerteza não mensurada”** e acompanhado da trilha do cálculo (filtro, UAs, média/DP, fator C, área condicional e conversões). Não sugerir que dispersão amostral seja a incerteza completa.
- Teste focal passou. Suíte local: 856 executados, 57 erros por dependências não instaladas, 1 falha associada ao ambiente e 28 ignorados; coleta de testes e padrão visual também bloqueados por dependências. Ainda requer CI, build Windows, teste com o KML integral e gates científicos no mesmo SHA. Versão não liberada.

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
- CLASSIFI…119064 tokens truncated…ontinua pré-campo experimental, não homologada; não declarar resultado de incerteza até leitura de dados reais passar no runtime.

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

# V88.45 — contingência HTTP 429 Sentinel-1 por token SAS de coleção (13/11/2026)

A leitura MPC Sentinel-1 GRD deve solicitar primeiro o token SAS da coleção `sentinel-1-grd` e usá-lo em memória para VV e VH. Para o storage GRD, as rotas documentadas são `/token/sentinel-1-grd` e `/token/sentinel1euwest/s1-grd`; são distintas das rotas RTC. Assim se evitam chamadas individuais ao signer para cada ativo quando a rota de coleção estiver disponível. Só recorrer ao signer por ativo se a emissão do token de coleção falhar; manter tentativas limitadas, respeitar Retry-After e parar o fan-out ao HTTP 429. Nunca registrar token, query SAS ou URL assinada.

Preservar `PROCESSADO` somente se VV e VH forem realmente lidos na mesma aquisição. A auditoria deve informar `COLLECTION_SAS_TOKEN` ou `PER_ASSET_SIGNER_FALLBACK`; falha conserva `ERRO_TECNICO`/N/D com diagnóstico.

Rotas independentes e estado: INPE RTC público e CDSE autenticado já são tentados pelo pipeline; falta de cena recente no INPE numa AOI não prova indisponibilidade nacional. ASF OPERA RTC-S1 é uma alternativa com Earthdata, mas seu catálogo ainda não está ligado a um leitor de pixels no pipeline. O arquivo global AWS Sentinel-1 GRD COG é uma opção pública que requer processamento RTC antes de comparação radiométrica; também não está integrado. ESA MAAP serve à rota Biomass já implementada e não autentica dados Sentinel-1.

A correção de código está na candidata `3.26.31-PRECAMPO-EXPERIMENTAL`. A suíte local completa passou: 1.150 testes aprovados e 1 ignorado por ausência de display gráfico. Esse resultado não testa acesso live no Windows. O token SAS de coleção ainda precisa provar leitura VV/VH, e o build/dashboard no SHA final e a execução do KML integral Maria Eduarda continuam pendentes. A V88.43 falhou em Petrolina com 429 no signer MPC e sem cenas no catálogo INPE naquele recorte; isso não prova indisponibilidade de todos os provedores nem de todo o Brasil. Manter a versão pré-campo experimental e não homologada até evidência operacional e observacional independente.

Fontes oficiais de acesso e alternativas constam em `docs/spec_updates/2026-11-13_v88_45_mpc_collection_token_sar_recovery.md`.


# V88.46 — validação Windows ao vivo da contingência SAR (13/11/2026)

No SHA `8334643eadb4d82366c06eed789c9e659c752b09`, o Windows CI #2726 leu VV e VH reais da mesma aquisição Sentinel-1 GRD em 8/8 AOIs amostrais de 6 biomas, usando `COLLECTION_SAS_TOKEN`; aquisições tinham 0,65–10,62 dias, 128.484–196.249 pixels válidos por banda, sem HTTP 429. Isso comprova o contorno operacional do 429 na amostra, não cobertura contínua nacional. O catálogo INPE RTC retornou zero cenas compatíveis nos oito recortes, com paginação completa.

Dashboard dual #3448, contratos rápidos #805, máscaras experimentais SAR Sinop #207, leitura SAR no KMZ de teste Tapajós, sondagens ópticas brasileiras e abertura no canvas de Sinop passaram. O build Windows #2726 ainda estava em andamento nos contratos de equações/recalibração quando o checkpoint foi escrito. O KML integral da Fazenda Maria Eduarda até o dashboard continua sem comprovação ponta a ponta. A homologação científica independente #3035 reprovou por falta de evidência observacional independente. Manter `3.26.31-PRECAMPO-EXPERIMENTAL`; não homologar, não afirmar cobertura wall-to-wall, e não derivar AGB de C-band isolada. Relatório por AOI: `inpe_sentinel1_rtc_live.json`; status do gate: `PASS_DISTRIBUTED_SAMPLE`.


# V88.47 — build Windows e aceite do executável concluídos (14/11/2026)

O workflow Windows #2726 concluiu com sucesso no SHA `8334643eadb4d82366c06eed789c9e659c752b09`. O executável `3.26.31-PRECAMPO-EXPERIMENTAL` passou autoteste em pasta limpa, paridade Python/Windows, smoke de interface, verificação visual e checagem de rede com TLS ativo. A leitura do executável confirmou CBERS-4A/WFI e Sentinel-1 VV/VH; rede HTTPS local confirmou 169.168 pixels válidos por banda. A aceitação do KMZ de teste Tapajós retornou `SAR_PROCESSADO`, 1.290,688 ha, 302.348 pixels e três cenas com `data_origin=SAR_DERIVED_CCI`; `fallback_agb_mg_ha=null`, portanto não relatar como nova AGB diretamente derivada da banda C.

O gate distribuído #2726 teve VV/VH legíveis por SAS de coleção em 8/8 AOIs amostrais de seis biomas sem 429. INPE RTC retornou zero cenas nesses recortes; não generalizar para a disponibilidade nacional. Dashboard #3448, contrato rápido #805 e máscara SAR experimental Sinop #207 passaram. O gate científico #3035 reprovou por falta de evidência observacional independente. O KML integral Fazenda Maria Eduarda até o dashboard ainda não foi executado/comprovado.

Artefato Actions ID `14087567135` (531.996.993 bytes). SHA-256 ZIP `1ad43f1281171b2eb49678bbc6ca5631587eef8f9b8ba69fa00904df1e2b9e77`; SHA-256 EXE `b7743a0d046390c14d3bdb97332fd15aeb82c8f72af85b07a0331e6db927264c`. Manter `PRECAMPO-EXPERIMENTAL`, sem declarar homologação.


---

## V88.48 — previsões experimentais de campo no painel (14/11/2026)

- Versão em desenvolvimento: `3.26.32-PRECAMPO-EXPERIMENTAL`. O painel de carbono agora expõe cada valor numérico que o manifesto pré-campo conseguiu derivar, por formação e compartimento: densidade, área-base, estoque associado, faixa disponível, tipo de incerteza, modelo, fonte, ID e hash de rastreio. Previsões de produtividade elegíveis mostram t/ha, produção-base, área, faixa, modelo, fonte e rastreio.
- Resultados incompatíveis ou sem fonte/método continuam N/D com o motivo; nenhuma média sintética é introduzida. A previsão experimental permanece fora do total conhecido/consolidado quando assim classificada. JSON e CSV mantêm previsões separadas de observações de campo; medições, parcelas e coordenadas ficam em branco até coleta independente.
- A regressão do handoff ganhou biomassa aérea numérica de fixture e valida que a previsão, o identificador de rastreio e a separação previsão/medição chegam ao painel. No commit executado antes desta sincronização, os testes direcionados passaram; a suíte completa executou 1.150 casos e falhou somente porque o Word ainda não continha a versão 3.26.32. Essa especificação e os documentos de continuidade foram sincronizados; repetir suíte completa e build Windows no novo SHA.
- A homologação científica independente continua reprovada por ausência de observações de campo e validação compatível. Não chamar o resultado de homologado. O teste integral do KML Fazenda Maria Eduarda até o dashboard permanece pendente.
- Esta alteração apresenta valores já calculados pelo manifesto existente; não modifica equações, calibra modelos, transforma Sentinel-1 C-band isolado em AGB nem garante resultado numérico para toda AOI. Onde não houver dado/modelo compatível, permanece N/D.

## V88.49 — auditoria de eficiência e retentativas SAR (14/11/2026)

- Versão da candidata: `3.26.33-PRECAMPO-EXPERIMENTAL`. Código no commit `3a7086011c61caf0a19dc8763a3276783d2e7b23`.
- O cache ESA CCI v7 é limitado a uma análise e à combinação de telhas de 10°. Evita repetir descoberta/download entre estratos que compartilham telhas; cada estatística zonal continua usando a geometria exata do estrato. Nenhuma estimativa científica é reutilizada entre propriedades ou execuções.
- A auditoria Sentinel-1 conserva MPC e CDSE em `sentinel1_provider_routes`; o resumo legado mantém a primeira rota que processou pixels, e a rota secundária não apaga a trilha primária.
- No monitoramento agrícola, falhas determinísticas de geometria/validade (sem pixels válidos, sem interseção, janela acima do limite ou par VV/VH incompleto) deixam de repetir transportes sobre a mesma cena. Falhas de TLS, conexão, decodificação e outros erros potencialmente transitórios mantêm as rotas alternativas.
- Não foi feita reescrita ampla nem cache de estoques por estrato. O perfil ponta a ponta ainda deve medir número de leituras COG, bytes, latência por provedor e tempo por AOI. Otimização futura pode compartilhar ativos/janelas verificados, mas sempre recalcula estatísticas por geometria.
- No SHA anterior `ee42b631f3ce69de3f78aaebbb366acfa4e82599`, a suíte completa passou (1.150 testes); falhou apenas o guard que exigia sincronizar Word e prompt. Novo CI e build Windows são necessários para o SHA `3a7086011c61caf0a19dc8763a3276783d2e7b23`.
- Expor previsões numéricas experimentais sempre que existirem dados, domínio de aplicação e método rastreáveis; N/D permanece quando a ausência de suporte ou falha está identificada. Não estimar AGB com Sentinel-1 C-band isolada. Seguem pendentes a execução integral da Fazenda Maria Eduarda até o dashboard e validação científica externa; não homologar.

## V88.50 — restauração da integridade do código-fonte (14/11/2026)

- A auditoria encontrou bytes binários inválidos em trechos de `desktop_app.py` no commit `3a7086011c61caf0a19dc8763a3276783d2e7b23`; o arquivo não compilava. O arquivo foi restaurado do pai íntegro, mantendo a versão `3.26.33-PRECAMPO-EXPERIMENTAL` e as alterações SAR já contidas em outros módulos.
- Correção publicada no commit `0f1cb66313bb0e989a8966dde3bc183b357128e2` da branch `patches-3.26.6`, sem merge. A árvore remota do commit foi conferida idêntica à árvore local revisada.
- Verificação local no conteúdo corrigido: `py_compile` passou em `desktop_app.py` e `recent_sar_landcover.py`; seis testes direcionados de órbita, redação de URL e política de retry passaram via `unittest`; `git diff --check` passou. A suíte completa, build Windows e novo relatório CI ainda devem executar no SHA atual.
- Atualizar artefatos e documentação para o SHA `0f1cb66313bb0e989a8966dde3bc183b357128e2`. Não atribuir o teste local nem futura compilação ao SHA corrompido. O fluxo KML Fazenda Maria Eduarda → dashboard e a validação científica independente continuam pendentes; manter status experimental e não homologado.

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


## V88.55 — evidência óptica real, suíte e build Windows (14/11/2026)

- Candidata `3.26.35-PRECAMPO-EXPERIMENTAL`, branch `patches-3.26.6`, SHA de código `417e93141ec035d5bb414abb620224d490580927`. CBERS-4A/WFI é a fonte óptica prioritária; Sentinel-2 L2A, alternativa. O raster cartográfico offline não é empacotado nem apresentado como imagem orbital.
- No workflow Windows #43633560279, o smoke óptico observou CBERS real em 11/11 janelas representativas brasileiras, cada uma com cobertura reportada de 100% (aceite mínimo 95%). Sentinel-2 real no Tapajós passou. Em Sinop, o painel Tk exibiu CBERS real numa janela ao redor do centroide (canvas 673×562). Não foi usado o KML integral da Fazenda Maria Eduarda.
- O dashboard #43633560291 executou os 1.156 testes da suíte e terminou `OK`. O job reportou falha apenas no guard que apontou ausência da sincronização documental; esta atualização cobre prompt, especificação Word e especificação de solo.
- O build Windows #43633560279 terminou verde: o EXE 3.26.35 passou o autoteste em pasta limpa. Artefato Actions 14129607134 (197.843.132 bytes); SHA-256 do ZIP `3ff077bc0a002190028732a27c76de6a9332f1fd773df2d1d249fc22eda814`; SHA-256 do EXE `ac9b68b0139f4a1694e5545d98bc3eb8902c17cee4aa771caf0b040330ad6f44`. A prova de pixels reais ESA BIOMASS FH em Sinop também passou.
- O gate científico independente #43633560339 segue reprovado por ausência de validação observacional independente. Não declarar homologação. A pendência operacional prioritária é executar o KML integral Maria Eduarda do processamento ao dashboard e guardar os resultados auditáveis. As 11 janelas são amostras, não comprovam cobertura contínua para toda área e toda data do Brasil.


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

## V88.57 — auditoria arquitetural preliminar (14/11/2026)

A primeira leitura estática da arquitetura foi feita no SHA `417e93141ec035d5bb414abb620224d490580927`. Ela identificou riscos que ainda precisam de correção e regressão: o caminho com SAR local chama o processamento pesado no thread da interface (`desktop_app.py:2780`); a contingência pode solicitar novamente o pipeline SAR dentro do loop de fitofisionomias (`desktop_app.py:498–502`); o teste de handoff usa resultados de fixture e não prova execução real do core (`tests/test_core_to_dashboard_handoff.py`); a contingência IFN atualmente cobre apenas domínio específico de Amazônia/Floresta Estacional Sempre-Verde em MT (`ifn_carbon_fallback.py:51–89`); e o estado agregado deve distinguir indisponibilidade, ausência, não execução e sucesso (`desktop_app.py:2927–2936`).

A revisão é preliminar, não exaustiva. A execução integral do KML da Fazenda Maria Eduarda até o dashboard continua sem comprovação; a homologação científica segue reprovada por falta de medições independentes. Manter o status pré-campo experimental. Ver `AUDITORIA_ARQUITETURAL_PRELIMINAR_V88_57.md` no pacote para gatilhos, impactos e próximos passos. Não declarar os achados corrigidos até haver commits e regressões que os cubram.


## Atualização de continuidade V88.60 — 14/11/2026

A versão `3.26.36-PRECAMPO-EXPERIMENTAL` foi compilada no Windows e aprovada no self-test em pasta limpa. O código-fonte está no commit `7e999022759fcbb540acbc7340dcc0036385c58e`, branch `patches-3.26.6`, PR #51 ainda em rascunho. O artefato, tamanho, SHA-256 e workflow estão em `APP_RELEASE_NOTES_v3.26.36.md`.

Os smokes live do build passaram nos cenários de imagem óptica CBERS-4A/Sentinel-2, Sentinel-1 RTC/INPE em seis biomas, classificação IBGE no Tapajós e cobertura BIOMASS FH sobre AOIs com inventário. Isso comprova somente os cenários observados no workflow; serviços externos podem variar. A execução independente no computador do usuário e a análise da Fazenda Maria Eduarda até o dashboard não foram realizadas nesta sessão.

**Status científico:** versão experimental/pré-campo. O gate de homologação continua reprovado pela ausência de observações independentes de campo. Não declarar homologado nem tratar os smokes de CI como validação científica nacional.


## V88.61 — prioridade de fontes de inventários florestais brasileiros (14/11/2026)

### Regra obrigatória para estimativas baseadas em inventários

O IFN é uma fonte utilizável, não exclusiva nem hierarquicamente dominante por padrão. O universo admissível inclui inventários florestais publicados no Brasil por instituições reconhecidas e documentos técnicos verificáveis de licenciamento ambiental e planos de manejo, além de Embrapa (suas unidades), INPA, universidades, órgãos públicos e repositórios científicos/institucionais. A prioridade máxima é para inventários publicados por instituições reconhecidas, na mesma fitofisionomia e na mesma microrregião/região da AOI. Entre esses inventários igualmente compatíveis, priorizar aqueles com dados primários de parcelas abertas, coordenadas ou identificação espacial suficiente, medições e metadados. Em seguida, considerar outras fontes publicadas de fitofisionomias/regiões progressivamente menos específicas, com penalização de transferência e incerteza declaradas. IFN é fonte utilizável, sem exclusividade; deve receber a mesma avaliação de compatibilidade e qualidade. IFN pode preencher lacuna quando compatível; nunca é filtro exclusivo.

### Descoberta e acesso às fontes

- Consultar PNLA e processos/licenças de órgãos federais, estaduais e distrital; consultar dados abertos e documentos ambientais públicos associados. O PNLA é um índice/portal de informações de licenciamento, não garantia de que cada inventário esteja anexado, aberto ou em formato tabular.
- Consultar SINAFLOR/IBAMA: cadastros de PMFS e POA, planilhas padrão de Inventário Florestal 100%, recursos abertos e documentos públicos do processo. Os conjuntos públicos de autorizações/volumes não equivalem necessariamente às planilhas primárias de parcelas. Distinguir metadado de plano, inventário primário, volume declarado/explorado e dado inacessível. Respeitar restrições de acesso, sigilo e termos de uso; não contornar autenticação.
- Buscar literatura e repositórios de Embrapa, INPA, universidades, órgãos ambientais, periódicos, teses/dissertações e relatórios técnicos. IFN/SNIF permanece no catálogo como mais uma fonte, com domínio e desenho amostral próprios.
- Registrar por fonte: instituição/autoria, título, ano, DOI/URL ou identificador do processo, fitofisionomia, bioma, local/microrregião, coordenadas/área, desenho e esforço amostral, condição aberta dos dados primários, variáveis, unidades, critérios de inclusão, equações, estágio de conservação/manejo, licença/permite reutilização, data de acesso, checksum do arquivo e transformações aplicadas.

### Elegibilidade e uso

Compatibilidade ecológica com a fitofisionomia IBGE e contexto regional prevalece sobre proximidade geométrica isolada. Exigir compatibilidade de compartimento, definição de árvore/limiar de DAP, unidades, época/condição do inventário, método e domínio da equação. Não misturar inventário de floresta manejada, plantada ou área autorizada de supressão com estoque de floresta nativa intacta sem justificativa ecológica e sem rotular o domínio. Parcelas abertas com dados primários têm prioridade para recalcular distribuições diamétricas, área basal, densidade/abundância, composição e estatísticas; inventário publicado só em médias/resumos pode ser usado apenas no nível de agregação que sustenta, sem fabricar microdados. Deduplicar versões e parcelas repetidas.

Cada resultado deve permitir rastrear a contribuição das fontes e o motivo de elegibilidade/exclusão. Separar observação primária, estatística publicada, dado derivado e parâmetro transferido; propagar incerteza amostral e de transferência. Não selecionar apenas o estudo que produz valor desejado. Quando não houver fonte compatível ou acesso aos dados necessários, informar N/D e motivo; não preencher lacuna com zero, IFN distante ou média nacional. Inventários históricos apoiam parâmetros estruturais, não confirmam cobertura atual, que permanece dependente de sensoriamento e validação adequados.

### Fontes oficiais verificadas para descoberta (não equivalem a dados de parcela já ingestados)

PNLA/MMA reúne informações básicas de processos de licenciamento; IBAMA/SINAFLOR publica bases de PMFS por região, planilhas padrão de Inventário Florestal 100% e dados de volumes explorados. A cobertura e a disponibilidade dos arquivos primários variam, inclusive por integração estadual. Antes de declarar uma fonte ingerida, registrar consulta, arquivo efetivamente obtido, parsing, validação de campos e teste de elegibilidade.

### Gates de implementação

1. Catálogo versionado de inventários com esquema de proveniência e critérios de qualidade.
2. Conectores de descoberta/download legal para PNLA/órgãos, SINAFLOR/IBAMA e repositórios; aquisição automatizada deve falhar com estado tipado e preservar URL/identificador, nunca mascarar ausência como sucesso.
3. Parsers testados para CSV/XLSX/PDF/GPKG/SHP quando aplicável, com fila de revisão manual para tabelas digitalizadas/ambíguas.
4. Deduplicação espacial/temporal e auditoria dos registros de parcela.
5. Testes por fitofisionomia/região, com fontes primárias abertas priorizadas; cobertura não comprovada continua N/D.
6. Só declarar recurso operacional após commit, testes, CI e execução reproduzível com uma fonte realmente ingerida. Esta regra documental não prova que os conectores estejam implementados.


## V88.62 — incerteza obrigatória e serrapilheira (14/11/2026)

### Regra transversal para carbono

Toda estimativa de carbono deve apresentar sua incerteza junto ao valor, por compartimento e para o total, em unidades interpretáveis (tC/ha e %, e estoque total quando aplicável). Informar método de propagação, componentes incluídos, cobertura amostral, período, fonte e limitações. Incerteza estatística, erro de modelo, transferência espacial/temporal e qualidade dos dados devem ser distinguidos; não chamar amplitude de sensibilidade de IC95%. Quando houver base para IC95%, declarar como foi calculado. Se a incerteza for parcial, quantificar a parte sustentada e nomear o que ficou de fora. Se o valor estimado tiver suporte, mas não for possível mensurar a incerteza de um parâmetro ou do resultado, apresentar o valor e exibir exatamente “incerteza não mensurável”, identificando parâmetro, motivo e fonte consultada. Não substituir esse valor por N/D nem ocultar a lacuna. Usar N/D somente quando o próprio valor estimado não tiver suporte suficiente. Aplicar à biomassa acima/abaixo do solo, necromassa, serrapilheira e carbono do solo, em todas as saídas, planilhas, mapas, painéis e exportações.

### Compartimento serrapilheira

Incluir serrapilheira na estimativa de carbono de formações nativas com base prioritária nos melhores inventários e estudos gravimétricos publicados que sejam compatíveis com a fitofisionomia e a microrregião/região da AOI; privilegiar instituições reconhecidas e, entre estudos equivalentes, dados primários abertos de parcelas. O IFN é referência válida quando o desenho, variáveis, localização e domínio ecológico forem adequados, inclusive como contingência; não é fonte exclusiva. Também podem ser usados estudos de Embrapa, INPA, universidades, órgãos ambientais, dissertações, teses e artigos com método verificável.

Registrar massa seca por área, protocolo de coleta/secagem, período/estação, parcelas e esforço amostral, fração de carbono e método/fonte da fração, coordenadas ou nível espacial, condição de manejo e conversões. Não confundir massa úmida com massa seca, serrapilheira acumulada com necromassa, nem carbono orgânico do solo com carbono da serrapilheira. Aplicar fator de carbono somente quando documentado; propagar sua incerteza. Distinguir observação local, estatística publicada e transferência. Não reconstruir parcelas a partir de médias. Sem massa seca ou fator de carbono compatível, se houver um valor estimado que ainda possa ser apresentado com base explicitada, mantê-lo e marcar “incerteza não mensurável” para o componente sem suporte; se o estoque em si não puder ser estimado, apresentar N/D com motivo. Nunca preencher com zero ou média nacional.

### Gate de implementação e evidência

A regra documental não comprova que todas as telas, arquivos exportados ou cálculos do executável já cumpram o contrato. Implementação só é aceita após auditoria de cada saída de carbono, testes de presença/formato/unidades da incerteza e testes de serrapilheira com dados gravimétricos efetivamente obtidos, com a fonte e licença registradas. A versão 3.26.36 permanece pré-campo experimental até esses gates, a execução integral da AOI de Sinop e validação científica independente.


## V88.63 — correção do rótulo de incerteza nas saídas

Requisito arquitetural já estabelecido: para todo valor de carbono sustentado, declarar a incerteza. Se não for possível mensurar a incerteza de um parâmetro, preservar o valor e rotular exatamente “incerteza não mensurável”, identificando parâmetro e motivo; não substituir por N/D. N/D fica reservado ao valor sem suporte. Conferir relatório, painel, mapa, planilha e exportação, incluindo total e compartimentos. Próximo candidato: 3.26.37-PRECAMPO-EXPERIMENTAL, sujeito à CI integral e build Windows do mesmo SHA.


## V88.63 — sincronização das regressões da candidata 3.26.37

O teste integral da revisão anterior executou 1.160 testes; as regressões agora exigem “incerteza não mensurável” para estoques suportados sem incerteza quantificável. A nova revisão deve repetir CI e build Windows no mesmo SHA; manter resultado experimental pré-campo até esses gates e as validações de campo.

## Evidência de validação da candidata 3.26.37

Commit validado: `9c4c60c76ce5cd88ec6ff29420db36c2d631c8e2`. Dashboard: 1.160 testes aprovados e guard documental sem pendências (execução 43652675732). Build Windows: aprovado, incluindo smoke óptico nacional, leitura no canvas Tk, SAR real e autoteste do EXE em pasta limpa (execução 43652675738). Provas independentes reais ESA BIOMASS FH e Sentinel-1 Sinop também aprovadas. Artefato `Enform-Verde-Windows-v3.26.37-PRECAMPO-EXPERIMENTAL`: 197.799.200 bytes; SHA-256 do pacote: `sha256:65b49f7980f3058bd5b8c55fdbd806d62188b1a931e1e37bbdc28e1062832232`.

Estado: candidata experimental pré-campo. A homologação científica independente permanece reprovada por ausência de validação de campo e de execução ponta a ponta do KML completo da Fazenda Maria Eduarda até o painel; não usar estes gates como comprovação de homologação ou desempenho de campo.


## V88.64 — preservar resultados SAR quando uma etapa posterior falha (14/11/2026)

### Diagnóstico e correção proposta na candidata 3.26.38

A ocorrência de processamento SAR não prova que o fluxo do aplicativo terminou. A auditoria do worker identificou que a execução de uso da terra, carbono nativo, pedologia e fertilidade estava acoplada a um tratamento amplo de exceções: quando uma etapa posterior falhava, a fila recebia apenas o erro e os resultados SAR/uso da terra já obtidos não eram apresentados. Isso explica o padrão “pixels processados, programa aparentemente sem funcionar” sem concluir que essa é a única causa de toda falha observada.

A candidata 3.26.38 preserva as etapas válidas, informa cada erro por módulo, mantém N/D com motivo para carbono não calculável, liga os dados ao mesmo analysis_run_id e hash da AOI e tenta gravar um checkpoint local antes de entregar os resultados ao dashboard. Falha de checkpoint também deve ser registrada sem ocultar os resultados já calculados. A correção não pode converter ausência de confirmação nativa em zero nem apresentar valor de carbono sem suporte.

### Critério obrigatório de ponta a ponta

Para a Fazenda Maria Eduarda, a aprovação exige uma única execução reproduzível do KML integral até a interface e auditoria: hash e área da AOI; cenas, datas e pixels realmente lidos; classes/áreas ou erro SAR com causa; resultado de carbono ou N/D/ERRO_TECNICO por compartimento; painel e relatório com o mesmo run_id/hash; reconciliação de área explícita. O KML e seus limites não devem ser incluídos no repositório público nem em logs/artefatos públicos. A validação passada de SAR em etapa isolada não substitui esse aceite.

### Status

A candidata 3.26.38-PRECAMPO-EXPERIMENTAL está em validação. Sintaxe Python das alterações preparada e compilada localmente; a suíte completa, o dashboard, o build Windows e o teste integral do KML ainda precisam terminar sobre o mesmo SHA. Não declarar nova versão validada, artefato pronto ou funcionamento na Fazenda Maria Eduarda antes da evidência desses gates. A validação científica independente de campo continua pendente.


## V88.65 — validação dos workflows da candidata 3.26.38 (14/11/2026)

A candidata 3.26.38-PRECAMPO-EXPERIMENTAL foi validada por CI/build no commit de código dc79606d4073da23cf5c83aed54a23d500f1ef1a. Dashboard 43659083027: 1.160 testes aprovados, incluindo descoberta integral e guard documental. Build Windows 43659082998: aprovado, incluindo build e autoteste do executável em cópia limpa; smokes ópticos, leitura live Sentinel-1 nos seis biomas, leitura SAR real no Tapajós, fonte/classificação IBGE, teste SICAR e prova real ESA BIOMASS FH em Sinop. Artefato Windows Enform-Verde-Windows-v3.26.38-PRECAMPO-EXPERIMENTAL: 197.808.715 bytes; SHA-256 ZIP e85085a2085453cfd8a54e9a601fc85c2e237434c39146a83b4cc0f829f93c2a.

A prova live de pixels e os smokes nacionais comprovam os respectivos módulos e localidades, não o percurso integral do KML privado da Fazenda Maria Eduarda até o dashboard. Esse percurso segue sem evidência ponta a ponta no mesmo run_id/hash. O gate de homologação científica permanece reprovado por ausência dessa execução completa e de validação de campo. A versão continua experimental pré-campo; não declarar homologação.


## V88.66 / candidata 3.26.39 — prioridade da rota principal SAR (15/11/2026)

O relatório real da Fazenda Maria Eduarda mostrou 12 cenas VV/VH lidas e áreas candidatas, mas a classe semântica anual permaneceu N/D. Causa encontrada no código: o modelo brasileiro ENFORM_SAR_BRASIL_RF_V2 requer 12 pares mensais VV/VH; sar_landcover_lemplus.py consultava apenas o catálogo MPC, enquanto recent_sar_landcover.py já consultava MPC e INPE. A leitura de cenas e a série do classificador estavam desacopladas.

A correção em andamento conecta a busca anual aos catálogos RTC MPC+INPE, seleciona uma única origem e órbita com maior cobertura mensal, prioriza MPC somente em empate e lê COG público INPE diretamente. Não mistura provedores. Se faltar qualquer mês, a classificação se abstém e informa a origem e os meses; não inventa pares ou máscaras. O modelo segue experimental, com transferência local e incerteza declaradas.

A mudança também fecha duas falhas secundárias: o cenário de inventário não repete a consulta SAR e a falha de refresh óptico conserva a última imagem válida. Esses ajustes não substituem o aceite da rota principal.

Validação ainda pendente: regressões no CI, busca live anual e build Windows no mesmo SHA; depois, KML integral da Fazenda Maria Eduarda até classificação, painéis e relatórios vinculados pelo mesmo run_id/hash. A versão continua pré-campo experimental e não homologada.

## Prova live concluída, execução integral pendente (15/11/2026)

O workflow 43667205598 executou o modelo ENFORM_SAR_BRASIL_RF_V2 com pixels Sentinel-1 RTC reais no recorte de 0,03° perto do centroide de Sinop: 30 cenas, 12 meses da safra 2025/2026, 1.692 pixels e polígonos experimentais. O recorte foi 1.084,73 ha, não o KML integral de 1.459,91 ha. Classes experimentais incluíram soja, floresta nativa, área antrópica e cobertura úmida. Prova confirma que MPC+INPE fornece a série temporal e a inferência do modelo opera no recorte; não comprova o mapa integral, carbono no dashboard, nem imagem óptica na tela. Build Windows e dashboard no SHA mais recente ainda pendentes.

## V88.84 — estado do CI, fundo óptico e otimização (15/11/2026)

O proprietário concluiu o push da branch `patches-3.26.6`; o commit documental remoto é `df114b6b3424605397156a7079beb0b012b27297` e contém o código `f797c6320baa9713cbcba6c199cb05357f0c5de8`. Os testes SAR live/dashboard e a prova real ESA BIOMASS FH foram aprovados. O smoke Windows do worker óptico até o canvas também passou em Sinop, após aguardar estado terminal; os builds Windows completos `43756793415` e `43756788960` ainda estavam em andamento na última consulta. Essa evidência cobre o cenário testado, não garante todo ponto do país nem substitui o teste do KML privado integral da Fazenda Maria Eduarda. Não declarar o executável liberado antes do build completo e da verificação do artefato.

A candidata 3.26.44 já inclui otimização de processamento do solo: preparação única por AOI reaproveitada entre estratos e mosaicos WCS em tiles de 1024×1024 acessados por VRT indexado, reduzindo chamadas repetidas, cópias e memória de pico. Resolução e cobertura espacial são preservadas. Ainda não há benchmark Windows comparável para quantificar o ganho de tempo total; não divulgar percentual de aceleração sem medição.

## V88.85 — builds Windows e artefato confirmados (15/11/2026)

Os dois builds Windows do código `3.26.44-PRECAMPO-EXPERIMENTAL`, SHA `f797c6320baa9713cbcba6c199cb05357f0c5de8`, concluíram com sucesso nos runs `43756793415` e `43756788960` (branch `patches-3.26.6`, código revisado no commit `df114b6b3424605397156a7079beb0b012b27297`). O artefato `Enform-Verde-Windows-v3.26.44-PRECAMPO-EXPERIMENTAL` foi gerado: 197.844.115 bytes; SHA-256 do arquivo ZIP do artefato `3ca6a9e41219a931668b40a701401b99714be8a1ea6a83a9fe87fb3a50e315a9`. O job `publish-release` foi ignorado; trata-se do artefato do workflow, não de uma publicação GitHub Release.

Passaram o smoke de cobertura óptica em biomas/extremos, a prévia Sentinel-2 no KMZ público do Tapajós e o smoke Windows do worker até o canvas em Sinop, que aceita imagem óptica ou fallback IBGE visível. Passaram também a leitura SAR live no KMZ público do Tapajós e pontos representativos dos seis biomas, a classificação IBGE do Tapajós, o build e o autoteste do EXE em cópia limpa. Esses resultados são evidência dos cenários ensaiados; o KML privado integral da Fazenda Maria Eduarda e a validação independente de campo continuam não testados. Manter a versão pré-campo experimental.

O push posterior de documentação foi confirmado em `ea002502375771ea5af668dc863ba56e517e77c6`; ainda não havia status de CI associado a esse commit documental na consulta. A otimização de mosaicos e reuso por AOI já está incluída; tempo total não foi comparado em benchmark Windows.

## V88.86 — fluxo de vigor SAR e previsão PAM × clima (15/11/2026)

A auditoria da rotina de vigor encontrou que polígonos fragmentados por pixel eram usados como talhões de referência, embora o classificador exija seis referências e ao menos 30 pixels válidos em cada geometria. A correção dissolve a máscara SAR candidata e seleciona blocos espaciais não sobrepostos para alvo e referências, preservando o mínimo. Esses blocos são apenas diagnósticos internos; não são parcelas independentes nem validação de campo. Busca de catálogo e token MPC são reutilizados por AOI; cada bloco continua sujeito à leitura real VV/VH, à janela de 30 dias e ao mínimo de pixels.

A assinatura atual de candidatos a cultivo não identifica cultura. Portanto não pode ser convertida em vigor agronômico de soja/café nem alimentar previsão específica. A previsão experimental continua baseada em PAM N9 e clima/balanço hídrico e explicita a origem e safra da máscara SAR, área, modelo, fontes climáticas, uso ou não de vigor específico e transferência não quantificada. Cenário baseado em máscara anual é retrospectivo e SEM VIGOR. Linhas antigas de MapBiomas não podem contradizer o cálculo de área SAR.

Código `3.26.45-PRECAMPO-EXPERIMENTAL`, SHA `8677a8ec2a3900247aafafb9f739e3e316b6f0ce`: compilação local e 10 testes de consistência de relatório aprovados. A suíte completa local identificou 953 testes, 30 ignorados, 70 erros e 2 falhas; dependências `geopandas`, `shapely`, `rasterio` e `requests` estão ausentes e o teste live Sentinel-1 não conseguiu ler pixels. Uma falha foi o guard documental antes desta sincronização; após atualização, seus 4 testes passaram. Não declarar suíte integral, CI, build Windows nem execução KML privado como aprovados até reexecutar gates no SHA final com dependências completas. KML privado integral e validação de campo seguem pendentes; candidata não homologada.

Relatório de carbono Tapajós fornecido em 15/11: a biomassa aérea indica ESA CCI Biomass v7.0, L4 multissensor derivado de SAR. Não há produto de altura, banda/cena, pixels válidos ou distribuição de alturas vinculada à equação. Portanto, altura SAR não foi demonstrada como entrada efetiva; AGB veio do CCI derivado de sensoriamento remoto/SAR. Estoque total permanece parcial e sua incerteza não mensurável; a incerteza amostral da serapilheira exclui transferência espacial.

## V88.87 — quadros executivos claros em todas as abas (15/11/2026)

A interface agora coloca um quadro executivo com borda e título em cada uma das seis abas principais: Propriedade, Mapas e limites, SAR/AGB, Carbono, Base científica e Monitoramento agrícola. Os quadros são resumos curtos e dinâmicos; detalhes técnicos e proveniência ficam em áreas identificadas separadamente. O quadro da propriedade acompanha o carregamento do perímetro; o geográfico separa fitofisionomia potencial de cobertura atual; SAR/AGB separa descoberta de catálogo de pixels efetivamente lidos; Carbono evidencia estoque conhecido, completude e incerteza; Agricultura resume classificação/cultura/produtividade/produção e atualiza após o retorno climático; a Base científica mostra a hierarquia e os limites de aplicação dos inventários. Uma nova pesquisa limpa os resumos da AOI anterior.

Código `3.26.46-PRECAMPO-EXPERIMENTAL`, SHA `88f9b67cc4f9cfdce04e9f974cff192dcc03af82`. `compileall` e 2 testes do contrato de quadros passaram. A verificação visual local não executou porque o ambiente não possui `requests`, dependência importada por `desktop_app.py`; exigir smoke visual Windows/CI no SHA final antes do EXE. A mudança é de apresentação e não altera cálculos, sensores ou limites científicos. A candidata permanece não homologada; KML privado integral da Fazenda Maria Eduarda e validação de campo seguem pendentes.
- `tools/check_test_collection.py` inspecionou 175 módulos, mas terminou com código 1 porque módulos geoespaciais não importam sem as dependências do ambiente. O `ui_visual_standard.py` também foi bloqueado pela falta de `requests`.

## V88.90 — inventários aceitos e supressão de classes SAR extrapoladas

Inventários de instituições reconhecidas têm prioridade; anexos de licenciamento ou manejo entram apenas como último recurso quando o órgão tiver aceitado explicitamente o próprio inventário em parecer/decisão. Aprovação do processo, licença, ASV ou plano não basta. Exigir anexo identificado (URL/SHA-256), processo, decisão, método/unidades, métrica e compatibilidade. Sem requisito, não usar numericamente; sem erro amostral, declarar “incerteza não mensurável”. 9.284 autorizações PMFS+IF100 e 2.532 processos/761 ASV são localizadores, não contagens de inventário.

No Tapajós, 0,64 ha de soja equivale a um pixel da grade SAR de 80 m; 1,92 ha de café equivale a três. Não há cache de classes compartilhado na rota SAR examinada; o risco confirmado era nomear culturas fora do domínio espacial de treinamento. Para a 3.26.49, nomes específicos e forecast por cultura ficam bloqueados se a AOI inteira exceder o envelope; manter apenas área cultivada experimental genérica com cultura N/D. Não afirmar que a cultura foi copiada de Sinop nem que sua presença real foi confirmada sem o KML e verificação independente.

## V88.88 — altura SAR e uso de cultura no domínio

Consultar primeiro produtos SAR de altura validados e não inferir altura em metros a partir de VV/VH. No classificador agrícola, a validação de cultura não se transfere automaticamente ao Brasil inteiro: nomes específicos só são emitidos quando toda a AOI cabe no envelope geográfico do treinamento. Fora dele, classe agrícola permanece genérica, cultura N/D e forecast específico bloqueado. O relatório Tapajós apresentou 0,64 ha (um pixel 80 m) de soja e 1,92 ha (três pixels) de café; a análise da rota não encontrou cache compartilhado entre AOIs. O defeito foi a extrapolação de nomes específicos. A ausência do KML impede reproduzir exatamente a máscara do relatório.

## V88.98 — Fazenda Maria Eduarda e otimização ESA (16/11/2026)
O KML integral privado foi processado localmente até o payload do dashboard com a identidade da AOI preservada. A máscara anual SAR permanece experimental; o carbono retornou parcial e levou 292 s. Não declarar altura SAR: o catálogo ESA encontrou ativos BIOMASS-FH, mas a leitura sem token recebeu HTTP 401. A 3.26.52 evita o download do ZIP ESA depois de sucesso do GeoTIFF direto e corrige o smoke de canvas para verificar fallback visível durante o worker pendente. A repetição aquecida não comprovou ganho total de tempo. Exigir suíte completa e build/smokes Windows antes de distribuição; sem homologação de campo.

## Checkpoint V88.99 (16/11/2026)
O build V88.98 falhou no smoke do canvas por falso negativo: o fundo cartográfico claro de fallback tinha baixo contraste apesar de estar visível. O smoke agora usa critérios separados para fallback cartográfico e imagem óptica; canvas preto continua reprovado. O teste local específico e a CI no novo SHA precisam passar antes de liberar EXE. A integração SAR Sinop/Tapajós, a suíte dashboard, a cobertura óptica nacional e a leitura real de pixels BIOMASS FH passaram na V88.98. Carbono da Fazenda Maria Eduarda está parcial; o fluxo não está homologado em campo.

## Checkpoint V88.100 (16/11/2026)
No Windows, a fonte óptica nacional e o restante do build passaram, mas o smoke Tk continuou em timeout após a correção de limiar. O novo teste traz a janela para frente e registra geometria, status, itens e pixels do canvas no timeout, permitindo localizar a falha em vez de inferi-la. Não liberar executável até o smoke visual passar. SAR real Sinop/Tapajós passou handoff ao dashboard; ESA BIOMASS FH pixel proof passou. Carbono incompleto e nenhuma validação de campo.

## Checkpoint V88.101 (16/11/2026)
A causa do smoke Tk falhar foi identificada: a página do mapa do Notebook permanecia oculta, embora CBERS estivesse carregado no widget; `winfo_viewable=false`. O teste agora seleciona Mapas e limites e requer widget visível e pixels. Executar novamente CI completa antes do release. Nenhum EXE homologado ainda.

## V88.104 — inventários prioritários, Mexiana e desempenho (16/11/2026)

- Preservar a ordem de ingestão: (1) microdados publicados por instituições de pesquisa, com fonte, licença, método, unidade amostral e domínio verificáveis; (2) inventário ambiental somente quando o próprio anexo estiver acessível em repositório oficial e houver prova documental de aceite expresso pelo órgão; (3) inventários fornecidos pelo proprietário como referência complementar; (4) licenças, autorizações e metadados administrativos apenas como localizadores. Não contar 27 arquivos estaduais como 27 inventários independentes.
- No estado local, somente Tapajós/ORNL 1552 é dataset institucional publicado já harmonizado e pronto. A base contém ainda Mexiana/Santo Ambrósio e Jalapão, dados complementares do projeto, totalizando três datasets locais; isso não corresponde a três fontes institucionais nem a cobertura representativa nacional. IFN DAP10 set/2025, Dryad 126 parcelas, ORNL Acre 1563 e NASA/ORNL SLB são candidatos catalogados e não entram em cálculos até download e validação dos dados primários.
- Mexiana/Santo Ambrósio: manter as 167 parcelas/2.144 árvores como referência estrutural agregada para várzea estuarina na foz do Amazonas, conforme a solicitação do proprietário. Sem georreferenciamento por parcela, estratos aluviais/terras baixas agregados e sem pares SAR; não usar para calibração/validação espacial, não separar classes nem extrapolar para savanas/campos. A AGB média de 418,6616 Mg/ha é alométrica, não destrutiva; área basal 36,4256 m²/ha, DAP 25,1882 cm e altura medida 14,9603 m são derivados dos registros e da área de parcela de 250 m².
- Jalapão: conservar registros individuais, mas manter métricas por hectare como N/D enquanto área de parcela e subtipo fitofisionômico não forem comprovados.
- V88.104 adiciona paralelismo limitado entre a etapa pedológica/fertilidade e uso da terra + carbono/SAR, com no máximo duas etapas concorrentes; registra duração por etapa. A redução do tempo ainda não foi demonstrada: comparar tempos frios/aquecidos sob a mesma AOI, hash, fontes e parâmetros e reconciliar saídas antes de alegar ganho. Referência anterior: 292 s frio; repetição aquecida incompleta em 180 s.
- Candidata 3.26.53-PRECAMPO-EXPERIMENTAL. Não liberar EXE nem alegar homologação antes da suíte integral, coleta de testes, padrão visual, CI Windows e gates de módulo/visual/rede/autoteste passarem no mesmo SHA.

## V88.105 — inventários de processos aprovados e curadoria institucional (16/11/2026)

- Decisão do proprietário: inventários que fundamentam PMFS aprovado no SINAFLOR ou licenciamento ambiental aprovado são considerados aceitos pelo órgão, sem exigir decisão autônoma sobre o inventário. Exigir status de aprovação e prova oficial do processo; localizar o inventário/anexo exato, vincular ao processo e conservar URL, SHA-256, método, unidade, fitofisionomia, período, amostragem e termos de uso antes do uso numérico. Processo, licença ou contagem agregada não substitui arquivo primário nem representa parcela. Registros SINAFLOR/licenciamento não são promovidos a treino/calibração SAR sem dados apropriados e pares independentes.
- Prioridade de pesquisa publicada: quaisquer unidades Embrapa (especialmente Florestas, Amazônia Oriental, Pantanal, Cerrados e Semiárido), INPA, UFV/SIF, UFPR, UFLA, IEF-MG, ESALQ/USP, UNESP, Museu Paraense Emílio Goeldi, Jardim Botânico do Rio de Janeiro e reservas empresariais como Vale. Manter ripárias em classe/domínio próprio e distinguir nativa, plantada, várzea, Caatinga e estágio sucessional.
- Evidências desta triagem: Embrapa Amazônia Oriental/UFOPA descrevem >125 mil árvores e >8 milhões de registros MFT, ainda não baixados; IEF-MG/UFLA 2008 descrevem 4.456 parcelas em 169 fragmentos, incluindo 1.763 do Cerrado e 2.122 do Domínio Atlântico, nos dois volumes da mesma campanha; artigo Embrapa/UnB 1993 descreve 1 ha ripário, 568 árvores DAP≥5 cm, 73 espécies e 127,49 t/ha de madeira seca (não AGB/carbono); artigo Embrapa Semiárido 2014 descreve 10 parcelas de 8×40 m com DNS≥3 cm; Expedição Silvicultura 2025 tem 446 parcelas de plantios e fica separada de floresta nativa; OpenDataBio/PDBFF consultado pelo INPA está restrito; UFRA descreve 30 parcelas, UFPR quatro parcelas PELO. ESALQ, UFV/SIF, UNESP, Museu Goeldi, JBRJ e Vale seguem com buscas por arquivo primário/licença; publicações sem dados de parcela não contam como microdados.
- A base local tem 3 conjuntos com microdados: 1 institucional harmonizado (ORNL Tapajós) e 2 conjuntos do projeto (Mexiana e Jalapão). O catálogo inclui 28 agregados publicados, mas não 28 campanhas independentes; inventários apontados por processos ainda não baixados não contam como prontos. Meta de longo prazo: uma base centralizada deduplicada; não afirmar que seja a maior do país sem comparação sistemática. Maior volume só melhora carbono com representatividade, domínio compatível, método/unidades, localização, pares SAR e validação independente.
- Versão `3.26.54-PRECAMPO-EXPERIMENTAL`. A classificação por processo aprovado é elegível como inventário aceito de último recurso somente quando o documento exato, prova de aprovação, URL/hash, método e estatística existirem. A coleta automatizada não presume status de aprovação.
- A paralelização/instrumentação V88.104 continua sem ganho total medido: benchmark comparável obrigatório (mesma AOI/hash, fontes, parâmetros, cache e equivalência de saídas). O gate visual não passou neste ambiente sem display. Exigir suíte integral, coleta, DOCX, padrão visual, CI Windows, smokes e autoteste do EXE no mesmo SHA; sem homologação ou executável enquanto os gates não passarem.

## V88.106 — catálogo sob demanda (16/11/2026)
A camada SQLite de inventários foi otimizada: fingerprint SHA-256 evita reler as sementes se não mudaram; índices compostos suportam consultas por bioma/fitofisionomia, tipo, fonte, UF e microrregião; a consulta ocorre somente quando requisitada, em conexão read-only, com parâmetros SQL, limite 200 e cache LRU invalidado por mtime/tamanho/revisão do banco. A descoberta remota não roda no início da análise. Resultados do catálogo não viram valores de carbono automaticamente. A redução do tempo total ainda não foi medida por benchmark pareado. Não homologar a versão 3.26.55 até suíte completa, checker de coleção e gates Windows.

## V88.107 — referência regional do EIA Gandarela 1995
Por decisão do proprietário, registrar o inventário vinculado ao EIA/RIMA “Região Gandarela” (Itaminas/Ambiente Consultoria, 1995; Santa Bárbara e Rio Acima) como aplicável à Floresta Estacional Semidecidual da região central de Minas Gerais. O proprietário participou da equipe e confirmou campanha abrangente por transectos, identificação botânica minuciosa, DAP e altura medidos, distâncias individuais pelo método da cruzeta. O documento e resultados ainda precisam ser recuperados no arquivo FEAM e auditados. Sem GPS: manter posição relativa por transecto, não inventar geocoordenadas nem fazer pareamento árvore-pixel. Não presumir biomassa direta nem normalização por hectare sem os métodos/resultados do documento.

### V88.107 — prioridade de inventários em unidades de conservação
Incluir na expansão nacional inventários de UCs federais, estaduais e municipais, inclusive levantamentos citados ou anexos aos diagnósticos e planos de manejo. O plano e a aprovação são localizadores/evidência administrativa; extrair, vincular e deduplicar o estudo primário antes do uso quantitativo. Adicionado artigo aberto de Andrade et al. (2015), campanha de 2012 na FLONA Tapajós: 204 unidades em duas áreas; resultados publicados de densidade, área basal, composição/fitossociologia e distribuição diamétrica. As métricas de cada estrato são agregados de uma única campanha, não microdados por parcela. Preservar a discrepância do artigo (110 versus 112 unidades na Área 2), não atribuir erro global à métrica sem estatística específica. ICMBio oficial é a rota para os planos de manejo; PPBio/INPA requer validação por dataset; censo PDBFF OpenDataBio está restrito e não conta como recuperado. Estado V88.107: 63 rotas, 110 registros de catálogo, 32 linhas agregadas (4 métricas novas = 1 campanha), 3 bases primárias locais com microdados, sendo apenas uma institucional harmonizada.
Os 11 testes focados do catálogo passaram. A suíte geral, o checker de importação e o gate visual não passaram neste ambiente por ausência de dependências (`requests`, `geopandas`) e acesso SAR live; CI Windows e execução integrada permanecem pendentes. Não homologar nem alegar aceleração total sem evidência comparável.

### V88.108 — coleta de links de planos de manejo ICMBio
O coletor consulta a página oficial do ICMBio e registra páginas e documentos vinculados no domínio gov.br/icmbio como leads não quantitativos; deduplicar URL, limitar a 500 itens e rejeitar domínios externos. O link do dataset central de planos no Portal de Dados Abertos retornou 404 em 16/11/2026, então a página oficial do Instituto é a rota efetiva. Recuperar/analisar cada anexo, ato de aprovação e estudo; metadado da UC não é parcela. Teste offline específico passou. 3.26.57-PRECAMPO-EXPERIMENTAL segue candidata sem homologação, CI Windows ou benchmark de tempo.

### V88.109 — validação local integrada
Reconstruído ambiente isolado de testes em `/tmp/enform-geo-runtime` usando `requirements_desktop.txt`; imports de GeoPandas 1.2.0, Requests 2.34.2, Shapely 2.2.0 e Rasterio 1.5.2 passaram. Handoff 4/4, contrato do pipeline 6/6, checker 183 módulos; suíte 1.239 testes OK com um skip headless. No desktop gráfico, `python ui_visual_standard.py` retornou `PADRAO_VISUAL_OK`. DOCX sincronizado à versão 3.26.57 e teste documental aprovado. Permanecem pendentes build/ensaio do EXE Windows, execução do KML integral privado da Fazenda Maria Eduarda e validação independente de campo; manter experimental.
Aceitação SAR real adicional no AOI público Tapajós retornou `SAR_PROCESSADO` (259.688 pixels, 1.290,69 ha, origem `SAR_DERIVED_CCI`); resumo em `validation/acceptance_tapajos_live_v88_109.json`. A prova não substitui todos os compartimentos, dashboard, KML privado ou Windows, nem estabelece benchmark de tempo.


# Continuidade V88.110 — vigor/safra e contingência (16/11/2026)

- O cálculo de identificação agrícola, vigor SAR e previsão PAM/clima agora inicia em worker próprio, em paralelo às consultas meteorológicas de apresentação do painel. A alteração não muda os dados, modelos, equações ou parâmetros; o resultado segue protegido pelo identificador da análise antes da atualização da interface.
- A previsão contingencial histórica permanece fechada enquanto houver pixels, máscara/unidades SAR, rota sem auditoria completa, paginação incompleta, missão sem configuração ou erro técnico. Só certificado de ausência integral das rotas SAR pode habilitar a contingência. A saída MapBiomas × PAM continua rotulada como referência histórica condicional, não como previsão observada da fazenda.
- Proteção de regressão adicionada: reconhecimento atual de uso/cultura por SAR bloqueia explicitamente a contingência histórica. Teste adicional confirma que ausência de auditoria de rota também não equivale a impossibilidade de obter cenas.
- Modelos mantidos: soja/milho usam painel PAM 2015–2024, tendência microrregional e rendimento relativo FAO-56/FAO-33; vigor contemporâneo elegível condiciona a distribuição de erros LOYO. Rotas experimentais das demais culturas mantêm a matriz de quantis PAM × clima. Não foi acrescentado termo de fertilidade nem qualquer coeficiente novo.
- O paralelismo reduz espera serial entre os workers; não há benchmark comparável desta atualização, portanto não se declara redução quantitativa do tempo total.
- Pendentes: execução Windows/EXE, teste live do KML privado integral da Fazenda Maria Eduarda (sem autorização para transmitir a geometria ao Microsoft Planetary Computer), CI remota e validação de campo. Versão candidata experimental, não homologada.


# V88.111 — contingência histórica visível no dashboard — 3.26.58-PRECAMPO-EXPERIMENTAL (16/11/2026)

- O gate da contingência continua fechado enquanto houver pixels/unidades SAR, auditoria incompleta, paginação incompleta, missões configuradas sem exaustão ou erro técnico. A consulta ao dataset histórico MapBiomas/PAM só é elegível depois do certificado integral de ausência definido em `crop_mapbiomas_pam_fallback.py`.
- Quando elegível e com dados suficientes, a estimativa histórica de produção que o core já calcula agora é apresentada no painel agrícola e na auditoria: área anual de referência MapBiomas × mediana de rendimento PAM microrregional 2015–2024, acompanhada do envelope P05–P95 da série. Ela não confirma a cultura/área atuais nem substitui uma previsão observada da safra.
- Há resultado numérico por classe quando a interseção anual MapBiomas fornece área positiva e a microrregião tem pelo menos seis anos PAM numéricos. Sem esses requisitos, o painel informa N/D e o motivo; não inventa classe nem área.
- Proteção contra regressão: classe ou pixels SAR atuais bloqueiam a contingência; uma auditoria de cenas ausente também a bloqueia. Testes focados incluem desbloqueio apenas com auditorias completas e propagação da estimativa para o dashboard.
- Permanecem os modelos prévios para previsões SAR habilitadas: painel PAM+FAO-56/FAO-33 para soja/milho; matriz experimental PAM×déficit climático e vigor para as demais culturas elegíveis. Fertilidade não é covariável de produtividade. A rota histórica de emergência não substitui essas equações e não recebe ajuste climático quando a saída é apenas PAM mediana; esse limite aparece no relatório.
- Os workers de vigor/safra rodam em paralelo às consultas meteorológicas do painel, sem alterar equações. Não há benchmark comparável desta versão, portanto sem alegação quantitativa de aceleração.
- Validação: 31 testes focados SAR/vigor/safra/handoff passaram antes da alteração de apresentação. A suíte integral executou 1.241 testes, com uma falha documental por versão ausente no DOCX; após atualização, os 4 testes documentais passaram. Uma nova verificação focada da apresentação contingencial foi acrescentada. Padrão visual não pôde ser repetido sem display nesta rodada; gate visual anterior na sessão aprovou. Versão candidata experimental; Windows/EXE, KML privado integral e validação de campo pendentes.


# V88.112 — certificado de ausência Sentinel-1 para contingência PAM — 3.26.58-PRECAMPO-EXPERIMENTAL (16/11/2026)

- A busca SAR recente agora grava `vigor_scene_absence_certificate` apenas se MPC e INPE completarem a paginação e não houver nenhuma cena Sentinel-1 RTC com VV e VH compatível na janela pesquisada de 150 dias. Esse período cobre a janela máxima de 30 dias para vigor atual.
- O gate pode liberar a contingência histórica MapBiomas/PAM com esse certificado específico de ausência de cenas adequadas ao vigor, mesmo que outros sensores SAR não tenham cobertura. Continua bloqueado se houver classificação/máscara/pixels SAR atuais, se faltar diagnóstico de provedor, se a paginação for incompleta ou se ocorrer qualquer erro técnico.
- Quando liberada, a estimativa de referência é exibida no dashboard e auditoria: área anual de referência MapBiomas × mediana PAM 2015–2024, com faixa descritiva P05–P95. Requer área de classe e pelo menos seis anos PAM. Não é previsão de safra observada nem confirmação de cobertura atual; quando esses dados não existirem, o painel mostra N/D e o motivo, sem fabricar resultado.
- A rota contingencial de emergência permanece a fórmula histórica MapBiomas × PAM mediana; não aplica a matriz climática se não há dados de cena/vigor/clima completos no fluxo. As equações PAM×déficit climático/vigor permanecem nos modelos experimentais anteriores quando há mask/crop apropriados. Fertilidade não entra como covariável.
- Testes novos cobrem certificado MPC+INPE completo, bloqueio em falha de provedor, bloqueio com classes SAR existentes e exibição da estimativa no dashboard. Suíte integral: 1.245 testes OK, 1 skip headless; 45 testes focados passaram; checker inspecionou 183 módulos sem falha; documentação 4/4 e `git diff --check` passaram. O gate visual não pôde ser repetido sem display nesta execução. Execução Windows/EXE e live Maria Eduarda continuam pendentes. Versão candidata experimental.


# V88.113 — previsão contingencial PAM×clima sem vigor — 3.26.59-PRECAMPO-EXPERIMENTAL (16/11/2026)

- Com certificado completo de ausência de cenas Sentinel-1 VV/VH para vigor, o dashboard executa a previsão contingencial por classe histórica do MapBiomas e PAM microrregional, consultando clima NASA POWER. A rota normal SAR e as equações anteriores permanecem inalteradas; pixels/classificação SAR atuais bloqueiam essa contingência.
- Soja/milho usam o painel já calibrado com PAM e rendimento relativo hídrico FAO-56/FAO-33: ŷ = aᵤ + bᵤt + βg·RY + ε_LOYO. Outras culturas elegíveis usam a matriz experimental PAM×clima anterior; o clima provém de D = Σ max(0,Kc·ET₀−P), H = Σ 1(Tmax>θ) e F = −[(D−mD)/sD + (H−mH)/sH]/√2, usando ET₀ de Hargreaves. A tendência PAM usa Theil–Sen e o cálculo toma Q_y′(q[vigor,clima]) + erro LOYO.
- Sem observação de vigor, nenhuma classe é inventada. Para outras culturas, a simulação climática percorre o envelope dos quantis PAM das três classes de vigor correspondente à classe climática sorteada; vigor fica explicitamente não quantificado e o envelope não é uma probabilidade calibrada. A distribuição climática usa anos análogos e o modelo permanece experimental.
- A estimativa histórica área MapBiomas × mediana PAM segue como reserva numérica quando clima/modelo falha. O painel informa N/D para a parte PAM×clima e mantém a reserva com fonte/faixa histórica; se não houver classe mapeada ou seis anos PAM, não há base para produção e permanece N/D com motivo.
- A consulta climática da contingência é cacheada por coordenada/período dentro da execução para evitar downloads repetidos entre classes. Fertilidade não é covariável de produtividade. Não há benchmark temporal comparável.
- Testes: 62 focados SAR/vigor/safra e contingência passaram; suíte integral: 1.247 testes OK, 1 skip headless; checker inspecionou 183 módulos; documentação aprovada. O padrão visual não pôde ser repetido sem display nesta execução. Teste Windows/EXE, execução live do KML integral da Fazenda Maria Eduarda e validação independente de campo seguem pendentes. Candidata experimental.


## Ponte para checkpoint atual
Versão candidata corrente: 3.26.60-PRECAMPO-EXPERIMENTAL, checkpoint V88.123 (16/11/2026). A documentação canônica e os critérios de validação ficam no prompt v52 e na especificação técnica vigente. O smoke calcula a posição do mapa na página espacial rolável e exige canvas integralmente visível; não declarar EXE liberado antes do build Windows integral verde no SHA final.


## V88.124 — interface dos relatórios (16/11/2026)

- Corrigida a apresentação das abas de monitoramento agrícola e carbono com rolagem vertical da página, mantendo as barras internas dos relatórios. Em telas menores, o usuário consegue descer até os controles, as subabas e todo o texto.
- O resumo de carbono abandona a tabela larga e passa a listar cada compartimento em linhas responsivas, com estoque conhecido em tC e tCO₂e, densidade, incerteza disponível e área de cobertura quantificada.
- A soma de estoques conhecidos é mostrada em destaque. Quando há compartimentos ou cobertura ausentes, rotular como parcial; o total completo e a densidade não defensável permanecem N/D. Ausência não equivale a zero e cenários experimentais ficam excluídos.
- A alteração é de apresentação e acessibilidade; não altera as rotas SAR, os parâmetros de inventário, a propagação de incerteza nem os gates científicos. Foi adicionada regressão automatizada para a soma parcial. A candidata aguarda confirmação do workflow Windows e continua experimental.


### Registro de sincronização documental V88.124
A especificação Word completa é atualizada pelo workflow de sincronização acionado por `docs/spec_updates/V88.124_INTERFACE_RELATORIOS.md`; a tarefa verifica a integridade do DOCX e a inclusão do checkpoint V88.124 antes de registrar a revisão. O SHA do código e os resultados dos gates permanecem sujeitos à execução do CI.


#### Ajuste da suíte completa
A suíte revelou expectativas de formatação vinculadas à tabela antiga. Elas foram atualizadas para verificar o novo formato responsivo, incluindo a soma, a propagação estatística declarada e a sinalização de incerteza não mensurável; os critérios de conteúdo permanecem.

## V88.126 — IFN no executável e gate fechado da contingência de carbono (16/11/2026)

- A versão candidata é `3.26.62-PRECAMPO-EXPERIMENTAL`. O workflow reconstrói a base oficial IFN DAP10 (27 partições estaduais, 841.387 observações e 8.951 unidades), cruza cada centro de UA com a `legenda_1` do IBGE e inclui o banco SQLite no pacote Windows. A consulta da aplicação seleciona por localização, bioma e fitofisionomia, em ordem de proximidade.
- A associação geométrica local encontrou uma correspondência única em cada UA. Isso representa região fitoecológica potencial, não vegetação atual ou validação em campo. Coordenadas são do centro de UA; observações brutas não sustentam por si só AGB/ha, área basal/ha nem altura média do dossel.
- A altura média do dossel continua prioritariamente dependente do ESA BIOMASS FH. A base IFN é referência estrutural, não substitui FH e não está promovida a estimador operacional enquanto faltarem área/pesos de expansão e pontes alométricas validadas.
- Corrigido o bypass da contingência: `conditional_only=True` não pode autorizar cenário. Inventários só são elegíveis após certificado explícito de ausência de cenas de altura, esgotamento de todas as rotas sem erro e ausência de altura/pixels SAR quantitativos ou outra rota de altura utilizável. Erros de rede, TLS, autenticação, leitura ou processamento bloqueiam; não se reclassificam como ausência.
- Testes relevantes do IFN, do gate de contingência e do handoff: 17 passaram. Após sincronizar a especificação Word, a suíte integral passou com 1.253 testes e um skip headless; o verificador inspecionou 183 módulos. O `--module-check` local confirmou a seleção da base IFN. Compilação Python e `git diff --check` passaram.
- Build Windows, banco embutido no EXE, seleção sob `--module-check`, canvas visível e network-check seguem pendentes de confirmação no SHA final. A versão continua experimental, sem homologação científica ou EXE liberado. O KML integral privado da Fazenda Maria Eduarda ainda precisa ser exercitado no Windows.

### Continuidade

Sincronizar DOCX V88.126, repetir suíte/checker e publicar somente na branch de desenvolvimento autorizada. Acompanhar o workflow Windows até terminal. Corrigir falhas reais sem relaxar critérios de pixels, visibilidade, TLS ou ausência de cenas. Não publicar na `main` nem afirmar homologação sem os gates verdes.

## V88.127 — build Windows, IFN e prova live ESA BIOMASS FH (16/11/2026)

- O workflow Windows `44002092852` passou no SHA `f3e50322332b99bbbb25b8bbda23e4add621a701`; artefato `14294027349` (264.032.192 bytes; SHA-256 `bbc5e19ba837ff4f787d9b0cb37a51403888f087dd4221482a6c9dd3e9fb44cd`). EXE em cópia limpa, paridade Python/Windows, `--module-check`, `--visual-check` e `--network-check` passaram. Prévia Sentinel‑2 Tapajós, cobertura óptica 11/11, canvas Tk Sinop, SAR Tapajós, rota S1/INPE em seis biomas, ALOS-PALSAR com pixels Cerrado e leitura S1 VV/VH Sinop passaram.
- O runner construiu e empacotou o SQLite IFN de 488.456.192 bytes: 841.387 observações, 8.951 unidades, 27 arquivos oficiais; cruzamento IBGE Vegetação 2026 `legenda_1` único em 8.951/8.951 unidades. Seleção por localização, bioma e fitofisionomia passou no EXE e teve paridade com Python. Mantém-se como referência estrutural, sem uso como estimador de AGB/ha ou altura média do dossel.
- ESA MAAP FH: prova live em bbox de Sinop próximo ao centro da Fazenda Maria Eduarda retornou dois produtos `FP_FH__L2A`, asset real com HTTP 206 e 2.304 pixels FH; média raster 18,284244 m. A prova confirma funcionamento da rota nesta janela, não estatística do KML integral ou validação de campo. Nas AOIs de Tapajós, FH contou zero produtos; assets L1C consultados responderam 401.
- A homologação científica independente terminou bloqueada: `validation/release_evidence.json` inválido/ausente e nenhuma candidatura com dados e relatório independentes verificados. A versão 3.26.62 segue experimental. KML privado integral da Fazenda Maria Eduarda, cálculo FH→carbono no polígono completo, validação de campo e benchmark de duração continuam pendentes.

## V88.128 — FH prioritário e comparação CCI/IFN (17/11/2026)

- Regra revisada: a rota prioritária é ESA BIOMASS FH H100 integrado a parâmetros horizontais de inventários compatíveis e a modelo matemático validado no domínio. FH mede altura superior do dossel; não é AGB. Se faltarem coeficientes aplicáveis/validados para a fitofisionomia, a rota FH→AGB é N/D com motivo, mas a análise continua pelas contingências CCI AGB direto e média de AGB de UAs IFN compatíveis, apresentadas lado a lado quando houver dados para ambas. Não somar CCI e IFN.
- O estimador FH estrutural atualmente implementado é restrito aos suportes Tapajós: `AGB = k × G × H100`, com k=0,4092378415 (PF+SLF) e k=0,2945481254 (SF). Validação leave-spatial-block-out contra AGB alométrica Chave 2014: n=16/4 blocos/RMSE 26,65 Mg/ha e n=14/3 blocos/RMSE 17,55 Mg/ha, respectivamente. Não transferir coeficientes para outros domínios. A incerteza informada não cobre automaticamente o erro FH nem a transferência.
- Forma candidata sem coeficientes pré-definidos para novas fitofisionomias: `ln(AGB)=β0+βH ln(H100)+βG ln(G_total)+Σβk share(Gk)` e correção por retransformação documentada. Só calcular após ajustar e validar independentemente coeficientes no domínio; sem isso, N/D para FH→AGB e prosseguir às contingências ESA CCI AGB direta e médias IFN elegíveis. Propagação futura deve incluir erro FH, parâmetros e desenho dos inventários, coeficientes, covariância e resíduo, com Monte Carlo ou método equivalente justificável.
- Comparação IFN adicionada para o domínio atualmente disponível (MT/Amazônia/Floresta Estacional Sempre-Verde): cruza o painel SFB `AGB_Chave` com a base expandida de 841.387 observações/8.951 UAs por identidade física de UA e interseção única com a mesma IBGE `legenda_1`. Seleciona cinco UAs mais próximas, até 250 km. AGB média aritmética por UA; exibe n, DP amostral, faixa, distância e número de observações associadas. DP/faixa são descritivos e não IC95% da propriedade; incertezas de equação, expansão, posição e transferência permanecem não quantificadas. A saída é experimental, comparativa e excluída do total conhecido.
- A interface executa a comparação IFN ao lado da fonte CCI quando o produto quantitativo do estrato é ESA CCI AGB e há cinco UAs elegíveis; planilha contém aba `Comparação AGB IFN`. Se FH+estrutura local já estimar AGB, a comparação CCI/IFN não aparece como segunda estimativa da área. Outras regiões sem dados AGB compatíveis permanecem N/D; a base estrutural expandida não autoriza por si só extrapolação para Mg/ha.
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

# V88.130 — resultado final do workflow Windows 3.26.64 (17/11/2026)

Versão: `3.26.64-PRECAMPO-EXPERIMENTAL`.

- O workflow `44136053595`, no commit de código `9b3d74286a7d0efce335ce84266c6154da9ba21e`, concluiu sem falhas. Passaram a prévia Sentinel-2 Tapajós, cobertura óptica real nos 11 pontos, worker óptico até canvas Tk em Sinop, leitura SAR real Tapajós, leitura INPE Sentinel-1 RTC nos seis biomas, verificação do runtime empacotado e autoteste do EXE em cópia limpa. A prova ESA BIOMASS FH real em Sinop, em job separado, também passou.
- ZIP Windows do artefato `Enform-Verde-Windows-v3.26.64-PRECAMPO-EXPERIMENTAL`, artefato Actions `14354102535`, 264.054.505 bytes; digest do arquivo do artefato `sha256:9e19c92ea56ee423eef8d4a4cd5c0ed6d4055faa4417d707296810dbc1504cca`. Esse digest é do ZIP do Actions, não deve ser apresentado como checksum isolado do EXE.
- O artefato está disponível na execução do Actions; a etapa de publicação formal de GitHub Release foi ignorada. Build e testes técnicos aprovados não equivalem a homologação científica.
- A homologação científica independente permanece bloqueada por falta de evidência de campo/manifesto válido. A geometria privada integral da Fazenda Maria Eduarda não está neste checkout; não houve execução integral da fazenda até o relatório final. A versão permanece experimental.
- O cache do IFN evita a validação integral repetida na mesma sessão, mas não há benchmark comparável que permita declarar redução do tempo total da análise.

## V88.131 — correções após divergência no uso real (17/11/2026)

- A comparação de AGB percorre todas as fontes utilizáveis e harmonizadas presentes no pacote: painel de UAs IFN e estudos agregados publicados com AGB, preservados separadamente por fonte, fitofisionomia e incerteza. Registros de catálogo sem dados/documento extraídos continuam pendentes. Não misturar formações para preencher lacunas. Na Fazenda Maria Eduarda, hash canônico LF/CRLF reabilita cinco UAs IFN (média experimental 152,55 Mg AGB/ha), fora do estoque CCI.
- O relatório V88.130 comprovou busca de cenas ESA FH, mas não leitura de pixels; a altura média H100 não foi extraída. Propagar ao relatório a trilha de busca, download, leitura, cobertura e falhas FH/GTDX. Não declarar ausência verdadeira nem substituir altura por CCI ou inventário enquanto houver leitura pendente ou erro.
- O resumo fitossociológico deve reutilizar o resultado IFN por estrato; falta de CSV opcional não significa que a base IFN não foi carregada.
- A falha óptica persiste no uso real. Exibir no painel espacial a fonte efetivamente carregada e as falhas detalhadas de cada provedor, por AOI. Imagem só passa se pixels ópticos reais estiverem visíveis no canvas. Testes públicos perto de Sinop não comprovam a geometria privada nem o computador do usuário.
- Vigor é funcionalidade crítica: permitir janelas menores (16/8/4/2 ha) para máscaras SAR experimentais fragmentadas, mantendo pureza ≥90% e seis blocos de referência independentes. Incorporar suas probabilidades na distribuição do modelo PAM×clima somente com pixels Sentinel-1 VV/VH atuais, cena datada e saída de vigor utilizável. Não apresentar assinatura estrutural genérica como vigor de cultura; máscara 2025/26 não confirma cultura atual.
- Gate da previsão: as probabilidades de baixo/adequado/alto vigor devem ser completas, finitas, estar entre 0 e 1 e somar 1; exigir identificador da cena Sentinel‑1 e data/fuso válidos (no objeto de vigor ou em cada cena aceita), aquisição não futura e dentro de 30 dias. Dado inválido não condiciona resíduos PAM; mostrar previsão sem vigor e motivo.
- O cartão executivo agrícola precisa identificar vigor por cultura, mostrar se a previsão o utilizou e explicar N/D; detalhes das cenas e métricas ficam na auditoria.
- A job completa de regressão precisa materializar a base oficial IFN antes dos testes que dependem do SQLite; falhas por banco ausente indicam ambiente de teste incompleto.
- A versão 3.26.65 permanece experimental. Só declarar correção FH e óptica após teste Windows com geometria integral, pixels extraídos/renderizados e os gates técnicos do SHA final.


### Checkpoint V88.132 — pós-regressão Windows
- No workflow de regressão, executar `tools/harvest_ifn_dap10_2025.py`, `tools/ingest_official_inventory_microdata.py` e `tools/build_ifn_ibge_crosswalk.py` nessa ordem antes de testes que selecionam parcelas IFN por local, bioma e legenda_1. A base sem cruzamento espacial não é operacional para essa seleção.
- Preservar a exigência de scene_id + acquisition_utc e probabilidades válidas para incorporar vigor na distribuição Monte Carlo da previsão. A ausência deve retornar motivo legível com “sem data” e/ou ID ausente.
- A área de 2 ha é avaliada em EPSG:6933; a asserção automatizada pode usar tolerância de 1e-6 ha devido à reprojeção. Não reduzir o gate de pureza ≥90%.
- O smoke CBERS-4A/WFI do Windows passou com pixels visíveis no canvas; 11/11 locais do smoke óptico nacional receberam pixels reais. Isso não substitui a execução com o KML integral privado da Fazenda Maria Eduarda.
- ESA BIOMASS FH real leu pixels na prova independente de Sinop; continuar reportando FH da fazenda como pendente até leitura com a geometria da propriedade. Homologação científica permanece independente.


### Checkpoint V88.133 — vigor e estado executivo
- Na primeira ponta do monitoramento agrícola, a seleção do vigor deve usar o validador `_usable_dated_vigor` do pipeline. Cena precisa ter `scene_id` e `acquisition_utc` dentro dos 30 dias, válida, sem ser futura, além de probabilidades normalizadas.
- O painel só declara `vigor usado/incorporado` quando `fields[cultura].vigor_model_audit.used_in_yield_distribution` confirma a aplicação no modelo. A auditoria do modelo é fonte de verdade para os flags executivos. Em N/D/rejeição, preservar motivo e não afirmar incorporação.
- A regressão deve testar `monitoring_forecast` com cena datada sem ID e verificar que o forecast recebe vigor N/D, que os flags ficam falsos e que o texto executivo informa a não incorporação.
- A distribuição vigente de safra continua PAM × clima; vigor SAR elegível condiciona a distribuição de resíduos Monte Carlo PAM, sem introdução de outro modelo concorrente nesta build.
