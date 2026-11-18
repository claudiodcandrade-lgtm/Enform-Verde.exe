# V88.153 — referência H100 de inventário para calibração ESA FH

Data: 18/11/2026  
Base: Enform Verde v3.26.71, branch `patches-3.26.6`

## Definição de altura

O produto ESA BIOMASS FH expressa H100: a média das alturas das 100 árvores mais altas por hectare. A função `derive_inventory_h100` deriva essa métrica de alturas totais por árvore nos microdados IFN, com área amostrada validada, bioma, fitofisionomia e microrregião. Registros de múltiplas hastes são consolidados por árvore; contagem insuficiente, ausência de área ou domínio incompleto bloqueiam o cálculo. A implementação não substitui nem corrige valores SAR diretamente.

## Uso em calibração

Para cada domínio produto × região × legenda_1 IBGE:

- parear H100 de inventário com pixels FH espacialmente compatíveis e da época compatível;
- reservar sítios externos completos para validação;
- avaliar viés, RMSE, MAE, R² e intervalos dos resíduos;
- só liberar modelo se a validação externa satisfizer limites previamente definidos;
- avaliar o requisito de missão de RMSE abaixo de 30% para árvores acima de 10 m como referência de qualidade, sem tratá-lo como validação local.

A calibragem AGB deve então usar FH validado e parâmetros horizontais médios de inventários microrregionais (G, DAP, densidade e distribuição diamétrica), tendo AGB de inventário como resposta. ESA CCI segue contingência exclusiva quando ausência de FH foi comprovada em rotas completas e sem erro.

## Estado

A função de derivação H100 e seus testes unitários foram adicionados. Isso torna executável a preparação da referência de altura, mas o fluxo ainda precisa construir pares reais IFN–FH por microrregião/fitofisionomia e validar os modelos no pipeline/executável. A funcionalidade nacional não pode ser rotulada como calibrada até esse gate terminar.
