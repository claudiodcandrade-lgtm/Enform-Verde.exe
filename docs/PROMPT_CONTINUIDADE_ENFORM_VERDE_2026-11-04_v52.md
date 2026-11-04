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
