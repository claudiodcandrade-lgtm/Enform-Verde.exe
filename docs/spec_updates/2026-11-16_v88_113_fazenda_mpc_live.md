# Fazenda Maria Eduarda — execução live limitada ao Microsoft Planetary Computer

**Data:** 16/11/2026
**Base:** Enform Verde 3.26.59-PRECAMPO-EXPERIMENTAL / V88.113
**Autorização:** usuário autorizou explicitamente o envio da geometria da AOI ao Microsoft Planetary Computer.

## Runtime geoespacial

Criado `/tmp/enform-geo-runtime` sem alterar o Python global. Dependências confirmadas por import:

- GeoPandas 1.2.0
- Shapely 2.2.0
- PyProj 3.8.0
- Pyogrio 0.13.0
- Rasterio 1.5.2
- Requests 2.34.2
- scikit-learn 1.8.0 (versão exigida pelo manifesto do classificador)

O KML local contém uma feição poligonal válida, CRS legível e área projetada de 1.459,91 ha (EPSG:6933). As coordenadas não foram incluídas neste registro.

## Busca e leitura SAR no MPC

- Catálogo Microsoft Planetary Computer, Sentinel-1 RTC: 30 itens encontrados na janela móvel de 365 dias; paginação completa.
- Classificador SAR experimental: 30 cenas lidas em pares VV/VH, da órbita descendente relativa 141, cobrindo todos os meses do ano agrícola completo 2025/2026 (out/2025–set/2026).
- Pixels válidos: 2.278. Identidade da classe/agricultura segue experimental e sem validação local de campo.

| Classe inferida | Área (ha) |
|---|---:|
| Área antrópica recente (corte raso/solo exposto) | 576,00 |
| Lavoura de soja | 399,36 |
| Lavoura de café | 1,92 |
| Área cultivada — cultura não identificada | 3,20 |
| Floresta nativa (assinatura SAR) | 471,68 |
| Vegetação nativa (assinatura SAR) | 5,12 |
| Área úmida | 0,64 |
| **Total classificado** | **1.457,92** |
| **Sem classe** | **1,99** |

O ano agrícola concluído não comprova o uso atual nem fornece vigor contemporâneo para 2026/27. A classe de corte raso/solo exposto não deve ser interpretada automaticamente como solo exposto atual. As classes nativas são máscaras experimentais; não constituem validação de campo nem base suficiente, por si só, para uma estimativa de carbono homologada.

## Limites de aceite

Este ensaio confirma instalação de GeoPandas, leitura do KML, descoberta de cenas MPC e execução do classificador sobre pixels SAR reais. Não confirma o handoff integral carbono→dashboard, previsões de safra/vigor atuais, apresentação no aplicativo Windows/EXE, desempenho nacional ou homologação científica. Não foram enviados dados da geometria a provedores além do Microsoft Planetary Computer neste ensaio.
