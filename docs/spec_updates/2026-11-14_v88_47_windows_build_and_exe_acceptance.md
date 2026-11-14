# V88.47 — build Windows e aceite do executável concluídos (14/11/2026)

## Resultado no SHA 8334643eadb4d82366c06eed789c9e659c752b09

O workflow Windows #2726 concluiu com sucesso. O executável `3.26.31-PRECAMPO-EXPERIMENTAL` foi compilado, testado numa pasta limpa, passou paridade dos módulos Python/Windows, smoke de interface, padrão visual e verificação de rede com TLS ativo. A verificação real do executável leu pixels CBERS-4A/WFI e Sentinel-1 VV/VH; no Sentinel-1 foram contados 170.820 pixels válidos por banda e 169.168 por banda na leitura HTTPS local da cópia de teste.

A aceitação do KMZ de teste Tapajós retornou `SAR_PROCESSADO`, 1.290,688 ha, 302.348 pixels e três cenas. O relatório identificou `data_origin=SAR_DERIVED_CCI` e `fallback_agb_mg_ha=null`; esse aceite operacional não deve ser descrito como uma nova estimativa de AGB quantitativa derivada diretamente da cena C-band.

O gate SAR distribuído #2726 também passou como `PASS_DISTRIBUTED_SAMPLE`: oito AOIs em seis biomas tiveram par VV/VH recente lido por `COLLECTION_SAS_TOKEN`, sem HTTP 429. INPE RTC retornou zero cenas compatíveis nesses recortes; não extrapolar a amostra para todo o país.

Dashboard dual #3448, contrato rápido #805 e máscara SAR experimental Sinop #207 passaram. A homologação científica independente #3035 reprovou por insuficiência de evidências observacionais. A análise integral do KML Fazenda Maria Eduarda até o dashboard não foi executada/comprovada neste workflow.

## Artefato Windows

- Artifact Actions: `Enform-Verde-Windows-v3.26.31-PRECAMPO-EXPERIMENTAL`, ID `14087567135`, tamanho 531.996.993 bytes.
- SHA-256 do ZIP Actions: `1ad43f1281171b2eb49678bbc6ca5631587eef8f9b8ba69fa00904df1e2b9e77`.
- SHA-256 do `Enform Verde.exe`: `b7743a0d046390c14d3bdb97332fd15aeb82c8f72af85b07a0331e6db927264c`.
- O EXE foi construído no código SHA `8334643eadb4d82366c06eed789c9e659c752b09`.

## Decisão

Build e smokes operacionais Windows aprovados para a candidata experimental. Manter a etiqueta `PRECAMPO-EXPERIMENTAL` e não declarar homologação científica. Permanecem pendentes a execução integral da Fazenda Maria Eduarda até o dashboard e a validação científica independente; a amostra SAR não garante cobertura em cada coordenada/data do Brasil.
