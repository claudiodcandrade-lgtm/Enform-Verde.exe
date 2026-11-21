# Enform Verde v3.26.30-PRECAMPO-EXPERIMENTAL

## Diagnóstico nacional de acesso Sentinel-1 e distribuição experimental

- No SHA V88.43, a suíte do dashboard, os contratos pré-campo, a máscara SAR experimental de Sinop e a leitura ESA BIOMASS FH em Sinop passaram. O build Windows parou no gate distribuído: em Petrolina, MPC retornou HTTP 429 ao assinar VV/VH e a busca RTC do INPE não encontrou cenas recentes nessa AOI.
- A rota MPC agora interrompe tentativas em cenas antigas após 429. A sondagem percorre os oito AOIs mesmo após um ponto falhar, salva o diagnóstico incrementalmente e remove URLs de ativos do relatório.
- A falha do gate de cobertura não bloqueia mais o build do pacote pré-campo. O EXE portátil deve incluir `DIAGNOSTICO_SAR_NACIONAL.json` e `STATUS_GATE_SAR_NACIONAL.txt`, e o LEIA-ME informa que amostras não provam cobertura SAR em todas as coordenadas/datas do Brasil.
- Resultados sem par VV/VH recente permanecem N/D/ERRO. Nenhum pixel SAR é promovido a classe agrícola validada e banda C não é convertida isoladamente em AGB.

**Status:** candidata experimental pré-campo, não homologada. O CI/build e os resultados da sondagem nacional no SHA 3.26.30 ainda são pendentes. Mesmo que o pacote seja gerado, cobertura nacional exaustiva e validação observacional independente não estão demonstradas.
