# V88.84 — estado do CI, fundo óptico e otimização

## Evidência operacional
- A branch `patches-3.26.6` foi enviada pelo proprietário no commit documental `df114b6b3424605397156a7079beb0b012b27297`; código associado: `f797c6320baa9713cbcba6c199cb05357f0c5de8`.
- Testes SAR live/dashboard e prova ESA BIOMASS FH aprovados.
- Smoke Windows do worker óptico até o canvas aprovado em Sinop, aguardando estado terminal. Evidência somente para o cenário testado; não equivale a garantia nacional nem ao KML privado integral de Maria Eduarda.
- Na última consulta, builds Windows dos runs `43756793415` e `43756788960` ainda estavam em andamento. Executável não liberado até conclusão verde e conferência do artefato.

## Otimização já incluída em 3.26.44
Preparação de fontes numéricas de solo uma vez por AOI, com reuso entre estratos; mosaicos WCS divididos em tiles de 1024×1024 e lidos por VRT indexado, sem merge integral em memória. Isso reduz consultas repetidas e memória de pico, preservando resolução e cobertura. O tempo total ainda não tem benchmark comparável no Windows; nenhum percentual de aceleração é declarado.
