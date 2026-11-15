# ATUALIZAÇÃO V87.40 — 8 DE NOVEMBRO DE 2026 — SERAPILHEIRA REGIONAL COM ERRO DE TRANSFERÊNCIA QUANTIFICADO (3.26.6)
Problema: a serapilheira nunca entrava no total — valores publicados isolados sem variância nem erro de transferência eram mantidos fora (NÃO ESTIMADO). Pedido do usuário: estimativa defensável a partir de inventários microrregionais/regionais por fitofisionomia, parcelas IFN e estudos gravimétricos.
## Modelo (regional_litter_hierarchy.py)
$$ ln L_sítio ~ N(μ_g, τ²);  μ̂_g = média de ln(médias dos sítios da mesma fitofisionomia e região, k_g)
$$ τ̂ = DP de ln(médias) entre k_F sítios florestais brasileiros independentes (heterogeneidade agregada, conservadora)
$$ ln L* = μ̂_g + t_{k_F−1} · τ̂ · √(1 + 1/k_g);   C = L* · f_C,  f_C ~ U(0,42; 0,50);  Monte Carlo 20.000, semente fixa
- Somente estoque gravimétrico da camada de serapilheira (nunca deposição anual, espessura IFN sem modelo massa/espessura validado, necromassa lenhosa ou MapBiomas). Um valor por sítio independente; o erro amostral interno ao sítio é pequeno frente a τ e não é somado de novo.
## Dados verificados para FESV (norte de MT)
- Silva, Lobo, Bleich & Sanches (2009), Acta Amazonica 39(3):591–600 — Fazenda Maracaí, ~50 km de Sinop (11°24′43″S, 55°19′26″W): 21 quadrados de 0,0625 m² por mês, mai/2004–abr/2005; médias mensais 3,53–6,49 Mg/ha; média anual 5,121 Mg/ha; CV temporal 16,6%.
- Volpato (2024), UFRRJ, Tabela 8 — FESV Submontana, 24 parcelas: 8,70 Mg/ha (± não definido, não usado).
- τ̂ = 0,396 (10 sítios florestais: os 2 acima + 8 do registro nacional). Resultado: L* geométrico 6,68 Mg/ha; C = 3,08 tC/ha; intervalo preditivo 90% 1,27–7,48 tC/ha; DP 2,28 tC/ha. include_in_total = True (experimental), origem INVENTARIO_REGIONAL_HIERARQUICO; aplicado apenas a estratos nativos FESV confirmados, dentro do envelope 59–52°W, 15–9°S.
## Extensão prevista
- Mesma hierarquia para outras fitofisionomias assim que houver ≥1 sítio gravimétrico local verificado; IFN só entra com modelo massa/espessura calibrado na mesma fitofisionomia.
