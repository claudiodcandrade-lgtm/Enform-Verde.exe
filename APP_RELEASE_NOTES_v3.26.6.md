# Enform Verde 3.26.6-PRECAMPO-EXPERIMENTAL

Status: build experimental pré-campo; não é homologação científica (gate independente fail-closed).

## Causa raiz corrigida — leitura de pixels SAR e CBERS-4A no Windows
- Sintoma (Sinop, Fazenda Maria Eduarda): triagem SAR “ERRO_TECNICO — ALL_CONFIGURED_RTC_PROVIDERS_FAILED_PIXEL_READ_OR_TEMPORAL_QA” e fundo CBERS-4A sem imagem, embora os catálogos respondessem.
- Causa: o GDAL/libcurl dentro do rasterio não usa o repositório de certificados do Windows. Antivírus com inspeção HTTPS e proxies instalam suas raízes apenas nesse repositório; o leitor da série SAR sequer recebia pacote de certificados. Catálogo (requests) funcionava; pixel (GDAL) falhava.
- Correção: `tls_setup.py` cria um único pacote de confiança (certifi + raízes ROOT/CA do Windows + pacote do sistema) e o exporta para requests e GDAL no início do programa, com verificação TLS sempre ligada.
- Evidência: em ambiente com proxy TLS, o código da 3.26.5 falhou com “self-signed certificate in certificate chain” e 0 cenas lidas; com a correção, 12 cenas Sentinel-1 reais de Sinop foram lidas (mais recente 31/10/2026), unidades radar produzidas, CBERS-4A lido (cena de 27/10/2026), sem desligar a verificação.

## Checkpoint V87.50 — validação e sincronização documental
- CI no SHA `0383178fed1d5cd16ce0b1bd0024dc3a153838d5`: regressão completa concluída com 994 testes aprovados; o contrato rápido pré-campo também passou.
- O primeiro run do dashboard acusou ausência dos arquivos canônicos do prompt V52, histórico V43, especificação dedicada de solo e DOCX no conjunto de commits. Todos foram atualizados neste checkpoint; a reexecução documental segue necessária.
- Os builds Windows push/PR avançaram pelos testes de pixels ópticos e SAR, mas ainda estavam em execução durante o registro. Não distribuir nem afirmar EXE/ZIP até confirmar `--network-check`, autoteste limpo, checksum e artefato no mesmo SHA.
- A homologação científica nacional continua bloqueada por falta de evidência independente; 994 testes de software não são homologação.

## Refinamento V87.49 — CA do GDAL no Windows
- O Windows CI detectou que o bundle combinado de CA excedia o limite de 1 MiB do backend Schannel ao abrir COGs Sentinel-2.
- No Windows, requests/Python usam a cadeia combinada e GDAL usa o repositório nativo do Schannel, sem receber o bundle PEM grande; em outros sistemas, GDAL/curl continua usando o bundle compartilhado. Bundles personalizados abaixo de 1 MiB podem ser preservados.
- `GDAL_HTTP_UNSAFESSL=NO` permanece obrigatório. Nenhuma verificação TLS foi desativada. Os leitores CBERS, Sentinel-2, Sentinel-1/ALOS e vigor usam a configuração compartilhada.
- Testes locais focados após o ajuste: 22 passaram. Sentinel-1 VV/VH real em Sinop e Sentinel-2 L2A real em Tapajós foram lidos. Os testes Windows live e build do SHA final continuam sendo o gate de distribuição.

## Contingência visual V87.46
- NASA GIBS/VIIRS SNPP entrou após CBERS-4A e Sentinel-2 como imagem pública exclusivamente visual. Tem resolução inferior; não entra em classificação, vigor, cultura, carbono ou validação.
- Uma chamada local para Tapajós retornou pixels reais; esse caso isolado não demonstra disponibilidade nacional. O smoke geográfico live continua obrigatório.
- A fixture de interface sintética valida apenas renderização/overlay e não conta como dado ou evidência científica.

## Outros
- Unidades radar experimentais com nomes neutros (sem “candidata a vegetação/cultivo”), conforme V87.36.

## Prevenção de recorrência
- Build Windows executa `Enform Verde.exe --network-check` na cópia limpa: exige pixels reais CBERS-4A e Sentinel-1 em Sinop com TLS verificado; falha reprova o build.
- Teste `tests/test_tls_trust_contract.py`: bundle combinado de requests/Python; GDAL usa Schannel nativo no Windows e bundle compartilhado nos demais sistemas; verificação nunca desligada.

## Serapilheira entra no total (V87.40)
- Floresta Estacional Sempre-Verde do norte de Mato Grosso (ex.: Sinop): estimativa hierárquica regional com erro de transferência QUANTIFICADO. Dois inventários gravimétricos locais independentes (Silva et al. 2009, Acta Amazonica, ~50 km de Sinop: 5,12 Mg/ha; Volpato 2024, UFRRJ: 8,70 Mg/ha) definem a média; a heterogeneidade entre 10 sítios florestais brasileiros independentes (τ = 0,396 em ln) define a incerteza de transferência; fração de carbono U(0,42; 0,50).
- Resultado para um sítio FESV novo: 3,08 tC/ha (intervalo preditivo 90%: 1,27–7,48 tC/ha); entra no total como experimental, só em estratos nativos confirmados.

## Decisões do proprietário incorporadas (08/11/2026)
- Classificador SAR: qualquer acurácia medida aceita como experimental, com n e IC95% obrigatórios (sem limiar mínimo).
- Previsão de safra sem vigor: produzida só com clima + histórico PAM, rotulada “PREVISÃO SEM VIGOR”, intervalo mais largo.
- Altura de plantas: modelo SAR publicado aceito como experimental com RMSE/n publicados e erro propagado.
- Serapilheira: estimativa hierárquica estendida a todas as fitofisionomias florestais com estudo gravimétrico verificado (ex.: FOD ES 2,03 tC/ha, IP90% 0,73–5,66).
- Incerteza total do carbono: correlação declarada (biomassa, raízes e necromassa ρ=1; serapilheira e solo independentes), nunca soma simples.

## V87.43 (08/11/2026) — experimento cartográfico opt-in
- Ferramenta separada para treino SAR com rótulos TerraClass 2024 em categorias amplas e validação espacial reportada somente como concordância com mapa.
- Não instala pesos, não integra inferência padrão, não representa validação de campo e não altera áreas/estoques existentes.
- Modelo homologado mantém prioridade; experimento só como contingência; demais áreas retornam N/D com motivo. TerraClass cobre Amazônia/Cerrado; coeficientes de altura por cultura ainda não instalados.

## V87.44 — publicação da branch (08/11/2026)
- Branch `patches-3.26.6` publicada no GitHub; HEAD de código publicado antes deste checkpoint documental `d92a91371007b2adb7bf0c6839197f610298e33c`.
- Conteúdo remoto do classificador experimental e da especificação Word conferido contra os blobs locais.
- Sem status de CI no commit; build Windows, autoteste do EXE e pacote ZIP não foram produzidos nesta etapa. Esta atualização não declara liberação final nem homologação científica.
