# Enform Verde v3.26.62-PRECAMPO-EXPERIMENTAL

## Registro V88.126 — base IFN de árvores no executável e seleção por domínio

Data: 16/11/2026  
Versão de aplicativo: 3.26.62-PRECAMPO-EXPERIMENTAL

## Banco IFN e associação IBGE

- O workflow passa a baixar e conferir por SHA-256 os 27 arquivos estaduais do conjunto IFN DAP ≥10 cm, reconstruir a base SQLite de medições e incluir o banco no pacote Windows.
- As 8.951 unidades amostrais são associadas espacialmente ao mapa de Vegetação do IBGE 2026 pela `legenda_1`, usando o ponto central da unidade IFN. A seleção de referência filtra primeiro pelo bioma SFB e pela fitofisionomia `legenda_1`, depois ordena unidades dentro de um raio geográfico definido.
- O executável deve conferir a presença do banco e exercitar a seleção por localização, bioma e `legenda_1` no teste de módulo compilado, além dos testes de fonte.
- As coordenadas pertencem às unidades amostrais, não às árvores individuais. `legenda_1` representa a região fitoecológica potencial do mapa IBGE; o cruzamento não confirma cobertura atual nem valida a classe em campo.

## Limites de uso para carbono

- A consulta produz referências estruturais de DAP e altura individual de árvores e resumos da amostra observada. Não aplica fator de expansão do desenho amostral, não converte área basal bruta em m²/ha e não chama altura individual média de altura do dossel.
- O banco não passa a gerar AGB por hectare nem substitui a altura média do dossel ESA BIOMASS FH. Esses cálculos continuam bloqueados até que pesos/área amostral e equações alométricas compatíveis sejam documentados e validados no domínio.
- Altura do inventário só pode ser uma referência contingencial quando a ausência de cenas de altura SAR tiver sido certificada após esgotar as rotas. Erro técnico, falha de acesso ou leitura incompleta não habilitam a contingência.

## Verificação e liberação

A reconstrução local confirmou 841.387 observações, 8.951 unidades e 27 hashes de planilhas. O cruzamento geométrico encontrou uma correspondência única `legenda_1` para cada unidade amostral. Seis testes específicos IFN passaram; a regressão relevante passou com 35 testes, e o self-test do código passou. Esses gates locais não comprovam o pacote Windows. A compilação, o autoteste do executável com o banco embutido e a paridade de seleção Python/EXE ainda dependem do workflow Windows no SHA desta revisão. A candidata continua experimental e não está homologada cientificamente.


## Gate da contingência SAR

A rota de contingência por inventário exige certificado explícito de ausência de cenas de altura, esgotamento das rotas sem erros e nenhuma altura quantitativa disponível. A flag legada `conditional_only` não contorna o gate. Falhas técnicas mantêm o resultado bloqueado.

A especificação Word foi sincronizada localmente na V88.126. O pacote Windows e a seleção na versão compilada ainda dependem do workflow no commit final.
