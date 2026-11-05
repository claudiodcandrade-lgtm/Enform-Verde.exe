# V87.5 — Satélite automático sem chave — 05/11/2026

## Decisão implementada

O Google Maps oficial continua opcional e exige chave de API/billing; sua API não permite acesso direto oficial sem credencial. Para não solicitar chave ou token ao usuário, acrescentam-se alternativas ópticas públicas:

- Sentinel-2 L2A via Planetary Computer, cujo STAC é público; a assinatura SAS temporária do arquivo é obtida automaticamente pelo cliente do serviço, sem credencial fornecida pelo usuário.
- Sentinel-2 L2A via Earth Search / AWS Open Data: pesquisa STAC anônima e COGs RGB públicos, sem token do usuário.
- NASA GIBS WMS, camada `VIIRS_SNPP_CorrectedReflectance_TrueColor`, pública sem chave; tentar datas UTC recentes (1–7 dias antes) para tolerar atraso de publicação, mostrando provedor e data. VIIRS é alternativa regional de resolução mais grossa.

## Ordem automática de fontes

1. Google Maps Static somente com chave oficial configurada.
2. Sentinel-2 L2A Planetary Computer sem credencial do usuário (assinatura SAS automatizada).
3. Sentinel-2 L2A Earth Search/AWS via STAC anônimo e COGs públicos sem chave.
4. NASA GIBS / VIIRS true color sem chave, contexto regional de resolução mais grossa.
5. Esri World Imagery e depois Esri Street Map, se acessíveis sem autenticação pela camada pública legada.
6. IBGE offline se todos os serviços online falharem.

A janela do entorno usa exclusivamente imagem óptica. Dados SAR/radar permanecem reservados aos módulos analíticos.

Todo pedido de rede segue em worker. A indisponibilidade ou erro de uma fonte não bloqueia as outras. O mapa e o limite AOI são apenas visualização; não entram nos cálculos SAR, na identificação de cobertura/cultura, biomassa ou carbono. O IBGE offline permanece empacotado e é mostrado como alternativa final.

## Limitação explícita

A camada VIIRS é uma composição colorida de resolução mais grossa e data de aquisição diferente de imagens de alta resolução; fornece apenas contexto regional. O rótulo deve identificar NASA GIBS, VIIRS e data selecionada. Não confundir essa imagem com Sentinel-2 de 10 m nem com dado analítico. O fallback não garante disponibilidade contínua de nenhum provedor.

## Alterações de software

- `desktop_app.py`: `sentinel2_earthsearch_preview` lê RGB de COGs Sentinel-2 L2A públicos; `nasa_gibs_preview` usa WMS VIIRS como fallback regional; imagem e data são identificadas. Versão `3.26.2-PRECAMPO-EXPERIMENTAL`.
- `tests/test_nasa_gibs_keyless.py`: contratos verificam ausência de credenciais do usuário e a sequência de fontes ópticas até IBGE.
- Atualizar prompt histórico e especificação Word integral junto com o código. Executar regressões e build Windows no SHA final, confirmar pacote e checksum.

## Limites de aceitação

Não alegar conexão live validada apenas porque o código ou build compila. Confirmar retorno de imagem do endpoint e fallback em caso de erro. Google continua opcional e exige chave própria. Earth Search/AWS e NASA GIBS são alternativas públicas automáticas sem token do usuário; no Planetary Computer, a assinatura curta SAS é feita pelo serviço sem credencial do usuário. Homologação científica independente permanece separada e não é modificada por esse recurso.

## Fontes técnicas oficiais

- Google Maps Static — chave obrigatória: https://developers.google.com/maps/documentation/maps-static/get-api-key
- Google Maps Static — cobrança e uso: https://developers.google.com/maps/documentation/maps-static/usage-and-billing
- NASA GIBS Access Basics: https://nasa-gibs.github.io/gibs-api-docs/access-basics/
- Earth Search / Sentinel-2 COGs: https://registry.opendata.aws/sentinel-2-l2a-cogs/
- Earth Search STAC/ativos públicos: https://github.com/Element84/earth-search
- NASA GIBS GIS/WMS usage: https://nasa-gibs.github.io/gibs-api-docs/gis-usage/
- Catálogo oficial de camadas: https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/
- Google Static Maps continua com suas próprias condições: https://developers.google.com/maps/documentation/maps-static/usage-and-billing
