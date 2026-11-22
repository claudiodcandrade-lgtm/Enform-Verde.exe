# V87.85 — confirmação experimental de vegetação nativa por pixels SAR e nomeação IBGE por interseção — 10/11/2026

## Regra obrigatória
1. Consultar cenas SAR Sentinel-1 RTC VV/VH (e ESA BIOMASS para altura/estrutura quando disponível). Leitura efetiva de pixels e características temporais/estruturais precedem classificação.
2. Identificar máscara de vegetação nativa e cobertura cultivada por classificador SAR executável. Padrões de estabilidade, retroespalhamento, sazonalidade e estrutura são preditores; **não equivalem sozinhos a validação local ou nacional**. O modelo LEM+ RF instalado pode produzir classes experimentais e deve preservar as incertezas/métricas de treino e o status NÃO VALIDADO LOCALMENTE.
3. Intersectar **somente os polígonos SAR de vegetação nativa** com as geometrias oficiais de regiões fitoecológicas IBGE `legenda_1` em EPSG:6933. Subdividir as áreas conforme interseções exatas. Nomear os pedaços por `legenda_1`; manter fonte `SAR_EXPERIMENTAL_MODELO+IBGE` quando classificação SAR for experimental. Não criar vegetação nativa pela camada potencial IBGE, nem por proximidade sem autorização.
4. Crops/agricultura/pastagens do SAR permanecem não nativos; nenhuma área cultivada pode herdar nome nativo do IBGE. Todas as áreas resultantes devem fechar a área da AOI e reportar lacunas não classificadas. A fitofisionomia potencial da AOI pode ser apresentada separadamente, sempre **não confirmada**.
5. Alimentar `native_carbon.summarize_native_carbon` apenas com a vegetação nativa identificada por SAR (incluindo experimental devidamente rotulada). Estimar cada compartimento por dados/modelos adequados por estrato, sem transformar dados experimentais em observações validadas e sem inventar estoques quando não existirem densidades compatíveis. A identificação SAR é precondição operacional, mas não substitui inventário/validação dos estoques.
6. Relatório agrícola usa os polígonos não nativos classificados a partir de SAR; cultura específica somente quando identificador sustentado, caso contrário `Área cultivada (cultura N/D)`, sem fabricar vigor ou produtividade.
7. Correções de transporte COG Windows introduzidas na V87.84 (tentativa HTTP/1.1 sem multipart) permanecem **hipótese técnica não comprovada no KML completo**. A leitura de cenas assinadas com `UnicodeDecodeError` deve ser testada no Windows do usuário; até então, a recuperação não é declarada definitiva.
8. Testes `tests/test_native_sar_ibge_intersection_experimental.py` cobrem cenários sintéticos: interseção exata floresta SAR e IBGE, não nomeação de agricultura, ausência de inferência por IBGE isolado e ausência de preenchimento por proximidade. Exigir ainda CI Windows aprovada e piloto real Fazenda Maria Eduarda 1.459,91 ha para homologar fluxo operacional.

## Versão, proveniência e documentação
- Aplicação experimental Windows `3.26.12-PRECAMPO-EXPERIMENTAL`; observações/validação nacional pendentes.
- Preservar classificação SAR `SAR_EXPERIMENTAL_MODELO` ao atribuir nome IBGE. Fonte `SAR_EXPERIMENTAL_MODELO+IBGE` é resultado de interseção e não altera o caráter experimental da máscara.
- Atualização imediata do prompt canônico, prompt complementar, especificação de solo e documento Word completo `V87.85`. Preservar histórico de checkpoints anteriores.

## Revisão de regressão Windows após primeira tentativa de build (V87.85.1)
- O build 3.26.12 anterior falhou **antes do executável** por contratos antigos: test_sar_landcover_lemplus esperava o nome genérico Formação savânica, quando a regra nova exige Savana Arborizada nomeada por interseção e fonte SAR_EXPERIMENTAL_MODELO+IBGE. O contrato GUI e tests/test_v82_national_ci_contract.py ainda exigiam a legenda antiga e não a distinção SAR atual × IBGE potencial.
- Corrigidos os testes para exigir a nova regra sem alterar indevidamente os resultados de classificação; registrado assert de fechamento da área AOI, identidade experimental e exclusão de soja da vegetação nativa.
- Gate PyInstaller continua obrigatoriamente bloqueado até concluir GUI contract, suite total, EXE + leitura de pixels ópticos/SAR e checksums no mesmo SHA. Não alegar êxito do KML real só com aprovação da CI.
