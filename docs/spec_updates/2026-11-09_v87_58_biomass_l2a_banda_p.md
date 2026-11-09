# ATUALIZAÇÃO V87.58 — 9 DE NOVEMBRO DE 2026 — PRIORIDADE BANDA P (ESA BIOMASS) PARA ALTURA DE FORMAÇÕES NATIVAS (3.26.8)
Pedido do proprietário: priorizar modelos com bandas X e P da missão ESA Biomass.
## Fatos verificados (ESA, 09/11/2026)
- A missão ESA BIOMASS opera somente em banda P (lançada em 29/04/2025; operação científica desde 26/01/2026). Banda X pertence a outras missões (TanDEM-X/TerraSAR-X, COSMO-SkyMed, ICEYE).
- Produtos: L2A Forest Height (FP_FH__L2A, altura do dossel superior + camada de qualidade, 200 m, por pilha de imagens) aberto desde 30/06/2026; L2B FH e AGB (fase tomográfica) só em maio/2027 e restritos antes disso. Acesso via ESA MAAP com conta EO Sign In (token offline).
- Correção: o programa buscava apenas L2B, por isso a altura banda P nunca era obtida. Agora a ordem é L2B operacional → L2B IOC → L2A operacional → L2A IOC; do L2A só o GeoTIFF FH é usado (qualidade, quick-looks, KML e XML excluídos).
- Busca real sobre Sinop: FP_FH__L2A de 20/08/2026 e 19/09/2026 cobrem a AOI (download requer token MAAP).
## Hierarquia de altura para formações nativas
1. BIOMASS banda P (FH L2B, depois L2A); 2. banda L (ALOS-2/PALSAR, já existente); 3. banda X (TanDEM-X) quando o usuário fornecer o produto; 4. banda C (Sentinel-1) apenas como estrutura auxiliar.
## Culturas agrícolas
- Banda P não é indicada para altura de culturas (comprimento de onda de ~70 cm atravessa dosséis baixos); culturas seguem com banda C (Sentinel-1, proxy VV+VH) e banda X quando houver dado disponível.
