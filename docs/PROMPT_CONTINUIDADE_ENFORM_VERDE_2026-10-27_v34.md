# PROMPT DE CONTINUIDADE — ENFORM VERDE — v34
Atualizado em 27/10/2026. Fonte: prompt anexado v30, histórico narrado v31-v33 e checagem direta do GitHub em 27/10/2026.

## INSTRUÇÃO CENTRAL
Prosseguir no repositório claudiodcandrade-lgtm/Enform-Verde.exe, branch `feature/agricultural-identification-native-carbon`, PR #50 (rascunho, não mesclar sem autorização). Preservar integralmente as rotas comprovadas de estoque de carbono nativo, sem regressões. Não confundir build aprovado com validação científica da previsão agrícola. Trabalhar a partir do commit real da branch, nunca presumir que alterações locais não enviadas estão incluídas no EXE.

## CHECKPOINT VERIFICADO — WINDOWS 3.25.1
- HEAD PR #50: `c442c142e489800325ef231f170d95a0080f1d55`.
- Workflow **Build Enform Verde Windows**, run #665, ID `40553874472`, **completed/success**: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40553874472
- Workflow dashboard dual, run #229, ID `40553874464`, **completed/success**.
- Artefato exato: `Enform-Verde-Windows-v3.25.1-CLIMA-DINAMICO`, artifact ID `12756553409`, tamanho `522563739` bytes, digest oficial `sha256:61e107fd8ee1d9a2f31c2868c15ac644c5c47ba758a465a18ebbbf1ec5b77f28`, expiração 26/11/2026.
- Link para o artefato via workflow: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/40553874472/artifacts/12756553409
- A execução anterior #664 falhou, mas é de outro SHA `255429aac796a3bb7e808e589c55beb53a7782f1`; não usar a falha antiga para reprovar o HEAD atual.
- A compilação Windows foi aprovada nos testes automatizados, incluindo os gates de carbono/painel e execução do EXE em pasta limpa conforme registro da sessão precedente. Validação final em PC de destino ainda precisa ser diferenciada da validação CI.
- Existe também o artefato de dados PAM `12757250203` do mesmo run (verificar dados, cobertura, escala e licenças), e o diagnóstico de altura Tapajós `12757035731` (não inferir resultado positivo apenas pela existência).

## REGRAS OPERACIONAIS DA ABA AGRÍCOLA
1. Primeiro detectar áreas cultivadas e só depois distinguir, quando houver evidência SAR/classificador validado, lavouras de soja, milho, cana-de-açúcar, sorgo, arroz, feijão, café, citros/laranja e algodão. Na dúvida mostrar **“áreas cultivadas”**. Para pastagem, floresta plantada e gêneros de silvicultura, exigir evidência própria; não confundir com vegetação nativa.
2. A mensagem exata quando não houver cultivo identificado na aba agrícola é **“sem cultivos detectados”**. Não exibir simultaneamente cultura identificada e mensagem negativa. Reconhecer rótulos iniciados por **“Lavoura de …”** na lógica de detecção, não apenas na apresentação.
3. Mostrar **clima dinâmico** na aba agrícola inclusive quando não houver cultivo detectado; não vincular consulta de clima à presença de lavoura. Preservar o rótulo do botão meteorológico compatível com o contrato existente e mencionar clima dinâmico.
4. Painel executivo simples, separado da Auditoria técnica. NASA POWER prioritária para histórico diário auditável, CPTEC/INPE para previsão futura compatível; usar INMET/BDMEP quando acessível, sem depender de Climatempo contratado. Não misturar períodos ou variáveis em média ponderada sem verificação de vieses e pesos.
5. Registrar fonte por classe, área/ha, tipo de inferência, confiança e abstenção. Ao informar cena SAR, preservar aquisição original UTC e conversão explícita “horário de aquisição (UTC -3)” e “horário de aquisição (UTC)”; distinguir ausência verdadeira de metadado de erro de coleta.

