# V87.83 - Token ESA MAAP emitido em 08/11/2026, renovação orientada
## Registro confirmado pelo proprietário
- Data de emissão do token ATUAL: 08/11/2026, declarada expressamente pelo proprietário.
- Validade nominal do ESA MAAP Long-Lasting Token: 90 dias corridos, com vencimento estimado em 06/02/2027 e alerta de renovação a partir de 22/01/2027.
- Ao abrir o Enform Verde, registrar a data inicial somente caso ainda não exista renovação posterior e o prazo original não tenha transcorrido. Registros de renovação posteriores prevalecem. Instalação nova após o prazo sem registro não deve presumir validade; mostrar desconhecido.
- A interface mantém campo mascarado para inserir/substituir token, botão para abrir o portal oficial https://portal.maap.eo.esa.int/ini/services/auth/token/ e botão para informar data efetiva do token novo.
- O arquivo local de lembretes registra somente data, versão de esquema e validade nominal. Não armazenar segredo em disco, relatórios ou logs. Não usar data presumida como evidência de autenticação.
- Testes de regressão validam a data inicial, o vencimento, aviso com 15 dias de antecedência, prevalência de renovações e ausência de informação armazenada depois de prazo vencido sem registro.
- Homologação do EXE Windows continua dependente dos testes do artefato compilado e da validação operacional no KML completo da Fazenda Maria Eduarda.
