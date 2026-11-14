# Checkpoint V88.47 — Windows build aprovado, validação científica pendente

Data: 14/11/2026  
Versão candidata: `3.26.31-PRECAMPO-EXPERIMENTAL`  
SHA de código testado: `8334643eadb4d82366c06eed789c9e659c752b09`  
Branch: `patches-3.26.6`, PR #51 em rascunho; não mesclar.

## Resultado Windows

O build Windows #2726 concluiu com sucesso. EXE compilado e validado em pasta limpa; passaram paridade Python/Windows, smoke da GUI, padrão visual e rede com TLS ativo. O teste real de rede no EXE leu CBERS-4A/WFI e Sentinel-1 VV/VH, 170.820 pixels por banda; a cópia HTTPS local leu 169.168 por banda.

A aceitação do KMZ de teste Tapajós resultou em `SAR_PROCESSADO`, 1.290,688 ha, 302.348 pixels, três cenas, `SAR_DERIVED_CCI`, sem valor `fallback_agb_mg_ha`. Esta é evidência de fluxo SAR operacional no caso de teste, não nova AGB quantitativa validada pela banda C.

Gate nacional amostral #2726: 8/8 AOIs em seis biomas lidas via SAS de coleção sem HTTP 429. INPE RTC teve zero cenas compatíveis nos recortes; essa amostra não prova cobertura wall-to-wall ou indisponibilidade nacional do INPE. Dashboard #3448, contrato rápido #805 e máscara experimental SAR Sinop #207 passaram.

## Artefato

- ZIP: `Enform-Verde-Windows-v3.26.31-PRECAMPO-EXPERIMENTAL`, ID `14087567135`, 531.996.993 bytes.
- SHA-256 do ZIP Actions: `1ad43f1281171b2eb49678bbc6ca5631587eef8f9b8ba69fa00904df1e2b9e77`.
- SHA-256 do executável: `b7743a0d046390c14d3bdb97332fd15aeb82c8f72af85b07a0331e6db927264c`.

## Estado e limites

Build e smokes operacionais do EXE aprovados. A homologação científica #3035 reprovou por falta de evidência observacional independente. Não foi comprovada a execução integral do KML da Fazenda Maria Eduarda até o dashboard. Manter `PRECAMPO-EXPERIMENTAL`, sem homologação, sem garantia nacional wall-to-wall e sem inferir AGB de C-band isolada. SOC 0–100 cm segue sob seu gate próprio de dados oficiais/incerteza.
