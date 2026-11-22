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

A reconstrução local confirmou 841.387 observações, 8.951 unidades e 27 hashes de planilhas. O cruzamento geométrico encontrou uma correspondência única `legenda_1` para cada unidade amostral. Seis testes específicos IFN passaram; a regressão relevante passou com 35 testes, e o self-test do código passou. Os gates locais foram complementados pelo workflow Windows V88.127, aprovado no SHA `f3e50322332b99bbbb25b8bbda23e4add621a701`: o banco IFN foi empacotado, a seleção e a paridade Python/EXE passaram, e o canvas foi capturado integralmente visível. A candidata continua experimental e não está homologada cientificamente.


## Gate da contingência SAR

A rota de contingência por inventário exige certificado explícito de ausência de cenas de altura, esgotamento das rotas sem erros e nenhuma altura quantitativa disponível. A flag legada `conditional_only` não contorna o gate. Falhas técnicas mantêm o resultado bloqueado.

A especificação Word foi atualizada com os resultados do workflow V88.127. A homologação científica independente continua bloqueada por ausência de manifesto de evidência válido e candidato auditado; a versão segue experimental.


## V88.127 — build Windows, IFN e prova live ESA BIOMASS FH (16/11/2026)

- O workflow Windows `44002092852` passou no SHA `f3e50322332b99bbbb25b8bbda23e4add621a701`; artefato `14294027349` (264.032.192 bytes; SHA-256 `bbc5e19ba837ff4f787d9b0cb37a51403888f087dd4221482a6c9dd3e9fb44cd`). EXE em cópia limpa, paridade Python/Windows, `--module-check`, `--visual-check` e `--network-check` passaram. Prévia Sentinel‑2 Tapajós, cobertura óptica 11/11, canvas Tk Sinop, SAR Tapajós, rota S1/INPE em seis biomas, ALOS-PALSAR com pixels Cerrado e leitura S1 VV/VH Sinop passaram.
- O runner construiu e empacotou o SQLite IFN de 488.456.192 bytes: 841.387 observações, 8.951 unidades, 27 arquivos oficiais; cruzamento IBGE Vegetação 2026 `legenda_1` único em 8.951/8.951 unidades. Seleção por localização, bioma e fitofisionomia passou no EXE e teve paridade com Python. Mantém-se como referência estrutural, sem uso como estimador de AGB/ha ou altura média do dossel.
- ESA MAAP FH: prova live em bbox de Sinop próximo ao centro da Fazenda Maria Eduarda retornou dois produtos `FP_FH__L2A`, asset real com HTTP 206 e 2.304 pixels FH; média raster 18,284244 m. A prova confirma funcionamento da rota nesta janela, não estatística do KML integral ou validação de campo. Nas AOIs de Tapajós, FH contou zero produtos; assets L1C consultados responderam 401.
- A homologação científica independente terminou bloqueada: `validation/release_evidence.json` inválido/ausente e nenhuma candidatura com dados e relatório independentes verificados. A versão 3.26.62 segue experimental. KML privado integral da Fazenda Maria Eduarda, cálculo FH→carbono no polígono completo, validação de campo e benchmark de duração continuam pendentes.
