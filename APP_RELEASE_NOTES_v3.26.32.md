# Enform Verde v3.26.32-PRECAMPO-EXPERIMENTAL

## Previsões experimentais visíveis e rastreáveis no painel de carbono

O painel de carbono agora lista cada previsão numérica derivada da análise, por compartimento e formação, com densidade, área-base, estoque correspondente, faixa disponível, incerteza declarada, modelo, fonte e identificador/hash de rastreio. Resultados sem modelo compatível continuam como N/D e exibem o motivo.

As previsões e cenários experimentais permanecem separados do total conhecido/consolidado. O JSON de previsões e a planilha CSV de medições de campo continuam a registrar previsões e observações em campos distintos; nenhuma observação de campo é fabricada.

A regressão do handoff core → painel agora contém uma previsão numérica de biomassa aérea e verifica que o valor, a identificação de rastreio e a separação entre previsão e medição chegam ao painel. O pacote Windows e a regressão completa ainda precisam passar no SHA desta versão para que o artefato possa ser anunciado.

## Limites

Esta versão não muda os modelos científicos nem cria calibração local. AGB de Sentinel-1 C-band isolada não é inferida. Resultados podem permanecer N/D quando faltam dados e modelos aplicáveis. Não homologado; aferição independente em campo pendente.
