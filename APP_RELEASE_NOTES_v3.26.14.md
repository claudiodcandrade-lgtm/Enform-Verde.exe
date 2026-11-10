# Enform Verde 3.26.14-PRECAMPO-EXPERIMENTAL

## Carbono condicional por inventário IFN quando não há pixels SAR utilizáveis

- Inclui candidatos públicos do Painel de Biomassa e Carbono do Serviço Florestal Brasileiro para Floresta Estacional Sempre-Verde no bioma Amazônia, Mato Grosso: 37 unidades amostrais físicas únicas, com AGB_Chave.
- O módulo de contingência e o CSV IFN estão declarados na receita de empacotamento PyInstaller para o pacote Windows.
- O cenário é executado apenas quando o pipeline SAR confirma ausência de observáveis quantitativos e não há falha técnica pendente. Pixels SAR processados, erro de leitura, autenticação ou falha de serviço bloqueiam a transferência.
- A área usada é a interseção potencial IBGE legenda_1, reportada em seção separada. A vegetação atual continua não confirmada por SAR; o resultado não entra no estoque nativo medido, não confirma cobertura e não é homologado.
- Relata média, desvio-padrão entre unidades e faixa observada. Esses números são dispersão ecológica descritiva; não são IC95% nem intervalo preditivo da fazenda. A conversão de AGB em carbono usa fator fixo 0,47, sem incerteza quantificada.
- Como a transferência e o fator de carbono não têm incerteza mensurada, o resultado usa literalmente “estimativa com incerteza não mensurada” e expõe no JSON/relatório a trilha dos filtros de unidades, soma/n, DP, conversão por fator 0,47, área condicional e conversão para tCO2e.
- A cobertura de inventário adicionada não permite generalização para outras fitofisionomias ou biomas. Para estas áreas, mantém N/D com motivo.

## Estado da validação

- Os testes unitários do novo módulo verificam o gate de ausência SAR, bloqueio de falha técnica e o domínio de fitofisionomia.
- Esta nota não comprova o KML da Fazenda Maria Eduarda no EXE Windows, a classificação atual, nem build ou homologação nacional. Consultar os workflows do SHA final antes de distribuir um executável.
- Verificação local neste ambiente: suíte completa não validada por dependências ausentes (`requests`, `geopandas`, `shapely`); 856 executados, 57 erros, 1 falha, 28 ignorados. Build/CI no SHA `d26a4f8` ainda pendentes.
