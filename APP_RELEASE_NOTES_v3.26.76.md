# Enform Verde v3.26.76-PRECAMPO-EXPERIMENTAL

Data: 18/11/2026

## Correção do pacote de inventários

- A investigação do aceite Tapajós no EXE encontrou o CSV harmonizado `structural_aggregate_evidence_v1.csv` na cópia externa do pacote, mas ausente no diretório interno do runtime congelado, onde o módulo de consulta o procura.
- O comando PyInstaller agora inclui esse arquivo em `data/` dentro do runtime `_internal`; a etapa Windows verifica a presença do arquivo e das referências Santos et al. KM72 e KM117 antes do aceite.
- O relatório de aceite registra estado, diagnóstico, quantidade e fontes da evidência de inventários. Falha técnica de leitura passa a ser exposta como erro técnico explícito.

## Verificação e estado

A versão anterior passou nos testes locais, SAR/óptico live e compilou o EXE; o autoteste limpo falhou porque o ativo de evidência não estava no runtime do PyInstaller. No SHA inicial do candidato, o FH ESA BIOMASS live em Sinop passou. A suíte Windows materializou a base IFN, mas a regressão completa encontrou uma falha de sincronização documental: o runner testou o commit de código antes do commit automático do DOCX V88.166, e por isso leu a especificação antiga. Esse resultado não testa o conteúdo atualizado. Uma nova execução integral no SHA com a documentação sincronizada é necessária.

A regressão local após sincronizar o Word passou: 1.312 testes OK, 1 ignorado; 191 módulos, self-test e module-check passaram. O aceite do EXE em pasta limpa Tapajós e o build Windows do SHA com documentos sincronizados ainda não foram aprovados. A homologação científica independente permanece pendente, sem bloquear por si só o funcionamento operacional. Esta é uma candidata pré-campo experimental; não declarar liberação até todos os gates operacionais passarem.
