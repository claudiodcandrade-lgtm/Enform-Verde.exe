# Enform Verde v3.26.35-PRECAMPO-EXPERIMENTAL

- Mantém CBERS‑4A/WFI (INPE) como provedor óptico prioritário e Sentinel‑2 L2A como alternativa.
- Lê COGs ópticos em quadrantes de até 512 × 512 pixels, limita cenas/tentativas remotas e exige pixels reais com cobertura mínima de 95% da AOI.
- Remove do build Windows o raster cartográfico nacional IBGE pesado. Se CBERS e Sentinel‑2 falharem, mantém o perímetro e apresenta diagnóstico; não substitui imagem orbital por cartografia. NASA/Esri seguem apenas como contexto visual inferior e identificado.
- Mantém o caráter pré-campo experimental. Suíte/Windows CI do SHA final, imagem na AOI integral de Fazenda Maria Eduarda até o dashboard e validação científica independente ainda não foram comprovadas.


Build Windows CI #43633560279 passou, incluindo autoteste do executável em pasta limpa. Artefato Actions: https://github.com/claudiodcandrade-lgtm/Enform-Verde.exe/actions/runs/43633560279/artifacts/14129607134. SHA-256 EXE: `ac9b68b0139f4a1694e5545d98bc3eb8902c17cee4aa771caf0b040330ad6f44`.


## V88.56 — confirmação final de CI

Build Windows #43635716635 passou: artefato Actions 14130517119; SHA-256 ZIP `33b359aea8f60573b4ae39851b096e1616bb85d4b39654fdf03c0bfedd050aab`; SHA-256 EXE `a7bc32707554ff870fa470d83381172bb0427751d508e9b28263a1a214fc81f4`. Dashboard: 1.156 testes aprovados. Continua pré-campo experimental, não homologado; KML integral da Fazenda Maria Eduarda até o dashboard e aferição de campo seguem pendentes.

A revisão de código V88.49 foi direcionada a cache/retentativas SAR e handoff; não foi exaustiva de todos os módulos. CI verde não prova eliminação universal de falhas recorrentes.

## V88.57 — revisão arquitetural preliminar (14/11/2026)

A inspeção estática identificou cinco riscos ainda pendentes: processamento síncrono no thread Tk quando SAR local é usado; possível repetição da aquisição/modelagem SAR na contingência por fitofisionomia; teste de handoff baseado em fixture, sem executar o core real; cobertura de contingência IFN restrita à Amazônia/FESV em MT; e contrato de estados agregados que precisa distinguir erro, ausência confirmada, etapa não executada e sucesso. Ver `AUDITORIA_ARQUITETURAL_PRELIMINAR_V88_57.md`.

No commit documental `6097f9cb9bf07b2738d4eb6c8f7805b0ef983a5f`, dashboard #43638982932, contrato pré-campo #43638982863 e máscara SAR Sinop #43638982929 passaram. Build Windows #43638982885 ainda estava em execução na consulta. O KML integral da Fazenda Maria Eduarda até o dashboard não foi executado; a homologação científica independente permanece reprovada por falta de medições de campo. Não homologado.
