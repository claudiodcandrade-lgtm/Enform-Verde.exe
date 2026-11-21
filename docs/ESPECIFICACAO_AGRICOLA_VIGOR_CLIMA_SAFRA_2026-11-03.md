# Enform Verde — identificação de culturas, vigor, clima e previsão de safra (experimental)

Revisão 2026-11-03. Estado: **experimental**; nenhuma componente homologada.

## 1. Hierarquia de identificadores (`crop_model_priority.py`)
1. Instituições brasileiras (Embrapa — qualquer unidade —, ESALQ/USP, UFV, UFLA, INPE, UNICAMP, INPA e afins).
2. Savanas africanas, **CIRAD primeiro** (depois ISRA, INERA, ICRISAT etc.).
3. Qualquer região, publicação científica sólida.

Um modelo só é usado se: artefato executável com SHA-256 reconferido; manifesto de preditores; método documentado; acurácia independente com *n* (intervalo de Wilson 95%); escopo de validação declarado. Validação independente no Brasil → `validated_brazil`; só validação no domínio original → `experimental_transfer` (erro de transferência não medido). Nenhum utilizável → "Área cultivada — cultura não identificada". Candidatos de nível superior rejeitados são listados com o motivo.
Referências registradas nesta revisão: INPE (Oldoni et al., 2020, Sentinel-1 RF, OA ≈0,82 LEM-BA e ≈0,80 Campo Verde-MT, DOI 10.5194/isprs-archives-XLIII-B3-2020-1039-2020); base LEM INPE/PUC-Rio/Embrapa (DOI 10.5194/isprs-archives-XLII-1-387-2018); CIRAD JECAM (Jolivot et al., 2021, ESSD 13:5951, dados DOI 10.18167/DVN1/P7OLAP). São métodos/dados de referência — **nenhum peso treinado está instalado**.

## 2. Vigor em três classes (`crop_vigor.py`)
Fatores por talhão (Sentinel-1 VV/VH; mesma cultura, fase e janela):
- tamanho: mediana da altura (m) se houver produto de altura; senão mediana de $\mathrm{RVI}=4\sigma^0_{VH}/(\sigma^0_{VV}+\sigma^0_{VH})$;
- uniformidade: $U=1/(1+\mathrm{CV})$ do RVI multilook 3×3;
- rugosidade/textura: homogeneidade GLCM $\sum P(i,j)/(1+(i-j)^2)$ do VH (32 níveis, −30…−5 dB, 4 direções).

$z_k=(x_k-\mathrm{mediana}_{ref})/(1{,}4826\,\mathrm{MAD}_{ref})$; $V=\sum w_k z_k/\sum w_k$ (pesos iguais — hipótese a calibrar). Limites = tercis dos compostos das referências (leave-one-out). Probabilidades de classe por bootstrap espacial em blocos 5×5 do talhão e bootstrap das referências. Mínimos: 30 pixels, 6 talhões de referência.

## 3. Favorabilidade climática (`crop_climate_favorability.py`)
$D=\sum\max(0,K_c\,ET_0-P)$ (Hargreaves, FAO-56 eq. 52; $R_a$ eq. 21; $K_c$ médio FAO-56 Tab. 12); $H$ = dias com $T_{max}$ acima do limiar da cultura (limiares assumidos, configuráveis). $F=-(z_D+z_H)/\sqrt2$ contra a mesma janela de ≥ 8 safras de referência (NASA POWER). Classes por tercis. Safra em curso: dias futuros preenchidos pelos anos análogos → probabilidades.

## 4. Previsão (`crop_yield_scenario.py`, `crop_forecast_pipeline.py`)
$P_{AOI}=\sum_s A_s\,\hat y_s$. Para cada talhão: série PAM (SIDRA 5457, N9) da microrregião (malha IBGE 2021), tendência Theil–Sen, valores destendenciados projetados ao ano-safra; $\hat y=Q_{\tilde y}(q(v,c))$ com

| vigor \ clima | desfavorável | neutro | favorável |
|---|---|---|---|
| baixo | 0,00 (piso) | 0,15 | 0,30 |
| adequado | 0,35 | 0,50 | 0,60 (pouco acima da média) |
| alto | 0,70 | 0,85 | 1,00 (teto) |

Monte Carlo simultâneo: classe de vigor (por talhão), classe climática, bootstrap da tendência e erro de hindcast (compartilhados por microrregião-cultura), erro de transferência (se medido) e erro de área (se conhecido). O relatório lista as fontes NÃO quantificadas.

## 5. Evidência de hindcast (dados reais, 03/11/2026)
Leave-one-year-out, 2015–2024, componente clima+histórico (vigor histórico desconhecido = adequado). MAE (kg/ha) modelo × só tendência: Soja Alto Teles Pires-MT 237 × 270; Soja Sudoeste de Goiás 201 × 258; Soja Cascavel-PR 267 × 257; Soja Ijuí-RS 918 × 939; Milho Cascavel-PR 649 × 564; Milho Ijuí-RS 1.010 × 1.290. **O componente climático tem ganho pequeno e variável por região**; nas secas do RS o erro é alto porque, sem vigor observado, o modelo não desce abaixo do quantil 0,35. A capacidade de prever depende do vigor, que ainda requer validação de campo. Milho da PAM soma 1ª e 2ª safras: a janela climática deve refletir a safra dominante da microrregião.

## 6. Modelo principal a partir de 3/11/2026: painel calibrado (ver crop_panel_yield_model.py)
y_ut = a_u + b_u·t + β_g·RY_ut, RY por balanço hídrico FAO-56 + Ky FAO-33, AD Embrapa/PronaSolos, 5 pontos × 3 semeaduras, β por Frisch–Waugh. LOYO por ano: soja Sul +24%, milho Centro-Norte +19%, soja Centro-Norte +7%, milho Sul +2% sobre só-tendência. Vigor posiciona no terço dos erros históricos. A matriz da seção 4 vira contingência rotulada “cenário não calibrado”.
