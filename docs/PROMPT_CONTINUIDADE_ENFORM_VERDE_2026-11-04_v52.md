# PROMPT DE CONTINUIDADE — ENFORM VERDE 3.26.0-SOLO-SAFRA
**Revisão v51 — 04/11/2026 (UTC−3)**  
**Missão principal:** concluir o desenvolvimento, publicar o código e o executável Windows para **testes de acurácia em propriedades reais posteriormente**, sem exigir previamente a homologação científica final.  
**Situação confirmada na verificação:** HEAD `3ff63d1bcfbfbc1d0bd00d08b7042c6574336f3f`; testes de dashboard aprovados nesse HEAD; workflow Windows ainda em execução na consulta; gate científico independente reprovado por ausência de evidências observacionais exigidas. Não declarar EXE 3.26.0 pronto sem conferir artefato, SHA, instalação e execução.  
**Repositório:** https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe  
**PR #50:** https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/pull/50  
**Branch de trabalho:** `feature/agricultural-identification-native-carbon`.

## 1. Decisão expressa do usuário — separação dos marcos
O **marco A — liberação técnica para testes de campo** precede o **marco B — homologação científica de acurácia em propriedades reais**. É obrigatório concluir código, dados, interfaces, compilação, testes de integração e disponibilização do EXE de modo que o usuário possa realizar o marco B. Não usar a falta desses ensaios de campo como justificativa única para não entregar piloto experimental. Não falsificar ou preencher artificialmente `validation/release_evidence.json`, não chamar resultados experimentais de validados, não emitir certificado científico ou alegar confiabilidade do IC95% não verificada. O gate independente continua fail-closed para **homologação científica**, enquanto o gate técnico é distinto e audita a distribuição para testes.

## 2. Hierarquia das fontes, patches e preservação de funcionalidades
1. Aplicar integralmente os patches **0001–0017** fornecidos em `enform_patches_v3.26.0.tar.gz` usando os caminhos indicados; os patches prevalecem sobre trechos desatualizados da branch, preservando correções posteriores comprovadas e conciliando conflitos por teste.
2. Patch 0003 (amostragem adaptativa de estratos finos) já foi incorporado ao HEAD verificado; não duplicá-lo. Verificar patch a patch quais os outros efetivamente estão integrados antes de marcar como concluído. O overlay local recuperado **não equivale a commit publicado**.
3. Recuperar, sem regressão, carbono em vegetação nativa, classes IBGE, estoques tC/tCO₂e, incerteza, UI aprovada, relatórios e funcionalidades climáticas já funcionais.
4. Preservar acesso ao **MapBiomas** se efetivo. Preferir Coleção 11 para as classes compatíveis, registrar ano de referência e acurácia por classe quando disponível; se ocorrer HTTP 403, tentar cópia local/canal autorizado, com log; nunca fabricar classe nem converter fallback cartográfico em classificação validada.
5. Priorizar dados brasileiros e microrregionais compatíveis com a fitofisionomia; alternativas internacionais publicadas quando aplicáveis; IFN estadual por fitofisionomia como último recurso, com ausência de precisão publicada explicitada.
6. Atentar para termos comerciais/licenças de mapas PronaSolos/Embrapa, MapBiomas, SAR e recursos de terceiros. O funcionamento científico e a licença de redistribuição são verificações separadas.

## 3. Fluxo de entrada e classes
Entrada SHP/GPKG/GeoJSON/KML/KMZ, SICAR/SIGEF, geometria válida, CRS e reprojeção consistentes, área geodésica/equivalente, interseção AOI × classes fitofisionômicas IBGE, cobertura atual independente; campo/pastagem/cultivo/floresta plantada não entram em carbono de vegetação nativa. Identificar primeiro **área cultivada**, depois cultura, e somente depois vigor, fitossanidade aparente e previsão de safra. Em falha de reconhecimento, mostrar **“Áreas cultivadas — cultura não identificada”**; em ausência comprovada, **“sem cultivos detectados”**. Classes IBGE apresentadas completas, sem texto cortado.

## 4. Carbono na vegetação nativa
- AGB: prioridade SAR BIOMASS banda P quando produto apropriado; X compatível, L-band como alternativa, C-band apenas na ausência de melhor fonte; usar produto real de biomassa se disponível, não converter mapa por médias genéricas de inventário. Altura SAR (BIOMASS FH/IOP, TanDEM-X/GTDX; GEDI complementar) quando possível.
- Parcelas/inventários: hierarquia microrregional → regional → transferência documentada, sempre mesma fitofisionomia e janela temporal justificável. Calibração pares parcela–pixel, RMSE/MAE/viés/R², separação espacial e temporal para validar quando houver dados.
- Compartimentos: AGB, raízes alométricas, necromassa em pé/caída e serrapilheira apenas com fontes compatíveis; não inferir necromassa de uma equação de raízes. Solo integral 0–100 cm, separadamente. Unidades tC, tC/ha, tCO₂e, IC95% somente quando defensável, intervalo experimental quando não calibrado. **N/D ≠ zero**.
- Auditoria: cada componente e estrato com área, fonte, URL, versão, data, janela SAR, SHA-256 (se artefato), equação, parâmetros, denominador, incerteza e falhas. Horários como **“horário de aquisição (UTC−3)”** e **“horário de aquisição (UTC)”**, jamais “aquisição em Brasília”.

## 5. Solo Embrapa/PronaSolos 0–100 cm — prioridade crítica
1. Consultar cinco horizontes físicos 0–5, 5–15, 15–30, 30–60, 60–100 cm da mesma fonte/geometria; obter GeoTIFF numérico 90 m via WCS quando acessível, **não capturar a imagem renderizada de um MapServer como estoque**.
2. Soma por pixel `SOC_0_100,p = Σ_h SOC_h,p` se unidades forem Mg C/ha por horizonte; se origem concentração/BD/espessura, calcular `SOC_h(tC/ha) = 0,1 · C_h(g/kg) · BD_h(g/cm³) · Δz_h(cm) · (1−f_grossos,h)`.
3. Interseção exata AOI×fitofisionomia nativa×pixel e pesos por área em projeção equivalente EPSG:6933: `T_C=Σ_p (a_p,ha · SOC_0_100,p)`. Não extrapolar para pixels não cobertos; informar cobertura, proporção, áreas, nodata, células e arquivo de proveniência. Garantir alinhamento entre horizontes e cache hash.
4. Amostragem por pontos de estratos finos (patch 0003) é **contingência rotulada**, nunca substituto silencioso da interseção exata. Tratar erros/ausência com N/D e diagnóstico.
5. Intervalos e validação contra perfis WoSIS/Embrapa ficam como experimentais até amostra independente. Se solo apresentar 0–30 cm, não tratar como resultado 0–100 cm.

## 6. Agricultura, oito culturas e prioridades
Culturas-alvo: soja, milho, sorgo, café, cana-de-açúcar, arroz, feijão, citros; algodão acrescentado quando houver base. Pastagens e silvicultura são categorias separadas; diferenciação incerta permanece “áreas cultivadas”. Hierarquia dos classificadores: brasileiros abertos com artefato/modelo verificável → savanas africanas (CIRAD primeiro) → outros publicados. Para usar pesos, exigir hash, preditores, resolução, janela, classes, matriz de confusão, acurácia mensurável no domínio de validação e proveniência. Estudos sem pesos não são classificadores operacionais. MapBiomas pode identificar classes que efetivamente separa; não denominar milho/sorgo/feijão com base em probabilidade a priori PAM.

