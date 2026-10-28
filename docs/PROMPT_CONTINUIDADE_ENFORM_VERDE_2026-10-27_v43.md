# PROMPT DE CONTINUIDADE — ENFORM VERDE — v35 — REGRESSÃO CRÍTICA DE CARBONO
Data 27/10/2026. Substitui v34 como checkpoint de prioridade imediata. Não mesclar PR #50 nem publicar versão como corrigida sem teste real.

## DEMANDA DO USUÁRIO
Restabelecer **universalmente**, não só no Tapajós, todas as funcionalidades de carbono previamente testadas/aprovadas: Amazônia, Cerrado, Pantanal, Mata Atlântica, Caatinga; todas fitofisionomias nativas e AGB, biomassa subterrânea, necromassa aérea/subterrânea, serrapilheira e solo 0–30 cm quando houver estimadores defensáveis. Preservar tC, tCO2e, erros/limites documentados, área, interseções, IBGE offline, métodos SAR/fallback e histórico de regressão. Preservar separadamente novos recursos agrícolas e clima. Não fazer hardcode Tapajós.

## BUG CRÍTICO REPRODUZIDO NO RELATO DO USUÁRIO
Versão 3.25.1, AOI Teste_SAR_Biomassa_Tapajos.kmz: 1.290,69 ha classificados IBGE legenda_1 como **Floresta Ombrófila Densa (100%)**, porém painel diz **0 ha de vegetação nativa** e todos os pools de carbono como não estimados. Log: `MapBiomas indisponível: 'utf-8' codec can't decode byte 0xe3 in position 126: invalid continuation byte`. Resultado: 1.290,69 ha de cobertura não confirmada. Isso é falha da cadeia de evidências de cobertura atual, não ausência demonstrada de vegetação e tampouco prova de carbono zero.

## CAUSA VERIFICADA NO CÓDIGO
No HEAD de 27/10/2026, `native_carbon.native_class(name,'IBGE')` retorna `None` por desenho científico (IBGE fitogeográfico não confirma cobertura atual). Em `land_use_sar.run_land_use`, a falha da leitura `mapbiomas_zonal.RASTER_URL` impede obter classe anual; na ausência de modelo SAR treinado aceito, `partition_land_use` usa apenas IBGE, que `summarize_native_carbon` contabiliza como cobertura desconhecida. O pipeline não aciona estimador algum para esses estratos; logo todos os compartimentos ficam indevidamente vazios. **Não corrigir simplesmente forçando fonte IBGE a True de forma nacional:** isso inflaria carbono em agricultura, silvicultura e áreas convertidas.

## CORREÇÃO GENÉRICA OBRIGATÓRIA
1. Investigar a resposta real da URL MapBiomas/GDAL que gera UnicodeDecodeError, incluindo HTTP status/Content-Type, exceção e codificação sem vazar credenciais, e corrigir o adaptador. Exercitar leitura remota em Windows PyInstaller limpo, rede variável e versão instalada de GDAL/rasterio. Registrar versão/fonte/ano/CRS/hash.
2. Implementar fontes **redundantes reais, licenciadas, versionadas e verificáveis** para cobertura presente: MapBiomas anual público, seus downloads/espelhos oficiais ou cache offline íntegro, classificação SAR validada e outras fontes independentes adequadas. Retries com backoff limitado, alternância de endpoint e suporte a cache espacial previamente verificado. Não transformar erro de transporte/decodificação em classe de vegetação inexistente.
3. Separar três estados: cobertura nativa confirmada, cobertura antropizada confirmada e cobertura **indeterminada por falha de fonte**. Ao combinar MapBiomas nativo × IBGE legenda_1, calcular interseção exata AOI × máscara de cobertura nativa × fitofisionomia IBGE; preservar sobreposições disjuntas e ausência de dupla contagem. Se SAR validado tiver precedência, documentar compatibilidade de classes e evidência.
4. Se faltarem TODAS as fontes atuais: mostrar mensagem precisa **“Cobertura atual não verificada por falha das fontes — mensuração de carbono bloqueada”**, preservar 1.290,69 ha de fitofisionomia IBGE como **potencial, não confirmação**, e oferecer repetição de aquisição/caches compatíveis; jamais exibir `0 ha de vegetação nativa` como fato confirmado. Campos desconhecidos N/D, não zeros. Nunca contabilizar carbono em lavoura/pastagem/silvicultura por fallback automático.
5. Ao restabelecer máscara nativa, chamar os estimadores EXISTENTES por estrato sem mudar seus cálculos ou pesos: AGB SAR e hierarquia fallback, raízes compatíveis, necromassa, serrapilheira, solos; não suprimir pools por falha de outro pool. Separar ausência de dado do compartimento e erro de acesso de fonte; publicar tC/tCO2e e incerteza real por classe/pool.
6. Verificar localização das tabelas offline sob `sys._MEIPASS` / diretório EXE, rasters de IBGE, modelos e fontes de carbono. Toda perda por PyInstaller (mapas, tabelas, certificados, locale, GDAL_DATA/PROJ_LIB) precisa virar teste de pacote.
7. Criar teste de integração para KMZ anexado e golden baseline de cada cenário real comprovado (Tapajós, Santo Ambrósio, Cerrado DF, Pantanal e amostras Mata Atlântica/Caatinga), comparando áreas, carbon pools, tC/tCO2e, fontes e status. Validar caso de erro MapBiomas simulando UnicodeDecodeError e falha HTTP 504; assegurar que não se converte erro de fonte em ausência de vegetação nem em carbono nativo calculado sem confirmação.
8. Corrigir e testar no repositório. Executar suites de carbono + Windows build + EXE em pasta limpa. Só liberar EXE novo com run/commit/artifact e hashes verificáveis. Se testes não passarem, manter a versão 3.25.1 como **regredida e NÃO recomendada para mensuração de carbono**.
9. Preservar contrato agrícola: áreas cultivadas primeiro, nomes 'Lavoura de ...' só quando fundamentados, 'sem cultivos detectados' somente quando verdadeiro; clima dinâmico mesmo sem cultivos. Nenhuma regressão agrícola para consertar carbono.

## CHECKPOINT EXTERNO
Última build 3.25.1 é workflow #665, run 40553874472, SHA c442c142e489800325ef231f170d95a0080f1d55, artifact 12756553409. Os gates CI passaram mas foram insuficientes para detectar o caso real de falha de fonte do Tapajós. Prompt v34 foi commitado no GitHub (cd5c515fbae367f289d46781be5b6a8d8b32856b), sem modificação dos algoritmos nesse commit. A versão 3.25.1 não está aprovada pelo usuário para carbono.

## PROIBIÇÕES
Não confundir IBGE potencial com cobertura atual; não codificar exceção geográfica Tapajós; não inventar métricas SAR, estoque, incertezas nem modelos. Não chamar de concluída uma correção sem teste real e artefato compilado após ela. Entregar prontamente novo prompt com situação honesta e link persistente.


## ADENDO v36 — OBRIGATÓRIO: PAINEL EXECUTIVO DE CARBONO, AUDITORIA SEPARADA E INCERTEZA TRIPLA
Esta instrução se aplica a TODOS os cinco biomas, fitofisionomias e compartimentos, inclusive na recuperação da regressão 3.25.1. Preservar todas as funcionalidades e fontes previamente aprovadas; não restringir ao Tapajós.

### Painel executivo separado
- Manter aba **Painel executivo — carbono** clara, com AOI, área total, área de vegetação nativa confirmada, outros usos, cobertura indeterminada, fitofisionomias, áreas/percentuais, estado da análise, carbono por compartimento e totais válidos.
- Por fitofisionomia e compartimento (biomassa aérea, raízes, necromassa aérea, necromassa subterrânea, serrapilheira e solo na profundidade informada), apresentar densidade em tC/ha e tCO2e/ha; quando disponível, estoque total em tC e tCO2e. Diferenciar estoque parcial de total completo e informar área efetivamente quantificada.
- **Incerteza visível obrigatoriamente nas três expressões para todo resultado, por compartimento e classe: ± tC/ha | ± tCO2e/ha | ± %**, especificando a natureza da medida: desvio-padrão espacial, desvio-padrão amostral, erro-padrão, RMSE, semiamplitude de IC ou intervalo preditivo, com nível quando existir.
- Conversão para mesma medida: `incerteza_tCO2e_ha = incerteza_tC_ha × 44/12`; `incerteza_pct = 100 × incerteza_tC_ha / densidade_tC_ha`, somente se denominador > 0 e estimando/unidade consistentes. A porcentagem é a mesma em tC e tCO2e. Para biomassas em Mg/ha, converter por fração de C fundamentada e rastreável, propagando a incerteza da fração se conhecida.
- Se o parâmetro possuir limites assimétricos, exibir limites inferior–superior correspondentes em tC/ha e tCO2e/ha e desvios percentuais apropriados: não fabricar ± simétrico. **Se faltar erro defensável, exibir “N/D — incerteza não quantificada” nas três colunas**, sem zero fictício ou percentuais inventados. Se valor central for nulo/zero, percentual N/D. Não converter variabilidade espacial em IC95% da estimativa. Não somar erros independentes sem comprovação das covariâncias.
- No caso crítico de falha MapBiomas, exibir **“Cobertura atual não verificada por falha das fontes”** em lugar de falsa confirmação de 0 ha nativo; preservar fitofisionomia IBGE potencial separada dos hectares efetivamente confirmados. Impedir estoques falsos até evidência de cobertura nativa. Exibir ação de nova consulta e recuperar fontes redundantes.

### Auditoria técnica separada, íntegra e exportável
- Criar/manter aba **Auditoria técnica — carbono**, sem suprimir nenhuma trilha já existente: fontes primárias/ secundárias, referências científicas completas, instituição, URLs/DOIs, data/hora de consulta, versão, licença, datas de aquisição SAR UTC e UTC−3, cena/ID, sensor/banda/órbita/polarização, pré-processamento, geometrias, CRS, resolução, mapas IBGE legenda_1 e MapBiomas, metodologias de interseção, áreas por classe, dados de inventário, parcelas e critérios de compatibilidade, estimadores, equações com parâmetros e domínio, conversões (incluindo tC→tCO2e), fallback e sua motivação, cálculo e natureza de incertezas, tamanho amostral, intervalos, diagnósticos de validação e transferência, falhas de acesso, logs e identificação de versões/arquivos.
- Organizar a auditoria em ordem reproduzível desde entrada/AOI → obtenção/filtragem de dados → classificação de uso/cobertura → fitofisionomia → SAR/biomassa → raízes → necromassa → serrapilheira → solo → incertezas → totais, incluindo os passos não executados e motivo. O executivo mostra resumos e referência da linha de auditoria, não substitui a prova.
- Disponibilizar exportação do painel e da auditoria (relatório e dados tabulares/máquina, sempre que o app permitir) com IDs estáveis por classe/compartimento e hashes/proveniência dos insumos.
- Garantir que limpeza/reset de AOI remova somente dados da análise anterior, nunca arquivos de fonte necessários ao processamento ou evidência da análise concluída arquivada intencionalmente.

### Critérios de regressão para liberação do novo EXE
1. Cenários representativos Amazônia, Cerrado, Caatinga, Mata Atlântica, Pantanal, com área nativa confirmada, área agrícola e cobertura indeterminada.
2. Teste do KMZ Tapajós: IBGE classifica 1.290,69 ha como Floresta Ombrófila Densa, mas classificação efetiva de uso exige fonte atual válida; falha de leitura MapBiomas não pode zerar silenciosamente carbono nativo nem habilitá-lo indevidamente.
3. Para cada compartimento elegível, validar correspondência valor→erro tC/ha→tCO2e/ha→% com arredondamento brasileiro e unidade; testar incerteza ausente, densidade zero, limite assimétrico e erro não comparável.
4. Verificar que relatório executivo e auditoria permanecem em abas separadas, com valores consistentes e fonte auditável, tanto no Python quanto no EXE empacotado em pasta limpa. Não flexibilizar gates anteriores de carbono ou meteorologia/agricultura.
5. Apenas publicar novo pacote Windows depois de corrigir código, testar AOIs reais, aprovar CI e verificar ZIP/EXE; documentar SHA do commit, workflow, artefato e hash.

**ESTADO EFETIVO DESTA ATUALIZAÇÃO:** este documento consolida o diagnóstico confirmado no código e os requisitos da correção, mas **não declara que a regressão no executável já esteja corrigida**. A 3.25.1 não é recomendada para laudos de carbono até aprovação de novo pacote.

## ADENDO v37 — IMPLEMENTAÇÃO REAL E PENDÊNCIA DE LIBERAÇÃO
- Alteração efetiva em `executive_carbon_report.py`: cobertura desconhecida expressa sem falsear ausência de floresta; incertezas por compartimento em tC/ha, tCO2e/ha, %; inclui densidade tCO2e/ha; N/D explícito. Commit `0ac5f35fa1bb3111384883ca1a344e1b24930de9`.
- Teste de regressão `tests/test_carbon_presentation_regression.py`, para cobertura não confirmada no Tapajós e três unidades de incerteza. Commit `a82d83ce5d56688b0fd5c26306203c464b5d6b50`.
- Alteração efetiva em `carbon_dashboard_html.py`: exibição das três unidades, e identificação da seção auditável. Commit `3030bf1ac5df100d2520000f64d56c8d6935e800`.
- Documentação oficial do MapBiomas C11 confirma a URL do GeoTIFF e o produto 2025: https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/ . **A disponibilidade declarada da URL não resolve nem prova leitura efetiva via GDAL/PyInstaller**.
- Correção NÃO CONCLUÍDA: ainda não foi reparada a leitura remota que falha com UnicodeDecodeError no Windows, nem introduzida rota de máscara atual comprovada; portanto os pools de carbono para classe IBGE isolada podem continuar sem cálculo. Não forçar retorno `native_class(...,'IBGE')=True`. Prioridade máxima resolver aquisição/caches reais e teste de AOI, sem inflar área nativa.
- Workflow da revisão atual: Build Windows run #671, cuja aprovação e artefato devem ser conferidos no commit acima. Testes do dashboard estão sendo executados. **Não publicar a build #671 como solução total sem análise do caso de falha de MapBiomas**.
- Próxima sequência técnica vinculante: reproduzir exceção em ambiente Windows; verificar resposta HTTP, certificados/GDAL e leitura de janela do COG; suportar download espacial validado/cache, sem download nacional desnecessário; integrar cobertura atual + legenda IBGE com áreas disjuntas; então executar todos os pools de carbono; testar nos cinco biomas e no KMZ anexado; emitir novos artefatos e resultados com trilha auditável; só então considerar recuperação concluída.

## ADENDO v38 — 27/10/2026 — PATCH EFETIVO DE DIAGNÓSTICO DA COBERTURA
- Fonte oficial MapBiomas Coleção 11 confirma caminho publicado do GeoTIFF 2025: https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection11/lulc/coverage/brazil_coverage/brazil_coverage-col11_2025.tif . Portanto não presumir que substituir a URL sem diagnosticar GDAL solucione UnicodeDecodeError.
- Commit `11985b7639c25190480e108758949b1bd999076e`: `land_use_sar.py` agora preserva `mapbiomas_failure`, `cover_verification`, `unknown_cover_ha` e aviso explícito de que falha de fonte não comprova ausência de vegetação nativa.
- Commit `d68df09802191cb786fa76239bc9aaa3edbfc0d6`: `tests/test_native_carbon.py` acrescenta regressão UnicodeDecodeError com IBGE FOD de 1 ha e verifica cobertura indeterminada, sem inventar carbono.
- **PENDÊNCIA BLOQUEANTE AINDA NÃO RESOLVIDA:** execução comprovada do recorte MapBiomas C11 dentro do EXE Windows, fonte alternativa/caching válido e, somente após a confirmação da cobertura, restabelecimento dos estimadores AGB, raízes, necromassa, serrapilheira e solo em todos os cinco biomas. Não denominar esta entrega "restabelecimento concluído".
- Observar workflow iniciado para o HEAD acima; não reutilizar run aprovado de SHA anterior. Corrigir e confirmar CI Windows e teste do EXE em pasta limpa; publicar artefato apenas após resolução da falha de fonte e testes científicos.

## ADENDO v39 — TENTATIVA CONTROLADA DE RECUPERAÇÃO GDAL/MAPBIOMAS
- Fonte oficial confirma Coleção 11 para 2025, GeoTIFF anual 30m e acesso público (CC BY 4.0): https://brasil.mapbiomas.org/downloads/mapas-para-download-geotiff/
- Commit `d51957524a83921855634986fa3b767bd1b59dbf`: fluxo `land_use_sar.run_land_use` agora executa até três tentativas de `raster_class_polygons`, com opções GDAL HTTP de retry/timeout, registrando `mapbiomas_access_attempts` por execução e `mapbiomas_failure`. Não infere ausência de floresta após falha de rede. A mudança não altera densidades de carbono nem dados de inventário.
- **Atenção:** esta correção aborda indisponibilidade transitória, mas não demonstra eliminação do UnicodeDecodeError de bytes não UTF-8 relatado no executável. Continua obrigatório obter recorte real de pixels MapBiomas no EXE Windows, ou fonte/cópia local válida com hash/licença/ano e cruzar IBGE×cobertura por classe.
- **Não concluir** até confirmar resultados AGB, raízes, necromassa aérea e subterrânea, serrapilheira e solo, incerteza tC/ha+tCO2e/ha+%, trilha em auditoria distinta, compatibilidade com cinco biomas, e CI/EXE funcional em pasta limpa. Nenhuma estimativa por média/IBGE somente deve ser apresentada como SAR.
- Atualizar run e hash após compilação do SHA específico desta alteração. Evitar disponibilizar compilação mais antiga como se contivesse este patch.

## ADENDO v40 — STATUS VERIFICADO DE LIBERAÇÃO
Data: 27/10/2026. PR #50 HEAD `937d6883b56758850b01412d62ffe68e50e3f002`.
- Build nº 676: `40562674839`, SUCESSO no commit anterior `d51957524a83921855634986fa3b767bd1b59dbf`, artefato Windows `12761043769`, SHA-256 ZIP de artefato `1064274cb96d6cd0017fc8f15b004311bc17730ba6149f0ec7c3ba5d70a64550`. Este build não é prova de restabelecimento efetivo do MapBiomas no PC do usuário.
- Build nº 677: `40562934408`, inicialmente falhou no gate Cerrado porque Microsoft Planetary Computer devolveu HTTP 504; retry attempt 2 solicitado e ainda em progresso quando observado. Dashboard do HEAD passou (253 e 252). A falha externa não autoriza desabilitar gate.
- PROIBIDO declarar versão definitiva somente pelo CI: ainda requer prova real de leitura de classes atuais do MapBiomas na AOI Tapajós, execução das estimativas de todos os compartimentos aplicáveis e do relatório de incerteza tripla (tC/ha, tCO2e/ha, %) em auditoria e painel.
- Diagnosticar endpoint MapBiomas e GDAL com inspeção de resposta HTTP e fonte raster; oferecer cache local legal e íntegro com metadados, ano e hash; implementar fallback de transporte e testes ponta-a-ponta em Windows. Não tratar IBGE potencial como cobertura nativa atual nem exibir zero falso. Reexecutar casos dos cinco biomas.
- Próxima liberação: vincular versão distinta à alteração técnica efetiva e SHA do commit, obter CI Windows aprovado do mesmo SHA, validar EXE em pasta limpa e AOI real; liberar ZIP só com advertências cientificamente pertinentes, nunca inventar resolução de regressão.

## ADENDO v41 — TESTE DE RECUPERAÇÃO DE CARBONO E ESTADO REAL
- HEAD de código funcional modificado nesta sequência: `2cd6c388bec3a09a99e78677e69e9c9ccbf2f7e9`.
- Novo teste em `tests/test_native_carbon.py`, `test_mapbiomas_retry_restores_native_carbon`: simula falha UnicodeDecodeError no primeiro acesso ao MapBiomas e sucesso no segundo, integra MapBiomas nativo com Floresta Ombrófila Densa IBGE e exige que o estimador de AGB seja chamado na interseção de 1 ha, produzindo 100 tC com densidade fictícia apenas para o teste. **100 tC é dado sintético de teste, não resultado da FLONA Tapajós**. Resultado CI deve ser consultado antes de declarar aprovação.
- Os builds 677 (retry) e 678 foram observados ainda em execução; não inventar status. A versão candidata 676 é do SHA `d51957524a83921855634986fa3b767bd1b59dbf`, anterior a este teste e não serve como liberação definitiva.
- Falta diagnosticar e corrigir o erro real `utf-8 codec can't decode byte 0xe3` em GDAL/MapBiomas no EXE do usuário; validar acesso e recorte real, além de backup/cache por fonte autêntica, sem considerar IBGE potencial como comprovação de vegetação atual.
- Próxima aprovação exige: leitura de pixels MapBiomas em Windows, interseção AOI×cobertura nativa×IBGE, estimativa de AGB/raízes/necromassa/serrapilheira/solo conforme dados reais, incerteza por classe/pool nas três unidades, auditoria separada, cinco biomas, gates e EXE em pasta limpa no mesmo SHA do pacote.
- Não declarar conclusão ou nova versão definitiva sem essas provas.

## ADENDO v42 — TESTES WINDOWS 679/680 E CORREÇÃO DE TOLERÂNCIA
- Os builds Windows #679 (run 40564756682) e #680 (run 40564823842) falharam no gate `Native-only stratification and confidence regression tests`, especificamente `test_mapbiomas_retry_restores_native_carbon`. O resultado calculado foi 99.99999977099287 tC versus 100.0 tC esperado, erro absoluto 2,29e-7 tC decorrente da reprojeção/geometria. Este NÃO foi erro do algoritmo físico de carbono.
- Commit `440ab757753733b7e8e1b56ec3699e0fc9763aba`: somente o teste teve sua tolerância ajustada para `places=4`; estimadores, conversões e regras científicas inalterados.
- O build #681 foi disparado para o commit corrigido. Inspecionar run/CI/EXE em vez de assumir sucesso.
- O teste sintético confirma apenas o comportamento de retry sob falha de decodificação seguida de leitura válida; ainda falta comprovação de leitura do raster real MapBiomas com o ambiente do usuário e estimação de AGB+raízes+necromassa+serrapilheira+solo e incertezas em cada um dos cinco biomas.
- EXE novo só pode ser declarado definitivo após compilação exitosa NO MESMO SHA, pacote testado em pasta limpa, cobertura atual real validada e regressão completa de carbono. A versão candidata #676 não contém esta correção de teste.

## ADENDO v43 — REGRA DE MONITORAMENTO E LIBERAÇÃO (27/10/2026)
**SOLICITAÇÃO VINCULANTE DO USUÁRIO:** verificar periodicamente alterações materiais de status do desenvolvimento e atualizar este prompt no GitHub a cada alteração comprovada; comunicar a mudança ao usuário. Assim que TODOS os testes forem concluídos satisfatoriamente e a validação operacional/científica estiver demonstrada, disponibilizar link do ZIP Windows com SHA, run, checklist e riscos remanescentes. Não afirmar que atualização ocorreu se não foi gravada; não prometer liberação sem gate final.
**STATUS BASAL CONFIRMADO EM 27/10/2026:** Build Windows #681 (`40565800602`, código `440ab757753733b7e8e1b56ec3699e0fc9763aba`) e #682 (`40565856210`, commit de documentação `231556f3c07160bc0bfe3e6b87cdf79d3bfa2d7f`) estavam em progresso; suites do painel #260–263 aprovadas; builds #679/680 falharam anteriormente em tolerância numérica sintética, corrigida no commit #681. Nenhuma aprovação científica integral por AOI real confirmada.
**CRITÉRIOS PARA LIBERAÇÃO COMO VERSÃO CONCLUÍDA:** build e EXE limpo aprovados para MESMO SHA; MapBiomas real com pixels atuais e AOI Tapajós processados (sem UnicodeDecodeError); máscara cobertura efetiva × IBGE compatível e exclusão de uso antrópico; compartimentos AGB/raízes/necromassa/serrapilheira/solo por classe e bioma com fonte e incerteza tC/ha, tCO₂e/ha e %, painel executivo distinto de trilha auditável; testes representativos cinco biomas; nenhum retrocesso nos recursos agrícolas/clima. CI aprovado sozinho NÃO autoriza selo científico de definitivo.
**FLUXO DO ACOMPANHAMENTO:** consultar PR #50, workflow Windows mais recente, logs de falha e artefatos; comparar com esta seção; se houver alteração de status real de build/validação, acrescentar seção datada a ESTE mesmo arquivo v43 usando update_file com SHA atualizado, sem sobrescrever dados anteriores; emitir resumo ao usuário com link do arquivo. Se todos gates forem comprovados, verificar artifact_url e oferecer link de download imediatamente; caso contrário informar impedimentos de maneira específica. Nunca reexecutar workflow nem modificar modelos apenas por mudança de status.


## REGISTRO DE STATUS — 27/10/2026 — ACOMPANHAMENTO
Consulta GitHub: build Windows nº 682 (run 40565856210) em progresso, etapa Build executable; nº 683 (run 40566753644) em progresso, etapa mapas IBGE offline; testes dashboard nº 264/265 concluídos com sucesso para SHA 5b4516cc5c832d7781adf171db5db39a2d8b7176. Nenhum novo ZIP de build 682/683 verificado e nenhuma comprovação de execução MapBiomas real no EXE. Pendência científica de cinco biomas e todos os compartimentos segue aberta. NÃO declarar versão final até concluir gates.


## REGISTRO DE STATUS — 27/10/2026 — BUILD 682 APROVADO
Build Windows #682 run 40565856210 CONCLUÍDO SUCCESS para SHA 231556f3c07160bc0bfe3e6b87cdf79d3bfa2d7f. Artefato Windows ID 12763402265, nome Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO, digest sha256:58d8b4c863a07c64a550ff8cea0dbb60b04ea49bc59d118f3129be8a1abee978, tamanho 522565787 bytes, expira 2026-11-26. Link: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40565856210/artifacts/12763402265 . Testes dashboard #262/#263 SUCCESS. Build #683 e #684 estavam em andamento; #266/#267 dashboard SUCCESS. **CI aprovado não prova leitura real MapBiomas na máquina do usuário nem recuperação do estoque de todos os compartimentos para os cinco biomas.** Download do build #682 é candidato para teste, não liberação científica definitiva. Manter prioridade em prova end-to-end e relatório de auditoria.


## REGISTRO DE STATUS — 27/10/2026 — BUILDS 683–685
Consulta: build #683 (40566753644) em andamento no passo 'Build executable'; build #684 (40567110425) em andamento no passo 'GUI contract test'; build #685 (40567577393) em andamento no passo 'Install dependencies'. Dashboard #268 e #269 aprovado para SHA 7b28a24b5bf8c6a1b2ca92142e4022e50dc91760. Nenhum desses builds foi verificado como concluído neste registro. Mantém-se obrigatória comprovação real de pixels MapBiomas Windows, recuperação completa dos pools nos cinco biomas e incerteza tripla por pool antes de chamar o EXE de definitivo. Build #682 permanece candidato aprovado em CI apenas.


