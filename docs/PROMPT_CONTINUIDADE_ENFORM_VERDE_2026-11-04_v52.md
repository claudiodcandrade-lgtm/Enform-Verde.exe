Warning: truncated output (original token count: 40216)
Total output lines: 765

Warning: truncated output (original token count: 46970)
Total output lines: 909

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
## V87.82 — Renovação ESA MAAP e substituição seg…30216 tokens truncated…s), fontes registradas no cadastro, fontes com correspondência exata e fontes efetivamente utilizáveis. Assim `0 compatíveis` fica distinto de `registro não consultado`; não inferir bioma/fitofisionomia nem extrapolar estudo.
- Candidata `3.26.70-PRECAMPO-EXPERIMENTAL`. Regressão integral e handoff do SHA `3999058` passaram; o Windows desse SHA está no build/autoteste final. As mudanças adicionais de auditoria e inventário exigem gates no SHA `3.26.70` antes de distribuir. Homologação científica permanece sem validação independente de campo.

## V88.149 — autenticação ESA MAAP no aceite do EXE Windows (18/11/2026)

- O autoteste EXE em pasta limpa do SHA anterior falhou no aceite Tapajós com `ERRO_TECNICO_ROTA_PRIORITARIA`. Diagnóstico da configuração do workflow: o job de prova MAAP separado recebia `ESA_MAAP_OFFLINE_TOKEN`, mas o processo compilado do aceite Windows não recebia a credencial. Isso impedia o download autorizado FH mesmo que a rota live Linux funcionasse.
- Correção: o passo de aceite do EXE recebe a variável secreta via ambiente, e `automatic_pipeline` usa `ESA_MAAP_OFFLINE_TOKEN` quando o chamador não informa um token explícito. A credencial nunca é escrita na auditoria; o token explícito do usuário mantém precedência.
- Adicionado teste unitário de precedência do token explícito e fallback à variável de ambiente. Nova candidata `3.26.71-PRECAMPO-EXPERIMENTAL`; requer regressão, handoff, build e autoteste limpo no SHA final. Não converter falha de autenticação em ausência de cenas ou promover CCI/inventário sem certificado.


## V88.150 — evidência do runner Windows e auditoria FH no EXE (18/11/2026)

- Revisão de código executada no SHA `f874140edebbe35ae503de91942a0e7fc3344f42`; workflows associados concluídos com êxito: Build Windows (run `44308456785`), suíte integral/dashboard (`44308456740`, 1.285 testes) e handoff SAR live (`44308456797`). O gate científico independente permanece reprovado enquanto não houver validação de campo independente; o pacote continua experimental/pré-campo.
- Fundo óptico: passaram a prévia Sentinel-2 sobre o KML público real do Tapajós, a consulta de pixels ópticos em biomas/extremos geográficos e o smoke worker→canvas Tk em Sinop. Isto confirma chegada da imagem ao canvas no runner, não valida todas as conexões/condições de cada computador do usuário.
- SAR nacional: passaram fallback de pixels Sentinel-1 RTC em locais representativos dos seis biomas, leitura VV/VH na amostra Sinop, e leitura quantitativa ALOS-PALSAR no gate do Cerrado.
- Altura FH live: no handoff, ESA BIOMASS `FP_FH__L2A` retornou H100 com 333 pixels florestais válidos em Sinop (média 23,35 m) e 1.263 em formação florestal no KML de teste do Tapajós (média 18,73 m); houve também quatro pixels savânicos em Sinop e um no Tapajós. O EXE compilado leu 1.512 pixels válidos FH no Tapajós em um candidato. Essas provas são das AOIs públicas/de teste; não são a geometria privada da Fazenda Maria Eduarda.
- AGB permaneceu distinta de FH: sem equação/coorte de inventário horizontal compatível aplicada, ESA CCI AGB v7 foi selecionada como produto AGB separado. A comparação de inventários pesquisou IFN expandido, painel SFB/IFN e registro harmonizado de publicações; nenhuma UA/agregação elegível de AGB com correspondência exata na mesma classe foi encontrada para as duas AOIs de teste. Comparação N/D, sem somar CCI e inventários nem extrapolar outra fitofisionomia.
- Lacuna de auditoria identificada no autoteste compilado: embora o leitor FH tenha registrado pixels válidos, os campos de resumo `priority_height_route_status` e `priority_height_route_gate` vieram nulos. A integração live independente reporta `ALTURA_SAR_PROCESSADA` e os pixels H100; portanto a evidência atual aponta para omissão no resumo/assertividade do teste de aceitação, não demonstra falha de leitura. Corrigir a propagação desses campos e fazer o EXE acceptance exigir proveniência/estado FH explícitos antes de afirmar que a auditoria compilada está completa.
- O EXE 3.26.71 foi compilado e aprovado em pasta limpa. SHA-256 do executável: `10171e9a27c9124ecaedee477ae6eccf5c092831e39a189f65bea109b125e4b5`. Artefato ZIP do runner: `sha256:6a9b88d8c6aa55ead7728495f0d245a1cf6786585bf217c9da9531fd42d06894` (run 44308456785, artifact 14431111511).
- Próxima correção obrigatória: incluir no JSON de aceitação `height_route_status`, produto, métrica, contagem/média de pixels e estado do gate CCI; quando FH tiver pixels válidos, falhar o acceptance se esses dados forem nulos ou inconsistentes. Atualizar também a especificação Word quando a revisão de código for incorporada.


