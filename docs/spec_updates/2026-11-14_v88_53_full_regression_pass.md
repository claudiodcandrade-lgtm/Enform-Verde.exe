# V88.53 — regressão completa com dependências Windows instaladas

- No SHA `15e0c0bc0742901d63892497f79c9c61148e11c4`, o runner Windows instalou os requisitos desktop/geoespaciais e passou a compilação completa de módulos, guard de coleta e suíte integral: 1.155 testes aprovados.
- A execução anterior de 1.155 testes teve uma falha no guard do DOCX, causada pela especificação técnica estar na versão 3.26.33 enquanto o código já estava em 3.26.34. A especificação Word e os documentos canônicos foram sincronizados; a regressão completa subsequente passou.
- O contrato rápido pré-campo, a máscara semântica SAR experimental de Sinop e a prova ESA BIOMASS FH real em Sinop passaram no SHA. Isso não comprova estimativa completa de carbono no KML real nem funcionamento ponta a ponta de Fazenda Maria Eduarda até o dashboard.
- O build Windows ainda está executando o preparo da base cartográfica IBGE offline; EXE e artefato não podem ser declarados até conclusão verde.
- A homologação científica independente permanece reprovada por falta de observações de campo independentes. Manter `3.26.34-PRECAMPO-EXPERIMENTAL`, não homologado; não chamar amostras de cobertura nacional.