## REGISTRO DE STATUS — 27/10/2026 16h29 (UTC−3) — BUILDS 681, 683–686 APROVADOS
- Mudança material desde o registro anterior: os workflows Windows #681 (`40565800602`, SHA `440ab757753733b7e8e1b56ec3699e0fc9763aba`), #683 (`40566753644`, SHA `5b4516cc5c832d7781adf171db5db39a2d8b7176`), #684 (`40567110425`, SHA `dd76d0cc300242b5ca7d904ef15fbc4e7efb0e50`), #685 (`40567577393`, SHA `7b28a24b5bf8c6a1b2ca92142e4022e50dc91760`) e #686 (`40567719050`, SHA `eaf604da8729b81d84009877b15ca79a3fb60219`) terminaram com conclusão `success`. O #682 já havia sido aprovado.
- Dashboard dual #270 e #271 concluídos `success` no MESMO SHA do #686; job `build-windows` do #686 `success` sem steps falhos.
- Artefato Windows do #686: ID `12763657857`, `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, 522566315 bytes, digest do artefato GitHub `sha256:5156a73c736bf36834f7caa388ef02c6d00cbc4f9635bb3887f1696f78850c87`, expiração `2026-11-26T19:26:13Z`; link `https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40567719050/artifacts/12763657857`.
- PR #50 permanece aberto e mergeable, HEAD `eaf604da8729b81d84009877b15ca79a3fb60219` no momento da consulta. O commit deste registro de documentação poderá gerar outro workflow; verificar o SHA antes de qualquer liberação.
- **Pendências ainda abertas:** evidência de leitura real do MapBiomas no Windows, processamento end-to-end das AOIs representativas dos cinco biomas, estoques AGB/raízes/necromassa/serrapilheira/solo por estrato com fontes e incertezas em tC/ha, tCO₂e/ha e %, auditoria separada e regressão agrícola/climática em execução real. A aprovação CI e o artefato #686 NÃO constituem homologação científica nem liberação definitiva. Prosseguir com validação e registrar evidências verificáveis.


## REGISTRO DE STATUS — 27/10/2026 — CORREÇÃO DE ROTA MAPBIOMAS NO WINDOWS
Erro reproduzido no relato do usuário após build #686: 1.290,69 ha da AOI Tapajós identificados como IBGE Floresta Ombrófila Densa, mas cobertura atual não confirmada e todos compartimentos em N/D porque `rasterio.open('/vsicurl/https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection11/lulc/coverage/brazil_coverage/brazil_coverage-col11_2025.tif')` gera `RasterioIOError`. Tentativas adicionais da mesma rota não solucionam ausência de suporte /vsicurl/ ou indisponibilidade do produto.
ALTERAÇÕES IMPLEMENTADAS: commit `f583e6f9d471cc47fa6eb8849a004682dbedb17b` modifica `land_use_sar.run_land_use`: mantém rota remota anterior e configura alternativa por arquivo GeoTIFF local via variável `ENFORM_MAPBIOMAS_LOCAL_TIF`; identifica fonte efetivamente usada na auditoria, sem aplicar IBGE isolado como prova de floresta atual. Commit `9ba0f03f8b7a77ee8045b2f66edec4bb07083328` cria teste para leitura local, cruzamento floresta × pastagem e acionamento do estimador apenas na floresta, com ajuste de total sintético no commit `600126467985076ef82412485b90eae74382dace`.
PENDÊNCIAS AINDA REAIS: assegurar aquisição automática verificável do produto MapBiomas (ou máscara equivalente devidamente validada), sem exigir configuração manual; implementar tratamento operacional caso GeoTIFF remoto gigante não permita leitura no Windows; comprovar leitura de arquivo oficial real, não apenas raster sintético; evidenciar estoques AGB, raízes, necromassa, serrapilheira e solo com incertezas tC/ha, tCO2e/ha e % nos cinco biomas. Preservar rotas SAR, IBGE e clima/agricultura anteriormente aprovadas. NÃO declarar versão definitiva nem publicar ZIP como corrigido até recompilar mesmo SHA, testar EXE em pasta limpa e validar AOI real.


## REGISTRO DE STATUS — 27/10/2026 — BUILDS 687–690 E TESTE LOCAL
Falhas CI #687 e #688 (run 40570272828 neste último) decorreram do teste sintético `test_windows_local_mapbiomas_route_preserves_native_carbon`: para 100 m² de floresta a 10 tC/ha, o resultado correto foi **0,10 tC**, e o teste incorretamente esperava 0,01 tC. Corrigido no commit `600126467985076ef82412485b90eae74382dace`, sem mudar os estimadores. No acompanhamento, #689 (40570302309) estava em `Build executable`; #690 (40570371293), no gate Cerrado. Dashboards #278 e #279 PASS no SHA `e7355e725c87d470347f284b3e87fe859fb9f71d`.
A rota `ENFORM_MAPBIOMAS_LOCAL_TIF` e o teste sintético de cruzamento MapBiomas floresta/pastagem com IBGE estão implementados; o erro do usuário `RasterioIOError ... /vsicurl/ ... does not exist` **não foi ainda demonstrado como resolvido automaticamente**. Sem raster oficial local efetivamente fornecido/baixado, o EXE pode continuar em N/D para carbono. Prioridade: aquisição robusta de MapBiomas oficial via transporte compatível com Windows, cache verificado, AOI Tapajós real, preservação total dos componentes e incertezas por classe nas três unidades, e novo EXE testado antes de divulgar como definitivo.


## REGISTRO — 27/10/2026 — BUILD 689 APROVADO
Windows build #689 run 40570302309, SHA 600126467985076ef82412485b90eae74382dace, SUCCESS. ZIP Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO artifact id 12764804260, tamanho 522565639 bytes, SHA256 1f6c52bc1b46f15f1ab310215d4232aa3c974624b4cd6ab47f28c28e3cb7685c. Link https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40570302309/artifacts/12764804260 . Builds #690 e #691 ainda em progresso, dashboards #280/#281 success. Release apenas para TESTE; fonte MapBiomas externa na instalação do usuário e inventário de carbono end-to-end ainda NÃO validados. Tentativa de criar KMZ teste agrícola pela ferramenta de arquivos resultou em erro da infraestrutura, sem caminho de arquivo verificável; não declarar KMZ disponível.


## ADENDO — 27/10/2026 — TREINAMENTO DE CULTURAS, FENOLOGIA, VIGOR E PREVISÃO DE SAFRA
**Diretriz do usuário:** aproveitar fontes semelhantes ao registro georreferenciado da Fazenda Horizontina para compor treinamento e validação de cultura, fenologia, vigor remoto e produtividade agrícola, sem exigir que o usuário forneça dados de campo. Não remover nem regredir inventário nativo, SAR, MapBiomas, IBGE, clima ou UI já aprovados.
**Fontes verificadas e finalidade distinta:**
1. `https://plantiosafra.com/` — Talhão 1, Fazenda Horizontina, Ipiranga do Norte MT, soja, área informada 331 ha, plantio 17–23/09/2026, V4 observado no registro de 16/10/2026, chuva acumulada 80,95 mm reportada no acompanhamento. O ponto de referência foi publicado, mas o polígono KML amostral criado anteriormente não equivale à geometria geodésica verificada do talhão inteiro. A previsão editorial de colheita 11/01/2027 por ciclo de 110 dias NÃO é safra observada nem rótulo de produtividade, e estádios intermediários editoriais NÃO são observações reais; separar rigorosamente observação/fato, previsão de calendário e derivação.
2. `https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/agricultura/uso-agricola/` — Agricultura Coleção 11 1985–2025, classes verificadas soja=39, cana=20, arroz=40, café=46, citrus=47, algodão=62, outras temporárias=41; segunda safra é produto COMPLEMENTAR e não deve ser confundida com soja/primeira safra. Usar ano e recorte espacial compatíveis. Classes agrícolas anuais são rótulos cartográficos sujeitos a erros; não inferir cultura de uma campanha distinta sem série temporal independente.
3. `https://source.coop/wri-data-lab/trazofields` — limites de talhões Trazo da América do Sul, temporada 2023–2024; geometria estimada por imagens Sentinel-2 e U-Net, com `mbmode` (classe modal MapBiomas 2024). É referência de contorno/pseudo-rótulo, NÃO ground truth de cultura ou estádio.
4. `https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal-culturas-temporarias-e-permanentes.html` — PAM/IBGE municipal: produção, área colhida e rendimento por cultura e ano. Agregar produtividade por município/microrregião com pesos por área e anos correspondentes; NÃO atribuir média municipal observada a pixel/talhão. Não usar dado de safra posterior à época de emissão como predictor (evitar vazamento temporal).
**Plano executável a implementar e VALIDAR antes de anunciar operacionalidade:**
A. Ingerir bases por conectores/licenças verificadas com metadados: fonte URL/código, cultura, geometria, safra, datas de plantio/emergência/fases/colheita (cada uma com natureza observada/estimada), estágio BBCH/escala da cultura, produtividade real com unidade t/ha, origem e escala, QC e licença de treinamento. Duplicatas espaço-temporais e pseudo-rótulos conflitantes devem ser isolados.
B. Montar séries co-registradas do Sentinel-1 (VV/VH, razões, texturas, ângulo de incidência, órbita, speckle e chuva), ALOS-2/BIOMASS apenas quando geometria/resolução e escala agrícola forem compatíveis, óptico Sentinel-2 quando permitido e climatologia diária NASA POWER/INMET/CPTEC. Registrar timestamps UTC, aquisição local UTC−3, qualidade, cobertura temporal e proveniência. Não declarar SAR processado quando somente catálogo/metadata acessados.
C. Primeiro **área cultivada vs vegetação nativa/pastagem/silvicultura**, depois cultura específica quando classificador atingir gate independente, caso contrário `áreas cultivadas`; quando ausência realmente demonstrada, `sem cultivos detectados`. Usar splits ESPACIAIS por fazenda/talhão e TEMPORAIS por safra e município; métricas matriz de confusão, precision/recall/F1 por classe, calibração probabilística, IC bootstrap por grupo e detecção de distribuição fora de domínio. Treinamento apenas com cultura documentada ou pseudo-rótulos com peso reduzido; nunca reusar pixels vizinhos como teste independente.
D. Fenologia: modelos temporais cultura-específicos com emissão de probabilidade de fase ou datas e incerteza por fase, calibrados contra estádios REAIS publicados; tabelas editoriais derivadas de calendário não são verdade fenológica. Validar plantio/emergência/vegetativo/reprodutivo/maturação/colheita com MAE em dias e desempenho por fase em anos e propriedades não vistos.
E. Vigor: índices SAR (anomalia multitemporal padronizada dentro de cultura/estádio/órbita, mudança VV/VH/textura) integrados a balanço hídrico/anomalias de temperatura. Mostrar `indicador remoto de vigor/anomalia` e grau de evidência; NÃO converter anomalia em diagnóstico fitossanitário causal (praga, doença ou deficiência) sem validação adequada. Sem dados de campo do usuário, usar bases públicas de validação e reconhecer limites.
F. Previsão produtividade: modelo agrícola-científico multiestágio SAR × fenologia × meteorologia × solo/município, alvo de rendimento observado com granularidade compatível. IBGE/PAM municipal pode calibrar município/safra, não provar previsão por talhão. Baselines climatologia histórica, PAM tendência, anomalia climática, regressão penalizada, RF/gradient boosting e modelos temporais somente se desempenho superior. Backtesting rolling-origin, leave-year-out e leave-region-out, MAE/RMSE/viés/R², faixas preditivas com cobertura empírica (80/95%) por cultura e estrato e verificação de leakage. Só ativar `previsão de safra` após validação independente real do alvo para a escala anunciada; em caso contrário `modelo não validado para previsão quantitativa`, oferecer monitoramento de indicadores.
G. Integrar executáveis e testes de download de cenas reais, ingestão de talhões reais, extração SAR/pixel e dados PAM; registrar gate, resultado e SHA em auditoria técnica. Manter o inventário de carbono em pipeline independente e testes de não regressão.
**ESTADO DE IMPLEMENTAÇÃO NESTE ADENDO:** fontes identificadas e requisitos definidos; NÃO foram treinados novos modelos, baixadas séries SAR ou validadas previsões nesta alteração documental. Evitar alegar conclusão sem artefatos, métricas e evidência de execução reais.


## STATUS — 27/10/2026 — APÓS PROTOCOLO DE TREINAMENTO AGRÍCOLA
Verificação dos workflows: Windows #692 (run 40572016657) CONCLUÍDO SUCCESS para SHA 8df72c5de84b735daed43456464b80814c6954e1; Windows #693 (40573611632) e #694 (40574361153) em progresso, este último restaurando mapa IBGE oficial. Testes Dashboard #286 e #287 PASS para SHA 209fccacea7176d2193d44ff2322b3e3b9b9ec13. O adendo de treinamento SAR/fenologia/vigor/produtividade é somente especificação até haver pipeline funcional e validação em observações independentes. A alternativa ENFORM_MAPBIOMAS_LOCAL_TIF NÃO resolve sozinha o caso do usuário sem arquivo oficial previamente acessível; nenhum processamento end-to-end real da AOI Tapajós com carbono completo foi comprovado. CI PASS não significa liberação definitiva.


## REGISTRO — 27/10/2026 — AUTODESCOBERTA DE CACHE MAPBIOMAS
Mudança de código: commit dbe0a8d4b61df0f7996f0c4838a5ba1c89f13083 adiciona autodescoberta de arquivo `brazil_coverage-col11_2025.tif` (e nome alternativo) nas pastas de cache `~/.enform_verde/mapbiomas`, `~/.enform_verde/cache/mapbiomas`, `~/.enform_verde/uso_solo`, `~/.enform_verde/dados/mapbiomas`. Abre e valida metadados do arquivo candidato via rasterio antes de selecioná-lo, preservando rota remota oficial, opção manual `ENFORM_MAPBIOMAS_LOCAL_TIF` e regra de não converter IBGE fitofisionomia potencial em presença atual. Commit b08d55e047c4ee4a257c90c334866b384534b8b3 acrescenta teste sintético de autodescoberta e cobertura nativa.
**AINDA NÃO É SOLUÇÃO INTEGRAL:** ausência de arquivo local válido e falha do `/vsicurl/` ainda impedem confirmação da cobertura atual e estimativa de carbono; a aquisição automática oficial permanece pendente. Nenhum dado experimental foi inventado; status dos testes do novo SHA ainda não confirmado. Manter liberação científica bloqueada até AOI real Tapajós e demais biomas/compartimentos com fontes e incertezas.


## REGISTRO — 27/10/2026 — RESTABELECIMENTO PRIORITÁRIO DAS ROTAS DE CARBONO
Instrução expressa do usuário: RESTABELECER E PRESERVAR rotas de mensuração de carbono previamente testadas e aprovadas, sem regressão; a obtenção de cobertura atual deve ser etapa auxiliar e não alterar prioridades de sensores, modelos, inventários, biomassa/AGB, raízes, necromassa, serrapilheira, solos, carbono tC/tCO₂e, dados IBGE, fitofisionomia ou interface. SAR (prioridade BIOMASS P e fontes compatíveis) e as rotas ESA CCI, inventários, classes e fallback estatístico seguem com seus gates científicos independentes. Nunca declarar carbono em antropização sem fonte comprovada, nem usar IBGE potencial como comprovação de ocupação atual.
Foi adicionada alternativa de obtenção do raster MapBiomas por HTTPS nativo para o erro específico /vsicurl/: commit `f00e0eca9644cec7facc6a2c583744b26a21952d`, com cache local, arquivo temporário, validação de metadados e descarte de transferência parcial. A ordem permanece: GeoTIFF explícito válido ou cache MapBiomas existente -> rota oficial GDAL previamente usada -> fallback HTTPS apenas quando abertura remota falha por protocolo. O novo fallback NÃO altera cálculo de carbono por compartimentos; foi acrescentado teste `test_previously_working_mapbiomas_route_remains_first_priority` (commit `20548d13027548d7773ecf7701e445654bf5af08`) para provar que a rota aprovada é usada sem download quando funciona. Teste novo ainda sujeito ao resultado do CI; download completo real e AOI Tapajós continuam exigindo prova. Não declarar versão definitiva antes de demonstração fim-a-fim.


## EXIGÊNCIA NACIONAL VINCULANTE — 27/10/2026 — CARBONO COM INCERTEZA PARA QUALQUER REGIÃO DO BRASIL
**Escopo:** toda AOI do território brasileiro, não apenas Tapajós nem somente áreas cobertas por exemplos de cinco biomas. Operar por cobertura/fitofisionomia e compartimento reconhecidos; adicionar suporte explícito a Pampa e demais formações/zonas quando relevantes. Os cinco biomas prioritários continuam gates mínimos de regressão, nunca limite territorial do sistema. Não inferir cobertura atual de um mapa de vegetação potencial. Excluir áreas não nativas da conta de carbono nativo com fonte verificável.
**Hierarquia de mensuração:** (1) dados SAR quantitativos adequados (BIOMASS P, ALOS PALSAR L e demais produtos/sensores conforme domínio) ou AGB espacialmente explícita validada, com processamento e proveniência de aquisição; (2) inventários primários e pares parcela-pixel para calibração/validação regional; (3) modelos reconhecidos por fitofisionomia/domínio ecológico e área com entrada suficiente; (4) fallback de inventário microrregional/fitofisionômico e, em último caso, IFN/SFB estadual/bioma, somente com transferência ecológica explícita e erros adicionais dimensionados. Preservar rotas anteriormente testadas; jamais transformar média publicada em 'mensuração SAR'.
**Carbono por compartimento:** biomassa viva aérea, raízes, necromassa em pé e caída, serrapilheira e solo nas profundidades suportadas; fonte e natureza da estimação diferenciadas em cada compartimento. Necromassa e serrapilheira requerem medições gravimétricas/inventários ou conversões publicadas, não alometria inventada. Solo não deve ser implicitamente zero por falta de dados.
**Estatística:** área e incerteza de classe/área, N amostral, erro de transferência, erro de mensuração/modelo, sensibilidade aos sensores, covariância quando estimável; intervalos 95% ou intervalos preditivos devidamente identificados, não misturar um com outro. Produzir densidade (tC/ha, tCO2e/ha), estoque por AOI (tC e tCO2e), incerteza correspondente em tC/ha, tCO2e/ha, %, e agregação por classe com propagação apropriada (Monte Carlo/bootstrapping por estrato ou fórmula com covariâncias). Não somar IC de diferentes fontes como se fossem DP independentes. Se erro de área/transferência não puder ser delimitado defensavelmente, apresentar faixa condicional com ressalva e N/D para IC95% total, NUNCA falsa precisão.
**Regra de disponibilidade:** obter sempre a MELHOR estimativa cientificamente defensável onde houver pelo menos uma fonte adequada ao domínio e exposição da incerteza. Se cobertura nativa não puder ser confirmada, produzir estimativa condicional claramente rotulada por cenário apenas se premissas auditáveis forem fornecidas (sem tratá-la como estoque confirmado), explicar especificamente dados ausentes e caminhos de recuperação; não afirmar zero ha nativos por falha do raster. Se não existir base científica para qualquer estimativa, manter N/D explícito em vez de inventar valores. Uma estimativa 'para qualquer região' significa infraestrutura e política de fallback nacionais, **não** promessa de valor verificado para qualquer pixel sem observações.
**Testes de aceitação obrigatórios:** AOIs reais independentes em Amazônia, Cerrado, Caatinga, Mata Atlântica, Pantanal, Pampa e transições ecológicas; gradiente de alta/baixa biomassa; presença de pastagem/monoculturas/silvicultura; sem internet mas cache oficial válido; internet sem /vsicurl/; normalização por classe, por bioma e por AOI, incerteza nativa e conversão tC↔tCO2e; não regressão agrícola/climática; evidência por arquivo, run, commit e dados. Liberar EXE definitivamente apenas quando o fluxo nacional estiver validado dentro dos limites declarados.
**STATUS:** requisito registrado; NÃO se pode inferir que todos os biomas e fitofisionomias já tenham validação nacional só porque tests CI passam. Em verificação, builds Windows #700 e #701 ainda em progresso; testes Dashboard #300/#301 SUCCESS.


## REGISTRO DE STATUS — 27/10/2026 — TESTE RECUPERAÇÃO HTTPS MAPBIOMAS
Windows builds #700 (run 40575563697), #701 (40575618449) e #702 (40575953470) ainda em progresso, #700 em testes de estratificação nativa, #701 em quadrantes IBGE, #702 restaurando mapa IBGE. Dashboard #302/#303 sucesso para SHA 46079ae1bc9de9192923208ddd81c4db5265830d. Commit 1af5b11266ff36ebb2cc158c51566d0230ee8387 acrescenta teste funcional simulando falha de abertura GDAL /vsicurl/ e resposta HTTPS com TIFF válido, garantindo recuperação de cobertura, cache e separação da rota existente. **Teste ainda precisa ser executado e aprovado no Windows; arquivo sintético não confirma MapBiomas remoto oficial nem carbono na AOI real.** Bloqueio de versão definitiva: adquirir produto oficial, confirmar mapa de cobertura atual nos cinco+ biomas e testar por compartimento e incerteza em AOIs independentes. Não alterar estimadores cientificamente aprovados.


## ATUALIZAÇÃO DE STATUS — 27/10/2026 — CI WINDOWS 703/704
Consulta oficial de Actions: build 703, run 40576223148, commit 1af5b11266ff36ebb2cc158c51566d0230ee8387, em progresso na etapa Install dependencies; build 704, run 40576266614, commit b88778e035fbc5e48ab40ee830460e50c06e34f8, em progresso na etapa Install dependencies. Suites Dashboard #306 e #307 concluídas SUCCESS para SHA b88778e035fbc5e48ab40ee830460e50c06e34f8. Nenhum destes builds ainda foi constatado como concluído nesta consulta. Recuperação real de MapBiomas via HTTPS/cache, estoque com incerteza por compartimento e aceitação nacional continuam não demonstrados. Não atribuir status de release definitivo.


## STATUS — 27/10/2026 — BUILDS 703–705
Dashboard #308 e #309 PASS em 76f2cc1944b64b7aac8af6c7a43a09207c3c75d2. Windows #703 run 40576223148 e #704 run 40576266614 em progresso preparando quadrantes IBGE. Windows #705 run 40576503553 em progresso inspecionando esquemas IFN de necromassa. Nenhuma falha nova visível nas etapas consultadas. **Não há confirmação de ZIP concluído no SHA atual nem evidência de recuperação automática real de MapBiomas/AGB e outros compartimentos com incerteza nacional.** A correção científica permanece aberta. O próximo gate útil é teste end-to-end com dados reais e relatório de stdout, não apenas status de CI. Não declarar homologação definitiva.


## STATUS — 27/10/2026 — INTEGRIDADE DE DOWNLOAD OFICIAL MAPBIOMAS
Bloqueio de cobertura nativa continua aberto para a AOI real Tapajós e validação nacional. Correção adicional f8d4a517e0ad9f7af1e549ccf8bf69a1356948a2 valida igualdade entre bytes efetivamente recebidos via HTTPS e Content-Length fornecido pelo servidor, descartando arquivo parcial e impedindo falsos sucessos de leitura raster. Teste fb021e67f7da5cd827ac2f7ff6837500e4945c11 reproduz truncamento, verifica exceção e remoção de arquivo temporário. Mantidas rotas previamente aprovadas e estimadores de carbono; não confundir essa proteção com solução final de download no Windows. Versão definitiva requer ensaio MapBiomas real no sistema de destino, tC/tCO2e e incertezas por compartimento, validação independente em regiões brasileiras, build Windows e auditoria. Teste CI novo pendente de confirmação.


## CORREÇÃO DE BLOQUEIO WINDOWS — 27/10/2026 — TESTE GEOTIFF VÁLIDO PEQUENO
Falhas dos Windows builds #706 (40576812079) e #707 (40576961496) identificadas nos logs: teste `test_https_fallback_recovers_native_cover_after_vsicurl_failure` retornava `ValueError: Arquivo MapBiomas incompleto` porque a implementação exigia tamanho >1.024 bytes mesmo para um GeoTIFF sintético pequeno, válido e legível. **Correção aplicada no código no commit 8f5a3769ad06d3dac44ebc6c8da22a64d4aee3c7:** rejeitar arquivo vazio, conferir Content-Length quando fornecido e abrir/validar metadados via Rasterio; remover exigência arbitrária de tamanho mínimo tanto no download quanto no cache local. Nenhum modelo matemático ou mensuração de carbono foi alterado. O teste sintético e nova compilação Windows devem ser verificados no CI após esse SHA. Persistem gate de leitura MapBiomas oficial real em Windows e processamento de carbono com erro por compartimento e cobertura nacional. Não declarar versão definitiva apenas por regressão sintética aprovada.


## STATUS VERIFICADO — 27/10/2026 — WINDOWS 710–711
Workflows #710 (run 40577714524) e #711 (run 40577751079) ainda em progresso, sem erro registrado nas etapas inspecionadas. #710 executa construção de quadrantes IBGE a partir de cache; #711 atingiu classificação oficial de fitofisionomia IBGE na AOI Tapajós real. Suites dashboard #318–321 SUCCESS. Isto valida apenas progresso da etapa IBGE, NÃO leitura MapBiomas atual nem estoque de carbono. Pendência decisiva: executar MapBiomas oficial real no ambiente Windows, comparar mapa de cobertura atual × IBGE × AOI, verificar números e incertezas por compartimento, repetir gates nacionais e gerar ZIP compilado para mesmo SHA. Nenhuma alteração nos estimadores nesta consulta.


## CORREÇÃO — 27/10/2026 — RECUPERAÇÃO HTTPS SEM DEPENDER DE MENSAGEM DO GDAL
A abertura da cobertura MapBiomas em Windows podia falhar com timeout, HTTP 403/TLS ou outra mensagem não coberta pelo antigo filtro textual, impedindo recuperação apesar da rota HTTPS alternativa. Commit `246da71100838035c7a1489fd9bb59f7bcbceaa9` faz a alternativa HTTPS atuar após qualquer falha de leitura GDAL de URL oficial (depois das tentativas), preservando a prioridade de raster local explícito, cache existente e abertura GDAL que funcione. Commit `e35a8244e1a020b40272dd0061f1ab7183088aa7` cria teste que simula timeout com fallback e verifica a cobertura nativa. NÃO houve alteração dos modelos de carbono; não há ainda evidência de execução com raster MapBiomas real no Windows nem de estoque com incerteza por compartimento e validação nacional. CI deve aprovar antes de nova compilação ser recomendada, e compilação não equivale a validação científica.


## REGISTRO — 27/10/2026 — 504 DO STAC CERRADO E REPARO
A compilação Windows nº 712 (run 40578527602) falhou no gate `Outside-Amazon national fallback gate — Cerrado` porque o endpoint `https://planetarycomputer.microsoft.com/api/stac/v1/search` devolveu **HTTP 504 Gateway Timeout**, conforme log real do job 122451378241. Trata-se de uma falha de comunicação com serviço externo, não de validação negativa dos estimadores. A correção commit `537ca24ba54d1ed1be16dd4b74c28dcf182d3e38` adicionou até 3 tentativas à consulta STAC para erros transitórios HTTP 429/500/502/503/504, timeout e erro de conexão, mantendo exatamente os filtros de cena, a AOI e a matemática SAR. Erros definitivos permanecem explícitos. Testar em novo build Windows. Builds #713–715 ainda em progresso na consulta desta etapa, dashboards #328/329 SUCCESS. PENDÊNCIA INALTERADA: leitura real do MapBiomas na máquina Windows e estoques por compartimento com incertezas, além de homologação nacional. Nenhuma nova versão foi homologada por esta correção.


## STATUS — 27/10/2026 — REVISÃO WINDOWS #714 A #717
Logs reais dos builds #714 (run 40578769314) e #715 (40578820401): falha no gate Cerrado causada por HTTP 504 do endpoint Microsoft Planetary Computer STAC ao executar `planetary_sentinel1_cog`; os SHAs antigos ainda usavam a consulta sem repetição automática. O retry limitado de 3 tentativas para HTTP transitório foi introduzido posteriormente em `sar_pipeline.py`, commit 537ca24ba54d1ed1be16dd4b74c28dcf182d3e38. Builds Windows #716 (40579451803) e #717 (40579489075) desse código estão em progresso; #717 alcançou construção de quadrantes IBGE. Dashboard suites #330–333 SUCCESS. SEM PROVA de MapBiomas oficial legível em Windows ou de carbono completo e incertezas em AOIs reais; não liberar como homologado até estes gates.