## V88.151 — bloqueio de seleção ESA CCI sem FH ou calibração (18/11/2026)

A seleção de AGB foi corrigida para manter ESA BIOMASS FH como rota prioritária. Qualquer pixel FH válido bloqueia a promoção do ESA CCI; a rota FH deve ser calibrada com variáveis horizontais compatíveis dos inventários (área basal, DAP e distribuição diamétrica) e continuar até resolver o modelo aplicável. Falha técnica, falta de modelo calibrado ou lacuna de auditoria não caracteriza ausência de cenas.

O ESA CCI só pode ser considerado após certificado completo, sem erros e com ausência real de pixels FH nas rotas prioritárias, e após existir calibração CCI–inventário compatível com o bioma e a fitofisionomia. O gate exige no mínimo 30 pares parcela–pixel, cinco sítios independentes, fonte documentada, validação independente e RMSE positivo. A versão atual do pipeline não injeta um registro calibrado; assim, CCI permanece bloqueado como estimativa até que o conjunto de calibração elegível seja produzido e integrado. O produto CCI bruto não substitui essa calibração.

A base IFN expandida empacotada contém observações arbóreas DAP≥10 cm e cruzamento com legenda_1 do IBGE, mas as tabelas inspecionadas não fornecem, por si só, pares co-registrados FH/CCI–parcela com AGB de referência auditada. O painel AGB candidato do IFN-MT mantém os marcadores de equação auditada, fitofisionomia verificada e validação científica em falso. Portanto, não gerar coeficientes, não publicar estimativa microrregional como calibrada e não converter médias estruturais em AGB.

A implementação em 18/11/2026 corrige a regra de contingência e adiciona testes para impedir a promoção do CCI com FH disponível ou sem calibração. A calibração microrregional por fitofisionomia ainda não está demonstrada em dados independentes e não pode ser rotulada como operacional/homologada. A rota de raízes ainda usa Cairns et al. como equação generalizada para formações florestais altas; a seleção da equação mais adequada por ecossistema e a propagação integral de sua incerteza seguem pendentes.

Condição para fechar a pendência científica: incorporar parcelas georreferenciadas e datadas com desenho amostral/área conhecida; AGB de referência rastreável, incluindo método alométrico e unidades; valores coincidentes de FH e CCI; estratos de bioma e legenda_1; validação por sítios externos; resíduos, viés, RMSE/MAE/R² e cobertura de intervalos. Persistir os modelos e o domínio aplicável em registro versionado, e validar a aplicação no EXE Windows ponta a ponta. Somente então disponibilizar a estimativa única calibrada.


## V88.152 — inventário oficial SFB para calibração microrregional (18/11/2026)

