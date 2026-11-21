# V87.86 — Portfólio científico de algoritmos SAR, inferência experimental e integração em estágios (10/11/2026)

## Princípio obrigatório
O programa deve **calcular** sempre que existirem pixels SAR, parâmetros e modelos aplicáveis; modelos experimentais publicados são permitidos quando devidamente documentados, e a falta de validação não autoriza fabricar evidências. Preferir Embrapa, instituições brasileiras e amostras nacionais; complementar com estudos internacionais testados.

## Implementado no commit desta revisão
- Novo `sar_algorithm_portfolio.py`: três métodos efetivamente executáveis — Random Forest (300 árvores, classes balanceadas), SVM RBF (padronização + SVC) e KNN (padronização + k=5), todos de bibliotecas científicas consolidadas. Referências metodológicas de prioridade: Embrapa Agricultura Digital (classificação multitemporal Sentinel-1/2), trabalhos de pós-graduação da UnB em KNN/RF/SVM e família de métodos RF já implementados no projeto. Esses trabalhos fundamentam a escolha de famílias, mas não fornecem os pesos usados neste código.
- Entrada: matriz de feições SAR reais na mesma ordem/nomes, rótulos de **referência independente**, grupos de separação espacial e fonte/intervalo de amostragem. Proibidos `IBGE`, `MAPBIOMAS` e `SAR_MODEL_PREDICTIONS` como verdade-terreno para treino.
- Avaliação: GroupKFold com no mínimo três grupos espaciais, matriz de confusão, balanced accuracy, macro-F1 e comparação na mesma partição espacial; seleção apenas de modelo treinável e medido. Saídas `sar_algorithm_comparison.json` e `sar_portfolio_experimental.joblib` (arquivos gerados somente com dados fornecidos). Validação cruzada é interna e NÃO equivale a validação independente no campo; não relatar IC95% local nem acurácia nacional sem amostras externas.
- Inferência experimental executável: `predict_experimental_sar_portfolio()` somente aceita arquivo de modelo local confiável e feições SAR com esquema idêntico, devolvendo rótulos e probabilidade **não calibrada** claramente identificada.
- Testes: `tests/test_sar_algorithm_portfolio.py` verificam os três estimadores, esquema, resultados, rejeição de pseudo-rótulos e não uso de NaN; `desktop_app.module_check()` confirma importação de RF/SVM/KNN no EXE compilado e NÃO os apresenta como já validados.
- Nova identidade de build: **3.26.13-PRECAMPO-EXPERIMENTAL**, com notas `APP_RELEASE_NOTES_v3.26.13.md` para evitar reutilização do release 3.26.12.

## Arquitetura de implantação por níveis
Nível A: leitura real de pixels SAR/ópticos (metadata STAC + tentativas de decodificação + logging) e controles de cobertura, robustez Windows e cache, sem imagem de fundo IBGE se RGB real disponível.
Nível B: classificador RF brasileiro instalado `sar_brasil_rf_v2`, classificador temporal Sentinel-1 RTC por estação e triagem experimental não calibrada; separar diferenças estruturais e temporais de vegetação nativa/cultivo e declarar o caráter modelado.
Nível C: portfólio treinável RF/SVM/KNN e, somente quando houver pesos, dados e licença adequados, redes LSTM, CNN/Transformer e WorldCereal/Presto. **Esta etapa não declara novos Transformers, WorldCereal, DSSAT ou AquaCrop já executáveis.**
Nível D: geometria nativa SAR por interseção exata com `IBGE legenda_1` (somente nomenclatura), quantificação de área EPSG:6933, carbono por compartimento com inventários microrregionais, ESA BIOMASS/GEDI e PronaSolos 0–100 cm. Não computar carbono sobre cultivo nem tratar cobertura potencial IBGE como nativa atual.
Nível E: monitoramento de agricultura (cultura se identificada, caso contrário área cultivada), vigor, balanço hídrico de solo 0–100 cm com cenários, dados NASA POWER/INMET/CPTEC e histórico PAM por microrregião. DSSAT/AquaCrop como integrações futuras condicionadas à parametrização e licença de execução verificadas.

## Gates e pendências reais
- A falha do Windows real no KML Fazenda Maria Eduarda (1.459,91 ha) `UnicodeDecodeError` nas leituras Sentinel-1 RTC permanece prova pendente; estratégias HTTP/1.1 sem multipartes ainda precisam de ensaio efetivo no mesmo PC. Não declarar correção definitiva sem pixels e análises geradas.
- A fotografia óptica de CBERS-4A ou Sentinel-2 deve ser exibida e datada; o ensaio automático de quadrante próximo a Sinop não substitui o KML completo.
- Homologação científica nacional permanece independente da aprovação de unit tests, build ou auto-check. Testes sintéticos são contratos de software, nunca campo.
- Preservar histórico das revisões V87.82 a V87.85 e manter a especificação Word sincronizada.