## AUDITORIA AUTOMÁTICA — 27/10/2026, 17h40 (UTC−3) — BUILD #711 APROVADO COM ARTEFATO; NÃO É VERSÃO DEFINITIVA
- **Mudança material desde o registro anterior:** Windows **#711**, run **40577751079**, SHA de código **08e413cb66f75dde9b36ef3bb32904656c434452**, terminou **SUCCESS** em 27/10/2026 20:33:49 UTC. Os steps de compilação do executável, verificação de runtime Python empacotado, self-test do EXE copiado para pasta limpa e upload de artefato passaram. Também passaram, nesse run, gates de visualização Sentinel-2 Tapajós, SAR público e fallback regional Tapajós, IBGE fitofisionomia Tapajós, SICAR, Cerrado SAR/fallback e contratos Pantanal. São evidências técnicas específicas, **não** validação de estoques SAR de alta biomassa nem de todos os compartimentos em todos os biomas.
- Artefato CI gerado: **Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO**, artifact ID **12768702147**, tamanho informado **522.569.661 bytes**, digest do ZIP do GitHub Actions **sha256:7d31752645224d0a4f960d8f056c357a6fc0a5574cd3eee38af4b6b9812b2120**, não expirado na consulta. Referência do run: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40577751079 . **Não homologar esse artefato como versão definitiva:** seu SHA é anterior às correções posteriores de HTTPS/timeout e ao HEAD atual.
- Log do self-test compilado no #711 reportou `{"status":"SAR_PROCESSADO","area_ha":1291.3187519527487,"pixel_count":302348,"data_origin":"SAR_DERIVED_CCI","scene_count":5,"fallback_agb_mg_ha":null}`. Isso comprova processamento de cenas e AOI no self-test, **não** AGB SAR quantitativa validada nem carbono completo com incertezas. O LEIA-ME do build adverte expressamente que H100/AGB SAR de alta biomassa não estão validadas e que não há classificador nacional treinado embarcado.
- Windows **#710**, run **40577714524**, SHA **8f5a3769ad06d3dac44ebc6c8da22a64d4aee3c7**, terminou **FAILURE** no gate de prévia Sentinel-2 real Tapajós: endpoint STAC Microsoft Planetary Computer devolveu **HTTP 504** em `desktop_app.py:695` (log do job 122448483947). Essa falha é distinta do gate SAR Cerrado tratado posteriormente em `sar_pipeline.py`; não afirmar que o retry SAR também corrige o código Sentinel-2.
- Estado do HEAD da PR #50 nesta consulta: **6b2236006ab18e12d87abeaf2c40bf2eefb9849d**, PR aberta. Dashboards **#334** (40579894694) e **#335** (40579901587) **SUCCESS** nesse SHA. Windows **#716** (40579451803) e **#717** (40579489075) **IN_PROGRESS**, ambos alcançaram GUI contract; Windows **#718** (40579901874) **IN_PROGRESS**, na etapa de restauração de mapas IBGE. A aprovação do #711 não pode ser transferida ao HEAD sem build e testes do mesmo commit.
- **Gates científicos e funcionais ainda NÃO comprovados:** leitura de MapBiomas **oficial real** em Windows no fluxo completo e área nativa atual auditada; recuperação comprovada nos cinco biomas; AGB/raízes/necromassa/serrapilheira/solos com fonte, domínio e incerteza por classe e AOI; validação espacial independente SAR/parcela; resultados em tC e tCO₂e; auditoria de proveniência e de datas; ZIP do **mesmo SHA final**. Não liberar versão definitiva antes de satisfazer todos esses gates.


## STATUS — 27/10/2026 — RETRY DE PRÉVIA SENTINEL-2
Windows #717 falhou no gate `Live Sentinel-2 polygon preview — actual Tapajos KMZ`: endpoint STAC Planetary Computer retornou HTTP 504, conforme log do job 122454716100. `desktop_app.sentinel2_preview` fazia consulta única sem repetição; corrigido no commit `19cb1f12215d1576ba670eb9c6d9be5bf0f05487`: até 3 tentativas para HTTP 429/500/502/503/504, timeout e erro de conexão, sem alteração da consulta, classificação e mensuração do carbono. Build Windows #719 ainda em execução na última consulta; testes Dashboard #336/337 PASS para SHA 3d5568357d248eb965cb84fe98c614e06fd9d7c2. Esta correção não prova MapBiomas real em Windows nem estoque completo com incerteza nacional. Reexecutar gates e não declarar homologação definitiva sem evidências.


## STATUS — 27/10/2026 — BUILDS 720–721
Consultas aos workflows: Windows build #720 (run 40580404591, SHA 19cb1f12215d1576ba670eb9c6d9be5bf0f05487) e #721 (run 40580442382, SHA 4d8edd3a3ef9c95ac332da6b205791ecf849cae2) em progresso, ambos na instalação de dependências ao momento da consulta e sem nova falha identificada. Dashboard #338–341 SUCCESS. A correção de timeout STAC Sentinel-2 está incorporada, mas NÃO foi ainda verificada em build concluído. Nenhuma validação real nova de MapBiomas/cobertura nativa/estoques por compartimento com incerteza. Priorizar gate reprodutível MapBiomas com AOI real e relatório em tC/tCO2e, em vez de apenas acompanhamento de novos builds de documentação. Não declarar versão definitiva.


## TESTE DE INTEGRAÇÃO — 27/10/2026 — COBERTURA NATIVA + SEIS COMPARTIMENTOS
Commit `98da2c39fb3a6180a3e36e72f1539ba8d5860915` acrescenta `test_full_native_carbon_pipeline_all_pools_and_anthropic_exclusion` em tests/test_native_carbon.py. Monta raster sintético com 50% floresta nativa (código MapBiomas 3) e 50% pastagem (15), cruza com IBGE FOD e AOI 0,2 ha, testa chamada de estimador somente nos 0,1 ha nativos, seis compartimentos, estoque total 15 tC / 55 tCO2e e exclusão integral do uso antrópico. Verifica explicitamente ausência de IC95% artificial quando estimador sintético não fornece erro. **Não é validação científica de inventários, rastreio SAR ou mapa MapBiomas real:** apenas teste automatizado de integração. Pendente resultado do CI do novo commit, teste real Windows, fontes e incerteza observada por compartimento nas regiões brasileiras. Não declarar versão definitiva com base nesse teste isolado.


## AUDITORIA DE CI — 27/10/2026, 18h14 (UTC−3) — FALHA MATERIAL #723–725 E CORREÇÃO DO TESTE
- **Mudança material desde o registro anterior:** Windows **#723**, run **40581088571**, SHA **98da2c39fb3a6180a3e36e72f1539ba8d5860915**, **FAILURE**; **#724**, run **40581134583**, SHA **61a4399f78fd634fad409599b61aa3ba1cae7cdf**, **FAILURE**; **#725**, run **40581646726**, SHA **803ace735834c05a85832333e2ef70b6eb12c749**, **FAILURE** (encerrado em 27/10/2026 20:54:20 UTC). Nos três casos, o step bloqueador foi `Native-only stratification and confidence regression tests`. No #725, job **122462297653**, o log de 145 testes reportou **1 falha**: `test_full_native_carbon_pipeline_all_pools_and_anthropic_exclusion` esperava 0,1 ha de floresta e obteve **0,9999999977 ha**.
- **Diagnóstico geométrico:** o raster sintético EPSG:6933 tem 20×10 pixels de 10×10 m (área AOI **2,0 ha**), divididos igualmente entre código 3 (floresta) e 15 (pastagem). Portanto a expectativa correta é **1,0 ha nativo + 1,0 ha excluído**, não 0,1+0,1 ha. Seis densidades sintéticas somam 150 tC/ha; estoque correto **150 tC e 550 tCO₂e** em 1 ha. O erro estava nas **asserções do teste**, não há evidência nesses logs de erro de cálculo de área do programa. **Correção aplicada** em `tests/test_native_carbon.py`, commit **575653836d85cbdffb08e0e244b42e083eefbc8a**. O teste corrigido **ainda não foi confirmado em CI** nesta consulta.
- Dashboards **#348**, run **40581636414**, e **#349**, run **40581646630**, **SUCCESS** para SHA **803ace735834c05a85832333e2ef70b6eb12c749**; dashboard **#350**, run **40585094303**, **QUEUED** para SHA da correção **575653836d85cbdffb08e0e244b42e083eefbc8a**. Passar nos dashboards não elimina a falha do build Windows.
- No #725 passaram os steps de restauração/verificação IBGE offline, diagnóstico Tapajós H100 2010, catálogo nacional de fontes SAR e self-test de fonte. Após a falha do step 18, os testes Pantanal, GUI, prévia Sentinel-2 e empacotamento do EXE foram **SKIPPED**. Artefatos desse run: `pam-microregion-yield-2015-2024` (ID 12769732906) e `tapajos-2010-height-diagnostic-725` (ID 12769542795); **nenhum ZIP do executável Windows** nesse run.
- **PENDÊNCIAS:** executar suite completa Windows após SHA 57565383 e verificar artefato ZIP **do mesmo commit final**; comprovar leitura de MapBiomas oficial real em Windows, cobertura atual e exclusão antrópica, execução independente nos cinco biomas, AGB e compartimentos raízes/necromassa/serrapilheira/solos por fitofisionomia com fontes e erros/intervalos defensáveis, auditoria e métricas de validação SAR parcela–pixel. Teste de raster sintético, mesmo aprovado, **não** equivale a homologação científica. Não declarar versão definitiva.


## CORREÇÃO — 27/10/2026 — CI BUILD #727: ISOLAMENTO DE CACHE NOS TESTES
Build Windows #727 (run 40585147454) falhou em `tests/test_native_carbon.py::test_https_fallback_recovers_after_remote_timeout_message`, porque o mock do download HTTPS não foi acionado. A investigação do teste mostrou dependência do estado de `Path.home()`: a presença de um raster local no cache pode fazer `run_land_use` pular corretamente a rota HTTPS, invalidando a premissa do teste. Commit `69d663385781478c36973e94b633753ccc530b83` isola `Path.home()` num diretório temporário dentro desse teste, reproduzindo corretamente a ausência de cache e a falha remota. **Trata-se de correção do teste, não de comprovação de processamento real nem de liberação Windows.** Os builds #725–727 falharam; aguardar gates completos do novo SHA e verificar o MapBiomas oficial, os seis compartimentos e incertezas em AOIs reais antes de homologar.


## CORREÇÃO — 27/10/2026 — LIVE SENTINEL-2 NÃO É GATE DE CARBONO
O build Windows #729 falhou em `Live Sentinel-2 polygon preview — actual Tapajos KMZ` por `requests.exceptions.ReadTimeout` no Planetary Computer (8 segundos), não por erro de estoque de carbono. No commit `4e760c644c733ea1cc016dc55f8dc4e848aa70a5`, o gate registra `LIVE_SENTINEL2_UNAVAILABLE_EXTERNAL` SOMENTE para Timeout/ConnectionError ou HTTP 429/500/502/503/504; mantém verificações de imagem e geometria obrigatórias quando a resposta chega e preserva sempre a verificação de zoom do mapa IBGE offline. Outros erros continuam causando falha. O skip por indisponibilidade externa NÃO significa aprovação do teste de prévia online ou homologação científica. Falta ainda evidência de MapBiomas oficial, seis compartimentos e incertezas reais, bem como o pacote Windows completo no SHA corrigido.


## BLOQUEIO CONFIRMADO — 27/10/2026 — ALOS/PALSAR STAC 401
Build Windows #731 (run 40591711777) falhou no gate `Live public SAR pixel processing and regional fallback — actual Tapajos KMZ`. Log do job 122497350157: HTTP 401 Unauthorized em `planetary_alos_palsar` para endpoint STAC Microsoft Planetary Computer. HTTP 401 NÃO é intermitência nem evidência de AGB nula, e tentativas adicionais não corrigem credencial/permissão. Commit `fe29a48a66d3401af6e529e1429602da80780a59` torna a falha de catálogo explícita e não fatal ao aplicativo (`pixel_state=NAO_PROCESSADO`, `access_status=AUTH_REQUIRED`, stats vazios), permitindo examinar provedores alternativos; o gate obrigatório de processamento de pixels SAR reais deve CONTINUAR reprovando quando nenhum pixel foi obtido. Exige habilitar credenciais/acesso ou fonte pública L-band alternativa com calibração e teste AOI real; não transformar `401` em aprovação. Os builds 730/731 não representam versão homologada. Pendente MapBiomas oficial no Windows e incertezas verdadeiras por compartimento.


## AUDITORIA DE LIBERAÇÃO — 27/10/2026, 19h23 (UTC−3) — BUILDS #730/#732 APROVADOS; HEAD #734 EM ANDAMENTO
- **Mudança material desde o registro anterior:** Windows **#730**, run **40591675935**, commit **4e760c644c733ea1cc016dc55f8dc4e848aa70a5**, terminou **SUCCESS** em 27/10/2026 22:12:48 UTC. O job aprovou a suite nativa de regressão, testes Pantanal, processamento público SAR/fallback Tapajós, fitofisionomia IBGE Tapajós, Cerrado SAR/fallback, compilação do EXE, self-test do executável em pasta limpa e upload. Artefato **Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO**, ID **12775490991**, **522.569.676 bytes**, digest **sha256:e00ba584c7f5f996bece673c503cb3d7815dd18476e78e700e81a7218da737db**, não expirado na consulta. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40591675935/artifacts/12775490991 . É compilação CI, não versão científica definitiva.
- **Novo sucesso Windows #732**, run **40592845537**, commit **fe29a48a66d3401af6e529e1429602da80780a59**, **SUCCESS** em 27/10/2026 22:20:56 UTC, inclusive teste nativo, Pantanal, SAR Tapajós/Cerrado, IBGE, compilação e self-test do EXE em pasta limpa. Novo ZIP **Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO**, artifact ID **12774593512**, **522.569.593 bytes**, digest GitHub Actions **sha256:a05000767b4999cddf9e54b3574fdb1182b288fd93979ab6492cf39b0d454c64**, não expirado. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40592845537/artifacts/12774593512 . Esse ZIP contém a correção de tratamento HTTP 401 de `sar_pipeline.py` (SHA fe29a48a), **mas não contém** as alterações posteriores de documentação e do teste de regressão `8fc2d8ec`.
- **HEAD da PR #50:** aberta em estado **draft**, SHA **8fc2d8ec4b92f1a60d1d8cc1013196b452cfa95d** antes desta atualização documental. Dashboards **#366** (run **40593109515**) e **#367** (run **40593120151**) **SUCCESS** nesse SHA. Windows **#734** (run **40593120058**) ainda **IN_PROGRESS** na última consulta: compilação e self-test em pasta limpa já concluídos com sucesso; etapa `actions/upload-artifact@v4` ainda em andamento, sem ZIP Windows listado no momento da verificação. Windows **#733** (run **40592880630**, SHA **44bfc979db67d9925351feb04b2b987fe056d1de**) também **IN_PROGRESS** no upload; não antecipar conclusão. O teste adicionado em `8fc2d8ec` confirma em suite automatizada que HTTP 401 ALOS/PALSAR não produz pixels inventados; **não** fornece dados L-band nem comprova carbono quantitativo.
- **Limite da evidência:** o step `Native-only stratification and confidence regression tests` passou, mas o teste integrado documentado usa **raster sintético**. Os passos SAR/IBGE com AOI real não comprovam, por si, aquisição e interseção do **GeoTIFF oficial MapBiomas** no Windows com auditoria das classes atuais. A consulta ao workflow não encontrou um gate explícito de download e verificação do MapBiomas real; **não inferir** homologação de cobertura nativa atual a partir do sucesso do workflow.
- **Gates ainda pendentes de evidência científica e funcional:** (1) MapBiomas oficial real, versão/ano, hash e interseção com AOI, validação e exclusão de uso antrópico; (2) processamento de recuperação auditável e demonstração em **Amazônia, Cerrado, Caatinga, Mata Atlântica e Pantanal**; (3) AGB, raízes, necromassa em pé/caída, serrapilheira e solos por fitofisionomia com estimativas efetivas, proveniência e incertezas em **tC/ha, tCO2e/ha e %**, sem intervalos inventados; (4) validação independente espacial parcela–pixel de modelos SAR e tratamento de saturação; (5) painel executivo e trilha completa de auditoria, datas de aquisição, tC e tCO2e; (6) ZIP do **mesmo SHA integralmente homologado**, hash e documentação. **Não publicar como versão definitiva** apenas por sucesso CI. A aprovação de #730/#732 não transfere validade ao HEAD ou a um commit documental posterior.


## AUDITORIA DE LIBERAÇÃO — 27/10/2026, 20h21 (UTC−3) — #733, #734 E #735 FINALIZADOS; ZIP DO HEAD DISPONÍVEL
- **Mudança material em relação ao último registro (19h23 UTC−3):** os três builds Windows antes pendentes agora estão **SUCCESS**: **#733**, run **40592880630**, SHA **44bfc979db67d9925351feb04b2b987fe056d1de**; **#734**, run **40593120058**, SHA **8fc2d8ec4b92f1a60d1d8cc1013196b452cfa95d**; **#735**, run **40594480376**, SHA **ee4dd9214e9dc90d3f7daaed118083be34dad803**, encerrado **27/10/2026 22:34:32 UTC**. Dashboards **#368** (run **40594471532**) e **#369** (run **40594480367**) também **SUCCESS** no SHA **ee4dd921**. PR #50 permanece aberta; HEAD consultado **ee4dd9214e9dc90d3f7daaed118083be34dad803** (antes da presente atualização documental).
- **Evidências Windows #735:** job **122506785519** concluiu com sucesso testes nativos (146 testes), Pantanal (4 testes), testes adicionais (235 testes), GUI, IBGE offline, SAR público Tapajós, ALOS/PALSAR quantitativo Cerrado, empacotamento, self-test do EXE em pasta limpa e upload. O log contém **LIVE_SENTINEL2_PREVIEW_OK** com cena S2B_MSIL2A_20261025T140709_R110_T21MYS_20261025T174956, **OFFLINE_ZOOM_EXTENT_OK (900,420)** e **LIVE_CERRADO_SAR_AGB_OK** com AGB **16,7534523925 Mg/ha**, incerteza reportada **11,2437158143 Mg/ha**, polarizações HH **−9,56694 dB** e HV **−15,31637 dB**. São evidências pontuais, não validação nacional independente. As sondagens BIOMASS em dois locais do Tapajós retornaram **FH=0, AGB=0** em ambos; não interpretar como estoque zero. Os testes test_mapbiomas_zonal passaram, porém isso **não comprova aquisição do GeoTIFF oficial MapBiomas e interseção real**. O teste CCI v7 verificou respostas HTTP range de 206 bytes; não comprova processamento completo de raster e validação da AGB.
- **Artefatos ZIP Windows CI** Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO, registrados no GitHub Actions com digests informados pela plataforma: #733 artifact **12775781442**, **522.569.272 bytes**, **sha256:553bd794ce924dd10f8323dda3c7a0faaaae20e58adadcdf9840214c99ca8ae5**, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40592880630/artifacts/12775781442 ; #734 artifact **12774788622**, **522.567.270 bytes**, **sha256:2ad2e1532950dd1ef1e7d58ee2f2d6ea7c8adcf6fe1c2b04ab506f087c5cd52f**, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40593120058/artifacts/12774788622 ; #735 artifact **12775404837**, **522.569.727 bytes**, **sha256:ef93159ba574fd204d8410e3ab95899510d147d0a20922b62ed5e3f9939111ef**, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40594480376/artifacts/12775404837 . O #735 foi produzido no SHA HEAD **antes** desta atualização documental; não afirmar que é ZIP do novo commit documental. Hashes são digests publicados pelo GitHub Actions, não recalculados localmente.
- **Pendências científicas inalteradas:** falta gate com **MapBiomas oficial real** (ano/coleção, arquivo/hash, AOI, classes, exclusão antrópica); recuperação comprovada nos **cinco biomas**; estimativas verificadas de AGB, raízes, necromassa em pé e caída, serrapilheira e solos **por fitofisionomia**, com fontes e incertezas em **tC/ha, tCO2e/ha e %**; validação espacial independente parcela–pixel e tratamento de saturação SAR; painel executivo e trilha auditável com datas, unidades e fontes; ZIP e documentação do **mesmo commit cientificamente homologado**. O resultado Cerrado AGB e as suites CI não suprem essas lacunas. **STATUS: BUILD WINDOWS APROVADO, VERSÃO CIENTÍFICA DEFINITIVA NÃO HOMOLOGADA.** Não promover CI a liberação definitiva.


## BLOQUEIO DE REGRESSÃO — 28/10/2026 (UTC−3) — MARARY E TAPAJÓS, EVIDÊNCIA DE EXECUÇÃO LOCAL DO USUÁRIO
- **Origem:** laudos da versão 3.25.1-CLIMA-DINAMICO e KML IMÓVEL MARARY fornecidos pelo usuário. Este registro documenta falhas observadas; NÃO declara código corrigido, testes executados ou novo EXE gerado.
- **Marary:** AOI 138.713,65 ha; IBGE classifica Floresta Ombrófila Densa 80.383,90 ha (57,95%), Aberta 58.137,28 ha (41,91%) e água 192,47 ha (0,14%). MapBiomas oficial C11/2025 foi localizado no cache local, mas falhou com `ValueError: Janela de classes excede 4 milhões de células; subdivida a AOI`. Resultado 0,00 ha nativo e 138.713,64 ha de cobertura não confirmada NÃO é evidência de ausência de floresta. Diferença de área IBGE 138.643,32 ha versus AOI 138.713,65 ha (70,33 ha) exige auditoria de geometria, CRS, recorte e denominador; diferenças de 0,01 ha podem decorrer de arredondamento, mas devem ser conciliadas. **Correção obrigatória:** localizar o gate de 4 milhões na rota efetivamente usada pela GUI, substituir por leitura em janelas/blocos e agregação por código de classe, sem recortar ou perder células; conferir bordas, nodata, áreas e proveniência; rodar teste com KML Marary e raster C11 real, além de testes sintéticos de blocos.
- **Tapajós:** AOI 1.290,69 ha, MapBiomas+IBGE 100% Floresta Ombrófila Densa; soma parcial reportada 262.202,00 tC e 961.407,35 tCO2e. AGB 123,64 tC/ha, incerteza de produto 59,58 tC/ha (não IC95%); BGB 22,42 tC/ha sem erro quantificado; necromassa aérea 8,70 tC/ha com IC publicado sem transferência; raízes mortas não estimadas; serrapilheira 2,33 tC/ha sem fração de C específica/erro de transferência; solo 0–30 cm 46,06 tC/ha com DP espacial, não erro de predição. Classe Formação Florestal 0,00 ha indevidamente apresentada com cálculos de solo e estado SAR não processado, confundindo o leitor. **Correção obrigatória:** excluir classes de área zero de todos os painéis e totais; exibir proveniência SAR por classe e não mensagem global enganosa; distinguir produto CCI anual de cena instantânea; mostrar soma explicitamente parcial e compartimentos ausentes; não inventar IC95% total nem combinar desvios de naturezas diferentes; manter tC e tCO2e e detalhamento em seção auditável.
- **Inspeção de código nesta revisão:** `mapbiomas_zonal.py` no branch lê a janela inteira com `src.read(1, window=window)`; `tests/test_mapbiomas_zonal.py` só cobre grades pequenas. O erro literal de 4 milhões provavelmente se encontra em outra rota de classificação/interseção; localizar a chamada real antes de alterar. Nenhuma correção de implementação foi realizada neste registro.
- **Gates de aceite:** (1) Marary C11 real processado integralmente sem limite de tamanho, classes e hectares conferidos, relatório com cobertura atual; (2) Tapajós sem classe de área zero, sem mensagens contraditórias, soma parcial transparente; (3) cinco biomas e seis compartimentos auditáveis com incertezas apropriadas; (4) regressões de GUI/Windows e EXE testado em pasta limpa no mesmo SHA; (5) evidência e hashes do ZIP do commit homologado. **STATUS: REGRESSÕES CONFIRMADAS EM RELATÓRIOS DO USUÁRIO; CORREÇÃO E NOVA VERSÃO PENDENTES.**


## IMPLEMENTAÇÃO PARCIAL — 28/10/2026 — LEITURA MAPBIOMAS EM BLOCOS
- Commit de código `befb5f980f24853bea319cf5a082a39b7f510ea8` na branch da PR #50: `land_use_sar.py::raster_class_polygons` deixa de rejeitar AOIs com mais de 4.000.000 células e passa a ler blocos de 512 × 512, com máscara de interseção, nodata, poligonização e agregação posterior pelo fluxo existente. Preserva prioridade de classificação e legendas; o processamento ainda requer validação de bordas, equivalência de áreas, memória e tempo em raster oficial real.
- **Não executados nesta etapa:** teste integrado KML Marary + MapBiomas C11 real no Windows, regressões completas, CI Windows e geração de novo ZIP. Não declarar resolução comprovada, nem versão definitiva.
- **Permanecem bloqueadores:** inconsistências do relatório Tapajós (classes zero, painel parcial, proveniência SAR e incertezas), validação de cobertura real, cinco biomas, compartimentos, auditoria, CI e pacote do mesmo SHA. Necessário adicionar teste de regressão Marary, verificar eventuais outras rotas com limites de 4M e evitar explosão de geometrias por mosaico de blocos.


## AUDITORIA AUTOMÁTICA — 27/10/2026, 21h22 (UTC−3) — BUILDS #736–#739 CONCLUÍDOS; #740 EM ANDAMENTO
- **Mudança material desde o último registro:** Windows #736 (run 40601616932, SHA `477a470d76410c22cff4725601773066c9e9bf45`), #737 (run 40606916928, SHA `6d92c95690aaaa2cae62b1be766c7afa74aee986`), #738 (run 40607099072, SHA `befb5f980f24853bea319cf5a082a39b7f510ea8`) e #739 (run 40607115184, SHA `f2be4bac9a1d7724f5e766ffcd7a67f12b581ff4`) encerraram **SUCCESS**. O #738 contém a primeira correção de leitura em blocos do MapBiomas em `land_use_sar.py`; o #739 contém a mesma correção e atualização documental. O commit de código posterior `aaa9aeb709444edcdbf449c69c951d83bd478c6a` adiciona exclusão de estratos de área numericamente nula em `native_carbon.py`; seu Windows #740, run **40608262509**, estava **IN_PROGRESS**, ainda em instalação de dependências, sem artefato na consulta. Dashboards #374/#375 (SHA befb5f98), #376/#377 (SHA f2be4bac) e #378/#379 (SHA aaa9aeb7) **SUCCESS**. PR #50 permanece **draft/open**. A presente edição documental não faz parte dos ZIPs anteriores.
- **Evidência técnica Windows #738/#739:** ambos aprovaram as etapas de testes nativos, Pantanal, GUI, prévia Sentinel-2, SAR Tapajós/Cerrado, IBGE, compilação, self-test do EXE em pasta limpa e upload. Logs dos jobs **122549197269** (#738) e **122549251408** (#739) incluem **235 testes adicionais aprovados**, `LIVE_CERRADO_SAR_AGB_OK 16.75345239253869 11.243715814333031`, e testes MapBiomas com raster de teste/cache. **Não há gate comprovado de execução integrada com KML Marary + raster oficial MapBiomas C11/2025 completo nem validação dos hectares e da classificação na AOI de 138.713,65 ha**. Sucesso dos testes pequenos não prova correção efetiva em área grande.
- **Bloqueio científico explícito nos logs, apesar do SUCCESS global:** a sondagem BIOMASS FH para parcelas de inventário no Tapajós registrou `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI; do not mark high-biomass SAR-height model as passed.` e `Process completed with exit code 1` dentro do step não bloqueante. Portanto **não declarar altura SAR/AGB de alta biomassa validada**; status global CI não equivale à aprovação científica desse requisito.
- **ZIPs CI verificados (digests GitHub Actions, não hashes recalculados localmente):** #736 artefato **12778634198**, 522.569.060 bytes, `sha256:195fa12fc215575de0579e2091d398d93c52d9144fa62db240bb907b8fe8f1d3`, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40601616932/artifacts/12778634198 ; #737 artefato **12781236954**, 522.569.409 bytes, `sha256:9bd2ccbf1b22f86ee07f396dbea5a2a17988a574d30e3d7aa4caf7e57bfc1ea4`, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40606916928/artifacts/12781236954 ; #738 artefato **12781612829**, 522.570.952 bytes, `sha256:a4287e5b3642151157b3f9153a72e0c429270edc548789d07e8182e67d240d15`, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40607099072/artifacts/12781612829 ; #739 artefato **12781492397**, 522.570.328 bytes, `sha256:abe5591026c50be4ed079c43d111dab007b09d5973bf66513ad338982ced264d`, https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40607115184/artifacts/12781492397 . Todos estavam não expirados na consulta; são **artefatos de teste, não versão definitiva**.
- **Pendências de liberação:** (1) MapBiomas oficial real C11/2025 no KML Marary, blocos/bordas, áreas, hash, cobertura atual e exclusão antrópica; (2) Tapajós sem estratos de área zero e sem mensagens contraditórias, com soma parcial explicitamente identificada e incertezas por compartimento; (3) recuperação e auditoria dos cinco biomas e seis compartimentos com incertezas defensáveis; (4) validação independente parcela–pixel e altura SAR/AGB em alta biomassa; (5) executar #740 até o fim, analisar seus logs, verificar ZIP do mesmo SHA e regressões Windows reais. **STATUS: CORREÇÕES PARCIAIS COM BUILD CI APROVADO EM #738/#739; HOMOLOGAÇÃO CIENTÍFICA NÃO COMPROVADA; #740 PENDENTE.** Não disponibilizar ZIP como versão definitiva.


