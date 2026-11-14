# ATUALIZAÇÃO V87.39 — 8 DE NOVEMBRO DE 2026 — VERSÃO 3.26.6-PRECAMPO-EXPERIMENTAL — CAUSA RAIZ DAS FALHAS DE PIXEL SAR E CBERS-4A
Base: 829a01d (3.26.5, V87.38). Sintoma no caso Sinop: “ALL_CONFIGURED_RTC_PROVIDERS_FAILED_PIXEL_READ_OR_TEMPORAL_QA” e fundo CBERS-4A ausente, com catálogos respondendo.
## Causa e correção
- GDAL/libcurl (rasterio) não lê o repositório de certificados do Windows; antivírus com inspeção HTTPS e proxies instalam raízes apenas nele. requests (catálogos) e GDAL (pixels COG) tinham cadeias de confiança diferentes; recent_sar_landcover não recebia pacote de CA.
- tls_setup.py: pacote único = certifi + raízes ROOT/CA do Windows (ssl.enum_certificates) + pacote do sistema; exporta REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE, GDAL_CURL_CA_BUNDLE no início do desktop_app; GDAL_HTTP_UNSAFESSL=NO sempre; valores definidos pelo usuário preservados. Leitor SAR usa tls_setup.gdal_env().
## Evidência (ambiente com proxy TLS, verificação ligada)
- Código 3.26.5: 0 cenas lidas; erro “self-signed certificate in certificate chain”.
- Com a correção: 12 cenas Sentinel-1 RTC (MPC) de Sinop lidas, mais recente 31/10/2026; unidades radar 278,8 / 457,5 / 948,4 ha (experimentais, sem rótulo semântico); CBERS-4A/WFI lido (27/10/2026); --network-check com 170.820 pixels VV e VH válidos.
## Prevenção
- Build Windows: Enform Verde.exe --network-check na cópia limpa exige pixels reais CBERS-4A e Sentinel-1 em Sinop com TLS verificado; falha reprova o build.
- tests/test_tls_trust_contract.py. Unidades radar renomeadas sem rótulo semântico.
## Limites
- O teste vivo prova uma AOI (Sinop) no SHA, não cobertura nacional. Classificador semântico SAR, altura validada e dados independentes continuam pendentes; gate fail-closed.
