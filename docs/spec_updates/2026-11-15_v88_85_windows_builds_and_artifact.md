# V88.85 — builds Windows e artefato confirmados

## Build do código 3.26.44
- SHA do código: `f797c6320baa9713cbcba6c199cb05357f0c5de8`; revisão com documentação V88.83 em `df114b6b3424605397156a7079beb0b012b27297`.
- Runs Windows `43756793415` e `43756788960`: concluídos com sucesso. O `publish-release` foi ignorado; o pacote existe como artefato de Actions, sem publicação GitHub Release.
- Artefato `Enform-Verde-Windows-v3.26.44-PRECAMPO-EXPERIMENTAL`: 197.844.115 bytes; SHA-256 do ZIP `3ca6a9e41219a931668b40a701401b99714be8a1ea6a83a9fe87fb3a50e315a9`.
- Passaram: smoke óptico em biomas/extremos; prévia Sentinel-2 no KMZ público Tapajós; worker óptico/fallback IBGE até canvas Windows em Sinop; SAR live no Tapajós e amostras dos seis biomas; classificação IBGE do Tapajós; build e autoteste do EXE em cópia limpa.
- Não testados: KML privado integral da Fazenda Maria Eduarda e validação independente de campo. Resultado permanece pré-campo experimental; evidência amostral não garante toda coordenada ou data.

## Registro documental
Push de documentação confirmado no commit `ea002502375771ea5af668dc863ba56e517e77c6`. Na consulta, ainda não havia status de CI associado a esse commit documental. Reuso dos dados de solo por AOI e mosaicos WCS particionados/VRT estão implementados; redução do tempo total não foi quantificada em benchmark Windows.