## ATUALIZAÇÃO DE REGRESSÃO — 28/10/2026
- `aaa9aeb709444edcdbf449c69c951d83bd478c6a`: `native_carbon.py` ignora estratos de área numérica nula antes de chamar estimadores e montar totais.
- `d1b28e8926166dafb84f8651dad8df4f7981290b`: teste sintético novo em `tests/test_land_use_sar.py` usa raster 2.100 × 2.100 (4.410.000 pixels) e verifica cobertura integral por classe sem rejeição de tamanho. Este teste foi **adicionado, não executado nem aprovado** nesta sessão.
- Bloqueios: teste integrado com KML Marary e raster oficial C11, desempenho de geometria/área, revisão de laudo Tapajós, incertezas por compartimento, cinco biomas e Windows CI/EXE do mesmo SHA. Não declarar homologação sem evidência.


## AUDITORIA AUTOMÁTICA — 27/10/2026, 21h46 (UTC−3) — WINDOWS #747 E #748 CONCLUÍDOS; ZIP DE TESTE DISPONÍVEL
- **Mudança material desde a auditoria anterior:** Windows #747 (run `40608952113`, SHA `f5abe8987b3e5e566ccb9204dc54df4c4f62e671`) e Windows **#748** (run `40609655092`, SHA **`826a436cb7d51589513557ca5d1a70412ddd902b`**) encerraram **COMPLETED/SUCCESS**. Dashboard #395 (run `40609655087`, mesmo SHA #748) também **SUCCESS**. PR #50 continua **open/draft**. Conferidos jobs, steps, artefatos e logs do job Windows #748 `122557815660`.
- **Evidências técnicas do #748:** 149 testes do conjunto principal e 4 testes Pantanal aprovados; suíte complementar **238 testes, OK** (há sobreposição entre suítes, não somar como testes únicos); testes de regressão `LargeMapBiomasRegression` (raster sintético 2.100×2.100), `EmptyMapBiomasCoverageRegression` e `MapBiomasOutsideRasterRegression` aparecem como **ok**. Compilação Windows, verificação do runtime empacotado, **self-test do EXE em pasta limpa** e upload do pacote encerraram **SUCCESS**. O log inclui `LIVE_CERRADO_SAR_AGB_OK 16.75345239253869 11.243715814333031`, processamento quantitativo de pixels SAR reais de baixa biomassa; isso não constitui validação independente nacional.
- **Falha interna não bloqueante encontrada no log #748, apesar de SUCCESS global:** o script `archive_guard_test.py` falhou com **`AssertionError`** ao comparar `_safe_target(root,'scene/subset.tif').parent == root/'scene'`. Investigar o teste e a função de proteção de extração de arquivos, corrigir e tornar a verificação bloqueante. **Não declarar todos os contratos de segurança aprovados** enquanto esta falha persistir.
- **Bloqueio científico persistente, comprovado no log #748:** `BIOMASS_COVERAGE_PROBE PF_HIGH_8_11 FH 0 AGB 0` e `SF_LOW_21_23 FH 0 AGB 0`; o passo de consulta não bloqueante registrou **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** e `Process completed with exit code 1`. Há cenas L1C catalogadas, mas os assets testados responderam HTTP **401**. Logo, **não está validada altura SAR BIOMASS nem AGB de alta biomassa nas AOIs Tapajós**; sucesso global do workflow não elimina essa pendência.
- **Artefato Windows #748 verificado no GitHub Actions, mas NÃO homologado cientificamente:** `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID **12782721892**, **522.570.444 bytes**, digest fornecido pelo GitHub Actions **`sha256:aeeb577c25ad29ce8b6328459db3649316c59bb8f61bce2aadfd8ed5dad2158f`** (não recalculado localmente), não expirado na consulta. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40609655092/artifacts/12782721892 . O ZIP pertence ao SHA `826a436c...`; não pertence ao commit documental criado por esta auditoria. Também há o ZIP #747, ID **12781994775**, **522.571.007 bytes**, digest GitHub **`sha256:8d5a40dc2114a786deb58ed3d681dbed709113cd3cb8e5963336c88ec24b24fe`** (SHA `f5abe898...`).
- **Gates que permanecem SEM comprovação:** (1) execução integrada do **KML Marary + raster oficial MapBiomas C11/2025** com conferência de classes, hectares, cobertura nativa atual, bordas e desempenho; (2) relatório real Tapajós sem classes nulas/contradições e com soma parcial e incertezas de todos os compartimentos corretamente qualificadas; (3) cinco biomas e compartimentos com estimativas, validação externa e propagação de incerteza; (4) validação independente parcela–pixel e altura SAR/AGB de alta biomassa; (5) correção e gate bloqueante para `archive_guard_test.py`; (6) artefato Windows do **mesmo SHA que vier a ser cientificamente homologado**, com hashes e documentação. **STATUS: CI WINDOWS E TESTES SINTÉTICOS APROVADOS, ZIP DE TESTE PUBLICADO, MAS HÁ FALHA NÃO BLOQUEANTE E BLOQUEIOS CIENTÍFICOS; VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## ATUALIZAÇÃO OPERACIONAL — 2026-10-28 UTC — MARARY GEOS, CERRADO HTTP 429, SOLO TAPAJÓS — CONTINUIDADE URGENTE

**Este registro é aditivo: preservar integralmente todo o histórico anterior.**

### Evidências verificadas no GitHub
- PR #50, branch `feature/agricultural-identification-native-carbon`.
- Falha real do usuário em Marary, versão desktop anterior: `desktop_app.py:1859 → land_use_sar.py:639 run_land_use → land_use_sar.py:100 partition_land_use → shapely.geometry.base.difference`, exceção `GEOSException: AssertionFailedException: Should never reach here: Unable to determine overlay result geometry dimension`. O log **não prova** que o tamanho da AOI, isoladamente, causou a falha.
- Commit `1718fb45698a135105e353a13ff97bdbcff03372`: `partition_land_use` dissolve fragmentos por classe/fonte/taxonomia antes de operações geométricas; evita laço de subtração por fragmento.
- Commit `39baef7cb404c8cddbe9e50b13da09a362e26cc7`: regressão sintética com 2.500 fragmentos.
- Commit `cbdd29dca06b03edcbb24366d20e09be6bed2376`: função `_robust_polygon_overlay`, `make_valid`, tentativa de overlay em precisão padrão, fallback `set_precision(..., 0.001)` e `grid_size=0.001`; falha fechada quando overlay não recuperável. **Não confundir com validação real Marary.**
- Commit `8c3367bc37215b28916189bd5c58a95bc6feeaba`: regressões que simulam GEOSException recuperável e irrecuperável.
- Workflow Windows **40614450522** do SHA `8c3367b`: **FAILURE**, antes de compilar EXE, na etapa `Live Cerrado ALOS-PALSAR quantitative AGB — actual pixels`. O log comprova pixel real **HH** (8.100 amostras, média -9,5669 dB), mas a polarização **HV** falhou com HTTP **429 Too Many Requests** na assinatura de URLs Planetary Computer; não foi possível validar AGB L-band Cerrado. Não atribuir esta falha à correção GEOS. URL https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40614450522
- Commit `ca85445246e2baeb4ba67ad5f3e6ddfde6f97da6`: marca a etapa SAR live como `continue-on-error: true` para permitir compilação/testes Windows, **sem transformar ausência de HV em aprovação científica**.
- Workflow Windows **40616043299** do SHA `ca85445`: **IN_PROGRESS na última consulta**, etapa `Install dependencies`; dashboard **40616043296**: **SUCCESS**. **Nenhum ZIP do novo SHA disponível na última consulta**. URL https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40616043299

### Evidência real do Tapajós e correção pendente
- AOI Tapajós **1.290,69 ha**, estoque parcial **262.202,00 tC / 961.407,35 tCO2e**, **sem IC95% total defensável**.
- Solo em densidades publicadas pelo programa: **0–30 cm 46,06 tC/ha; 0–60 cm 65,70; 0–100 cm 83,43; 0–200 cm 115,81**. O código `native_carbon.py` fixa `Solo 0–30 cm` em `COMPARTMENTS` e soma apenas esse perfil; profundidades adicionais são informativas. **IMPLEMENTAR** seleção de profundidade 0–30/0–60/0–100/0–200 cm, persistência e recálculo de tC/tCO2e por classe e AOI; nunca somar perfis cumulativos entre si; preservar incerteza específica de cada profundidade e não rotular SD espacial como IC95%.
- Biomassa subterrânea, serrapilheira e necromassa subterrânea continuam com incerteza ausente/compartimento não estimado; **não inventar valores nem IC**. Preservar status parcial, fontes, limites e transferibilidade.

### Próximos passos mandatórios — executar, não apenas prometer
1. **Verificar Windows 40616043299**: resultado final, falhas e `continue-on-error`, testes GEOS novos, EXE self-test, ZIP do SHA exato, digest e tamanho. Se falhar, diagnosticar log e corrigir; não rotular versão definitiva.
2. **Marary real**: executar KML original com raster oficial MapBiomas C11/2025 e classes IBGE; validar CRS, `make_valid`, `dissolve`, overlay com precisão, fechamento de áreas, limites, ausência de sobreposição, desempenho/memória e resultados reproduzíveis. Se a recuperação geométrica falhar, mostrar erro preciso e manter área não classificada sem carbono.
3. **Fortalecer testes geométricos**: simular interseções multipartes, `GeometryCollection`, polígonos inválidos, geometrias quase coincidentes, limites e sobreposições; testar área preservada após fallback e recusar diferenças incompatíveis com resolução cartográfica.
4. **Solo**: implementar seletor de profundidade e testes para os quatro perfis e seus totais, evitando dupla contagem; diferenciar SD espacial, incerteza preditiva e IC95%.
5. **SAR**: tratar HTTP 429 com backoff limitado e cache/alternativas documentadas, nunca inventar polarização HV; manter falha de validação live registrada. Validar BIOMASS FH/AGB alta biomassa e cinco biomas com dados reais.
6. **Liberação**: somente após evidência do Windows compilado e autoexecutado em pasta limpa, Marary real validado, compartimentos e incertezas auditados, modelos cientificamente validados, apresentar ZIP, SHA, digest, documentação. Caso contrário disponibilizar apenas **build experimental** explicitamente rotulada, quando houver artefato.

**STATUS NA ATUALIZAÇÃO:** correções GEOS e testes **COMMITADOS**, mas testes do novo commit, Marary real e solo selecionável **NÃO COMPROVADOS**; SAR Cerrado HV **NÃO VALIDADO** (429); Windows novo **EM EXECUÇÃO**. **VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA DE LIBERAÇÃO — 2026-10-28 01:46 UTC (2026-10-27 22:46 UTC−3) — MUDANÇA MATERIAL: ZIP WINDOWS PUBLICADO

**Registro aditivo; manter o histórico integral acima.** PR #50, branch `feature/agricultural-identification-native-carbon`.

### Compilação e artefatos confirmados
- **SHA compilado:** `6e3640b2d166207305235dc09a27b54b220e4ad0`.
- **Windows run 40616128588:** `completed/success`; job `build-windows` `completed/success`. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40616128588
- **Dashboard run 40616128605:** `completed/success`.
- **ZIP Windows experimental publicado**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **artifact ID 12786130423**, **522.572.322 bytes**, **digest reportado pelo GitHub Actions** `sha256:2b550973e8fff114135ac0bcc288115b2f3c0985ed6ea90a61238e2d7e97beb1` (**não recalculado localmente**), `expired=false`. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40616128588/artifacts/12786130423
- O workflow passou `Source self-test`, `Native-only stratification and confidence regression tests`, `Pantanal fallback tests`, `GUI contract test`, `python -m unittest discover -s tests -v` (**241 testes OK**), `Build executable`, `Compiled EXE self-test from clean copied folder`, `upload-artifact`. Conjunto anterior de **152 testes OK**. Testes GEOS incluídos no commit.
- **SAR Cerrado real HV recuperado nesta execução**: `LIVE_CERRADO_SAR_AGB_OK 16.75345239253869 11.243715814333031 [('HH', -9.566937505382494), ('HV', -15.316372308713804)]`. Isto comprova execução do teste quantitativo específico em AOI Cerrado; **não equivale a validação independente nacional**.

### Falhas não bloqueantes ainda verificadas no log Windows
- `archive_guard_test.py`: **AssertionError** em `assert _safe_target(root,'scene/subset.tif').parent==root/'scene'`. A etapa não bloqueou o resultado geral; **corrigir e tornar bloqueante** antes de homologação.
- Verificação de altura SAR/ESA BIOMASS Tapajós: `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`; assets L1C consultados responderam **HTTP 401**. **Altura SAR/AGB de alta biomassa NÃO APROVADAS**; o `success` geral não elimina a falha científica.
- **Marary real não foi executado/validado nesta auditoria** com KML e MapBiomas oficial C11/2025; correção GEOS aprovada em testes de código/Windows, **não comprovada em AOI real**.
- **Solo Tapajós:** seletor de profundidade 0–30/0–60/0–100/0–200 cm e totais sem dupla contagem ainda **não comprovados**; compartimentos e IC95% total permanecem incompletos.
- **Cinco biomas, fitofisionomias, validação espacial independente e auditoria científica completa** ainda não comprovados. A classificação como versão definitiva permanece **PROIBIDA**.

### Continuidade prioritária
1. Corrigir `archive_guard_test.py` e confirmar rejeição de path traversal com gate CI bloqueante.
2. Validar o KML Marary com MapBiomas C11/2025 real, fechamento de área, classes e desempenho; investigar qualquer GEOSException remanescente.
3. Implementar seleção de profundidade do solo, recálculo e propagação de incertezas sem dupla contagem; validar relatórios reais Tapajós.
4. Solucionar aquisição/autorização e validação SAR BIOMASS alta biomassa; auditar incertezas e compartimentos nos cinco biomas.
5. Somente após cumprir todos os gates, gerar novo EXE/ZIP do **mesmo SHA aprovado** e divulgar digest. O ZIP ID 12786130423 é **BUILD EXPERIMENTAL**, apesar do CI verde.

**STATUS:** MUDANÇA MATERIAL — **ZIP WINDOWS PUBLICADO, COMPILAÇÃO E TESTES AUTOMATIZADOS PASSARAM**, mas **FALHAS NÃO BLOQUEANTES E GATES CIENTÍFICOS PENDENTES; NÃO HOMOLOGADO.**


---

## AUDITORIA DE LIBERAÇÃO — 2026-10-27 23:48 UTC−3 (2026-10-28 02:48 UTC) — CORREÇÕES MATERIAIS MARARY E SOLO 0–100 CM

**Registro aditivo; preservar integralmente o histórico anterior.** PR #50 permanece **open/draft**, branch `feature/agricultural-identification-native-carbon`. Último SHA de código consultado: `feab7f5c159fbd1d35c8b3b92c9e9c0906f608b0`. Este registro não é homologação.

### Auditoria do relatório real fornecido pelo usuário (Marary)
- Relatório de 138.713,65 ha apontou 138.452,38 ha como nativos, mas incluiu indevidamente **156,83 ha de "Corpo d'água continental"**, atribuindo **14.326,46 tC de biomassa aérea e 8.672,54 tC de solo 0–30 cm** à água. Isso viola a regra de carbono apenas em formações nativas; o total parcial original de 28.163.648,99 tC não deve ser homologado.
- A estimativa de **Floresta Ombrófila Densa** (80.383,65 ha, 133,91 tC/ha de AGB no relatório antigo) aparecia após Floresta Ombrófila Aberta; o usuário exige **Densa como primeira formação estimada e exibida**.
- O relatório continua **parcial**: necromassa aérea/subterrânea e serapilheira não estimadas; incerteza da AGB CCI não é IC95%, e desvio-padrão espacial do solo não é erro preditivo. A correção da água implica recalcular área nativa e todos os totais; não publicar estimativa definitiva baseada só em subtração manual.

### Alterações reais publicadas no GitHub
1. `ed6e579a7aac91d5645b8d9bf88b8df328a457cd` — `native_carbon.py`: rejeita classes aquáticas mesmo quando erroneamente rotuladas IBGE+MAPBIOMAS; ordena Floresta Ombrófila Densa antes de Aberta.
2. `b6b10beb579b2ff5ebe6b5cfa3429d39d6d66f1b` — `tests/test_native_carbon.py`: adiciona regressões sintéticas de exclusão de água, ordem e fechamento de área/carbono.
3. `085dfdb912c645dc4a0f879f02f197dafa28ed5a` — `native_carbon.py`: altera o compartimento somado de `Solo 0–30 cm` para **`Solo 0–100 cm`**, usando o perfil cumulativo de PronaSolos e impedindo soma duplicada de profundidades sobrepostas. Perfis 0–30/0–60/0–200 cm permanecem informativos no relatório; seletor de profundidade configurável **ainda não implementado**.
4. `feab7f5c159fbd1d35c8b3b92c9e9c0906f608b0` — `tests/test_native_carbon.py`: atualiza fixture de solo e asserção de 0–30 para 0–100 cm, eliminando uma incompatibilidade de teste introduzida pela alteração do compartimento. **Não afirmar aprovação dos novos testes sem workflow concluído.**

### CI Windows e dashboard verificados nesta consulta
- SHA `b6b10beb...`: Windows run **40622796576**, `in_progress` (job `build-windows`, etapa `Build on-demand IBGE quadrants from previous cache when needed`); dashboard run **40622796237** `completed/success`.
- SHA `085dfdb...`: Windows run **40622888950**, `in_progress` (mesma etapa de quadrantes IBGE); dashboard run **40622888967** `completed/success`. Artefato PAM intermediário ID 12787204623, **não é ZIP Windows**.
- SHA `feab7f5c...`: na primeira consulta nenhum run aparecia; **nova consulta confirmou Windows run 40623119574 `in_progress` e dashboard run 40623119610 `in_progress`**, sem conclusão ou ZIP confirmado. Portanto, **nenhum ZIP Windows validado do SHA mais recente**. Não reutilizar ZIP anterior como se incorporasse as correções de água, ordem e solo 0–100 cm.
- Tentativa de consultar logs do job Windows em execução retornou 404 BlobNotFound; sem logs de conclusão, **não inferir falha ou sucesso**.
- Último ZIP confirmado no histórico anterior (run 40616128588, SHA 6e3640b2) é **experimental e anterior a todas estas correções**.

### Pendências e critérios de conclusão
1. Aguardar Windows CI do **SHA mais recente** (ou refazer build no SHA final), verificar testes, erros não bloqueantes, EXE self-test, ZIP, digest e documentação; tornar `archive_guard_test.py` bloqueante após correção.
2. **Reprocessar Marary real** com KML original + raster oficial MapBiomas C11/2025 + IBGE; confirmar exclusão de água, Densa primeiro, fechamento das áreas, sem sobreposições e resultados auditáveis. Confirmar carbono do solo **0–100 cm** no painel, no relatório e na exportação, sem duplicar perfis.
3. Reprocessar Tapajós e outras AOIs reais; validar os perfis cumulativos do solo e erro/transferibilidade por profundidade. A seleção configurável de profundidade permanece desejável, mas **0–100 cm é o mínimo exigido**.
4. Validar MapBiomas real, carbono em todos os cinco biomas, compartimentos, fontes e incertezas, altura/AGB SAR alta biomassa, métricas de validação espacial independente e segurança de arquivos. Não inventar necromassa, serapilheira ou IC95%.
5. Só declarar **VERSÃO DEFINITIVA** após evidências científicas e técnicas completas e artefato ZIP do mesmo SHA homologado.

**STATUS:** MUDANÇA MATERIAL — CORREÇÕES DE ÁGUA, ORDEM DE FLORESTA DENSA E SOLO 0–100 CM COMMITADAS; TESTE DE SOLO ATUALIZADO. WINDOWS DO NOVO SHA E REPROCESSAMENTO REAL AINDA **NÃO COMPROVADOS**. **VERSÃO DEFINITIVA NÃO LIBERADA.**


## Atualização de interface — fitofisionomias IBGE sem truncamento (28/10/2026)