## 7. Vigor, fitossanidade aparente e clima
Vigor classificado em **pouco vigorosa / vigor adequado / muito vigorosa**, com probabilidades e evidência SAR temporal e espacial; altura média SAR quando disponível. Combinar medianas VH/VV, RVI (`4·σ°VH/(σ°VV+σ°VH)`), uniformidade `1/(1+CV)`, GLCM, variação de altura, padrões de falhas/linhas e contexto fenológico. Calibrar parâmetros por mesma cultura/fase/região; empregar robust z por mediana/MAD; indisponibilidade de séries ou comparáveis gera N/D. Fitossanidade apenas **aparente — bom/médio/ruim**, sem diagnóstico de patógeno. Clima dinâmico: NASA POWER prioritário, CPTEC complementar quando legal/técnico, INMET/BDMEP quando disponível; não usar Climatempo. Fonte, variáveis, janelas, faltantes, médias e previsões são explicitadas; ponderar fontes somente com base justificada.

## 8. Previsão de safra — modelos matemáticos e limites
Base histórica PAM/IBGE 2015–2024, 133.920 registros recuperados; agrupar por cultura/microrregião com área colhida e produção coerentes. Modelo-painel principal para culturas e microrregiões efetivamente calibradas: `y_u,t = α_u + β_u·t + γ_g·RY_u,t + ε_u,t`; `RY` do balanço hídrico FAO-56 e resposta `Ky` FAO-33 com parâmetros locais. Estimar γ_g com separação de efeitos e validar leave-one-year-out, preservando blocos geográficos. Com vigor observado, usar probabilidades dos tercis dos erros históricos; sem vigor, não assumir classe normal. Para talhões `P_total = Σ_s A_s · yhat_s`; Monte Carlo conjunto respeita correlação climática/temporal/microrregional e reporta intervalo, fontes de erro e **incerteza não quantificada**. Modelos solo-safra e analogias de transferência são **experimentais**; nunca anunciar precisão de propriedade ainda não medida. Soja e milho têm modelo-painel documentado; para outros cultivos sem treinamento adequado, fornecer cenário rotulado ou N/D, não inventar estimativas calibradas.

## 9. Os 17 patches — matriz de trabalho
- 0001 PAM gzip e .gitattributes; 0002 densificação IBGE e testes; **0003 já aplicado** amostragem estratos; 0004 documentação.
- 0005 interseção pixel solo/GeoTIFF WCS, relatório, integração; 0006–0007 documentação solo.
- 0008 hierarquia agrícola, vigor, favorabilidade climática, cenário PAM, geometrias IBGE e testes; 0009 documentação.
- 0010 validação exploratória mapa/perfis e triagem WoSIS; 0011 documentação.
- 0012 bump **3.26.0**, Windows workflow, testes e release notes; 0013 documentação.
- 0014 atualização DOCX e regra de documentação sincronizada; 0015 padrão visual e testes.
- 0016 modelo-painel FAO-56/33 e PAM com artefatos/testes; 0017 identificadores consolidados, vigor automático, monitoramento, testes.
Aplicar todos em ordem com resolução de conflitos, `pytest` (coleta completa, não apenas subconjunto), cobertura de falhas, empacotamento de dados e artefatos e validação funcional. **Não confundir arquivos recuperados em `/mnt/data/enform_326_overlay` com arquivos já comitados**.

## 10. Critérios obrigatórios para liberação técnica do piloto
Requer: (i) `git` limpo e commit imutável do código e documentação; (ii) suíte coletada e executada sem exclusões silenciosas; (iii) smoke tests dos fluxos com polígono brasileiro em cada bioma quando os dados estiverem disponíveis e testes unitários determinísticos com fixtures; (iv) área nativa/fitofisionomia, solo, SAR e módulos agrícolas com falha controlada N/D; (v) proteção das funcionalidades antes aprovadas e layout; (vi) EXE Windows sem exigir Python, com entradas/saídas testadas em máquina Windows limpa e `--visual-check`; (vii) hash do EXE, versão interna 3.26.0, SHA do código embutido, links do workflow e artefato para download; (viii) notas de release dizendo **PILOTO EXPERIMENTAL — NÃO HOMOLOGADO**; (ix) relatório de licenças e dados ausentes. Testes de acurácia em propriedades reais **não são requisito prévio** do piloto, mas sua ausência deve ser visível.

## 11. Critérios independentes para homologação científica futura
Para cada bioma × compartimento e funcionalidades agricultura/clima/vigor/safra, reunir dados primários ou observacionais rastreáveis, validação espacial/temporal independente, n, intervalos, viés, RMSE/MAE, domínio e permissões. O manifesto de evidências (`validation/release_evidence.json` e seu template) é preenchido apenas com registros verificados; faltas continuam no gate científico. Diferenciar testes matemáticos/contratuais do desempenho preditivo. Liberar uma linha de produto piloto agora **não significa** declarar o gate aprovado.

## 12. Política para qualquer falha ou lacuna
Usar rota tecnicamente defensável existente, retornar classe/estoque **experimental** quando houver fonte mensurável e erro/intervalo coerente; do contrário apresentar N/D explícito sem inventar. Falhas de API: timeout, status, licença, CRS, tile, nodata, hash, fonte e última tentativa em `enform_diagnostico.log`. Nunca utilizar conversão de incerteza inexistente para IC95%; nunca fazer imputação não identificada.

## 13. Engenharia e publicações a cada mudança
A cada alteração efetiva, atualizar **este prompt** e o Word `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` (ou sua revisão sucessora), relatório de patches, `APP_RELEASE_NOTES_v3.26.0.md`; incluir referência a algoritmo, equação, hipótese, entrada/saída, testes e status. O CI deve impedir código sem revisão documental. Publicar commits no PR #50 usando update_ref com `expected_sha`, sem force push; executar build Windows no mesmo SHA final, sem gerar commits intermediários que cancelem workflow anterior. Somente anunciar artefato depois de sua existência e inspeção.

## 14. Estado factual no momento desta revisão
- GitHub HEAD `3ff63d1bcfbfbc1d0bd00d08b7042c6574336f3f`. Dashboard dual tests em sucesso no SHA; gate independente em failure; Windows workflow em andamento na verificação, sem EXE 3.26.0 confirmado.
- Implementados e publicados nesta sequência anterior: trilha `experimental_audit.py` e testes; patch 0003 de estratos finos e regressões; documentos de rastreabilidade. Demais patches no overlay recuperado **não podem ser considerados integrados até verificação/commit**.
- Módulos de agricultura e solo recuperados localmente incluem `crop_identifier_consolidated.py`, `crop_vigor_auto.py`, `crop_panel_yield_model.py`, `pronasolos_wcs.py`, `soil_intersection_report.py`; exigem reconciliação com código da branch antes de compilar. Matriz de 17 patches permanece o roteiro de fechamento.
- Aplicar sem regressões o que foi validado previamente em carbono e interface; preservar MapBiomas quando o acesso real estiver funcionando.

## 15. Saídas finais obrigatórias
1. PR #50 atualizado com commits do código e documentação e relatório objetivo de patches aplicados; 2. prompt + especificação Word para download; 3. link **verificado** do arquivo ZIP Windows com `Enform Verde.exe`, SHA-256, build e instrução de instalação; 4. relatório de testes técnicos e limitações do piloto; 5. plano de validação de acurácia em propriedades reais em fase separada.

**Instrução final:** prosseguir até entregar o marco A sem esperar os testes de acurácia do marco B. Em todas as comunicações, distinguir claramente **realmente integrado**, **testado**, **compilado** e **homologado**.

## Correção CI e preservação da rastreabilidade — 2026-11-04
- Recuperada a função `nd()` em `soil_pronasolos_zonal.py` após integração de patch que produziu `IndentationError` na linha 101 do SHA 3618ed66. O solo sem cinco horizontes válidos retorna N/D, nunca zero.
- Mantida a checagem operacional de tipos raster: apenas float32/float64; raster uint8/renderizado deve ser rejeitado.
- Após o commit verificar `Dashboard dual - tests` e `Build Enform Verde Windows` no SHA novo. Não declarar sucesso antes da verificação.
- Liberação 3.26.0: piloto experimental tecnicamente funcional; a acurácia em propriedades reais será medida depois, sem baixar o nível de transparência ou simular validação independente.


