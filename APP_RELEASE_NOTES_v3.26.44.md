# Enform Verde v3.26.44-PRECAMPO-EXPERIMENTAL

## O que mudou

- O fluxo de carbono no Tapajós aceita a máscara ampla `Formação florestal` para a fonte gravimétrica local de serapilheira somente dentro da geocerca da fonte, sem afirmar subtipo IBGE não observado.
- A estimativa de raízes informa que Cairns estima raízes totais vivas + mortas. Sensibilidade à AGB pode ser exibida como parcial; não é IC95 nem incerteza total.
- As fontes numéricas PronaSolos são preparadas uma vez por AOI e reaproveitadas entre estratos.
- Mosaicos WCS grandes são divididos em tiles de 1024×1024 e apresentados por VRT indexado, sem merge integral em memória. Cache verifica VRT e tiles de origem.
- A mesma leitura fragmentada/indexada vale para limites oficiais de incerteza e camadas numéricas de fertilidade.

## Estado de validação

Esta é uma candidata experimental até a suíte integral, os workflows, o build/execução Windows do mesmo commit e a verificação do artefato terminarem. O KML privado integral da Fazenda Maria Eduarda e a validação científica independente de campo não são declarados como testados. Resultados que não tenham suporte continuam N/D; incertezas totais não mensuráveis não são substituídas por dispersão espacial.
