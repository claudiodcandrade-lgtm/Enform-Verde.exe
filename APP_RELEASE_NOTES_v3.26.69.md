# Enform Verde v3.26.69-PRECAMPO-EXPERIMENTAL

Esta candidata separa a proveniência da altura FH/GTDX da estimativa de AGB ESA CCI nos resultados, dashboard e gráficos exportados.

## Correção incorporada

- O smoke live do SHA `49c2f17` confirmou FH válido no Tapajós: 1.263 pixels no estrato florestal, leitura completa e sem erro técnico. O handoff completo passou.
- O artefato revelou que a altura e seus pixels eram FH, mas a interface mostrava CCI AGB como produto e origem dessa altura. Agora o `sar_height` explícito segue até o estrato nativo e o dashboard/planilha retiram altura apenas dessa fonte validada. CCI AGB permanece origem separada da estimativa de biomassa.
- Adicionados contratos para rejeitar uma altura cuja única origem seja o raster CCI, além de verificar separadamente o produto/caminho FH e a fonte/caminho CCI.
- A consulta de inventários continua usando todas as fontes harmonizadas compatíveis, além da base IFN. Na AOI do smoke não houve referência agregada ou número suficiente de UAs para comparação; o resultado é N/D com motivo.

## Status

A candidata 3.26.69 ainda não foi liberada. Aguardar regressão integral, novo handoff live, build e autoteste do EXE no mesmo SHA. A homologação científica independente e a validação integral da Fazenda Maria Eduarda continuam sem comprovação.
