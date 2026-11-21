# Atualização da especificação V87.48 — 09/11/2026

Esta nota complementa `docs/ESPECIFICACAO_TECNICA_COMPLETA.docx` e registra a revisão óptica e TLS incorporada à versão 3.26.6.

## Ordem do fundo óptico

CBERS-4A/WFI do INPE é a fonte prioritária. Sentinel-2 Earth Search e Planetary Computer são contingências posteriores; VIIRS é contexto visual adicional e não comprova que as rotas orbitais tenham funcionado. Cada resultado precisa de pixels COG reais, fonte, data, cobertura da AOI e diagnóstico. O mapa IBGE não é imagem de satélite e não pode ocultar falha óptica.

## TLS no Windows

As rotas CBERS/Sentinel-2 usam `tls_setup.gdal_env()`. A política mantém a validação TLS ativa. No Windows, GDAL usa a confiança nativa do Schannel e não recebe bundles PEM mesclados acima do limite de 1 MB. Não usar `GDAL_HTTP_UNSAFESSL=YES`, `verify=False` ou bypass de certificado.

A falha observada no workflow Windows 42554440241 foi `schannel: CA file exceeds max size of 1048576 bytes` ao abrir o COG da prévia Sentinel-2; etapas posteriores de cobertura óptica, SAR live, EXE e checksum foram ignoradas. A correção está no commit de código `0383178fed1d5cd16ce0b1bd0024dc3a153838d5`; workflows iniciados antes da sincronização dos documentos não validam o SHA final.

## Solo e estimativas experimentais

Carbono do solo 0–100 cm e fertilidade usam exclusivamente dados específicos brasileiros Embrapa Solos/PronaSolos, compatíveis com atributo, profundidade, unidade e interseção espacial. SoilGrids e outros dados estrangeiros são inaplicáveis: não usar para preencher lacunas, calibrar, comparar, validar ou produzir sensibilidade desses resultados. Sem cobertura nacional adequada, apresentar N/D e a lacuna.

Quando não houver modelo validado aplicável, estimativas experimentais podem ser operacionais se o método for cientificamente defensável, os dados forem compatíveis e a incerteza puder ser quantificada e apresentada. Distinguir intervalo preditivo, envelope de cenário e dispersão; não inventar erro nem chamar concordância cartográfica de validação de campo.

## Estado de liberação

A PR #51 permanece draft e a PR #50 deve ser preservada. A homologação científica nacional continua sendo um gate independente. Não distribuir como versão final até o SHA que contém código e documentos passar o build Windows, testes live necessários, empacotamento, autoteste do EXE em pasta limpa e verificação do hash. Não declarar cobertura orbital garantida para qualquer AOI do país sem evidência que sustente essa afirmação.
