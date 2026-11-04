# PREVISÃO REGIONAL DE SOJA E AUDITORIA DE SINOP — CORREÇÕES 04/11/2026
## Problema corrigido no painel executivo
- O relatório de Sinop mantinha simultaneamente Produtividade provável: BLOQUEADA, Produção provável: INDISPONÍVEL e uma previsão PAM/FAO posterior de 3,82 t/ha com produção cenário de 686.588,89 t.
- A função crop_report_consistency.remove_superseded_yield_placeholders percorre linhas de cada bloco textual e remove somente os placeholders vencidos quando há projeção regional efetivamente calculada. Mantém N/D de vigor, idade e fitossanidade quando sem evidência.
- desktop_app.py adota a correção, mantendo a estética executiva original e carbono nativo separado.
## Natureza científica da previsão e da máscara
- A soja mapeada cobre 179.859,77 ha conforme mapa anual MapBiomas 2025. Não comprova plantio de soja nem área efetivamente colhida na safra 2026/2027.
- A produção agregada sobre essa área é cenário condicional experimental, não produção confirmada; o intervalo preditivo PAM/FAO de 90% cobre somente os componentes representados no modelo, não erro cartográfico, manejo ou transferência sem validação.
- Vigor SAR N/D indica que as medidas por radar não condicionaram essa previsão. O MAE histórico de 266 kg/ha contra 286 kg/ha para a tendência não é acurácia em propriedade real.
## Restrições do monitoramento remoto
- AOI mista de 500–2.000 ha, sem polígono de cultura comprovado, não pode ser tratada como talhão homogêneo para SAR; vigor N/D justificado.
- Sentinel-1 precisa ter pixels reais VV/VH com aquisição nos últimos 30 dias, IDs e datas UTC e UTC−3, cobertura e incerteza. Vigor por RVI/porte aparente, uniformidade e textura VH/GLCM com bootstrap espacial.
## Cronologia meteorológica e transparência
- agricultural_weather.summarize_weather mantém datas início/fim, origem, URL e horário UTC da consulta NASA POWER. inmet_weather_client.weather_executive_lines mostra o período explícito da série de temperatura/precipitação/GDD.
- Dados NASA POWER em grade no centroide e dados CPTEC de previsão têm escalas e períodos distintos; não somar ou ponderar sem validação.
## Testes e governança
- tests/test_crop_report_consistency.py cobre textos multilinha e preservação de campos N/D; tests/test_agricultural_weather_source_period.py assegura fonte e período da consulta.
- Testes de contrato não comprovam observação orbital; gate científico independente permanece condicionado a evidências e modelos experimentais precisam de calibração real para liberação definitiva.
- A atualização do Word é aditiva e preserva a especificação histórica. Compilação EXE, hashes e ZIP devem corresponder ao último SHA, não a uma versão anterior.