## Integração de bases binárias — 2026-11-04
- Substituir na árvore Git a série PAM N9 2015–2024 corrompida por `data/pam_microregion_yield_2015_2024.csv.gz` (945226 bytes; SHA-256 `18b375cc39de635cf78abd192f8ff05bfa5b058d631b9d0956a3d68c04165db8`; Git blob `93fe179618f2fb6b63b460ef05e58240fd4e0bb7`). Atualizar metadados da mesma fonte; validar gzip, contagens e CSV.
- Incorporar `data/ibge_microrregioes_2021_simplificada.geojson.gz` (2496988 bytes; SHA-256 `1d8a48b938911831cc29b7c86af7e62f2ab8f762bd64d868a11b7e206f150bbc`; Git blob `b402109bd1d40f06c0f51f14f684f26f14c855fa`) e sua licença/metadados.
- Atualizar `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` com a v51. Não interpretar a série histórica PAM como validação de previsão ao nível de talhão; não publicar acurácia não calculada.
- Manter versão piloto tecnicamente testada como objetivo prioritário, reportar qualquer erro real de CI/Windows e conferir nome, tamanho e SHA do EXE antes de declarar liberado.


## v52 — CI documental corrigido, 826 testes e build piloto (04/11/2026)
HEAD de origem anterior à correção: `993a0f3bc7e93f2413e79b2c44dd0d5e830e9776`.
1. A bateria de 826 testes de regressão e os quatro testes nucleares de incerteza passou no commit `993a0f3b`, confirmada nos logs do workflow `Dashboard dual - tests`. A etapa posterior falhou por erro de sintaxe PowerShell no controle de documentação: `!(git cat-file -e "$base^{commit}" 2>$null; $?)` não é expressão válida. Não confundir falha do workflow com falha do motor científico.
2. Corrigir a condição em `.github/workflows/dashboard-dual-tests.yml` com validação de SHA via comandos PowerShell sequenciais, sem ignorar falhas. Persistir o gate de atualização documental.
3. Apontar `tools/check_docs_updated.py` para este prompt v52 e a especificação completa `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx`. Ambos devem constar no diff quando código/workflow/dados mudarem.
4. Com a série PAM e a malha IBGE agora incorporadas ao repositório, reexecutar os 826 testes completos, a checagem documental e o build Windows no MESMO SHA. Registrar resultado preciso de cada job e smoke test do EXE.
5. A versão piloto 3.26.0-SOLO-SAFRA pode ser liberada antes da homologação de acurácia em propriedades, que será medida posteriormente. O gate científico independente continua verificável e fail-closed; não preencher evidências fictícias.
6. Dados e fórmulas seguem hierarquia científica do corpo principal: SOC 0–100 cm por cinco horizontes no mesmo pixel, interseção exata e cobertura; AGB SAR e fitofisionomias IBGE; identificação de culturas prioritária, vigor e safra experimentais com rastreabilidade e incertezas declaradas.
7. Sempre diferenciar no relatório funcionalidades testadas, simulações e evidência independente real. MapBiomas deve permanecer quando o acesso for válido.


## ADENDO OPERACIONAL v53 — 04/11/2026 — SINOP, MONITORAMENTO DE LAVOURAS
Este adendo prevalece sobre qualquer bloqueio de vigor pelo simples fato de a AOI ser municipal. A área municipal pode ser analisada por completo **desde que cada análise agrícola tenha máscara espacial de cultura**. A interface e a validação de carbono nativo não podem regredir.

- Falha identificada em Sinop: MapBiomas C11 nomeou 179.859,77 ha de soja, mas as chaves do pipeline eram `soja` vs. `Soja`, levando ao falso aviso "sem modelo calibrado". Corrigido por `canonical_crop` em `crop_monitoring_forecast.py`.
- `land_use_sar.run_land_use` já grava os polígonos disjuntos em `uso_solo_intersecao.geojson`. Nova função `crop_spatial_monitoring.crop_geometry` lê esse resultado, seleciona **somente** polígonos `Lavoura de [cultura]` de fontes elegíveis e exclui formações nativas, água, infraestrutura urbana e outras coberturas.
- Uma AOI municipal superior a 5.000 ha usa `sample_crop_patches`: no máximo seis recortes internos de aproximadamente 64 ha, classe de referência com pureza cartográfica mínima de 90%, em várias regiões da geometria. `sampled_sentinel_vigor` aplica Sentinel-1 VV/VH real em cada recorte e agrega as probabilidades por área válida de amostra. Não é uma amostra probabilística representativa nem mapa wall-to-wall; registrar N/D quando a cena e a referência de cultura faltarem.
- O módulo de vigor deve reutilizar o **mesmo GeoTIFF MapBiomas já acessível** utilizado pela classificação, inclusive caminhos locais Windows. Se ocorrer 403, falta de referência, cena ou máscara, registrar erro e N/D, sem inventar vigor.
- A previsão regional de soja/milho usa o modelo-painel PAM/FAO-56/FAO-33, clima NASA POWER e erros leave-one-year-out; pode produzir distribuição experimental mesmo sem vigor SAR, usando a distribuição residual total. **A previsão sobre a área cartográfica não é rendimento observado nem validação municipal**. A interface substitui o rótulo antigo BLOQUEADA quando houver resultado efetivo, e mostra produtividade e produção experimentais com intervalos e ressalvas.
- O modelo opera por cultura e por polígonos; quando houver máscaras de segunda safra, elas devem ser agregadas separadamente e nunca somadas indevidamente às classes de primeira safra. Em grandes municípios os recortes SAR são amostras diagnósticas, não vigilância exaustiva de todos os talhões; operacionalização wall-to-wall, por talhão e validação de área permanecem futuras.
- Carbono nativo preservado: nenhuma modificação em `native_carbon.py` ou nos motores SAR/solo. O novo teste `tests/test_municipal_crop_masks.py` verifica a exclusão da vegetação nativa e a amostragem em geometria de lavouras; a suíte integral ainda exige verificação no SHA final.
- IFN/SFB serrapilheira: a base corrigida 2025 contém espessura da camada em centímetros, com cinco medições por UA. Estimar SE/intervalos de **espessura** por bootstrap de UA respeitando desenho e classe quando compatível. Não produzir tC/ha por profundidade sem dados independentes de massa seca pareada e fração C, com propagação da calibração e do erro de transferência. Inventários gravimétricos microrregionais compatíveis continuam prioritários.
- Commits desta etapa: `2ef96798`, `fb950498`, `f1533a42`, `4b211878`, `55034796`, `5b03b0e7`. Atualizar SHA final e release notes após CI. A especificação técnica correspondente foi produzida como arquivo de revisão v53 para download, mas ainda requer sincronização binária no GitHub.
- **Não anunciar novo executável** até conclusão de `Dashboard dual - tests`, `Build Enform Verde Windows`, autenticação das dependências de dados e autoteste EXE em Windows no MESMO SHA. A homologação científica independente continuará separada.


### Adendo v54 — regra de validade do vigor municipal Sentinel-1 (Sinop)
A execução por município exige cobertura rastreável das parcelas agrícolas. O protótipo atual analisa recortes internos de polígonos MapBiomas (diagnóstico, e NÃO monitoramento exaustivo de todos os talhões). Registrar por cultura `mapped_crop_area_ha`, `sample_area_ha`, `sar_sample_coverage_fraction`, quantidade de recortes e cenas, datas UTC e erros. **Não aplicar as probabilidades de vigor das amostras à totalidade de Sinop na equação de rendimento.** `crop_monitoring_forecast` passa vigor N/D à previsão regional enquanto a representatividade espacial não estiver demonstrada, preservando o modelo-painel PAM/FAO e as distribuições de resíduos completas. Separar claramente: identificação cartográfica anual (2025), observação SAR amostral atual e projeção regional experimental. Código efetivo: `f5f025b1`, `a06b22d3`. Próximo marco: classificação SAR temporal espacialmente exaustiva por polígonos/células com cobertura, máscara de cultura, erros de atribuição, calibração fenológica e validação por blocos. Proibido afirmar tal implementação já pronta; relatório deve explicitar o que falta. Carimbo e artefato somente do SHA final com CI concluído.


