## V88.56 — confirmação final de CI e build Windows (14/11/2026)

- O código da versão 3.26.35 permanece no SHA `417e93141ec035d5bb414abb620224d490580927`. O SHA `b4f7adcd4da162021df35187dabef7cc435fcd1e` contém apenas sincronização documental, restauração das marcações científicas V87.1 e rebuild; nenhuma alteração de runtime foi introduzida depois do código testado.
- No dashboard CI #43635716670, a suíte completa terminou com 1.156 testes aprovados. O contrato rápido pré-campo #43635716654 e a máscara SAR experimental de Sinop #43635716643 passaram. Uma execução intermediária do contrato pré-campo falhou porque o marcador V87.1 havia sido omitido dos documentos; o texto foi restaurado e o contrato passou no SHA final.
- O build Windows #43635716635 passou no SHA documental b4f7adcd4da162021df35187dabef7cc435fcd1e. O EXE 3.26.35 passou autoteste em pasta limpa. Artefato Actions 14130517119, 197.798.620 bytes; SHA-256 do ZIP `33b359aea8f60573b4ae39851b096e1616bb85d4b39654fdf03c0bfedd050aab`; SHA-256 do EXE `a7bc32707554ff870fa470d83381172bb0427751d508e9b28263a1a214fc81f4`.
- CBERS-4A/WFI foi lido com pixels reais em 11/11 janelas brasileiras representativas, com cobertura reportada de 100% por janela (mínimo de aceite 95%). O painel Tk mostrou CBERS real numa janela ao redor do centroide de Sinop; Sentinel-2 real no Tapajós passou. Foram aprovados o teste live de SAR no Tapajós, o catálogo INPE Sentinel-1 RTC em amostras dos seis biomas e a prova de pixels ESA BIOMASS FH em Sinop.
- Essas evidências não incluem o KML integral da Fazenda Maria Eduarda até o dashboard e não provam cobertura contínua nacional para todo local e data. O gate científico independente #43635716646 permanece reprovado por ausência de observações de campo independentes. Não homologado; manter pré-campo experimental.


### Auditoria do código e limite da evidência

A revisão V88.49 cobriu cache CCI por análise, retentativas e persistência da auditoria Sentinel-1 e o handoff SAR ao dashboard. Foi uma auditoria direcionada, não uma auditoria exaustiva de todos os módulos e fluxos do produto. Os testes verdes cobrem os contratos e cenários executados; não provam que todas as falhas recorrentes estejam eliminadas nem cobrem toda AOI. Manter essa distinção e realizar revisão estrutural/integração ponta a ponta antes de alegar correção definitiva.


## Auditoria arquitetural pendente

A verificação executada nesta etapa foi direcionada, não uma auditoria exaustiva do repositório. Para avançar, revisar as fronteiras de aquisição→leitura de pixels→processamento SAR→estimadores→manifesto/serialização→handoff para dashboard e o caminho óptico→canvas, incluindo concorrência, timeouts, cache, cancelamento, memória e estados de erro. Registrar cada achado com módulo/linha, condição que o reproduz, impacto, correção e regressão. Não afirmar eliminação universal das falhas recorrentes até concluir essa revisão e a execução da AOI integral da fazenda.


## Revisão arquitetural V88.57 — achados pendentes

Leitura estática preliminar no SHA `417e93141ec035d5bb414abb620224d490580927`: (1) `desktop_app.py:2780` mantém caminho SAR local síncrono; (2) `desktop_app.py:498–502` pode chamar novamente o estimador SAR para cada fitofisionomia potencial; (3) `tests/test_core_to_dashboard_handoff.py` encaminha payload de fixture, não execução real do core; (4) `ifn_carbon_fallback.py:51–89` tem domínio regional limitado à Amazônia/FESV em MT; (5) agregação em `desktop_app.py:2927–2936` precisa de estados tipados. Nenhum item foi corrigido ou validado pela CI prévia. A dashboard #43638982932, contrato pré-campo #43638982863 e máscara SAR Sinop #43638982929 passaram no commit documental `6097f9c`; build Windows #43638982885 ainda estava em execução na consulta. Detalhes e plano no relatório V88.57 incluído no pacote.


## V88.58 — CI em execução no registro inicial

No SHA `2eda195edf89986381e2cf55651f0de16ab4edef`, o contrato pré-campo #43640903762 passou; build Windows #43640903809 e #43640898030, dashboard #43640903822 e máscara SAR #43640903777 estavam em execução. O gate científico #43640903771 falhou corretamente pela ausência de validação independente. ESA BIOMASS FH tinha um workflow associado concluído com sucesso (#43640898030); o segundo ainda em execução. Atualizar este estado após conclusão dos jobs, sem atribuir evidência de aprovação a execuções pendentes.