- Evidência: captura de tela do usuário da aba **Mapas e limites** com classe cortada como "Floresta Ombr..." no campo **Fitofisionomia IBGE (legenda_1)**. Não é problema do dado cartográfico: o campo Tkinter tinha `ttk.Label(... wraplength=840)` com largura fixa incompatível com o espaço disponível.
- Correção commit **a25c8141d6e43579701fa1a1f31bf19185737832** em `desktop_app.py`: campo substituído por `tk.Text` somente leitura, quebra automática de palavras, altura de quatro linhas e scrollbar vertical; atualização vinculada a `self.ibge_phys_display.trace_add("write", ...)`. Não reduzir a informação, não truncar classes, códigos ou percentuais.
- Critério de aceite: abrir AOI com três ou mais classes (incluindo Floresta Ombrófila Densa, Floresta Ombrófila Aberta e Corpo d'água continental), reduzir largura da janela, rolar campo e comprovar leitura integral de todas as classes e números. Testar redimensionamento, Windows DPI 125%/150% e atualização de perímetro.
- Interface: o botão ainda exibe "Buscar COS 0–30 cm — Embrapa", enquanto a contabilização nativa foi alterada para solo 0–100 cm. Harmonizar o rótulo e confirmar se o provedor disponibiliza efetivamente 0–100 cm; não prometer profundidade que o serviço de consulta não entrega.
- **Não declarar EXE concluído sem workflow Windows aprovado no SHA que contenha este commit e seus testes.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 01h09 (UTC−3; 04h09 UTC) — FALHA WINDOWS DIAGNOSTICADA E TESTE CORRIGIDO

**Mudança material desde o registro anterior:** os workflows Windows que estavam em andamento foram concluídos com **FAILURE**, inclusive o mais recente do SHA `9f39888e80139759ad9ded8157a587f3fa9614cd`. O dashboard desse SHA passou, mas isso não valida o executável Windows.

### Execuções consultadas (evidência GitHub Actions)
- **Windows #760**, run **40623119574**, SHA `feab7f5c159fbd1d35c8b3b92c9e9c0906f608b0`: `completed/failure`; dashboard run 40623119610 `completed/success`.
- **Windows #763**, run **40623429034**, SHA `5a55c3040ab3852733afff365ae64369219db831`: `completed/failure`; dashboard 40623429024 `success`.
- **Windows #764**, run **40623968426**, SHA `a25c8141d6e43579701fa1a1f31bf19185737832`: `completed/failure`; dashboard 40623968434 `success`.
- **Windows #765**, run **40623984194**, SHA `66b43a2f9fcabf134b216747febbad70120e60b3`: `completed/failure`; dashboard 40623984298 `success`.
- **Windows #766**, run **40624125322**, SHA `9f39888e80139759ad9ded8157a587f3fa9614cd`: `completed/failure`; dashboard 40624125315 `success`. Job Windows **122604879119** consultado com log completo. Link: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40624125322 .

### Causa comprovada da falha Windows #766
- A etapa **Native-only stratification and confidence regression tests** executou **154 testes**, com **153 aprovados e 1 falha**; as etapas posteriores, inclusive `Build executable`, foram **skipped**. Portanto, **não existe ZIP Windows da revisão #766**.
- O teste `tests.test_native_carbon.WaterExclusionAndOrderingRegression.test_dense_forest_is_first_and_water_excluded` comparou o estoque calculado `199.99999977072028` tC com `200.0` tC usando `assertAlmostEqual` com precisão padrão de 7 casas. Diferença absoluta **2,2927972054×10⁻⁷ tC**, atribuível a arredondamento numérico de área/geométrico, não prova desvio material do cálculo.
- **Correção publicada neste ciclo:** commit `bec5a24fed7931edd93538def4ddfb7cf543021a` ajusta **somente a tolerância do teste** para `places=5`, mantendo as asserções de exclusão da água, ordem Densa/Aberta e fechamento das áreas. **Não altera cálculo científico.** Não alegar aprovação da nova revisão até observar novo workflow.
- A consulta do run #765 revelou a mesma falha numérica; #763 e #764 falharam na mesma etapa, sem exame detalhado de seus logs. A causa precisa desses dois runs anteriores não foi independentemente confirmada nesta auditoria.
- Artefatos de #766: apenas `pam-microregion-yield-2015-2024` (ID 12788522441) e `tapajos-2010-height-diagnostic-766` (ID 12788134954). **Nenhum é EXE/ZIP Windows**. Não divulgar como programa concluído.

### Alterações adicionais já presentes na branch
- `5a55c304`: correção de aspas em teste de água; `a25c8141`: campo IBGE de fitofisionomia com quebra de linha e rolagem vertical; `66b43a2f`: documentação da correção visual; `9f39888`: botão do raster de solo renomeado para **“Baixar raster COS 0–30 cm (auxiliar)”**. O carbono contabilizado permanece **0–100 cm**. Interface visual não foi verificada em Windows nesta auditoria.

### Próximas verificações obrigatórias
1. Conferir Windows CI e dashboard para **`bec5a24f...` e posterior commit documental**: 154 testes nativos, demais suítes, segurança de extração de arquivos (`archive_guard_test.py` com gate bloqueante), compilação, EXE self-test em pasta limpa e ZIP do mesmo SHA. Se falhar, analisar o novo log e corrigir.
2. Reprocessar **Marary real** com KML original + MapBiomas oficial C11/2025 + IBGE, fechar áreas e remover água; demonstrar ordem Floresta Ombrófila Densa primeiro; testar visualização integral dos nomes no Windows com DPI 125%/150%.
3. Validar solo **0–100 cm** em relatório, totais e exportação, sem duplicação de perfis; verificar origem e incertezas; manter profundidades informativas.
4. Auditar cinco biomas, necromassa, serrapilheira, biomassa subterrânea, altura/AGB SAR alta biomassa, validação independente e incertezas. O sucesso do CI **não substitui homologação científica**.
5. Liberar **versão definitiva** somente após todas as evidências técnicas e científicas, com ZIP Windows, SHA, digest e documentação; não oferecer ZIP antigo como se contivesse correções recentes.

**STATUS EM 28/10 01h09 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #760/#763/#764/#765/#766 FALHARAM; ERRO NUMÉRICO DE TOLERÂNCIA DIAGNOSTICADO E CORRIGIDO NO TESTE, AINDA SEM EXECUÇÃO CI DO NOVO SHA COMPROVADA; SEM ZIP NOVO; HOMOLOGAÇÃO CIENTÍFICA PENDENTE.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 02h28 (UTC−3; 05h28 UTC) — WINDOWS #767/#768 VERDES, ZIP EXPERIMENTAL, BLOQUEIOS PERSISTENTES

**Mudança MATERIAL desde o registro de 01h09:** a correção da tolerância numérica do teste (commit `bec5a24fed7931edd93538def4ddfb7cf543021a`) permitiu que as compilações Windows **#767** e **#768** concluíssem com `completed/success`; os dashboards correspondentes também passaram. A PR #50 segue aberta; SHA da branch auditado antes desta atualização documental: **`54d20f3c5bb7a9e6b5b0aef12913450c973ea8eb`**. Não confundir aprovação do CI com homologação científica.

### Execuções e artefatos confirmados
- Windows **#767**, run **40630817176**, SHA `bec5a24fed7931edd93538def4ddfb7cf543021a`: `completed/success`; dashboard run **40630817111** `completed/success`. Artefato Windows **12791826977**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.572.832 bytes**, digest GitHub Actions **`sha256:e55648530ecfaf15b375210c62b5f49c6b05d909c97a10df0df890fc486a12d5`** (não recalculado localmente).
- Windows **#768**, run **40630848168**, SHA `54d20f3c5bb7a9e6b5b0aef12913450c973ea8eb`: `completed/success`; dashboard run **40630848148** `completed/success`. Artefato Windows **12791478983**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.571.441 bytes**, digest GitHub Actions **`sha256:93c02309d1280f3b256068b7a56741f380378a5d667fcb979cd444561de73aa1`** (não recalculado localmente); `expired=false` na consulta. URL de inspeção: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40630848168/artifacts/12791478983
- **#768:** etapa de regressões nativas **154 testes OK**; suíte geral **243 testes OK**; etapas `Build executable`, `Compiled EXE self-test from clean copied folder` e `upload-artifact` passaram. Classificação IBGE real da AOI Tapajós confirmou `Floresta Ombrófila Densa`; Cerrado ALOS-PALSAR quantitativo real retornou AGB **16,75345 Mg/ha** e incerteza reportada **11,24372 Mg/ha** (não equivale a validação espacial nacional).

### Falhas e restrições demonstradas pelo log Windows #768 (job 122626592296)
- O script `archive_guard_test.py` **continua falhando com `AssertionError`** (linhas do log em torno de 1551–1555), apesar de o workflow permanecer verde. A segurança da extração de arquivos ainda não está homologada; corrigir o teste/implementação e **tornar a etapa bloqueante**. Não interpretar a passagem de outros contratos como prova de que este gate passou.
- A prova de cobertura **ESA BIOMASS FP_FH__L2B** nas AOIs inventariadas do Tapajós continua lançando **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** (log em torno de 1866–1869), sem derrubar o workflow. Portanto, **altura SAR e AGB SAR de alta biomassa não homologadas**. Não converter o sucesso do workflow em sucesso científico.
- Testes MapBiomas no log incluem regressões e contratos sintéticos, mas **não demonstram reprocessamento integral do KML real de Marary com raster oficial MapBiomas C11/2025**, fechamento de área e totais sem água. Também não há evidência nesta auditoria de relatório real comprovando solo **0–100 cm** em todos os estratos, erro por profundidade e exportação sem duplicação.
- **Cinco biomas**, necromassa/serapilheira, biomassa subterrânea, validação espacial independente, covariâncias e incerteza total não foram demonstrados de modo suficiente para homologação. O GUI contract passou, mas não comprova inspeção visual em Windows com DPI 125%/150% nem leitura de todas as classes sem truncamento.

### Ações prioritárias
1. Reparar e tornar **bloqueante** `archive_guard_test.py`, repetir Windows CI e inspecionar logs; manter prova de rejeição de path traversal.
2. Resolver disponibilidade/autorização da missão BIOMASS para altura e AGB SAR de alta biomassa; validar pares parcela–pixel e métricas independentes, sem inventar AGB quantitativa.
3. Reprocessar Marary **real** com KML original, IBGE e MapBiomas oficial C11/2025; verificar água excluída, Densa primeiro, área e estoques corretos.
4. Reprocessar Tapajós e cinco biomas, verificar solo **0–100 cm**, necromassa, serapilheira, compartimentos, fontes, incertezas e exportações; não confundir desvio-padrão espacial com IC95%.
5. Confirmar leitura integral das fitofisionomias em Windows redimensionado e DPI 125%/150%, e preparar artefato Windows **do SHA final homologado** com digest, instruções e link.

**STATUS 28/10/2026 02h28 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #767/#768 E DASHBOARD PASSARAM; ZIP WINDOWS EXISTE MAS É EXPERIMENTAL. SEGURANÇA DE ARQUIVO E SAR BIOMASS ALTA BIOMASSA AINDA FALHAM EM ETAPAS NÃO BLOQUEANTES; HOMOLOGAÇÃO CIENTÍFICA E VERSÃO DEFINITIVA NÃO LIBERADAS.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 03h12 (UTC−3; 06h12 UTC) — WINDOWS #769 VERDE, NOVO ZIP EXPERIMENTAL, BLOQUEIOS CONFIRMADOS

**Mudança MATERIAL desde o registro 02h28:** a revisão documental `3724560e27164cbc0009ce7e20893347edc9e90a` (head da PR #50 consultado nesta auditoria) recebeu nova compilação Windows **#769** e dashboard **#437**, ambos `completed/success`. Foi publicado **novo artefato Windows** do mesmo SHA; isto **não** demonstra a homologação científica nem elimina os erros não bloqueantes conhecidos.

### Evidências verificadas diretamente
- PR #50: `open`, `draft=true`, `merged=false`; branch `feature/agricultural-identification-native-carbon`, head `3724560e27164cbc0009ce7e20893347edc9e90a` antes deste commit documental.
- **Windows #769**: run **40638244181**, job **122650116659** (`build-windows`), `completed/success`. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40638244181 .
- **Dashboard #437**: run **40638244195**, `completed/success`; etapas `Syntax check` e `Unit and regression tests` aprovadas. URL: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40638244195 .
- Logs Windows #769 inspecionados: **154 testes nativos OK**; **243 testes da suíte geral OK**; compilação, verificação do runtime Python empacotado, autoteste do EXE copiado para pasta limpa, instruções e `upload-artifact` passaram.
- Artefato Windows **ID 12794204774**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.572.027 bytes**, `expired=false` (consulta 28/10), digest informado pela API GitHub Actions **`sha256:ff4f60ef9a811eea1958ccd45c99169f5c502a85f6a4abbf05fbd5af1224199c`**. Digest **não recalculado localmente**. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40638244181/artifacts/12794204774 . Acesso/download pode exigir login GitHub.
- Artefatos auxiliares: PAM microrregional **12795110037**; diagnóstico de altura Tapajós **12794368047**. Nenhum substitui o EXE.

### Falhas persistentes, agora reconfirmadas no log do job #769
1. **`archive_guard_test.py` continua falhando com `AssertionError`** na asserção `_safe_target(root,'scene/subset.tif').parent==root/'scene'`. A falha é impressa como traceback mas o job termina verde: o gate de segurança **não é bloqueante**. Investigar normalização/resolução de caminhos Windows e semântica de `_safe_target`, testar caminho legítimo e rejeição de `../escape.txt`; somente após corrigir tornar o teste obrigatório e bloquear o CI em falha. Não declarar segurança homologada.
2. **`biomass_fh_probe.py` continua lançando `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`**. Não há comprovação de altura SAR quantitativa/AGB SAR de alta biomassa do Tapajós; teste de cobertura não é bloqueante. Não extrapolar AGB sem dados/preditores e validação adequados.
3. **MapBiomas real de Marary, cinco biomas, carbono do solo 0–100 cm com incerteza por perfil, necromassa, serrapilheira, biomassa subterrânea, calibração parcela–pixel e validação espacial independente** permanecem sem evidência de homologação integral nesta execução. Os testes de MapBiomas vistos no log são regressões/contratos, não reprocessamento auditado de Marary com raster oficial.
4. **Interface IBGE sem truncamento** ainda precisa de inspeção visual em Windows com janelas estreitas e DPI 125%/150%; o `GUI contract test` passou, mas não substitui a inspeção visual.

### Próximos critérios obrigatórios
- Corrigir os dois erros persistentes e exigir gates bloqueantes apropriados; recompilar o **SHA posterior às correções**.
- Reprocessar AOIs reais com fontes auditáveis: Marary (KML + MapBiomas C11/2025 + IBGE), Tapajós, Pantanal e exemplos representativos de Amazônia, Cerrado, Caatinga e Mata Atlântica; demonstrar os cinco biomas, classificação e exclusão da água.
- Auditar AGB, raízes, necromassa, serrapilheira e solo **0–100 cm**, estoques tC/tCO2e, fontes, incertezas por compartimento/estrato, totais sem dupla contagem e exportações.
- Somente após todas as evidências, disponibilizar ZIP Windows do **mesmo SHA final homologado**, com digest conferido e documentação. **O ZIP #769 é experimental e não deve ser anunciado como versão definitiva.**

**STATUS 28/10/2026 03h12 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #769 E DASHBOARD #437 APROVADOS, NOVO ZIP EXPERIMENTAL PUBLICADO; TESTE DE SEGURANÇA E COBERTURA BIOMASS FH CONTINUAM FALHANDO EM ETAPAS NÃO BLOQUEANTES; VALIDAÇÃO CIENTÍFICA INTEGRAL PENDENTE. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 03h47 (UTC−3; 06h47 UTC) — WINDOWS #770 APROVADO, ZIP EXPERIMENTAL NOVO, DOIS BLOQUEIOS RECONFIRMADOS

**Mudança MATERIAL desde 03h12:** o head auditado da PR #50 era **`cfc6c0f9d280a8e9cf805de472cbdb05220e6c1f`** (commit documental anterior); foram concluídos com `completed/success` os workflows **Windows #770** (run **40642509897**, job **122663663284**) e **dashboard #439** (run **40642509976**), com novo artefato ZIP Windows do mesmo SHA. PR permanece `open`, `draft=true`, não mesclada. Os dois bloqueios não bloqueantes anteriores **continuam reproduzíveis no log Windows #770**; portanto não houve homologação científica.

### Evidências verificadas diretamente (GitHub Actions)
- Windows #770: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40642509897 ; dashboard #439: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40642509976 . Ambos concluídos com sucesso.
- Log completo do job Windows **122663663284** consultado: **154 testes nativos OK** (linha ~1134); **243 testes gerais OK** (linha ~2501); build, runtime, autoteste do EXE em pasta limpa e upload de artefato com status `success`. Dashboard passou nas etapas `Syntax check` e `Unit and regression tests`.
- Artefato **12796985783**, `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.572.606 bytes**, `expired=false`, publicado em **28/10/2026 06:24:27 UTC**; digest **informado pelo GitHub Actions**, não recalculado localmente: **`sha256:a66233506a83001c6b3c39ab712b4f58f9990d8e11f3f547f3a36e234885eb7a`**. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40642509897/artifacts/12796985783 . Acesso ao download pode exigir autenticação no GitHub. **Artefato experimental, não divulgar como versão definitiva**.
- Artefatos auxiliares: diagnóstico Tapajós 2010 ID **12796745033** e PAM 2015–2024 ID **12795854419**. Não são EXE/ZIP de distribuição.

### Bloqueios reconfirmados no log do Windows #770
1. **Segurança de arquivos:** `archive_guard_test.py` executou e imprimiu **`Traceback`/`AssertionError`** (linhas ~1554–1558), mas a etapa `Professional scientific contracts` foi marcada como sucesso. A falha ainda não bloqueia CI; corrigir a asserção/caminho legítimo, verificar rejeição de `../escape.txt`, e tornar o teste bloqueante antes de homologar.
2. **SAR de alta biomassa Tapajós:** `biomass_fh_probe.py` imprimiu **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** (linhas ~1869–1872); a etapa do catálogo foi marcada como sucesso. Não há prova de cobertura SAR FH/altura e AGB quantitativa de alta biomassa nessa AOI. Não inventar preditores nem aprovar o modelo por fallback.
3. **Validação científica incompleta:** ainda sem demonstração auditada de Marary real (KML + MapBiomas oficial C11/2025 + IBGE, fechamento e exclusão da água), solo **0–100 cm** e incerteza por profundidade em resultados reais, todos os compartimentos e cinco biomas, calibração parcela–pixel, validação espacial independente e agregação correta das incertezas. Testes sintéticos e sucesso CI não suprem essas evidências.
4. **Interface:** testes de contrato não substituem inspeção visual em Windows com DPI 125%/150% e nomes IBGE completos após redimensionamento.

### Ações seguintes e regra de liberação
- Resolver e tornar bloqueante o teste de segurança; buscar dados SAR FH realmente elegíveis ou reportar indisponibilidade sem homologar alta biomassa; repetir Windows CI no SHA corrigido.
- Reprocessar e documentar AOIs reais de Marary, Tapajós, Pantanal, Amazônia, Cerrado, Caatinga e Mata Atlântica, com MapBiomas/IBGE, AGB, raízes, necromassa, serrapilheira e solo 0–100 cm, fontes, tC/tCO2e, incertezas e exportações; verificar não regressão.
- Só disponibilizar **versão definitiva** após aprovação integral das evidências e ZIP do **mesmo SHA final homologado**, com digest verificado e documentação. O ZIP #770 é **experimental**.

**STATUS 28/10/2026 03h47 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #770 E DASHBOARD #439 APROVADOS, NOVO ZIP EXPERIMENTAL PUBLICADO; SEGURANÇA DE ARQUIVOS E BIOMASS FH AINDA FALHAM SEM BLOQUEAR CI; HOMOLOGAÇÃO CIENTÍFICA INTEGRAL PENDENTE. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 04h42 (UTC−3; 07h42 UTC) — WINDOWS #771 E DASHBOARD #441 APROVADOS; NOVO ZIP EXPERIMENTAL; BLOQUEIOS PERSISTENTES

**Mudança MATERIAL desde o registro de 03h47:** o head da PR #50 consultado foi `13d5f35585af47668acbe775258a41699df99c0e`, com **Windows #771** (run **40646085523**, job **122675113084**) e **dashboard #441** (run **40646085573**, job **122675113165**) concluídos com `completed/success`. O GitHub Actions publicou novo ZIP Windows deste SHA, mas a aprovação do job **não significa aprovação dos testes científicos não bloqueantes**. PR continua `open`, `draft=true`, `merged=false`. Não foi identificado novo commit de código nesta consulta, somente nova execução e novo artefato.

### Evidências verificadas diretamente no GitHub Actions
- Windows #771: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40646085523 . Job `build-windows` concluído com sucesso; logs consultados. **154 testes nativos OK** (linha ~1133), **243 testes gerais OK** (linha ~2475), compilação PyInstaller, verificação do runtime empacotado, autoteste do EXE copiado para pasta limpa e upload de artefato concluídos com sucesso.
- Dashboard #441: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40646085573 . Etapas `Syntax check` e `Unit and regression tests` aprovadas; logs consultados.
- Novo ZIP **experimental**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, artefato **12798162588**, tamanho **522.570.503 bytes**, `expired=false`, publicado em **28/10/2026 06:59:45 UTC**, expiração informada **27/11/2026**. Digest **informado pelo GitHub**, **não recalculado localmente**: `sha256:8671cd084b383adf6ed9ee7b7b949b7d4b54d04bba1bb5ea297db95e2ed990fa`. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40646085523/artifacts/12798162588 . O download pode exigir login GitHub; **não oferecer como versão definitiva**.
- Artefatos auxiliares: PAM **12797841419**; diagnóstico de altura Tapajós **12797591601**. Nenhum deles é ZIP executável.

### Bloqueios persistentes, confirmados novamente nos logs Windows #771
1. **Segurança de arquivos ainda não aprovada:** `archive_guard_test.py` lança `AssertionError` na asserção `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1553–1557); a etapa `Professional scientific contracts` permanece marcada `success`. Corrigir o teste/semântica Windows, comprovar caminho legítimo e rejeição de traversal `../escape.txt`, e torná-lo **gate bloqueante**.
2. **SAR alta biomassa Tapajós ainda não homologado:** `biomass_fh_probe.py` retorna `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI` (linhas ~1842–1845). O log registra `FH 0 AGB 0` para as duas AOIs; há 21 itens L1C encontrados para `SF_LOW_21_23`, mas os acessos a ativos reais retornaram **HTTP 401** e outra consulta L1C sofreu `ReadTimeout`. O passo gerou `Process completed with exit code 1` (linha ~1859), **mas foi tolerado e não derrubou o job**. Não alegar validação de altura/AGB SAR em floresta de alta biomassa.
3. **MapBiomas real Marary e auditoria científica não demonstrados nesta execução:** os logs incluem testes MapBiomas e verificações de catálogo CCI v7, mas **não comprovam reprocessamento integral de KML Marary + raster oficial MapBiomas C11/2025 + IBGE**, fechamento espacial e exclusão da água em resultados reais; tampouco validação completa dos **cinco biomas**, compartimentos AGB/raízes/necromassa/serapilheira/solo **0–100 cm**, fontes e incertezas, calibração parcela–pixel, validação espacial independente e ausência de dupla contagem.
4. **GUI:** contrato passou, mas ainda não há prova visual de leitura integral das classes IBGE em Windows redimensionado com DPI 125%/150%.
5. **Interpretação científica:** métricas exibidas em `ROBUST_P_BAND_GROUPED_CALIBRATION_OK` no log, isoladamente, **não comprovam validação externa com parcelas reais em alta biomassa**; não equiparar a evidência de homologação.

### Próximas ações e condição de liberação
- Tornar o teste de segurança bloqueante, sanar o problema e recompilar SHA posterior; resolver acesso/compatibilidade de dados SAR adequados ou reportar ausência com transparência, sem inventar AGB.
- Executar e arquivar validações reais de Marary, Tapajós e AOIs representativas de **Amazônia, Cerrado, Caatinga, Mata Atlântica e Pantanal**, com estoques e incertezas por estrato/compartimento, solo 0–100 cm, relatórios e exportações.
- Validar visualmente GUI Windows. Só então publicar o ZIP Windows **do mesmo SHA final homologado**, com hash conferido, instruções e link de download.

**STATUS 28/10/2026 04h42 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #771 E DASHBOARD #441 APROVADOS; NOVO ZIP EXPERIMENTAL PUBLICADO. FALHA DE SEGURANÇA E AUSÊNCIA DE COBERTURA BIOMASS FH PERSISTEM EM TESTES NÃO BLOQUEANTES; HOMOLOGAÇÃO CIENTÍFICA PENDENTE. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 06h06 (UTC−3; 09h06 UTC) — WINDOWS #772 E DASHBOARD #443 APROVADOS; ZIP EXPERIMENTAL NOVO; BLOQUEIOS PERSISTEM

**Mudança MATERIAL desde 04h42:** a PR #50 permanece **aberta, draft e não mesclada**, no head **`d533d5780c698828af69ef7f2f9828fee7b90f76`** (commit documental anterior). Os workflows disparados por esse SHA concluíram com **`completed/success`**: Windows **#772** (run **40651958889**, job **122693893930**) e dashboard **#443** (run **40651958865**, job **122693893806**). Foi publicado **novo ZIP Windows experimental** do SHA consultado. Nenhuma correção adicional de código nem homologação científica foi demonstrada por esta execução.

### Evidências verificadas diretamente
- Windows: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40651958889 . Log do job consultado: **154 testes nativos OK** (linha ~1133), **243 testes gerais OK** (linha ~2500), compilação PyInstaller, runtime empacotado, autoteste do EXE em pasta limpa e upload do ZIP concluídos. As etapas globais exibem sucesso, **mas testes não bloqueantes falham**, como detalhado abaixo.
- Dashboard: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40651958865 . Log consultado: duas suítes com **6 e 9 testes OK**, além de sintaxe aprovada.
- Novo artefato ZIP **`Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`**, ID **12800168782**, **522.573.035 bytes**, publicado em **28/10/2026 07:54:07 UTC**, expira em **27/11/2026 07:53:41 UTC**, `expired=false`. **Digest informado pelo GitHub Actions, não recalculado localmente:** `sha256:aef0e8405885240c934f89f1c16bd406e4acf1b1129bf81a63442104fdd21760`. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40651958889/artifacts/12800168782 . Download pode exigir autenticação. **Não apresentar como versão definitiva.**
- Artefatos auxiliares: diagnóstico Tapajós 2010 ID **12800102194** e série PAM ID **12799199588**; nenhum é ZIP de distribuição.

### Bloqueios ainda reproduzidos nos logs Windows #772
1. **Segurança de arquivos:** `archive_guard_test.py` ainda lança **`AssertionError`** na verificação `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1554–1557). A etapa `Professional scientific contracts` foi registrada como sucesso apesar disso. Corrigir o comportamento de caminhos no Windows, verificar rejeição de `../escape.txt` e tornar o teste **bloqueante**.
2. **BIOMASS FH/AGB de alta biomassa no Tapajós:** `biomass_fh_probe.py` ainda lança **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** (linhas ~1869–1871); sondas registraram **FH 0 AGB 0** nas duas AOIs, e acessos a ativos L1C retornaram **HTTP 401** (linhas ~1826–1884). O comando encerrou com **exit code 1**, mas o job continuou e terminou aprovado. Não considerar altura/AGB SAR alta biomassa validadas.
3. **Validação científica não demonstrada:** não há no log reprocessamento auditado de Marary real com KML + raster oficial MapBiomas C11/2025 + IBGE; nem homologação integral dos cinco biomas, dos estoques e incertezas por fitofisionomia/compartimento (AGB, raízes, necromassa, serrapilheira e solo **0–100 cm**), calibração parcela–pixel e validação espacial independente. Os testes MapBiomas observados são regressões/contratos, não prova de execução real completa.
4. **GUI:** ainda não há inspeção visual Windows com janela estreita e DPI 125%/150% comprovando ausência de truncamento de todas as fitofisionomias IBGE.

### Próximos passos e condição de liberação
- Corrigir o teste de segurança e exigir sua aprovação no CI; resolver ou delimitar a indisponibilidade dos produtos SAR FH sem inventar estimativas quantitativas; documentar o estado dos acessos aos dados.
- Reprocessar e arquivar evidências reais de Marary, Tapajós e AOIs dos cinco biomas, com classificação, água excluída, fontes, estoques tC/tCO2e, incertezas defensáveis e solo 0–100 cm, além de validação visual da interface.
- **Atenção operacional:** a atualização deste prompt também cria novo commit e pode disparar outra compilação sem alteração do código. Não interpretar uma sequência de builds bem-sucedidos de commits exclusivamente documentais como avanço científico; distinguir nova embalagem de correção real.
- Somente liberar **versão definitiva** quando todos os requisitos técnicos e científicos estiverem comprovadamente aprovados e o ZIP corresponder ao **mesmo SHA homologado**, com hash verificado e documentação.

**STATUS 28/10/2026 06h06 UTC−3:** **MUDANÇA MATERIAL — WINDOWS #772 E DASHBOARD #443 APROVADOS; NOVO ZIP EXPERIMENTAL PUBLICADO. ERRO DE SEGURANÇA E AUSÊNCIA DE BIOMASS FH PERSISTEM EM TESTES NÃO BLOQUEANTES; HOMOLOGAÇÃO CIENTÍFICA AINDA PENDENTE. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 07h24 (UTC−3; 10h24 UTC) — WINDOWS #773 E DASHBOARD #445 APROVADOS; NOVO ZIP EXPERIMENTAL; BLOQUEIOS INALTERADOS

**Mudança MATERIAL desde 06h06:** para o head auditado da PR #50 **`6f2da51eb12d18537c361902792b2da531bcc200`** (commit exclusivamente documental anterior), o GitHub Actions concluiu **Windows #773** (run **40661737157**, job **122726171007**) e **dashboard #445** (run **40661737151**, job **122726171108**) com `completed/success` e publicou **novo artefato ZIP Windows**. A PR permanece `open`, `draft=true`, não mesclada. **Não foi comprovada nova correção de código, mudança de modelo ou validação científica desde o registro anterior; o avanço é exclusivamente de execução/embalagem do commit documental.**

### Evidências diretamente verificadas
- Windows #773: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40661737157 ; job **122726171007**. Logs consultados: **154 testes nativos OK** (linha ~1133), **243 testes gerais OK** (linha ~2500), build do executável, verificação do runtime empacotado, autoteste do EXE em pasta limpa e upload de artefato marcados `success`. O autoteste do Tapajós informa `SAR_PROCESSADO`, área **1.291,3187519527487 ha**, `data_origin=SAR_DERIVED_CCI`, cinco cenas, mas **não valida altura H100 nem AGB SAR de alta biomassa**; o próprio LEIA-ME gerado registra essas limitações.
- Dashboard #445: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40661737151 ; job **122726171108**. `Syntax check` e `Unit and regression tests` aprovados; log mostra suítes de **6 e 9 testes OK**.
- Novo artefato Windows **experimental**: nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID **12804098427**, **522.573.455 bytes**, criado **28/10/2026 09:19:34 UTC**, `expired=false`, expiração informada **27/11/2026 09:19:03 UTC**. Digest **informado pela API GitHub Actions, NÃO recalculado localmente**: **`sha256:2d4bbf5ee1d8c16ff05f9b2ffad1bfb23f983df447fb3b47be31faccabb97bca`**. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40661737157/artifacts/12804098427 . Download pode exigir autenticação. **Não apresentar como versão definitiva.**
- Artefatos auxiliares: PAM ID **12804246955** e diagnóstico de altura Tapajós ID **12804217784**; não são ZIP de distribuição.

### Falhas e lacunas reconfirmadas nos logs Windows #773
1. **Segurança de arquivos:** `archive_guard_test.py` novamente lança `AssertionError` na asserção `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1553–1557). O workflow fica verde apesar da falha. É necessário corrigir o contrato/implementação, testar aceitação de caminho legítimo e rejeição de `../escape.txt` e tornar o teste bloqueante.
2. **ESA BIOMASS FH/AGB no Tapajós:** `biomass_fh_probe.py` novamente lança `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI` (linhas ~1868–1871), com **FH 0 AGB 0** em AOIs investigadas. Ativos L1C encontrados continuam retornando **HTTP 401** (linhas ~1849–1852 e 1880–1883). O passo registra `Process completed with exit code 1` (linha ~1884), mas é tolerado pelo job. **Não há validação quantitativa de altura/AGB SAR de alta biomassa.**
3. **Homologação científica não demonstrada:** não foi comprovado reprocessamento completo de **Marary real** (KML original, raster oficial MapBiomas C11/2025, IBGE, água excluída e fechamento de área), nem demonstração auditada de todos os **cinco biomas** e compartimentos (AGB, raízes, necromassa, serrapilheira, solo **0–100 cm**) com tC/tCO2e, fontes, incertezas e validação espacial independente. Testes de contratos MapBiomas e exemplos de processamento real restrito não substituem essa comprovação.
4. **GUI:** contrato passou, mas permanece sem prova visual em Windows com janela estreita e DPI 125%/150% de que todas as fitofisionomias IBGE aparecem integralmente.
5. **Observação operacional:** esta atualização documental cria novo SHA e poderá disparar novamente CI. **Novo build de commit documental não deve ser tratado como avanço científico ou correção de software.** Evitar ciclo de recompilações documentais como substituto das correções efetivas.

### Critério de liberação
Corrigir e tornar bloqueante a segurança; obter e validar dados SAR FH adequados ou documentar indisponibilidade sem alegar estimativa quantitativa; reprocessar Marary, Tapajós e AOIs representativas dos cinco biomas com estoques, incertezas e auditoria real; validar interface visualmente; então gerar e verificar ZIP do **mesmo SHA de código homologado**, com hash e documentação. **O ZIP #773 é experimental.**

**STATUS 28/10/2026 07h24 UTC−3:** **MUDANÇA MATERIAL OPERACIONAL — WINDOWS #773 E DASHBOARD #445 APROVADOS E NOVO ZIP EXPERIMENTAL DISPONÍVEL; SEM CORREÇÃO DE CÓDIGO OU AVANÇO CIENTÍFICO COMPROVADO; SEGURANÇA E BIOMASS FH CONTINUAM FALHANDO EM ETAPAS NÃO BLOQUEANTES. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 08h30 (UTC−3; 11h30 UTC) — WINDOWS #774 E DASHBOARD #447 APROVADOS; ZIP EXPERIMENTAL NOVO, SEM CORREÇÃO DE CÓDIGO