## CORREÇÃO EFETIVA 04/11/2026 — compilação de relatório Sentinel-1
A execução de CI no SHA df5aebeb falhou na compilação Python de `crop_monitoring_forecast.py` por fechamento incorreto de parênteses na formatação do campo "Cenas auditáveis". O erro foi corrigido no commit e27c8707529e102702d0e2d83639da1f85a4efc3, separando a composição de `scene_ids` da string de relatório. Próxima obrigação: confirmar o CI de compilação, suite completa e EXE do mesmo SHA. Não reutilizar binários anteriores como se contivessem a correção. As demais pendências de evidência operacional Sentinel-1 em Sinop, de conversão gravimétrica IFN serrapilheira e KMZ auditável ainda necessitam resolução independente.


## Atualização 04/11/2026 — produtividade de soja com duas unidades
Correção publicada em `crop_forecast_pipeline.py` (commit bce37bc9), `desktop_app.py` (commit f1285750) e teste `tests/test_soybean_productivity_dual_units.py` (commit 95c51a9c): para SOJA preservar produtividade e os quantis preditivos p05, mediana e p95 em **t/ha**, acrescentando os mesmos quantis em **sacas/ha de 60 kg**. Conversão exata: `t/ha = kg/ha / 1000`; `sacas/ha = kg/ha / 60 = t/ha * 1000 / 60`. Mostrar as unidades simultaneamente no relatório de previsão detalhado e painel executivo, sem alterar valores matemáticos, parâmetros, quantis, incertezas, status experimental ou as culturas diferentes de soja. Conferir CI do commit mais recente; nenhum build anterior contém esta alteração. Atualizar a especificação Word canônica no repositório e recompor EXE do mesmo SHA antes de declarar nova versão pronta.


## CHECKPOINT MODELOS POR CULTURA E INCERTEZA DE SOJA — 04/11/2026
- Commit b1dfc9da: `crop_forecast_pipeline.py` expressa intervalo preditivo central de 90% da soja em t/ha e sacas de 60 kg/ha, com desvios percentuais assimétricos da mediana: -100(m-q05)/m e +100(q95-m)/m. Se m=0, porcentagem N/D. A transformação das unidades não altera incerteza estatística ou predição.
- Commit 4d0d1056: apresentação idêntica no painel executivo `desktop_app.py`. Testes em `tests/test_soybean_productivity_dual_units.py` incluem casos de conversão, assimetria e zero.
- Commit c6b8fb19: `crop_specific_model_registry.py` documenta modelos fisiológicos por cultura para Soja (CROPGRO), Milho (CERES/IXIM), Sorgo (CERES), Feijão (CROPGRO), Arroz (ORYZA/CERES), Cana (APSIM/CANEGRO), Algodão (CROPGRO), Café (agrometeorológico e bienalidade) e Citros (fenologia e frutificação), com requisitos de SAR por fenofase e variáveis meteorológicas particulares. Pesquisado NÃO significa solver instalado ou calibrado. `CURRENT_CALIBRATED_PANEL` contém somente Soja/Milho, com modelo PAM/FAO, experimental.
- Commit c243e204: `crop_monitoring_forecast.py` lista modelo especializado como PESQUISA não executada e audita necessidades por cultura. Commit a03f4694: teste de cobertura 9 culturas e vedação de falsa integração.
- Requisitos de integração efetiva: dados reais Sentinel-1 VV/VH com cenas <=30 dias, SAR multitemporal e máscara de culturas, etapa fenológica com incerteza, NASA POWER diários com proveniência, solo, PAM por microrregião, validação independente temporal e espacial, erro de previsão total. Separar projeção histórica regional sem condicionamento SAR de verdadeira previsão condicionada a observações radar.
- Pendências críticas N/D até evidência: coleta pixels atuais para cada AOI, treinamento/validação dos identificadores milho/sorgo/algodão, execução local dos solvers agrícolas por espécie e parâmetros de solo/genótipo/manejo, calibração gravimétrica de serrapilheira SFB/IFN e testes de classificação no município inteiro.
- Nunca liberar ZIP anterior como contendo commits novos. Usar sha do HEAD, CI de suite, autoteste EXE, checksum e ZIP do MESMO SHA. Gate científico não pode ser dispensado nem adulterado.


## CHECKPOINT 04/11/2026 — vigor SAR: porte, uniformidade e textura/rugosidade com incerteza por indicador
Código real:
- `crop_vigor.py` em 95da35fe: mede RVI mediano ou altura quando disponível (porte aparente), uniformidade = 1/(1+CV do RVI multilook 3×3), homogeneidade GLCM da polarização VH em dB (indicador de textura, NÃO rugosidade física). Produz quantis p05/p95 de cada índice por bootstrap espacial em blocos 5×5 e probabilidades descritivas de classe. Não afirma acurácia de campo; quando bootstrap inválido retorna N/D.
- `crop_spatial_monitoring.py` em 916faa38: retém no JSON de cada recorte valores, intervalos dos índices, identificador e idade da cena, pixels, probabilidades, fontes e metadados de rastreabilidade quando fornecidos.
- `crop_monitoring_forecast.py` em 0ee24bf6: mostra os três índices e seus intervalos nos relatórios e preserva auditoria detalhada; não extrapola amostra SAR para produtividade municipal.
- `tests/test_crop_vigor_metric_uncertainty.py` em ff608047: testa métricas, intervalos, probabilidades normalizadas e ausência de referências. Arranjos sintéticos são APENAS fixtures de teste e não prova orbital.
- Persistem requisitos de imagem REAL Sentinel-1 VV/VH recente <=30 dias, cobertura temporal e territorial, comparação com lavouras da mesma cultura e mesma fenofase; erros de transferência e acurácia somente com validação externa. Não converter automaticamente a textura em doença/praga, densidade de plantas, altura física ou produtividade.
- Integrar a matriz PAM × fases FAO-56/FAO-33 × vigor SAR apenas quando forem estimados os coeficientes de vigor/interação com observações independentes de produtividade; sem isso, modelo regional PAM/FAO mantém rótulo experimental e SAR-conditional yield = N/D.


## CHECKPOINT 04/11/2026 — modelo experimental por prior publicado; testes unittest; KMZ reais
HEAD de código e testes verificado: `efff34a250b528a8059294f5354e05e0035dae2f`. Depois de introduzir as rotinas por cultura, o CI (Dashboard dual) detectou que quatro `tests/test_*.py` não eram descobertos por `unittest`, por conterem funções pytest e import `pytest` indisponível. Correções efetivas: commits c3d3e22e (soja 3 unidades), d24d8022 (registro 9 culturas), 4c705d08 (matriz fenológica), a613b0a5 (incerteza porte/uniformidade/textura). Testes agora usam `unittest.TestCase`; confirmar resultado do CI após HEAD novo.
Nova função `experimental_prior_projection` em `crop_yield_phenology_matrix.py`, commit bc6f1c61: previsão experimental PAM×FAO-56/FAO-33×vigor SAR condicionada a coeficientes e erro publicado compatível com cada cultura/fase. Propaga por Monte Carlo coeficientes, erro da linha de base PAM, resíduos históricos e erro de transferência. Exige fonte URL, domínio, metadados e parametrização integral; caso contrário retorna N/D. Não usar prior fictício para produção; fixtures de teste não são evidência científica.
Teste desse comportamento no commit efff34a2 com dados explicitamente sintéticos de contrato.
Recortes para teste disponíveis no artefato de conversa `Enform_Verde_KMZ_KML_3_areas_experimentais_Sinop_600_1000_1500ha.zip`: 600.08 ha e 1000.14 ha (zona Fazenda São Luiz) e 1500.33 ha (Embrapa Agrossilvipastoril), KMZ/KML com metadados e SHA256. São AOIs matematicamente delimitadas próximas a agricultura histórica; NÃO são talhões cadastrados nem áreas cultivadas 2026 comprovadas. Recortes 600/1000 ha se sobrepõem. Antes de testar produtividade, confirmar máscara de lavoura atual sobre o polígono.
Pendências: acesso a pixels SAR Sentinel-1 reais em Sinop, parâmetros experimentais numéricos cientificamente auditados por cultura, calibração transferível IFN serrapilheira, classificação atual das lavouras, instalação de solvers específicos e homologação modular independente. NUNCA declarar tudo operacional com saída numérica enquanto faltarem dados físicos — N/D auditável é correto. CI Word exige também alteração do binário `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx`, ainda não sincronizado automaticamente por atualização do prompt de conversa; atualizar antes de release definitiva.


