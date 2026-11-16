# Enform Verde v3.26.52-PRECAMPO-EXPERIMENTAL

## Correções e preservação de resultados

- No download ESA BIOMASS FH/AGB, o GeoTIFF direto é priorizado; depois de pixels raster válidos, o pacote ZIP não é baixado em duplicidade. O ZIP continua como contingência se o raster direto falhar.
- O smoke de canvas agora avalia o fundo de contingência que já está realmente visível enquanto a busca óptica ocorre em segundo plano. A evidência registra se o worker ainda estava pendente; a leitura de imagens CBERS/Sentinel-2 continua coberta pelo gate nacional independente.
- Mantidos os ganhos anteriores: máscaras SAR experimentais, guardas de domínio para rótulos de culturas, catálogo nacional de inventários, PAM, carbono por compartimento, trilha `run_id`/hash e painéis separados.

## Evidência real da Fazenda Maria Eduarda

- O KML fornecido foi lido localmente: 1.459,91 ha. O Sentinel-1 VV/VH produziu uma classificação anual experimental 2025/2026; 12 cenas recentes foram lidas, com a mais recente em 12/11/2026. A máscara anual não é uma classificação atual validada e não tem incerteza de área mensurada.
- Na passagem local de carbono para o payload do dashboard, a identidade da execução e o hash da AOI foram preservados. O carbono foi parcial, com 2 estratos e total conhecido de 90.822,16 tC; `complete=False`. O painel recebeu 7 classes semânticas em 1.442,46 ha; 17,45 ha permaneceram sem classificação semântica.
- A execução fria levou 292 s. Uma repetição com cache disponível não concluiu em 180 s; portanto esta revisão não declara ganho de tempo total. O teste local sem credencial ESA recebeu HTTP 401 nos ativos BIOMASS-FH; isso é bloqueio de autorização, não ausência de produto nem altura medida.

## Estado de liberação

Candidata pré-campo experimental. A suíte e o build Windows do novo SHA ainda precisam passar. O gate científico independente continua separado de funcionamento técnico; estimativas sem validação de campo permanecem experimentais e incerteza não mensurável permanece explícita.

## V88.99 — correção do smoke de canvas (16/11/2026)
A primeira CI da V88.98 passou o dashboard, integração SAR de Sinop/Tapajós, leitura live de pixels ESA BIOMASS FH e cobertura nacional óptica. O build Windows falhou no smoke visual por exigir contraste de satélite do fallback claro AOI/IBGE. O critério foi corrigido e ganhou regressão para fallback claro e contraprova de tela preta. Reexecutar CI e build no novo SHA; não houve EXE liberado na V88.98.

## V88.100 — diagnóstico adicional do smoke Tk (16/11/2026)
A V88.99 manteve timeout no canvas Windows apesar de a cobertura nacional óptica passar. O smoke agora eleva a janela e registra status do provedor, visibilidade/dimensões do widget, itens e luminância/fração visível, para separar falha de desenho da captura encoberta. A versão continua pré-campo; nenhum EXE liberável até novo smoke Windows.

## V88.101 — seleciona a página do mapa no smoke (16/11/2026)
A saída CBERS estava carregada, mas a página Mapas e limites permanecia oculta no smoke do Tk. O teste agora seleciona essa página e exige visibilidade do widget, além de pixels. Repetir CI completa; a V88.100 não gerou EXE liberável.


## V88.102 — correção da captura visual do canvas
O smoke Windows de V88.101 detectou canvas visível e imagem Sentinel-2, mas a captura reportou apenas 4,98% de pixels claros. V88.102 converte coordenadas Tk para pixels físicos do ImageGrab em telas escaladas, registra dimensões e anexa captura de diagnóstico em caso de falha. A causa DPI ainda é hipótese até confirmação pela nova CI. Doze testes focados passaram localmente; gates Windows pendentes.
