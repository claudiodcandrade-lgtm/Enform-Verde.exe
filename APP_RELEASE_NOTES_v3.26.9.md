# Enform Verde 3.26.9-PRECAMPO-EXPERIMENTAL — 10/11/2026

**Natureza:** piloto experimental para avaliação em campo; não homologado cientificamente. Esta versão só pode ser distribuída se build Windows, suíte completa e autotestes no mesmo SHA forem aprovados.

## Correções comprovadas no código
- ESA BIOMASS: descoberta por MAAP STAC GET/bbox com fallback POST e paginação controlada; erros HTTP e paginação incompleta não devem ser reportados como ausência de cenas.
- Integração de altura P-band: o pipeline automático de formações nativas agora aceita `FP_FH__L2A` (além de `FP_FH__L2B`), executa leitura zonal do GeoTIFF de altura e mantém produto, fonte, número de pixels, média e dispersão espacial, sem converter FH diretamente em AGB.
- Sentinel-1: transações VV/VH por cena preservam a grade de uma leitura válida; falha de uma cena não contamina as próximas. Pouca separabilidade das assinaturas gera abstenção científica, não classificação fabricada.
- Diagnóstico de uso da terra: número de cenas, tentativas, pixels lidos e falhas por provedor no relatório.
- Imagem óptica: teste live de CBERS-4A no caminho completo thread/fila/Tk canvas para detectar defeitos que o simples teste de COG não enxergava.

## Evidência ESA BIOMASS prévia e seu alcance
- GitHub Actions 42813753319: na bbox de teste em Sinop, 2.304 pixels FH L2A reais com altura média de 18,284244 m. **Não representa a média de altura da Fazenda Maria Eduarda**, cuja máscara florestal e KML completo não foram validados nesse teste.
- O FH (H100) não mede diretamente biomassa aérea ou carbono. Resultados somente com modelagem alométrica e inventários elegíveis; incertezas e dados ausentes devem ser identificados.

## Bloqueios que impedem alegar conclusão científica e eficácia nacional
- No Windows do proprietário, a imagem CBERS-4A/Sentinel-2 não abriu na AOI Fazenda Maria Eduarda; a nova cadeia GUI exige ensaio real.
- Identificação e delimitação atuais de nativas e cultivos por SAR e a previsão de safra não foram demonstradas nesse KML, e não podem ser substituídas por área IBGE potencial ou MapBiomas histórico.
- FH L2A da pequena bbox não é um cálculo de carbono por fitofisionomia. Precisam-se máscara atual, área por formação, inventários microrregionais, alometria e incerteza por compartimento.
- Homologação científica independente nacional continua pendente; N/D é preferível a números sintéticos apresentados como observados.

## Critérios técnicos mínimos para a distribuição
- Exigir CI de regressão, build do mesmo SHA, EXE abrindo em pasta limpa, dados ópticos visíveis em canvas, prova MAAP live e relatórios com proveniência auditável.
- Publicar checksum SHA256, número de build e artefato imutável; não reutilizar ZIP de versões anteriores.