## CHECKPOINT SINOP — 04/11/2026 — correções de painel e clima
- Relatório de Sinop recebido do usuário: área 399.087,54 ha, soja cartográfica MapBiomas 2025 179.859,77 ha, estimativa regional soja 3,82 t/ha (intervalo preditivo central 90% 3,14–4,32 t/ha), produção condicionada à máscara anual 686.588,89 t. Vigor SAR N/D (sem cenas/referências válidas) NÃO entrou na previsão; MAE histórica 266 kg/ha vs 286 da tendência não é erro de propriedade.
- `crop_report_consistency.py` commit 2eb3814b4 e `desktop_app.py` commit ab96065c: eliminam os placeholders `Produtividade provável: BLOQUEADA` e `Produção provável: INDISPONÍVEL` mesmo quando linhas estão dentro de relatório de texto multilinha, mas somente se cálculo posterior efetivamente produziu estimativa regional. Preservar N/D de SAR, idade, fitossanidade. A produção passa a ser cenário condicional com superfície cartográfica MapBiomas 2025 não validada como área da safra projetada. Sem contaminação do estoque de carbono nativo.
- `crop_monitoring_forecast.py` commit e09c0f60: nunca inferir vigor SAR para um KMZ agrícola 500–2000 ha usando a AOI mista inteira sem máscara vetorial validada da cultura; devolver N/D justificado.
- `agricultural_weather.py` commit 5cd1406a e `inmet_weather_client.py` commit 4b65a139: mostrar exatamente período diário NASA POWER (datas inicial/final), instante UTC da consulta e fonte. Médias não são aquisição Sentinel-1; não representar parâmetros meteorológicos como diagnóstico SAR.
- Testes de regressão novos: `tests/test_crop_report_consistency.py` commit 6e87c720; `tests/test_agricultural_weather_source_period.py` commit 65ffa638. Confirmar CI em SHA posterior, e integridade de todos relatórios carbono, solo 0–100, SAS/RVI/GLCM, vigor e safras. Teste de contrato sintético não equivale a observações reais.
- Documentação para download consolidada: `PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v61.md` e `Enform_Verde_Especificacao_Tecnica_Completa_v61_2026-11-04.docx`. Documento Word CANÔNICO do GitHub `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` ainda deve ser sincronizado via commit binário genuíno (não simular alteração apenas de metadados). O gate documental do CI deve continuar restritivo.
- Estado científico: não afirmar homologação independente de serrapilheira IFN, acesso SAR de Sinop ou calibração de vigor SAR×PAM×balanço hídrico enquanto não houver dados publicados e erros demonstráveis. Piloto experimental deve ser explicitamente identificado como tal.


## CHECKPOINT DOCUMENTAL EFETIVO — 04/11/2026
O workflow `Sync full Word specification from reviewed checkpoint` run 41890581153 concluiu com SUCESSO, registrando o commit `b534e072f6f22e84b05d5acda47c819732477a61` que atualizou o arquivo binário genuíno `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` sem perder as seções anteriores. O adendo de Sinop está em `docs/spec_updates/2026-11-04_v61_sinop_report.md`; a versão de download completa é `Enform_Verde_Especificacao_Tecnica_Completa_v61_2026-11-04.docx`. Manter os requisitos de CI e documentação sincronizados. Reexecutar testes e build Windows em SHA posterior de usuário, pois commits do próprio GITHUB_TOKEN não disparam workflows de forma normal. Homologação científica permanece bloqueada, independente do documento. 


## CHECKPOINT v62 — 04/11/2026 — sincronização concluída da revisão do Word
O arquivo Word canônico `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` recebeu o adendo v62 sobre a regressão de Sinop por meio do workflow `Sync full Word specification` run 41892021486 (sucesso), resultando no commit `61c3f07ac1b756732e0fdc0985b59e7107f171b8`. O último teste de unidade corrigiu expectativa inválida de vigor em AOI sem máscara; código continua exigindo máscara real de cultura e dados Sentinel-1 efetivamente processados. Testes de regressão e build Windows precisam passar no SHA final, sem aceitar artefatos de commits cancelados. Documentos locais completos para o usuário: prompt v62 e especificação técnica Word v62. CI não equivale a gate científico, que permanece independente.


## CHECKPOINT v65 — 04/11/2026 — painéis, incerteza e catálogo de serapilheira
Código publicado: `crop_monitoring_forecast.py` corrige shadowing do `timedelta` (commit 50276c7a); `desktop_app.py` discrimina 1500,33 ha da AOI em 72,92 ha nativos, 1241,75 ha de soja cartográfica MapBiomas 2025 e demais classes, sem extrapolação de cultura atual; `executive_carbon_report.py` diferencia cobertura, carbono parcial e cenários.
`carbon_compartments.py` adiciona transferência experimental de estoque seco de serapilheira para Floresta Estacional Sempre-Verde do norte MT, com grafias `Sempre-Verde`/`Sempre Verde`, sem IC95% de transferência e sem somar cenário ao estoque conhecido. `national_litter_inventory_registry.py` contém dez estudos regionais para contextos específicos de Caatinga, Cerrado e Mata Atlântica; nenhuma extrapolação nacional indiscriminada por bioma. IFN/SFB apenas espessura em cm permanece N/D para massa seca, com justificativa no painel, até ter gravimetria e propagação de incerteza. Os testes corrigidos preservam cobertura não confirmada e o rótulo `SEM IC95%`.
Documentação local completa distribuída: `PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v65.md`, `Enform_Verde_Especificacao_Tecnica_Completa_v65_2026-11-04.docx`, `Enform_Verde_Documentacao_Completa_v65.zip`. Adendo GitHub `docs/spec_updates/2026-11-04_v65_sinop_litter.md`. A atualização do DOCX canônico foi executada no workflow `41904967840` (sucesso) gerando commit `497395798c6b1f3fe1432bceb7455f4fde8f878b`. Código final deve ser conferido com CI e Windows EXE smoke test no MESMO SHA. O gate científico é independente e não deve ser declarado aprovado sem dados reais de validação.


