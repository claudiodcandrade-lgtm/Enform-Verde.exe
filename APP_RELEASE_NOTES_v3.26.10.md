# Enform Verde 3.26.10-PRECAMPO-EXPERIMENTAL — 10/11/2026

## Natureza do lançamento

Piloto **experimental**, para gerar evidências e permitir confronto posterior com campo. A liberação técnica do ZIP exige todos os testes obrigatórios e o autoteste do executável no mesmo SHA. Não é homologação científica nacional.

## Implementações

- Dados ESA BIOMASS: MAAP STAC GET/bbox, paginação e recuperação de produtos `FP_FH__L2A` e `FP_FH__L2B`. FH fornece altura superior do dossel, não AGB automaticamente. Evidência independente: run 42813753319 — 2304 pixels, 18,28 m na janela Sinop, não no KML completo.
- Base óptica: CBERS-4A e Sentinel-2; teste anterior de worker até canvas Tk em Sinop aprovado. Conferir novamente a build de 3.26.10.
- Sentinel-1 RTC VV/VH: janelas COG limitadas e composição temporal 12 meses com cenas pareadas; modelo RF rastreável pelo SHA e `SAR_EXPERIMENTAL_MODELO`. Máscaras atuais não são inferidas automaticamente de assinaturas da safra passada.
- Polígonos de classes e áreas exclusivas por EPSG:6933. Ensaio real de Sinop em 1084,73 ha (NÃO a Fazenda Maria Eduarda inteira) produziu GeoJSON, classificador RF e observações de 30 cenas na safra 2025/26. Evidência run 42825630140.
- Monitoramento de culturas: a área experimental da safra completa pode fundamentar cenário condicional de produtividade. É registrada como `SAR_EXPERIMENTAL_ANUAL_NAO_ATUAL` e não como área/plantio verificado no mês corrente. Vigor datado exige cena SAR recente e máscara de cultura que não seja mero mapa cartográfico.
- Água no solo: `soil_water_balance_spatial.py`, pedotransferência Saxton–Rawls, FAO-56 depleção de água radicular, cenários seco/central/úmido, déficit, excedente, tendência de 7 dias. Valores são **MODELADOS**, não umidade medida, nem IC95.
- Previsão: `crop_forecast_pipeline.py` expõe sensibilidade de rendimento por cenários hídricos a partir do painel PAM calibrado e FAO-33/FAO-56, com ressalva de extrapolação. Sem dados hidráulicos, solo N/D ou hipótese de contingência explicitada.

## Pendências objetivas (sem mascarar resultados)

- Área completa e limites reais do KML `FAZENDA_MARIA_EDUARDA.kml` não foram disponibilizados ao teste integrado; não usar bbox de Sinop como equivalente.
- A janela histórica 2025/26 do RF não é visão atual novembro/2026. Necessária segmentação SAR contemporânea de até 30 dias para confirmar a cobertura de cada cultura e atualização real do vigor.
- Validação independente espacial e temporal e matriz hídrico-produtividade por cultura/solo/bioma permanecem experimentais; índices de qualidade de treino não são IC95 de área/predição nacional.
- Associações pedológicas Embrapa precisam receber atributos hidráulicos por horizonte e profundidade para cenários por unidade do solo; não inventar laboratório.
- Não usar fallback IBGE/MapBiomas como se fosse classificação orbital atual.
