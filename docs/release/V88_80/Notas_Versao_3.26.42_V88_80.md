# Enform Verde v3.26.42-PRECAMPO-EXPERIMENTAL — V88.80

Data: 15/11/2026  
Commit: `98b0a6795e8af7e3b7f24ac075ed2886a47a8634`

## Correção da regressão do smoke visual

O smoke anterior aceitava o fundo AOI provisório antes de o worker óptico/cartográfico terminar. O critério foi alterado para exigir estado terminal do worker e verificar a imagem renderizada no canvas. O artefato de CI `optical-gui-sinop-live-2899` registra `PASS_CBERS`, provedor CBERS-4A/WFI L4-SR / INPE STAC, 1 item de imagem no canvas, 673×562 e pixels RGB visíveis.

## Resultado da validação

- Dashboard: 1.173 testes aprovados (workflow 43733571768).
- Build Windows e teste do EXE em pasta limpa: aprovados (workflow 43733571725).
- SAR live: processamento até payload do dashboard em amostra pública de Sinop e KMZ Tapajós (workflow 43733571694).
- Sync da especificação Word: aprovado (workflow 43733567007).
- ZIP íntegro; SHA-256: `56bcd4e367cde2d0378cea01164f00a840f563750532cae21cc37553197c264c`.
- EXE SHA-256: `b5db289882b9143e51f0c06080f7a85979ddbaa01fb2245db8fe1d1dd434947c`.

## Restrições científicas e operacionais

O teste de GUI foi feito em amostra pública na vizinhança do centroide de Sinop, não no KML privado da Fazenda Maria Eduarda. O SAR é anual (2025/2026), experimental; classificação semântica atual permanece N/D. O payload de carbono é incompleto, com compartimentos e incertezas não quantificados; não há IC total. O gate de homologação científica não está aprovado. O smoke CBERS 11/11 é uma amostragem, não prova exaustiva de cobertura nacional.

A próxima validação é executar o KML privado integral no Windows e conferir que tela, relatório, exportação e auditoria correspondem à mesma execução.