## CHECKPOINT v66 — 04/11/2026 — alerta de cobertura desconhecida
- Regressão detectada no run 41905276990: a frase obrigatória `Cobertura nativa: N/D — cobertura não integralmente verificada` havia desaparecido do painel ao modernizar o resumo territorial. Corrigido no `executive_carbon_report.py` commit `fe5214fea99e7a034d4e0c96e7680e0efea1c914`. Teste de regressão `test_carbon_presentation_regression.py` deve passar no HEAD novo.
- Quando há qualquer área sem classe, reportar área nativa MAPEADA e área desconhecida separadamente; não calcular percentual de cobertura nativa como proporção definitiva, não converter desconhecido em 0% e não afirmar estoque total de carbono.
- Workflow de atualização Word completo configurado para o adendo `docs/spec_updates/2026-11-04_v66_cover_unknown_regression.md`, preservando histórico do DOCX. Esperar conclusão efetiva do workflow e CI e compilar o ZIP Windows do mesmo SHA para liberar piloto experimental.
- Documentos da conversa: `PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v66.md`, `Enform_Verde_Especificacao_Tecnica_Completa_v66_2026-11-04.docx`, `Enform_Verde_Documentacao_Completa_v66.zip`. Homologação independente não concluída; compilação e teste não a substituem.


## CHECKPOINT v67 — 04/11/2026 — cobertura não confirmada sem falso zero
- A regressão de apresentação foi corrigida no commit `360b8eb68a6a7213b14aa600dfc2aace2436cb7d`: o painel executivo conserva ambas as frases obrigatórias `Cobertura nativa: N/D — cobertura não integralmente verificada` e `Cobertura não confirmada: X ha — não equivale a zero de vegetação nativa; pode conter vegetação não mapeada`. O valor da área nativa MAPEADA é preservado e não representa o percentual confirmado de toda a AOI quando há lacunas.
- Run CI `41906378666` aprovou a suíte; run paralelo `41906388137` reprovou apenas controle documental porque os arquivos Word e prompt precisavam integrar a mesma alteração. O adendo `docs/spec_updates/2026-11-04_v67_cover_caveat_release.md` aciona sincronização do Word canônico.
- Novos documentos de download: `PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v67.md` e `Enform_Verde_Especificacao_Tecnica_Completa_v67_2026-11-04.docx`. Manter rastro v65 e v66. Exigir CI e EXE Windows do mesmo SHA, checksum e pacote ZIP antes de declarar nova versão compilada; homologação científica não é substituída por testes.


## CHECKPOINT v68 — 04/11/2026 — SAR atual prioritário e fontes internacionais
- Atualizações no código: `sar_crop_live_probe.py` consulta Sentinel-1 RTC recente, lê de forma auditável pixels VV/VH no interior da amostra agrícola cartográfica, sem atribuir automaticamente cultura; `crop_monitoring_forecast.py` integra a sondagem na auditoria e painel; `crop_vigor_auto.py` corrige assinatura TIFF binária e trata falhas Unicode/recuperação local; `desktop_app.py` alerta classe urbana >=50% de AOI; `international_crop_model_sources.py` lista WorldCereal, agroimpacts, WorldCereal RDM, Radiant Earth MLHub e EuroCropsML (este óptico-only).
- `land_use_sar.py` prioriza classificador SAR executável calibrado/validado e rotula MapBiomas ANUAL HISTÓRICO; sem classificador SAR executável permanece `N/D_SEM_MODELO_EXECUTAVEL_VALIDADO`. Não fabricar estimativas de acurácia brasileira a partir de modelos estrangeiros.
- Fonte científica revisada `docs/spec_updates/2026-11-04_v68_sar_global_catalog.md`; workflow canônico de especificação Word deve sincronizar este adendo, e controles de CI/testes devem passar no mesmo SHA final antes de compilar EXE.
- Critério de aceite operacional: aquisição Sentinel-1 atual com data e VV/VH, preditores harmonizados, modelo de culturas realmente treinado + pesos, licença, validação independente da região/cultura, matriz de confusão, intervalos e trilha de auditoria por polígono. Sondagem SAR sozinha não atinge esse critério.
- Arquivos de continuidade para usuário: `Enform_Verde_Prompt_Continuidade_v68.md`, `Enform_Verde_Especificacao_Tecnica_Completa_v68.docx`, `Enform_Verde_Documentos_v68.zip`.


## CHECKPOINT v69 — 04/11/2026 — correção da última regressão IBGE/SAR
- Código `land_use_sar.py` no commit `b5a142460ae11ae853e449dd6642832917ca5a1b`: preservada literalmente a cláusula `IBGE legenda_1 apenas nomeia fitofisionomia em interseção natural compatível` requisitada pelo teste `test_validated_sar_crop_precedes_mapbiomas_crop_layer`, mantendo classificador SAR de safra atual como fonte de primeira ordem, MapBiomas C11 de 2025 estritamente histórico, e falha segura N/D sem modelo SAR executável validado.
- O run de testes `41920055953` (SHA `d1a0e29a`) registrou 858 testes, apenas uma falha textual. Reexecutar suíte integral e EXE Windows após commits finais; build de SHA anterior NÃO libera a revisão nova.
- Adendo `docs/spec_updates/2026-11-04_v69_sar_priority_regression.md`; workflow canônico de Word sincroniza este conteúdo e deve terminar com sucesso.
- Modelos globais, observações Sentinel-1 recentes e tratamentos de erro TIFF da v68 preservados. A instalação efetiva de pesos e validação do classificador por cultura ainda é trabalho em aberto; não declarar essa funcionalidade plenamente operacional.
- Documentos atualizados deverão ser rotulados v69 e ter integridade DOCX/ZIP verificada. Cientificamente: homologação independente continua PENDENTE, separada da liberação de piloto experimental.


## CHECKPOINT V70 — 04/11/2026 — VEGETAÇÃO NATIVA SAR, ALTURA ESA BIOMASS + S1, AGB E COMPARTIMENTOS PROTEGIDOS
- A identificação de presença NATIVA deve usar classificador SAR real validado (Sentinel-1 VV/VH recente, estrutura, textura, padrões não geométricos e ESA Biomass quando efetivamente disponível). IBGE NÃO confirma cobertura atual: apenas NOMEIA as fitofisionomias. `name_native_from_ibge` prefere sobreposição exata e, quando não há, permite nome INFERIDO por proximidade <= 3 km em EPSG:6933, somente para a mesma formação SAR, indicando distância e proveniência. Nunca propagá-lo como rótulo de vegetação nativa para local sem classificação SAR. Correção de sintaxe foi incluída no commit eaa9e0f8166634f081a00e9f7b439824260d5c96.
- `native_biomass_sentinel1_height.py` extrai estatísticas radiométricas/espaciais de pixels VV/VH e mantém ESA Biomass P FP_FH__L2B como fonte direta de altura H100 (quando válida). Com S1 não é permitido derivar altura por correspondência não calibrada. Fusão residual só é liberada por coeficientes, definição de altura e holdout independente no domínio; se não, usar altura FH direta com incerteza e registrar S1 como covariável.
- `native_sar_structural_agb.py` define contrato AGB H SAR + área projetada de copa SAR (segmentação validada) + DAP médio e área basal média G de inventários microrregionais/regionais por fitofisionomia + equação efetivamente calibrada e erro independente. Bloquear AGB estrutural por falta de qualquer insumo: `AGB_ESTRUTURAL_N/D`. Não reinterpretar retroespalhamento VV/VH como área de copa sem segmentação, nem alegar que a nova rota já está operacional quando não existe tal modelo/segmentação.
- PROIBIÇÃO DE REGRESSÃO: biomassa viva de raízes continua pelo módulo `root_allometry_uncertainty.py`, alometria Cairns (1997) em domínio aplicável, incerteza condicional e rastreio. Carbono de solo permanece por `soil_pronasolos_zonal.py` e cinco horizontes brutos 0-5, 5-15, 15-30, 30-60, 60-100 cm Embrapa Solos/PronaSolos, interseção EXATA do polígono, alvo 0–100 cm, área realmente coberta e sem extrapolação de 0–30 cm. Ambos protegidos por `tests/test_sar_structural_nonregression_roots_soil.py`.
- Documentação técnica revisada: `docs/spec_updates/2026-11-04_v70_native_structure_s1_biomass.md`. Verificar workflow Word canônico, suite integral e build do mesmo SHA antes de liberar EXE Windows. Homologação científica independente permanece pendente até evidências observacionais reais.
- Disponibilizar `Enform_Verde_Especificacao_Tecnica_Completa_v70.docx`, `Enform_Verde_Prompt_Continuidade_v70.md` e `Enform_Verde_Documentos_v70.zip`, verificando que existam antes de enviar links.