**Mudança MATERIAL operacional desde 07h24:** o head da PR #50 permaneceu no SHA **`1bc71a49619d635f8d79e8fffb6e2c4646201b84`**, que altera **somente este documento** (verificação do commit). A PR permanece aberta, draft e não mesclada. Para esse SHA, o GitHub Actions concluiu com `completed/success` o **Windows #774** (run **40671972610**, job **122760741315**) e o **dashboard #447** (run **40671972620**, job **122760741290**). Houve **novo ZIP experimental**, mas **nenhuma correção de código nem homologação científica nova comprovada**.

### Evidências consultadas diretamente no GitHub
- Windows #774: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40671972610 — log do job consultado; **154 testes nativos OK** (linha ~1133), **243 testes gerais OK** (linha ~2500), compilação PyInstaller, verificação do runtime, autoteste do EXE em pasta limpa e upload concluídos. O autoteste Tapajós imprime `SAR_PROCESSADO`, área de **1.291,3187519527487 ha**, `SAR_DERIVED_CCI`, 5 cenas; **não** comprova AGB por modelo quantitativo P-band nem H100 de alta biomassa.
- Dashboard #447: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40671972620 — sintaxe e suítes com **6 e 9 testes OK**.
- Novo artefato Windows **experimental**, `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID **12808888411**, **522.571.740 bytes**, criado em **28/10/2026 10:36:34 UTC**, `expired=false`, expira em **27/11/2026 10:36:02 UTC**. **SHA-256 informado pela API GitHub Actions, não recalculado localmente:** `sha256:46d19aaec0b23fe1d1b037c8feae60bdf199ed4d1530ad409ea5c19fc7ccd7b6`. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40671972610/artifacts/12808888411 (pode exigir autenticação). **Não distribuir como versão definitiva.**
- Artefatos auxiliares: diagnóstico Tapajós 2010 **12808164089**, série PAM **12808128901**; não são executáveis.

### Bloqueios reconfirmados nos logs Windows #774
1. **Segurança de arquivos ainda falha:** `archive_guard_test.py` retorna `AssertionError` em `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1553–1557). A etapa `Professional scientific contracts` segue marcada sucesso; tornar o teste bloqueante, validar caminhos legítimos e impedir traversal.
2. **ESA BIOMASS FH no Tapajós ainda não validado:** `biomass_fh_probe.py` lança `RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI` (linhas ~1868–1871). O processo encerra com **exit code 1** (linha ~1884), mas o workflow prossegue e termina verde. Não há validação quantitativa de altura/AGB SAR em floresta de alta biomassa.
3. **MapBiomas e cinco biomas:** testes de contrato e regressão passaram, mas esta execução **não demonstrou** reprocessamento completo e auditado do polígono real de Marary com raster oficial MapBiomas C11/2025, IBGE, água excluída e fechamento espacial; tampouco os estoques AGB/raízes/necromassa/serrapilheira/solo **0–100 cm**, fontes, tC/tCO2e, incertezas e validação espacial independente nos **cinco biomas**.
4. **GUI:** sem evidência visual de legibilidade integral das classes fitofisionômicas IBGE em DPI 125%/150% e janela estreita.

### Ação exigida e critério de liberação
Priorizar correções **de código** e testes realmente bloqueantes em vez de novas recompilações induzidas por commits documentais. Resolver segurança, acesso e validação científica SAR ou registrar indisponibilidade sem inventar estimativas; produzir relatórios e evidências reais de Marary e AOIs dos cinco biomas, incluindo solo 0–100 cm e incertezas; verificar interface visualmente. Liberar apenas ZIP do **mesmo SHA de código homologado**, com digest recalculado e documentação.

**STATUS 28/10/2026 08h30 UTC−3:** **NOVO BUILD #774 E DASHBOARD #447 APROVADOS, ZIP EXPERIMENTAL PUBLICADO; SEM ALTERAÇÃO DE CÓDIGO OU AVANÇO CIENTÍFICO. SEGURANÇA E BIOMASS FH SEGUEM FALHANDO EM ETAPAS NÃO BLOQUEANTES; VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 09h05 (UTC−3; 12h05 UTC) — WINDOWS #775 E DASHBOARD #449 APROVADOS; NOVO ZIP EXPERIMENTAL; SEM MUDANÇA DE CÓDIGO

**Mudança MATERIAL estritamente operacional desde o registro das 08h30:** a PR #50 continua `open`, `draft=true`, não mesclada, no commit **`8183558c527ffd85b56e18da9508edc527eb129b`**. A inspeção direta desse commit mostra alteração **exclusivamente em `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md`**, sem correção de código. Para esse SHA, o GitHub Actions concluiu com `completed/success` o **Windows #775** (run **40680626827**, job **122790123025**) e o **dashboard #449** (run **40680626800**, job **122790122703**). Um novo ZIP Windows foi publicado; **não existe evidência de avanço científico nem de correção dos bloqueios**. A nova embalagem não constitui homologação.

### Evidências verificadas nesta execução
- Windows #775: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40680626827 — log completo do job consultado, **154 testes nativos OK** (linha ~1132) e **243 testes gerais OK** (linha ~2499), compilação PyInstaller, runtime empacotado, autoteste do executável em pasta limpa e upload marcados `success`. Autoteste Tapajós: `SAR_PROCESSADO`, **1.291,3187519527487 ha**, `SAR_DERIVED_CCI`, cinco cenas; isso **não** prova H100 ou AGB quantitativa de alta biomassa por ESA BIOMASS.
- Dashboard #449: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40680626800 — job **122790122703**, verificação de sintaxe e suítes de **6 e 9 testes OK**.
- **Novo artefato Windows experimental:** `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID **12812978381**, **522.570.435 bytes**, criado em **28/10/2026 11:42:24 UTC**, `expired=false`, expiração informada **27/11/2026 11:41:53 UTC**. Digest **informado pela API GitHub Actions, não recalculado localmente**: **`sha256:38dacf3418eafc033c98a0e72fda13eac78c30983ddc48904118722900b78ee8`**. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40680626827/artifacts/12812978381 . O download pode exigir autenticação; **não distribuir como versão definitiva**.
- Artefatos auxiliares: série PAM ID **12812792245** e diagnóstico de altura Tapajós 2010 ID **12812388388**. Não são ZIP do executável.

### Falhas e lacunas reconfirmadas no log Windows #775
1. **Segurança de arquivos:** `archive_guard_test.py` ainda lança **`AssertionError`** na asserção de caminho legítimo `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1553–1556). A etapa `Professional scientific contracts` é marcada sucesso apesar da falha. Corrigir o comportamento e tornar o teste bloqueante, com casos de aceitação de caminho válido e rejeição de traversal.
2. **ESA BIOMASS FH/AGB de alta biomassa no Tapajós:** `biomass_fh_probe.py` ainda lança **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** (linhas ~1869–1870), com processo encerrando em **exit code 1** (linha ~1883), mas workflow geral verde. Não alegar altura SAR H100 nem AGB P-band quantitativas validadas.
3. **MapBiomas real, cinco biomas e carbono:** o run não apresenta reprocessamento completo auditado de Marary real com KML, raster oficial MapBiomas C11/2025, IBGE, exclusão de água e fechamento de área; nem validação independente de AGB, raízes, necromassa, serrapilheira e solo **0–100 cm**, tC/tCO2e, fontes e incertezas nos **cinco biomas**. Testes de contrato não suprem essa evidência.
4. **Interface:** sem comprovação visual Windows para todas as classes fitofisionômicas IBGE em janela estreita e DPI 125%/150%.

### Próximas ações e regra de liberação
Priorizar commits com **correções de código e evidências científicas reais**, em vez de recompilações sucessivas geradas por commits exclusivamente documentais. Tornar a segurança bloqueante, resolver ou documentar rigorosamente a indisponibilidade SAR FH, auditar MapBiomas real/Marary e os cinco biomas com compartimentos e incertezas, e validar a interface. Somente considerar definitiva a versão cujos **requisitos técnicos e científicos estejam integralmente aprovados**, com ZIP produzido do **mesmo commit homologado**, digest verificado independentemente e documentação.

**STATUS 28/10/2026 09h05 UTC−3:** **WINDOWS #775 E DASHBOARD #449 APROVADOS, NOVO ZIP EXPERIMENTAL PUBLICADO; SEM ALTERAÇÃO DE CÓDIGO OU AVANÇO CIENTÍFICO. SEGURANÇA E BIOMASS FH AINDA FALHAM EM ETAPAS NÃO BLOQUEANTES. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 09h47 (UTC−3; 12h47 UTC) — WINDOWS #776 E DASHBOARD #451 APROVADOS; NOVO ZIP EXPERIMENTAL; SEM CORREÇÃO DE CÓDIGO

**Mudança MATERIAL estritamente operacional desde 09h05:** a PR #50 permanece `open`, `draft=true`, não mesclada, no commit **`9b96cf5262d153130d99f02d0adcfcbfc33c3b53`**. A consulta do commit confirma alteração **somente em `docs/PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-10-27_v43.md`**. Os workflows associados a esse mesmo SHA foram concluídos com `completed/success`: **Windows #776**, run **40685091452**, job **122805278289**, e **dashboard #451**, run **40685091428**, job **122805277999**. A compilação foi disparada por atualização documental, **sem nova correção de código nem avanço científico demonstrado**.

### Evidências efetivamente verificadas nesta execução
- Windows #776: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40685091452 — job e log consultados. **154 testes nativos aprovados** (log linha ~1133), **243 testes gerais aprovados** (linha ~2500), PyInstaller concluído, runtime empacotado, autoteste do EXE em pasta limpa e upload do ZIP marcados sucesso. Autoteste Tapajós: `SAR_PROCESSADO`, **1.291,3187519527487 ha**, `SAR_DERIVED_CCI`, cinco cenas (linha ~4303); isso **não demonstra** altura H100 nem AGB quantitativa ESA BIOMASS P-band em alta biomassa.
- Dashboard #451: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40685091428 — job e log consultados; **6 testes de dashboard e 9 testes meteorológicos aprovados**.
- **Novo artefato Windows experimental:** `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID **12815291273**, **522.573.281 bytes**, criado em **28/10/2026 12:16:50 UTC**, `expired=false`, expira em **27/11/2026 12:16:18 UTC**. **SHA-256 informado pela API GitHub Actions, não recalculado localmente:** `sha256:43b11ead2ecda672dc1d9fe124f86c052c1aef5736a3ad3f60c13bab8c564597`. Página: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40685091452/artifacts/12815291273 (download pode exigir autenticação). **Não distribuir como versão definitiva.**
- Artefatos auxiliares: série PAM **12813329753** e diagnóstico de altura Tapajós **12814044541**; não são executáveis.
- Commit compilado: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/commit/9b96cf5262d153130d99f02d0adcfcbfc33c3b53 — exclusivamente documental.

### Bloqueios reconfirmados diretamente no log Windows #776
1. **Segurança de arquivos:** `archive_guard_test.py` apresenta **`AssertionError`** ao testar caminho legítimo `_safe_target(root,'scene/subset.tif').parent==root/'scene'` (linhas ~1554–1557). O job permanece verde. Corrigir a implementação/contrato, testar aceitação de caminho legítimo e rejeição de traversal, e tornar o teste **bloqueante**.
2. **ESA BIOMASS FH/AGB no Tapajós:** `biomass_fh_probe.py` lança **`RuntimeError: Acceptance blocked: no ESA BIOMASS FP_FH__L2B covers either inventory-supported Tapajos AOI`** (linhas ~1873–1874). A consulta a ativos L1C registrou HTTP **401** (linhas ~1882–1883). O processo encerrou com **exit code 1** (linha ~1884), mas a falha não bloqueou o workflow. Não alegar validação quantitativa de H100/AGB P-band de alta biomassa.
3. **MapBiomas real, carbono e cinco biomas:** não foi demonstrado reprocessamento auditado de Marary real com KML original, raster oficial MapBiomas C11/2025, IBGE, exclusão de água e fechamento espacial; tampouco validação independente dos **cinco biomas** com AGB, raízes, necromassa, serrapilheira, solo **0–100 cm**, tC/tCO2e, fontes, incertezas e rastreabilidade. Testes unitários e contratos não equivalem à validação científica de campo/pixel.
4. **Interface:** sem comprovação visual Windows em janela estreita e DPI 125%/150% da legibilidade integral das classes IBGE.

### Encaminhamento e regra de liberação
Priorizar **correções de código e evidências científicas reais**, evitando tratar a sucessão de recompilações de commits documentais como evolução do software. Resolver segurança com teste bloqueante; obter/validar cobertura FH adequada ou registrar indisponibilidade sem inferir AGB não suportada; auditar MapBiomas/Marary, cinco biomas e compartimentos com incertezas; validar GUI. Somente liberar como definitiva versão com **todos os requisitos técnicos e científicos aprovados**, ZIP do **mesmo SHA homologado**, digest verificado independentemente e documentação.

**STATUS 28/10/2026 09h47 UTC−3:** **WINDOWS #776 E DASHBOARD #451 APROVADOS; NOVO ZIP EXPERIMENTAL; NENHUMA ALTERAÇÃO DE CÓDIGO OU VALIDAÇÃO CIENTÍFICA NOVA. SEGURANÇA E BIOMASS FH CONTINUAM FALHANDO EM ETAPAS NÃO BLOQUEANTES. VERSÃO DEFINITIVA NÃO LIBERADA.**


---

## ATUALIZAÇÃO DE CONTINUIDADE — 28/10/2026 — SINOP: PRIORIDADE SAR AGRÍCOLA E CORREÇÃO CONTROLADA DO CARBONO (SEM ALTERAÇÃO VISUAL)

**Ordem obrigatória de trabalho:** (1) tornar efetivos os identificadores agrícolas usando séries SAR tão recentes quanto tecnicamente possível; (2) corrigir falhas científicas e de integridade do carbono nativo; (3) validar rigorosamente regressões e compilar Windows somente após evidência. **Não modificar a forma de apresentação aprovada**: disposição, títulos, ordem dos compartimentos, formatação brasileira, tC/tCO₂e, legenda e organização dos painéis. Corrigir apenas conteúdo incorreto ou avisos metodológicos, sem alterar valores antes de validação.

### Teste real de referência — Sinop/MT, município IBGE 5107909
- AOI 399.087,54 ha; painel agrícola retornou `FALLBACK_CARTOGRAFICO`, MapBiomas C11/2025: soja 179.859,77 ha; outras áreas cultivadas 19.902,50 ha. Isso **não comprova detecção SAR**. Corrigir acesso/seleção de cenas, integração do pipeline e modelos; registrar no relatório motivo técnico exato do fallback. Não atribuir à safra atual áreas cartográficas anuais sem validação.
- Sentinel-1 multitemporal recente como rota prioritária para classificação, com data/hora UTC e UTC−3 quando realmente verificáveis, polarização, órbita, cobertura, máscara e qualidade. Priorizar cenas válidas mais recentes, mas usar histórico fenológico suficiente para diferenciar culturas; fontes SAR alternativas apenas quando compatíveis e úteis. Separar aquisição de produto anual composto.
- Detectar primeiro áreas cultivadas; identificar soja, milho, sorgo, café, cana-de-açúcar, arroz, feijão e citros apenas quando modelo treinado, atributos disponíveis e validação espacial/temporal independente sustentarem o rótulo. Caso contrário: `áreas cultivadas`; pastagem somente quando segura; ausência comprovada: `sem cultivos detectados`. Apresentar precisão, revocação, F1, matriz de confusão, calibração e incerteza por cultura; não inventar métricas. Manter previsão de produtividade bloqueada sem modelo SAR+clima validado.
- Corrigir mensagem contraditória `área da cultura no polígono não quantificada` quando houver área cartográfica de soja: distinguir área MapBiomas histórica de área SAR da safra atual.

### Diagnóstico do relatório de carbono de Sinop (arquivo fornecido pelo usuário)
- Área nativa 145.576,63 ha, estoque **parcial** 26.354.199,32 tC / 96.632.064,17 tCO₂e; **preservar como baseline de regressão, não homologar como total completo**. AGB proveniente de **ESA CCI Biomass v7 L4 anual 2024**, não de integração comprovada de altura SAR com inventários. Rotular precisamente método e data; não alegar H100/BIOMASS FH quando indisponível.
- Fitofisionomias: Floresta Ombrófila Densa 8.028,39 ha; Contato (Ecótono e Encrave) 20.826,54 ha; Floresta Estacional Sempre-Verde 116.706,22 ha; Formação Pioneira 15,50 ha. Soma de valores impressos 145.576,65 ha versus área nativa 145.576,63 ha (verificar arredondamento sem ajustar arbitrariamente). Área nativa + outros usos 253.508,88 ha = 399.085,51 ha, faltam 2,03 ha perante AOI; auditar geometria, água, máscara, arredondamento e fechamento espacial usando números não arredondados, sem dupla contagem.
- Biomassa subterrânea ausente no ecótono e formação pioneira; necromassa aérea/subterrânea e serapilheira ausentes em todos os estratos. Buscar estoques diretos em inventários e referências gravimétricas compatíveis por classe e proximidade, com hierarquia microrregional→regional→IFN/SFB→SINAFLOR, quantificar amostragem e transferência; não usar alometria para serapilheira; não criar números quando evidência insuficiente. Para raízes, verificar domínio e unidades da equação Cairns et al. (1997) e propagar erro da AGB mais erro residual/transferência.
- Solo cumulativo 0–100 cm deve permanecer; não somar 0–60/0–100/0–200 como estoques independentes. Desvio-padrão espacial zero **não é erro de predição zero**; obter incerteza preditiva e verificar fonte, profundidade, densidade aparente, fragmentos grossos e consistência espacial. Erro do produto AGB não equivale a IC95% do total; incorporar erro de área, covariâncias e validação independente antes de anunciar IC95%.
- Auditoria da classe água (170,68 ha `Corpo d'água continental` vs 14.272,12 ha `Rio, Lago e Oceano`) e dos rótulos IBGE/MapBiomas; preservar exclusão de água e agropecuária do carbono nativo.
- Preservar texto, estrutura e ordem do painel executivo; nunca substituir o bom desempenho de carbono por uma rota não validada. Testes de regressão por estrato, compartimento, áreas, fontes, tC/tCO₂e e formatação; diferenciar alterações intencionais de regressões.

### Alterações de código efetivamente registradas
- Commit `e49c71bc81806fae3b972b24b35346a6a8f97b55`: em `executive_carbon_report.py`, esclarece que desvio-padrão espacial igual a zero não implica incerteza de predição zero, **sem modificar estoque ou layout**.
- Commit `9d405f69c5b69d864c5bbd4a5aa29aafe8b67b54`: adiciona teste em `tests/test_carbon_presentation_regression.py` para esse aviso.
- **Não afirmar** que demais falhas foram corrigidas ou que os testes/EXE desta revisão passaram: ainda exigem execução CI e teste real Sinop. Manter pendências prévias de segurança do arquivo, ESA BIOMASS FH, Marary, cinco biomas e evidência científica. Não liberar ZIP definitivo antes de CI bloqueante e validação; evitar recompilar só por atualização documental.


---

## DIRETRIZ IMEDIATA — 28/10/2026: MODELOS INTERNACIONAIS, VIGOR EM TRÊS CLASSES, CLIMA E PREVISÃO DE SAFRA

**Pedido vinculante:** implementar a arquitetura integrada na aba existente `Monitoramento – Áreas Cultivadas`, preservando integralmente a aba de carbono nativo e a forma de apresentação aprovada (títulos, disposição, formatação brasileira, fontes, estoques, compartimentos e avisos). **Não declarar nova versão concluída antes de build Windows e testes reais aprovados.**

### 1. Identificadores agrícolas por transferência de modelos internacionais
- Inventariar modelos, algoritmos, pesos pré-treinados, código, licenças e domínios de validade de instituições científicas reconhecidas de qualquer país; priorizar trópicos e, na falta de modelos tropicais confiáveis, considerar outras regiões.
- **A aparência visual semelhante não garante assinatura SAR transferível**: incidência, órbita, VV/VH, banda, umidade, textura, manejo, cultivar, sazonalidade e fenologia alteram a resposta. Usar somente modelos realmente executáveis e compatíveis com as bandas, resolução e atributos disponíveis. Não atribuir ao SAR características de cor.
- Priorizar séries Sentinel-1 atuais, com histórico fenológico, metadados de aquisição verificáveis e tratamento de lacunas. Detecção de área cultivada precede classificação específica (soja, milho, sorgo, café, cana, arroz, feijão, citros). Se a cultura não for confiável, exibir `áreas cultivadas`; se ausência for demonstrada, `sem cultivos detectados`. Não confundir pastagem, silvicultura e vegetação nativa.
- Validar transferência com dados independentes espacial e temporalmente, matrizes de confusão, precisão, revocação, F1, calibração, desempenho por classe e região; registrar versão/licença/fonte/modelo. Sem evidência, permanecer em `modelo não validado` ou fallback cartográfico explicitamente datado.

### 2. Nova categoria dentro da aba existente: MONITORAMENTO DE VIGOR
- Incluir categoria **`Monitoramento de vigor`**, sem reformular a interface. Classes literais exigidas: **`lavoura pouco vigorosa`**, **`lavoura com vigor adequado`**, **`lavoura muito vigorosa`**. Somente atribuir classe com modelo e limiares calibrados para cultura e estádio fenológico; caso contrário, `vigor não classificável com confiança`.
- Variáveis SAR: retroespalhamento e sua evolução temporal, razões VV/VH, coerência quando disponível, textura, heterogeneidade horizontal, padrões de falhas, estrutura e proxies de dossel; altura/porte e sua uniformidade **somente** se houver estimativa estrutural compatível e validada. Coloração e reflectância são propriedades **ópticas**, não medidas por SAR; adicionar sensores ópticos apenas como complemento identificado e com nuvens/qualidade auditadas.
- Comparar cada lavoura a referências da mesma cultura, fase e ambiente; evitar classificar estágio inicial como pouco vigoroso apenas por baixa biomassa. Diferenciar vigor de fitossanidade confirmada e de produtividade final. Exibir fonte, data, estádio, indicador, incerteza e limitações.

### 3. Climatologia dinâmica integrada ao vigor
- Integrar NASA POWER, CPTEC/INMET quando confiáveis e disponíveis; usar precipitação, temperatura, radiação, evapotranspiração e déficit hídrico, com cobertura temporal, resolução, latência, falhas e proveniência explícitas.
- Avaliar modelos agronômicos publicados e reproduzíveis, como FAO AquaCrop e APSIM **somente nas culturas e versões para as quais existam parâmetros executáveis e licenças adequadas**. Ajustar a fenologia local, solos e calendário; evitar afirmar estresse fisiológico específico a partir de SAR isolado.
- Produzir vigor provável e sua incerteza mediante modelo SAR+clima validado; sem modelo validado, fornecer indicadores observados separadamente, sem estimativa causal inventada.

### 4. Produtividade/produção provável por séries microrregionais
- Agregar séries reais PAM/IBGE por município e microrregião com cultura, ano, unidade, área colhida, produção e rendimento; alinhar a safra e a janela temporal de aquisição SAR e clima. Não vazar informação futura no treinamento.
- Treinar/calibrar ou transferir modelos matemáticos publicados, avaliando baseline histórico/climático, SAR+clima e SAR+clima+vigor; usar validação bloqueada por ano e por região, RMSE, MAE, viés, R², cobertura de intervalos preditivos e comparação com baseline.
- Produção provável = produtividade prevista × **área da cultura na safra correspondente validada**. Não usar área histórica MapBiomas como área atual sem evidência. Sem cultura/área/modelo validados, declarar previsão indisponível e motivo exato.

### Entregáveis e critérios de aceite
1. Registro auditável de modelos internacionais com instituição, publicação, DOI, pesos/código/licença, sensores, culturas, regiões e limitações; seleção justificada e teste executável.
2. Pipeline real para SAR recente e classificação de culturas em AOI Sinop, incluindo prova de que não é apenas MapBiomas C11/2025.
3. Categoria `Monitoramento de vigor` operacional com três classes, classificação condicional, fase fenológica, indicadores e proveniência; testes de casos positivos e abstenção por falta de evidência.
4. Integração meteorológica e previsão de produtividade/produção com séries reais e validação temporal/espacial independente; bloqueio explícito de previsões não demonstradas.
5. Testes de regressão do carbono nativo, inclusive Sinop, Tapajós, Pantanal e Santo Ambrósio, preservando apresentação, solo 0–100 cm, tC/tCO₂e e avisos de incerteza.
6. CI Windows bloqueante, smoke test do EXE, relatório de validação científica, artefato ZIP verificável do mesmo SHA, digest e link de download. **Não confundir atualização de prompt, testes sintéticos ou compilação com homologação científica.**

**STATUS:** esta seção é especificação/ordem de implementação; não é evidência de que os modelos foram integrados, validados ou compilados.


---

## DIRETRIZ DE PERFORMANCE — 28/10/2026 — APIs SOB DEMANDA E LIBERAÇÃO RESPONSÁVEL

**Prioridade transversal:** menor tempo de resposta sem reduzir rigor científico nem alterar o layout existente. Adotar `metadata-first → filtro geográfico/temático → seleção científica → leitura por janela/arquivo → QA → cálculo → cache`. **Nunca** baixar todos os inventários ou planos de manejo do Brasil para o instalador Windows.

- **Inventários/PMFS/licenciamento:** priorizar APIs oficiais públicas (CKAN/SINAFLOR, Embrapa REDAPE/Dataverse, IFN/SFB quando houver serviço oficial compatível). PNLA é descoberta federada de processos, não API garantida de microdados; anexos restritos exigem acesso autorizado. Consultar metadados paginados, deduplicar IDs e DOI, limitar por UF/bioma/fitofisionomia/AOI e ano; obter só tabelas/parcelas úteis e disponíveis. Não assumir que metadado é inventário ou dado validado.
- **Implementado neste ciclo:** `official_inventory_harvest.discover_sinaflor_metadata_fast` com `package_search` paginado, sessão reutilizada e deduplicação, sem download nem `package_show` na descoberta; teste de paginação e ausência de download em `tests/test_official_inventory_harvest.py`. **Ainda não integrado ao fluxo completo do desktop nem validado no CI.**
- **Performance:** timeout e retries com backoff e jitter; limitação de taxa por servidor; cache persistente por URL+versão+ETag/Last-Modified e validade configurável; índice SQLite local compacto; cache LRU de cenas/tabelas e rasters recortados por AOI; transferências concorrentes com limite por host, não paralelismo irrestrito; downloads retomáveis e verificação de checksum; COG por HTTP Range e janelas raster; priorização de dados recentes e cancelamento de buscas irrelevantes. Degradação offline explícita, sem trocar ausência de dados por valores inventados.
- **Geoespacial:** interseção espacial antes de leitura integral; simplificação apenas para consultas preliminares, nunca para área final; CRS e topologia auditados; reprojeção e rasterização por bloco; evitar ler rasters nacionais em memória; resultados por estrato com áreas exatas.
- **Observabilidade:** medir tempo por fase (descoberta, download, recorte, classificação, carbono, renderização), bytes transferidos, cache hit rate, tempo frio/quente e consumo máximo de memória; publicar benchmark real em AOIs Sinop, Tapajós, Santo Ambrósio e Pantanal, comparando antes/depois sem perda de exatidão.
- **Aceite:** testes offline simulados e online reais, regressão de carbono e agricultura, performance com cache frio/quente, CI Windows bloqueante, EXE e ZIP íntegros do SHA aprovado. **Não declarar versão definitiva enquanto faltarem modelos agrícolas/vigor/safra e validações de carbono.** Manter rigor científico, proveniência e a forma de apresentação atual.


---

