# Enform Verde v3.26.76-PRECAMPO-EXPERIMENTAL

Data: 19/11/2026

## Correções incorporadas

- O aceite Tapajós no EXE falhava porque `structural_aggregate_evidence_v1.csv` era copiado somente para a pasta externa; PyInstaller agora o inclui no runtime interno e o gate verifica os agregados KM72/KM117.
- O relatório do aceite registra estado, diagnóstico, quantidade e fontes; falhas de leitura são explicitadas como erros técnicos.
- A sincronização Word agora atualiza a linha de versão e estado da capa, além do histórico, com testes de regressão.
- O gate pré-campo deixou de exigir frases da revisão histórica V87.1. Ele valida a versão atual do executável no DOCX e o checkpoint V88.166/3.26.76 no prompt v52 e na especificação de solo; v43 permanece histórico.

## Verificações e estado

- Testes locais focados após as correções: 17 aprovados; 191 módulos coletados.
- FH real ESA BIOMASS em Sinop e handoff SAR live em Sinop/Tapajós passaram em execução da candidata.
- Os gates de build Windows e regressão integral do SHA com a checagem documental atualizada foram reiniciados; autoteste EXE limpo Tapajós ainda precisa passar.
- Homologação científica independente permanece pendente e separada do funcionamento operacional. Esta versão continua candidata pré-campo experimental; nenhum EXE é liberado até os gates operacionais passarem no mesmo SHA.