## CHECKPOINT V71 — 04/11/2026 — SAR NATIVO E ESTOQUES POR COMPARTIMENTO
- Presença de vegetação nativa prioritariamente por classificador SAR validado; Sentinel-1 VV/VH textura, granularidade, rugosidade radiométrica e padrões espaciais como variáveis auxiliares reais. A mera textura não confirma origem natural. ESA BIOMASS banda P para altura direta FP_FH__L2B quando válida. IBGE legenda_1 só NOMEIA fitofisionomias após classificação SAR: interseção exata prioritária e distância <=3 km na mesma formação como denominação INFERIDA auditável, nunca cobertura nativa presumida.
- `native_biomass_sentinel1_height.py`: textura VV/VH, contraste espacial, média e variância; fusão residual entre altura BIOMASS FH e observações Sentinel-1 só com modelo/validação independentes dentro do domínio e erro registrado. Não derivar altura em metros diretamente de backscatter C.
- `native_sar_structural_agb.py`: AGB estrutural exige H SAR real, área de copa projetada derivada de pixels SAR e segmentação validada, DAP médio e área basal G provenientes de inventários microrregionais/regionais compatíveis e equação efetivamente ajustada com erro independente. Sem um desses, `AGB_ESTRUTURAL_N/D`; não regredir os produtos quantitativos SAR AGB previamente validados.
- Biomassa viva subterrânea continua via equações alométricas por fitofisionomia (Cairns para florestas upland onde compatível); solo segue Embrapa Solos/PronaSolos por interseção real com 5 horizontes 0–5,5–15,15–30,30–60,60–100 cm, apenas produto 0–100 cm, com incerteza e área coberta. 0–30 cm não substitui 0–100 cm.
- Serrapilheira continua via estoque SECO gravimétrico microrregional/regional da MESMA fitofisionomia: `national_litter_inventory_registry.inventory_litter_transfer_model` prevê tC/ha = Mg seco/ha × fC. Sem SD transferida validada externamente, não produzir IC95% nem somar ao estoque conhecido; com SD de inventário, n independente e SD de transferência validado, apresentar intervalo preditivo normal 90% CONDICIONAL, não IC95% homologado. IFN só espessura em cm não é estoque seco.
- Documentação canônica: `docs/spec_updates/2026-11-04_v71_litter_transfer_and_release.md` e workflow `sync-full-spec-word.yml`; testes novos `tests/test_native_sar_ibge_proximity_height_fusion.py`, `tests/test_sar_structural_nonregression_roots_soil.py`, `tests/test_litter_gravimetric_transfer_model.py`. Exigir CI completo, autoteste Windows em pasta limpa, ZIP no SHA atual antes de anunciar executável. Homologação científica independente N/D/reprovada até evidências observacionais externas.


## CHECKPOINT V72 — 04/11/2026 — PRIORIDADE P/X/L, ALTURA EXPERIMENTAL AUDITÁVEL E IDENTIFICAÇÃO NATIVA

### Hierarquia obrigatória de observação estrutural
1. Tentar primeiro ESA BIOMASS P-band FP_FH__L2B para altura H100 e produto P-band aplicável para AGB, lendo somente pixels válidos, unidade, métrica, incerteza do produto, data, cobertura e hash.
2. Integrar Sentinel-1 VV/VH recente como covariável de estrutura/textura e contexto temporal quando houver cenas válidas e compatibilidade espacial/temporal. VV/VH não é altura direta nem confirmação automática de origem nativa.
3. Usar X-band como alternativa seguinte somente quando a rota P-band ESA + observação SAR recente prioritária estiver indisponível/não tiver pixels válidos na AOI.
4. Usar L-band como última alternativa somente quando a rota prioritária e X-band estiverem indisponíveis. Não executar X/L em paralelo para substituir uma fonte P/S1 que esteja válida; conservar resultados candidatos na trilha de auditoria.
5. Não converter retroespalhamento bruto em metros com coeficientes arbitrários. A estimativa X/L experimental exige observações de campo pareadas, mesmo conceito de altura, footprint e época compatíveis, pelo menos cinco sítios espaciais independentes, fonte institucional/publicação, licença e SHA-256 do conjunto.

### Implementação X/L adicionada ao PR #50
- native_biomass_sentinel1_height.py: fit_experimental_xl_height_model ajusta regressão linear multivariada explícita usando somente preditores e medições de altura observadas; particiona por sítio com GroupKFold e publica RMSE, MAE, viés, R², quantis de resíduos OOF 5–95%, coeficientes, limites por preditor, sensor/banda, fitofisionomia, URL e SHA-256 da referência.
- predict_experimental_xl_height aplica o modelo apenas se P/Sentinel-1 prioritário estiver indisponível, se X estiver selecionado antes de L, se banda/fitofisionomia coincidirem e todos os preditores estiverem dentro do domínio observado. Retorna estimativa experimental e faixa preditiva empírica; sem erro OOF mensurável, domínio compatível ou proveniência, retorna N/D.
- tests/test_experimental_xl_height_model.py cobre os contratos com dados sintéticos. Esses testes verificam execução e bloqueios; NÃO demonstram desempenho ambiental real.
- O código foi enviado ao branch por commits e1ece3aa632d4983b9d53a06d10e7fef3ff18f6c e a037009d6567b8714fe48d8b4f2a1c8019ada960. No momento deste checkpoint, a suíte Dashboard dual - tests e o build Windows estão em execução no SHA novo. Confirmar CI e build novamente após esta atualização documental, pois commits posteriores podem gerar novos workflows. Não anunciar EXE pronto sem artifact ZIP, smoke test limpo e hash do mesmo SHA.

### Identificação de presença nativa: requisitos e limite atual
- A geometria de cobertura nativa precisa ser classificada por SAR recente treinado e avaliado com observações de campo independentes. Sentinel-1 deve fornecer preditores de retroespalhamento, textura/granulometria multiescala e contraste espacial; métricas de objetos devem quantificar regularidade geométrica (retangularidade, razão perímetro/área, orientação/repetição) como preditores auxiliares. "Rugosidade" derivada de SAR é proxy radiométrico/textural e jamais deve ser nomeada rugosidade física em metros sem medição correspondente.
- Padrões geométricos regulares podem reduzir a probabilidade de origem natural, mas sua ausência sozinha não prova vegetação nativa. Não usar MapBiomas histórico, legenda IBGE ou forma do polígono como rótulos verdadeiros de cobertura atual.
- No HEAD deste checkpoint, sondagem Sentinel-1 e extração de textura local existem; o contrato de classificador SAR supervisionado e a função de nomeação IBGE por interseção/proximidade existem. Entretanto, a sondagem não é classificação; não há evidência de pesos nacionais/regionais nativos executáveis nem de matriz de confusão independente para esta rota. Assim, não anunciar reconhecimento nativo plenamente operacional até integrar preditores multiescala/geométricos à inferência, demonstrar dados SAR recentes reais, referência independente e métricas por classe/fitofisionomia.
- IBGE legenda_1 apenas nomeia formação compatível após detecção SAR; sobreposição exata tem prioridade. Nome transferido por proximidade de até 3 km fica explicitamente "inferido", com distância registrada; não altera geometria SAR nem preenche pixels sem detecção.

