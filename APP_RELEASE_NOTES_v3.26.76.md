# Enform Verde v3.26.76-PRECAMPO-EXPERIMENTAL

Data: 18/11/2026

## Correção do pacote de inventários

- A investigação do aceite Tapajós no EXE encontrou o CSV harmonizado `structural_aggregate_evidence_v1.csv` na cópia externa do pacote, mas ausente no diretório interno do runtime congelado, onde o módulo de consulta o procura.
- O comando PyInstaller agora inclui esse arquivo em `data/` dentro do runtime `_internal`; a etapa Windows verifica a presença do arquivo e das referências Santos et al. KM72 e KM117 antes do aceite.
- O relatório de aceite registra estado, diagnóstico, quantidade e fontes da evidência de inventários. Falha técnica de leitura passa a ser exposta como erro técnico explícito.

## Verificação e estado

A versão anterior passou nos testes locais, SAR/óptico live e compilou o EXE; o autoteste limpo falhou porque o ativo de evidência não estava no runtime do PyInstaller. A regressão local após sincronizar o Word passou: 1.312 testes OK, 1 ignorado; 191 módulos, self-test e module-check passaram. Novo build Windows e aceite Tapajós em cópia limpa no SHA final ainda pendentes. A homologação científica independente permanece pendente. Esta é uma candidata pré-campo experimental, sem EXE liberado até todos os gates operacionais passarem.
