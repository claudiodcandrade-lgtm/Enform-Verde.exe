# Enform Verde 3.26.8-PRECAMPO-EXPERIMENTAL

Status: build experimental pré-campo; não é homologação científica (gate independente fail-closed).

## Identificação do uso da terra por SAR (classificador semântico)
- Integra o classificador Sentinel-1 `sar_landcover_lemplus` v2 (`data/models/sar_brasil_rf_v2.joblib`): 12 meses de VV, VH e VH−VV (RTC, 80 m) → floresta nativa, Cerrado nativo, cultivo, pastagem, silvicultura, área antrópica recente (corte raso/solo exposto), água, área úmida; dentro do cultivo: soja, milho, algodão e café.
- Rótulos: LEM+ (INPE, campo, CC BY 4.0), INPE e-sensing Rondônia 2022 e Mato Grosso 2014–2016. MapBiomas não usado.
- Validação em 708 blocos espaciais: OA 92,1% (91,1–93,1%); floresta nativa precisão 0,93 (0,90–0,95); Amazônia-RO 88,8%. Experimental medido (decisão 2B).
- Quando nenhuma cultura listada atinge maioria dos votos, a área aparece como “Área cultivada — cultura não identificada”.
- Domínio validado: savana/Cerrado, ou floresta no envelope MT/RO/oeste-BA (inclui Sinop). Fora dele, permanece o candidato temporal “Área cultivada — candidato SAR experimental; cultura N/D” da 3.26.7 e N/D.
- Teste real em Sinop (2025/26): FESV Submontana 414,7 ha (nativa, IBGE), soja 512,6 ha, área antrópica recente 745,8 ha (conferir em campo).

## Mantido da 3.26.7
- CBERS-4A/WFI prioritário no fundo óptico; Sentinel-2 contingência; TLS por plataforma; serapilheira hierárquica; incerteza total por correlação declarada; previsão “sem vigor”.

## Modelos experimentais em teste (política do proprietário, 09/11/2026)
- Cálculos e predições podem usar modelos experimentais cientificamente defensáveis; a acurácia será aferida depois com dados de campo.
- Vigor sem altura medida: o tamanho aparente das plantas usa o RVI dual-pol como proxy (rotulado EXPERIMENTAL_PROXY_RVI); uniformidade 1/(1+CV) e textura GLCM do VH completam o índice; referência = talhões vizinhos da mesma cultura classificados pelo SAR no raio de 8 km.
- Correções encontradas no teste ponta a ponta: (1) a busca de cenas do vigor falhava com polígonos de classificação muito detalhados — agora usa o retângulo do talhão; (2) a defasagem de publicação do NASA POWER zerava a safra em curso — dias ainda não publicados passam a ser completados por anos análogos.
- Ferramenta `tools/test_models_aoi.py`: roda a cadeia completa (SAR → uso da terra → culturas → vigor → previsão PAM/clima) para qualquer AOI.
- Teste real em Sinop (09/11/2026, proxy RVI): soja 506,6 ha; vigor baixo (cena de 31/10, início da safra, frente a 112 talhões vizinhos — comparação precoce, conferir estádio); previsão 3,45 t/ha (90%: 2,59–3,71), 57,5 sc/ha; produção 1.749 t (1.312–1.878 t). Água disponível do solo: serviço PronaSolos indisponível no momento do teste → valor padrão 1,0 mm/cm registrado.

## Proxy de altura conforme Nasirzadehdizaji et al. (2019)
- O artigo (Applied Sciences 9:655, Tabela 3) mostra que σ⁰VV+σ⁰VH tem a maior relação com a altura do milho no início do ciclo (R² 0,82; VV 0,81; VH 0,80; RVI apenas 0,53) e que a sensibilidade desaparece acima de ~150 cm. O vigor passa a usar VV+VH (dB, multilook 3×3) como tamanho relativo (`EXPERIMENTAL_PROXY_VV+VH`).
- O artigo publica só R² (sem coeficientes nem RMSE): o proxy NÃO é convertido em metros; serve apenas para comparar talhões da mesma cultura e fase. Evidência forte para milho no início do ciclo; para soja não há evidência nesse estudo (registrado em cada resultado).
- Rerodado com o proxy VV+VH: vigor baixo 78% / adequado 22%; previsão 3,53 t/ha (90%: 2,71–3,88), 58,9 sc/ha; produção 1.790 t (1.372–1.966 t).

## Prioridade P-band (ESA BIOMASS) para altura das formações nativas
- A busca de altura passa a incluir o produto aberto ESA BIOMASS Level-2A Forest Height (FP_FH__L2A, banda P, 200 m, liberado em 30/06/2026), depois do L2B (restrito até maio/2027). Em Sinop há produtos L2A FH de 20/08/2026 e 19/09/2026.
- O download exige o token gratuito da ESA MAAP (conta EO Sign In); o programa já aceita esse token.
- Banda X não pertence à missão BIOMASS (é TanDEM-X/TerraSAR-X, COSMO-SkyMed etc.); entra como fonte de altura quando o usuário fornecer o produto. Banda P não é indicada para altura de culturas agrícolas (penetra o dossel baixo); culturas seguem com banda C (Sentinel-1) e banda X quando disponível.