## REGISTRO DE VERIFICAÇÃO CI — 28/10/2026, 11h29–11h35 (UTC−3)

**Comparação com o registro anterior:** houve mudança material: o build Windows de um SHA anterior, que estava em andamento, terminou com sucesso e gerou ZIP; **não é o HEAD atual e não constitui homologação científica**. Preservar todo o histórico acima.

- **PR #50:** aberta, **draft**; branch `feature/agricultural-identification-native-carbon`; HEAD verificado: `3c8e33db98a4636186d05d2f8a3196666ea71584` (otimização API e documentação).
- **Build anterior — run 40700795637**, SHA `9816fc38ec3118c596eb10c63bf6464b8b1ab829`: `completed/success`. Evidências no job: `Source self-test`, `Inspect public IFN necromass and point schemas`, `Probe live BIOMASS FH coverage over inventory-supported Tapajos AOIs` e `Compiled EXE self-test from clean copied folder` concluídos com sucesso **como etapas CI**. Artefato `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, ID `12822745630`, 522.571.185 bytes, não expirado na consulta; link https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40700795637/artifacts/12822745630 . **Este ZIP é experimental, anterior às mudanças atuais; não liberar como definitivo.** Não foi verificado hash SHA-256 do conteúdo nesta consulta.
- **Build intermediário — run 40704980689**, SHA `006c384966f74971a48cb857b0dd6f5aeeac151a`: `in_progress` na consulta, sem ZIP Windows; somente artefatos de produtividade PAM e diagnóstico de altura Tapajós. Dashboard dessa revisão, run `40704980690`: `completed/success`.
- **Build HEAD — run 40706220012**, SHA `3c8e33db98a4636186d05d2f8a3196666ea71584`: `in_progress`, sem ZIP Windows na consulta; apenas `pam-microregion-yield-2015-2024`, ID `12824835240`. Dashboard HEAD, run `40706223913`: `completed/success`. Evidências: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40706220012 e https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40706223913 .
- **Pendências que impedem homologação:** não demonstrada validação real do MapBiomas e da identificação agrícola SAR atual, modelos internacionais de cultura, três classes de vigor, integração vigor–clima e previsão de safras; não comprovada cobertura funcional quantitativa dos cinco biomas e de todos os compartimentos, solo 0–100 cm com incerteza preditiva, raízes, necromassa, serapilheira, auditoria de área e fontes; sem benchmarks de APIs/caches, regressão científica abrangente, documentação e hash verificável do ZIP do HEAD.
- **Regra de liberação:** conclusão verde de CI/compilação ou presença de ZIP **não substituem** validação científica, nem autorizam denominação `versão definitiva`. Próxima verificação: observar run do HEAD, artefato e testes reais; registrar apenas mudanças materiais.


---

## REGISTRO DE CORREÇÃO REAL — 28/10/2026 — PAGINAÇÃO SEM TOTAL CKAN

- Corrigido `official_inventory_harvest.discover_sinaflor_metadata_fast`: a busca de páginas adicionais **não deve ser interrompida quando a resposta CKAN omite `count`**; antes, `int(result.get("count") or 0)` provocava término antecipado na primeira página. Agora o limite total só é aplicado quando `count` está presente; a busca termina por página incompleta ou `max_pages_per_term`.
- Acrescentado teste de regressão `test_fast_discovery_without_count_still_reaches_second_page` em `tests/test_official_inventory_harvest.py`, simulando resposta sem `count` e verificando a segunda página.
- Commits: `45361aea096ebd69114140510be35f151dd790bf` (código) e `b4a0b245174eb879ac673f6a5e04d3866c91936c` (teste).
- **Status honesto:** código e teste adicionados; execução do CI e integração operacional completa ainda exigem comprovação. A correção não autoriza declarar todos os inventários nacionais indexados nem os modelos SAR/vigor/safra/carbono homologados.


---

## NOVA DIRETRIZ VINCULANTE — BIOMASSA VIVA ABAIXO DO SOLO (BGB)

**Determinação:** estimar biomassa viva subterrânea por modelos alométricos compatíveis com a fitofisionomia e condições ecológicas da AOI; priorizar dados e modelos microrregionais de inventários florestais verificáveis. Instituições prioritárias: **todas as unidades da Embrapa, UFV, ESALQ/USP, UFLA, INPA, SFB/IFN**, além de universidades, institutos e redes científicas afins. Prioridade de origem institucional não substitui avaliação de qualidade, domínio e independência dos dados.

**Hierarquia operacional obrigatória:**
1. Dados primários microrregionais de biomassa de raízes (escavação/amostragem destrutiva, coring, monólitos ou outros métodos documentados), estratificados por fitofisionomia, profundidade, diâmetro e manejo; preferir modelos locais calibrados com amostras suficientes, incerteza e validação independente.
2. Equações locais ou regionais publicadas e executáveis, compatíveis com bioma, fitofisionomia, classe de tamanho, AGB, densidade da madeira, clima, solo e demais preditores efetivamente disponíveis.
3. Equações nacionais/regionais por fitofisionomia de instituições reconhecidas, com domínio de transferência e erro de extrapolação demonstrados.
4. **Modelos pantropicais publicados** somente quando aplicáveis à fitofisionomia, compartimento de raízes, preditores, faixa de biomassa e condições ecológicas da AOI. Não aplicar um fator raiz:parte aérea universal como se fosse medição local.

**Restrições científicas:** distinguir raízes vivas de raízes mortas e carbono orgânico do solo; distinguir raízes finas/grossas e profundidade de amostragem conforme o estudo. Nunca somar compartimentos sobrepostos nem assumir que modelo de raízes grossas cobre raízes finas. Propagar incerteza da AGB de entrada, parâmetros alométricos, resíduos, amostragem, classificação fitofisionômica e transferência regional, com covariâncias quando disponíveis; apresentar o tipo correto de intervalo (não rotular desvio-padrão ou envelope como IC95%). Registrar instituição, estudo/DOI, equação completa, unidades, domínio, N, qualidade, local, data, versão, fitofisionomia e motivo da escolha. Quando nenhum modelo for cientificamente defensável, marcar BGB não estimada com justificativa; **não inventar números**.

**Eficiência:** pesquisar metadados de Embrapa, UFV, ESALQ, UFLA, INPA, SFB/IFN e instituições afins por APIs públicas quando disponíveis, priorizando proximidade AOI/fitofisionomia; baixar apenas tabelas, parâmetros e arquivos necessários; cache de equações e metadados com proveniência. Não carregar uma biblioteca nacional bruta no instalador.

**Aceite:** testes para seleção microrregional versus regional/pantropical, rejeição de equações incompatíveis, unidades e propagação de erro, casos de abstenção, ausência de dupla contagem e regressão de todos os cinco biomas. Preservar integralmente o layout aprovado e os resultados existentes que sejam cientificamente válidos. **Este registro é requisito de implementação; não atesta que todos os modelos já estejam integrados ou validados.**


---

## VERIFICAÇÃO DE FONTE OFICIAL — ESA BIOMASS/CCI — 28/10/2026

Pesquisa na documentação oficial confirma **duas rotas distintas que não podem ser confundidas**:
- **ESA BIOMASS P-band, ESA MAAP:** catálogo de produtos PDGS Level 2A `FP_FH__L2A` (forest height) e Level 2B `FP_AGB_L2B`, `FP_FH__L2B` e `FP_FD__L2B`. A ESA MAAP oferece exemplo oficial de pesquisa STAC, streaming e download sob demanda: https://catalog.maap.eo.esa.int/doc/examples/ESAMAAP_biomassdataaccess.html ; especificação de oferta: https://portal.maap.eo.esa.int/biomass/biomass-data-offer/ . **Priorizar descoberta espacial/temporal STAC e leitura parcial dos produtos realmente disponíveis na AOI, verificando permissão, formato, QA, escala, data, CRS e incerteza.**
- **ESA CCI Biomass v7:** produto global **multissensor** de AGB anual a 100 m, com desvio-padrão por pixel, distinto do produto ESA BIOMASS P-band e de calibração SAR local. Fonte: https://climate.esa.int/en/projects/biomass/ . Nunca rotular pixel SD como IC95% da média da AOI, nem chamar o produto CCI de equação local de SAR calibrada em parcelas.
- **Regra de execução:** só declarar ESA BIOMASS P-band utilizado se houver produto efetivamente acessado, recortado, processado e com qualidade validada; quando indisponível, fallback CCI identificado e demais rotas cientificamente válidas, sem resultados fabricados. Os produtos ESA MAAP podem ter autorização específica e latência; não presumir disponibilidade irrestrita de todas as cenas.
- **Performance e aceite:** consulta STAC por bbox/interseção e intervalo, paginação, seleção de menor volume útil, streaming/range quando suportado, cache e benchmark por AOI. Testar disponibilidade real e erro; comparar saída do modelo contra inventários independentes e publicar RMSE, MAE, viés e R² quando estimáveis.
- **Status:** pesquisa documental oficial confirmada; **não constitui implementação nem prova de processamento P-band no executável**.


---

## CHECKPOINT DE CONTINUIDADE — 28/10/2026 — LIBERAÇÃO DEFINITIVA AINDA BLOQUEADA

**Revisão atual:** PR #50 permanece draft no SHA `e4880b2b3b10f2c158f9d770c015d24386951207`; execuções Windows `40708617996` e painel `40708617915` estavam na fila no momento da verificação. Não inferir sucesso de CI pendente.

**Fontes oficiais verificadas:** ESA MAAP publica tipos `FP_AGB_L2B`, `FP_FH__L2B`, `FP_FH__L2A` e acesso STAC; especificações oficiais BioPAL/BPS documentam formatos e algoritmos, inclusive ATBD AGB L2B versão 3.1.4 de 02/04/2026. ESA CCI Biomass v7 fornece AGB anual 100 m e incerteza por pixel (desvio-padrão), não IC95% por AOI. Fontes:
- https://portal.maap.eo.esa.int/biomass/biomass-data-offer/
- https://catalog.maap.eo.esa.int/doc/stac.html
- https://www.biomass-disc.info/docs/about/applicable-documents.html
- https://climate.esa.int/en/projects/biomass/data/

**Próxima execução exigida, por prioridade:**
1. Tornar bloqueantes os testes de regressão e de integração no Windows, inspecionar logs e resolver falhas; vincular artefato ZIP ao SHA testado.
2. Integrar consulta STAC real, filtro AOI/tempo/qualidade e leitura por janela; evidenciar cenas, datas, polarização, versões e incertezas, com fallback rotulado quando não houver P-band utilizável.
3. Selecionar equações BGB microrregionais/regionais/pantropicais por fitofisionomia com domínio e preditores completos; verificar unidades, raízes finas/grossas, profundidade, erro de transferência e ausência de dupla contagem.
4. Resolver necromassa, serrapilheira e solo 0–100 cm com dados compatíveis, estimadores e intervalos defensáveis; demonstrar funcionamento nos cinco biomas.
5. Integrar identificação agrícola SAR multitemporal, cultura e vigor fenológico com validação independente; previsão de safra somente após correlação observada com séries PAM/IBGE e meteorologia reais.
6. Medir desempenho real, cache frio/quente, transferência e memória em AOIs de teste, preservando interface e comportamento aprovado.

**Regra de honestidade:** commits documentais e builds verdes não equivalem à conclusão científica. Não rotular uma versão como definitiva enquanto faltar evidência experimental das funções requeridas.


---

## MONITORAMENTO DE CI — 28/10/2026, 11h52 (UTC−3) — MUDANÇA MATERIAL SEM HOMOLOGAÇÃO

**Comparação:** o checkpoint anterior registrava HEAD `e4880b2b3b10f2c158f9d770c015d24386951207` e os runs `40708617996` (Windows) e `40708617915` (painel) na fila. O HEAD agora é `41e8c454d7f7fea389469b0868a7a201ae29593d` (commit apenas documental); PR #50 continua **aberta e draft**.

**Evidência verificada no GitHub Actions:**
- HEAD `41e8c454`: painel `40708866766` **completed/success**; build Windows `40708866905` **in_progress**. No momento da consulta, os testes de origem, estratificação nativa, Pantanal, GUI, pré-visualização Sentinel-2 e processamento SAR público/Tapajós haviam passado; a classificação IBGE Tapajós ainda executava e as etapas finais, inclusive geração do EXE e autoverificação do pacote, ainda não tinham iniciado. O run continha apenas artefatos auxiliares PAM e diagnóstico H100, **sem ZIP de EXE**.
- Revisão anterior `e4880b2b`: painel `40708617915` **completed/success**; build `40708617996` ainda **in_progress**, na etapa `Build executable`, sem ZIP final disponível. Testes anteriores dessa revisão passaram, mas isso não homologa a revisão corrente.
- Links verificáveis: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40708866766 ; https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40708866905 ; https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40708617996 .

**Bloqueios mantidos:** ainda não existe evidência consolidada de validação científica de todos os cinco biomas, raízes e solo 0–100 cm com incerteza, SAR quantitativo e sua validação espacial independente, culturas/vigor e previsão de safra, benchmarks de desempenho, nem EXE Windows testado e ZIP do mesmo SHA. **Não liberar nem notificar como versão definitiva.** A aprovação de testes de contrato e de um painel isolado não comprova esses requisitos.


---

## CHECKPOINT DE COMPILAÇÃO WINDOWS — 28/10/2026, 12h54 (UTC−3) — AVANÇO MATERIAL, SEM HOMOLOGAÇÃO CIENTÍFICA

**HEAD verificado antes desta atualização:** `f895bc59b17decb9b681e052e2ebbd7e49770022`; PR #50 ainda aberta e draft.

**GitHub Actions da mesma revisão `f895bc59`:**
- Painel `40710305931`: **completed / success**.
- Build Windows `40710305957`: **completed / success**.
- ZIP existente e não expirado: artefato `12827007175`, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.574.672 bytes**, criado em 28/10/2026 15:09:08 UTC. Página verificável: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40710305957/artifacts/12827007175 .
- Demais artefatos: diagnóstico de altura Tapajós 2010 `12826831149` (357 bytes), série PAM microrregional 2015–2024 `12825697544` (898.085 bytes). Existência dos arquivos **não atesta** validação de seus conteúdos.
- **Etapas CI aprovadas observadas:** testes de origem, estratificação nativa, Pantanal, fallback Cerrado, testes de contrato GUI e de equações, prévia Sentinel-2 Tapajós, processamento SAR público Tapajós, classificação fitogeográfica IBGE, busca SICAR, processamento quantitativo ALOS-PALSAR Cerrado, consulta ao catálogo BIOMASS P-band em local AfriSAR, consulta de cobertura FH no Tapajós, build EXE, verificação de runtime Python empacotado e autoteste do EXE a partir de pasta limpa.

**Interpretação científica obrigatória:** CI verde comprova apenas os testes que foram executados. Consulta de catálogo ESA BIOMASS não comprova estimação local P-band validada; teste de contrato não demonstra calibração/validação espacial de AGB; download da PAM não comprova correlação independente SAR-produtividade; testes de fallback por bioma não demonstram ausência de viés nem estoques completos de raízes, necromassa, serrapilheira e solo 0–100 cm. Não há aqui benchmark auditado frio/quente nem prova de classificação robusta de cultura e das três classes de vigor em múltiplas AOIs reais.

**Status de liberação:** **artefato Windows experimental compilado com sucesso; NÃO versão definitiva homologada**. Não notificar o usuário como liberação definitiva, não mesclar a PR draft antes do aceite. Para concluir, obter evidência quantitativa independente de todas as funções científicas obrigatórias, teste integrado em cinco biomas, métricas de performance, histórico de erros resolvidos, e só então emitir release e link do artefato exato aprovado. Preservar rigor científico e aparência do painel.


---

## CORREÇÃO DE CÓDIGO — 28/10/2026 — PRIORIDADE DE RAÍZES MICRORREGIONAIS

**Alterações efetivamente incorporadas:**
- Commit `83fc75ac6b216379271f5d4caee54940f034fc0c`: em `native_carbon.estimate_native_components`, a checagem anterior `'Biomassa subterrânea' not in regional` exigia igualdade exata. Uma fonte como `Biomassa subterrânea — inventário microrregional` podia não ser reconhecida, permitindo calcular em paralelo a alometria generalizada Cairns (1997) e o estoque microrregional. Substituída por comparação normalizada de prefixo que reconhece descrições qualificadas de BGB e impede o fallback duplicado.
- Commit `f24b0fbd72a591f7f7154c027df3cf8988664b88`: acrescentado teste `RootBiomassSourcePriorityTests.test_microrregional_root_component_suppresses_generic_allometry` em `tests/test_native_carbon.py`, com SAR sintético controlado, BGB microrregional sintética e verificação de uma única linha BGB preservando fonte e valor. **Este teste não constitui evidência de dados reais de raízes.**
- **Validação pendente:** executar o novo teste no CI, depois validar inventários reais, modelos por fitofisionomia, incerteza residual e transferência geográfica; evitar rótulos de IC95% sem base estatística e estimar erro com independência amostral. **Não liberar o build anterior como definitivo.**

**Situação CI anterior a estes commits:** SHA `cc40c609c9d8127d6f02c0746dcb68fe4cb55170`, PR #50 draft; painel `40720842296` completed/success e build Windows `40720842251` in_progress. Esses runs não validam os commits de correção novos. Continuam os bloqueios de carbono nos cinco biomas, BGB/necromassa/serrapilheira/solo 0–100 cm, calibração SAR independente, identificação e vigor de culturas, previsão de safra e benchmark real.


---

## EVOLUÇÃO DE CÓDIGO — 28/10/2026 — API SINAFLOR INTEGRADA AO FLUXO REAL

**Alteração funcional:** a implementação principal `official_inventory_harvest.discover_sinaflor_datasets`, usada por `harvest_sinaflor`, deixou de pesquisar só os 100 primeiros registros por termo e passa a consumir `discover_sinaflor_metadata_fast` (paginação, deduplicação). Quando a resposta de `package_search` contém `resources` como lista, evita `package_show` redundante; se a chave falta, busca detalhes individualmente. Isso reduz chamadas de rede para respostas completas. **Limitação:** `max_pages_per_term` permanece finito (padrão 10), de modo que não se deve alegar descoberta exaustiva do país.

**Código:** commit `cc3d1235f71fbda290504ab8d2306303706842d6` em `official_inventory_harvest.py`.

**Regressões adicionadas:** commit `6d270c7274690b2a61506891afaf2ac3caf5c410` em `tests/test_official_inventory_harvest.py`, com verificações simuladas de metadados completos sem `package_show` e fallback quando o campo `resources` não está presente. A execução CI após esse SHA é necessária; testes simulados não substituem consulta real de API e verificação de conjuntos de dados.

**Aceite de desempenho pendente:** medir número real de consultas, bytes, tempo de descoberta e download em vários cenários, além de monitorar limites de taxa, timeout e servidores indisponíveis. **Não classificar como release final** sem as provas de SAR, carbono por compartimento e incertezas, agricultura/vigor/safras e teste integrado Windows.


---

## REGRESSÃO REFORÇADA — 28/10/2026 — TESTE EFETIVO DE PAGINAÇÃO SINAFLOR

**Problema comprovado no teste anterior:** o teste chamado `test_actual_sinaflor_discovery_uses_pagination_without_redundant_package_show` substituía por mock a própria função `discover_sinaflor_metadata_fast` responsável pela paginação; assim não exercitava efetivamente a passagem entre páginas pela rota principal.

**Correção incorporada:** commit `1b811e2eceaa63d5dda25daae2b68f05a4376481` modifica `tests/test_official_inventory_harvest.py` para executar o caminho real `discover_sinaflor_datasets → discover_sinaflor_metadata_fast → _ckan_action` e simular duas páginas oficiais, com 101 registros distintos e `count=101`. O teste exige duas requisições `package_search`, deslocamentos 0 e 100, todos os 101 resultados preservados e nenhuma requisição `package_show` redundante. Isto é uma simulação de API, não uma pesquisa nacional real, e não altera cálculos científicos.

**Situação no momento:** antes do commit, HEAD `58b84aef55ef31682bb1ebfb407e1973374a92b4` da PR #50 draft: dashboard `40722774304` completed/success e Windows `40722774295` in_progress. Necessário validar o SHA novo em CI e medir latência/transferência reais antes de afirmar ganho de desempenho.

**Bloqueios de release mantidos:** comprovação integrada e independente de AGB SAR/altura, BGB por modelos adequados, necromassa, serrapilheira, solo 0–100 cm e suas incertezas nos cinco biomas; detecção e classificação de lavouras/vigor com validação; modelos de rendimento com séries SAR/PAM reais; benchmarks reais e ZIP Windows do SHA homologado. Não liberar como definitivo apenas por testes verdes.


---

## CORREÇÃO REAL — 28/10/2026 — NÃO CONFUNDIR INVENTÁRIO PARCIAL COM COBERTURA NACIONAL

**Problema:** a função `discover_sinaflor_metadata_fast` limitava a descoberta por termo a 10 páginas sem registrar que a API CKAN possuía mais resultados, podendo induzir a falsa conclusão de que toda a coleção pública tinha sido consultada.

**Alterações incorporadas:** commit `648f2d8fb617699dfa6c81981f941c4559e54da6` obriga a rotina a interromper com erro explícito e acionável quando atinge `max_pages_per_term` ainda com página cheia e total CKAN não exaurido. Não retorna silenciosamente a amostra parcial como resultado completo. Permite ampliar `max_pages_per_term` ou refinar a consulta. Commit `1c684bc050c184a36cf7a7882f428180242364e3` acrescenta regressão simulando 300 registros com limite de duas páginas e ajusta o teste anterior de `count` omitido para terminar por página vazia. **Não constitui acesso efetivo a todos os dados do Brasil.**

**Risco residual e desempenho:** quando grandes resultados exigirem mais páginas, a integridade requer novas chamadas ou filtro regional, portanto medir latência e implementar filtros geográficos/UF sempre que a API suportar. `harvest_sinaflor` ainda baixa recursos suportados após descoberta; a obtenção seletiva por relevância de AOI e integração completa ao módulo de carbono continuam pendentes.

**CI antes das alterações:** PR #50 draft; SHA `d4c4312cbef4479748f68bb249118fdc35c00fa6`, painel `40723310274` completed/success e Windows `40723310468` in_progress. Os commits novos exigem novamente testes próprios. Sem evidência integral dos cinco biomas, BGB, necromassa, serrapilheira, solo 0–100 cm com incerteza, SAR/validação e culturas/vigor/safras, **não homologar a versão definitiva**.


---

## REGRA INFLEXÍVEL — FONTES MICRORREGIONAIS E COMPATIBILIDADE FITOFISIONÔMICA (28/10/2026)

**Determinação do usuário — vinculante para todo processamento de carbono:**

1. **AGB:** entregar estimativa pontual e intervalo de incerteza cientificamente interpretável sempre que existir observação SAR válida ou referência publicada transferível para a **mesma fitofisionomia**. Prioridade a inventários abertos com unidades amostrais primárias, localização, desenho e parâmetros; aceitar inventários totalizados de instituições reconhecidas quando classe, N/variância (ou intervalo válido), unidades, data e domínio estiverem documentados. Distância microrregional e qualidade ecológica são critérios de seleção, nunca licença para usar fitofisionomia distinta. Publicar se intervalo é preditivo, IC de média, desvio-padrão espacial ou envelope — não misturar.
2. **BGB viva:** estimar via equações alométricas cuja aplicabilidade à mesma fitofisionomia, solos/clima e domínio de biomassa esteja comprovada; priorizar unidades Embrapa, UFV, ESALQ, UFLA, INPA, SFB/IFN e fontes afins, locais antes de regionais e pantropicais. Quantificar incerteza da AGB, coeficientes, resíduo e **transferência**; se esses componentes de erro não puderem ser quantificados, não rotular a estimativa como cientificamente validada ou como IC95%. Proibir somar raízes vivas a raízes mortas e proibir duplicar BGB local + fator genérico.
3. **Solo:** sempre investigar/estimar estoque **0–100 cm**, preferindo perfis microrregionais compatíveis com classe/condições edáficas e método de profundidade, densidade e fragmentos grosseiros; se usar modelo/regionalização, documentar o domínio e o erro de predição para a AOI. Variabilidade espacial de pixel não é incerteza preditiva, tampouco IC95%.
4. **Necromassa (aérea ou subterrânea):** **não usar alometria de árvores vivas para necromassa**. Admitir exclusivamente observações diretas dos compartimentos relevantes oriundas de inventários publicados por instituição reconhecida e com compatibilidade fitofisionômica inequívoca; primárias de parcela primeiro, depois totalizadas auditáveis, respeitando proximidade. Propagar variância/desenho amostral/intervalos, além do erro de transferência espacial. Não extrapolar estadual bioma×UF quando não há estrato de fitofisionomia comprovado.
5. **Serrapilheira:** usar estoque de massa seca diretamente medido/gravimetria de mesma fitofisionomia, nunca deposição anual, proxy alométrica nem transferências de outras classes.
6. **Tentativa de estimar em todos os casos:** conduzir busca exaustiva **entre fontes verificáveis e compatíveis** com prioridade microrregional e, onde apropriado, utilizar modelos pan-tropicais aplicáveis. A obrigação de responder inclui sempre explicar fonte, método, cobertura, incerteza ou a impossibilidade demonstrada de quantificação defensável. Não gerar número falso ou intervalo arbitrário somente para preencher campo. Indicar explicitamente `NÃO ESTIMÁVEL COM INCERTEZA DEFENSÁVEL` quando nenhum método elegível existir. Fontes privadas somente com acesso autorizado, metadados e estatísticas auditáveis. Nunca confundir ausência de estimativa com carbono igual a zero.
7. **Desempenho:** consultas por API oficiais quando possível; índice geográfico por AOI/bioma/fitofisionomia, pré-seleção por metadados, download somente do dado necessário, cache com proveniência. Não sacrificar compatibilidade científica para reduzir tempo.
8. **Critérios de aceite:** testes unitários de seleção exclusivamente por fitofisionomia e preferência por fonte primária/microrregional versus totalizada/regional; propagação e rotulagem de incerteza; testes dos cinco biomas e sem regressão do painel. Sem métricas reais de erro de transferência, não homologar afirmações de estoque com IC95% local.

**Correção real incorporada agora:** `native_carbon.estimate_native_components` deixou de usar automaticamente `ifn_necromass_component` por bioma×UF como substituto da necromassa de uma fitofisionomia não documentada. O próprio fornecedor IFN registra que seus dados não trazem campo de fitofisionomia IBGE; portanto o intervalo de UAs não valida extrapolação entre classes. Commit `024a25f906767131cd256d2453851fa414c9262c`; teste `StrictNecromassPhysiognomyTests` commit `a16a36f39193fd4eef5ca39b981f2b2c77e7ef2c`. Teste aguarda execução do CI após esses commits. Esta alteração é cientificamente conservadora e pode aumentar campos N/D até que inventários compatíveis sejam integrados; isso é preferível a imputação não defensável.

**PENDÊNCIA NÃO RESOLVIDA:** integração automática de inventários microrregionais abertos e totalizados por fitofisionomia, escolha/validação completa das equações BGB, erro preditivo local de solos 0–100 cm, procura e agregação de necromassa/serrapilheira por classe, regressões e benchmarks integrados. Não declarar versão definitiva.


---

## REGRA COMPLEMENTAR IFN/SFB — ÚLTIMO RECURSO POR FITOFISIONOMIA (28/10/2026)

**Determinação:** somente utilizar médias estaduais do **Inventário Florestal Nacional (IFN/SFB) estratificadas pela mesma fitofisionomia** da AOI **depois** de esgotar fontes microrregionais e outras referências de maior pertinência, qualidade e confiabilidade. A fonte estadual não substitui inventários de parcelas locais ou totalizações locais auditáveis.

**Seleção vinculante:** 1. inventários primários de parcelas da mesma fitofisionomia e microrregião, com dados de variância/desenho; 2. inventários totalizados microrregionais da mesma fitofisionomia, de instituição reconhecida e com erro auditável; 3. estudos regionais da mesma fitofisionomia com domínio e incerteza de transferência defendíveis; 4. **IFN estadual POR FITOFISIONOMIA como último recurso**, desde que o estrato esteja documentalmente identificado, haja compatibilidade de medição/compartimento/unidades e não exista fonte melhor. A mera coincidência de bioma e UF **não** demonstra fitofisionomia e **não** autoriza cálculo, mesmo se a tabela publicar média e desvio-padrão.

**Transparência no relatório:** explicitar `Origem: SFB/IFN — UF [sigla] — fitofisionomia [nome] — estrato [identificador]`, ano/ciclo, número de unidades amostrais independentes, dados de estoque, método estatístico, fonte e URL quando disponíveis, razão documentada da escolha e aviso `fallback estadual`. Publicar IC da média, intervalo preditivo ou desvio-padrão segundo seu significado real, incorporando variação entre parcelas, efeito amostral, representatividade e transferência microrregional quando quantificáveis. **Quando a incerteza não puder ser estimada defensavelmente, declarar literalmente `incerteza não estimável com os dados disponíveis`, explicar por quê e não apresentar IC95% inventado.** Se política do compartimento exigir erro quantificado, manter valor apenas como referência contextual, **fora do total de carbono validado**.

**Necromassa:** a fonte IFN deve provir de medição direta de necromassa, jamais de equações alométricas de árvores vivas; inventários estaduais sem fitofisionomia explícita continuam excluídos da estimativa, como na correção `024a25f906767131cd256d2453851fa414c9262c`. A própria base atualmente consumida por `ifn_necromass_component` está agregada apenas por bioma×UF: portanto **não é elegível** para o fallback por fitofisionomia até a ingestão de dados oficiais estratificados e auditáveis. Essa orientação **ainda não implementa automaticamente** o novo conector/estratificação estadual nem habilita seu uso no relatório.

**Critérios de aceite:** testes que comprovem precedência de primária e totalizada local sobre IFN, veto de fitofisionomia ausente/incompatível, rotulagem completa de fallback estadual e publicação explícita da incerteza ou de sua impossibilidade; testes de integração por fitofisionomia, cinco biomas e painel aprovado, com fonte auditável.


---

## CORREÇÃO DE CÓDIGO — NECROMASSA AÉREA DIRETA EM PÉ + CAÍDA (28/10/2026)

**Falha encontrada:** `carbon_compartments.tapajos_necromass_components` disponibiliza componentes distintos de madeira morta caída (32,0 tC/ha) e em pé (8,7 tC/ha), publicados para floresta ombrófila densa em área microrregional. `native_carbon.estimate_native_components` normalizava ambos para `Necromassa aérea` e `summarize_native_carbon` reduzia as linhas a um dicionário por nome, de modo que um dos estoques podia sobrescrever o outro. Isso subestimava o compartimento somável sem nenhuma indicação ao usuário.

**Correção incorporada:** commit `9af35da02876fa7a80ebd6851aa0ed1002126647` consolida os dois estoques diretos **apenas** quando os nomes explicitam subcompartimentos disjuntos (madeira caída versus em pé), ambos possuem valores finitos e não negativos e têm a mesma referência. Valores do exemplo publicado: 32,0 + 8,7 = **40,7 tC/ha**. Os extremos marginais de cada subpool são somados apenas como **envelope**, explicitamente **NÃO** como IC95% conjunto — correlações e transferência espacial não conhecidas. Mistura ambígua entre estoque total e subpool **não é agregada** nem sobrescrita; nenhuma estimativa deste pool é exibida até resolver a ambiguidade.

**Regressões adicionadas:** commit `498fa356d087cd8fff1f22c30a81ed1951b7b8dc` inclui `DisjointNecromassAggregationTests` em `tests/test_native_carbon.py`: valida soma de 40,7 tC/ha, envelope de 35,7–45,7 tC/ha e recusa de total + subpool. Os testes foram adicionados ao repositório, mas **ainda requerem execução CI**.

**Regra permanente:** somente dados diretos de necromassa de mesma fitofisionomia, instituições reconhecidas, prioritariamente microrregionais; nunca alometria de biomassa viva para madeira morta. Não emitir IC95% conjunto de pools usando soma ingênua dos ICs marginais. **Não declarar versão definitiva** enquanto persistirem as demais lacunas SAR, carbono, fitofisionomias, agricultura, previsão de safra e validação independente.


---

## CORREÇÃO IMPLEMENTADA — 28/10/2026 — CONTROLE DE ERROS DA SOMA DE NECROMASSA

**Código:** `native_carbon.estimate_native_components`, commit `c05de68d8ca54abcba8762643318da8204630e19`. Reforçada a consolidação de estoques diretos disjuntos de necromassa aérea (madeira caída + em pé):
- Quando apenas um subcompartimento possui intervalo, a soma pontual pode ser apresentada **sem intervalo conjunto**; não herdar silenciosamente o IC publicado da parcela caída como se fosse do total.
- Quando ambos possuem intervalos marginais completos, finitos e coerentes (0 ≤ limite inferior ≤ superior), a soma dos limites é rotulada exclusivamente como envelope conservador, **não IC95% conjunto**, sem inferir covariância.
- Valores de estoque ausentes, não numéricos, negativos ou não finitos; fontes incompatíveis; e estrutura total+subpool ambígua **bloqueiam** a consolidação do pool, evitando a sobrescrita silenciosa anterior.
- Falta de incerteza conjunta é rotulada explicitamente `Incerteza conjunta não quantificada`. Para homologação científica com intervalo preditivo da AOI ainda é necessário conhecer desenho amostral, covariâncias, transferência fitofisionômica e incerteza espacial.

**Testes novos:** commit `ceaf0e0dd29116eafb1c6c0c09af07cead7917b3` em `tests/test_native_carbon.py`, incluindo `test_total_does_not_inherit_partial_fallen_interval` e `test_invalid_direct_stock_cannot_silently_replace_second_stock`. São testes controlados; a aprovação no CI do mesmo HEAD é obrigatória.

**Estado da entrega:** reparo localizado de contabilidade e comunicação de incerteza; não integra automaticamente todas as bases do IFN por fitofisionomia nem resolve os demais compartimentos e modelos agrícolas. PR #50 ainda requer todos os critérios de liberação, benchmarks reais e testes Windows. Não publicar artefato como definitivo antes da homologação total.


---

## AUDITORIA DE CI E ARTEFATO — 28/10/2026 13h49 (UTC−3)

**HEAD auditado antes desta anotação:** `653c71025da02063b7ef18145daec9c328da75c2`, PR #50 ainda **aberta e draft**. Comparação com o HEAD registrado na rodada anterior: **idêntico** (0 commits). Evidências GitHub Actions associadas **ao mesmo SHA**:
- `Dashboard dual - tests` — run **40727711191**, job **122955353842**, conclusão **success**; passos `Syntax check` e `Unit and regression tests` concluídos com êxito. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40727711191
- `Build Enform Verde Windows` — run **40727711326**, job **122955354666**, conclusão **success**. Etapas de testes de contrato, consultas live específicas, build, `Compiled EXE self-test from clean copied folder` e upload de artefato concluídas. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40727711326
- Artefato de Actions associado ao run: ID **12834207264**, nome `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, tamanho do arquivo de artefato **522.576.408 bytes**, `expired=false` na consulta. **Isto comprova a existência do artefato de Actions, não a homologação científica ou um download público permanente.** Não há checksum verificado nesta auditoria.
- No log do job Windows, às **16:48:39 UTC** o próprio README gerado adverte expressamente: **“Para Tapajós, altura H100 e AGB derivada de SAR continuam NÃO VALIDADAS”**. O mesmo log afirma **“Nenhum modelo nacional treinado vem embutido”** para a identificação algorítmica do uso do solo, exigindo atributos SAR e referências independentes para ativação; caso contrário utiliza fallback cartográfico. São **bloqueios científicos explícitos** para a liberação definitiva nacional.
- O log comprova AGB quantitativa ALOS-PALSAR em AOI de Cerrado, verificação de catálogo BIOMASS em sítio AfriSAR, consulta live para Tapajós e smoke test do EXE. **Não** comprova cobertura nacional dos cinco biomas, validação independente de AGB/raízes/solo 0–100 cm/necromassa/serrapilheira em todas as fitofisionomias, modelos SAR agrícolas treinados/validados, classes de vigor e previsão de safras com erro preditivo calibrado. Testes de contratos e smoke test não substituem esses benchmarks.
- **Decisão:** NÃO HOMOLOGADO; NÃO NOTIFICAR usuário como versão definitiva. Continuar validação e resolução dos bloqueios, sem confundir `success` dos workflows com prova de desempenho científico. **Esta anotação é novo commit de documentação e portanto altera o HEAD; o artefato supracitado pertence ao SHA anterior e NÃO pode ser atribuído automaticamente ao novo SHA.** Qualquer homologação futura deve demonstrar EXE compilado, testado e distribuído no **exato SHA** homologado.

