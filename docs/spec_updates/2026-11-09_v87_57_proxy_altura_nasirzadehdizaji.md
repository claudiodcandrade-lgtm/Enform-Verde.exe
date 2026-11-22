# ATUALIZAÇÃO V87.57 — 9 DE NOVEMBRO DE 2026 — PROXY DE ALTURA DE CULTURAS PELO ARTIGO NASIRZADEHDIZAJI ET AL. (2019) (3.26.8)
Fonte fornecida pelo proprietário: Nasirzadehdizaji, R.; Balik Sanli, F.; Abdikan, S.; Cakir, Z.; Sekertekin, A.; Ustuner, M. (2019). Sensitivity Analysis of Multi-Temporal Sentinel-1 SAR Parameters to Crop Height and Canopy Coverage. Applied Sciences 9(4):655, doi:10.3390/app9040655.
## O que o artigo traz (Tabela 3, R² com a altura medida em campo, Konya/Turquia, 2016)
- Milho, H < 150 cm: VH 0,80; VV 0,81; VV+VH 0,82 (maior); entropia 0,53; anisotropia −0,54; α −0,52; RVI 0,53. Milho, H > 150 cm: todos próximos de zero (saturação).
- Girassol: no máximo 0,31 (VH). Trigo, H < 53 cm: correlações negativas (VH −0,65; RVI −0,65); α 0,67.
- Não há coeficientes de regressão nem RMSE no texto ou nas figuras: não é possível converter retroespalhamento em metros a partir desse estudo.
## Uso no Enform Verde
$$ tamanho relativo = mediana[10·log10(σ⁰VV + σ⁰VH)] (γ⁰ RTC linear, multilook 3×3) no talhão
- Substitui o RVI como proxy de tamanho no vigor quando não há produto de altura (size_basis = EXPERIMENTAL_PROXY_VV+VH); comparado apenas com talhões vizinhos da mesma cultura e mesma cena (z robusto, tercis).
- Cada resultado traz a nota de evidência: forte para milho no início do ciclo; saturação acima de ~150 cm; sem evidência para soja e outras culturas de folha larga neste estudo.
- A conversão para metros continua dependente de coeficientes verificáveis (ex.: calibração local com medições de altura).
