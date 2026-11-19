# Enform Verde v3.26.76-PRECAMPO-EXPERIMENTAL

Data: 18/11/2026

## Correção do pacote de inventários

- A investigação do aceite Tapajós no EXE encontrou o CSV harmonizado `structural_aggregate_evidence_v1.csv` na cópia externa do pacote, mas ausente no diretório interno do runtime congelado, onde o módulo de consulta o procura.
- O comando PyInstaller agora inclui esse arquivo em `data/` dentro do runtime `_internal`; a etapa Windows verifica a presença do arquivo e das referências Santos et al. KM72 e KM117 antes do aceite.
- O relatório de aceite registra estado, diagnóstico, quantidade e fontes da evidência de inventários. Falha técnica de leitura passa a ser exposta como erro técnico explícito.

## Correções da documentação e estado dos testes

- A regressão integral identificou que a sincronização do histórico do DOCX não atualizava a versão na capa. O gerador agora atualiza o estado e a linha de versão da capa automaticamente, e a suíte cobre esse comportamento.
- O gate inicial confirmou a causa com 1 falha documental em 1.312 testes. A regressão completa, build Windows, FH/SAR live e aceite Tapajós em EXE limpo foram disparados novamente após a sincronização automática da capa; ainda aguardam conclusão no SHA final.
- FH real ESA BIOMASS em Sinop e o gate SAR live de Sinop/Tapajós passaram em execução anterior desta candidata. Isso comprova leitura/handoff, não calibração nem homologação científica.
- A homologação científica independente permanece pendente e separada da disponibilidade operacional. Candidata experimental; nenhum EXE liberado até todos os gates operacionais passarem.
