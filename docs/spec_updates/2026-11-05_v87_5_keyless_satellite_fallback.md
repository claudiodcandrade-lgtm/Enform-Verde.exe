# V87.5 — Satélite automático sem chave — 05/11/2026

## Decisão implementada

Adicionar NASA GIBS WMS como fonte pública de visualização de satélite sem API key, token do usuário ou faturamento. A camada usada é `VIIRS_SNPP_CorrectedReflectance_TrueColor`, solicitada via WMS EPSG:4326. O cliente tenta datas recentes (1 a 7 dias antes da data UTC atual) para tolerar o atraso de publicação. Mostra a data da cena na atribuição do provedor.

## Ordem automática de fontes

1. Google Maps Static, se o usuário configurou uma chave válida.
2. Sentinel-2 L2A via Planetary Computer, sem credencial do usuário.
3. NASA GIBS / VIIRS verdadeiro colorido, serviço público sem chave.
4. Esri World Imagery e depois Esri Street Map, quando acessíveis.
5. IBGE offline se todos os serviços online falharem.

Todo pedido de rede segue em worker. A indisponibilidade ou erro de uma fonte não bloqueia as outras. O mapa e o limite AOI são apenas visualização; não entram nos cálculos SAR, na identificação de cobertura/cultura, biomassa ou carbono. O IBGE offline permanece empacotado e é mostrado como alternativa final.

## Limitação explícita

A camada VIIRS é uma composição colorida de resolução mais grossa e data de aquisição diferente de imagens de alta resolução; fornece apenas contexto regional. O rótulo deve identificar NASA GIBS, VIIRS e data selecionada. Não confundir essa imagem com Sentinel-2 de 10 m nem com dado analítico. O fallback não garante disponibilidade contínua de nenhum provedor.

## Alterações de software

- `desktop_app.py`: nova função `nasa_gibs_preview`, tentativa automatizada após falha Sentinel-2, legenda/data do serviço, mensagem da interface explicando alternativas sem chave; versão `3.26.2-PRECAMPO-EXPERIMENTAL`.
- `tests/test_nasa_gibs_keyless.py`: contratos verificam endpoint público e camada, ausência de chave/autorização, ordem NASA→Esri→IBGE, qualificação da imagem como contexto visual.
- Atualizar prompt histórico e especificação Word integral junto com o código. Executar regressões e build Windows no SHA final, confirmar pacote e checksum.

## Limites de aceitação

Não alegar conexão live validada apenas porque o código ou build compila. Confirmar retorno de imagem do endpoint e fallback em caso de erro. Google continua opcional e exige chave própria; NASA GIBS é a alternativa pública automática, sem token. Homologação científica independente permanece separada e não é modificada por esse recurso.

## Fontes técnicas oficiais

- NASA GIBS Access Basics: https://nasa-gibs.github.io/gibs-api-docs/access-basics/
- NASA GIBS GIS/WMS usage: https://nasa-gibs.github.io/gibs-api-docs/gis-usage/
- Catálogo oficial de camadas: https://gibs.earthdata.nasa.gov/layer-metadata/v1.0/
- Google Static Maps continua com suas próprias condições: https://developers.google.com/maps/documentation/maps-static/usage-and-billing
