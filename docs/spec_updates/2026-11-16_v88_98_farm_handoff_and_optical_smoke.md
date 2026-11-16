# V88.98 — Fazenda Maria Eduarda, handoff e mapa óptico

## Resultado técnico
- KML integral local válido: 1.459,91 ha; sem incorporar a geometria privada ao repositório.
- Sentinel-1 VV/VH lido em 12 cenas; máscara LEM+ anual 2025/2026 aplicada, experimental e sem incerteza de área mensurada.
- O fluxo local SAR → uso do solo → carbono parcial → dashboard preservou `analysis_run_id` e hash SHA-256 da AOI.
- Carbono: dois estratos; 90.822,16 tC conhecidos; `complete=False`. O painel recebeu 7 classes semânticas (1.442,46 ha) e manteve 17,45 ha sem classificação semântica.
- Tempo frio observado: 292 s. Repetição com cache não concluiu em 180 s; não há alegação de aceleração.
- Catálogo ESA encontrou produtos BIOMASS-FH; leitura de pixels sem token retornou HTTP 401. Não afirmar altura medida nem ausência de produto.

## Otimização e regressão
- Download do GeoTIFF direto FH/AGB encerra a seleção do ativo quando produz pixels; o ZIP completo fica reservado para contingência.
- Smoke do canvas inspeciona pixels visíveis do fallback ao mesmo tempo que o worker remoto continua. Registra se o worker estava pendente. O teste nacional CBERS/Sentinel-2 é independente.
- Executar suíte completa, coleta de testes, e build/smokes Windows no SHA final. A versão permanece pré-campo até esses gates e não é homologação científica.
