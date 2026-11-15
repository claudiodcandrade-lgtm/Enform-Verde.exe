# TESTE DE REGRESSÃO DE SINOP — ADENDO v62 (04/11/2026)
## Correção conclusiva do teste sem máscara agrícola
- Dashboard dual - tests run 41890828872: 844 testes, uma falha no cenário sintético test_crop_identifier_monitoring.MonitoringTests.test_monitoring_lines_use_vigor_and_forecast_and_attribution. O teste presumiu que um limite de AOI mista poderia servir de polígono específico de soja para calcular vigor.
- O código científico exige uma máscara geométrica realmente cartografada da cultura para analisar o vigor, inclusive em recortes de 500–2.000 ha. Sem máscara validada, N/D, e previsão regional PAM/FAO permanece experimental e sem condicionamento SAR.
- tests/test_crop_identifier_monitoring.py atualizado no commit b6c9fc25fd7ee8576b9c5155b7a8cb5675934ad9 para exigir N/D em AOI sem máscara; não enfraquecer crop_monitoring_forecast.py nem inventar leitura Sentinel-1 para satisfazer teste.
- Docs de download: PROMPT_CONTINUIDADE_ENFORM_VERDE_2026-11-04_v62.md e Enform_Verde_Especificacao_Tecnica_Completa_v62_2026-11-04.docx.
## Critérios de liberação mantidos
- O painel de Sinop elimina mensagens provisórias contraditórias somente se houver previsão realmente calculada; dados NASA POWER mostram período e origem; produção sobre MapBiomas 2025 é cenário condicional.
- Manter rastreabilidade do SAR (<=30 dias, UTC/UTC−3, VV/VH, RVI, textura GLCM, uniformidade) e incerteza científica.
- Corrigir a falha de teste não homologa modelos SAR ou serrapilheira sem dados reais. Confirmar CI e executável do mesmo SHA com checksum.
