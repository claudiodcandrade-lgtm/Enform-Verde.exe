# V88.152 — base oficial de inventários e calibração FH/CCI

Data: 18/11/2026  
Base: Enform Verde v3.26.71, branch `patches-3.26.6`

## Fonte oficial incorporada

O Painel de Biomassa e Carbono do Serviço Florestal Brasileiro disponibiliza AGB derivada dos levantamentos IFN. Os metadados oficiais descrevem UA e coordenadas, fitotipologia, área por tipologia, equação, média de AGB por hectare e variância. O SFB também publica a tabela de equações e os fatores de raízes. Os dados abrangem levantamentos de 2011–2024 e foram atualizados em 2026. O build agora materializa e registra hashes da tabela de biomassa e do catálogo de equações; a base crua IFN/IBGE permanece integrada.

A tipologia do painel tem ressalva de ser inferida com fontes secundárias. A compatibilidade final deve ser conferida com o cruzamento espacial do IFN para legenda_1 IBGE; discrepâncias não podem ser silenciosamente aceitas. AGB do painel é uma estimativa alométrica oficial, não biomassa destrutiva observada. Sua variância e equação têm de acompanhar o pareamento.

## Fluxo acordado para altura e AGB

1. Derivar H100 de campo das medições DAP/altura IFN, com expansão pelo desenho amostral e área real da tipologia.
2. Parear H100 com pixels ESA FH espacial e temporalmente compatíveis, estratificados por produto, fitofisionomia IBGE e região. Reservar sítios externos; publicar viés, RMSE, MAE e R² da altura.
3. Derivar médias horizontais regionais de G, DAP, número de árvores e distribuição diamétrica com pesos e áreas do inventário; priorizar microrregião e nunca contar subparcelas como sítios independentes.
4. Ajustar/validar AGB por pares de inventário com FH e estrutura horizontal compatíveis, com grupos espaciais e incerteza que combine AGB do painel, amostragem, erro de altura e transferência.
5. Se existir FH utilizável, gerar só a estimativa FH + inventário. Só com ausência real e auditada de FH, usar CCI calibrado contra AGB IFN pareado em suporte/época. Nunca publicar CCI bruto como segunda estimativa.
6. Estimar raízes por equação alométrica adequada. `valor_r` do painel SFB é fator raiz/parte aérea e não deve ser rotulado como equação.

## Limite de status

O código nesta alteração materializa os dados oficiais e conserva sua proveniência; isso disponibiliza a matéria-prima que faltava. Ainda é necessário gerar o pareamento real com FH/CCI por microrregião/fitofisionomia, ajustar os modelos e validar em sítios não usados no ajuste antes de declarar calibração operacional. Não apresentar coeficientes fictícios nem divulgar o bloqueio anterior como falta definitiva de fontes; a fonte já foi encontrada e está sendo integrada.
