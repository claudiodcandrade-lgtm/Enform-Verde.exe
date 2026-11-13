# V88.45 — contingência ao HTTP 429 do assinador MPC (13/11/2026)

## Causa operacional e alternativa direta

O build Windows da candidata V88.43 encontrou HTTP 429 no endpoint de assinatura de ativos do Microsoft Planetary Computer (MPC) enquanto tentava ler VV e VH. Isso indica limitação transitória do assinador por ativo; não prova que o catálogo ou os dados Sentinel-1 estejam indisponíveis. O MPC documenta tokens SAS de coleção e a assinatura individual como duas rotas de acesso. A coleção Sentinel-1 GRD usa o armazenamento `sentinel1euwest/s1-grd`, separado do armazenamento da coleção RTC.

A candidata 3.26.31-PRECAMPO-EXPERIMENTAL agora tenta primeiro um único token SAS para `sentinel-1-grd` e o reaproveita somente em memória para abrir os COGs VV e VH da mesma aquisição. O token da coleção evita uma chamada ao assinador para cada ativo. Se a rota de token falhar, o código recorre ao assinador por ativo com limite de tentativas; ao receber HTTP 429, para novas cenas nesse provedor/AOI. Tokens e URLs assinadas não são escritos nos relatórios. A auditoria registra qual rota de acesso foi usada.

## Outras rotas Sentinel-1

- INPE RTC público: catálogo STAC e COGs Sentinel-1 calibrados; rota independente já integrada ao pipeline. Uma consulta sem cenas recentes em uma AOI deve ser registrada como tal e não prova indisponibilidade nacional.
- Copernicus Data Space (CDSE): catálogo STAC inclui Sentinel-1 GRD. A rota autenticada Process API e o download direto requerem credenciais OAuth válidas; a indisponibilidade de MPC não deve impedir essa tentativa quando a conta estiver configurada.
- ASF/NASA OPERA RTC-S1: produtos RTC globais sobre áreas terrestres, com novas cenas geralmente processadas em até 12 horas. Exigem acesso ASF/Earthdata; o catálogo ASF já é consultado, mas a leitura de pixel OPERA não está ligada ao pipeline desta candidata.
- AWS Sentinel-1 GRD COG: arquivo global público, com novas cenas normalmente adicionadas em poucas horas. É uma alternativa de descoberta/leitura sem o assinador MPC; os produtos são GRD e não substituem RTC nem calibração/modelagem. Esta rota ainda não foi implementada no leitor da candidata.
- ESA MAAP: o token MAAP permite a rota autorizada de produtos ESA Biomass já implementada para biomassa/altura conforme o produto. Ele não é uma credencial Sentinel-1 e não substitui as rotas MPC, INPE, CDSE ou ASF para monitoramento agrícola C-band.

## Teste e limites

- Testes determinísticos verificam que o token de coleção GRD é preferido e que o signer por ativo não é chamado quando VV/VH são lidos por essa rota.
- A candidata só recebe estado `PROCESSADO` quando VV e VH da mesma cena são lidos. Sem pixels ou após falha técnica, preservar N/D/ERRO com diagnóstico.
- A descoberta de catálogo não é prova de leitura de pixels. O acesso efetivo do token de coleção, por AOI, no Windows e no SHA final ainda precisa passar no CI.
- A amostragem em oito AOIs continua sem garantir disponibilidade em toda coordenada ou data do Brasil. A versão permanece pré-campo experimental, não homologada; banda C Sentinel-1 não é convertida isoladamente em AGB.

## Documentação oficial

- Microsoft Planetary Computer, tokens SAS e assinatura: https://planetarycomputer.microsoft.com/docs/concepts/sas/
- Exemplo STAC oficial Sentinel-1 GRD com ativos COG VV/VH no armazenamento `sentinel1euwest/s1-grd`: https://github.com/stac-extensions/sentinel-1/blob/main/examples/mspc-s1-grd.json
- INPE Sentinel-1: https://data.inpe.br/dados/sentinel-1/
- Copernicus Data Space STAC: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- ASF OPERA RTC-S1: https://hyp3-docs.asf.alaska.edu/guides/opera_rtc_product_guide/
- AWS Sentinel-1 GRD aberto: https://registry.opendata.aws/sentinel-1/
