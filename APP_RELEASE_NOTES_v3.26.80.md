# Enform Verde v3.26.80-PRECAMPO-EXPERIMENTAL

## Correções desta candidata

- O resumo fitossociológico IFN para até 100 unidades amostrais agora agrega os registros selecionados em uma única consulta SQLite, em vez de executar uma consulta por unidade. Mantém a mesma seleção espacial e os mesmos indicadores de frequência, abundância, DAP, altura, área basal e classes diamétricas.
- Acrescenta regressão que exige uma única consulta agregada para a rota compacta de biodiversidade e compara seus números com a leitura detalhada.
- O autoteste do EXE agora identifica cada subprocesso (`ui-smoke`, `module-check`, `visual-check`, `network-check`, `tapajos-acceptance`) e interrompe uma etapa que exceda seu limite. Um runner preso não fica mais sem diagnóstico por tempo indefinido.
- Mantém a validação IFN por manifesto e a seleção espacial indexada; nenhuma leitura integral do banco é feita por consulta.

## Estado

Candidata experimental. FH real em Sinop e handoff FH/AGB até o payload do dashboard passaram na candidata anterior. A conclusão do EXE limpo da v3.26.79 permaneceu presa no autoteste por mais de 25 minutos, sem expor qual subprocesso estava aguardando. A v3.26.80 melhora a consulta fitossociológica e adiciona limites/identificação de etapa para localizar esse bloqueio.

Build Windows, autoteste em pasta limpa e checksum desta candidata ainda precisam concluir no mesmo SHA antes da disponibilização do ZIP. Homologação científica independente e validação de campo permanecem pendentes.
