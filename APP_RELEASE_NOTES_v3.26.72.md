# Enform Verde v3.26.72-PRECAMPO-EXPERIMENTAL

## Integração de inventários publicados e estrutura horizontal

- A comparação mult fonte de inventários passa a ser anexada ao resultado nativo para qualquer método primário de AGB, inclusive ESA BIOMASS FH; antes ficava restrita ao resultado ESA CCI.
- Relatório e Excel exibem agregados publicados de área basal, densidade e demais métricas horizontais por bioma e fitofisionomia como balizas regionais, separando fontes, regiões, unidades e incerteza publicada.
- Agregados publicados não são tratados como parcelas, pares pixel-campo ou validação independente, não são agrupados quando os desenhos não são comparáveis e não são somados ao estoque estimado.
- A limitação de saturação tropical da ESA CCI é mostrada na auditoria executiva quando a rota a reporta.
- Testes cobrem leitura mult fonte sem disponibilidade da base IFN, preservação de fontes separadas, distinção de erro técnico e uso de agregados como referência.

## Situação

Candidata experimental/pré-campo. Esta versão ainda depende da suíte completa, dos workflows Windows no SHA final, inclusive `--module-check`, `--visual-check` e `--network-check`, e do aceite integrado SAR→dashboard. Não declarar EXE liberado, calibração FH validada ou homologação científica antes desses gates. A calibração continua condicionada a pares de inventário compatíveis; estimativas e incertezas não sustentadas permanecem explicitamente N/D.
