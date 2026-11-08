# V87.37 — contrato de correção da classificação SAR, imagem e carbono

## Diagnóstico da branch antes do patch

O HEAD do PR #50, SHA `4d0e464d4b078df5acabd934ca4fc8e596cb2bda`, ainda adicionava polígonos MapBiomas às classes finais quando faltava classificador SAR. O módulo de vigor ainda carregava raster MapBiomas como referência de classe. O fundo óptico tentava Sentinel-2 antes de CBERS-4A. O painel executivo agrupava `native_status=None` como uso não nativo e podia mostrar ausência de máscara como 0 ha. Esses fatos contradiziam os documentos V87.36.

## Patch de correção candidato

1. Remove consulta/overlay MapBiomas do caminho de classificação corrente. Não fornecer classe de uso, máscara de cultura, rótulo, área, referência de vigor ou entrada de previsão.
2. Mantém classes temáticas apenas de SAR semântico validado com suporte por classe: n≥30 e limite inferior Wilson 95% ≥0,70. Isso é gate de implantação, não certificação de cobertura nacional.
3. Usa assinaturas temporais SAR lidas como unidades experimentais sem semântica. Sem classificação validada, presença nativa/cultura é N/D.
4. Separa explicitamente `native_status=None` de `False`; ausência de dado não se transforma em 0 ha.
5. Reordena o fundo óptico para CBERS-4A/WFI antes das duas rotas Sentinel-2 existentes. A função exige RGB COG real e máscara válida; a execução específica em Sinop ainda precisa ser observada.
6. Retira MapBiomas do classificador consolidado e do vigor. O composto de vigor bloqueia quando a altura em metros não é compatível ou ausente; mantém métricas parciais.
7. Emite quadro de carbono com compartimentos, densidades e incertezas; não soma incertezas marginais. A incerteza total fica N/D sem covariância completa/replicação sustentada.
8. Preserva o painel de fertilidade. Serrapilheira continua N/D quando houver somente espessura IFN, sem massa seca gravimétrica transferível.

## Evidência local

Oito regressões do contrato SAR-only, fonte CBERS prioritária, diferença N/D/zero, vigor/altura e quadro de carbono passaram localmente; `py_compile` dos módulos presentes no patch passou. Isso não substitui o conjunto integral de testes, execução real com KML, CI Windows, leitura real de pixels CBERS e verificação do EXE/artefato no SHA final.

## Critério de publicação

Não mesclar nem chamar de release operacional até todos os checks exigidos e a geração do ZIP Windows passarem no mesmo commit. Gate técnico não equivale a homologação científica nacional. No relatório do KML Sinop, não afirmar que houve abertura CBERS ou identificação semântica até que logs e pixels reais comprovem esses eventos.
