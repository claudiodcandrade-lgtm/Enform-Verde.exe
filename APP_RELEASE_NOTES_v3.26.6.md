# Enform Verde 3.26.6-PRECAMPO-EXPERIMENTAL

Status: build experimental pré-campo; não é homologação científica (gate independente fail-closed).

## Causa raiz corrigida — leitura de pixels SAR e CBERS-4A no Windows
- Sintoma (Sinop, Fazenda Maria Eduarda): triagem SAR “ERRO_TECNICO — ALL_CONFIGURED_RTC_PROVIDERS_FAILED_PIXEL_READ_OR_TEMPORAL_QA” e fundo CBERS-4A sem imagem, embora os catálogos respondessem.
- Causa: o GDAL/libcurl dentro do rasterio não usa o repositório de certificados do Windows. Antivírus com inspeção HTTPS e proxies instalam suas raízes apenas nesse repositório; o leitor da série SAR sequer recebia pacote de certificados. Catálogo (requests) funcionava; pixel (GDAL) falhava.
- Correção: `tls_setup.py` cria um único pacote de confiança (certifi + raízes ROOT/CA do Windows + pacote do sistema) e o exporta para requests e GDAL no início do programa, com verificação TLS sempre ligada.
- Evidência: em ambiente com proxy TLS, o código da 3.26.5 falhou com “self-signed certificate in certificate chain” e 0 cenas lidas; com a correção, 12 cenas Sentinel-1 reais de Sinop foram lidas (mais recente 31/10/2026), unidades radar produzidas, CBERS-4A lido (cena de 27/10/2026), sem desligar a verificação.

## Outros
- Unidades radar experimentais com nomes neutros (sem “candidata a vegetação/cultivo”), conforme V87.36.

## Prevenção de recorrência
- Build Windows executa `Enform Verde.exe --network-check` na cópia limpa: exige pixels reais CBERS-4A e Sentinel-1 em Sinop com TLS verificado; falha reprova o build.
- Teste `tests/test_tls_trust_contract.py`: pacote combinado inclui raízes do sistema e é usado pelo leitor SAR; verificação nunca desligada.