## CARBONO NATIVO — PROIBIÇÃO DE REGRESSÃO
- Biomas: Amazônia, Cerrado, Caatinga, Mata Atlântica e Pantanal.
- Preferir BIOMASS P, SAR L e SAR X onde adequados; C quando justificável; fallback ESA CCI v7 devidamente descrito. Nunca rotular média regional/inventário como estimativa SAR pixel a pixel.
- Fitofisionomias por IBGE legenda_1 e interseção espacial, com MapBiomas auxiliar documentado, cálculo por classe.
- AGB, raízes, necromassa, serrapilheira e solo: seguir hierarquia de inventários microrregionais, SFB/IFN, Embrapa, universidades, SINAFLOR/PNLA, Embrapa Solos, sem inventar precisão. Para necromassa e serrapilheira usar observações/inventários adequados e incerteza de transferência, não equação alométrica indiscriminada para serapilheira.
- Preservar tC e tCO2e, formato brasileiro de números, mapa IBGE offline, geometrias, arquivos SHP/GPKG/GeoJSON/KML/KMZ, layout da marca, relatório de proveniência.
- Gates obrigatórios: Tapajós (altura SAR somente quando efetiva), Santo Ambrósio/167 parcelas para AGB de floresta, Cerrado/DF, Pantanal e testes reais SAR/IBGE. Não reduzir testes para liberar binário.

## PREVISÃO DE SAFRA — AINDA NÃO CONFIRMADA OPERACIONAL
- Nunca confundir modelo codificado/treinável, referências científicas, PAM histórica, cenas STAC ou leitura de bytes COG com modelo por cultura efetivamente treinado, validado e integrado.
- A série oficial PAM/SIDRA de 2015–2024 contém 133.920 células para oito produtos, 558 microrregiões e três variáveis; conferir o artefato de dados do run atual. Rendimento por produto/ano/MI e censura/supressão têm de ser auditáveis. Laranja não equivale a todos os citros.
- Rota de acesso SAR: Microsoft Planetary Computer Sentinel-1 RTC (STAC e SAS temporário), ou Copernicus/ASF autorizados; provar leitura de pixels VV/VH, geometria/CRS/unidades, órbita, data/hora e cobertura. HTTP 206 para bytes isolados não equivale à extração radiométrica validada. Falhas HTTP 504 externas devem ter retry/backoff limitado e tratamento de indisponibilidade sem modificar o cálculo de carbono.
- Para identificar cultura, obter máscaras SAR com rótulos verdadeiramente independentes, validação por região/ano/talhão e matriz de confusão. MapBiomas não é validação independente se usado no treinamento.
- Construir painel MI × safra, relacionar somente pixels realmente classificados como cultura e safras PAM compatíveis. Incorporar clima e baseline histórico defasado sem vazamento; comparar baseline MI, MI+clima e MI+clima+SAR; holdout espacial e temporal e ablação do ganho de SAR.
- Critérios de atualidade da imagem por cultura/fase/região e timestamps de aquisição reais, não data de ingestão. Anomalia SAR fitossanitária é inespecífica e não diagnostica doença ou praga.
- Reportar RMSE, MAE, viés, métricas por região/safra, intervalos preditivos calibrados e cobertura em holdout independente com incerteza por blocos. Se domínio, licença, escala, máscara, previsão de clima, calibração ou cobertura falhar, mostrar **“previsão indisponível”** e motivo; não imprimir safra fictícia.

## EXECUÇÃO SEGUINTE — VERIFICAR E CONCLUIR
1. Conferir árvore do SHA do PR e resultados completos do run 665, inclusive logs de gates; identificar configurações que possam ter passado por contingência e testar em Windows físico quando possível.
2. Baixar o artefato oficial `12756553409`, conferir tamanho, digest, integridade ZIP e existência do EXE e mapas offline; não oferecer ZIP de código-fonte como executável. Se o container não aceitar binários grandes, usar URL do artefato verificado no GitHub sem alegar inspeção local.
3. Testar interface agrícola com (i) lavoura identificada, (ii) área cultivada sem cultura resolvida, (iii) nenhuma lavoura e mensagem exata, sempre com clima dinâmico; confirmar fonte e ausência de rótulos contraditórios.
4. Reexecutar testes dos cinco biomas e compartimentos de carbono, tC/tCO2e, mapa offline e numerais pt-BR; comparar com golden outputs de versões aprovadas.
5. Implementar de fato o pipeline SAR × PAM × clima e validação por cultura; sem evidência não habilitar previsões. Priorizar soja/milho quando amostras independentes/licenças estiverem disponíveis, não extrapolar às demais culturas.
6. Atualizar este prompt após cada alteração com SHA, run, status, testes, artefato e lacunas, mantendo separação clara entre operacional, experimental e indisponível.

## CRITÉRIO DE ACEITAÇÃO
Distribuição 3.25.1 é aceitável como **build Windows aprovado em CI**, não como comprovação da conclusão de toda a pesquisa agrícola. Toda alegação nova deve ter evidência rastreável por commit, teste, dados e domínio de validação. Nenhuma alteração pode regredir o carbono nativo.
