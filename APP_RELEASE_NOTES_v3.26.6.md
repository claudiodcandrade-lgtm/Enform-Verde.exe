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

## Serapilheira entra no total (V87.40)
- Floresta Estacional Sempre-Verde do norte de Mato Grosso (ex.: Sinop): estimativa hierárquica regional com erro de transferência QUANTIFICADO. Dois inventários gravimétricos locais independentes (Silva et al. 2009, Acta Amazonica, ~50 km de Sinop: 5,12 Mg/ha; Volpato 2024, UFRRJ: 8,70 Mg/ha) definem a média; a heterogeneidade entre 10 sítios florestais brasileiros independentes (τ = 0,396 em ln) define a incerteza de transferência; fração de carbono U(0,42; 0,50).
- Resultado para um sítio FESV novo: 3,08 tC/ha (intervalo preditivo 90%: 1,27–7,48 tC/ha); entra no total como experimental, só em estratos nativos confirmados.

## Decisões do proprietário incorporadas (08/11/2026)
- Classificador SAR: qualquer acurácia medida aceita como experimental, com n e IC95% obrigatórios (sem limiar mínimo).
- Previsão de safra sem vigor: produzida só com clima + histórico PAM, rotulada “PREVISÃO SEM VIGOR”, intervalo mais largo.
- Altura de plantas: modelo SAR publicado aceito como experimental com RMSE/n publicados e erro propagado.
- Serapilheira: estimativa hierárquica estendida a todas as fitofisionomias florestais com estudo gravimétrico verificado (ex.: FOD ES 2,03 tC/ha, IP90% 0,73–5,66).
- Incerteza total do carbono: correlação declarada (biomassa, raízes e necromassa ρ=1; serapilheira e solo independentes), nunca soma simples.
