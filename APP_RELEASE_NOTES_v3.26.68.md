# Enform Verde v3.26.68-PRECAMPO-EXPERIMENTAL

Candidata técnica com correções das rotas prioritárias de altura FH e GTDX.

## Alterações

- Corrigido o seletor GTDX: entre os links CMR de um mesmo arquivo, escolhe a URL HTTPS oficial de distribuição Earthdata e ignora `s3://`, que não é aceito pelo cliente HTTP do aplicativo Windows.
- Corrigida a leitura FH para tentar todos os rasters candidatos e preservar a auditoria por arquivo. Leitura concluída sem pixels na AOI é distinta de falha de driver, decodificação, download ou autenticação.
- O gate de contingência só certifica ausência com consulta, downloads e leituras completas, sem erros técnicos.
- Autoteste grava diagnóstico antes de reprovar e informa a falha da rota prioritária, sem culpar a referência regional quando FH/GTDX está incompleto.
- A comparação CCI usa referências AGB compatíveis do registro de inventários inteiro, não apenas IFN; estudos permanecem separados e fontes não harmonizadas não são extrapoladas.

## Status da candidata

Ainda não liberada. Aguardar suíte integral, handoff live Sinop/Tapajós, build e autoteste Windows no mesmo SHA. A geometria integral da Fazenda Maria Eduarda e a homologação científica continuam sem comprovação nesta revisão.
