# REVISÃO V87.34 — ENFORM VERDE 3.26.4-PRECAMPO-EXPERIMENTAL
A contingência de estoque de carbono orgânico do solo por Identify foi restringida a uma amostra espacial reprodutível de pontos internos à interseção AOI × formação. O resultado só é calculado quando um único serviço oficial retorna os cinco horizontes em todos os pontos solicitados; sem essa completude, o estoque 0–100 cm permanece N/D. A interseção dos rasters brutos oficiais por pixel e polígono continua sendo a rota prioritária.

## Relato e incerteza
- O diagnóstico registra número de pontos, serviço escolhido e tentativas por serviço.
- A amostra descreve a distribuição do produto cartográfico dentro da formação; não quantifica erro do mapa, viés de transferência, validação de campo ou intervalo preditivo. O relatório expõe o tamanho amostral e a origem do dado para auditoria.
- Fertilidade do solo segue em painel próprio e não é confundida com o compartimento de carbono do solo.
- A sondagem do serviço em pontos de controle confirma respostas dos cinco horizontes nesses pontos, não acurácia nacional nem validação observacional independente.

## Estado de release
- Versão 3.26.4-PRECAMPO-EXPERIMENTAL: candidata técnica.
- A homologação científica independente permanece reprovada enquanto faltarem evidências observacionais independentes exigidas para biomas, compartimentos e funcionalidades.
- Resultados sem cobertura completa ou suporte científico permanecem N/D; não são preenchidos com dados sintéticos.


## UPDATE V87.34.1 — CI contract aligned with the soil service module (06/11/2026)
The Windows GUI contract was incorrectly searching for the primary PronaSolos endpoint inside desktop_app.py, although endpoint definitions intentionally live in pronasolos_identify.py. The assertion now reads that dedicated registry and checks the primary official endpoint plus candidate-service declaration. No service behavior or scientific acceptance threshold changed. Re-run Windows build, GUI contract, complete regression, package integrity and clean-folder EXE checks at the new source SHA. The independent scientific homologation gate remains failed pending real independent evidence; this contract fix does not satisfy it.
