# Enform Verde v3.26.76-PRECAMPO-EXPERIMENTAL

Data: 19/11/2026

## Correção do pacote de inventários

- A investigação do aceite Tapajós no EXE encontrou o CSV harmonizado `structural_aggregate_evidence_v1.csv` na cópia externa do pacote, mas ausente no diretório interno do runtime congelado, onde o módulo de consulta o procura.
- O comando PyInstaller agora inclui esse arquivo em `data/` dentro do runtime `_internal`; a etapa Windows verifica a presença do arquivo e das referências Santos et al. KM72 e KM117 antes do aceite.
- O relatório de aceite registra estado, diagnóstico, quantidade e fontes da evidência de inventários. Falha técnica de leitura passa a ser exposta como erro técnico explícito.

## Verificação e estado

- SHA do código testado: `46119d9db17d00b2e5fd077d9f184afcc5939e1c`.
- Regressão completa: 1.314 testes aprovados; contrato pré-campo aprovado.
- FH ESA BIOMASS real em Sinop, handoff SAR live Sinop/Tapajós, leitura óptica multibioma, build Windows, verificação do runtime empacotado e autoteste do EXE em pasta limpa aprovados. O aceite Tapajós confirmou a referência agregada no runtime.
- ZIP Windows: `Enform-Verde-Windows-v3.26.76-PRECAMPO-EXPERIMENTAL.zip`, 271.236.209 bytes; SHA-256 `f7154e936c5bac06fd10f76b1fd45f21808f0cc78bcc0a459bcc07b533b6fec3`.
- O contrato pré-campo e os gates operacionais passaram; a homologação científica independente permanece pendente por falta de validação de campo. O programa é operacional como candidata pré-campo/experimental; seus resultados não devem ser declarados cientificamente homologados nem FH–AGB calibrados.
