# Tapajós ORNL 1552 — estrutura horizontal × H100 — modelo local v1

Fonte primária: Gonçalves et al. (2018), ORNL DAAC dataset 1552, DOI 10.3334/ORNLDAAC/1552. O CSV derivado em `data/tapajos_ornl1552_structure_v1.csv` foi recalculado a partir das 30 parcelas de 50×50 m. Para SF foi preservado DAP mínimo de 5 cm; para PF/SLF, 10 cm. H100 é a média das 25 árvores mais altas por parcela de 0,25 ha, exatamente equivalente à definição de 100 árvores/ha usada pelo produto ESA BIOMASS FH.

AGB de referência de parcela foi recalculada árvore a árvore com Chave et al. (2014): `0.0673*(rho*D^2*H)^0.976`, usando DAP (cm), altura total (m) e densidade da madeira (g cm-3). Portanto é referência alométrica, não biomassa destrutiva.

## Modelos de forma stand-level

- PF + SLF (16 parcelas): `AGB = 0.4092378415 × G × H100`; domínio observado G=15.921–31.267 m²/ha, H100=19.956–34.104 m, AGB=164.460–424.937 Mg/ha. Validação leave-spatial-block-out em 4 blocos internos do sítio: RMSE=26.650 Mg/ha, MAE=21.662, viés=-0.833, R²=0.879.
- SF (14 parcelas): `AGB = 0.2945481254 × G × H100`; domínio observado G=1.458–16.921 m²/ha, H100=8.436–28.708 m, AGB=4.365–138.237 Mg/ha. Validação leave-spatial-block-out em 3 blocos internos: RMSE=17.551 Mg/ha, MAE=11.515, viés=+5.496, R²=0.839.

Essas métricas medem capacidade de reproduzir a referência alométrica de campo em blocos espaciais dentro de Tapajós; não são validação independente do produto SAR FH. A rota operacional só pode usar o modelo quando a altura vem de `FP_FH__L2B`/H100 ou outro produto SAR explicitamente compatível e quando a AOI estiver dentro de um suporte de estrutura horizontal cadastrado. A incerteza do modelo deve permanecer separada do erro do produto de altura.

## Suportes de aceitação

- alta biomassa PF, parcelas 8–11: G médio 26.777591963 m²/ha, DP 2.996066381; AGB alométrica média 346.331 Mg/ha.
- baixa biomassa SF, parcelas 21–23: G médio 2.284585027 m²/ha, DP 1.268601582; AGB alométrica média 7.474 Mg/ha.

O uso desses suportes fora dos respectivos polígonos é proibido. A cobertura SAR FH precisa ser verificada em execução real antes de qualquer KML receber o status “garantido”.
