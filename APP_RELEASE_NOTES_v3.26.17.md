# Enform Verde 3.26.17-PRECAMPO-EXPERIMENTAL

## Correções de acesso SAR e contingência de carbono

- Nas retentativas MPC de leitura de pixels, alterna SAS da coleção, assinatura individual do ativo e renovação de SAS. As tentativas deixam de repetir somente a mesma rota do assinador.
- A triagem SAR recente e o classificador experimental LEM+ usam a mesma sequência de recuperação de credenciais.
- Os diagnósticos SAR registram se a falha ocorreu na autorização, abertura do COG, leitura da janela ou reprojeção. A verificação TLS permanece ativa.
- Acrescenta contingência agrícola MapBiomas Collection 11 + PAM 2015–2024 somente depois que todas as rotas SAR configuradas forem auditadas e não produzirem pixels/máscara. Os resultados ficam separados da classificação atual SAR: classe MapBiomas anual, histórico PAM e produção condicional são referências, não observação ou previsão atuais.
- Normaliza pontuação, hífen, acentos e espaços em nomes de fitofisionomia. A grafia IBGE “Floresta Estacional Sempre Verde Submontana” agora encontra as unidades IFN compatíveis já existentes.
- Tenta a contingência de inventário quando nenhum estoque de carbono foi quantificado, inclusive quando há máscara/estrato sem compartimentos calculados. O cenário permanece separado do estoque medido e não confirma cobertura nativa.

## Verificação e limites

Os seis testes focados de recuperação de credenciais e fallback IFN passaram neste ambiente. Os testes geoespaciais e a leitura de pixels reais não puderam ser executados localmente porque GeoPandas e Rasterio estão ausentes. Não há evidência ainda de que o SAR ou as imagens CBERS-4A/Sentinel-2 funcionem no KML integral do Tapajós ou da Fazenda Maria Eduarda. Esta versão não deve ser tratada como liberação corrigida até o CI Windows e os testes de pixels nesses perímetros passarem.
