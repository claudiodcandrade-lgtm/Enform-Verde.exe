# Enform Verde v3.26.35-PRECAMPO-EXPERIMENTAL

- Mantém CBERS‑4A/WFI (INPE) como provedor óptico prioritário e Sentinel‑2 L2A como alternativa.
- Lê COGs ópticos em quadrantes de até 512 × 512 pixels, limita cenas/tentativas remotas e exige pixels reais com cobertura mínima de 95% da AOI.
- Remove do build Windows o raster cartográfico nacional IBGE pesado. Se CBERS e Sentinel‑2 falharem, mantém o perímetro e apresenta diagnóstico; não substitui imagem orbital por cartografia. NASA/Esri seguem apenas como contexto visual inferior e identificado.
- Mantém o caráter pré-campo experimental. Suíte/Windows CI do SHA final, imagem na AOI integral de Fazenda Maria Eduarda até o dashboard e validação científica independente ainda não foram comprovadas.
