# V88.99 — correção do gate visual do fallback óptico (16/11/2026)

## Causa da falha V88.98
- No Windows, o smoke nacional de fontes ópticas passou; o smoke do canvas chegou ao fallback AOI/IBGE, mas terminou em timeout. O gate aplicava à cartografia clara o mesmo desvio-padrão mínimo exigido para imagens ópticas. Um fundo claro quase uniforme pode estar visível e ainda ter baixo contraste.
- A falha era do critério do smoke, não evidência de que pixels SAR não foram lidos nem de que a camada de fundo era preta.

## Correção e proteção contra regressão
- Para fallback cartográfico, exigir pixels com luminância p99 ≥20, fração visível ≥0,15 e itens no canvas; não exigir contraste de satélite.
- Imagens CBERS/Sentinel-2 continuam exigindo luminância, cobertura, contraste, dimensões e item de imagem. Tela preta não satisfaz os critérios de fallback.
- Incluído teste de fundo claro de baixo contraste e contraprova de canvas preto. Repetir CI Windows completo e smokes no SHA final; a falha V88.98 não pode ser contada como aprovação.

## Situação de release
- O handoff SAR→carbono parcial→dashboard para Sinop/Tapajós passou; a suíte completa do dashboard passou; a prova ESA BIOMASS FH real passou; a disponibilidade nacional de fontes ópticas passou.
- O build Windows do SHA V88.98 parou no smoke visual por esse falso negativo; não produziu EXE liberável. O pacote continua pré-campo até a nova CI Windows e o executável final passarem.
- A classificação agrícola continua anual experimental; carbono permanece parcial. O caso privado não comprova validação de campo.
