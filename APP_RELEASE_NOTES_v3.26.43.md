# Enform Verde v3.26.43-PRECAMPO-EXPERIMENTAL

## Correções nesta candidata

- Garante identidade única de execução e geometria entre uso do solo, carbono e payload SAR antes de entregar resultados à interface.
- Propaga explicitamente altura SAR e metadados por estrato ao painel, arquivo de auditoria e nova aba `Handoff SAR` do Excel.
- Desbloqueia cenário calibrado clima+PAM para soja/milho quando existe somente máscara SAR experimental anual, mantendo o resultado retrospectivo, sem vigor e condicional à safra da máscara.

## Estado de validação

A candidata não é homologada. Os testes focados passaram antes da sincronização final de documentos. A suíte completa, o build Windows, a leitura final no canvas e os ensaios de AOI devem passar no mesmo SHA antes de se divulgar executável como validado. A AOI privada integral da Fazenda Maria Eduarda não foi executada neste ambiente.
