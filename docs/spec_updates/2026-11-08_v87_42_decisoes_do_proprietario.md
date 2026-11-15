# ATUALIZAÇÃO V87.42 — 8 DE NOVEMBRO DE 2026 — DECISÕES DO PROPRIETÁRIO INCORPORADAS (3.26.6)
- 1A — Previsão de safra: modelo de painel calibrado (y = a_u + b_u·t + β·RY), vigor posiciona no terço dos erros históricos (piso → teto).
- 2B — Classificador SAR: qualquer acurácia MEDIDA aceita como experimental; n independente e IC95% Wilson obrigatórios; sem limiar mínimo (MIN_VALIDATION = 1; aviso de amostra pequena abaixo de 30).
- 3C — PAM microrregional 2015–2024 mantida.
- 4B — Altura: modelo SAR publicado aceito como experimental (validation_tier = experimental_published) com RMSE e n publicados e incerteza da altura ≥ RMSE; erro de transferência declarado não validado. Ainda sem conjunto de coeficientes verificável instalado.
- 5B — Sem vigor, previsão só clima + histórico PAM, rotulada “PREVISÃO SEM VIGOR”, intervalo de todos os erros históricos; máscara SAR da cultura obrigatória.
- 6A — Serapilheira hierárquica (média ln dos sítios + t·τ·√(1+1/k), τ = 0,396) para todas as fitofisionomias florestais com ≥ 1 estudo gravimétrico verificado; não florestais seguem cenário até ≥ 3 sítios.
$$ σ_total² = (σ_BA + σ_BS + σ_NA + σ_NS)² + σ_Serap² + σ_Solo²
- 7B — Incerteza total com correlação declarada (fórmula acima, ρ = 1 no grupo da biomassa, 0 nos demais); N/D se algum compartimento não tiver incerteza; nunca soma simples.
- 8A — Unidades radar sem nome apenas no mapa e no painel, sem carbono nem safra; prioridade máxima: sempre haver classificador SAR (roteiro B6).
