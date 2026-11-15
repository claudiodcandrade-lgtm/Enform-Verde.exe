# Enform Verde v3.26.45-PRECAMPO-EXPERIMENTAL

## Correções do fluxo de vigor e safra

- A triagem SAR recente continua classificada como área candidata, sem identidade de cultura. Para o diagnóstico estrutural relativo, a máscara de pixels candidatos agora é dissolvida e amostrada em blocos espaciais sem sobreposição; pixels fragmentados deixam de ser contados como talhões de referência.
- O mínimo existente de seis blocos de referência e a janela de aquisição de até 30 dias são mantidos. A consulta de catálogo e o token MPC são reutilizados entre blocos; cada bloco continua verificando aquisição e pixels VV/VH reais.
- O painel diferencia assinatura estrutural SAR relativa de vigor agronômico validado. Nenhum vigor genérico é transferido a soja, café ou outra cultura sem máscara semântica atual correspondente.
- A previsão informa as entradas efetivas: produtividade do painel PAM e clima/balanço hídrico; cultura e área vêm da máscara SAR que originou o cenário. Para máscara SAR anual experimental, safra, transferência não quantificada e ausência de vigor atual são explicitadas.
- Removida do painel a atribuição fixa de produção ao MapBiomas 2025 quando o cenário usa área da máscara SAR experimental.

## Estado de validação

Esta candidata requer CI e build Windows no novo SHA. No ambiente local, `compileall` passou e a regressão de consistência do relatório passou (10 testes). Os testes geoespaciais focados não puderam ser executados localmente porque `geopandas` e `shapely` não estão instalados; o workflow com dependências geoespaciais precisa validar a nova amostragem. O KML privado integral da Fazenda Maria Eduarda e a validação independente de campo permanecem pendentes. Não homologada.

### Resultado adicional da suíte local

A descoberta integral encontrou 953 testes, 30 ignorados, 70 erros e 2 falhas. Os erros ocorreram sobretudo porque este ambiente não possui `geopandas`, `shapely`, `rasterio` e `requests`; o teste live Sentinel-1 também ficou sem `requests` para decodificar VV/VH. Uma das falhas é o guard de sincronização documental anterior à inclusão deste checkpoint. A outra é um teste live externo que precisa ser reexecutado em ambiente de CI com as dependências e rotas de rede corretas. Portanto, esta candidata ainda requer suíte integral, teste SAR live e build Windows aprovados no mesmo SHA.

### Leitura do carbono Tapajós

O relatório fornecido registra AGB pelo ESA CCI Biomass v7.0, produto L4 multissensor derivado de SAR. Não registra produto de altura, banda/cena, pixels válidos ou distribuição de alturas ligada à equação. Assim, altura SAR não está comprovada como entrada efetiva; o que foi usado foi AGB CCI derivada de sensoriamento remoto/SAR. Estoque total é parcial, com incerteza total não mensurável. A incerteza amostral de serapilheira não cobre transferência espacial.
