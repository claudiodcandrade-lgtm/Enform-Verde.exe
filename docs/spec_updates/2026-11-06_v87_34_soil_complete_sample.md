# REVISÃO V87.34 — ENFORM VERDE 3.26.4-PRECAMPO-EXPERIMENTAL
A contingência de estoque de carbono orgânico do solo por Identify foi restringida a uma amostra espacial reprodutível de pontos internos à interseção AOI × formação. O resultado só é calculado quando um único serviço oficial retorna os cinco horizontes em todos os pontos solicitados; sem essa completude, o estoque 0–100 cm permanece N/D. A interseção dos rasters brutos oficiais por pixel e polígono continua sendo a rota prioritária.

## Relato e incerteza
- O diagnóstico registra número de pontos, serviço escolhido e tentativas por serviço.
- A amostra descreve a distribuição do produto cartográfico dentro da formação; não quantifica erro do mapa, viés de transferência, validação de campo ou intervalo preditivo. O relatório expõe o tamanho amostral e a origem do dado para auditoria.
- Fertilidade do solo segue em painel próprio e não é confundida com o compartimento de carbono do solo.
- A sondagem do serviço em pontos de controle confirma respostas dos cinco horizontes nesses pontos, não acurácia nacional nem validação observacional independente.

## Estado de release
- Versão 3.26.4-PRECAMPO-EXPERIMENTAL: candidata técnica.
- A homologação científica independente permanece reprovada enquanto faltarem evidências observacionais independentes exigidas para biomas, compartimentos e funcionalidades.
- Resultados sem cobertura completa ou suporte científico permanecem N/D; não são preenchidos com dados sintéticos.


## UPDATE V87.34.1 — CI contract aligned with the soil service module (06/11/2026)
The Windows GUI contract was incorrectly searching for the primary PronaSolos endpoint inside desktop_app.py, although endpoint definitions intentionally live in pronasolos_identify.py. The assertion now reads that dedicated registry and checks the primary official endpoint plus candidate-service declaration. No service behavior or scientific acceptance threshold changed. Re-run Windows build, GUI contract, complete regression, package integrity and clean-folder EXE checks at the new source SHA. The independent scientific homologation gate remains failed pending real independent evidence; this contract fix does not satisfy it.

## REVISÃO V87.35 — critério territorial nacional (06/11/2026)

### Requisito de operação
O aplicativo deve aceitar AOIs em todas as UFs e manter o fluxo disponível em todo o Brasil. A cobertura observacional, atualização e validade de cada produto são condicionais às fontes; para cada AOI/módulo o sistema deve retornar um resultado sustentado ou um estado explícito de ausência de dados, modelo não validado ou erro técnico. Não usar preenchimento cartográfico como imagem de satélite, nem médias genéricas para ocultar ausência de pixels SAR.

### Cobertura e verificação
A prévia óptica procura Sentinel-2 e usa CBERS-4A/WFI em contingência, exibindo proveniência, data, resolução, cobertura e falhas. A matriz de dez localidades é um smoke test representativo, não prova de cobertura de cada pixel nacional. Os testes SAR de Tapajós e Cerrado também são evidência localizada, não cobertura nacional. Para afirmar operação nacional integral, executar uma matriz estratificada por seis biomas, UFs, extremos, bordas de cena, órbitas e períodos, registrando denominadores, pixels válidos, cobertura por módulo/AOI, erros de serviço/licença/autenticação e fallbacks.

### Domínio científico
Solo orgânico 0–100 cm requer os cinco horizontes pareados no mesmo serviço; qualquer incompletude implica N/D para o total. AGB, altura, necromassa, serrapilheira, raízes, fertilidade, identificação de cultura, vigor e safra só produzem números dentro do domínio e da evidência documentados. Sem pesos ou validação aplicável, usar abstenção/N/D_VALIDACAO. Testes de contrato e leitura de pixels não são validação independente.

### Estado de liberação
PR #50, branch feature/agricultural-identification-native-carbon. O HEAD 732957be2462b33a727b0211f9b089621f3ea666 tinha contratos rápidos aprovados, com regressão completa e build Windows em execução; o gate independente de homologação científica reprovou. Este critério é adicionado ao prompt canônico V52 e à especificação Word pelo workflow sincronizado. Só anunciar pacote técnico após a regressão completa, matriz óptica, testes SAR regionais, build e autoteste do EXE em pasta limpa, hashes e SHA final coincidirem. Operação nacional integral e homologação científica não estão demonstradas por dez amostras.