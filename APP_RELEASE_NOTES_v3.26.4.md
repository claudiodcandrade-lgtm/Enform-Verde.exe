# Enform Verde 3.26.4-PRECAMPO-EXPERIMENTAL

Versão experimental para validação operacional. Não representa homologação científica independente.

## Correções desta versão

- O fallback de carbono orgânico do solo usa pontos reprodutíveis, uniformes por área e internos ao estrato AOI × formação.
- O fallback só produz totais quando um único serviço retorna os cinco horizontes de 0–100 cm em todos os pontos da amostra. Se isso não ocorrer, o total permanece N/D; não há média de subconjunto nem extrapolação.
- A interseção dos rasters brutos oficiais, por geometria e área de pixel, continua sendo a rota prioritária.
- Os relatórios identificam o tamanho da amostra de fallback e esclarecem que a estimativa descreve o mapa amostrado, sem quantificar erro cartográfico nem incerteza preditiva.

## Limites científicos

A versão continua experimental e não está homologada nacionalmente. O intervalo amostral, erro do produto cartográfico, validação independente em campo e transferibilidade ecológica não são demonstrados por esta alteração. Não substituir lacunas por dados sintéticos.

## Condição de distribuição

O pacote Windows só deve ser considerado pronto após testes completos, execução limpa do EXE e verificação de que artefato, executável e SHA correspondem ao mesmo commit. O gate científico independente é separado e pode permanecer reprovado.
