# ATUALIZAÇÃO V87.56 — 9 DE NOVEMBRO DE 2026 — CADEIA EXPERIMENTAL TESTADA PONTA A PONTA (3.26.8)
Política do proprietário: os cálculos e predições podem ser baseados em modelos matemáticos experimentais desde que cientificamente defensáveis; a acurácia será aferida depois com resultados reais de campo; o fundamental agora é testar os modelos.
## Mudanças
- Vigor: sem produto de altura, o tamanho usa o RVI = 4σVH/(σVV+σVH) (proxy de cobertura/biomassa; VV+VH acompanham a altura do milho, R² ≈ 0,8, Nasirzadehdizaji et al. 2019); saída rotulada size_basis = EXPERIMENTAL_PROXY_RVI. Altura e RVI nunca misturados na mesma comparação.
- Referência do vigor: talhões vizinhos da mesma cultura classificados pelo SAR em anel de 8 km (componentes ≥ 5 ha), mesma cena.
- Correção 1: busca de cenas Sentinel-1 do vigor com o retângulo do talhão (polígonos de pixel faziam a busca STAC falhar).
- Correção 2: dias ainda não publicados pelo NASA POWER são tratados como futuros e completados por anos análogos (a defasagem anulava a safra em curso).
- tools/test_models_aoi.py: cadeia SAR → uso da terra → culturas → vigor → previsão (painel PAM + balanço hídrico) para qualquer AOI; relatório JSON/texto; geometria privada não vai ao repositório.
## Resultado do teste — Sinop (AOI de demonstração em torno da fazenda, 09/11/2026)
- Uso da terra SAR (safra 2025/26, 30 cenas): área antrópica recente 748,9 ha; soja 506,6 ha; floresta nativa 419,7 ha; área cultivada sem cultura identificada 8,3 ha; outros < 3 ha.
- Soja: 112 talhões vizinhos de referência; vigor baixo (100%) na cena de 31/10/2026 (início da safra; comparação precoce, depende do estádio — conferir). Previsão: 3,45 t/ha (intervalo preditivo 90%: 2,59–3,71); 57,5 sc/ha; produção 1.749 t (1.312–1.878 t). RY hídrico mediano 0,98 (26 anos análogos). Água disponível do solo em fallback 1,0 mm/cm (serviço indisponível no teste).
## Limites
- Acurácia de vigor e previsão só será conhecida com colheitas e observações de campo; vigor no início da safra é pouco informativo; cultivares e datas de semeadura não são conhecidas.
