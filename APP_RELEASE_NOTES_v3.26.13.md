# Enform Verde 3.26.13-PRECAMPO-EXPERIMENTAL — Portfólio SAR de algoritmos científicos
Data de desenvolvimento: 2026-11-10.

## Acrescentado neste build
- `sar_algorithm_portfolio.py` implementa de fato 3 comparadores SAR (Random Forest com árvores balanceadas; SVM RBF; KNN padronizado), com validação cruzada por blocos/grupos espaciais de referência, matriz de confusão, macro-F1, acurácia balanceada e preservação de evidência da origem.
- `tests/test_sar_algorithm_portfolio.py` executa os três algoritmos em testes sintéticos de contrato e verifica rejeição de pseudo-rótulos IBGE/MapBiomas e dados com NaN; resultados sintéticos NÃO são evidência científica.
- `desktop_app.module_check()` verifica os classificadores também dentro do EXE congelado; status é `trainable only with independent reference samples` — não fingir pesos calibrados/inferência instalada.
- Mantidas as correções anteriores V87.84/V87.85: reaquisição de pixels SAR no Windows com modo HTTP/1.1 sem multipart na terceira tentativa; imagens CBERS-4A/S2; prevenção de recarga circular do mapa; mensagens de falha por provedor; interseção exata SAR × IBGE, fonte experimental preservada.
- Mantido o mecanismo ESA MAAP de troca do token e lembrete da validade estimada.

## Condições de aceitação / limitação
- Treinamento real e inferência espacial dos três algoritmos exigem amostras rotuladas independentes com datas, geografia compatível, feições SAR corretas e teste externo. A comparação de algoritmos em si não é classificador nacional validado.
- Os pesos brasileiros RF já existentes continuam sendo a rota efetiva da primeira geração; a seleção de RF/SVM/KNN não é ativada automaticamente sem as provas acima.
- O programa inteiro NÃO deve ser chamado de funcional na Fazenda Maria Eduarda até demonstrar pixel SAR VV/VH legível, imagem óptica visualizada, classificação nativa/agricultura e cálculos reais/modelados com N/D honesto.
- Homologação científica nacional é independente da compilação Windows.