O Painel de Biomassa e Carbono SFB/IFN é uma fonte oficial pública disponível e deve ser incorporado ao conjunto expandido, não tratado como inexistente. A ingestão de build baixa a tabela por unidade amostral e a tabela de equações usadas, valida as colunas, registra URLs, quantidade de registros e SHA-256 e preserva arquivos no pacote/auditoria. Os metadados oficiais descrevem AGB média em kg/ha, variância por UA, área, tipologia atribuída, equação e coordenadas centrais. Biomassa de referência derivada de alometria oficial deve manter esse rótulo, domínio e equação; não é medição destrutiva.

Para calibrar FH, calcular H100 de campo a partir das árvores IFN com DAP e altura, respeitando o desenho amostral e área efetivamente medida; parear com pixels/footprints ESA FH da mesma UA e períodos compatíveis. Validar correção de FH por produto, definição H100, fitofisionomia IBGE e região, usando sítios inteiramente externos ao ajuste. O erro de concordância da altura deve ser separado do erro do modelo de AGB.

Para os parâmetros horizontais da estimativa, resumir área basal por hectare, DAP médio, densidade e distribuição diamétrica como médias de inventários confiáveis, priorizando a menor região compatível e legenda_1 IBGE. Respeitar pesos e áreas do desenho; agregar uma vez por UA para evitar pseudorreplicação. Ajustar AGB com FH e parâmetros horizontais em observações parcela–pixel compatíveis; os mesmos agregados regionais podem ser preditores no alvo, mas não substituem os pares de treinamento e validação.

Para ESA CCI, usar as AGB do painel SFB/IFN como referências de inventário após compatibilizar unidade, suporte espacial, máscara de vegetação e data do inventário. O CCI é a única estimativa AGB contingencial, só se a ausência FH estiver certificada sem erros; aplicar a calibração regional e propagar a incerteza do CCI, variância do inventário, amostragem e validação. O resultado final deve mostrar uma única AGB selecionada.

Biomassa abaixo do solo: preferir equação alométrica de raízes publicada e aplicável à fitofisionomia; quando inexistente, usar razão raiz/parte aérea oficial compatível, incluindo a dispersão e deixando explícito que não é alometria local. O campo `valor_r` do painel SFB é uma razão/fator, não deve ser descrito como equação alométrica. Não aplicar Cairns universal se existir uma equação ou referência estratificada mais apropriada.


## V88.153 — altura H100 de referência IFN para calibrar FH (18/11/2026)

A altura ESA BIOMASS FH é H100: média da altura das 100 árvores mais altas por hectare. A função `derive_inventory_h100` calcula o valor correspondente usando alturas totais do IFN, área amostrada validada e identificador de árvore; múltiplas hastes da mesma árvore contam uma vez. Ajusta a fração da árvore de borda quando 100 × área não é inteiro e recusa a parcela se a contagem observada for insuficiente ou se faltarem bioma, fitofisionomia e microrregião.

Os pares de calibração precisam combinar esse H100 de campo com pixels ESA FH no mesmo suporte espacial e período compatível. Ajustar por produto, região e legenda_1; separar sítios externos do treinamento. Reportar erro absoluto e relativo, viés, RMSE, MAE, R² e intervalo dos resíduos. O limiar de missão publicado para FH é RMSE <30% em florestas com árvores >10 m, mas essa meta não substitui métricas locais nem validação independente. Não declarar o modelo operacional enquanto o pareamento real e a validação externa não forem concluídos.


## V88.157 — checkpoint de continuidade (18/11/2026)

Código mais recente: `894835bae7fdf35a972efe652f95a79ce55e413f` na branch `patches-3.26.6`. O commit anterior normaliza datas IFN em ISO (texto, datetime e serial Excel); este commit impede que datas ausentes provoquem comparação entre `None` e texto ao calcular mínimo/máximo e inclui regressão unitária. O contrato rápido pré-campo passou.

Diretriz FH/AGB: usar a base expandida inteira de inventários confiáveis, não somente IFN. Parear FH ESA BIOMASS com alturas compatíveis, espaciais e temporalmente coincidentes; usar demais inventários para variáveis horizontais mesmo se não sustentarem H100. Modelos microrregionais por legenda_1 integram FH, área basal, distribuição diamétrica e outras covariáveis elegíveis, com validação independente e incerteza propagada. Mostrar uma estimativa AGB única. CCI só após ausência física certificada de FH sem erro de software; médias de inventário só após inexistência real de SAR utilizável. FH válido sem modelo aplicável não equivale a ausência de cenas. Raízes por alometria adequada e incerteza explícita.

