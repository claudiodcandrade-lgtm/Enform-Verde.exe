# V88.156 — normalização de datas dos inventários IFN

Data: 18/11/2026  
Código-base: 3.26.71-PRECAMPO-EXPERIMENTAL

## Falha encontrada

A colheita IFN convertia as datas das planilhas para texto antes de obter mínimo/máximo. Isso ordenava datas como DD/MM/AAAA lexicograficamente, e valores Excel como o serial 45541 ficavam sem conversão. Consequentemente, o manifesto podia exibir um máximo menor que o mínimo ou um número serial, prejudicando qualquer auditoria temporal para pares FH–campo.

## Correção

Foi adicionada normalização compartilhada que reconhece datas Python, textos DD/MM/AAAA/ISO e serials Excel; blanks, zero e valores inválidos não viram datas falsas. O manifesto passa a ordenar datas ISO cronologicamente e conta valores não interpretáveis. A ingestão SQLite aplica o mesmo parser à coluna measurement_date.

Teste de contrato cobre o serial 45541 → 2024-09-06, formatos textuais/datetime e valores ausentes/inválidos. Ele não prova formação de pares FH–inventário nem calibração AGB.

## Evidência de inventários e limite do modelo

O build anterior materializou 841.387 observações IFN em 8.951 unidades, com cruzamento único de legenda_1 IBGE, e 439.970 registros do painel SFB. O modelo local continua sem pareamento temporal/espacial FH–inventário validado no AOI amplo do Tapajós. O modelo ORNL tem suporte restrito às parcelas cadastradas e medições de 2010; sua referência de altura não deve ser pareada com FH contemporâneo sem justificativa temporal e validação. O teste 2010 tentou a rota regional Digital Earth Africa e detectou que ela não cobre o Brasil; não prova ausência de mosaico PALSAR global.

## Estado de liberação

O executável compilou, mas o autoteste em pasta limpa falhou no aceite Tapajós: pixels SAR foram lidos, porém não foi produzida AGB prioritária nem referência de inventário elegível. O job não publicou pacote. A checagem de módulo mostrou que o banco IFN foi incluído (841.387 registros; 8.951 UAs), porém não fornece, por si, um estimador por hectare nem altura de dossel. Correção de datas é necessária para a busca de pareamentos, mas não substitui a calibração e validação microrregional requeridas. Não liberar o 3.26.71 como nova versão operacional.
