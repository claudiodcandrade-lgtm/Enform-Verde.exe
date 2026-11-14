# Checkpoint V88.56 — CI final

Data: 14/11/2026. Versão: `3.26.35-PRECAMPO-EXPERIMENTAL`. Código: `417e93141ec035d5bb414abb620224d490580927`; SHA documental/rebuild: `b4f7adcd4da162021df35187dabef7cc435fcd1e`.

- Dashboard CI #43635716670: 1.156 testes passaram; contrato rápido pré-campo #43635716654 e máscara SAR Sinop #43635716643 passaram.
- Build Windows #43635716635: EXE autotestado em pasta limpa; artefato 14130517119. SHA-256 ZIP `33b359aea8f60573b4ae39851b096e1616bb85d4b39654fdf03c0bfedd050aab`; EXE `a7bc32707554ff870fa470d83381172bb0427751d508e9b28263a1a214fc81f4`.
- CBERS-4A real: 11/11 janelas representativas, 100% cobertura reportada em cada; imagem visível no canvas em janela de Sinop. Sentinel-2 real Tapajós passou. SAR live Tapajós, INPE RTC amostral nos seis biomas e ESA BIOMASS FH real Sinop passaram.
- O KML integral da Fazenda Maria Eduarda até o dashboard continua sem execução comprovada. Gate de homologação científica reprovado por ausência de observações de campo independentes. Manter experimental, não homologado.

A auditoria arquitetural exaustiva ainda não foi concluída. A revisão V88.49 foi dirigida a cache, retries SAR e handoff; a investigação seguinte precisa percorrer os limites entre UI, workers, provedores, pipelines, modelos, persistência e painéis. Não declarar eliminadas todas as falhas recorrentes antes dessa revisão e de testes ponta a ponta por AOI.