Evidência: prova MAAP Sinop leu 2.304 pixels FH (média 18,284 m), o que confirma aquisição/leitura, não calibração. O build anterior falhou no autoteste AGB amplo do Tapajós apesar de FH válido. O gate independente de homologação científica continua reprovado por falta de validação de campo. O IFN/SFB materializado e as contagens agregadas não representam pares FH–inventário. Em 18/11/2026, os workflows Windows, SAR live e dashboard no SHA acima ainda estavam em etapas longas de materialização/testes e não havia novo EXE/checksum publicado. Manter 3.26.71 como pré-campo até que os gates terminem com sucesso no mesmo SHA; não declarar versão operacional sem evidência.


## V88.158 — continuidade após falha do transporte (18/11/2026)

A ingestão IFN e o crosswalk concluíram: 841.387 observações em 8.951 UAs, com correspondência única à IBGE legenda_1. O job Windows falhou no CSV SFB porque o servidor interrompeu a conexão antes dos últimos 45.819 bytes. Correção adiciona streaming, retentativas limitadas, resume por Range com Content-Range e validator ETag/Last-Modified, reinício quando Range é ignorado, verificação de tamanho e escrita atômica após validação do CSV. Cinco testes locais passaram; a correção aguarda CI.

Timeouts do probe PronaSolos em três AOIs são indisponibilidade técnica de um passo opcional (continue-on-error), não evidência de ausência de dados. A homologação científica segue bloqueada; nenhum novo EXE foi publicado. Aplicar as diretrizes FH/AGB e contingências já registradas na seção V88.157 sem afrouxá-las.

## V88.160 — inventários publicados como balizas horizontais mult fonte (18/11/2026)

Inventários publicados totalizados por região e fitofisionomia são evidência útil mesmo sem parcelas abertas. Para cada fonte compatível, exibir separadamente métricas horizontais como área basal, densidade e estrutura diamétrica com citação, região, unidade e incerteza publicada. Usar como baliza regional/fitofisionômica e plausibilidade, nunca como parcela sintética, pareamento FH-pixel, validação de campo ou coeficiente de calibração por si só. Não agrupar estudos incompatíveis nem inventar variância ausente. A consulta e apresentação acompanham qualquer rota primária FH/AGB; não ficam restritas ao ESA CCI. Exibir a limitação de saturação tropical da CCI sempre que a auditoria SAR a registrar.

A candidata `3.26.72-PRECAMPO-EXPERIMENTAL` incorpora referências estruturais no resultado e na planilha para qualquer método primário. A regressão local completa passou: 1.288 testes OK, 1 ignorado; a coleção de 187 módulos não apresentou falhas. A base IFN oficial foi materializada: 841.387 observações em 8.951 unidades, todas com correspondência única a legenda_1 do IBGE. Ainda faltam workflow Windows no SHA atualizado, aceite compilado SAR e revisão científica independente; manter caráter pré-campo até evidência desses gates.


## V88.162 — gate CCI antes da aquisição (18/11/2026)

O pipeline avalia o gate completo da contingência ESA CCI antes de consultar ou baixar o raster. Quando há pixels FH válidos, a pesquisa prioritária está incompleta/tem erro técnico ou não existe calibração CCI–inventário validada, registrar `NAO_ADQUIRIDO_GATE_BLOQUEADO` e `download_skipped=true`; não fazer o download. Isso separa a decisão de não adquirir do erro técnico em uma tentativa efetiva e evita I/O remoto inútil. Nunca tratar falta de modelo FH como ausência de cenas. A correção não cria modelo de AGB: FH válido sem modelo aplicável continua N/D explícito, e CCI segue bloqueado. Candidata 3.26.73 pré-campo até regressão integral, build Windows, aceite SAR→dashboard e revisão científica independente no SHA final.


