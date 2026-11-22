# Enform Verde v3.26.70-PRECAMPO-EXPERIMENTAL

A candidata mantém FH como fonte prioritária de altura, ESA CCI como rota de AGB secundária, e evidencia a busca de todas as fontes de inventários.

## Alterações

- O artefato live do SHA `3999058` confirmou FH no Tapajós (1.263 pixels florestais) e Sinop (333 pixels florestais; 4 savânicos) com produto, métrica H100, caminho e fonte ESA BIOMASS exibidos corretamente no payload do dashboard; CCI permaneceu rotulado como AGB.
- O resumo de rotas de altura no relatório live agora usa o registro aninhado `sar_height` e reporta em paralelo os campos de AGB, evitando altura sem métrica ou sem fonte no relatório executivo.
- A comparação de inventários registra as fontes pesquisadas, o registro harmonizado consultado, fontes agregadas cadastradas, correspondências compatíveis e fontes realmente utilizáveis. N/D por ausência de dados compatíveis não parece mais uma omissão de consulta. IFN, Embrapa, INPA, universidades e outras fontes permanecem selecionáveis conforme harmonização e compatibilidade.
- Nenhuma média publicada ou dado de inventário não harmonizado é extrapolado para a AOI ou somado ao CCI.

## Status

Candidata experimental/pré-campo, ainda não liberada. O dashboard integral e o handoff live passaram em SHA anterior (`3999058`); as novas correções de auditoria precisam passar na suíte, handoff, build e autoteste do EXE no SHA final. A prova de Tapajós não é validação da Fazenda Maria Eduarda. A homologação científica exige evidência independente de campo.