### Estado de validação e próximos passos obrigatórios
1. Aguardar/inspecionar CI e build Windows no SHA documental final; corrigir regressões, não aceitar testes sintéticos como dado de validação.
2. Integrar a cadeia P → Sentinel-1 recente → X → L ao pipeline de carbono e à auditoria do aplicativo. O módulo X/L recém-adicionado ainda precisa consumir manifesto de observações reais e ser chamado pelo processamento da AOI, com estado por tentativa e razão de fallback registrados.
3. Executar pares reais independentes parcela–pixel por banda/fitofisionomia; publicar n, sítios, datas, definições de altura, domínio, licença, SHA-256, RMSE, MAE, viés, R² e intervalos de resíduos OOF. Holdout externo por região é necessário antes de rotular resultado como operacional validado.
4. Para detecção nativa, obter verdade de campo georreferenciada e independente, construir preditores SAR VV/VH em escalas declaradas e medidas de forma do objeto; comparar modelos dentro e fora da amostra espacialmente. Reportar sensibilidade, especificidade, precisão, matriz de confusão, incerteza de área e cobertura não classificada.
5. Preservar carbono nativo, raízes alométricas, solo Embrapa/PronaSolos 0–100 cm, necromassa e serapilheira sem regressão. AGB estrutural permanece N/D até existir altura, segmentação de copa, inventário compatível e modelo AGB com erro independente.
6. O gate científico independente continua pendente/reprovado até evidências observacionais. O gate de distribuição técnica e eventual piloto experimental são avaliados separadamente; não renomear N/D, CI aprovado ou ajuste sintético como homologação.


## v76 — mapeamento radar orbital atualizado (04/11/2026)

# REVISÃO v76 — TRIAGEM ORBITAL REAL SENTINEL-1 NA AOI — 04/11/2026
## Ocorrência informada: Fazenda Maria Eduarda, Sinop/MT
- Área da AOI no relatório fornecido: 1.459,91 ha. MapBiomas C11 2025: vegetação cartográfica 917,81 ha, soja 535,73 ha, outras lavouras 4,98 ha e outros usos 1,39 ha. Distribuição anual não comprova a ocupação de 2026/27.
- Erro visual: região fitoecológica IBGE exibida com percentual territorial foi interpretada como 100% de floresta estacional sempre viva. A interface agora distingue região FITOGEOGRÁFICA POTENCIAL de cobertura atual.
- Falha relatada: GDAL/UnicodeDecodeError na leitura de Sentinel-1, sem pixels VV/VH suficientes; a previsão histórica PAM/FAO é cenário regional, não monitoramento radar da safra atual.
## Hierarquia de implementação
- Classificação operacional potencialmente mais robusta: ESA WorldCereal no openEO/CDSE (Sentinel-1 + Sentinel-2), com autenticação, emprego de modelo por região e validação. Os mapas globais WorldCereal disponibilizados atualmente não provam culturas da safra atual nesta propriedade.
- Implementação automática nesta revisão: módulo recent_sar_landcover.py consulta cenas Sentinel-1 RTC da Microsoft Planetary Computer, obtém SAS temporário e lê recortes COG VV/VH no polígono. Exige pelo menos três cenas de mesma órbita relativa e direção ao longo de >=35 dias, última <=30 dias. Leitura fail-closed.
- Algoritmo experimental: VH_t,dB=10 log10(VH_t linear); L=mediana temporal VH; A=P90_t(VH)-P10_t(VH). Candidato lenhoso persistente se L>=P65 espacial(L) e A<=P35 espacial(A); candidato mudança sazonal se A>=P70 espacial(A) e L<P75 espacial(L). Demais pixels = indeterminados. Filtro de manchas <12 pixels.
- Exportações: raster GeoTIFF classes 1/2/3 e vetor GeoJSON quando volume manejável, áreas por interseção espacial projetada EPSG:6933, IDs/datas das cenas, órbita, cobertura de pixels, falhas sem expor SAS. Integração no relatório do painel de agricultura e na auditoria; não modifica a classificação cartográfica anual.
- Limite científico obrigatório: classe 1 NÃO comprova vegetação nativa; classe 2 NÃO comprova lavoura. Áreas candidatas NÃO são hectares validados, não alimentam diretamente o carbono ou produção de soja, não possuem IC95% nem matriz de confusão. Ausência de pixels retorna N/D.
- Radar C-band para detecção de padrões de cobertura não altera prioridade BIOMASS P e X, posteriormente L, nos fluxos apropriados de AGB/altura.
## Validação e distribuição
- Testes de contrato usando pixels sintéticos verificam classificação matemática e falha N/D; não são evidência orbital nem homologação científica.
- Validar execução AOI real Fazenda Maria Eduarda com cenas VV/VH auditáveis, melhorar caso de erro Unicode Windows e substituir índices heurísticos por modelo treinado e avaliação independente. WorldCereal sob demanda exige condições de serviço apropriadas.
- Nenhum executável anterior contém esta alteração. Somente distribuir EXE novo após teste completo, autoteste Windows, checksum e mesmo SHA.



# REVISÃO v77 — Fitofisionomia presente na propriedade (04/11/2026)
## Correções do painel e sintaxe
- Falha do CI v76: fechamento da string em ibge_area_summary_lines de desktop_app.py, corrigido na revisão v77.
- O painel Mapas e limites apresenta agora BIOMA e FITOFISIONOMIA PRESENTE NA PROPRIEDADE, com hectare e percentual da área total para cada classe nativa, a partir de native_carbon.strata (interseção de cobertura com o nome fitofisionômico IBGE).
- Antes do processamento de cobertura, a interface não exibe a área potencial do IBGE como presença atual; o diagnóstico IBGE potencial fica separado na auditoria.
- Exemplo do relatório da Fazenda Maria Eduarda: AOI 1.459,91 ha, área nativa mapeada no MapBiomas anual 917,81 ha (62,87%), não 100%. Somente declarar esta área para Floresta Estacional Sempre-Verde se todos os estratos nativos mapeados tiverem esse nome na interseção. Não é validação orbital da cobertura atual.
- Fórmula: área_fitofisionomia(ha) = soma áreas dos estratos nativos com mesma fitofisionomia; percentual_total = 100 * área_fitofisionomia / área_total_AOI.
- Fontes e qualidade explícitas: cartografia anual MapBiomas + nome IBGE, ou classificação SAR com nome IBGE. Nenhuma das duas equivale a confirmação independente em propriedade real. Falta de classificação resulta NÃO DETERMINADA, não 100% de floresta.
- Testes novos em tests/test_property_physiognomy_display.py verificam imóvel misto, 62,87%, fitofisionomias múltiplas, cobertura indeterminada e retorno N/D.
## Próximas verificações e versões
- Manter triagem SAR orbital experimental recente e alertas do classificador; não usar pixels candidatos para afirmar lavoura ou vegetação nativa sem modelo apropriado.
- Reexecutar toda a suíte e novo EXE em Windows no SHA final; build anterior do SHA 8839435 não contém estas mudanças.
- Gate científico independente continua reprovado até evidência observacional real. Modelos biomassa P/X/L continuam com hierarquia e limites originais.


# REVISÃO v78 — Teste de rótulo IBGE potencial coerente com v77 (04/11/2026)
- A rotina ibge_area_summary_lines foi corrigida no v77 para rotular a região fitoecológica IBGE como POTENCIAL e não como cobertura atual; o teste legado tests/test_ibge_area_summary.py ainda exigia a cadeia antiga. Agora valida o texto novo, sem reduzir a conferência de ha, porcentagens e erro de fonte.
- Permanecem inalterados: nome por IBGE, área nativa estratificada pela interseção da máscara de cobertura, percentual com base na AOI total, exibição do bioma e apresentação N/D para cobertura ausente.
- Exigir suíte completa, teste Windows de interface, processamento de uma AOI real e build de mesmo SHA; a homologação científica permanece separada e reprovada.
- Não declarar o erro UnicodeDecodeError/GDAL resolvido antes de um teste de aquisição de dados VV/VH real em Windows. Os candidatos SAR S1 são experimentais e não substituem classificadores treinados para lavouras/nativa.