## V88.164 — aceite Tapajós com referências agregadas compatíveis (18/11/2026)

A aceitação anterior encontrou pixels SAR, mas descartou referências publicadas devido à comparação literal da fitofisionomia. O filtro reconhece apenas relações IBGE pai/subformação explicitamente listadas, mantendo o bioma exato e rejeitando formações irmãs. Santos et al. KM72 e KM117 aparecem como referências agregadas separadas, não são agrupadas, adicionadas ao estoque, usadas como calibração FH ou convertidas em parcelas. Com SAR e sem modelo quantitativo aplicável, o aceite registra `SAR_E_REFERENCIAS_INVENTARIO_OK_AGB_N_D`; AGB permanece N/D e não há contingência sem SAR nem homologação. Candidata `3.26.74-PRECAMPO-EXPERIMENTAL`; código no commit `c49badba6f79cf854a1808552b1583d17dffc870`; EXE depende de build/autoteste Windows verde no mesmo SHA.

## V88.165 — indexação sob demanda das bases de inventários (18/11/2026)

A consulta às bases de inventários deve evitar leituras repetidas integrais. O registro harmonizado CSV de referências é carregado em cache de memória, compartilhado entre fontes, AGB e estrutura, com invalidação por caminho/tamanho/`mtime_ns`. Na base IFN SQLite de 466 MiB, filtrar primeiro pela chave indexada bioma + legenda_1 IBGE e consultar árvores apenas das UAs selecionadas pelo índice de UA. A auditoria de integridade já é cacheada por revisão do arquivo. Preservar os mesmos registros e resultados; falha técnica nunca vira ausência ecológica. Limite: o cache em memória usa metadados do arquivo, sem hash integral a cada consulta. Versão `3.26.75-PRECAMPO-EXPERIMENTAL`; regressão integral local passou após o Word (1.312 testes OK, 1 ignorado); 191 módulos, autoteste e module-check passaram. Build Windows e aceite do EXE limpo continuam pendentes no SHA final. Não chamar de homologado.

A sincronização da especificação Word V88.165 é automatizada pelo workflow `.github/workflows/sync-v88-165-word.yml`, acionado pela entrada `docs/spec_updates/V88.165_INDICE_SOB_DEMANDA_INVENTARIOS.md`; ele atualiza a versão canônica e a cópia DOCX versionada.

## V88.166 — evidência de inventário dentro do EXE (18/11/2026)

O aceite Windows da V88.165 revelou falha operacional concreta: o PyInstaller copiava `structural_aggregate_evidence_v1.csv` apenas para `dist/data`, mas `inventory_agb_comparison` procura o registro junto aos módulos congelados em `_internal/data`. O arquivo agora é incluído pelo próprio comando PyInstaller no destino interno. O gate também confere o arquivo e os IDs Tapajós KM72/KM117, e o relatório de aceite expõe estado, diagnóstico, quantidade e fontes do registro; erro de leitura é `ERRO_TECNICO_LEITURA_REGISTRO_INVENTARIOS`. Após sincronização do Word V88.166, regressão integral passou: 1.312 testes OK, 1 ignorado; coleção de 191 módulos, self-test e module-check passaram. Novo build e aceite EXE limpo no SHA `7df90886f3bc087994a614cc37686f461be46a04` seguem pendentes. AGB permanece N/D sem estimador quantitativo elegível; não homologado.

Workflow de sincronização documental: `.github/workflows/sync-v88-166-word.yml`, acionado por `docs/spec_updates/V88.166_PYINSTALLER_INVENTORY_EVIDENCE_RUNTIME.md`.

O teste integral Windows detectou que a sincronização inseria o checkpoint, mas deixava a capa do DOCX na versão anterior, fazendo `test_versioned_spec_is_valid_docx_with_current_update` falhar. `tools/update_spec_docx.py` e o workflow agora atualizam programaticamente o estado e a linha V88.166/3.26.76 da capa; há testes de regressão para esses campos. Nova suíte completa e novo build/autoteste do EXE precisam concluir no SHA corrigido antes de liberar. Não reduzir o gate documental nem classificar essa falha de documentação como falha científica.
