# Enform Verde v3.26.26-PRECAMPO-EXPERIMENTAL

## Correção de leitura dos limites oficiais de incerteza do solo

- O leitor das capacidades WCS da Embrapa/PronaSolos agora remove somente referências numéricas de caractere proibidas pelo XML 1.0 antes do parsing.
- Referências XML válidas e demais bytes da resposta permanecem inalterados. A resposta original é hasheada e a quantidade de referências removidas fica registrada na proveniência.
- XML truncado ou estruturalmente inválido continua como erro técnico. Ausência de camada continua separada de erro de leitura.
- O estoque SOC 0–100 cm não é descartado se a leitura dos metadados de incerteza falhar; a incerteza permanece N/D até as camadas e grades passarem as validações existentes.
- Adicionado teste de regressão que verifica sanitização seletiva e descoberta de cobertura com referência XML inválida.

**Status:** pré-campo experimental; não homologado. Esta alteração não comprova incerteza oficial para a AOI nem validação científica independente.