**Pendências de aceite prioritárias:** (1) modelo e altura SAR Tapajós com erro validado e alta biomassa; (2) fontes IFN e inventários por fitofisionomia com incerteza e erro de transferência; (3) estimativa defensável de raízes e solo 0–100 cm nos cinco biomas; (4) classificação SAR agrícola nacional com treino e validação independentes; (5) classes de vigor/estresse e modelo SAR–clima–PAM de produtividade com desempenho fora da amostra; (6) benchmark integrado de AOIs reais e medição de desempenho; (7) checksum, pacote e smoke tests finais no mesmo SHA de liberação.


---

## PLANO DE RESOLUÇÃO CIENTÍFICA — 28/10/2026 (modelos e incerteza; NÃO HOMOLOGADO)

**Natureza:** especificação de implementação e validação, não evidência de implementação. Preservar todas as rotas existentes e histórico. SHA de base documental: consultar HEAD da PR #50 no momento da implementação; este registro não comprova build nem validação.

1. **AGB SAR real por fitofisionomia:** priorizar BIOMASS banda P com produto/algoritmo e qualidade verificáveis; aceitar CCI Biomass v7 (AGB e desvio-padrão por pixel) como produto remoto alternativo, rotulado corretamente, jamais como estimativa local SAR P direta. Máscara AOI × IBGE/MapBiomas, exclusão de usos incompatíveis, agregação com correlação espacial; calibração/validação com parcelas independentes, estratificação por fitofisionomia e faixa de biomassa. Reportar viés, RMSE, MAE, R², cobertura empírica dos intervalos e erro de transferência. Para Tapajós, não transformar altura ou AGB não validada em resultado homologado. BIOMASS FH somente com cobertura, qualidade e referência verificadas; GEDI como apoio claramente identificado.
2. **Raízes:** equação alométrica publicada aplicável ao domínio e fitofisionomia, com coeficientes e covariância; propagação conjunta de AGB, parâmetros e erro residual por Monte Carlo. Proibir razão raiz/parte aérea fixa sem justificativa científica e erro de transferência.
3. **Necromassa e serrapilheira:** somente dados gravimétricos/volumétricos e inventários pertinentes à fitofisionomia, sem alometria indevida para necromassa; hierarquia parcela aberta microrregional → inventário consolidado compatível → IFN estadual por fitofisionomia como último recurso. Variância amostral, efeito de desenho e heterogeneidade espacial; modelo hierárquico de transferência somente quando identificável por dados, sem atribuir precisão artificial.
4. **Solo 0–100 cm:** integração de horizontes 0–30, 30–60, 60–100 cm (ou limites observados), densidade aparente, fração de carbono, fragmentos grosseiros e correção de profundidade; respeitar massa equivalente quando comparações temporais o exigirem. Propagar incertezas dos horizontes e suas covariâncias; não extrapolar 0–30 para 0–100 sem perfil ou modelo validado.
5. **Agricultura:** pipeline SAR temporal de detecção cultivo/não cultivo → cultura específica apenas com probabilidade calibrada e validação espacial/temporal independente → rótulo genérico 'áreas cultivadas' quando identificação não confiável. Classes de vigor/estresse são indicadores indiretos, não diagnóstico fitossanitário. Previsão de safra por cultura e microrregião com PAM real, cenas SAR datadas e clima dinâmico, validação bloqueada por ano e região, comparação com baseline climatológico e histórico; somente habilitar previsão quando intervalo preditivo calibrado e desempenho fora da amostra superarem baseline.
6. **Motor comum de incerteza:** simulação Monte Carlo ou bootstrap hierárquico com covariâncias entre compartimentos e pixels; intervalos 95%, unidade tC/tCO2e, origem e data, N efetivo, métricas de validação e flag de estimativa remota versus transferência secundária. Incerteza do produto não equivale automaticamente à incerteza da média da AOI; tratar correlação espacial e erro sistemático. Se componente indispensável da incerteza não puder ser estimado, mostrar 'incerteza não quantificável com os dados disponíveis' e manter bloqueio científico correspondente.
7. **Critérios de aceite:** testes unitários de unidades, propagação, ausência de dados e domínios; AOIs reais nos cinco biomas; comparação independente parcela–pixel, cobertura dos intervalos de 95%, regressão de interface e desempenho; EXE Windows com smoke test e checksum no mesmo SHA da homologação. Nunca declarar liberação por CI verde isolado.

**Fontes técnicas para implementação:** ESA CCI Biomass v7 https://climate.esa.int/en/projects/biomass/ ; BIOMASS DISC https://www.biomass-disc.info/ ; ESA BIOMASS dados https://www.esa.int/Applications/Observing_the_Earth/FutureEO/Biomass/ESA_s_Biomass_goes_live_with_data_now_open_to_all .

**Estado:** pendências ainda abertas. Nenhum modelo treinado, calibração independente, execução nacional, pacote Windows ou checksum foi comprovado por este registro. NÃO HOMOLOGADO.


---

## IMPLEMENTAÇÃO PARCIAL CONTROLADA — 28/10/2026 — NÃO HOMOLOGADA

**Commits de implementação anteriores a esta anotação:** `0516ae9edc86e68a37459803332efa65e647062f` (núcleo de propagação) e `4ad81906ba30e1b03f8e94719b9b49b6faf5006b` (testes). Arquivos novos: `enform_uncertainty_core.py`, `test_enform_uncertainty_core.py`.

**O que está implementado no código-fonte:** função pura de agregação de estoques tC e tCO2e com matriz de covariância entre estratos/compartimentos, erro-padrão e IC normal aproximado 95%; função para calcular estoque de carbono de um horizonte de solo a partir de espessura, densidade, fração de carbono e fragmentos grosseiros. Testes de unidade, conversão e covariância adicionados, mas **a execução em CI, a integração na GUI, a compilação e a validação científica ainda NÃO foram verificadas**. Os valores de teste são sintéticos, não estimativas de campo. O IC normal não é adequado automaticamente a assimetria forte, calibração incerta ou distribuição não gaussiana; migrar para bootstrap/Monte Carlo calibrado quando houver distribuições e covariâncias fundamentadas. Matriz de covariância fornecida externamente deve ser estimada de dados válidos; não inventá-la. Verificar semidefinição positiva completa em integração posterior.

**Ações obrigatórias para modo operacional:** conectar núcleo ao pipeline por fitofisionomia, importar perfis reais de solo 0–100 cm e seus erros/covariâncias; ingestão de produtos BIOMASS L2 FP_AGB_L2B (AGB e desvio padrão), FP_FH__L2B (altura e flags) quando realmente disponíveis para a AOI; fallback ESA CCI v7 rotulado como fusão SAR/LiDAR (não BIOMASS P); validar espacialmente parcelas–pixel; incluir alometria de raízes com coeficientes verificáveis; inventários de necromassa e serrapilheira compatíveis; classificação agrícola SAR treinada e calibrada e previsão de safras somente após validação fora da amostra. Preservar painel executivo, classes e fontes, horário UTC/UTC−3, convenção numérica brasileira e todas as rotas aprovadas.

**Fontes confirmadas:** ESA CCI Biomass v7 https://climate.esa.int/en/projects/biomass/ (mapas globais anuais 100 m, 2015–2024 e incerteza por pixel); ESA BIOMASS MAAP https://portal.maap.eo.esa.int/biomass/biomass-data-offer/ (tipos de produtos L2A/L2B); ESA https://www.esa.int/Applications/Observing_the_Earth/FutureEO/Biomass/ESA_s_Biomass_goes_live_with_data_now_open_to_all (dados públicos desde 2026). Existência de produto em catálogo não prova disponibilidade/qualidade em cada AOI.

**Pendências de liberação:** integração real, dados de inventário e solo, modelos agrícolas calibrados, benchmark independente nos cinco biomas, cobertura dos IC, desempenho, regressão GUI, execução dos testes, build e smoke test Windows no mesmo SHA e checksum do artefato. **NÃO HOMOLOGAR, NÃO ANUNCIAR ZIP DEFINITIVO.**


---

## AUDITORIA AUTOMÁTICA DE CI, ARTEFATO E COBERTURA — 28/10/2026 15h32 (UTC−3)

**HEAD auditado ANTES deste registro:** `9d0a46e8d3a2e114cb67d794d5c7bf067fd4029d`; PR #50 aberta e draft; HEAD inalterado desde a atualização anterior. **Mudança material nos resultados externos:** workflows anteriormente em execução concluíram com sucesso, e foi publicado um novo artefato Windows referente exatamente ao SHA auditado. Evidências:

- `Dashboard dual - tests`: run `40734560688`, job `122979495378`, `completed/success`; os passos de sintaxe e testes do painel passaram. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40734560688
- `Build Enform Verde Windows`: run `40734560774`, job `122979495930`, `completed/success`; testes e verificações de contrato, consulta SAR real no Cerrado, checagem de catálogo BIOMASS, testes de integração controlados, build PyInstaller, smoke test do executável em pasta limpa e upload passaram. `python -m unittest discover -s tests -v` reportou **255 testes**. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40734560774
- Artefato Windows: ID `12837690935`, `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.575.526 bytes**, `expired=false` na consulta, criado em **2026-10-28 17:29:51 UTC**. Digest informado pelo GitHub Actions: **SHA-256 `2788cd3fe3962dbb93dcd4b5ccfd498364937a9606ab70a3b28fc6c6668b6601`** (digest do ZIP de artefato do Actions, **não** checksum local independente do EXE). Endpoint autenticado: https://api.github.com/repos/claudiodcandrade-lgtm/Enform-Verde.exe/actions/artifacts/12837690935/zip ; acesso via https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40734560774/artifacts/12837690935 . Artefato existente, não release público permanente nem homologação científica.
- Artefatos adicionais: `tapajos-2010-height-diagnostic-819` ID `12836797025` e `pam-microregion-yield-2015-2024` ID `12836778018`. Disponibilidade de séries e diagnóstico não demonstra modelo preditivo calibrado ou SAR de alta biomassa validado.
- **Lacuna adicional de cobertura de regressão detectada:** o módulo novo `enform_uncertainty_core.py` e seu arquivo de testes `test_enform_uncertainty_core.py` estão na **raiz**, mas os workflows executam `python -m unittest discover -s tests -v` ou descobertas seletivas dentro de `tests`. A inspeção dos logs não encontrou `test_enform_uncertainty_core` nem `UncertaintyCoreTests`. Portanto **NÃO está comprovado que os testes novos do núcleo de incerteza foram executados no CI**; mover ou duplicar os testes para `tests/` e adicionar teste de integração explícito no Windows, depois conferir logs.
- O README produzido no build ainda declara literalmente: **“Para Tapajós, altura H100 e AGB derivada de SAR continuam NÃO VALIDADAS”** e **“Nenhum modelo nacional treinado vem embutido”**. Isto mantém bloqueadas a homologação SAR de alta biomassa e a classificação agrícola nacional. O núcleo de covariância recém-criado não está comprovadamente integrado ao relatório/GUI nem validado com dados reais.
- **Pendências remanescentes:** modelos por fitofisionomia nos cinco biomas, AGB/altura SAR de alta biomassa com validação independente, raízes, necromassa, serrapilheira e solo 0–100 cm com incerteza total defensável, IFN por fitofisionomia com transferência auditável, identificação agrícola treinada, classes de vigor e previsões de safra calibradas e testadas fora da amostra, testes de regressão do núcleo novo, benchmarks de desempenho, interface final e checksum de distribuição no SHA final.

**Decisão:** **NÃO HOMOLOGADO; NÃO NOTIFICAR COMO LIBERAÇÃO.** A conclusão bem-sucedida do build é uma mudança material documentada, mas não satisfaz os gates científicos. Este registro altera o HEAD por ser um commit de documentação; o artefato Windows acima permanece associado ao SHA `9d0a46e...`, e **não** ao novo HEAD criado por esta anotação. Exigir ZIP compilado e testado no mesmo SHA de homologação futuro.


---

## CORREÇÃO DE COBERTURA DE TESTES — 28/10/2026, 15h37 UTC−3

**Mudança material:** commit `cd0ed1c1c311d8e5c25b8a6b234dd4fa4c93661b`: cópia dos testes de regressão de carbono/solo/covariância para `tests/test_enform_uncertainty_core.py`, dentro do diretório descoberto pelos workflows (`python -m unittest discover -s tests -v`). O arquivo original na raiz foi preservado. Esta alteração corrige o caminho de descoberta, mas **não demonstra que a execução do novo CI passou**; verificar logs e testes por nome no SHA novo.

**Evidência prévia:** build Windows SHA `9d0a46e8d3a2e114cb67d794d5c7bf067fd4029d` concluiu 255 testes, smoke test e upload de artefato; documentação anterior registra ID e digest. O executável daquele SHA não inclui a presente alteração. Não considerar esse artefato homologado.

**Pendências bloqueantes:** integração do módulo de incerteza à GUI e aos relatórios, solos 0–100 cm com perfis reais e covariância, raízes, necromassa e serrapilheira por fitofisionomia, AGB e altura SAR de alta biomassa validadas, classificadores agrícolas reais treinados e avaliados independentemente, classes de vigor e previsão de safras fora da amostra, cobertura dos cinco biomas, benchmark de desempenho, novo build Windows, testes e checksum do mesmo SHA. Manter PR #50 draft e proibir liberação definitiva até evidência de todos os critérios.


---

## AUDITORIA AUTOMÁTICA — 28/10/2026 16h36 (UTC−3): TESTES DO NÚCLEO DE INCERTEZA EFETIVAMENTE EXECUTADOS

**HEAD antes desta anotação:** `b3d80d43fee4a19805bf9e9d64a915eca1803081`; PR #50 aberta, em draft. **Mudança material comprovada em relação à anotação anterior:** os workflows do novo HEAD concluíram e os quatro testes antes ausentes da descoberta foram executados.

**Evidências verificadas no GitHub Actions:**
- `Dashboard dual - tests`: run **40746957206**, job **123023181911**, `completed/success`; sintaxe e testes de regressão concluídos. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40746957206
- `Build Enform Verde Windows`: run **40746957612**, job **123023187221**, `completed/success`; instalação, fontes, contratos, checagens SAR, PyInstaller, smoke test do EXE e upload concluídos. https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40746957612
- O log Windows registra **259 testes aprovados** na descoberta `tests/`, incluindo `UncertaintyCoreTests.test_correlated_strata`, `test_missing_covariance_rejected`, `test_negative_variance_rejected` e `test_soil_units`, todos `ok`. Assim, a lacuna de descoberta dos quatro testes foi **corrigida e verificada em CI**. Trata-se de testes de software com entradas sintéticas, **não** validação científica de dados reais.
- Artefato Windows gerado pelo run do **mesmo SHA auditado**: ID **12843330906**, `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, **522.574.187 bytes**, `expired=false`, criado em **2026-10-28 18:48:36 UTC**; digest informado pelo GitHub Actions: **sha256:ebcb9d2b1b37071511ad937c46c511872e33a3bd35109af1d751d9a145e93d55** (ZIP de Actions, não checksum local independente do executável). Acesso autenticado: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40746957612/artifacts/12843330906 . **Não** é release definitivo.
- Artefatos auxiliares: `pam-microregion-yield-2015-2024` ID **12841832988** e `tapajos-2010-height-diagnostic-822` ID **12841614738**. Não comprovam, isoladamente, previsão SAR–clima–produtividade nem validação H100.
- O README do mesmo build **continua advertindo expressamente**: “Para Tapajós, altura H100 e AGB derivada de SAR continuam NÃO VALIDADAS” e “Nenhum modelo nacional treinado vem embutido”. Portanto, o sucesso da compilação não supera os bloqueios científicos.

**Pendências de aceite ainda abertas:** AGB e altura SAR com validação independente em alta biomassa; carbono por compartimento (incluindo raízes, necromassa, serrapilheira e solo 0–100 cm) com incerteza calibrada por fitofisionomia nos cinco biomas; integração real do módulo de covariância na GUI e relatórios; identificação agrícola SAR com modelo treinado e validação espaço-temporal; vigor e previsão de safra defensável fora da amostra; desempenho integrado, regressões end-to-end e pacote final testado no SHA de homologação.

**Decisão:** **NÃO HOMOLOGADO; NÃO NOTIFICAR COMO LIBERAÇÃO.** Esta anotação cria novo commit documental e altera o HEAD; o ZIP comprovado pertence ao SHA `b3d80d43...`, não ao novo SHA resultante. Manter acompanhamento e exigir testes/build e checksum do SHA efetivamente homologado.


---

## EVOLUÇÃO CIENTÍFICA — 28/10/2026, 19h03 (UTC−3) — SOLOS PAREADOS E RAÍZES

**Objetivo:** corrigir um erro metodológico do módulo PronaSolos sem confundir variabilidade espacial de produtos de mapa com incerteza preditiva.

**Commits de código desta evolução:**
- `74288fd569f74e40b40f6c9cd966b47b020e7e5f`: `soil_profile_stats.py` — agrega horizontes apenas quando todos foram consultados **no mesmo ponto espacial**; proíbe preenchimento de ausência com zero e somas de perfis cumulativos; reporta desvio-padrão espacial real de totais pareados (preserva covariância espacial/horizontes dentro dos pontos), N por profundidade e ausência explícita de IC de predição.
- `23c430b8493c62445e8924c5875c1f516d5e1ee1`: `desktop_app.py` — conserta a composição de 0–30, 0–60, 0–100 e 0–200 cm a partir de valores coincidentes; o código anterior somava médias de horizontes calculadas sobre pontos diferentes e ignorava correlação entre camadas. Corrige texto da tela de Fontes: raízes da floresta de terras altas são obtidas com Cairns et al. (1997), não pela razão fixa 0,26 anunciada na interface. Equação condicionada ao domínio; erro residual/transferência ainda não quantificado.
- `2e759f9827e5b527da3262c0a15f4e16cd5b4454`: seis novos testes `tests/test_soil_profile_stats.py` abrangendo horizontes desencontrados, profundidades ausentes, covariância negativa entre horizontes, pares coerentes, zeros legítimos e entradas inválidas. Execução CI do novo SHA ainda pendente de comprovação.

**Evidência disponível:** alterações de código e testes commitados na branch da PR #50; nenhuma consulta PronaSolos real ou repetibilidade de mosaico raster validada nesta evolução. A correção metodológica é implementada, mas os testes de CI e smoke test do Windows revisado precisam ser conferidos no SHA correspondente. O último EXE anteriormente comprovado pertence a SHA anterior e não demonstra a correção atual.

**Pendências:** mapas 90 m representam valores modelados e o DP espacial das amostras **não** constitui IC95% do estoque da AOI. Para IC de estoque defensável é necessário mapear o erro preditivo do produto, autocorrelação espacial, viés local e covariância entre horizontes com observações independentes. Obter perfis e erros medidos por fitofisionomia, inclusive 0–100 cm, e validar nos cinco biomas. Persistem bloqueios anteriores de BIOMASS P e altura em alta biomassa, necromassa/serrapilheira e raízes fora de domínio, classificador agrícola nacional, vigor e safras calibradas, integração total, desempenho e homologação Windows.

**Estado:** NÃO HOMOLOGADO. Preservar painel, prioridades de fontes e funções aprovadas; continuar até comprovação de todos os critérios.
