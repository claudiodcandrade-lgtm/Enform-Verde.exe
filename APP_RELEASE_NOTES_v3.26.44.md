# Enform Verde v3.26.44-PRECAMPO-EXPERIMENTAL

## O que mudou

- O fluxo de carbono no Tapajós aceita a máscara ampla `Formação florestal` para a fonte gravimétrica local de serapilheira somente dentro da geocerca da fonte, sem afirmar subtipo IBGE não observado.
- A estimativa de raízes informa que Cairns estima raízes totais vivas + mortas. Sensibilidade à AGB pode ser exibida como parcial; não é IC95 nem incerteza total.
- As fontes numéricas PronaSolos são preparadas uma vez por AOI e reaproveitadas entre estratos.
- Mosaicos WCS grandes são divididos em tiles de 1024×1024 e apresentados por VRT indexado, sem merge integral em memória. Cache verifica VRT e tiles de origem.
- A mesma leitura fragmentada/indexada vale para limites oficiais de incerteza e camadas numéricas de fertilidade.

## Estado de validação

Esta é uma candidata experimental até a suíte integral, os workflows, o build/execução Windows do mesmo commit e a verificação do artefato terminarem. O KML privado integral da Fazenda Maria Eduarda e a validação científica independente de campo não são declarados como testados. Resultados que não tenham suporte continuam N/D; incertezas totais não mensuráveis não são substituídas por dispersão espacial.


## Atualização V88.84 — 15/11/2026

O push da branch `patches-3.26.6` foi confirmado no commit documental `df114b6b3424605397156a7079beb0b012b27297`, associado ao código `f797c6320baa9713cbcba6c199cb05357f0c5de8`. Os testes SAR live/dashboard, a prova real ESA BIOMASS FH e o smoke Windows do worker óptico até o canvas em Sinop passaram. Os builds Windows completos `43756793415` e `43756788960` ainda estavam em andamento na última consulta; a liberação do executável depende de conclusão verde e verificação do artefato.

A otimização de solo já está incluída: reuso de dados preparados por AOI e leitura de mosaicos em tiles/VRT indexado. Reduz trabalho repetido e memória de pico; o tempo total ainda não foi quantificado por benchmark comparável.


## Atualização V88.85 — builds Windows concluídos

Os builds Windows do código `3.26.44-PRECAMPO-EXPERIMENTAL` terminaram com sucesso nos runs `43756793415` e `43756788960`. O artefato `Enform-Verde-Windows-v3.26.44-PRECAMPO-EXPERIMENTAL` tem 197.844.115 bytes; SHA-256 do ZIP: `3ca6a9e41219a931668b40a701401b99714be8a1ea6a83a9fe87fb3a50e315a9`. O workflow não publicou GitHub Release (`publish-release` ignorado); o arquivo está disponível como artefato de Actions. Smokes ópticos, canvas Windows, SAR live e autoteste do EXE passaram nos cenários indicados, sem representar teste do KML privado integral da Fazenda Maria Eduarda ou homologação científica de campo. O ganho de tempo da otimização ainda não foi quantificado.
