# V87.6 — Prioridade ao catálogo aberto Sentinel-2 — 05/11/2026

## Requisito funcional consolidado

O mapa do entorno deve mostrar somente imagens ópticas. SAR/radar permanece exclusivo às análises. Entre as rotas sem chave do usuário, priorizar imagens Sentinel-2 L2A do catálogo Earth Search / AWS Open Data.

## Ordem efetiva

1. Google Maps Static apenas se o usuário fornecer chave oficial válida; a API Google não aceita acesso oficial anônimo/sem chave.
2. Earth Search STAC anônimo + RGB Sentinel-2 L2A em COGs públicos, sem chave ou token do usuário.
3. Planetary Computer Sentinel-2 como segundo catálogo, com assinatura SAS de ativos obtida automaticamente, sem credenciais de usuário.
4. NASA GIBS VIIRS true color sem chave, cena regional de resolução mais grossa.
5. Camadas públicas Esri quando acessíveis.
6. IBGE offline como fallback final.

A fonte prioritária Earth Search deve ser tentada antes das outras alternativas no código real, não apenas documentada. Falhas de conexão passam à próxima fonte sem travar interface. Mostrar provedor/data/nuvens quando metadados disponíveis e manter a AOI visível.

## Fronteiras funcionais

Todas essas imagens são para visualização do entorno; não servem como entrada para identificação de culturas, classificação, SAR, estoque de biomassa ou carbono. Não armazenar imagens sem observar licenças/termos dos fornecedores. O fallback NASA VIIRS deve ser claramente identificado como regional e de resolução mais grossa.

## Verificações

O teste de contrato `tests/test_nasa_gibs_keyless.py` deve garantir ordem Earth Search → Planetary Computer → NASA GIBS → Esri → IBGE e ausência de chave de usuário na rota aberta. Exigir regressão completa e build Windows no mesmo SHA antes de publicar um novo pacote. Não afirmar acesso live enquanto a resposta real do provedor não for observada.

O build 3.26.2-PRECAMPO-EXPERIMENTAL continua sujeito aos gates de testes. A homologação científica permanece independente e experimental/pré-campo.

## Referências

- Google Maps Static exige chave: https://developers.google.com/maps/documentation/maps-static/get-api-key
- Sentinel-2 COGs públicos no AWS Open Data: https://registry.opendata.aws/sentinel-2-l2a-cogs/
- Earth Search: https://github.com/Element84/earth-search
- NASA GIBS: https://nasa-gibs.github.io/gibs-api-docs/access-basics/
