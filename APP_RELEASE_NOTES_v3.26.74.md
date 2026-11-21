# Enform Verde v3.26.74-PRECAMPO-EXPERIMENTAL

Data: 18/11/2026

## Correção desta versão candidata

- Corrige o filtro que impedia as referências agregadas de Santos et al. do Tapajós de serem apresentadas para a subformação Floresta Ombrófila Densa das Terras Baixas. A correspondência pai/subformação é explícita e limitada; bioma permanece exato.
- Expõe as referências KM72 e KM117 separadamente, com os metadados estatísticos publicados. Elas permanecem somente comparativas; não são combinadas, adicionadas ao estoque, nem usadas como calibração de FH.
- O autoteste de aceitação pode reconhecer pixels SAR reais mais referências elegíveis mantendo `AGB=N/D`; isso não cria uma estimativa quantitativa nem aciona contingência de ausência de SAR.
- Otimiza a contingência ESA CCI: não consultar/baixar antes de satisfazer o gate de ausência real de FH e calibração compatível.

## Estado científico e de distribuição

Esta é uma candidata pré-campo experimental. Não há nesta correção modelo quantitativo FH–inventário validado aplicável ao Tapajós, nem aprovação independente de homologação. O EXE só será disponibilizado após regressão, build Windows e autoteste da cópia limpa no mesmo SHA. Não anunciar resultados de AGB numéricos com base nas médias citadas.
